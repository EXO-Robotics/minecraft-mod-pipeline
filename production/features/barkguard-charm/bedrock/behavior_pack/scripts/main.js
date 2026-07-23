import { EquipmentSlot, EntityComponentTypes, system, world } from "@minecraft/server";

const ITEM = "ccoriginal_cc:barkguard_charm";
const COOLDOWN = "barkguard_charm";
const DAMAGE_THRESHOLD = 2;
const EFFECT_TICKS = 60;
const COOLDOWN_TICKS = 240;
const lastHandledTick = new Map();

function tryActivate(player, damage) {
  if (damage < DAMAGE_THRESHOLD || player.getItemCooldown(COOLDOWN) > 0) return false;
  const equippable = player.getComponent(EntityComponentTypes.Equippable);
  const charm = equippable?.getEquipment(EquipmentSlot.Offhand);
  if (!charm || charm.typeId !== ITEM) return false;

  const tick = system.currentTick;
  if (lastHandledTick.get(player.id) === tick) return false;
  lastHandledTick.set(player.id, tick);

  const durability = charm.getComponent("minecraft:durability");
  if (!durability) return false;
  player.addEffect("resistance", EFFECT_TICKS, { amplifier: 0, showParticles: true });
  player.startItemCooldown(COOLDOWN, COOLDOWN_TICKS);
  const nextDamage = durability.damage + 1;
  if (nextDamage >= durability.maxDurability) {
    equippable.setEquipment(EquipmentSlot.Offhand, undefined);
    player.sendMessage("§6Your Barkguard Charm returns to the forest.");
  } else {
    durability.damage = nextDamage;
    equippable.setEquipment(EquipmentSlot.Offhand, charm);
  }
  return true;
}

world.afterEvents.entityHurt.subscribe((event) => {
  const player = event.hurtEntity;
  if (player?.typeId !== "minecraft:player") return;
  tryActivate(player, event.damage);
});

world.afterEvents.playerLeave.subscribe((event) => lastHandledTick.delete(event.playerId));
console.warn("[barkguard-charm] stable_api=2.0.0 event_driven=true global_scans_per_tick=0 persistent_records=0");
