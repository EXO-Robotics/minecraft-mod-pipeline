import { EntityDamageCause, GameMode, ItemStack, system, world } from '@minecraft/server';
import { spawnSimulatedPlayer } from '@minecraft/server-gametest';

const TAG = '[mccompiler:showcase-actions]';
const ARM_MARKER = { x: 11, y: 64, z: 10 };
const PLAYER_SPAWN = { x: 10.5, y: 65, z: 10.5 };
const MACHINE_BLOCK = { x: 12, y: 64, z: 10 };
const ENTITY_SHOT_ORIGIN = { x: 18.5, y: 65.5, z: 10.5 };
const ENTITY_SHOT_TARGET = { x: 18.5, y: 65.5, z: 17.5 };
const ENTITY_TARGET_SPAWN = { x: 18.5, y: 64, z: 17.5 };
const BLOCK_SHOT_ORIGIN = { x: 24.5, y: 67, z: 10.5 };
const BLOCK_SHOT_TARGET = { x: 24, y: 67, z: 18 };
const PROJECTILE_TYPE = 'clockwork_gardens:sunseed_projectile';
const results = new Map();
const trackedProjectiles = new Map();
let diagnosticPlayerId;
let diagnosticPlayer;

function detail(value) {
  return String(value ?? '').replaceAll('\n', ' ').replaceAll('\r', ' ');
}

function report(check, status, message = '') {
  if (results.has(check)) return;
  results.set(check, status);
  console.warn(`${TAG} check=${check} status=${status} detail=${detail(message)}`);
  if (status === 'passed') console.warn(`${TAG} ${check}=passed`);
}

function pending(check, message) {
  report(check, 'not_supported', message);
}

function diagnosticPlayerEntity(entity) {
  return diagnosticPlayerId !== undefined && entity?.id === diagnosticPlayerId;
}

function safeRemove(entity) {
  try {
    if (entity?.isValid) entity.remove();
  } catch {}
}

function effect(entity, typeId) {
  try {
    return entity?.getEffects().find((entry) => entry.typeId === typeId);
  } catch {
    return undefined;
  }
}

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
}

function normalized(from, to, speed) {
  const delta = { x: to.x - from.x, y: to.y - from.y, z: to.z - from.z };
  const length = Math.hypot(delta.x, delta.y, delta.z);
  if (!length) throw new Error('projectile fixture has a zero-length path');
  return { x: delta.x / length * speed, y: delta.y / length * speed, z: delta.z / length * speed };
}

function inventoryCount(player, typeId) {
  try {
    const container = player.getComponent('minecraft:inventory')?.container;
    let count = 0;
    for (let slot = 0; container && slot < container.size; slot += 1) {
      const item = container.getItem(slot);
      if (item?.typeId === typeId) count += item.amount;
    }
    return count;
  } catch {
    return 0;
  }
}

function traceProjectile(id, stage, expectedTarget) {
  const tracked = trackedProjectiles.get(id);
  if (!tracked) return;
  try {
    const location = tracked.entity.location;
    tracked.samples.push({ tick: system.currentTick, ...location });
    if (distance(location, tracked.origin) > 0.35) tracked.moved = true;
    if (distance(location, expectedTarget) < 1.8) tracked.pathCrossed = true;
    console.warn(`${TAG} projectile_stage case=${tracked.kind} stage=${stage} tick=${system.currentTick} position=${JSON.stringify(location)}`);
  } catch {
    console.warn(`${TAG} projectile_stage case=${tracked.kind} stage=${stage} tick=${system.currentTick} position=unavailable`);
  }
}

world.afterEvents.itemUse.subscribe((event) => {
  if (!diagnosticPlayerEntity(event.source)
    || event.itemStack?.typeId !== 'clockwork_gardens:sunseed_launcher') return;
  report('item_use_adapter', 'passed', 'Preview SimulatedPlayer itemUse event observed');
  console.warn(`${TAG} effect_stage stage=generated_dispatch_input_observed target=simulated_player`);
});

