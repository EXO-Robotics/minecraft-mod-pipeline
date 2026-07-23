import { GameMode, ItemStack, system, world } from '@minecraft/server';
import { spawnSimulatedPlayer } from '@minecraft/server-gametest';

const ARM_MARKER = { x: 11, y: 64, z: 10 };
const PLAYER_SPAWN = { x: 10.5, y: 65, z: 10.5 };
const PROJECTILE_TARGET = { x: 10.5, y: 65, z: 12.5 };
const MACHINE_BLOCK = { x: 12, y: 64, z: 10 };
const observed = {
  playerId: undefined,
  itemUse: false,
  projectileSpawn: false,
  projectileHit: false,
  projectileBlockHit: false,
  projectileBlockLocation: undefined,
  projectileSpawnLocation: undefined,
  projectileRemoved: false,
  entityHit: false,
  entityHurt: false,
  entityDeath: false,
  machineBlockInteract: false,
  itemUseOnBlock: false,
  entityDamagesPlayer: false,
};

function diagnosticPlayer(entity) {
  return observed.playerId !== undefined && entity?.id === observed.playerId;
}

function fail(message) {
  throw new Error(`[mccompiler:showcase-actions] ${message}`);
}

world.afterEvents.itemUse.subscribe((event) => {
  if (diagnosticPlayer(event.source)
    && event.itemStack?.typeId === 'clockwork_gardens:sunseed_launcher') observed.itemUse = true;
});
world.beforeEvents.playerInteractWithBlock.subscribe((event) => {
  if (!diagnosticPlayer(event.player)) return;
  if (event.block?.location.x !== MACHINE_BLOCK.x
    || event.block?.location.y !== MACHINE_BLOCK.y
    || event.block?.location.z !== MACHINE_BLOCK.z) return;
  observed.machineBlockInteract = true;
  const usedItem = event.itemStack?.typeId || event.beforeItemStack?.typeId;
  if (usedItem === 'clockwork_gardens:lumen_ingot') observed.itemUseOnBlock = true;
  console.warn(`[mccompiler:showcase-actions] machine_event item=${event.itemStack?.typeId} before=${event.beforeItemStack?.typeId}`);
});
world.afterEvents.entitySpawn.subscribe((event) => {
  if (event.entity?.typeId === 'clockwork_gardens:sunseed_projectile') {
    observed.projectileSpawn = true;
    observed.projectileSpawnLocation = event.entity.location;
  }
});
world.afterEvents.projectileHitEntity.subscribe((event) => {
  if (event.projectile?.typeId === 'clockwork_gardens:sunseed_projectile') observed.projectileHit = true;
});
world.afterEvents.projectileHitBlock.subscribe((event) => {
  if (event.projectile?.typeId === 'clockwork_gardens:sunseed_projectile') {
    observed.projectileBlockHit = true;
    try { observed.projectileBlockLocation = event.getBlockHit()?.block?.location; } catch {}
  }
});
world.afterEvents.entityRemove.subscribe((event) => {
  if (event.removedEntityTypeId === 'clockwork_gardens:sunseed_projectile') observed.projectileRemoved = true;
});
world.afterEvents.entityHitEntity.subscribe((event) => {
  if (diagnosticPlayer(event.damagingEntity)) observed.entityHit = true;
});
world.afterEvents.entityHurt.subscribe((event) => {
  if (diagnosticPlayer(event.damageSource?.damagingEntity)) observed.entityHurt = true;
  if (diagnosticPlayer(event.hurtEntity)
    && event.damageSource?.damagingEntity?.typeId === 'minecraft:husk') observed.entityDamagesPlayer = true;
});
world.afterEvents.entityDie.subscribe((event) => {
  if (diagnosticPlayer(event.damageSource?.damagingEntity)) observed.entityDeath = true;
});

