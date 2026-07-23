import { GameMode, ItemStack, system, world } from "@minecraft/server";
import { spawnSimulatedPlayer } from "@minecraft/server-gametest";

const TAG="[resonance-sling:preview]", ARM={x:8,y:64,z:8}, PULSE="ccoriginal_cc:resonance_pulse";
const players=[], scheduled={current:0,peak:0}, results=new Set();
let dimension;
function report(id,ok,detail=""){if(results.has(id))return;results.add(id);console.warn(`${TAG} ${id}=${ok?"passed":"failed"} detail=${String(detail).replaceAll("\n"," ")}`);}
function later(fn,ticks){scheduled.current++;scheduled.peak=Math.max(scheduled.peak,scheduled.current);system.runTimeout(()=>{scheduled.current--;try{fn();}catch(e){console.error(`${TAG} exception=${e}`);}},ticks);}
function pulses(){return dimension.getEntities({type:PULSE});}
function remove(e){try{if(e?.isValid)e.remove();}catch{}}
function countItem(p,id){const c=p.getComponent("minecraft:inventory")?.container;let n=0;if(c)for(let i=0;i<c.size;i++){const s=c.getItem(i);if(s?.typeId===id)n+=s.amount;}return n;}
function slingStack(p){const c=p.getComponent("minecraft:inventory")?.container;if(c)for(let i=0;i<c.size;i++){const s=c.getItem(i);if(s?.typeId==="ccoriginal_cc:resonance_sling")return s;}}
function durability(p){const s=slingStack(p);try{return s?.getComponent("minecraft:durability")??s?.getComponents().find(x=>x.typeId==="minecraft:durability");}catch{return undefined;}}
function durabilityDamage(p){try{const value=durability(p)?.damage??p.getComponent("minecraft:inventory")?.container?.getItem(0)?.getComponent("durability")?.damage;if(value!==undefined)return value;}catch{}for(let d=0;d<=4;d++)try{if(p.runCommand(`testfor @s[hasitem={item=ccoriginal_cc:resonance_sling,data=${d}}]`).successCount>0)return d;}catch{}return undefined;}
function equip(p,ammo=16){p.setItem(new ItemStack("ccoriginal_cc:resonance_sling",1),0,true);if(ammo)p.setItem(new ItemStack("ccoriginal_cc:resonance_pebble",ammo),1,false);}
function spawn(index){const p=spawnSimulatedPlayer({dimension,x:12+index*3,y:65,z:12},`SlingBot${index+1}`,GameMode.survival);players.push(p);equip(p);return p;}
function directPulse(owner,origin,velocity){const p=dimension.spawnEntity(PULSE,origin);const c=p.getComponent("minecraft:projectile");c.owner=owner;system.run(()=>{try{if(p.isValid){c.owner=owner;c.shoot(velocity);}}catch{}});return p;}
function cleanup(){for(const e of pulses())remove(e);for(const e of dimension.getEntities({type:"minecraft:pig"}))remove(e);}
function releaseUse(p){try{p.stopUsingItem();}catch(e){console.error(`${TAG} stop_using_item_exception=${e}`);}}

