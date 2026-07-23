import { ItemStack, world, system } from "@minecraft/server";
const NS = "ccoriginal_cc:signal_ruin_";
const VALID = new Set(["READY","ACTIVE_WAVE_1","ACTIVE_WAVE_2","ACTIVE_WAVE_3","REWARD_READY","COMPLETE"]);
const CAP = 12;
const INSTANCE_CAP = 2;
const ENCOUNTER_SECONDS_CAP = 80;
const activeAnchors = new Map();
function get(a,k,d){ const v=a.getDynamicProperty(NS+k); return v===undefined?d:v; }
function set(a,k,v){ a.setDynamicProperty(NS+k,v); }
function state(a){
  const reward=!!get(a,"reward_issued",false), raw=String(get(a,"state","READY"));
  if(reward) return "COMPLETE";
  return VALID.has(raw)?raw:"READY";
}
function mobs(a){ const id=String(get(a,"instance",a.id)).replace(/[^A-Za-z0-9_-]/g,"_"); return a.dimension.getEntities({tags:["ccoriginal_cc_signal_ruin_mob","sri_"+id]}); }
function clean(a){ for(const e of mobs(a)) e.remove(); set(a,"token",Number(get(a,"token",0))+1); }
function activeInstances(){
  return activeAnchors.size;
}
function spawnWave(a,w){
  const token=Number(get(a,"token",0))+1; set(a,"token",token); set(a,"state","ACTIVE_WAVE_"+w); set(a,"wave",w);
  const id=String(get(a,"instance",a.id)).replace(/[^A-Za-z0-9_-]/g,"_");
  const types=w===1?["minecraft:zombie","minecraft:zombie","minecraft:spider"]:w===2?["minecraft:skeleton","minecraft:skeleton","minecraft:zombie","minecraft:spider"]:["minecraft:husk","minecraft:skeleton","minecraft:zombie","minecraft:spider","minecraft:spider"];
  for(let i=0;i<types.length && mobs(a).length<CAP;i++){ const q=a.dimension.spawnEntity(types[i],{x:a.location.x+(i%3-1)*4,y:a.location.y,z:a.location.z+(Math.floor(i/3)*3+4)}); q.addTag("ccoriginal_cc_signal_ruin_mob"); q.addTag("sri_"+id); }
}
function cacheTag(a){ return "sri_cache_"+String(get(a,"instance",a.id)).replace(/[^A-Za-z0-9_-]/g,"_"); }
function materializeCache(a){
  const tag=cacheTag(a);
  let cache=a.dimension.getEntities({type:"minecraft:chest_minecart",tags:[tag],location:a.location,maxDistance:4})[0];
  if(!cache){ cache=a.dimension.spawnEntity("minecraft:chest_minecart",{x:a.location.x,y:a.location.y+1,z:a.location.z}); cache.addTag("ccoriginal_cc_signal_ruin_cache"); cache.addTag(tag); cache.nameTag="Signal Ruin Shared Cache"; }
  const container=cache.getComponent("minecraft:inventory")?.container;
  if(!container) throw new Error("Signal Ruin cache inventory unavailable");
  container.clearAll(); container.setItem(0,new ItemStack("minecraft:chest",1)); container.setItem(1,new ItemStack("minecraft:emerald",3));
  return cache;
}
function reward(a){
  if(get(a,"reward_issued",false)) { set(a,"state","COMPLETE"); return; }
  set(a,"state","REWARD_READY");
  materializeCache(a);
  set(a,"reward_issued",true); set(a,"state","COMPLETE"); activeAnchors.delete(a.id);
  world.setDynamicProperty("ccoriginal_cc:signal_ruin_completed",true);
  world.sendMessage("Signal Ruin completed. One shared cache has formed.");
}
function activate(a,p){
  if(state(a)!=="READY"){ p.sendMessage(state(a)==="COMPLETE"?"This Signal Ruin is quiet; its cache was already issued.":"This Signal Ruin is already active."); return; }
  if(activeInstances()>=INSTANCE_CAP){ p.sendMessage("Only two Signal Ruins may be active at once. This ruin remains ready."); return; }
  activeAnchors.set(a.id,a);
  try { set(a,"schema",1); set(a,"instance",a.id); set(a,"reward_issued",false); set(a,"absent_seconds",0); set(a,"elapsed_seconds",0); spawnWave(a,1); }
  catch(error){ activeAnchors.delete(a.id); set(a,"state","READY"); throw error; }
}
world.afterEvents.playerInteractWithEntity.subscribe(e=>{ if(e.target.typeId==="ccoriginal_cc:signal_ruin_anchor") activate(e.target,e.player); });
world.afterEvents.worldLoad.subscribe(()=>system.runTimeout(()=>{
  for(const d of ["overworld","nether","the_end"].map(x=>world.getDimension(x))) for(const a of d.getEntities({type:"ccoriginal_cc:signal_ruin_anchor"})){
    const s=state(a); if(s==="COMPLETE"){set(a,"state","COMPLETE");continue;} if(s==="REWARD_READY"){activeAnchors.set(a.id,a);continue;} if(s.startsWith("ACTIVE_")){activeAnchors.set(a.id,a);clean(a);set(a,"elapsed_seconds",0);spawnWave(a,Math.max(1,Math.min(3,Number(get(a,"wave",1)))));}
  }
},1));
system.runInterval(()=>{
  for(const [id,a] of activeAnchors){
    try {
    const s=state(a); if(s==="REWARD_READY"){reward(a);continue;} if(!s.startsWith("ACTIVE_")){activeAnchors.delete(id);continue;}
    const elapsed=Number(get(a,"elapsed_seconds",0))+1; set(a,"elapsed_seconds",elapsed);
    if(elapsed>=ENCOUNTER_SECONDS_CAP){ clean(a); set(a,"state","READY"); set(a,"wave",0); set(a,"absent_seconds",0); set(a,"elapsed_seconds",0); activeAnchors.delete(id); continue; }
    const near=a.dimension.getPlayers({location:a.location,maxDistance:32});
    if(!near.length){ const absent=Number(get(a,"absent_seconds",0))+1; set(a,"absent_seconds",absent); if(absent>=20){clean(a);set(a,"state","READY");set(a,"wave",0);set(a,"elapsed_seconds",0);activeAnchors.delete(id);} continue; }
    set(a,"absent_seconds",0);
    if(mobs(a).length===0){ const w=Number(get(a,"wave",1)); if(w<3) spawnWave(a,w+1); else reward(a); }
    } catch(error) { activeAnchors.delete(id); console.warn(`[Signal Ruin] removed invalid active anchor ${id}: ${error}`); }
  }
},20);
