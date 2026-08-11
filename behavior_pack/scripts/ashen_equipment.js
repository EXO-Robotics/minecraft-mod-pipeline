import { ASHEN_ACCESSORY_ROLES, ASHEN_ARMOR_SET, ASHEN_ARMORED_TARGETS, ASHEN_MELEE_ROLES, ASHEN_RANGED_ROLES } from "./ashen_equipment_roles.js";

export function createAshenEquipmentService({ world, system, state, arbiter, EquipmentSlot = {}, EntityComponentTypes = {} }) {
  const slot = {
    offhand: EquipmentSlot.Offhand ?? "Offhand", head: EquipmentSlot.Head ?? "Head", chest: EquipmentSlot.Chest ?? "Chest",
    legs: EquipmentSlot.Legs ?? "Legs", feet: EquipmentSlot.Feet ?? "Feet",
  };
  const equippable = player => player.getComponent(EntityComponentTypes.Equippable ?? "minecraft:equippable");
  const inventory = player => player.getComponent("minecraft:inventory")?.container;
  const selected = player => inventory(player)?.getItem(player.selectedSlotIndex);
  const offhandType = player => equippable(player)?.getEquipment(slot.offhand)?.typeId;
  const ready = (player, key, cooldown) => {
    const record = state.playerState(player), now = system.currentTick;
    if ((record.cooldowns[key] ?? 0) > now) return false;
    record.cooldowns[key] = now + cooldown; return state.savePlayer(player, record);
  };
  function inventoryOne(player, typeId, consume = false) {
    const container = inventory(player);
    for (let index = 0; index < (container?.size ?? 0); index++) {
      const item = container.getItem(index); if (item?.typeId !== typeId) continue;
      if (consume) { if (item.amount > 1) { item.amount--; container.setItem(index, item); } else container.setItem(index, undefined); }
      return true;
    }
    return false;
  }
  function damageSelected(player, itemType, amount = 1) {
    const container = inventory(player), index = player.selectedSlotIndex, item = container?.getItem(index);
    if (item?.typeId !== itemType) return false;
    const durability = item.getComponent?.("minecraft:durability"); if (!durability) return false;
    durability.damage = Math.min(durability.maxDurability, durability.damage + amount);
    container.setItem(index, durability.damage >= durability.maxDurability ? undefined : item); return true;
  }
  function routeMeleeHurt(event) {
    const target = event.hurtEntity, player = event.damageSource?.damagingEntity;
    if (player?.typeId !== "minecraft:player") return false;
    const itemType = selected(player)?.typeId, spec = ASHEN_MELEE_ROLES[itemType];
    if (!spec || !ready(player, `ashen:weapon:${itemType}`, spec.cooldown)) return false;
    if (spec.role === "basalt_stun") {
      target.addEffect?.("slowness", spec.stunTicks, { amplifier: 0, showParticles: false });
      if (ASHEN_ARMORED_TARGETS.has(target.typeId)) target.addEffect?.("weakness", spec.armoredWeaknessTicks, { amplifier: 0, showParticles: false });
    }
    if (spec.role === "wide_heat_pressure") {
      target.setOnFire?.(spec.fireSeconds, true); let applied = 0;
      for (const entity of target.dimension.getEntities({ location: target.location, maxDistance: spec.radius, families: ["monster"] })) {
        if (entity.id === target.id || entity.id === player.id || applied >= spec.targets || !arbiter.spend("entityQuery")) continue;
        entity.applyDamage?.(spec.pressureDamage, { damagingEntity: player }); entity.setOnFire?.(spec.fireSeconds, true); applied++;
      }
    }
    return true;
  }
  function useRanged(player, itemType) {
    const spec = ASHEN_RANGED_ROLES[itemType]; if (!spec) return false;
    const target = player.getEntitiesFromViewDirection({ maxDistance: spec.range })[0]?.entity;
    if (!target) { state.warn(player, "No bounded target is in range."); return false; }
    if (!inventoryOne(player, spec.ammo)) { state.warn(player, "The Ash Repeater needs a volcanic glass shard."); return false; }
    if (!ready(player, `ashen:weapon:${itemType}`, spec.cooldown) || !inventoryOne(player, spec.ammo, true)) return false;
    target.applyDamage(spec.damage, { damagingEntity: player }); target.setOnFire?.(spec.fireSeconds, true); damageSelected(player, itemType, spec.durabilityCost);
    const vector = player.getViewDirection(), head = player.getHeadLocation();
    for (let index = 1; index <= spec.particles && arbiter.spend("particlesAction"); index++) player.dimension.spawnParticle("minecraft:basic_flame_particle", { x: head.x + vector.x * index * 1.5, y: head.y + vector.y * index * 1.5, z: head.z + vector.z * index * 1.5 });
    return true;
  }
  function armorSet(player) {
    const equipment = equippable(player); if (!equipment) return false;
    const ids = [slot.head, slot.chest, slot.legs, slot.feet].map(key => equipment.getEquipment(key)?.typeId);
    return ASHEN_ARMOR_SET.every((id, index) => ids[index] === id);
  }
  function handlePlayerHurt(event) {
    const player = event.hurtEntity; if (player?.typeId !== "minecraft:player" || ASHEN_ACCESSORY_ROLES[offhandType(player)] !== "heat_ward") return false;
    if (!["fire", "fireTick", "lava", "magma"].includes(event.damageSource?.cause) || !ready(player, "ashen:accessory:ember_totem", 200)) return false;
    player.addEffect("fire_resistance", 200, { amplifier: 0, showParticles: false }); return true;
  }
  function tickPlayers() {
    for (const player of world.getAllPlayers()) {
      if (ASHEN_ACCESSORY_ROLES[offhandType(player)] === "heat_ward") player.addEffect("fire_resistance", 60, { amplifier: 0, showParticles: false });
      if (armorSet(player)) player.addEffect("fire_resistance", 60, { amplifier: 0, showParticles: false });
    }
  }
  return Object.freeze({ routeMeleeHurt, useRanged, armorSet, handlePlayerHurt, tickPlayers });
}
