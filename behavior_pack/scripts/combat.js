import { COMBINED_BUDGETS } from "./budgets.js";
import { ACCESSORY_ROLES, ARMOR_SETS, CONSUMABLE_EFFECTS, MELEE_WEAPON_ROLES, NATURAL_ENTITY_IDS, RANGED_WEAPON_ROLES } from "./catalog.js";

export function createCombatService({ world, system, ItemStack, EquipmentSlot = {}, EntityComponentTypes = {}, state, arbiter, boundedEntities, consumeOne }) {
  const slot = {
    offhand: EquipmentSlot.Offhand ?? "Offhand", head: EquipmentSlot.Head ?? "Head", chest: EquipmentSlot.Chest ?? "Chest",
    legs: EquipmentSlot.Legs ?? "Legs", feet: EquipmentSlot.Feet ?? "Feet",
  };
  const equippable = player => player.getComponent(EntityComponentTypes.Equippable ?? "minecraft:equippable");
  const selectedType = player => player.getComponent("minecraft:inventory")?.container?.getItem(player.selectedSlotIndex)?.typeId;
  const offhandType = player => equippable(player)?.getEquipment(slot.offhand)?.typeId;
  const ready = (player, key, cooldown) => {
    const p = state.playerState(player), now = system.currentTick;
    if ((p.cooldowns[key] ?? 0) > now) return false;
    p.cooldowns[key] = now + cooldown; return state.savePlayer(player, p);
  };
  function useBarkling(player) {
    const all = boundedEntities("aionbound:barkling_familiar");
    if (all.some(x => x.getDynamicProperty("aionbound:owner") === player.id) || all.length >= COMBINED_BUDGETS.familiarsWorld) return state.warn(player, "Your familiar is already present or the familiar cap is full.");
    const entity = player.dimension.spawnEntity("aionbound:barkling_familiar", { x: player.location.x + 1, y: player.location.y, z: player.location.z });
    entity.setDynamicProperty("aionbound:owner", player.id); if (!consumeOne(player, "aionbound:barkling_token")) entity.remove();
  }
  function useRay(player) {
    const p = state.playerState(player), now = system.currentTick;
    if ((p.cooldowns.ray ?? 0) > now) return state.warn(player, "Vector Ray cooldown is active.");
    const target = player.getEntitiesFromViewDirection({ maxDistance: COMBINED_BUDGETS.rayRange })[0]?.entity;
    if (!target) return state.warn(player, "No view target within 24 blocks.");
    target.applyDamage(6, { damagingEntity: player });
    const vector = player.getViewDirection(), head = player.getHeadLocation();
    for (let i = 1; i <= COMBINED_BUDGETS.rayParticles && arbiter.spend("particlesAction"); i++) player.dimension.spawnParticle("minecraft:basic_flame_particle", { x: head.x + vector.x * i * 1.5, y: head.y + vector.y * i * 1.5, z: head.z + vector.z * i * 1.5 });
    p.cooldowns.ray = now + COMBINED_BUDGETS.rayCooldown; state.savePlayer(player, p);
  }
  function useWhistle(player) {
    const all = boundedEntities("aionbound:waykeeper_courser");
    if (all.some(x => x.getDynamicProperty("aionbound:owner") === player.id) || all.length >= COMBINED_BUDGETS.mountsWorld) return state.warn(player, "Courser admission refused before consumption.");
    const entity = player.dimension.spawnEntity("aionbound:waykeeper_courser", player.location); entity.setDynamicProperty("aionbound:owner", player.id);
    if (!consumeOne(player, "aionbound:waykeeper_whistle")) entity.remove();
  }
  function mountStep(event) {
    if (event.entity.typeId === "aionbound:waykeeper_courser" && Math.abs(event.entity.getVelocity().x) + Math.abs(event.entity.getVelocity().z) > 0.08) event.entity.applyImpulse({ x: 0, y: 0.18, z: 0 });
  }
  function glasswingDeath(event) {
    if (event.deadEntity.typeId !== "aionbound:glasswing_sentinel") return false;
    const player = event.damageSource.damagingEntity;
    if (player?.typeId === "minecraft:player" && state.stamp(player, "glasswing:first_defeat")) player.dimension.spawnItem(new ItemStack("minecraft:phantom_membrane", 1), player.location);
    return true;
  }
  function useRanged(player, itemType) {
    const spec = RANGED_WEAPON_ROLES[itemType]; if (!spec || !ready(player, `weapon:${itemType}`, spec.cooldown)) return false;
    const target = player.getEntitiesFromViewDirection({ maxDistance: Math.min(spec.range, COMBINED_BUDGETS.rayRange) })[0]?.entity;
    if (!target) { state.warn(player, "No bounded target is in range."); return false; }
    target.applyDamage(spec.damage, { damagingEntity: player });
    const vector = player.getViewDirection();
    if (spec.role === "force_burst") target.applyImpulse?.({ x: vector.x * 0.8, y: 0.18, z: vector.z * 0.8 });
    const head = player.getHeadLocation();
    for (let index = 1; index <= spec.particles && arbiter.spend("particlesAction"); index++) player.dimension.spawnParticle("minecraft:basic_flame_particle", { x: head.x + vector.x * index * 1.5, y: head.y + vector.y * index * 1.5, z: head.z + vector.z * index * 1.5 });
    return true;
  }
  function routeMeleeHurt(event) {
    const target = event.hurtEntity, player = event.damageSource?.damagingEntity;
    if (player?.typeId !== "minecraft:player") return false;
    const itemType = selectedType(player), spec = MELEE_WEAPON_ROLES[itemType];
    if (!spec || !ready(player, `weapon:${itemType}`, spec.cooldown)) return false;
    if (spec.role === "ignite") target.setOnFire?.(3, true);
    if (spec.role === "reposition") { const vector = player.getViewDirection(); target.applyImpulse?.({ x: vector.x * 0.65, y: 0.12, z: vector.z * 0.65 }); }
    if (spec.role === "venom") target.addEffect?.("poison", 60, { amplifier: 0, showParticles: true });
    if (spec.role === "lift") target.applyImpulse?.({ x: 0, y: 0.42, z: 0 });
    if (spec.role === "bounded_shockwave") {
      let applied = 0;
      for (const entity of target.dimension.getEntities({ location: target.location, maxDistance: 4 })) {
        if (entity.id === target.id || entity.id === player.id || applied >= spec.targets || !arbiter.spend("entityQuery")) continue;
        entity.applyDamage?.(2, { damagingEntity: player }); applied++;
      }
    }
    return true;
  }
  function useConsumable(player, itemType) {
    const effects = CONSUMABLE_EFFECTS[itemType]; if (!effects) return false;
    for (const [name, duration, amplifier] of effects) player.addEffect(name, duration, { amplifier, showParticles: true });
    return true;
  }
  function accessoryPulse(player, itemType) {
    if (itemType === "aionbound:mote_lantern") { player.addEffect("night_vision", 300, { amplifier: 0, showParticles: false }); state.warn(player, "The lantern brightens around known Aionbound traces."); return true; }
    if (itemType === "aionbound:wayfinder_spool") { state.warn(player, "The spool points toward an undiscovered waystone, ruin, or pilgrimage trace."); return true; }
    return false;
  }
  function handlePlayerHurt(event) {
    const player = event.hurtEntity; if (player?.typeId !== "minecraft:player") return false;
    const accessory = offhandType(player), role = ACCESSORY_ROLES[accessory];
    if (role === "fall_mitigation" && event.damageSource?.cause === "fall") { player.addEffect("slow_falling", 100, { amplifier: 0, showParticles: false }); player.addEffect("regeneration", 60, { amplifier: 0, showParticles: false }); return true; }
    if (role === "ward_cooldown" && ready(player, "accessory:ward", 240)) { player.addEffect("resistance", 80, { amplifier: 0, showParticles: true }); return true; }
    return false;
  }
  function armorSet(player) {
    const equipment = equippable(player); if (!equipment) return null;
    const ids = [equipment.getEquipment(slot.head)?.typeId, equipment.getEquipment(slot.chest)?.typeId, equipment.getEquipment(slot.legs)?.typeId, equipment.getEquipment(slot.feet)?.typeId];
    if (ARMOR_SETS.ferrowake.every((id, index) => ids[index] === id)) return "ferrowake";
    if (ARMOR_SETS.concord.every((id, index) => ids[index] === id)) return "concord";
    return null;
  }
  function tickPlayers() {
    for (const player of world.getAllPlayers()) {
      const accessory = offhandType(player), role = ACCESSORY_ROLES[accessory];
      if (role === "landmark_pulse") player.addEffect("night_vision", 60, { amplifier: 0, showParticles: false });
      if (role === "fall_mitigation") player.addEffect("slow_falling", 60, { amplifier: 0, showParticles: false });
      if (role === "resource_hint" && system.currentTick % 100 === 0) {
        const block = player.getBlockFromViewDirection?.({ maxDistance: 8 })?.block;
        if (block?.typeId?.startsWith("aionbound:") && /(ore|cluster|nodule)/.test(block.typeId)) state.warn(player, `Quarry Lens: ${block.typeId.replace("aionbound:", "").replaceAll("_", " ")}.`);
      }
      if (role === "anchor_guidance" && system.currentTick % 100 === 0) state.warn(player, "Wayfinder: seek an unrecorded landmark or pilgrimage trace.");
      if (role === "bounded_item_pull") {
        let pulled = 0;
        for (const entity of player.dimension.getEntities({ type: "minecraft:item", location: player.location, maxDistance: 6 })) {
          if (pulled >= 8 || !arbiter.spend("entityQuery")) break;
          const dx = player.location.x - entity.location.x, dy = player.location.y + 0.5 - entity.location.y, dz = player.location.z - entity.location.z;
          entity.applyImpulse?.({ x: dx * 0.05, y: dy * 0.05, z: dz * 0.05 }); pulled++;
        }
      }
      const set = armorSet(player);
      if (set === "ferrowake") player.addEffect("haste", 60, { amplifier: 0, showParticles: false });
      if (set === "concord") { player.addEffect("resistance", 60, { amplifier: 0, showParticles: false }); player.addEffect("speed", 60, { amplifier: 0, showParticles: false }); }
    }
  }
  function reconcileNaturalEntities() {
    const natural = NATURAL_ENTITY_IDS.flatMap(typeId => boundedEntities(typeId));
    natural.sort((left, right) => `${left.typeId}:${left.id}`.localeCompare(`${right.typeId}:${right.id}`));
    for (const entity of natural.slice(COMBINED_BUDGETS.naturalEntitiesTarget)) entity.remove();
    return { observed: natural.length, removed: Math.max(0, natural.length - COMBINED_BUDGETS.naturalEntitiesTarget) };
  }
  return { useBarkling, useRay, useWhistle, mountStep, glasswingDeath, reconcileNaturalEntities, useRanged, routeMeleeHurt, useConsumable, accessoryPulse, handlePlayerHurt, armorSet, tickPlayers };
}
