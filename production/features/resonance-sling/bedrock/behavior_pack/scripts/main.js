import { system, world } from "@minecraft/server";
const NS="ccoriginal_cc", SLING=`${NS}:resonance_sling`, AMMO=`${NS}:resonance_pebble`, PULSE=`${NS}:resonance_pulse`;
const activeByOwner=new Map(), ownerByProjectile=new Map(); let activeGlobal=0;
function releaseId(projectileId){
  if(!ownerByProjectile.has(projectileId))return;const ownerId=ownerByProjectile.get(projectileId);ownerByProjectile.delete(projectileId);activeGlobal=Math.max(0,activeGlobal-1);
  if(ownerId)activeByOwner.set(ownerId,Math.max(0,(activeByOwner.get(ownerId)||1)-1));
}
function removeProjectile(projectile){if(!projectile)return;let id;try{id=projectile.id;}catch{}if(id)releaseId(id);try{if(projectile.isValid)projectile.remove();}catch{}}
world.afterEvents.entitySpawn.subscribe(e=>{if(e.entity.typeId!==PULSE)return;const p=e.entity;system.run(()=>{
  if(!p?.isValid)return;const owner=p.getComponent("minecraft:projectile")?.owner,ownerId=owner?.id,own=ownerId?(activeByOwner.get(ownerId)||0):0;
  if((ownerId&&own>=4)||activeGlobal>=16){try{owner?.sendMessage("§cToo many resonance pulses are active.");}catch{}removeProjectile(p);return;}
  if(ownerId)activeByOwner.set(ownerId,own+1);activeGlobal++;ownerByProjectile.set(p.id,ownerId);system.runTimeout(()=>removeProjectile(p),60);
});});
world.afterEvents.entityRemove.subscribe(e=>{if(e.removedEntityTypeId===PULSE)releaseId(e.removedEntityId);});
world.afterEvents.playerSpawn.subscribe(e=>{const p=e.player;if(e.initialSpawn&&p)system.runTimeout(()=>{if(p?.isValid)p.sendMessage("§a[Resonance Sling] ORIGINAL INTERNAL TEST BUILD initialized");},20);});
console.warn("[resonance-sling] script runtime initialized stable_api=2.0.0 persistent_records=0 global_scan_per_tick=0 cap=16");
