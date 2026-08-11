import { COMBINED_BUDGETS } from "./budgets.js";
import { STRUCTURE_REWARDS, STRUCTURE_SITES, WHISPERWOOD_PROGRESSION_SITES } from "./catalog.js";

const SOFT = new Set(["minecraft:dirt", "minecraft:grass_block", "minecraft:sand", "minecraft:gravel", "minecraft:clay", "minecraft:mud", "minecraft:netherrack", "minecraft:soul_sand", "minecraft:soul_soil", "minecraft:snow", "minecraft:snow_layer", "minecraft:moss_block"]);
const NEARBY_SIGNATURE_OFFSETS = Object.freeze((() => {
  const offsets = [];
  for (let y = -2; y <= 2; y++) for (let x = -2; x <= 2; x++) for (let z = -2; z <= 2; z++) {
    const distance = Math.abs(x) + Math.abs(y) + Math.abs(z);
    if (distance > 0 && distance <= 2) offsets.push(Object.freeze({ x, y, z, distance }));
  }
  offsets.sort((a, b) => a.distance - b.distance || a.y - b.y || a.x - b.x || a.z - b.z);
  return offsets;
})());

export function cellEdits(base) {
  const edits = [];
  for (let y = 0; y < 3; y++) for (let x = 0; x < 8; x++) for (let z = 0; z < 8; z++) {
    edits.push({ x: base.x + x, y: base.y + y, z: base.z + z, type: y === 0 ? "minecraft:stone" : y === 2 && x === 0 && z === 3 ? "aionbound:orevein_hollow_gate" : "minecraft:air" });
  }
  return edits;
}

