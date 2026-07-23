import { ItemStack, system, world } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";

const NS = "controlled_chaos";
const VERSION = 1;
const MAX_CREATURES = 6;
const MAX_PROJECTILES = 12;
const CHAOS_COOLDOWN = 1200;
const activeProjectiles = new Map();
const activeEncounters = new Set();

const playerKey = (player, key) => `${NS}:player:${player.id}:${key}`;
const worldKey = key => `${NS}:world:${key}`;
const numberProperty = (owner, key, fallback = 0) => {
  const value = Number(owner.getDynamicProperty(key));
  return Number.isFinite(value) ? value : fallback;
};
const setOnce = (owner, key) => {
  if (owner.getDynamicProperty(key) === true) return false;
  owner.setDynamicProperty(key, true);
  return true;
};
const reward = (player, item, key) => {
  if (!setOnce(player, playerKey(player, key))) return false;
  player.getComponent("minecraft:inventory")?.container?.addItem(new ItemStack(item, 1));
  return true;
};
const playerFromDamage = event => {
  const source = event.damageSource?.damagingEntity;
  if (source?.typeId === "minecraft:player") return source;
  const owner = source?.getComponent?.("minecraft:projectile")?.owner;
  return owner?.typeId === "minecraft:player" ? owner : undefined;
};
const deterministicOutcome = seed => {
  let x = (Number(seed) || 1) >>> 0;
  x = (Math.imul(x ^ (x >>> 16), 0x45d9f3b) ^ (x >>> 16)) >>> 0;
  return ["haste", "supply", "sprouts"][x % 3];
};

function initializeStructure(player) {
  const dimension = player.dimension;
  const location = { x: 8, y: 64, z: 8 };
  if (!setOnce(world, worldKey("structure_initialized"))) return;
  dimension.runCommand(`structure load ${NS}:signal_ruin ${location.x} ${location.y} ${location.z}`);
  world.setDynamicProperty(worldKey("structure_location"), JSON.stringify(location));
  activeEncounters.add("signal_ruin");
}

function launchWeapon(player) {
  if (!player) return false;
  if (player.getItemCooldown("resonance_sling") > 0) return;
  if (activeProjectiles.size >= MAX_PROJECTILES) {
    player.sendMessage("The sling is stabilizing.");
    return;
  }
  const view = player.getViewDirection();
  const head = player.getHeadLocation();
  const projectile = player.dimension.spawnEntity(`${NS}:resonance_bolt`, {
    x: head.x + view.x * 0.6,
    y: head.y + view.y * 0.6,
    z: head.z + view.z * 0.6,
  });
  const component = projectile.getComponent("minecraft:projectile");
  component.owner = player;
  component.shoot({ x: view.x * 1.4, y: view.y * 1.4, z: view.z * 1.4 });
  activeProjectiles.set(projectile.id, { owner: player.id, expires: system.currentTick + 100 });
  player.startItemCooldown("resonance_sling", 20);
  return true;
}

async function openConsole(player) {
  const form = new ActionFormData()
    .title("Signal Console")
    .body("Choose one bounded action.")
    .button("Initialize encounter")
    .button("Trigger earned anomaly")
    .button("Show progression");
  const result = await form.show(player);
  if (result.canceled) return;
  if (result.selection === 0) initializeStructure(player);
  if (result.selection === 1) triggerChaos(player);
  if (result.selection === 2) {
    const unlocked = player.getDynamicProperty(playerKey(player, "unlock")) === true;
    player.sendMessage(unlocked ? "Resonance attunement: unlocked" : "Resonance attunement: locked");
  }
}

function triggerChaos(player, fixedSeed) {
  if (player.getDynamicProperty(playerKey(player, "unlock")) !== true) {
    player.sendMessage("The console remains dormant.");
    return false;
  }
  const readyAt = numberProperty(world, worldKey("chaos_ready_tick"));
  if (system.currentTick < readyAt) return false;
  const occurrence = numberProperty(world, worldKey("chaos_occurrence"));
  if (occurrence >= 3) return false;
  const seed = fixedSeed ?? (numberProperty(world, worldKey("chaos_seed"), 7305) + occurrence);
  const outcome = deterministicOutcome(seed);
  if (outcome === "haste") player.addEffect("minecraft:haste", 200, { amplifier: 0 });
  if (outcome === "supply") player.dimension.spawnItem(new ItemStack("minecraft:bread", 2), player.location);
  if (outcome === "sprouts") {
    const count = player.dimension.getEntities({ type: `${NS}:mossling` }).length;
    for (let index = count; index < Math.min(MAX_CREATURES, count + 2); index += 1) {
      player.dimension.spawnEntity(`${NS}:mossling`, player.location);
    }
  }
  world.setDynamicProperty(worldKey("chaos_occurrence"), occurrence + 1);
  world.setDynamicProperty(worldKey("chaos_ready_tick"), system.currentTick + CHAOS_COOLDOWN);
  world.sendMessage(`Bounded anomaly: ${outcome}`);
  return true;
}

