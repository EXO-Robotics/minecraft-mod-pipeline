export const LEGACY_UNCLAIMED_OWNER = 'legacy-unclaimed';
export const CURRENT_STATE_SCHEMA = 1;
export const NORMAL_KEY_IDS = new Set(['door_lock:key', 'door_lock:golden_key']);
export const UNIVERSAL_KEY_ID = 'door_lock:universal_key';
export const BREAK_POLICY_REMOVE = 'remove';
export const BREAK_POLICY_DENY = 'deny';
const LOCKABLE_EXACT_IDS = new Set(['minecraft:chest', 'minecraft:trapped_chest']);
const LOCKABLE_SUFFIXES = ['_door', '_fence_gate', '_trapdoor', '_shulker_box'];
const SHA256_K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

function locationOrder(a, b) {
  return a.x - b.x || a.y - b.y || a.z - b.z;
}

export function canonicalLocationKey({ dimensionId, location, doorLowerLocation, pairedLocations = [] }) {
  let canonical = location;
  if (doorLowerLocation) canonical = doorLowerLocation;
  else if (pairedLocations.length === 1) canonical = [location, pairedLocations[0]].sort(locationOrder)[0];
  return `${dimensionId}:${canonical.x}:${canonical.y}:${canonical.z}`;
}

export function isLockableBlockType(typeId) {
  return typeof typeId === 'string'
    && (LOCKABLE_EXACT_IDS.has(typeId) || LOCKABLE_SUFFIXES.some((suffix) => typeId.endsWith(suffix)));
}

export function universalKeyAllowedForBlock(typeId) {
  return typeId !== 'minecraft:iron_door' && typeId !== 'minecraft:iron_trapdoor';
}

function utf8Bytes(text) {
  const bytes = [];
  for (const character of text) {
    const point = character.codePointAt(0);
    if (point <= 0x7f) bytes.push(point);
    else if (point <= 0x7ff) bytes.push(0xc0 | (point >>> 6), 0x80 | (point & 0x3f));
    else if (point <= 0xffff) bytes.push(0xe0 | (point >>> 12), 0x80 | ((point >>> 6) & 0x3f), 0x80 | (point & 0x3f));
    else bytes.push(0xf0 | (point >>> 18), 0x80 | ((point >>> 12) & 0x3f), 0x80 | ((point >>> 6) & 0x3f), 0x80 | (point & 0x3f));
  }
  return bytes;
}

function rotateRight(value, amount) {
  return (value >>> amount) | (value << (32 - amount));
}

