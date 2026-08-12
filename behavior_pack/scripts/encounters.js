import { BOSS_LADDER, BOSS_REWARDS } from "./catalog.js";
import { COMBINED_BUDGETS } from "./budgets.js";

export function createEncounterService({ world, ItemStack, state, boundedEntities, consumeOne }) {
  const activeBosses = () => boundedEntities().filter(entity => entity.getDynamicProperty("aionbound:encounter") && !entity.getDynamicProperty("aionbound:terminal"));

  function spawnBoss(player, type, location, key) {
    const w = state.worldState(), journal = w.encounters;
    if (journal.active[key] || journal.terminal[key] || Object.keys(journal.active).length >= COMBINED_BUDGETS.bossesWorld) { state.warn(player, "Encounter is active, terminal, or capped."); return null; }
    journal.active[key] = { v: 3, key, type, owner: player.id, state: "admitted" };
    if (!state.saveWorld(w)) { delete journal.active[key]; return null; }
    try {
      const entity = player.dimension.spawnEntity(type, location);
      entity.setDynamicProperty("aionbound:owner", player.id); entity.setDynamicProperty("aionbound:encounter", key);
      journal.active[key].state = "active"; state.saveWorld(w); return entity;
    } catch {
      delete journal.active[key]; state.saveWorld(w); state.warn(player, "Spawn failed; admission rolled back."); return null;
    }
  }

  function spawnTwinbond(player, _location, _itemType) {
    // Preserve the approved obelisk/action seam as inert preparation. The G7
    // finale key, Concord Scale, and endpoint path are superseded by the Wave 1
    // ledger and cannot admit new gameplay in G8.
    state.warn(player, "Twinbond is withheld pending the ratified Wave 1 finale contract.");
    return false;
  }

  function routeBoss(action, context) {
    const { player, block, itemType } = context;
    if (action === "boss:foundry") {
      if (!state.playerState(player).stamps.includes("glasswing:first_defeat")) return state.warn(player, "Defeat Glasswing before foundry admission.");
      spawnBoss(player, "aionbound:chrono_robo_sentinel", block.location, `foundry:${player.id}`); return;
    }
    if (action === "boss:twinbond") { spawnTwinbond(player, block.location, itemType); return; }
    const spec = BOSS_LADDER[action]; if (!spec) return;
    const p = state.playerState(player);
    if (!p.stamps.includes(spec.prerequisite) || p.stamps.includes(spec.terminal)) return state.warn(player, "Boss prerequisite missing or trophy already credited.");
    spawnBoss(player, spec.type, block.location, `${spec.type}:${player.id}`);
  }

  function bossDeath(event) {
    const entity = event.deadEntity, owner = entity.getDynamicProperty("aionbound:owner"), key = entity.getDynamicProperty("aionbound:encounter");
    if (!key) return false;
    // Do not translate a legacy Twinbond shell into superseded endpoint or
    // Concord Scale state. Existing entities and journals are left untouched;
    // this bounded reconciliation performs no destructive cleanup.
    if (entity.typeId === "aionbound:ash_sovereign_wyrm" || entity.typeId === "aionbound:tide_empress_wyrm" || key.startsWith("twinbond:")) return true;
    const w = state.worldState(); if (w.encounters.terminal[key]) return true;
    delete w.encounters.active[key]; w.encounters.terminal[key] = { v: 3, state: "terminal", rewarded: true }; state.saveWorld(w);
    const player = world.getAllPlayers().find(candidate => candidate.id === owner); if (!player) return true;
    const reward = BOSS_REWARDS[entity.typeId];
    if (reward && state.stamp(player, reward[0])) player.dimension.spawnItem(new ItemStack(reward[1], 1), player.location);
    return true;
  }

  function reconcile() {
    const w = state.worldState(), mounts = boundedEntities("aionbound:waykeeper_courser"), owners = new Set();
    for (const entity of mounts) { const owner = entity.getDynamicProperty("aionbound:owner"); if (!owner || owners.has(owner) || owners.size >= COMBINED_BUDGETS.mountsWorld) entity.remove(); else owners.add(owner); }
    const live = new Map();
    for (const entity of activeBosses()) {
      const key = entity.getDynamicProperty("aionbound:encounter");
      if (!key || w.encounters.terminal[key] || live.has(key)) entity.remove();
      else { live.set(key, entity); w.encounters.active[key] ??= { v: 3, key, type: entity.typeId, owner: entity.getDynamicProperty("aionbound:owner"), state: "active" }; }
    }
    for (const key of Object.keys(w.encounters.active)) if (!live.has(key)) delete w.encounters.active[key];
    state.saveWorld(w);
  }
  return { spawnBoss, spawnTwinbond, routeBoss, bossDeath, activeBosses, reconcile };
}