function migrate() {
  const raw = world.getDynamicProperty(worldKey("state"));
  let state;
  try {
    state = raw ? JSON.parse(String(raw)) : { version: VERSION };
  } catch {
    state = { version: VERSION, recovered_from_corrupt: true };
  }
  if (state.version === 0) state = { ...state, version: VERSION, migrated_from: 0 };
  if (state.version !== VERSION) state = { version: VERSION, recovered_from_unsupported: true };
  world.setDynamicProperty(worldKey("state"), JSON.stringify(state));
  const boot = numberProperty(world, worldKey("boot_count")) + 1;
  world.setDynamicProperty(worldKey("boot_count"), boot);
  console.warn(`[controlled_chaos] runtime initialized persistent_boot=${boot}`);
}

world.afterEvents.itemUse.subscribe(event => {
  if (event.itemStack?.typeId === `${NS}:resonance_sling`) launchWeapon(event.source);
  if (event.itemStack?.typeId === `${NS}:signal_console`) system.run(() => openConsole(event.source));
});
world.afterEvents.projectileHitEntity.subscribe(event => {
  if (event.projectile?.typeId !== `${NS}:resonance_bolt`) return;
  const hit = event.getEntityHit()?.entity;
  let owner;
  try { owner = event.source ?? event.projectile.getComponent("minecraft:projectile")?.owner; } catch {}
  if (owner) hit?.applyDamage(4, { damagingEntity: owner });
  else hit?.applyDamage(4);
  hit?.addEffect("minecraft:slowness", 60, { amplifier: 0 });
  activeProjectiles.delete(event.projectile.id);
  try { if (event.projectile.isValid) event.projectile.remove(); } catch {}
});
world.afterEvents.projectileHitBlock.subscribe(event => {
  if (event.projectile?.typeId !== `${NS}:resonance_bolt`) return;
  activeProjectiles.delete(event.projectile.id);
  try { if (event.projectile.isValid) event.projectile.remove(); } catch {}
});
world.afterEvents.entityDie.subscribe(event => {
  const player = playerFromDamage(event);
  if (!player) return;
  if (event.deadEntity.typeId === `${NS}:mossling`) reward(player, "minecraft:amethyst_shard", "creature_reward");
  if (event.deadEntity.typeId === `${NS}:bramble_guard`) {
    reward(player, `${NS}:boss_key`, "elite_reward");
    world.setDynamicProperty(worldKey("elite_complete"), true);
  }
  if (event.deadEntity.typeId === `${NS}:tempest_warden`) {
    if (setOnce(world, worldKey("boss_rewarded"))) {
      player.setDynamicProperty(playerKey(player, "unlock"), true);
      world.setDynamicProperty(worldKey("boss_complete"), true);
    }
    activeEncounters.delete("boss");
  }
});
world.afterEvents.entityHurt.subscribe(event => {
  const entity = event.hurtEntity;
  if (entity.typeId !== `${NS}:tempest_warden`) return;
  const health = entity.getComponent("minecraft:health");
  const ratio = health.currentValue / health.effectiveMax;
  const phase = numberProperty(entity, `${NS}:phase`, 1);
  if (ratio <= 0.66 && phase === 1) entity.setDynamicProperty(`${NS}:phase`, 2);
  if (ratio <= 0.33 && phase === 2) entity.setDynamicProperty(`${NS}:phase`, 3);
});
world.afterEvents.playerSpawn.subscribe(event => {
  if (!event.initialSpawn) return;
  const player = event.player;
  if (!player) return;
  player.getComponent("minecraft:inventory")?.container?.addItem(new ItemStack(`${NS}:signal_console`, 1));
});
system.run(migrate);
system.runInterval(() => {
  for (const [id, record] of activeProjectiles) {
    if (system.currentTick <= record.expires) continue;
    for (const dimensionName of ["overworld", "nether", "the_end"]) {
      world.getDimension(dimensionName).getEntities().find(entity => entity.id === id)?.remove();
    }
    activeProjectiles.delete(id);
  }
}, 20);

export const qualification = {
  deterministicOutcome,
  limits: { creatures: MAX_CREATURES, projectiles: MAX_PROJECTILES, chaosOccurrences: 3 },
};