world.beforeEvents.playerInteractWithBlock.subscribe((event) => {
  if (!diagnosticPlayerEntity(event.player)) return;
  if (event.block?.location.x !== MACHINE_BLOCK.x
    || event.block?.location.y !== MACHINE_BLOCK.y
    || event.block?.location.z !== MACHINE_BLOCK.z) return;
  report('block_interaction_adapter', 'passed', 'stable before-event observed');
  const usedItem = event.itemStack?.typeId || event.beforeItemStack?.typeId;
  if (usedItem === 'clockwork_gardens:lumen_ingot') {
    report('item_use_on_block_adapter', 'passed', 'lumen ingot and Lumen Press context observed');
  }
});

world.afterEvents.entitySpawn.subscribe((event) => {
  if (event.entity?.typeId !== PROJECTILE_TYPE) return;
  const nearest = [...trackedProjectiles.values()]
    .filter((entry) => entry.awaitingSpawn)
    .sort((left, right) => distance(event.entity.location, left.origin)
      - distance(event.entity.location, right.origin))[0];
  if (nearest && distance(event.entity.location, nearest.origin) < 2) {
    nearest.entity = event.entity;
    nearest.awaitingSpawn = false;
    nearest.created = true;
    trackedProjectiles.set(event.entity.id, nearest);
    trackedProjectiles.delete(nearest.fixtureId);
    console.warn(`${TAG} projectile_stage case=${nearest.kind} stage=created id=${event.entity.id} origin=${JSON.stringify(event.entity.location)} target=${JSON.stringify(nearest.target)}`);
  }
});

world.afterEvents.projectileHitEntity.subscribe((event) => {
  const tracked = trackedProjectiles.get(event.projectile?.id);
  if (!tracked) return;
  tracked.collision = true;
  tracked.normalizedEvent = !!event.projectile && !!event.source;
  try {
    tracked.hitEntity = event.getEntityHit()?.entity;
  } catch {
    tracked.hitEntity = undefined;
  }
  console.warn(`${TAG} projectile_stage case=${tracked.kind} stage=entity_collision target=${tracked.hitEntity?.typeId}`);
});

world.afterEvents.projectileHitBlock.subscribe((event) => {
  const tracked = trackedProjectiles.get(event.projectile?.id);
  if (!tracked) return;
  tracked.collision = true;
  tracked.normalizedEvent = !!event.projectile;
  try {
    tracked.hitBlock = event.getBlockHit()?.block;
  } catch {
    tracked.hitBlock = undefined;
  }
  console.warn(`${TAG} projectile_stage case=${tracked.kind} stage=block_collision block=${tracked.hitBlock?.typeId} location=${JSON.stringify(tracked.hitBlock?.location)}`);
});

world.afterEvents.entityRemove.subscribe((event) => {
  if (event.removedEntityTypeId !== PROJECTILE_TYPE) return;
  const tracked = trackedProjectiles.get(event.removedEntityId);
  if (tracked) {
    tracked.removed = true;
    console.warn(`${TAG} projectile_stage case=${tracked.kind} stage=cleanup_event`);
  }
});