function runWhenArmed() {
  try {
    const dimension = world.getDimension('minecraft:overworld');
    if (dimension.getBlock(ARM_MARKER)?.typeId !== 'minecraft:gold_block') {
      system.runTimeout(runWhenArmed, 20);
      return;
    }
    const player = spawnSimulatedPlayer(
      { dimension, ...PLAYER_SPAWN }, 'MCCompilerShowcaseBot', GameMode.survival,
    );
    observed.playerId = player.id;
    player.setItem(new ItemStack('clockwork_gardens:lumen_ingot', 1), 0, true);
    const usedOnBlock = player.useItemInSlotOnBlock(0, MACHINE_BLOCK);
    console.warn(`[mccompiler:showcase-actions] item_use_on_block_started=${usedOnBlock}`);
    dimension.spawnEntity('clockwork_gardens:brass_sprout', { x: 14.5, y: 65, z: 10.5 });
    // The generated entitySpawn lifecycle registration must place this boss
    // into the production scheduler; the diagnostic never invokes dispatch.
    dimension.spawnEntity('clockwork_gardens:verdant_colossus', { x: 16.5, y: 65, z: 10.5 });
    let itemStarted = false;
    // Keep independent player actions on separate ticks; GameTest rejects a
    // second use while the first interaction is still active.
    system.runTimeout(() => {
      itemStarted = player.useItem(new ItemStack('clockwork_gardens:sunseed_launcher', 1));
      console.warn(`[mccompiler:showcase-actions] item_use_started=${itemStarted}`);
    }, 20);

    system.runTimeout(() => {
      try {
        if (!itemStarted) fail('simulated launcher use did not start');
        if (!observed.itemUse) fail('itemUse event was not observed');
        console.warn('[mccompiler:showcase-actions] item_use_event=passed');
      } catch (error) {
        console.error(String(error));
      }
    }, 25);

    system.runTimeout(() => {
      try {
        if (!observed.machineBlockInteract) fail('machine block interaction was not observed');
        if (!usedOnBlock || !observed.itemUseOnBlock) fail('item use on machine block was not observed');
        console.warn('[mccompiler:showcase-actions] block_interaction_events=passed');
      } catch (error) {
        console.error(String(error));
      }
    }, 10);

    let projectileTarget;
    system.runTimeout(() => {
      try {
        projectileTarget = dimension.spawnEntity('minecraft:iron_golem', PROJECTILE_TARGET);
        const projectile = dimension.spawnEntity(
          'clockwork_gardens:sunseed_projectile',
          { x: PROJECTILE_TARGET.x, y: PROJECTILE_TARGET.y + 1.2, z: PROJECTILE_TARGET.z - 1.5 },
        );
        const component = projectile.getComponent('minecraft:projectile');
        if (!component) fail('custom projectile lacks minecraft:projectile');
        component.owner = player;
        component.shoot({ x: 0, y: 0, z: 0.8 });
      } catch (error) {
        console.error(String(error));
      }
    }, 20);

    system.runTimeout(() => {
      try {
        if (!observed.projectileHit) fail(`custom projectile did not produce projectileHitEntity; block_hit=${observed.projectileBlockHit} removed=${observed.projectileRemoved} spawn=${JSON.stringify(observed.projectileSpawnLocation)} block=${JSON.stringify(observed.projectileBlockLocation)} target=${JSON.stringify(projectileTarget.location)}`);
        if (!projectileTarget?.getEffects().some((effect) => effect.typeId === 'minecraft:slowness')) fail('projectile impact adapter did not apply slowness');
        console.warn('[mccompiler:showcase-actions] projectile_impact_adapter=passed');
      } catch (error) {
        console.error(String(error));
      }
    }, 60);

    system.runTimeout(() => {
      try {
        dimension.spawnEntity('minecraft:husk', { x: 11.5, y: 65, z: 10.5 });
      } catch (error) {
        console.error(String(error));
      }
    }, 65);

    system.runTimeout(() => {
      try {
        if (!observed.entityDamagesPlayer) fail('hostile entity did not damage the simulated player');
        console.warn('[mccompiler:showcase-actions] entity_damages_player=passed');
      } catch (error) {
        console.error(String(error));
      }
    }, 120);

    // Keep combat independent: a projectile failure must not hide other real event adapters.
    system.runTimeout(() => {
      try {
        const combatTarget = dimension.spawnEntity('minecraft:pig', { x: 10.5, y: 65, z: 12.5 });
        player.setItem(new ItemStack('minecraft:netherite_sword', 1), 0, true);
        if (!player.attackEntity(combatTarget)) fail('first simulated melee attack did not start');
        system.runTimeout(() => {
          try {
            if (!observed.entityHit) fail('entityHitEntity event was not observed');
            if (!observed.entityHurt) fail('entityHurt event was not observed');
            player.attackEntity(combatTarget);
            system.runTimeout(() => {
              try {
                if (!observed.entityDeath) fail('entityDie event from simulated melee was not observed');
                console.warn('[mccompiler:showcase-actions] melee_hurt_and_death_actions=passed');
                player.remove();
              } catch (error) {
                console.error(String(error));
              }
            }, 20);
          } catch (error) {
            console.error(String(error));
          }
        }, 20);
      } catch (error) {
        console.error(String(error));
      }
    }, 140);
  } catch (error) {
    console.error(String(error));
  }
}

system.runTimeout(runWhenArmed, 20);
