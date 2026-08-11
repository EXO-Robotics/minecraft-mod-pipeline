import { CODEX_ENTRY_REGISTRY, CODEX_EVENT_INDEX, CODEX_TOPICS } from "./catalog.js";
import { COMBINED_BUDGETS } from "./budgets.js";
import { codexDiscoveryState } from "./state.js";
import { CODEX_QUESTION_LABELS, WHISPERWOOD_CODEX_UI_BY_ID } from "./wave1_codex_ui_data.js";

export const CODEX_UI_CATEGORIES = Object.freeze([
  Object.freeze({ id: "resource", title: "Resources & Blocks" }),
  Object.freeze({ id: "plant", title: "Plants" }),
  Object.freeze({ id: "creature", title: "Creatures" }),
]);

const unavailable = "Unavailable until its approved runtime dependency is complete.";
const incomplete = "Complete this entry to reveal this answer.";
const humanize = value => value.split("_").map(word => word ? word[0].toUpperCase() + word.slice(1) : word).join(" ");

export function codexStateForEntry(playerState, entry) {
  const address = CODEX_EVENT_INDEX[entry.events[0]?.id];
  return address ? codexDiscoveryState(playerState.codex?.discovery, address.region, address.category, address.index) : 0;
}

export function codexStatus(stateValue) {
  if (stateValue >= 2) return "Complete";
  if (stateValue === 1) return "Observed";
  return "Locked";
}

export function codexEntryTitle(entry, stateValue) {
  return stateValue > 0 ? humanize(entry.id) : "Unknown entry";
}

export function codexEntryBody(entry, stateValue) {
  if (stateValue === 0) return "This entry has not been discovered.";
  const approved = WHISPERWOOD_CODEX_UI_BY_ID[entry.id]?.answers ?? [null, null, null];
  return CODEX_QUESTION_LABELS.map((question, index) => {
    const answer = stateValue === 1 && index > 0 ? incomplete : (approved[index] ?? unavailable);
    return `${question}\n${answer}`;
  }).join("\n\n");
}

export function createCodexService({ state, ActionFormData = null }) {
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

  function fallback(player) {
    const p = state.playerState(player), delta = player.isSneaking ? -1 : 1;
    p.codex.topic = (p.codex.topic + delta + CODEX_TOPICS.length) % CODEX_TOPICS.length;
    p.goals = deriveGoals(p.stamps);
    state.savePlayer(player, p);
    guidance(player);
    return false;
  }

  function show(player, form, onSelection) {
    let response;
    try { response = form.show(player); }
    catch { return Promise.resolve(fallback(player)); }
    return Promise.resolve(response).then(result => {
      if (result?.canceled || !Number.isInteger(result?.selection)) return false;
      return onSelection(result.selection);
    }).catch(() => fallback(player));
  }

  function entriesFor(category) { return CODEX_ENTRY_REGISTRY.filter(entry => entry.category === category); }

  function openEntry(player, categoryIndex, entryIndex) {
    const category = CODEX_UI_CATEGORIES[categoryIndex], entry = entriesFor(category.id)[entryIndex];
    if (!entry) return Promise.resolve(false);
    const stateValue = codexStateForEntry(state.playerState(player), entry);
    const form = new ActionFormData()
      .title(`Aionbound Codex — ${codexEntryTitle(entry, stateValue)}`)
      .body(codexEntryBody(entry, stateValue))
      .button("Back");
    return show(player, form, selection => selection === 0 ? openCategory(player, categoryIndex) : false);
  }

  function openCategory(player, categoryIndex) {
    const category = CODEX_UI_CATEGORIES[categoryIndex];
    if (!category) return Promise.resolve(false);
    const playerState = state.playerState(player), entries = entriesFor(category.id);
    const form = new ActionFormData().title(`Whisperwood — ${category.title}`).body("Choose an entry.");
    for (const entry of entries) {
      const stateValue = codexStateForEntry(playerState, entry);
      form.button(`[${codexStatus(stateValue)}] ${codexEntryTitle(entry, stateValue)}`);
    }
    form.button("Back");
    return show(player, form, selection => selection === entries.length ? openRoot(player) : openEntry(player, categoryIndex, selection));
  }

  function openRoot(player) {
    if (typeof ActionFormData !== "function") return Promise.resolve(fallback(player));
    const playerState = state.playerState(player);
    const form = new ActionFormData().title("Aionbound Codex — Whisperwood").body("Choose a category.");
    for (const category of CODEX_UI_CATEGORIES) {
      const entries = entriesFor(category.id), complete = entries.filter(entry => codexStateForEntry(playerState, entry) === 2).length;
      form.button(`${category.title} — ${complete}/${entries.length}`);
    }
    return show(player, form, selection => openCategory(player, selection));
  }

  function use(player, itemType) {
    if (itemType === "aionbound:starter_codex_bookmark") state.stamp(player, "bookmark:first_waystone");
    return openRoot(player);
  }

  function discover(player, eventId) {
    const event = CODEX_EVENT_INDEX[eventId];
    if (!event) return false;
    return state.transitionCodex(player, event.region, event.category, event.index, event.state);
  }
  return { guidance, use, openRoot, openCategory, openEntry, discover, deriveGoals };
}