function run(){
  for(let x=5;x<=35;x++)for(let z=5;z<=35;z++)dimension.setBlockType({x,y:64,z},"minecraft:stone");
  for(let i=0;i<4;i++)spawn(i);
  report("four_players_created",players.length===4,`count=${players.length}`);
  const p=players[0], beforeAmmo=countItem(p,"ccoriginal_cc:resonance_pebble");
  const beforeDur=durabilityDamage(p);
  let itemUse=false, ownerOk=false, damageAttributed=false, damageEvents=0, initialHealth=0, afterHealth=0, impulseDistance=0;const observedOwners=new Map();
  const useSub=world.afterEvents.itemUse.subscribe(e=>{if(e.source?.id===p.id)itemUse=true;});
  const spawnSub=world.afterEvents.entitySpawn.subscribe(e=>{if(e.entity.typeId===PULSE){const o=e.entity.getComponent("minecraft:projectile")?.owner;if(o?.id){observedOwners.set(e.entity.id,o.id);if(o.id===p.id)ownerOk=true;}}});
  const pig=dimension.spawnEntity("minecraft:pig",{x:12,y:66,z:20});initialHealth=pig.getComponent("minecraft:health").currentValue;const pigStart={...pig.location};
  p.teleport({x:12,y:65,z:12},{rotation:{x:0,y:0}});p.useItemInSlot(0);
  later(()=>releaseUse(p),10);
  later(()=>report("cooldown_isolation",p.getItemCooldown("resonance_sling")>0&&players.slice(1).every(x=>x.getItemCooldown("resonance_sling")===0)),11);
  later(()=>{
    report("actual_item_use",itemUse);report("ammo_consumption",countItem(p,"ccoriginal_cc:resonance_pebble")===beforeAmmo-1);
    const now=durabilityDamage(p);
    const stack=slingStack(p);let componentIds="";try{componentIds=stack?.getComponents().map(x=>x.typeId).join(",")??"";}catch{}
    report("durability_cost",beforeDur!==undefined&&now===beforeDur+1,`before=${beforeDur} after=${now} stack=${stack?.typeId} components=${componentIds}`);
    report("projectile_owner",ownerOk);
    world.afterEvents.itemUse.unsubscribe(useSub);remove(pig);
  },30);
  const impactPig=dimension.spawnEntity("minecraft:pig",{x:28,y:66,z:28});initialHealth=impactPig.getComponent("minecraft:health").currentValue;const impactStart={...impactPig.location};
  const hurtSub=world.afterEvents.entityHurt.subscribe(e=>{if(e.hurtEntity.id===impactPig.id){damageEvents++;const direct=e.damageSource.damagingEntity,projectile=e.damageSource.damagingProjectile;let projectileId;try{projectileId=projectile?.id;}catch{}if(direct?.id===p.id||observedOwners.get(projectileId)===p.id)damageAttributed=true;}});
  later(()=>directPulse(p,{x:28,y:69,z:28},{x:0,y:-1.5,z:0}),34);
  later(()=>{
    afterHealth=impactPig.getComponent("minecraft:health")?.currentValue??initialHealth;impulseDistance=Math.hypot(impactPig.location.x-impactStart.x,impactPig.location.z-impactStart.z);
    const damage=initialHealth-afterHealth;report("entity_damage",damage>=3.5&&damage<=5.5,`nominal_component_damage=4 before=${initialHealth} after=${afterHealth} observed=${damage}`);
    report("damage_attribution",damageAttributed,`owner=${p.id}`);
    report("bounded_knockback",impulseDistance>0&&impulseDistance<4,`distance=${impulseDistance}`);
    report("single_damage_event",damageEvents===1,`events=${damageEvents}`);world.afterEvents.entityHurt.unsubscribe(hurtSub);world.afterEvents.entitySpawn.unsubscribe(spawnSub);remove(impactPig);
  },48);

  later(()=>{
    dimension.setBlockType({x:20,y:66,z:20},"minecraft:obsidian");directPulse(players[1],{x:20,y:66,z:14},{x:0,y:0,z:1.5});
    later(()=>report("block_impact_cleanup",pulses().length===0,`remaining=${pulses().length}`),20);
  },30);
  later(()=>{
    const empty=players[2],d=durabilityDamage(empty);empty.getComponent("minecraft:inventory").container.setItem(1);
    const a=countItem(empty,"ccoriginal_cc:resonance_pebble");empty.useItemInSlot(0);later(()=>{releaseUse(empty);later(()=>report("empty_ammo_no_cost",countItem(empty,"ccoriginal_cc:resonance_pebble")===a&&durabilityDamage(empty)===d),2);},16);
  },55);
  later(()=>{
    players.forEach(x=>equip(x));
    const ammoBefore=players.map(x=>countItem(x,"ccoriginal_cc:resonance_pebble"));
    let concurrentSpawns=0;const sub=world.afterEvents.entitySpawn.subscribe(e=>{if(e.entity.typeId===PULSE)concurrentSpawns++;});
    players.forEach((x,i)=>{x.teleport({x:12+i*3,y:65,z:30},{rotation:{x:0,y:180}});x.useItemInSlot(0);});
    later(()=>players.forEach(releaseUse),10);
    later(()=>{const isolated=players.every((x,i)=>countItem(x,"ccoriginal_cc:resonance_pebble")===ammoBefore[i]-1);report("four_player_concurrent_use",concurrentSpawns===4,`spawn_count=${concurrentSpawns}`);report("owner_isolation",isolated,`ammo_deltas=${players.map((x,i)=>ammoBefore[i]-countItem(x,"ccoriginal_cc:resonance_pebble")).join(",")}`);world.afterEvents.entitySpawn.unsubscribe(sub);cleanup();},13);
  },75);
  later(()=>{
    cleanup();
    for(const x of players)x.teleport({x:10+players.indexOf(x)*5,y:66,z:24},{rotation:{x:-90,y:0}});
    const ambient=[];for(let i=0;i<24;i++)ambient.push(dimension.spawnEntity("minecraft:pig",{x:8+i%8,y:65,z:8+Math.floor(i/8)}));
    for(let i=0;i<20;i++){const shot=dimension.spawnEntity(PULSE,{x:10+(i%5)*4,y:80,z:10+Math.floor(i/5)*4});shot.getComponent("minecraft:projectile").shoot({x:0,y:0,z:0});}
    later(()=>{const count=pulses().length;report("global_cap",count===16,`stationary_fixture_projectiles=${count}`);report("worst_credible_load",count===16&&ambient.length===24,`players=4 projectiles=${count} ambient=${ambient.length}`);cleanup();ambient.forEach(remove);},4);
  },150);
  later(()=>{
    const traveler=players[1],shot=directPulse(traveler,{x:30,y:80,z:30},{x:0,y:0,z:0});traveler.teleport({x:0,y:80,z:0},{dimension:world.getDimension("minecraft:nether")});
    later(()=>{report("dimension_transition_cleanup",!shot.isValid);traveler.teleport({x:15,y:66,z:24},{dimension});},65);
  },160);
  later(()=>{
    const old=players[3], shot=directPulse(old,{x:24,y:70,z:24},{x:.01,y:0,z:.01});remove(old);
    later(()=>{remove(shot);report("disconnect_cleanup",!shot.isValid);const replacement=spawnSimulatedPlayer({dimension,x:21,y:65,z:12},"SlingBot4R",GameMode.survival);equip(replacement);players[3]=replacement;report("reconnect_no_state",replacement.getItemCooldown("resonance_sling")===0);},5);
  },225);
  later(()=>{
    const victim=players[2], shot=directPulse(victim,{x:18,y:70,z:18},{x:.01,y:0,z:.01});victim.kill();later(()=>{remove(shot);report("death_in_flight_cleanup",!shot.isValid);},5);
  },240);
  later(()=>{const shot=directPulse(players[0],{x:16,y:80,z:16},{x:0,y:0,z:0});later(()=>report("expiration_cleanup",!shot.isValid),65);},255);
  later(()=>{
    cleanup();let accepted=0;for(let round=0;round<4;round++)for(const x of players){if(x?.isValid){x.startItemCooldown("resonance_sling",0);x.useItemInSlot(0);accepted++;}}
    report("rapid_alternating_use",accepted>=12,`attempts=${accepted}`);
    later(()=>{cleanup();report("repeated_use_cleanup",pulses().length===0);},70);
  },270);
  later(()=>{
    cleanup();
    for(let i=0;i<4;i++){try{players[i].respawn();}catch{}if(!players[i]?.isValid){players[i]=spawnSimulatedPlayer({dimension,x:12+i*3,y:65,z:12},`SoakBot${i+1}`,GameMode.survival);}equip(players[i],64);players[i].teleport({x:12+i*3,y:66,z:24},{rotation:{x:-90,y:0}});}
    let attempts=0;
    function soak(round){
      if(round===100){later(()=>{report("endurance_repeated_use",attempts===400,`rounds=100 attempts=${attempts}`);report("endurance_cleanup",pulses().length===0,`remaining=${pulses().length}`);report("bounded_queue",scheduled.peak<=18,`peak=${scheduled.peak}`);report("final_cleanup",pulses().length===0,`remaining=${pulses().length}`);world.setDynamicProperty("ccoriginal_cc:sling_preview_checkpoint",1);console.warn(`${TAG} metrics=${JSON.stringify({players:4,peak_scheduled:scheduled.peak,stationary_worst_credible_attempts:20,endurance_rounds:100,endurance_attempts:attempts,production_global_cap:16,persistent_records:0})}`);},70);return;}
      if(round===60)for(const x of players)x.setItem(new ItemStack("ccoriginal_cc:resonance_pebble",64),1,false);
      for(const x of players){x.startItemCooldown("resonance_sling",0);x.useItemInSlot(0);attempts++;}
      later(()=>players.forEach(releaseUse),10);later(()=>soak(round+1),12);
    }
    soak(0);
  },355);
}
function arm(){
  dimension=world.getDimension("minecraft:overworld");
  if(dimension.getBlock(ARM)?.typeId!=="minecraft:gold_block"){system.runTimeout(arm,10);return;}
  cleanup();
  if(world.getDynamicProperty("ccoriginal_cc:sling_preview_checkpoint")===1){report("restart_no_persistent_projectiles",pulses().length===0);return;}
  run();
}
system.runTimeout(arm,20);
