import { system, world } from '@minecraft/server';
import { ActionFormData } from '@minecraft/server-ui';
import {
  buildOwnerLock, createLockIfAbsent, decideBreak, decideInteraction,
  migrateLegacyState, normalizeLockMap, removalConfirmed, removeLockIfRevision, validateLockMap,
} from './doorlock-state.js';

const STATE_KEY = 'mccompiler:doorlock:locks:v1';
const LEGACY_STATE_KEY = 'mccompiler:doorlock:locks:v0';
const MIGRATION_KEY = 'mccompiler:doorlock:migration:v0-to-v1';
const QUARANTINE_KEY = 'mccompiler:doorlock:migration-quarantine:v0-to-v1';
const BOOT_KEY = 'mccompiler:doorlock:diagnostic_boot';
const SUPPORTED_BLOCKS = new Set([
  'minecraft:acacia_door', 'minecraft:anvil', 'minecraft:barrel', 'minecraft:birch_door',
  'minecraft:chest', 'minecraft:copper_door', 'minecraft:dark_oak_door', 'minecraft:iron_door',
  'minecraft:jungle_door', 'minecraft:mangrove_door', 'minecraft:oak_door',
  'minecraft:spruce_door', 'minecraft:trapped_chest',
]);
let migrationReady = false;

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

function blockKey(block) {
  const p = block.location;
  return `${block.dimension.id}:${p.x}:${p.y}:${p.z}`;
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

function runLegacyMigration() {
  const current = readLocks();
  if (current === null) return;
  const journal = world.getDynamicProperty(MIGRATION_KEY);
  if (typeof journal === 'string' && journal.length > 0) {
    try {
      if (JSON.parse(journal)?.status === 'completed') {
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
  const result = migrateLegacyState(world.getDynamicProperty(LEGACY_STATE_KEY), current);
  writeLocks(result.locks);
  if (result.quarantine.length > 0) {
    world.setDynamicProperty(QUARANTINE_KEY, JSON.stringify(result.quarantine));
  }
  world.setDynamicProperty(MIGRATION_KEY, JSON.stringify({ schema: 1, status: 'completed', stats: result.stats }));
  if (result.stats.imported > 0) {
    const migrated = Object.values(result.locks).filter((record) => record.authorization_mode === 'legacy_credential').length;
    console.warn(`[mccompiler:doorlock] migration_nonempty_verified=${migrated}`);
  }
  migrationReady = true;
  console.warn(`[mccompiler:doorlock] migration_v0_v1=${JSON.stringify(result.stats)}`);
}

world.beforeEvents.playerInteractWithBlock.subscribe((event) => {
  const { block, itemStack, player } = event;
  if (!SUPPORTED_BLOCKS.has(block.typeId)) return;
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
  const location = blockKey(block);
  const lock = locks[location];
  const decision = decideInteraction({
    lock,
    itemId: itemStack?.typeId,
    playerId: player.id,
    isSneaking: player.isSneaking,
  });

  if (decision.action === 'DENY_LOCKED') {
    event.cancel = true;
    deferMessage(player, 'This block is locked.');
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
  if (decision.action === 'CREATE_LOCK') {
    event.cancel = true;
    system.run(() => {
      const current = readLocks();
      if (current === null) return;
      const record = buildOwnerLock(location, decision.owner, system.currentTick);
      const result = createLockIfAbsent(current, location, record);
      if (!result.changed) return;
      writeLocks(result.locks);
      player.sendMessage('Block locked to your player identity. Sneak-use a key to remove it.');
    });
  }
});

world.beforeEvents.playerBreakBlock.subscribe((event) => {
  if (!SUPPORTED_BLOCKS.has(event.block.typeId)) return;
  if (!migrationReady) {
    event.cancel = true;
    deferMessage(event.player, 'Lock data is still initializing.');
    return;
  }
  const locks = readLocks();
  if (locks === null || decideBreak(locks[blockKey(event.block)]).action === 'DENY_LOCKED') {
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
