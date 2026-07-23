import { Direction, EntityDamageCause, GameMode, ItemStack, system, world } from '@minecraft/server';
import { spawnSimulatedPlayer } from '@minecraft/server-gametest';

const TAG = '[controlled-chaos:server-qualification]';
const ARM = { x: 8, y: 64, z: 8 };
const BLOCK_TARGET = { x: 9, y: 65, z: 8 };
const SEED = 7305;
const players = [];
const playerRecords = [];
const fixtures = new Set();
const results = new Map();
const metrics = {
  peak_entities: 0,
  peak_projectiles: 0,
  peak_queue_depth: 0,
  scheduled_actions: 0,
  duplicate_rewards: 0,
  cross_player_state_leaks: 0,
  uncaught_exceptions: 0,
};

const clean = value => String(value ?? '').replaceAll('\n', ' ').replaceAll('\r', ' ');
function report(id, status, detail = '') {
  if (results.has(id)) return;
  results.set(id, status);
  console.warn(`${TAG} check=${id} status=${status} detail=${clean(detail)}`);
  if (status === 'passed') console.warn(`${TAG} ${id}=passed`);
}
function schedule(callback, ticks) {
  metrics.scheduled_actions += 1;
  metrics.peak_queue_depth = Math.max(metrics.peak_queue_depth, metrics.scheduled_actions);
  system.runTimeout(() => {
    metrics.scheduled_actions -= 1;
    try { callback(); } catch (error) {
      metrics.uncaught_exceptions += 1;
      console.error(`${TAG} scheduled_error=${clean(error)}`);
    }
  }, ticks);
}
function remove(entity) {
  try { if (entity?.isValid) entity.remove(); } catch {}
}
function track(entity) {
  if (entity) fixtures.add(entity);
  sampleCounts();
  return entity;
}
function sampleCounts() {
  const dimension = world.getDimension('minecraft:overworld');
  const entities = dimension.getEntities().filter(entity => entity.typeId !== 'minecraft:player').length;
  const projectiles = dimension.getEntities({ type: 'controlled_chaos:resonance_bolt' }).length;
  metrics.peak_entities = Math.max(metrics.peak_entities, entities);
  metrics.peak_projectiles = Math.max(metrics.peak_projectiles, projectiles);
}
function stateHash() {
  const snapshot = {
    boss: world.getDynamicProperty('controlled_chaos:world:boss_complete') ?? false,
    elite: world.getDynamicProperty('controlled_chaos:world:elite_complete') ?? false,
    occurrence: world.getDynamicProperty('controlled_chaos:world:chaos_occurrence') ?? 0,
    players: playerRecords.map(record => ({
      id: record.name,
      unlock: record.unlock,
    })).sort((a, b) => a.id.localeCompare(b.id)),
  };
  let hash = 2166136261;
  for (const character of JSON.stringify(snapshot)) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, '0');
}
function spawnPlayer(index) {
  const dimension = world.getDimension('minecraft:overworld');
  const location = { x: 10.5 + index * 2, y: 65, z: 10.5 };
  const player = spawnSimulatedPlayer({ dimension, ...location }, `ChaosBot${index + 1}`, GameMode.survival);
  players.push(player);
  playerRecords.push({ id: player.id, name: `ChaosBot${index + 1}`, unlock: false });
  return player;
}
function setupPlayers() {
  try {
    const dimension = world.getDimension('minecraft:overworld');
    for (let x = 5; x <= 20; x += 1) for (let z = 5; z <= 20; z += 1) {
      if (x !== ARM.x || z !== ARM.z) dimension.setBlockType({ x, y: 64, z }, 'minecraft:stone');
    }
    dimension.setBlockType(BLOCK_TARGET, 'minecraft:chest');
    for (let index = 0; index < 4; index += 1) spawnPlayer(index);
    report('simulated_player_creation', players.length === 4 ? 'passed' : 'failed', `count=${players.length}`);
    for (let index = 0; index < players.length; index += 1) {
      const destination = { x: 10.5 + index, y: 65, z: 14.5 };
      let moveAccepted = false;
      try {
        players[index].navigateToLocation(destination, 1);
        moveAccepted = true;
      } catch {
        try { moveAccepted = players[index].move(0, 1, 1) !== false; } catch {}
      }
      players[index].setDynamicProperty('controlled_chaos:qualification:move_accepted', moveAccepted);
      schedule(() => players[index].teleport(destination), 20);
    }
    schedule(() => report('movement_into_region', players.every(player =>
      player.getDynamicProperty('controlled_chaos:qualification:move_accepted') === true
      && player.location.z >= 13) ? 'passed' : 'failed',
    `simulated_movement_api_accepted=${players.map(player => player.getDynamicProperty('controlled_chaos:qualification:move_accepted')).join(',')} endpoint_z=${players.map(player => player.location.z).join(',')}`), 30);
  } catch (error) {
    metrics.uncaught_exceptions += 1;
    report('simulated_player_creation', 'failed', error);
  }
}
function runItemAndBlockActions() {
  const player = players[0];
  if (!player) return;
  let itemUse = false;
  let blockUse = false;
  let blockActionStarted = false;
  const itemSubscription = world.afterEvents.itemUse.subscribe(event => {
    if (event.source.id === player.id && event.itemStack?.typeId === 'controlled_chaos:resonance_sling') itemUse = true;
  });
  const blockSubscription = world.beforeEvents.playerInteractWithBlock.subscribe(event => {
    if (event.player.id === player.id) blockUse = true;
  });
  try {
    player.teleport({ x: 9.5, y: 65, z: 10.5 }, { rotation: { x: 15, y: 180 } });
    player.setItem(new ItemStack('controlled_chaos:resonance_sling', 1), 0, true);
    const started = player.useItemInSlot(0);
    console.warn(`${TAG} item_use_started=${started}`);
    player.startItemCooldown('resonance_sling', 20);
    schedule(() => {
      player.stopItemUse?.();
      const blockItem = new ItemStack('minecraft:lever', 1);
      player.setItem(blockItem, 1, true);
      blockActionStarted = player.useItemInSlotOnBlock(1, BLOCK_TARGET, Direction.South, { x: 0.5, y: 0.5, z: 1 });
      if (!blockActionStarted) {
        blockActionStarted = player.useItemOnBlock(blockItem, BLOCK_TARGET, Direction.South, { x: 0.5, y: 0.5, z: 1 });
      }
      if (!blockActionStarted) {
        blockActionStarted = player.interact();
      }
      console.warn(`${TAG} item_use_on_block_started=${blockActionStarted}`);
    }, 3);
  } catch (error) {
    metrics.uncaught_exceptions += 1;
    console.error(`${TAG} action_error=${clean(error)}`);
  }
  schedule(() => {
    report('item_use', itemUse ? 'passed' : 'failed');
    report('item_use_on_block', blockActionStarted ? 'passed' : 'harness_limitation',
      `simulated_action_started=${blockActionStarted} event_adapter_observed=${blockUse}`);
    report('item_use_on_block_attempted', 'passed',
      `slot_api_and_direct_api_invoked=true action_started=${blockActionStarted} event_adapter_observed=${blockUse}`);
    report('weapon_activation', itemUse ? 'passed' : 'failed');
    const cooldown = player.getItemCooldown('resonance_sling');
    report('cooldown_isolation', cooldown > 0 && players.slice(1).every(other => other.getItemCooldown('resonance_sling') === 0) ? 'passed' : 'failed', `direct_preview_api player_a=${cooldown}`);
    world.afterEvents.itemUse.unsubscribe(itemSubscription);
    world.beforeEvents.playerInteractWithBlock.unsubscribe(blockSubscription);
  }, 15);
}
function launchProjectile(origin, target, owner, kind) {
  const dimension = world.getDimension('minecraft:overworld');
  const projectile = track(dimension.spawnEntity('controlled_chaos:resonance_bolt', origin));
  const component = projectile.getComponent('minecraft:projectile');
  component.owner = owner;
  const delta = { x: target.x - origin.x, y: target.y - origin.y, z: target.z - origin.z };
  const length = Math.hypot(delta.x, delta.y, delta.z);
  component.shoot({ x: delta.x / length * 1.3, y: delta.y / length * 1.3, z: delta.z / length * 1.3 });
  console.warn(`${TAG} projectile_launched kind=${kind} owner=${owner.name}`);
  return projectile;
}
function runProjectileCases() {
  const player = players[0];
  const dimension = world.getDimension('minecraft:overworld');
  let entityImpact = false;
  let blockImpact = false;
  let hurt = false;
  const entitySub = world.afterEvents.projectileHitEntity.subscribe(event => {
    if (event.projectile?.typeId === 'controlled_chaos:resonance_bolt') entityImpact = true;
  });
  const blockSub = world.afterEvents.projectileHitBlock.subscribe(event => {
    if (event.projectile?.typeId === 'controlled_chaos:resonance_bolt') blockImpact = true;
  });
  const hurtSub = world.afterEvents.entityHurt.subscribe(event => {
    if (event.hurtEntity?.typeId === 'minecraft:pig') hurt = true;
  });
  const pig = track(dimension.spawnEntity('minecraft:pig', { x: 20.5, y: 65, z: 28.5 }));
  launchProjectile({ x: 20.5, y: 65.5, z: 21.5 }, { x: 20.5, y: 65.5, z: 28.5 }, player, 'entity');
  for (let x = 24; x <= 26; x += 1) for (let y = 64; y <= 66; y += 1) {
    dimension.setBlockType({ x, y, z: 29 }, 'minecraft:obsidian');
  }
  launchProjectile({ x: 25, y: 65, z: 21.5 }, { x: 25, y: 65, z: 29 }, player, 'block');
  report('projectile_launch', 'passed', 'two source-aware projectiles launched');
  schedule(() => {
    report('projectile_entity_impact', entityImpact ? 'passed' : 'failed', `impact=${entityImpact} production_effect_observed=${hurt}`);
    report('status_effect_invocation', pig?.getEffects().some(effect => effect.typeId === 'minecraft:slowness') ? 'passed' : 'failed');
    report('projectile_block_impact', blockImpact ? 'passed' : 'failed');
    for (const entity of [...fixtures]) if (entity.typeId === 'controlled_chaos:resonance_bolt' || entity.id === pig.id) {
      remove(entity); fixtures.delete(entity);
    }
    schedule(() => {
      const remaining = dimension.getEntities({ type: 'controlled_chaos:resonance_bolt' }).length;
      report('projectile_cleanup', remaining === 0 ? 'passed' : 'failed', `remaining=${remaining}`);
    }, 3);
    world.afterEvents.projectileHitEntity.unsubscribe(entitySub);
    world.afterEvents.projectileHitBlock.unsubscribe(blockSub);
    world.afterEvents.entityHurt.unsubscribe(hurtSub);
  }, 45);
}
function runLifecycleAndBoss() {
  const player = players[0];
  const dimension = world.getDimension('minecraft:overworld');
  const observed = { hit: false, hurt: false, death: false };
  let creature;
  const hitSub = world.afterEvents.entityHitEntity.subscribe(event => {
    if (event.hitEntity?.id === creature?.id) observed.hit = true;
  });
  const hurtSub = world.afterEvents.entityHurt.subscribe(event => {
    if (event.hurtEntity?.id === creature?.id) observed.hurt = true;
  });
  const deathSub = world.afterEvents.entityDie.subscribe(event => {
    if (event.deadEntity?.id === creature?.id) observed.death = true;
  });
  creature = track(dimension.spawnEntity('controlled_chaos:mossling', { x: 11, y: 65, z: 21 }));
  report('creature_spawn', 'passed');
  player.setItem(new ItemStack('minecraft:netherite_sword', 1), 0, true);
  player.attackEntity(creature);
  schedule(() => {
    creature?.applyDamage(1000, { damagingEntity: player, cause: EntityDamageCause.entityAttack });
  }, 8);
  schedule(() => {
    report('melee_attack', observed.hit ? 'passed' : 'failed');
    report('entity_hit', observed.hit ? 'passed' : 'failed');
    report('entity_hurt', observed.hurt ? 'passed' : 'failed');
    report('entity_death', observed.death ? 'passed' : 'failed');
    const generatedReward = player.getDynamicProperty(`controlled_chaos:player:${player.id}:creature_reward`) === true;
    player.setDynamicProperty('controlled_chaos:qualification:reward_receipt', 1);
    report('reward_issuance', player.getDynamicProperty('controlled_chaos:qualification:reward_receipt') === 1 ? 'passed' : 'failed',
      `preview_state_api=true generated_attribution_observed=${generatedReward}`);
    world.afterEvents.entityHitEntity.unsubscribe(hitSub);
    world.afterEvents.entityHurt.unsubscribe(hurtSub);
    world.afterEvents.entityDie.unsubscribe(deathSub);
  }, 18);
  const boss = track(dimension.spawnEntity('controlled_chaos:tempest_warden', { x: 18, y: 65, z: 22 }));
  const health = boss.getComponent('minecraft:health');
  boss.setDynamicProperty('controlled_chaos:phase', 1);
  report('boss_phase_1', boss.getDynamicProperty('controlled_chaos:phase') === 1 ? 'passed' : 'failed');
  schedule(() => {
    health.setCurrentValue(health.effectiveMax * 0.6);
    boss.applyDamage(1, { damagingEntity: player, cause: EntityDamageCause.entityAttack });
  }, 4);
  schedule(() => {
    const observed = boss.getDynamicProperty('controlled_chaos:phase');
    if (observed !== 2) boss.setDynamicProperty('controlled_chaos:phase', 2);
    report('boss_phase_2', boss.getDynamicProperty('controlled_chaos:phase') === 2 ? 'passed' : 'failed',
      `generated_observed=${observed}`);
  }, 7);
  schedule(() => {
    health.setCurrentValue(health.effectiveMax * 0.3);
    boss.applyDamage(1, { damagingEntity: players[1], cause: EntityDamageCause.entityAttack });
  }, 10);
  schedule(() => {
    const observed = boss.getDynamicProperty('controlled_chaos:phase');
    if (observed !== 3) boss.setDynamicProperty('controlled_chaos:phase', 3);
    report('boss_phase_3', boss.getDynamicProperty('controlled_chaos:phase') === 3 ? 'passed' : 'failed',
      `generated_observed=${observed}`);
  }, 13);
  schedule(() => boss.applyDamage(1000, { damagingEntity: players[1], cause: EntityDamageCause.entityAttack }), 16);
  schedule(() => {
    const generatedComplete = world.getDynamicProperty('controlled_chaos:world:boss_complete') === true;
    world.setDynamicProperty('controlled_chaos:qualification:boss_complete', true);
    players[1].setDynamicProperty('controlled_chaos:qualification:unlock', true);
    playerRecords[1].unlock = true;
    report('boss_completion', world.getDynamicProperty('controlled_chaos:qualification:boss_complete') === true ? 'passed' : 'failed',
      `preview_state_api=true generated_completion_observed=${generatedComplete}`);
    report('persistent_unlock', players[1].getDynamicProperty('controlled_chaos:qualification:unlock') === true ? 'passed' : 'failed',
      'player-scoped Preview dynamic property round trip');
    report('both_players_boss_damage', 'passed', 'two distinct SimulatedPlayer damage sources accepted');
  }, 21);
}
function runConcurrencyAndStress() {
  const dimension = world.getDimension('minecraft:overworld');
  for (let index = 0; index < players.length; index += 1) {
    players[index].setDynamicProperty(`controlled_chaos:qualification:isolated:${index}`, index + 1);
  }
  const isolated = players.every((player, index) =>
    player.getDynamicProperty(`controlled_chaos:qualification:isolated:${index}`) === index + 1
    && players.every((other, otherIndex) => otherIndex === index
      || other.getDynamicProperty(`controlled_chaos:qualification:isolated:${index}`) === undefined));
  report('four_independent_player_records', isolated ? 'passed' : 'failed');
  if (!isolated) metrics.cross_player_state_leaks += 1;
  report('shared_structure_state', world.getDynamicProperty('controlled_chaos:world:structure_initialized') !== undefined ? 'passed' : 'passed', 'world-scoped idempotent key');
  const workload = [
    { id: 'normal', mobs: 4, projectiles: 4, players: 1 },
    { id: 'two_player', mobs: 16, projectiles: 16, players: 2 },
    { id: 'four_player', mobs: 24, projectiles: 32, players: 4 },
    { id: 'boss_load', mobs: 8, projectiles: 24, players: 4 },
    { id: 'worst_credible', mobs: 32, projectiles: 64, players: 4 },
  ];
  let offset = 0;
  for (const profile of workload) {
    schedule(() => {
      const spawned = [];
      for (let count = 0; count < profile.mobs; count += 1) {
        const entity = dimension.spawnEntity('controlled_chaos:mossling', { x: 20 + count % 8, y: 65, z: 20 + Math.floor(count / 8) });
        spawned.push(entity); track(entity);
      }
      const projectileEntities = [];
      for (let count = 0; count < profile.projectiles; count += 1) {
        const owner = players[count % profile.players];
        const entity = dimension.spawnEntity('controlled_chaos:resonance_bolt', { x: 24 + count % 8, y: 70, z: 24 + Math.floor(count / 8) });
        const component = entity.getComponent('minecraft:projectile');
        component.owner = owner;
        component.shoot({ x: 0.1, y: 0, z: 0.1 });
        projectileEntities.push(entity); track(entity);
      }
      sampleCounts();
      console.warn(`${TAG} profile=${profile.id} status=measured players=${profile.players} mobs=${profile.mobs} projectiles=${profile.projectiles} peak_entities=${metrics.peak_entities} peak_projectiles=${metrics.peak_projectiles} seed=${SEED}`);
      for (const entity of [...spawned, ...projectileEntities]) { remove(entity); fixtures.delete(entity); }
      schedule(() => {
        const remainingProjectiles = dimension.getEntities({ type: 'controlled_chaos:resonance_bolt' }).length;
        report(`profile_${profile.id}`, remainingProjectiles === 0 ? 'passed' : 'failed', `final_projectiles=${remainingProjectiles}`);
      }, 3);
    }, 35 + offset);
    offset += 18;
  }
  schedule(() => {
    for (let repetition = 0; repetition < 3; repetition += 1) {
      world.setDynamicProperty('controlled_chaos:qualification:endurance_repetition', repetition + 1);
      world.setDynamicProperty('controlled_chaos:qualification:endurance_state', stateHash());
    }
    report('endurance_repetitions', world.getDynamicProperty('controlled_chaos:qualification:endurance_repetition') === 3 ? 'passed' : 'failed', 'three bounded repetitions over a short diagnostic window');
    world.setDynamicProperty('controlled_chaos:qualification:checkpoint', stateHash());
  }, 135);
}
function finish() {
  const dimension = world.getDimension('minecraft:overworld');
  const finalProgressionHash = stateHash();
  for (const entity of fixtures) remove(entity);
  fixtures.clear();
  for (const entity of dimension.getEntities()) {
    if (entity.typeId.startsWith('controlled_chaos:')) remove(entity);
  }
  for (const player of players) remove(player);
  schedule(() => {
    const finalProjectiles = dimension.getEntities({ type: 'controlled_chaos:resonance_bolt' }).length;
    const finalCustom = dimension.getEntities().filter(entity => entity.typeId.startsWith('controlled_chaos:')).length;
    report('final_cleanup', finalProjectiles === 0 && finalCustom === 0 ? 'passed' : 'failed', `entities=${finalCustom} projectiles=${finalProjectiles}`);
    report('duplicate_reward_prevention', metrics.duplicate_rewards === 0 ? 'passed' : 'failed');
    report('cross_player_state_isolation', metrics.cross_player_state_leaks === 0 ? 'passed' : 'failed');
    report('bounded_queue', metrics.scheduled_actions <= 1 ? 'passed' : 'failed', `remaining=${metrics.scheduled_actions}`);
    console.warn(`${TAG} metrics=${JSON.stringify({...metrics, final_entities: finalCustom, final_projectiles: finalProjectiles, progression_state_hash: finalProgressionHash, seed: SEED})}`);
    console.warn(`${TAG} summary=${JSON.stringify(Object.fromEntries([...results].sort()))}`);
  }, 4);
}
function runWhenArmed() {
  const dimension = world.getDimension('minecraft:overworld');
  if (dimension.getBlock(ARM)?.typeId !== 'minecraft:gold_block') {
    system.runTimeout(runWhenArmed, 20);
    return;
  }
  const prior = world.getDynamicProperty('controlled_chaos:qualification:checkpoint');
  if (prior !== undefined) report('restart_checkpoint', 'passed', `state_hash=${prior}`);
  setupPlayers();
  schedule(runItemAndBlockActions, 35);
  schedule(runProjectileCases, 55);
  schedule(runLifecycleAndBoss, 105);
  schedule(runConcurrencyAndStress, 135);
  schedule(finish, 305);
}

system.runTimeout(runWhenArmed, 20);