export function createStructureService({ world, system, ItemStack, state, arbiter, consumeOne }) {
  const live = { stripJobs: [], cellJob: null };

  function useStrip(player) {
    const now = system.currentTick, p = state.playerState(player);
    if ((p.cooldowns.strip ?? 0) > now || live.stripJobs.length >= COMBINED_BUDGETS.stripJobs) return state.warn(player, "Stripvein queue or cooldown is full; the charge was not consumed.");
    const hit = player.getBlockFromViewDirection({ maxDistance: 6 });
    if (!hit?.block) return state.warn(player, "No bounded excavation origin; the charge was not consumed.");
    const frozen = [], origin = hit.block.location;
    outer: for (let x = -COMBINED_BUDGETS.stripRadius; x <= COMBINED_BUDGETS.stripRadius; x++) for (let y = -COMBINED_BUDGETS.stripRadius; y <= COMBINED_BUDGETS.stripRadius; y++) for (let z = -COMBINED_BUDGETS.stripRadius; z <= COMBINED_BUDGETS.stripRadius; z++) {
      if (frozen.length >= COMBINED_BUDGETS.stripBlocks) break outer;
      const block = player.dimension.getBlock({ x: origin.x + x, y: origin.y + y, z: origin.z + z });
      if (block && SOFT.has(block.typeId)) frozen.push({ x: block.x, y: block.y, z: block.z, type: block.typeId });
    }
    if (!frozen.length || !consumeOne(player, "aionbound:stripvein_charge")) return state.warn(player, "Preflight found no allowlisted job; the charge was not consumed.");
    p.cooldowns.strip = now + COMBINED_BUDGETS.stripCooldown; state.savePlayer(player, p);
    live.stripJobs.push({ owner: player.id, dimension: player.dimension.id, frozen, cursor: 0 });
  }

  function useCell(player, block, itemType) {
    const p = state.playerState(player), w = state.worldState(), cell = w.cells[player.id];
    if (cell && block.location.x >= cell.base.x && block.location.x < cell.base.x + 8 && block.location.z >= cell.base.z && block.location.z < cell.base.z + 8) {
      player.teleport(cell.return.location, { dimension: world.getDimension(cell.return.dimension.replace("minecraft:", "")) }); return;
    }
    if (cell) {
      if (cell.state !== "ready") return state.warn(player, "Pocket building; you remain safe.");
      player.teleport({ x: cell.base.x + 4.5, y: cell.base.y + 1, z: cell.base.z + 4.5 }, { dimension: world.getDimension("overworld") }); return;
    }
    if (itemType !== "aionbound:burrowgate_key" || p.cell || live.cellJob || Object.values(w.cells).some(x => x.state === "building")) return state.warn(player, "Pocket admission refused; key not consumed.");
    const base = { x: 100000 + Object.keys(w.cells).length * 32, y: -48, z: 100000 };
    const next = { v: 3, owner: player.id, base, cursor: 0, state: "building", return: { dimension: player.dimension.id, location: { x: player.location.x, y: player.location.y, z: player.location.z } } };
    w.cells[player.id] = next; p.cell = { owner: player.id };
    if (!state.savePlayer(player, p) || !state.saveWorld(w)) { delete w.cells[player.id]; p.cell = null; state.savePlayer(player, p); return; }
    if (!consumeOne(player, itemType)) { delete w.cells[player.id]; p.cell = null; state.saveWorld(w); state.savePlayer(player, p); return; }
    live.cellJob = { owner: player.id, edits: cellEdits(base), cursor: 0 };
  }

  function tick() {
    arbiter.beginTick(system.currentTick);
    while (live.stripJobs.length) {
      const job = live.stripJobs[0], entry = job.frozen[job.cursor];
      if (!arbiter.spend("worldEditsTick")) break;
      job.cursor++;
      const block = world.getDimension(job.dimension).getBlock(entry);
      if (block?.typeId === entry.type && SOFT.has(entry.type)) block.setType("minecraft:air");
      if (job.cursor >= job.frozen.length) live.stripJobs.shift();
    }
    const job = live.cellJob;
    if (!job) return;
    const w = state.worldState(), cell = w.cells[job.owner];
    if (!cell) { live.cellJob = null; return; }
    let count = 0;
    while (count < COMBINED_BUDGETS.cellEditsTick && job.cursor < job.edits.length && arbiter.spend("worldEditsTick")) {
      const edit = job.edits[job.cursor++]; world.getDimension("overworld").getBlock(edit)?.setType(edit.type); count++;
    }
    cell.cursor = job.cursor;
    if (job.cursor >= job.edits.length) {
      cell.state = "ready"; live.cellJob = null;
      const player = world.getAllPlayers().find(x => x.id === cell.owner);
      if (player) player.teleport({ x: cell.base.x + 4.5, y: cell.base.y + 1, z: cell.base.z + 4.5 }, { dimension: world.getDimension("overworld") });
    }
    state.saveWorld(w);
  }

  function reconcile() {
    live.stripJobs.length = 0; live.cellJob = null;
    const w = state.worldState(), interrupted = Object.values(w.cells).find(x => x.state === "building");
    if (!interrupted) return;
    const player = world.getAllPlayers().find(x => x.id === interrupted.owner);
    if (player) player.teleport(interrupted.return.location, { dimension: world.getDimension(interrupted.return.dimension.replace("minecraft:", "")) });
    live.cellJob = { owner: interrupted.owner, edits: cellEdits(interrupted.base), cursor: Math.max(0, interrupted.cursor ?? 0) };
  }
  function hasSignature(dimension, location, typeId) {
    let checked = 0;
    for (let y = -2; y <= 2; y++) for (let x = -2; x <= 2; x++) for (let z = -2; z <= 2; z++) {
      if (++checked > COMBINED_BUDGETS.entityQuery) return false;
      if (dimension.getBlock({ x: location.x + x, y: location.y + y, z: location.z + z })?.typeId === typeId) return true;
    }
    return false;
  }
  function resolveSite(block, dimension) {
    return STRUCTURE_SITES.filter(site => site.center === block.typeId).find(site => hasSignature(dimension, block.location, site.signature)) ?? null;
  }
  function hasNearbyProgressionSignature(dimension, location, typeId) {
    return NEARBY_SIGNATURE_OFFSETS.some(offset => dimension.getBlock({
      x: location.x + offset.x,
      y: location.y + offset.y,
      z: location.z + offset.z,
    })?.typeId === typeId);
  }
  function resolveProgressionSite(block, dimension) {
    return WHISPERWOOD_PROGRESSION_SITES
      .filter(site => site.center === block.typeId)
      .find(site => site.signatures.every(signature => hasNearbyProgressionSignature(dimension, block.location, signature))) ?? null;
  }
  function activateProgressionSite({ player, block }) {
    const site = resolveProgressionSite(block, player.dimension);
    if (!site) return false;
    return Object.freeze({
      site: site.id,
      stamp: site.stamp,
      role: site.role,
      transition: site.transition ?? null,
      action: site.action ?? null,
      changed: state.stamp(player, site.stamp),
    });
  }
  function claimSite({ player, block }) {
    const site = resolveSite(block, player.dimension); if (!site) return;
    state.stamp(player, `landmark:${site.id}`);
    const p = state.playerState(player), sites = Array.isArray(p.credits.sites) ? p.credits.sites : [];
    const claim = `${site.id}:${block.location.x},${block.location.y},${block.location.z}`;
    if (sites.includes(claim)) return state.warn(player, "This structure reward was already claimed by you.");
    if (sites.length >= 64) return state.warn(player, "Structure reward history is full; no reward was changed.");
    p.credits = { ...p.credits, sites: [...sites, claim] };
    if (!state.savePlayer(player, p)) return;
    const reward = STRUCTURE_REWARDS[site.pool];
    if (reward) player.dimension.spawnItem(new ItemStack(reward[0], reward[1]), player.location);
    player.sendMessage(`§a[Discovery]§r ${site.id.replaceAll("_", " ")} · ${site.pool.replaceAll("_", " ")}`);
  }
  return { useStrip, useCell, tick, reconcile, claimSite, resolveSite, activateProgressionSite, resolveProgressionSite, live };
}