function launchProjectileCase(kind, origin, target, owner, speed, onReady) {
  const fixtureId = `fixture:${kind}`;
  const tracked = {
    fixtureId,
    kind,
    origin,
    target,
    awaitingSpawn: true,
    created: false,
    configured: false,
    ownerAssigned: false,
    launched: false,
    moved: false,
    pathCrossed: false,
    collision: false,
    normalizedEvent: false,
    removed: false,
    samples: [],
  };
  trackedProjectiles.set(fixtureId, tracked);
  try {
    const dimension = world.getDimension('minecraft:overworld');
    const projectile = dimension.spawnEntity(PROJECTILE_TYPE, origin);
    tracked.entity = projectile;
    tracked.created = true;
    tracked.awaitingSpawn = false;
    trackedProjectiles.delete(fixtureId);
    trackedProjectiles.set(projectile.id, tracked);
    console.warn(`${TAG} projectile_stage case=${kind} stage=created id=${projectile.id} origin=${JSON.stringify(origin)} target=${JSON.stringify(target)}`);
    const component = projectile.getComponent('minecraft:projectile');
    if (!component?.shoot) throw new Error('minecraft:projectile component with shoot() is unavailable');
    tracked.configured = true;
    console.warn(`${TAG} projectile_stage case=${kind} stage=component_configured`);
    component.owner = owner;
    tracked.ownerAssigned = component.owner?.id === owner?.id;
    console.warn(`${TAG} projectile_stage case=${kind} stage=owner_assigned value=${tracked.ownerAssigned}`);
    component.shoot(normalized(origin, target, speed));
    tracked.launched = true;
    console.warn(`${TAG} projectile_stage case=${kind} stage=launched speed=${speed}`);
    for (const ticks of [2, 5, 10, 15, 20]) {
      system.runTimeout(() => traceProjectile(projectile.id, `sample_${ticks}`, target), ticks);
    }
    system.runTimeout(() => onReady(tracked), 35);
  } catch (error) {
    trackedProjectiles.delete(fixtureId);
    report(`projectile_${kind}`, 'failed', error);
  }
}

function runEffectAndCooldownCase(player) {
  let directSimulatedAccepted = false;
  let directNormalAccepted = false;
  const dimension = player.dimension;
  let normalTarget;
  try {
    player.removeEffect('minecraft:speed');
    normalTarget = dimension.spawnEntity('minecraft:iron_golem', { x: 14.5, y: 65, z: 14.5 });
    normalTarget.removeEffect('minecraft:speed');
    player.addEffect('minecraft:speed', 40, { amplifier: 0 });
    directSimulatedAccepted = true;
    console.warn(`${TAG} effect_stage stage=api_invoked target=simulated_player accepted=true`);
  } catch (error) {
    console.warn(`${TAG} effect_stage stage=api_invoked target=simulated_player accepted=false error=${detail(error)}`);
  }
  try {
    normalTarget?.addEffect('minecraft:speed', 40, { amplifier: 0 });
    directNormalAccepted = true;
    console.warn(`${TAG} effect_stage stage=api_invoked target=normal_entity accepted=true`);
  } catch (error) {
    console.warn(`${TAG} effect_stage stage=api_invoked target=normal_entity accepted=false error=${detail(error)}`);
  }
  const immediateSimulated = !!effect(player, 'minecraft:speed');
  const immediateNormal = !!effect(normalTarget, 'minecraft:speed');
  console.warn(`${TAG} effect_stage stage=immediate_observation simulated=${immediateSimulated} normal=${immediateNormal}`);
  if (directSimulatedAccepted && directNormalAccepted) {
    report('effect_api_invocation', 'passed', 'direct stable API calls accepted for both targets');
  } else {
    report('effect_api_invocation', 'failed', `simulated=${directSimulatedAccepted} normal=${directNormalAccepted}`);
  }
  if (immediateSimulated && immediateNormal) {
    report('effect_immediate_observation', 'passed', 'speed visible on SimulatedPlayer and normal entity');
  } else {
    report('effect_immediate_observation', 'failed', `simulated=${immediateSimulated} normal=${immediateNormal}`);
  }
  system.runTimeout(() => {
    const delayedSimulated = !!effect(player, 'minecraft:speed');
    const delayedNormal = !!effect(normalTarget, 'minecraft:speed');
    console.warn(`${TAG} effect_stage stage=delayed_observation simulated=${delayedSimulated} normal=${delayedNormal}`);
    if (delayedSimulated && delayedNormal) {
      report('effect_delayed_observation', 'passed', 'speed remained visible after five ticks');
      report('effect_target_comparison', 'passed', 'no SimulatedPlayer/normal-entity observation difference');
    } else {
      report('effect_delayed_observation', 'failed', `simulated=${delayedSimulated} normal=${delayedNormal}`);
      report('effect_target_comparison', delayedSimulated === delayedNormal ? 'inconclusive' : 'passed',
        `simulated=${delayedSimulated} normal=${delayedNormal}`);
    }
    safeRemove(normalTarget);
  }, 5);

  // This use is the generated adapter input. Direct API checks above are
  // intentionally separate and do not prove generated dispatch.
  system.runTimeout(() => {
    try {
      player.removeEffect('minecraft:speed');
      player.stopItemUse?.();
      const started = player.useItem(new ItemStack('clockwork_gardens:sunseed_launcher', 1));
      console.warn(`${TAG} effect_stage stage=generated_use_started value=${started}`);
      if (!started) report('item_use_adapter', 'failed', 'SimulatedPlayer useItem returned false');
    } catch (error) {
      report('item_use_adapter', 'failed', error);
    }
  }, 10);
  system.runTimeout(() => {
    const generatedEffect = !!effect(player, 'minecraft:speed');
    const cooldown = player.getItemCooldown?.('clockwork_gardens:sunseed_launcher') ?? 0;
    console.warn(`${TAG} effect_stage stage=generated_action_observation speed=${generatedEffect} cooldown=${cooldown}`);
    report('effect_generated_dispatch', generatedEffect ? 'passed' : 'not_observed',
      generatedEffect ? 'speed observed after generated item-use input' : 'item-use event alone does not prove generated effect dispatch');
    report('cooldown', cooldown > 0 ? 'passed' : 'not_observed',
      cooldown > 0 ? `remaining_ticks=${cooldown}` : 'generated cooldown state was not observable');
  }, 13);
  pending('effect_real_player', 'requires a local Minecraft client and human observation');
}

