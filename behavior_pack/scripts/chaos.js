import { CHAOS_OUTCOMES } from "./catalog.js";
import { COMBINED_BUDGETS } from "./budgets.js";

export function selectOutcomeIndex(x, z, sequence) {
  let value = ((x | 0) * 1103515245) ^ ((z | 0) * 12345) ^ (sequence | 0);
  value ^= value >>> 16; return Math.abs(value | 0) % CHAOS_OUTCOMES.length;
}

const locationKey = location => `${location.x},${location.y},${location.z}`;

export function createChaosService({ world, system, ItemStack, state, arbiter }) {
  function activeChaos(w) { return Object.values(w.journals).filter(j => j.kind === "chaos" && j.state !== "terminal"); }
  function terminalize(w, id) { const journal = w.journals[id]; if (!journal) return; journal.state = "terminal"; journal.terminal = true; state.pruneJournals(w); state.saveWorld(w); arbiter.release("chaos"); }

  function execute(id, player) {
    let w = state.worldState(), journal = w.journals[id];
    if (!journal || journal.state !== "accepted") return false;
    const outcome = CHAOS_OUTCOMES[journal.outcome];
    const location = journal.location, dimension = world.getDimension(journal.dimension);
    if (outcome.temporary) {
      const offsets = [[1, 1, 0], [-1, 1, 0], [0, 1, 1], [0, 1, -1]], reverse = [];
      for (const [dx, dy, dz] of offsets.slice(0, COMBINED_BUDGETS.chaosBlocksEvent)) {
        const target = { x: location.x + dx, y: location.y + dy, z: location.z + dz }, block = dimension.getBlock(target);
        if (block?.typeId === "minecraft:air") reverse.push({ ...target, type: block.typeId });
      }
      journal.reverse = reverse; journal.cleanupAt = system.currentTick + Math.min(outcome.temporary[1], COMBINED_BUDGETS.chaosCleanupTicks); journal.state = "cleanup";
      if (!state.saveWorld(w)) return false;
      for (const target of reverse) dimension.getBlock(target)?.setType(outcome.temporary[0]);
      return true;
    }
    journal.state = "executing"; if (!state.saveWorld(w)) return false;
    if (outcome.effect) player.addEffect(outcome.effect[0], outcome.effect[1], { amplifier: outcome.effect[2], showParticles: true });
    if (outcome.item) dimension.spawnItem(new ItemStack(outcome.item[0], outcome.item[1]), location);
    if (outcome.discovery) state.stamp(player, outcome.discovery);
    if (outcome.entities) {
      for (let index = 0; index < outcome.entities.length && index < COMBINED_BUDGETS.chaosEntitiesEvent; index++) {
        const entity = dimension.spawnEntity(outcome.entities[index], { x: location.x + (index % 3) - 1, y: location.y + 1, z: location.z + Math.floor(index / 3) + 1 });
        entity.addTag(`aionbound_chaos_${id.replace(/[^A-Za-z0-9_]/g, "_").slice(-80)}`);
      }
    }
    w = state.worldState(); terminalize(w, id);
    return true;
  }

  function use({ player, block }) {
    const now = system.currentTick, p = state.playerState(player); p.opens = p.opens.filter(tick => now - tick < 1200);
    const w = state.worldState();
    if (activeChaos(w).length >= COMBINED_BUDGETS.chaosActiveWorld || p.opens.length >= COMBINED_BUDGETS.chaosMinute || (p.cooldowns.chaos ?? 0) > now || !arbiter.admit("chaos", "chaosActiveWorld")) return state.warn(player, "The crate refuses while its bounded chaos budget or cooldown is full.");
    const id = state.nextOperationId("chaos", player.id); if (!id) { arbiter.release("chaos"); return; }
    const current = state.worldState(), sequence = current.sequence, location = { x: block.location.x, y: block.location.y, z: block.location.z };
    current.journals[id] = { v: 3, kind: "chaos", state: "accepted", owner: player.id, dimension: player.dimension.id, location, locationKey: locationKey(location), outcome: selectOutcomeIndex(location.x, location.z, sequence) };
    current.journalOrder.push(id);
    const nextPlayer = { ...p, opens: [...p.opens, now], cooldowns: { ...p.cooldowns, chaos: now + COMBINED_BUDGETS.chaosCooldown } };
    if (!state.savePlayer(player, nextPlayer) || !state.saveWorld(current)) { delete current.journals[id]; current.journalOrder = current.journalOrder.filter(x => x !== id); state.saveWorld(current); arbiter.release("chaos"); return; }
    if (!arbiter.defer(system, () => execute(id, player))) { current.journals[id].state = "terminal"; current.journals[id].terminal = true; state.saveWorld(current); arbiter.release("chaos"); state.warn(player, "Scheduler capacity refused the chaos operation."); }
  }

  function tick() {
    arbiter.beginTick(system.currentTick); const w = state.worldState();
    const accepted = Object.entries(w.journals).find(([, journal]) => journal.kind === "chaos" && journal.state === "accepted");
    if (accepted) {
      const player = world.getAllPlayers().find(candidate => candidate.id === accepted[1].owner);
      if (player) { execute(accepted[0], player); return; }
    }
    for (const [id, journal] of Object.entries(w.journals)) {
      if (journal.kind !== "chaos" || journal.state !== "cleanup" || journal.cleanupAt > system.currentTick) continue;
      const dimension = world.getDimension(journal.dimension);
      for (const original of journal.reverse ?? []) {
        if (!arbiter.spend("worldEditsTick")) return;
        dimension.getBlock(original)?.setType(original.type);
      }
      terminalize(w, id); return;
    }
  }

  function reconcile() {
    const w = state.worldState();
    for (const journal of Object.values(w.journals)) {
      if (journal.kind !== "chaos" || journal.state === "terminal") continue;
      // An executing non-temporary outcome is never replayed after restart.
      // It never acquires live capacity during reconciliation.
      if (journal.state === "executing") { journal.state = "terminal"; journal.terminal = true; }
      else arbiter.admit("chaos", "chaosActiveWorld");
    }
    state.pruneJournals(w); state.saveWorld(w);
  }
  return { use, execute, tick, reconcile, activeChaos };
}
