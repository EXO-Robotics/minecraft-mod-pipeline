import { CODEX_ENTRY_REGISTRY, CODEX_EVENT_INDEX, CODEX_TOPICS } from "./catalog.js";
import { COMBINED_BUDGETS } from "./budgets.js";
import { codexDiscoveryState } from "./state.js";
import { CODEX_QUESTION_LABELS, WHISPERWOOD_CODEX_UI_BY_ID } from "./wave1_codex_ui_data.js";

export const CODEX_UI_CATEGORIES = Object.freeze([
  Object.freeze({ id: "resource", title: "Resources & Blocks" }),
  Object.freeze({ id: "plant", title: "Plants" }),
  Object.freeze({ id: "creature", title: "Creatures" }),
  Object.freeze({ id: "structure", title: "Structures" }),
  Object.freeze({ id: "equipment", title: "Equipment & Trophies" }),
  Object.freeze({ id: "boss", title: "Bosses" }),
  Object.freeze({ id: "progression", title: "Journey" }),
]);
export const CODEX_UI_REGIONS = Object.freeze([
  Object.freeze({ id: "ww", title: "Whisperwood" }),
  Object.freeze({ id: "ah", title: "Ashen Highlands" }),
  Object.freeze({ id: "cm", title: "Crystal Marsh" }),
  Object.freeze({ id: "sr", title: "Skyreach" }),
]);

const unavailable = "Unavailable until its approved runtime dependency is complete.";
const incomplete = "Complete this entry to reveal this answer.";
const humanize = value => value.split("_").map(word => word ? word[0].toUpperCase() + word.slice(1) : word).join(" ");
const displayAuthorityValue = value => Array.isArray(value) ? value.join(", ") : String(value);

function extensionBody(entry, stateValue) {
  const fields = Object.entries(entry.authorityText ?? {}).filter(([key]) => !(
    entry.kind === "boss" && stateValue === 1 && key === "phase_field_notes"
  ));
  return fields.map(([key, value]) => `${humanize(key)}\n${displayAuthorityValue(value)}`).join("\n\n");
}

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
  if (entry.authorityText) return extensionBody(entry, stateValue);
  const approved = WHISPERWOOD_CODEX_UI_BY_ID[entry.id]?.answers ?? [null, null, null];
  return CODEX_QUESTION_LABELS.map((question, index) => {
    const answer = stateValue === 1 && index > 0 ? incomplete : (approved[index] ?? unavailable);
    return `${question}\n${answer}`;
  }).join("\n\n");
}

export function createCodexService({ state, ActionFormData = null }) {
  const ownedItemEvents = new Map(CODEX_ENTRY_REGISTRY.flatMap(entry => {
    // Bedrock exposes no stable craft-output event in the approved subscription
    // set. Whisperwood's recipe-only equipment therefore reconciles its
    // already-ratified successful_craft_output transitions from bounded
    // inventory ownership, just as later-region first_owned entries do.
    const events = entry.events.filter(event =>
      event.event === "first_obtain" ||
      event.event === "first_owned" ||
      event.action === "successful_craft_output"
    ).map(event => event.id);
    return events.length ? [[entry.runtimeId, events]] : [];
  }));
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

  function entriesFor(region, category) { return CODEX_ENTRY_REGISTRY.filter(entry => entry.region === region && entry.category === category); }

  function openEntry(player, regionIndex, categoryIndex, entryIndex) {
    const region = CODEX_UI_REGIONS[regionIndex], category = CODEX_UI_CATEGORIES[categoryIndex];
    const entry = entriesFor(region.id, category.id)[entryIndex];
    if (!entry) return Promise.resolve(false);
    const stateValue = codexStateForEntry(state.playerState(player), entry);
    const form = new ActionFormData()
      .title(`Aionbound Codex — ${codexEntryTitle(entry, stateValue)}`)
      .body(codexEntryBody(entry, stateValue))
      .button("Back");
    return show(player, form, selection => selection === 0 ? openCategory(player, regionIndex, categoryIndex) : false);
  }

  function openCategory(player, regionIndex, categoryIndex) {
    const region = CODEX_UI_REGIONS[regionIndex], category = CODEX_UI_CATEGORIES[categoryIndex];
    if (!region || !category) return Promise.resolve(false);
    const playerState = state.playerState(player), entries = entriesFor(region.id, category.id);
    const form = new ActionFormData().title(`${region.title} — ${category.title}`).body("Choose an entry.");
    for (const entry of entries) {
      const stateValue = codexStateForEntry(playerState, entry);
      form.button(`[${codexStatus(stateValue)}] ${codexEntryTitle(entry, stateValue)}`);
    }
    form.button("Back");
    return show(player, form, selection => selection === entries.length ? openRegion(player, regionIndex) : openEntry(player, regionIndex, categoryIndex, selection));
  }

  function openRegion(player, regionIndex) {
    const region = CODEX_UI_REGIONS[regionIndex];
    if (!region) return Promise.resolve(false);
    const playerState = state.playerState(player);
    const form = new ActionFormData().title(`Aionbound Codex — ${region.title}`).body("Choose a category.");
    for (const category of CODEX_UI_CATEGORIES) {
      const entries = entriesFor(region.id, category.id);
      const complete = entries.filter(entry => codexStateForEntry(playerState, entry) === 2).length;
      form.button(`${category.title} — ${complete}/${entries.length}`);
    }
    form.button("Back");
    return show(player, form, selection => selection === CODEX_UI_CATEGORIES.length ? openRoot(player) : openCategory(player, regionIndex, selection));
  }

  function openRoot(player) {
    if (typeof ActionFormData !== "function") return Promise.resolve(fallback(player));
    const form = new ActionFormData().title("Aionbound Codex — Living World").body("Choose a region.");
    for (const region of CODEX_UI_REGIONS) form.button(region.title);
    return show(player, form, selection => openRegion(player, selection));
  }

  function use(player, itemType) {
    if (itemType === "aionbound:starter_codex_bookmark") state.stamp(player, "bookmark:first_waystone");
    return openRoot(player);
  }

  function discover(player, eventId) {
    const event = CODEX_EVENT_INDEX[eventId];
    if (!event) return false;
    let chapterChanged = false;
    const chapterEventId = event.region === "ww" ? "codex:ww:progression:whisperwood_chapter:entered"
      : event.region === "ah" ? "codex:ah:progression:ashen_chapter:entered"
      : event.region === "cm" ? "codex:cm:progression:crystal_marsh_chapter:entered"
      : event.region === "sr" ? "codex:sr:progression:skyreach_chapter:entered" : null;
    if (chapterEventId && eventId !== chapterEventId) {
      const chapter = CODEX_EVENT_INDEX[chapterEventId];
      chapterChanged = state.transitionCodex(player, chapter.region, chapter.category, chapter.index, chapter.state);
    }
    return state.transitionCodex(player, event.region, event.category, event.index, event.state) || chapterChanged;
  }
  function reconcileOwnedItems(player) {
    const container = player.getComponent?.("minecraft:inventory")?.container;
    if (!container) return 0;
    let transitions = 0;
    for (let slot = 0; slot < container.size && transitions < 8; slot++) {
      const item = container.getItem(slot), events = item && ownedItemEvents.get(item.typeId);
      if (!events) continue;
      for (const eventId of events) if (discover(player, eventId)) transitions++;
    }
    return transitions;
  }
  return { guidance, use, openRoot, openRegion, openCategory, openEntry, discover, reconcileOwnedItems, deriveGoals };
}