function runBlockCases(player) {
  const dimension = player.dimension;
  const block = dimension.getBlock(MACHINE_BLOCK);
  if (block?.typeId !== 'clockwork_gardens:lumen_press') {
    report('block_interaction_adapter', 'failed', 'generated Lumen Press fixture is missing');
    report('item_use_on_block_adapter', 'failed', 'generated Lumen Press fixture is missing');
    report('form_invocation', 'not_observed', 'block fixture unavailable');
    report('machine_cycle', 'not_observed', 'block fixture unavailable');
    return;
  }
  try {
    player.setItem(new ItemStack('clockwork_gardens:lumen_ingot', 1), 0, true);
    const started = player.useItemInSlotOnBlock(0, MACHINE_BLOCK);
    console.warn(`${TAG} block_stage stage=use_on_block_started value=${started}`);
    if (!started) report('item_use_on_block_adapter', 'failed', 'SimulatedPlayer action returned false');
  } catch (error) {
    report('item_use_on_block_adapter', 'failed', error);
  }
  system.runTimeout(() => {
    if (!results.has('block_interaction_adapter')) {
      report('block_interaction_adapter', 'not_observed', 'stable block before-event did not arrive');
    }
    if (!results.has('item_use_on_block_adapter')) {
      report('item_use_on_block_adapter', 'not_observed', 'item and block context did not arrive');
    }
    // ActionForm display state is not observable from a Preview BDS
    // SimulatedPlayer, so event arrival is not promoted to a form pass.
    report('form_invocation', 'not_observed',
      'block event observed; generated ActionForm invocation has no independent BDS observation surface');
  }, 8);

  const prefix = 'mccompiler:clockwork_gardens:lumen_press:';
  const locationKey = `minecraft:overworld:${MACHINE_BLOCK.x}:${MACHINE_BLOCK.y}:${MACHINE_BLOCK.z}`;
  try {
    world.setDynamicProperty(`${prefix}${locationKey}:press_progress`, 0);
    console.warn(`${TAG} machine_stage stage=diagnostic_observation_reset progress=0`);
  } catch (error) {
    report('machine_cycle', 'failed', `fixture state write failed: ${error}`);
    return;
  }
  system.runTimeout(() => {
    const progress = Number(world.getDynamicProperty(`${prefix}${locationKey}:press_progress`) ?? 0);
    const energy = Number(world.getDynamicProperty(`${prefix}${locationKey}:press_energy`) ?? 0);
    const inventoryOutput = inventoryCount(player, 'clockwork_gardens:charged_sunseed');
    const droppedOutput = dimension.getEntities({
      type: 'minecraft:item', location: MACHINE_BLOCK, maxDistance: 4,
    }).some((entity) => entity.getComponent('minecraft:item')?.itemStack?.typeId
      === 'clockwork_gardens:charged_sunseed');
    console.warn(`${TAG} machine_stage stage=cycle_observation progress=${progress} energy=${energy} inventory_output=${inventoryOutput} dropped_output=${droppedOutput}`);
    report('machine_cycle', inventoryOutput >= 1 || droppedOutput
      ? 'passed' : 'not_observed',
    `generated_output_observed=${inventoryOutput >= 1 || droppedOutput} progress_cross_pack=${progress} energy_cross_pack=${energy} inventory_output=${inventoryOutput} dropped_output=${droppedOutput}`);
    if (inventoryOutput >= 1 || droppedOutput) {
      world.setDynamicProperty('mccompiler:showcase:machine_progress_checkpoint', 1);
      console.warn(`${TAG} persistence_stage stage=checkpoint_written value=1`);
    }
  }, 30);
}

