import { CODEX_EVENT_INDEX, CODEX_TOPICS } from "./catalog.js";
import { COMBINED_BUDGETS } from "./budgets.js";

export function createCodexService({ state }) {
  const deriveGoals = stamps => ({
    arsenal: stamps.includes("edge:assembled") || stamps.includes("chrono:first_defeat"),
    naturalist: stamps.includes("glasswing:first_defeat") && stamps.some(x => x.startsWith("landmark:")),
    surveyor: stamps.filter(x => x.startsWith("pilgrimage:")).length >= 3,
  });

  function guidance(player) {
    const p = state.playerState(player), page = CODEX_TOPICS[p.codex.topic % CODEX_TOPICS.length];
    const goals = deriveGoals(p.stamps);
    player.sendMessage(`§dAionbound Codex — ${page.title}§r\n${page.lines.join("\n")}\nDiscoveries ${p.stamps.length}/${COMBINED_BUDGETS.discoveries}\nTracks: Arsenal ${goals.arsenal ? "active" : "open"} · Naturalist ${goals.naturalist ? "active" : "open"} · Surveyor ${goals.surveyor ? "active" : "open"}`);
  }

  function use(player, itemType) {
    if (itemType === "aionbound:starter_codex_bookmark") state.stamp(player, "bookmark:first_waystone");
    const p = state.playerState(player);
    const delta = player.isSneaking ? -1 : 1;
    p.codex.topic = (p.codex.topic + delta + CODEX_TOPICS.length) % CODEX_TOPICS.length;
    p.goals = deriveGoals(p.stamps);
    state.savePlayer(player, p); guidance(player);
  }
  function discover(player, eventId) {
    const event = CODEX_EVENT_INDEX[eventId];
    if (!event) return false;
    return state.transitionCodex(player, event.region, event.category, event.index, event.state);
  }
  return { guidance, use, discover, deriveGoals };
}
