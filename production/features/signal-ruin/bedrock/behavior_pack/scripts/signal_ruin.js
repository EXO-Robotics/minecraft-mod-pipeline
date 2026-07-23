import { world, system } from "@minecraft/server";
const NS = "ccoriginal_cc:signal_ruin_";
const VALID = new Set(["READY","ACTIVE_WAVE_1","ACTIVE_WAVE_2","ACTIVE_WAVE_3","REWARD_READY","COMPLETE"]);
const CAP = 12;
const INSTANCE_CAP = 2;
const ENCOUNTER_SECONDS_CAP = 80;
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
  let count=0;
  for(const d of ["overworld","nether","the_end"].map(x=>world.getDimension(x)))
    for(const a of d.getEntities({type:"ccoriginal_cc:signal_ruin_anchor"}))
      if(state(a).startsWith("ACTIVE_")) count++;
  return count;
}
function spawnWave(a,w){
  const token=Number(get(a,"token",0))+1; set(a,"token",token); set(a,"state","ACTIVE_WAVE_"+w); set(a,"wave",w);
  const id=String(get(a,"instance",a.id)).replace(/[^A-Za-z0-9_-]/g,"_");
  const types=w===1?["minecraft:zombie","minecraft:zombie","minecraft:spider"]:w===2?["minecraft:skeleton","minecraft:skeleton","minecraft:zombie","minecraft:spider"]:["minecraft:husk","minecraft:skeleton","minecraft:zombie","minecraft:spider","minecraft:spider"];
  for(let i=0;i<types.length && mobs(a).length<CAP;i++){ const q=a.dimension.spawnEntity(types[i],{x:a.location.x+(i%3-1)*4,y:a.location.y,z:a.location.z+(Math.floor(i/3)*3+4)}); q.addTag("ccoriginal_cc_signal_ruin_mob"); q.addTag("sri_"+id); }
}
function reward(a){
  if(get(a,"reward_issued",false)) { set(a,"state","COMPLETE"); return; }
  set(a,"state","REWARD_READY"); set(a,"reward_issued",true);
  a.dimension.runCommand(`loot spawn ${a.location.x} ${a.location.y+1} ${a.location.z} loot "ccoriginal_cc/signal_ruin_cache"`);
  set(a,"state","COMPLETE"); world.sendMessage("Signal Ruin completed. One shared cache has formed.");
}
function activate(a,p){
  if(state(a)!=="READY"){ p.sendMessage(state(a)==="COMPLETE"?"This Signal Ruin is quiet; its cache was already issued.":"This Signal Ruin is already active."); return; }
  if(activeInstances()>=INSTANCE_CAP){ p.sendMessage("Only two Signal Ruins may be active at once. This ruin remains ready."); return; }
  set(a,"schema",1); set(a,"instance",a.id); set(a,"reward_issued",false); set(a,"absent_seconds",0); set(a,"elapsed_seconds",0); spawnWave(a,1);
}
world.afterEvents.playerInteractWithEntity.subscribe(e=>{ if(e.target.typeId==="ccoriginal_cc:signal_ruin_anchor") activate(e.target,e.player); });
world.afterEvents.worldLoad.subscribe(()=>system.runTimeout(()=>{
  for(const d of ["overworld","nether","the_end"].map(x=>world.getDimension(x))) for(const a of d.getEntities({type:"ccoriginal_cc:signal_ruin_anchor"})){
    const s=state(a); if(s==="COMPLETE"){set(a,"state","COMPLETE");continue;} if(s.startsWith("ACTIVE_")){clean(a);set(a,"elapsed_seconds",0);spawnWave(a,Math.max(1,Math.min(3,Number(get(a,"wave",1)))));}
  }
},1));
system.runInterval(()=>{
  for(const d of ["overworld","nether","the_end"].map(x=>world.getDimension(x))) for(const a of d.getEntities({type:"ccoriginal_cc:signal_ruin_anchor"})){
    const s=state(a); if(!s.startsWith("ACTIVE_")) continue;
    const elapsed=Number(get(a,"elapsed_seconds",0))+1; set(a,"elapsed_seconds",elapsed);
    if(elapsed>=ENCOUNTER_SECONDS_CAP){ clean(a); set(a,"state","READY"); set(a,"wave",0); set(a,"absent_seconds",0); set(a,"elapsed_seconds",0); continue; }
    const near=d.getPlayers({location:a.location,maxDistance:32});
    if(!near.length){ const absent=Number(get(a,"absent_seconds",0))+1; set(a,"absent_seconds",absent); if(absent>=20){clean(a);set(a,"state","READY");set(a,"wave",0);set(a,"elapsed_seconds",0);} continue; }
    set(a,"absent_seconds",0);
    if(mobs(a).length===0){ const w=Number(get(a,"wave",1)); if(w<3) spawnWave(a,w+1); else reward(a); }
  }
},20);