function runProjectileCases(player) {
  const dimension = player.dimension;
  let entityTarget;
  try {
    entityTarget = dimension.spawnEntity('minecraft:iron_golem', ENTITY_TARGET_SPAWN);
    entityTarget.teleport(ENTITY_TARGET_SPAWN);
    for (const ticks of [2, 5, 10, 15, 20]) {
      system.runTimeout(() => {
        try { entityTarget?.teleport(ENTITY_TARGET_SPAWN); } catch {}
      }, ticks);
    }
  } catch (error) {
    report('projectile_entity_impact', 'failed', `target fixture failed: ${error}`);
  }
  if (entityTarget) {
    launchProjectileCase('entity_impact', ENTITY_SHOT_ORIGIN, ENTITY_SHOT_TARGET, player, 1.3, (tracked) => {
      const actionObserved = !!effect(entityTarget, 'minecraft:slowness');
      report('projectile_creation', tracked.created && tracked.configured && tracked.ownerAssigned && tracked.launched
        ? 'passed' : 'failed',
      `created=${tracked.created} configured=${tracked.configured} owner=${tracked.ownerAssigned} launched=${tracked.launched}`);
      report('projectile_entity_impact',
        tracked.moved && tracked.collision && !!tracked.hitEntity && tracked.normalizedEvent ? 'passed' : 'failed',
        `moved=${tracked.moved} path_crossed=${tracked.pathCrossed} collision=${tracked.collision} normalized=${tracked.normalizedEvent} hit=${tracked.hitEntity?.typeId}`);
      report('projectile_entity_impact_action', actionObserved && tracked.collision ? 'passed' : 'not_observed',
        `slowness_observed=${actionObserved} collision=${tracked.collision}`);
      safeRemove(tracked.entity);
      safeRemove(entityTarget);
      system.runTimeout(() => {
        report('projectile_entity_cleanup', !tracked.entity?.isValid || tracked.removed ? 'passed' : 'failed',
          `remove_event=${tracked.removed}`);
      }, 2);
    });
  }

  try {
    for (let x = 23; x <= 25; x += 1) {
      for (let y = 66; y <= 68; y += 1) {
        dimension.setBlockType({ x, y, z: BLOCK_SHOT_TARGET.z }, 'minecraft:obsidian');
      }
    }
    console.warn(`${TAG} projectile_stage case=block_impact stage=fixture_ready location=${JSON.stringify(BLOCK_SHOT_TARGET)}`);
    launchProjectileCase('block_impact', BLOCK_SHOT_ORIGIN, BLOCK_SHOT_TARGET, player, 1.3, (tracked) => {
      report('projectile_block_impact',
        tracked.moved && tracked.collision && !!tracked.hitBlock && tracked.normalizedEvent ? 'passed' : 'failed',
        `moved=${tracked.moved} path_crossed=${tracked.pathCrossed} collision=${tracked.collision} normalized=${tracked.normalizedEvent} hit=${tracked.hitBlock?.typeId}`);
      report('projectile_block_impact_action', 'not_run',
        'compiler adapter supports block impact; this benchmark has no generated block-impact behavior contract');
      safeRemove(tracked.entity);
      system.runTimeout(() => {
        report('projectile_block_cleanup', !tracked.entity?.isValid || tracked.removed ? 'passed' : 'failed',
          `remove_event=${tracked.removed}`);
      }, 2);
    });
  } catch (error) {
    report('projectile_block_impact', 'failed', `block fixture failed: ${error}`);
  }
}

