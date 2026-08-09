import { BOSS_LADDER, BOSS_REWARDS, PILGRIMAGE } from "./catalog.js";
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

  function spawnTwinbond(player, location, itemType) {
    const p = state.playerState(player), w = state.worldState();
    const missingPilgrimage = Object.values(PILGRIMAGE).some(key => !p.stamps.includes(key));
    if (itemType !== "aionbound:finale_ignition_key" || !p.stamps.includes("edge:assembled") || missingPilgrimage || p.endpoint || Object.keys(w.encounters.active).length > COMBINED_BUDGETS.bossesWorld - COMBINED_BUDGETS.twinbondMax) return state.warn(player, "Twinbond prerequisites or boss budget refused the key.");
    const specs = [
      { key: `twinbond:${player.id}:ash`, type: "aionbound:ash_sovereign_wyrm", location },
      { key: `twinbond:${player.id}:tide`, type: "aionbound:tide_empress_wyrm", location: { x: location.x + 4, y: location.y, z: location.z } },
    ];
    if (specs.some(spec => w.encounters.active[spec.key] || w.encounters.terminal[spec.key])) return state.warn(player, "Twinbond is already active or complete.");
    for (const spec of specs) w.encounters.active[spec.key] = { v: 3, key: spec.key, type: spec.type, owner: player.id, state: "admitted" };
    if (!state.saveWorld(w)) { for (const spec of specs) delete w.encounters.active[spec.key]; return; }
    if (!consumeOne(player, itemType)) { for (const spec of specs) delete w.encounters.active[spec.key]; state.saveWorld(w); return; }
    const spawned = [];
    try {
      for (const spec of specs) {
        const entity = player.dimension.spawnEntity(spec.type, spec.location); spawned.push(entity);
        entity.setDynamicProperty("aionbound:owner", player.id); entity.setDynamicProperty("aionbound:encounter", spec.key); w.encounters.active[spec.key].state = "active";
      }
      state.saveWorld(w);
    } catch {
      for (const entity of spawned) entity.remove();
      for (const spec of specs) delete w.encounters.active[spec.key]; state.saveWorld(w);
      player.dimension.spawnItem(new ItemStack(itemType, 1), player.location);
      state.warn(player, "Twinbond spawn failed; the key was returned.");
    }
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
    const w = state.worldState(); if (w.encounters.terminal[key]) return true;
    delete w.encounters.active[key]; w.encounters.terminal[key] = { v: 3, state: "terminal", rewarded: true }; state.saveWorld(w);
    const player = world.getAllPlayers().find(candidate => candidate.id === owner); if (!player) return true;
    const reward = BOSS_REWARDS[entity.typeId];
    if (reward && state.stamp(player, reward[0])) player.dimension.spawnItem(new ItemStack(reward[1], 1), player.location);
    if (entity.typeId === "aionbound:ash_sovereign_wyrm") state.stamp(player, "twinbond:ash");
    if (entity.typeId === "aionbound:tide_empress_wyrm") state.stamp(player, "twinbond:tide");
    const p = state.playerState(player);
    if (p.stamps.includes("twinbond:ash") && p.stamps.includes("twinbond:tide") && !p.endpoint) {
      p.endpoint = true; if (!p.stamps.includes("endpoint:concord")) p.stamps.push("endpoint:concord");
      if (state.savePlayer(player, p)) player.dimension.spawnItem(new ItemStack("aionbound:trophy_concord_scale", 1), player.location);
    }
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
