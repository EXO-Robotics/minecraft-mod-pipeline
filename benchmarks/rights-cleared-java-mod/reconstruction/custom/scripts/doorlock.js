import { system, world } from '@minecraft/server';
import { ActionFormData, ModalFormData } from '@minecraft/server-ui';
import {
  BREAK_POLICY_DENY, BREAK_POLICY_REMOVE, buildCredentialLock, canonicalLocationKey,
  createLockIfAbsent, credentialFormResult,
  decideBreak, decideInteraction, decideOpenReconciliation, isLockableBlockType,
  isRedstoneProtectedBlockType, NORMAL_KEY_IDS, normalizeLockMap,
  normalizeBreakPolicy, prepareLegacyMigration, removalConfirmed, removeLockIfRevision,
  resumePreparedMigration, UNIVERSAL_KEY_ID, universalKeyAllowedForBlock,
  updateProtectedOpenIfRevision, validateLockMap,
} from './doorlock-state.js';

const STATE_KEY = 'mccompiler:doorlock:locks:v1';
const LEGACY_STATE_KEY = 'mccompiler:doorlock:locks:v0';
const MIGRATION_KEY = 'mccompiler:doorlock:migration:v0-to-v1';
const QUARANTINE_KEY = 'mccompiler:doorlock:migration-quarantine:v0-to-v1';
const BOOT_KEY = 'mccompiler:doorlock:diagnostic_boot';
const BREAK_POLICY_KEY = 'mccompiler:doorlock:break-policy:v1';
const CHEST_IDS = new Set(['minecraft:chest', 'minecraft:trapped_chest']);
const REDSTONE_RECONCILE_BUDGET = 32;
const pendingBreaks = new Map();
const pendingAuthorizedOpens = new Map();
const pendingAuthorizedLocations = new Map();
let migrationReady = false;
let redstoneCursor = 0;
let lockCacheReady = false;
let lockCache = null;
let lockLocationCache = [];

function credentialProperty(itemId) {
  if (itemId === 'door_lock:key') return 'mccompiler:doorlock:key-digest:normal';
  if (itemId === 'door_lock:golden_key') return 'mccompiler:doorlock:key-digest:golden';
  return null;
}

function playerCredential(player, itemId) {
  const property = credentialProperty(itemId);
  if (!property) return null;
  const value = player.getDynamicProperty(property);
  return typeof value === 'string' && /^[0-9a-f]{64}$/.test(value) ? value : null;
}

function readLocks() {
  if (lockCacheReady) return lockCache;
  const encoded = world.getDynamicProperty(STATE_KEY);
  if (typeof encoded !== 'string' || encoded.length === 0) {
    lockCacheReady = true;
    lockCache = {};
    lockLocationCache = [];
    return lockCache;
  }
  try {
    const parsed = JSON.parse(encoded);
    const normalized = normalizeLockMap(parsed);
    const errors = validateLockMap(normalized.locks);
    if (errors.length > 0) {
      console.warn(`[mccompiler:doorlock] invalid lock state: ${errors.join('; ')}`);
      lockCacheReady = true;
      lockCache = null;
      lockLocationCache = [];
      return null;
    }
    lockCacheReady = true;
    lockCache = normalized.locks;
    lockLocationCache = Object.keys(normalized.locks).sort();
    return lockCache;
  } catch {
    console.warn('[mccompiler:doorlock] invalid lock state; writes remain fail-closed');
    lockCacheReady = true;
    lockCache = null;
    lockLocationCache = [];
    return null;
  }
}

function writeLocks(locks) {
  world.setDynamicProperty(STATE_KEY, JSON.stringify(locks));
  lockCacheReady = true;
  lockCache = locks;
  lockLocationCache = Object.keys(locks).sort();
}

function state(block, name) {
  try {
    return block.permutation.getState(name);
  } catch {
    return undefined;
  }
}

function inventorySize(block) {
  try {
    return block.getComponent('inventory')?.container?.size;
  } catch {
    return undefined;
  }
}

