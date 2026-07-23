import { system, world } from "@minecraft/server";
const NS="ccoriginal_cc", SLING=`${NS}:resonance_sling`, AMMO=`${NS}:resonance_pebble`, PULSE=`${NS}:resonance_pulse`;
const activeByOwner=new Map(), processed=new Set(); let activeGlobal=0;
function tell(p,m){ try { p.onScreenDisplay.setActionBar(m); } catch { p.sendMessage(m); } }
function consume(player){
  const inv=player.getComponent("minecraft:inventory")?.container;
  if(!inv) return false;
  for(let i=0;i<inv.size;i++){ const s=inv.getItem(i); if(s?.typeId===AMMO){ if(s.amount>1){s.amount--;inv.setItem(i,s);}else inv.setItem(i); return true; } }
  return false;
}
function damageSling(player){
  const inv=player.getComponent("minecraft:inventory")?.container; if(!inv)return;
  const slot=player.selectedSlotIndex, stack=inv.getItem(slot); if(stack?.typeId!==SLING)return;
  const d=stack.getComponent("minecraft:durability"); if(!d)return;
  d.damage++; if(d.damage>=d.maxDurability) inv.setItem(slot); else inv.setItem(slot,stack);
}
function release(projectile,ownerId){
  if(!projectile)return; processed.delete(projectile.id); activeGlobal=Math.max(0,activeGlobal-1);
  activeByOwner.set(ownerId,Math.max(0,(activeByOwner.get(ownerId)||1)-1));
  try { projectile.remove(); } catch {}
}
function fire(player){
  const own=activeByOwner.get(player.id)||0;
  if(player.getItemCooldown("resonance_sling")>0){tell(player,"§7Resonance is re-forming.");return;}
  if(own>=4||activeGlobal>=16){tell(player,"§cToo many pulses are active.");return;}
  if(!consume(player)){tell(player,"§eResonance Pebbles required.");return;}
  const head=player.getHeadLocation(), direction=player.getViewDirection();
  const p=player.dimension.spawnEntity(PULSE,{x:head.x+direction.x,y:head.y+direction.y,z:head.z+direction.z});
  const projectile=p.getComponent("minecraft:projectile"); projectile.owner=player; projectile.shoot({x:direction.x*1.55,y:direction.y*1.55,z:direction.z*1.55});
  activeByOwner.set(player.id,own+1); activeGlobal++; player.startItemCooldown("resonance_sling",16); damageSling(player);
  player.dimension.playSound("random.orb",head); tell(player,"§bResonance released");
  system.runTimeout(()=>release(p,player.id),60);
}
world.afterEvents.itemUse.subscribe(e=>{if(e.itemStack?.typeId===SLING)fire(e.source);});
world.afterEvents.projectileHitEntity.subscribe(e=>{
  const p=e.projectile; if(p.typeId!==PULSE||processed.has(p.id))return; processed.add(p.id);
  const owner=p.getComponent("minecraft:projectile")?.owner, target=e.getEntityHit()?.entity;
  if(owner?.isValid&&target?.isValid){target.applyDamage(4,{damagingEntity:owner}); const v=owner.getViewDirection(); target.applyImpulse({x:v.x*.7,y:.14,z:v.z*.7});}
  try{p.dimension.spawnParticle("ccoriginal_cc:resonance_impact",p.location);}catch{} release(p,owner?.id||"invalid");
});
world.afterEvents.projectileHitBlock.subscribe(e=>{const p=e.projectile;if(p.typeId!==PULSE||processed.has(p.id))return;processed.add(p.id);const o=p.getComponent("minecraft:projectile")?.owner;try{p.dimension.spawnParticle("ccoriginal_cc:resonance_impact",p.location);}catch{}release(p,o?.id||"invalid");});
world.afterEvents.playerSpawn.subscribe(e=>{if(e.initialSpawn)system.runTimeout(()=>e.player.sendMessage("§a[Resonance Sling] ORIGINAL INTERNAL TEST BUILD initialized"),20);});
console.warn("[resonance-sling] script runtime initialized stable_api=2.0.0 persistent_records=0 global_scan_per_tick=0 cap=16");
