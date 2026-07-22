export const LEGACY_UNCLAIMED_OWNER = 'legacy-unclaimed';
export const CURRENT_STATE_SCHEMA = 1;
export const NORMAL_KEY_IDS = new Set(['door_lock:key', 'door_lock:golden_key']);
export const UNIVERSAL_KEY_ID = 'door_lock:universal_key';

export function decideInteraction({ lock, itemId, playerId, isSneaking }) {
  const universal = itemId === UNIVERSAL_KEY_ID;
  if (lock) {
    const authorized = universal || lock.owner === playerId;
    if (!authorized) return { action: 'DENY_LOCKED' };
    if (isSneaking) return { action: 'REMOVE_LOCK', expectedOwner: lock.owner, expectedRevision: lock.revision };
    return { action: 'ALLOW_OPEN' };
  }
  if (universal || NORMAL_KEY_IDS.has(itemId)) return { action: 'CREATE_LOCK', owner: playerId };
  return { action: 'ALLOW_DEFAULT' };
}

export function decideBreak(lock) {
  return lock ? { action: 'DENY_LOCKED' } : { action: 'ALLOW_BREAK' };
}

function locationFields(location) {
  const match = /^(.+):(-?\d+):(-?\d+):(-?\d+)$/.exec(location);
  if (!match) throw new Error(`invalid lock location: ${location}`);
  return {
    dimension: match[1],
    position: { x: Number(match[2]), y: Number(match[3]), z: Number(match[4]) },
  };
}

export function validateLockMap(locks) {
  const errors = [];
  if (!locks || typeof locks !== 'object' || Array.isArray(locks)) return ['lock map must be an object'];
  for (const [location, record] of Object.entries(locks)) {
    let expected;
    try {
      expected = locationFields(location);
    } catch (error) {
      errors.push(String(error));
      continue;
    }
    if (!record || typeof record !== 'object' || Array.isArray(record)) {
      errors.push(`${location}: record must be an object`);
      continue;
    }
    if (record.schema !== CURRENT_STATE_SCHEMA) errors.push(`${location}: schema must be 1`);
    if (record.dimension !== expected.dimension) errors.push(`${location}: dimension does not match map key`);
    if (!record.position || record.position.x !== expected.position.x || record.position.y !== expected.position.y || record.position.z !== expected.position.z) {
      errors.push(`${location}: position does not match map key`);
    }
    if (!Number.isInteger(record.revision) || record.revision < 1) errors.push(`${location}: revision must be positive`);
    if (!Number.isInteger(record.created_at_tick) || record.created_at_tick < 0) errors.push(`${location}: created_at_tick must be nonnegative`);
    if (typeof record.created_by_player_id !== 'string' || record.created_by_player_id.length === 0) errors.push(`${location}: creator identity is required`);
    if (record.authorization_mode === 'owner_identity') {
      if (typeof record.owner !== 'string' || record.owner.length === 0 || record.owner === LEGACY_UNCLAIMED_OWNER) errors.push(`${location}: owner identity is invalid`);
    } else if (record.authorization_mode === 'legacy_credential') {
      if (record.owner !== LEGACY_UNCLAIMED_OWNER) errors.push(`${location}: legacy record must remain unclaimed`);
      if (typeof record.credential_digest !== 'string' || record.credential_digest.length === 0) errors.push(`${location}: legacy credential digest is required`);
    } else {
      errors.push(`${location}: authorization mode is unsupported`);
    }
  }
  return errors;
}

export function normalizeLockMap(locks) {
  if (!locks || typeof locks !== 'object' || Array.isArray(locks)) return { locks, upgraded: false };
  const next = { ...locks };
  let upgraded = false;
  for (const [location, record] of Object.entries(locks)) {
    if (!record || typeof record !== 'object' || Array.isArray(record)) continue;
    const sparseOwnerV1 = record.schema === 1 && typeof record.owner === 'string'
      && record.owner !== LEGACY_UNCLAIMED_OWNER && record.authorization_mode === undefined;
    if (!sparseOwnerV1) continue;
    const fields = locationFields(location);
    next[location] = {
      schema: CURRENT_STATE_SCHEMA,
      ...fields,
      authorization_mode: 'owner_identity',
      owner: record.owner,
      created_by_player_id: record.owner,
      created_at_tick: 0,
      revision: 1,
    };
    upgraded = true;
  }
  return { locks: next, upgraded };
}

export function buildOwnerLock(location, owner, createdAtTick) {
  return {
    schema: CURRENT_STATE_SCHEMA,
    ...locationFields(location),
    authorization_mode: 'owner_identity',
    owner,
    created_by_player_id: owner,
    created_at_tick: createdAtTick,
    revision: 1,
  };
}

export function createLockIfAbsent(locks, location, record) {
  if (locks[location]) return { changed: false, locks };
  return { changed: true, locks: { ...locks, [location]: record } };
}

export function removeLockIfRevision(locks, location, expectedOwner, expectedRevision) {
  const current = locks[location];
  if (!current || current.owner !== expectedOwner || current.revision !== expectedRevision) {
    return { changed: false, locks };
  }
  const next = { ...locks };
  delete next[location];
  return { changed: true, locks: next };
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
      ...locationFields(location),
      owner: LEGACY_UNCLAIMED_OWNER,
      schema: CURRENT_STATE_SCHEMA,
      authorization_mode: 'legacy_credential',
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