function isIronOpenable(typeId) {
  return typeId === 'minecraft:iron_door' || typeId === 'minecraft:iron_trapdoor';
}

function setOpenState(block, open) {
  const targets = [block];
  if (block.typeId.endsWith('_door') && !block.typeId.endsWith('_trapdoor')) {
    const upper = state(block, 'upper_block_bit') === true;
    const otherLocation = { ...block.location, y: block.location.y + (upper ? -1 : 1) };
    const other = block.dimension.getBlock(otherLocation);
    if (!other || other.typeId !== block.typeId) return false;
    targets.push(other);
  }
  for (const target of targets) {
    target.setPermutation(target.permutation.withState('open_bit', open));
  }
  return true;
}

function toggleIronOpen(block, player) {
  const open = state(block, 'open_bit');
  if (typeof open !== 'boolean') {
    player.sendMessage('This iron block could not be toggled safely.');
    return undefined;
  }
  try {
    if (!setOpenState(block, !open)) {
      player.sendMessage('This iron door is incomplete and was not toggled.');
      return undefined;
    }
    return !open;
  } catch {
    player.sendMessage('This iron block could not be toggled safely.');
    return undefined;
  }
}

export function canonicalBlockKey(block) {
  const { dimension, location, typeId } = block;
  if (typeId.endsWith('_door') && state(block, 'upper_block_bit') === true) {
    const lowerLocation = { x: location.x, y: location.y - 1, z: location.z };
    try {
      const lower = dimension.getBlock(lowerLocation);
      if (lower?.typeId === typeId && state(lower, 'upper_block_bit') === false) {
        return canonicalLocationKey({ dimensionId: dimension.id, location, doorLowerLocation: lowerLocation });
      }
    } catch {
      return canonicalLocationKey({ dimensionId: dimension.id, location });
    }
  }
  if (CHEST_IDS.has(typeId) && inventorySize(block) === 54) {
    const direction = state(block, 'minecraft:cardinal_direction');
    const offsets = direction === 'north' || direction === 'south'
      ? [{ x: -1, z: 0 }, { x: 1, z: 0 }]
      : direction === 'east' || direction === 'west'
        ? [{ x: 0, z: -1 }, { x: 0, z: 1 }]
        : [];
    const partners = [];
    for (const offset of offsets) {
      const candidateLocation = { x: location.x + offset.x, y: location.y, z: location.z + offset.z };
      try {
        const candidate = dimension.getBlock(candidateLocation);
        if (candidate?.typeId === typeId
          && state(candidate, 'minecraft:cardinal_direction') === direction
          && inventorySize(candidate) === 54) partners.push(candidateLocation);
      } catch {
        // An unloaded or invalid adjacent block cannot be treated as an authoritative partner.
      }
    }
    if (partners.length === 1) {
      return canonicalLocationKey({ dimensionId: dimension.id, location, pairedLocations: partners });
    }
  }
  return canonicalLocationKey({ dimensionId: dimension.id, location });
}

function deferMessage(player, message) {
  system.run(() => player.sendMessage(message));
}

function rawBreakKey(block) {
  const { x, y, z } = block.location;
  return `${block.dimension.id}:${x}:${y}:${z}`;
}

function readBreakPolicy() {
  const result = normalizeBreakPolicy(world.getDynamicProperty(BREAK_POLICY_KEY));
  if (!result.valid) console.warn('[mccompiler:doorlock] invalid break policy; locked breaks are denied');
  return result.policy;
}

function authorizedOpenKey(player, location) {
  return `${player.id}:${location}`;
}

function updateProtectedOpen(location, expectedOwner, expectedRevision, open) {
  const locks = readLocks();
  if (locks === null) return;
  const result = updateProtectedOpenIfRevision(
    locks, location, expectedOwner, expectedRevision, open,
  );
  if (result.changed) writeLocks(result.locks);
}