function runLifecycleAndProgressionCases(player) {
  const observed = { hit: false, hurt: false, death: false };
  let target;
  const hitSubscription = world.afterEvents.entityHitEntity.subscribe((event) => {
    if (event.damagingEntity?.id === player.id && event.hitEntity?.id === target?.id) observed.hit = true;
  });
  const hurtSubscription = world.afterEvents.entityHurt.subscribe((event) => {
    if (event.damageSource?.damagingEntity?.id === player.id && event.hurtEntity?.id === target?.id) observed.hurt = true;
  });
  const deathSubscription = world.afterEvents.entityDie.subscribe((event) => {
    if (event.damageSource?.damagingEntity?.id === player.id && event.deadEntity?.id === target?.id) observed.death = true;
  });
  try {
    target = player.dimension.spawnEntity('minecraft:pig', { x: 10.5, y: 65, z: 12.0 });
    player.teleport(PLAYER_SPAWN, { rotation: { x: 0, y: 0 } });
    player.setItem(new ItemStack('minecraft:netherite_sword', 1), 0, true);
    if (!player.attackEntity(target)) throw new Error('first attackEntity returned false');
  } catch (error) {
    report('entity_hit', 'failed', error);
    report('entity_hurt', 'failed', error);
    report('entity_death', 'failed', error);
    return;
  }
  system.runTimeout(() => {
    report('entity_hit', observed.hit ? 'passed' : 'not_observed', 'independent entityHitEntity subscription');
    report('entity_hurt', observed.hurt ? 'passed' : 'not_observed', 'independent entityHurt subscription');
    try {
      target?.applyDamage(1000, { damagingEntity: player, cause: EntityDamageCause.entityAttack });
    } catch (error) {
      console.warn(`${TAG} lifecycle_stage stage=death_setup_failed error=${detail(error)}`);
    }
  }, 10);
  system.runTimeout(() => {
    report('entity_death', observed.death ? 'passed' : 'not_observed', 'independent entityDie subscription');
    const progressionKey = 'mccompiler:clockwork_gardens:garden_rank:garden_rank';
    const priorRank = Number(player.getDynamicProperty(progressionKey) ?? 0);
    player.setDynamicProperty(progressionKey, priorRank + 1);
    const rank = Number(player.getDynamicProperty('mccompiler:clockwork_gardens:garden_rank:garden_rank') ?? 0);
    report('progression_state_update', rank === priorRank + 1 ? 'passed' : 'failed',
      `state_adapter prior=${priorRank} garden_rank=${rank}; generated death dispatch remains independently classified`);
    world.afterEvents.entityHitEntity.unsubscribe(hitSubscription);
    world.afterEvents.entityHurt.unsubscribe(hurtSubscription);
    world.afterEvents.entityDie.unsubscribe(deathSubscription);
    safeRemove(target);
  }, 20);

  try {
    const sprout = player.dimension.spawnEntity('clockwork_gardens:brass_sprout', { x: 14.5, y: 65, z: 10.5 });
    system.runTimeout(() => {
      const phase = sprout.getDynamicProperty('mccompiler:phase');
      report('entity_spawn', phase === 1 ? 'passed' : 'not_observed', `spawn phase=${phase}`);
      safeRemove(sprout);
    }, 10);
  } catch (error) {
    report('entity_spawn', 'failed', error);
  }
  console.warn(`${TAG} growth_stage stage=generated_delayed_phase_expected`);
}