export function sha256(text) {
  const bytes = utf8Bytes(text);
  const bitLength = bytes.length * 8;
  bytes.push(0x80);
  while (bytes.length % 64 !== 56) bytes.push(0);
  const high = Math.floor(bitLength / 0x100000000);
  const low = bitLength >>> 0;
  for (let shift = 24; shift >= 0; shift -= 8) bytes.push((high >>> shift) & 0xff);
  for (let shift = 24; shift >= 0; shift -= 8) bytes.push((low >>> shift) & 0xff);
  const hash = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
  const words = new Array(64);
  for (let offset = 0; offset < bytes.length; offset += 64) {
    for (let i = 0; i < 16; i += 1) {
      const j = offset + i * 4;
      words[i] = ((bytes[j] << 24) | (bytes[j + 1] << 16) | (bytes[j + 2] << 8) | bytes[j + 3]) >>> 0;
    }
    for (let i = 16; i < 64; i += 1) {
      const a = words[i - 15];
      const b = words[i - 2];
      const s0 = rotateRight(a, 7) ^ rotateRight(a, 18) ^ (a >>> 3);
      const s1 = rotateRight(b, 17) ^ rotateRight(b, 19) ^ (b >>> 10);
      words[i] = (words[i - 16] + s0 + words[i - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, h] = hash;
    for (let i = 0; i < 64; i += 1) {
      const sum1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
      const choice = (e & f) ^ (~e & g);
      const temp1 = (h + sum1 + choice + SHA256_K[i] + words[i]) >>> 0;
      const sum0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
      const majority = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (sum0 + majority) >>> 0;
      h = g; g = f; f = e; e = (d + temp1) >>> 0; d = c; c = b; b = a; a = (temp1 + temp2) >>> 0;
    }
    const state = [a, b, c, d, e, f, g, h];
    for (let i = 0; i < 8; i += 1) hash[i] = (hash[i] + state[i]) >>> 0;
  }
  return hash.map((value) => value.toString(16).padStart(8, '0')).join('');
}

export function digestCredential(value) {
  if (typeof value !== 'string') return { ok: false, error: 'Credential must be text.' };
  const secret = value.trim();
  if (secret.length < 4 || secret.length > 64) return { ok: false, error: 'Credential must contain 4 to 64 characters.' };
  if (/\p{Cc}/u.test(secret)) return { ok: false, error: 'Credential contains unsupported control characters.' };
  return { ok: true, digest: sha256(`mccompiler:doorlock:v1:${secret}`) };
}

export function credentialFormResult(response) {
  if (response?.canceled !== false) return { ok: false, canceled: true };
  return digestCredential(response.formValues?.[0]);
}

export function decideInteraction({ lock, itemId, playerId, isSneaking, credentialDigest, universalAllowed = true }) {
  const universal = itemId === UNIVERSAL_KEY_ID && universalAllowed;
  if (lock) {
    const credentialMode = lock.authorization_mode === 'shared_credential' || lock.authorization_mode === 'legacy_credential';
    const ownerMode = lock.authorization_mode === 'owner_identity';
    const authorized = universal || (ownerMode && lock.owner === playerId) || (credentialMode && credentialDigest === lock.credential_digest);
    if (!authorized) return { action: 'DENY_LOCKED' };
    if (isSneaking) return { action: 'REMOVE_LOCK', expectedOwner: lock.owner, expectedRevision: lock.revision };
    return { action: 'ALLOW_OPEN' };
  }
  if (itemId === UNIVERSAL_KEY_ID) return { action: 'ALLOW_DEFAULT' };
  if (NORMAL_KEY_IDS.has(itemId) && !credentialDigest) return { action: 'DENY_UNCONFIGURED' };
  if (NORMAL_KEY_IDS.has(itemId)) return { action: 'CREATE_CREDENTIAL_LOCK', owner: playerId, credentialDigest };
  return { action: 'ALLOW_DEFAULT' };
}

export function normalizeBreakPolicy(value) {
  if (value === undefined) return { policy: BREAK_POLICY_REMOVE, valid: true, usedDefault: true };
  if (value === BREAK_POLICY_REMOVE || value === BREAK_POLICY_DENY) {
    return { policy: value, valid: true, usedDefault: false };
  }
  return { policy: BREAK_POLICY_DENY, valid: false, usedDefault: false };
}

export function decideBreak(lock, policy = BREAK_POLICY_REMOVE) {
  if (!lock) return { action: 'ALLOW_BREAK' };
  if (policy === BREAK_POLICY_REMOVE) {
    return {
      action: 'ALLOW_BREAK_REMOVE_LOCK',
      expectedOwner: lock.owner,
      expectedRevision: lock.revision,
    };
  }
  return { action: 'DENY_LOCKED' };
}

export function removalConfirmed(response) {
  return response?.canceled === false && response.selection === 0;
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
    } else if (record.authorization_mode === 'shared_credential') {
      if (typeof record.owner !== 'string' || record.owner.length === 0 || record.owner === LEGACY_UNCLAIMED_OWNER) errors.push(`${location}: credential lock creator is invalid`);
      if (typeof record.credential_digest !== 'string' || !/^[0-9a-f]{64}$/.test(record.credential_digest)) errors.push(`${location}: SHA-256 credential digest is required`);
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

export function buildCredentialLock(location, credentialDigest, creator, createdAtTick) {
  return {
    schema: CURRENT_STATE_SCHEMA,
    ...locationFields(location),
    authorization_mode: 'shared_credential',
    owner: creator,
    credential_digest: credentialDigest,
    created_by_player_id: creator,
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

function payloadDigest(value) {
  return sha256(JSON.stringify(value));
}

export function prepareLegacyMigration(rawLegacy, currentLocks = {}, options = {}) {
  const result = migrateLegacyState(rawLegacy, currentLocks, options);
  return {
    ...result,
    journal: {
      schema: 1,
      status: 'prepared',
      legacy_digest: payloadDigest(rawLegacy ?? null),
      before_digest: payloadDigest(currentLocks),
      result_digest: payloadDigest(result.locks),
      quarantine_digest: payloadDigest(result.quarantine),
      stats: result.stats,
    },
  };
}

export function resumePreparedMigration(rawLegacy, currentLocks, journal, options = {}) {
  if (!journal || journal.schema !== 1 || journal.status !== 'prepared') {
    return { ok: false, error: 'invalid_prepared_journal' };
  }
  if (journal.legacy_digest !== payloadDigest(rawLegacy ?? null)) {
    return { ok: false, error: 'legacy_payload_changed' };
  }
  const currentDigest = payloadDigest(currentLocks);
  if (currentDigest !== journal.before_digest && currentDigest !== journal.result_digest) {
    return { ok: false, error: 'current_state_diverged' };
  }
  const result = migrateLegacyState(rawLegacy, currentLocks, options);
  if (payloadDigest(result.locks) !== journal.result_digest) {
    return { ok: false, error: 'result_digest_mismatch' };
  }
  if (payloadDigest(result.quarantine) !== journal.quarantine_digest) {
    return { ok: false, error: 'quarantine_digest_mismatch' };
  }
  return {
    ok: true,
    locks: result.locks,
    quarantine: result.quarantine,
    stats: journal.stats,
    journal: { ...journal, status: 'completed' },
  };
}
