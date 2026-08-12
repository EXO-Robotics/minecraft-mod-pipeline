import { CRYSTAL_ACCESSORY_ROLES, CRYSTAL_RANGED_ROLES } from "./crystal_equipment_roles.js";

export function createCrystalEquipmentService({ system, state, arbiter, EntityComponentTypes = {}, EquipmentSlot = {} }) {
  const offhandSlot = EquipmentSlot.Offhand ?? "Offhand";
  const inventory = player => player.getComponent("minecraft:inventory")?.container;
  const offhandType = player => player.getComponent(EntityComponentTypes.Equippable ?? "minecraft:equippable")?.getEquipment(offhandSlot)?.typeId;
  const ready = (player, key, cooldown) => {
    const record = state.playerState(player), now = system.currentTick;
    if ((record.cooldowns[key] ?? 0) > now) return false;
    record.cooldowns[key] = now + cooldown;
    return state.savePlayer(player, record);
  };
  function inventoryOne(player, typeId, consume = false) {
    const container = inventory(player);
    for (let index = 0; index < (container?.size ?? 0); index++) {
      const item = container.getItem(index);
      if (item?.typeId !== typeId) continue;
      if (consume) {
        if (item.amount > 1) { item.amount--; container.setItem(index, item); }
        else container.setItem(index, undefined);
      }
      return true;
    }
    return false;
  }
  function damageSelected(player, itemType, amount) {
    const container = inventory(player), index = player.selectedSlotIndex, item = container?.getItem(index);
    if (item?.typeId !== itemType) return false;
    const durability = item.getComponent?.("minecraft:durability");
    if (!durability) return false;
    durability.damage = Math.min(durability.maxDurability, durability.damage + amount);
    container.setItem(index, durability.damage >= durability.maxDurability ? undefined : item);
    return true;
  }
  function useRanged(player, itemType) {
    const spec = CRYSTAL_RANGED_ROLES[itemType];
    if (!spec) return false;
    const target = player.getEntitiesFromViewDirection({ maxDistance: spec.range })[0]?.entity;
    if (!target) { state.warn(player, "No bounded target is in range."); return false; }
    if (!inventoryOne(player, spec.ammo)) { state.warn(player, "The Prism Bow needs an arrow."); return false; }
    if (!ready(player, `crystal:weapon:${itemType}`, spec.cooldown) || !inventoryOne(player, spec.ammo, true)) return false;
    target.applyDamage(spec.damage, { damagingEntity: player });
    damageSelected(player, itemType, spec.durabilityCost);
    const vector = player.getViewDirection(), head = player.getHeadLocation();
    for (let index = 1; index <= spec.particles && arbiter.spend("particlesAction"); index++) {
      player.dimension.spawnParticle("minecraft:endrod", {
        x: head.x + vector.x * index * 1.5,
        y: head.y + vector.y * index * 1.5,
        z: head.z + vector.z * index * 1.5,
      });
    }
    return true;
  }
  function tickPlayer(player) {
    if (CRYSTAL_ACCESSORY_ROLES[offhandType(player)] !== "wet_vision") return false;
    const block = player.dimension.getBlock?.(player.location);
    if (!player.isInWater && block?.typeId !== "minecraft:water") return false;
    player.addEffect("night_vision", 60, { amplifier: 0, showParticles: false });
    return true;
  }
  return Object.freeze({ useRanged, tickPlayer });
}
