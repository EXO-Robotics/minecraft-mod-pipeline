export const LEGACY_UNCLAIMED_OWNER = 'legacy-unclaimed';
export const CURRENT_STATE_SCHEMA = 1;
export const NORMAL_KEY_IDS = new Set(['door_lock:key', 'door_lock:golden_key']);
export const UNIVERSAL_KEY_ID = 'door_lock:universal_key';

export function decideInteraction({ lock, itemId, playerId, isSneaking }) {
  const universal = itemId === UNIVERSAL_KEY_ID;
  if (lock) {
    const authorized = universal || lock.owner === playerId;
    if (!authorized) return { action: 'DENY_LOCKED' };
    if (isSneaking) return { action: 'REMOVE_LOCK', expectedOwner: lock.owner };
    return { action: 'ALLOW_OPEN' };
  }
  if (universal || NORMAL_KEY_IDS.has(itemId)) return { action: 'CREATE_LOCK', owner: playerId };
  return { action: 'ALLOW_DEFAULT' };
}

export function decideBreak(lock) {
  return lock ? { action: 'DENY_LOCKED' } : { action: 'ALLOW_BREAK' };
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function decodeLegacyPayload(raw) {
  if (raw === undefined || raw === null || raw === '') return [];
  if (Array.isArray(raw)) return raw;
  if (typeof raw !== 'string') throw new Error('legacy payload must be a JSON array or encoded JSON array');
  const parsed = JSON.parse(raw);
  if (!Array.isArray(parsed)) throw new Error('legacy payload JSON must contain an array');
  return parsed;
}

function parseLegacyEntry(value, index, dimension) {
  if (typeof value !== 'string') return { error: 'entry_not_string', index, value };
  const match = /^(-?\d+),(-?\d+),(-?\d+)_(.+)$/.exec(value);
  if (!match || match[4].length === 0) return { error: 'malformed_legacy_entry', index, value };
  const [, x, y, z, credentialDigest] = match;
  return {
    index,
    value,
    location: `${dimension}:${Number(x)}:${Number(y)}:${Number(z)}`,
    credentialDigest,
  };
}

export function migrateLegacyState(rawLegacy, currentLocks = {}, options = {}) {
  const dimension = options.dimension ?? 'minecraft:overworld';
  if (dimension !== 'minecraft:overworld' && options.nonOverworldMappingApproved !== true) {
    return {
      locks: clone(currentLocks),
      quarantine: [{ error: 'non_overworld_mapping_requires_approval', dimension }],
      stats: { imported: 0, deduplicated: 0, quarantined: 1 },
    };
  }

  let entries;
  try {
    entries = decodeLegacyPayload(rawLegacy);
  } catch (error) {
    return {
      locks: clone(currentLocks),
      quarantine: [{ error: 'invalid_legacy_payload', detail: String(error) }],
      stats: { imported: 0, deduplicated: 0, quarantined: 1 },
    };
  }

  const locks = clone(currentLocks);
  const quarantine = [];
  const candidates = new Map();
  let deduplicated = 0;

  for (let index = 0; index < entries.length; index += 1) {
    const parsed = parseLegacyEntry(entries[index], index, dimension);
    if (parsed.error) {
      quarantine.push(parsed);
      continue;
    }
    const grouped = candidates.get(parsed.location) ?? [];
    grouped.push(parsed);
    candidates.set(parsed.location, grouped);
  }

  let imported = 0;
  for (const [location, grouped] of candidates.entries()) {
    const digests = new Set(grouped.map((entry) => entry.credentialDigest));
    if (digests.size > 1) {
      quarantine.push(...grouped.map((entry) => ({ ...entry, error: 'conflicting_credential_digests' })));
      continue;
    }
    const digest = grouped[0].credentialDigest;
    deduplicated += grouped.length - 1;
    const existing = locks[location];
    if (existing) {
      if (existing.credential_digest === digest && existing.owner === LEGACY_UNCLAIMED_OWNER) {
        deduplicated += 1;
      } else {
        quarantine.push(...grouped.map((entry) => ({ ...entry, error: 'current_state_collision' })));
      }
      continue;
    }
    locks[location] = {
      owner: LEGACY_UNCLAIMED_OWNER,
      schema: CURRENT_STATE_SCHEMA,
      credential_digest: digest,
      created_by_player_id: LEGACY_UNCLAIMED_OWNER,
      created_at_tick: 0,
      revision: 1,
    };
    imported += 1;
  }

  return {
    locks,
    quarantine,
    stats: { imported, deduplicated, quarantined: quarantine.length },
  };
}