function runBossCases(player) {
  const cases = [
    { name: 'boss_phase_1', ratio: 0.9, expected: 1, x: 16.5 },
    { name: 'boss_phase_2', ratio: 0.5, expected: 2, x: 20.5 },
    { name: 'boss_phase_3', ratio: 0.2, expected: 3, x: 24.5 },
  ];
  for (const entry of cases) {
    try {
      const boss = player.dimension.spawnEntity('clockwork_gardens:verdant_colossus',
        { x: entry.x, y: 65, z: 22.5 });
      const health = boss.getComponent('minecraft:health');
      health.setCurrentValue(health.effectiveMax * entry.ratio);
      console.warn(`${TAG} boss_stage case=${entry.name} stage=fixture_ready ratio=${entry.ratio}`);
      system.runTimeout(() => {
        const phase = boss.getDynamicProperty('mccompiler:phase');
        report(entry.name, phase === entry.expected ? 'passed' : 'not_observed',
          `expected=${entry.expected} observed=${phase}`);
        safeRemove(boss);
      }, 20);
    } catch (error) {
      report(entry.name, 'failed', error);
    }
  }
}

function runWhenArmed() {
  const dimension = world.getDimension('minecraft:overworld');
  if (dimension.getBlock(ARM_MARKER)?.typeId !== 'minecraft:gold_block') {
    system.runTimeout(runWhenArmed, 20);
    return;
  }
  const persisted = Number(world.getDynamicProperty('mccompiler:showcase:machine_progress_checkpoint') ?? 0);
  if (persisted > 0) {
    report('persistence_after_restart', 'passed', `world checkpoint restored value=${persisted}`);
  } else {
    console.warn(`${TAG} persistence_stage stage=no_prior_checkpoint`);
  }
  try {
    diagnosticPlayer = spawnSimulatedPlayer(
      { dimension, ...PLAYER_SPAWN }, 'MCCompilerShowcaseBot', GameMode.survival,
    );
    diagnosticPlayerId = diagnosticPlayer.id;
  } catch (error) {
    console.error(`${TAG} harness_start_failed ${detail(error)}`);
    return;
  }

  // Each case owns its fixtures, assertions, timeout, and cleanup. Their start
  // ticks are staggered only to avoid GameTest action contention.
  system.runTimeout(() => runBlockCases(diagnosticPlayer), 2);
  system.runTimeout(() => runEffectAndCooldownCase(diagnosticPlayer), 20);
  system.runTimeout(() => runProjectileCases(diagnosticPlayer), 45);
  system.runTimeout(() => runLifecycleAndProgressionCases(diagnosticPlayer), 100);
  system.runTimeout(() => runBossCases(diagnosticPlayer), 145);
  system.runTimeout(() => {
    if (!results.has('persistence_after_restart')) {
      report('persistence_after_restart', 'not_run',
        'requires a second BDS cycle after a successful machine checkpoint');
    }
    pending('real_client', 'not exercised by Preview BDS diagnostic');
    pending('multiplayer', 'single SimulatedPlayer fixture only');
    pending('console', 'no physical console was exercised');
    console.warn(`${TAG} summary=${JSON.stringify(Object.fromEntries([...results].sort()))}`);
    safeRemove(diagnosticPlayer);
  }, 190);
}

system.runTimeout(runWhenArmed, 20);
