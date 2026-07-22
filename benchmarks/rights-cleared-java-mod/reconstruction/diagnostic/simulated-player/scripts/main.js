import { GameMode, system, world } from '@minecraft/server';
import { spawnSimulatedPlayer } from '@minecraft/server-gametest';

const TARGET = { x: 10, y: 64, z: 10 };
const ARM_MARKER = { x: 11, y: 64, z: 10 };
const observed = {
  playerId: undefined,
  breakBefore: false,
  breakAfter: false,
};

function isDiagnosticPlayer(player) {
  return observed.playerId !== undefined && player?.id === observed.playerId;
}

world.beforeEvents.playerBreakBlock.subscribe((event) => {
  if (isDiagnosticPlayer(event.player)) observed.breakBefore = true;
});
world.afterEvents.playerBreakBlock.subscribe((event) => {
  if (isDiagnosticPlayer(event.player)) observed.breakAfter = true;
});

function fail(message) {
  throw new Error(`[mccompiler:simulated-player] ${message}`);
}

function runWhenArmed() {
  try {
    const dimension = world.getDimension('minecraft:overworld');
    if (dimension.getBlock(ARM_MARKER)?.typeId !== 'minecraft:gold_block') {
      system.runTimeout(runWhenArmed, 20);
      return;
    }
    const player = spawnSimulatedPlayer(
      { dimension, x: 10.5, y: 65, z: 8.5 },
      'MCCompilerAdapterBot',
      GameMode.creative,
    );
    observed.playerId = player.id;
    const breakStarted = player.breakBlock(TARGET);
    console.warn(`[mccompiler:simulated-player] break_started=${breakStarted}`);
    system.runTimeout(() => {
      try {
        player.stopBreakingBlock();
        const block = dimension.getBlock(TARGET);
        if (!observed.breakBefore) fail('playerBreakBlock before-event was not observed');
        if (!observed.breakAfter) fail('allowed locked break did not reach the after-event');
        if (block?.typeId === 'minecraft:chest') fail('allowed locked break left the chest in place');
        console.warn('[mccompiler:simulated-player] locked_break_action=passed');
        player.remove();
      } catch (error) {
        console.error(String(error));
      }
    }, 120);
  } catch (error) {
    console.error(String(error));
  }
}

system.runTimeout(runWhenArmed, 20);
