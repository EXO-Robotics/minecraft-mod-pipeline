import { system, world } from '@minecraft/server';
import { migrateLegacyState } from './doorlock-state.js';

const STATE_KEY = 'mccompiler:doorlock:locks:v1';
const LEGACY_STATE_KEY = 'mccompiler:doorlock:locks:v0';
const MIGRATION_KEY = 'mccompiler:doorlock:migration:v0-to-v1';
const QUARANTINE_KEY = 'mccompiler:doorlock:migration-quarantine:v0-to-v1';
const BOOT_KEY = 'mccompiler:doorlock:diagnostic_boot';
const NORMAL_KEYS = new Set(['door_lock:key', 'door_lock:golden_key']);
const UNIVERSAL_KEY = 'door_lock:universal_key';
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
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
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

function runLegacyMigration() {
  const journal = world.getDynamicProperty(MIGRATION_KEY);
  if (typeof journal === 'string' && journal.length > 0) {
    try {
      if (JSON.parse(journal)?.status === 'completed') {
        migrationReady = true;
        return;
      }
    } catch {
      console.warn('[mccompiler:doorlock] invalid migration journal; retrying migration');
    }
  }
  const current = readLocks();
  if (current === null) return;
  const result = migrateLegacyState(world.getDynamicProperty(LEGACY_STATE_KEY), current);
  writeLocks(result.locks);
  if (result.quarantine.length > 0) {
    world.setDynamicProperty(QUARANTINE_KEY, JSON.stringify(result.quarantine));
  }
  world.setDynamicProperty(MIGRATION_KEY, JSON.stringify({ schema: 1, status: 'completed', stats: result.stats }));
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
  const item = itemStack?.typeId;
  const universal = item === UNIVERSAL_KEY;
  const ownsLock = lock?.owner === player.id;

  if (lock) {
    if (!universal && !ownsLock) {
      event.cancel = true;
      deferMessage(player, 'This block is locked.');
      return;
    }
    if (player.isSneaking) {
      event.cancel = true;
      system.run(() => {
        const current = readLocks();
        if (current === null || current[location]?.owner !== lock.owner) return;
        delete current[location];
        writeLocks(current);
        player.sendMessage('Lock removed.');
      });
    }
    return;
  }

  if (!NORMAL_KEYS.has(item) && !universal) return;
  event.cancel = true;
  system.run(() => {
    const current = readLocks();
    if (current === null || current[location]) return;
    current[location] = { owner: player.id, schema: 1 };
    writeLocks(current);
    player.sendMessage('Block locked to your player identity. Sneak-use a key to remove it.');
  });
});

world.beforeEvents.playerBreakBlock.subscribe((event) => {
  if (!SUPPORTED_BLOCKS.has(event.block.typeId)) return;
  if (!migrationReady) {
    event.cancel = true;
    deferMessage(event.player, 'Lock data is still initializing.');
    return;
  }
  const locks = readLocks();
  if (locks === null || locks[blockKey(event.block)]) {
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