function reconcileLockedOpenables() {
  if (!migrationReady) return;
  const locks = readLocks();
  if (locks === null) return;
  const locations = lockLocationCache;
  if (locations.length === 0) return;
  let working = locks;
  let stateChanged = false;
  const count = Math.min(REDSTONE_RECONCILE_BUDGET, locations.length);
  for (let used = 0; used < count; used += 1) {
    const location = locations[redstoneCursor % locations.length];
    redstoneCursor = (redstoneCursor + 1) % locations.length;
    const record = working[location];
    if (!record) continue;
    if (pendingAuthorizedLocations.has(location)) continue;
    let block;
    try {
      block = world.getDimension(record.dimension).getBlock(record.position);
      if (!block || !isRedstoneProtectedBlockType(block.typeId)) continue;
    } catch {
      continue;
    }
    const decision = decideOpenReconciliation(record.protected_open, state(block, 'open_bit'));
    if (decision.action === 'CAPTURE_OPEN_STATE') {
      const result = updateProtectedOpenIfRevision(
        working, location, record.owner, record.revision, decision.open,
      );
      if (result.changed) {
        working = result.locks;
        stateChanged = true;
      }
    } else if (decision.action === 'RESTORE_OPEN_STATE') {
      try {
        setOpenState(block, decision.open);
      } catch {
        // Unloaded or invalid block locations are retried by a later bounded pass.
      }
    }
  }
  if (stateChanged) writeLocks(working);
}

async function configureBreakPolicy(player) {
  const current = readBreakPolicy();
  try {
    const response = await new ActionFormData()
      .title('Locked-block break policy')
      .body(`Current policy: ${current === BREAK_POLICY_REMOVE ? 'break and remove lock' : 'deny break'}`)
      .button('Break and remove lock')
      .button('Deny locked breaks')
      .button('Keep current policy')
      .show(player);
    if (response.canceled || (response.selection !== 0 && response.selection !== 1)) return;
    const selected = response.selection === 0 ? BREAK_POLICY_REMOVE : BREAK_POLICY_DENY;
    world.setDynamicProperty(BREAK_POLICY_KEY, selected);
    player.sendMessage(selected === BREAK_POLICY_REMOVE
      ? 'Locked blocks may be broken; their lock is removed after a successful break.'
      : 'Locked blocks cannot be broken until unlocked.');
  } catch (error) {
    player.sendMessage('Break policy configuration could not be opened. No changes were made.');
    console.warn(`[mccompiler:doorlock] break_policy_form_failed=${String(error)}`);
  }
}

async function confirmLockRemoval(player) {
  try {
    const response = await new ActionFormData()
      .title('Remove lock?')
      .body('This block will become available to every player.')
      .button('Remove lock')
      .button('Keep lock')
      .show(player);
    return removalConfirmed(response);
  } catch (error) {
    player.sendMessage('Lock removal confirmation could not be opened. No changes were made.');
    console.warn(`[mccompiler:doorlock] removal_form_failed=${String(error)}`);
    return false;
  }
}

async function configureCredential(player, itemId) {
  const property = credentialProperty(itemId);
  if (!property) return;
  try {
    const response = await new ModalFormData()
      .title('Configure lock key')
      .textField('Shared credential', '4 to 64 characters')
      .submitButton('Save credential')
      .show(player);
    const result = credentialFormResult(response);
    if (result.canceled) return;
    if (!result.ok) {
      player.sendMessage(result.error);
      return;
    }
    player.setDynamicProperty(property, result.digest);
    player.sendMessage('Key credential saved. The credential itself was not stored.');
  } catch (error) {
    player.sendMessage('Key configuration could not be opened. No changes were made.');
    console.warn(`[mccompiler:doorlock] credential_form_failed=${String(error)}`);
  }
}

