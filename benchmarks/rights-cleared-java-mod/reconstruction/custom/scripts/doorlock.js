import { system, world } from '@minecraft/server';
import { ActionFormData, ModalFormData } from '@minecraft/server-ui';
import {
  buildCredentialLock, canonicalLocationKey, createLockIfAbsent, credentialFormResult,
  decideBreak, decideInteraction, isLockableBlockType, NORMAL_KEY_IDS, normalizeLockMap,
  prepareLegacyMigration, removalConfirmed, removeLockIfRevision, resumePreparedMigration,
  universalKeyAllowedForBlock, validateLockMap,
} from './doorlock-state.js';

const STATE_KEY = 'mccompiler:doorlock:locks:v1';
const LEGACY_STATE_KEY = 'mccompiler:doorlock:locks:v0';
const MIGRATION_KEY = 'mccompiler:doorlock:migration:v0-to-v1';
const QUARANTINE_KEY = 'mccompiler:doorlock:migration-quarantine:v0-to-v1';
const BOOT_KEY = 'mccompiler:doorlock:diagnostic_boot';
const CHEST_IDS = new Set(['minecraft:chest', 'minecraft:trapped_chest']);
let migrationReady = false;

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
  const encoded = world.getDynamicProperty(STATE_KEY);
  if (typeof encoded !== 'string' || encoded.length === 0) return {};
  try {
    const parsed = JSON.parse(encoded);
    const normalized = normalizeLockMap(parsed);
    const errors = validateLockMap(normalized.locks);
    if (errors.length > 0) {
      console.warn(`[mccompiler:doorlock] invalid lock state: ${errors.join('; ')}`);
      return null;
    }
    return normalized.locks;
  } catch {
    console.warn('[mccompiler:doorlock] invalid lock state; writes remain fail-closed');
    return null;
  }
}

function writeLocks(locks) {
  world.setDynamicProperty(STATE_KEY, JSON.stringify(locks));
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

function toggleIronOpen(block, player) {
  const open = state(block, 'minecraft:open_bit');
  if (typeof open !== 'boolean') {
    player.sendMessage('This iron block could not be toggled safely.');
    return;
  }
  const targets = [block];
  if (block.typeId === 'minecraft:iron_door') {
    const upper = state(block, 'minecraft:upper_block_bit') === true;
    const otherLocation = { ...block.location, y: block.location.y + (upper ? -1 : 1) };
    try {
      const other = block.dimension.getBlock(otherLocation);
      if (!other || other.typeId !== block.typeId) {
        player.sendMessage('This iron door is incomplete and was not toggled.');
        return;
      }
      targets.push(other);
    } catch {
      player.sendMessage('This iron door could not be toggled safely.');
      return;
    }
  }
  try {
    for (const target of targets) {
      target.setPermutation(target.permutation.withState('minecraft:open_bit', !open));
    }
  } catch {
    player.sendMessage('This iron block could not be toggled safely.');
  }
}

export function canonicalBlockKey(block) {
  const { dimension, location, typeId } = block;
  if (typeId.endsWith('_door') && state(block, 'minecraft:upper_block_bit') === true) {
    const lowerLocation = { x: location.x, y: location.y - 1, z: location.z };
    try {
      const lower = dimension.getBlock(lowerLocation);
      if (lower?.typeId === typeId && state(lower, 'minecraft:upper_block_bit') === false) {
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
  if (!NORMAL_KEY_IDS.has(event.itemStack.typeId) || event.source.typeId !== 'minecraft:player') return;
  system.run(() => configureCredential(event.source, event.itemStack.typeId));
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
    system.run(() => toggleIronOpen(block, player));
    return;
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
      );
      const result = createLockIfAbsent(current, location, record);
      if (!result.changed) return;
      writeLocks(result.locks);
      player.sendMessage('Block locked with this shared credential. Sneak-use a matching key to remove it.');
    });
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
  if (locks === null || decideBreak(locks[canonicalBlockKey(event.block)]).action === 'DENY_LOCKED') {
    event.cancel = true;
    deferMessage(event.player, 'Unlock this block before breaking it.');
  }
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