function runLegacyMigration() {
  const current = readLocks();
  if (current === null) return;
  const rawLegacy = world.getDynamicProperty(LEGACY_STATE_KEY);
  const encodedJournal = world.getDynamicProperty(MIGRATION_KEY);
  let journal;
  if (typeof encodedJournal === 'string' && encodedJournal.length > 0) {
    try {
      journal = JSON.parse(encodedJournal);
      if (journal?.status === 'completed') {
        writeLocks(current);
        const migrated = Object.values(current).filter((record) => record.authorization_mode === 'legacy_credential').length;
        console.warn(`[mccompiler:doorlock] migration_state_records=${migrated}`);
        migrationReady = true;
        return;
      }
    } catch {
      console.warn('[mccompiler:doorlock] invalid migration journal; retrying migration');
    }
  }
  let transaction;
  if (journal?.status === 'prepared') {
    transaction = resumePreparedMigration(rawLegacy, current, journal);
    if (!transaction.ok) throw new Error(`prepared migration recovery failed: ${transaction.error}`);
  } else {
    transaction = prepareLegacyMigration(rawLegacy, current);
    world.setDynamicProperty(MIGRATION_KEY, JSON.stringify(transaction.journal));
  }
  world.setDynamicProperty(
    QUARANTINE_KEY,
    transaction.quarantine.length > 0 ? JSON.stringify(transaction.quarantine) : undefined,
  );
  writeLocks(transaction.locks);
  world.setDynamicProperty(MIGRATION_KEY, JSON.stringify({ ...transaction.journal, status: 'completed' }));
  if (transaction.stats.imported > 0) {
    const migrated = Object.values(transaction.locks).filter((record) => record.authorization_mode === 'legacy_credential').length;
    console.warn(`[mccompiler:doorlock] migration_nonempty_verified=${migrated}`);
  }
  migrationReady = true;
  console.warn(`[mccompiler:doorlock] migration_v0_v1=${JSON.stringify(transaction.stats)}`);
}

world.afterEvents.itemUse.subscribe((event) => {
  if (event.source.typeId !== 'minecraft:player') return;
  if (NORMAL_KEY_IDS.has(event.itemStack.typeId)) {
    system.run(() => configureCredential(event.source, event.itemStack.typeId));
  } else if (event.itemStack.typeId === UNIVERSAL_KEY_ID) {
    system.run(() => configureBreakPolicy(event.source));
  }
});

world.beforeEvents.playerInteractWithBlock.subscribe((event) => {
  const { block, itemStack, player } = event;
  if (!isLockableBlockType(block.typeId)) return;
  if (!migrationReady) {
    event.cancel = true;
    deferMessage(player, 'Lock data is still initializing.');
    return;
  }
  const locks = readLocks();
  if (locks === null) {
    event.cancel = true;
    deferMessage(player, 'Lock data needs administrator repair.');
    return;
  }
  const location = canonicalBlockKey(block);
  const lock = locks[location];
  const decision = decideInteraction({
    lock,
    itemId: itemStack?.typeId,
    playerId: player.id,
    isSneaking: player.isSneaking,
    credentialDigest: playerCredential(player, itemStack?.typeId),
    universalAllowed: universalKeyAllowedForBlock(block.typeId),
  });

  if (decision.action === 'DENY_LOCKED') {
    event.cancel = true;
    deferMessage(player, 'This block is locked.');
    return;
  }
  if (decision.action === 'DENY_UNCONFIGURED') {
    event.cancel = true;
    deferMessage(player, 'Configure this key by using it away from a block first.');
    return;
  }
  if (decision.action === 'ALLOW_OPEN' && isIronOpenable(block.typeId)) {
    event.cancel = true;
    system.run(() => {
      const open = toggleIronOpen(block, player);
      if (typeof open === 'boolean') {
        updateProtectedOpen(location, lock.owner, lock.revision, open);
      }
    });
    return;
  }
  if (decision.action === 'ALLOW_OPEN' && isRedstoneProtectedBlockType(block.typeId)) {
    const key = authorizedOpenKey(player, location);
    const pending = {
      location,
      expectedOwner: lock.owner,
      expectedRevision: lock.revision,
    };
    pendingAuthorizedOpens.set(key, pending);
    pendingAuthorizedLocations.set(location, pending);
    system.runTimeout(() => {
      if (pendingAuthorizedOpens.get(key) === pending) pendingAuthorizedOpens.delete(key);
      if (pendingAuthorizedLocations.get(location) === pending) pendingAuthorizedLocations.delete(location);
    }, 4);
  }
  if (decision.action === 'REMOVE_LOCK') {
    event.cancel = true;
    system.run(async () => {
      if (!await confirmLockRemoval(player)) return;
      const current = readLocks();
      if (current === null) return;
      const result = removeLockIfRevision(
        current, location, decision.expectedOwner, decision.expectedRevision,
      );
      if (!result.changed) return;
      writeLocks(result.locks);
      player.sendMessage('Lock removed.');
    });
    return;
  }
  if (decision.action === 'CREATE_CREDENTIAL_LOCK') {
    event.cancel = true;
    system.run(() => {
      const current = readLocks();
      if (current === null) return;
      const record = buildCredentialLock(
        location, decision.credentialDigest, decision.owner, system.currentTick,
        state(block, 'open_bit'),
      );
      const result = createLockIfAbsent(current, location, record);
      if (!result.changed) return;
      writeLocks(result.locks);
      player.sendMessage('Block locked with this shared credential. Sneak-use a matching key to remove it.');
    });
  }
});

world.afterEvents.playerInteractWithBlock.subscribe((event) => {
  if (!isRedstoneProtectedBlockType(event.block.typeId)) return;
  const location = canonicalBlockKey(event.block);
  const key = authorizedOpenKey(event.player, location);
  const pending = pendingAuthorizedOpens.get(key);
  if (!pending) return;
  pendingAuthorizedOpens.delete(key);
  if (pendingAuthorizedLocations.get(location) === pending) pendingAuthorizedLocations.delete(location);
  const open = state(event.block, 'open_bit');
  if (typeof open === 'boolean') {
    updateProtectedOpen(
      pending.location, pending.expectedOwner, pending.expectedRevision, open,
    );
  }
});

world.beforeEvents.playerBreakBlock.subscribe((event) => {
  if (!isLockableBlockType(event.block.typeId)) return;
  if (!migrationReady) {
    event.cancel = true;
    deferMessage(event.player, 'Lock data is still initializing.');
    return;
  }
  const locks = readLocks();
  if (locks === null) {
    event.cancel = true;
    deferMessage(event.player, 'Unlock this block before breaking it.');
    return;
  }
  const location = canonicalBlockKey(event.block);
  const decision = decideBreak(locks[location], readBreakPolicy());
  if (decision.action === 'DENY_LOCKED') {
    event.cancel = true;
    deferMessage(event.player, 'Unlock this block before breaking it.');
    return;
  }
  if (decision.action === 'ALLOW_BREAK_REMOVE_LOCK') {
    const key = rawBreakKey(event.block);
    const pending = {
      location,
      expectedOwner: decision.expectedOwner,
      expectedRevision: decision.expectedRevision,
    };
    pendingBreaks.set(key, pending);
    system.runTimeout(() => {
      if (pendingBreaks.get(key) === pending) pendingBreaks.delete(key);
    }, 40);
  }
});

world.afterEvents.playerBreakBlock.subscribe((event) => {
  const key = rawBreakKey(event.block);
  const pending = pendingBreaks.get(key);
  if (!pending) return;
  pendingBreaks.delete(key);
  const locks = readLocks();
  if (locks === null) return;
  const result = removeLockIfRevision(
    locks, pending.location, pending.expectedOwner, pending.expectedRevision,
  );
  if (result.changed) writeLocks(result.locks);
});

system.run(() => {
  try {
    runLegacyMigration();
  } catch (error) {
    migrationReady = false;
    console.warn(`[mccompiler:doorlock] migration_v0_v1_failed=${String(error)}`);
  }
  const previous = Number(world.getDynamicProperty(BOOT_KEY)) || 0;
  const current = previous + 1;
  world.setDynamicProperty(BOOT_KEY, current);
  console.warn(`[mccompiler:doorlock] persistent_boot=${current}`);
});

system.runInterval(reconcileLockedOpenables, 1);
