// Approved Whisperwood question text from the frozen implementation map.
// A null value means the authored answer has an unresolved acquisition or
// progression dependency and is deliberately absent from shipping runtime.
const rows = Object.freeze([
  Object.freeze(["whisper_bark", null, "Whisperwood planks, handles, stocks, hatchet parts, and armor wrap.", "Use the first forest wood currency to establish the Whisperwood craft loop."]),
  Object.freeze(["moss_resin", null, null, "Pair it with glow spore for the forest binder path."]),
  Object.freeze(["glow_spore", null, null, "Night paths and bloom patches lead toward the utility-light line."]),
  Object.freeze(["hollow_amber", null, null, "Search hollow wood and root caves for the mid-forest catalyst."]),
  Object.freeze(["lantern_fur", null, null, "Follow safe night trails and lantern blooms toward light utility."]),
  Object.freeze(["moon_sap", null, null, "Lily pools and deep-night forest open the soft-power path."]),
  Object.freeze(["root_heart", null, null, "Investigate deep roots once the early binder loop is established."]),
  Object.freeze(["briar_antler", null, null, "Rare meadows lead into the elite equipment and trophy path."]),
  Object.freeze(["widow_silk", null, null, "Caves beneath roots connect silk to the elite craft line."]),
  Object.freeze(["ancient_acorn", null, "Ancient Acorn Display with pedestal wood.", null]),
  Object.freeze(["whisperwood_log", null, "Whisperwood planks, bark harvest, handles, and stocks.", "Turn the forest silhouette into the first building and crafting material."]),
  Object.freeze(["stripped_whisperwood_log", "Worked Whisperwood timber.", "Intermediate timber for player builds.", "Use crafted forest wood to extend camps and bases."]),
  Object.freeze(["whisperwood_wood", "Bark-on-all-sides timber used for deep-woods massing.", "Structural builds and forest massing.", "Carry deep-forest identity into player construction."]),
  Object.freeze(["whisperwood_planks", "Safe-forest building timber made from Whisperwood wood.", "Furniture, handles, camps, and trophy bases.", "Planks connect gathered bark and logs to tools and shelter."]),
  Object.freeze(["whisperwood_leaves", null, "Compost or decay relationships where runtime rules support them.", "Canopy density marks the living forest and its clearings."]),
  Object.freeze(["whisperwood_sapling", null, "Renewable tree growth and future logs.", "Replanting closes the forest sustainability loop."]),
  Object.freeze(["whisperwood_roots", null, "Harvest fantasy and traversal footing.", "Root paths lead toward ravines, caves, and deeper resources."]),
  Object.freeze(["moss_bark", null, "Binding materials and build detail.", "Moss identity points back to resin and the early binder loop."]),
  Object.freeze(["hollow_wood", null, "Mystery builds and hollow-amber source fantasy.", "Search hollows and caves for the mid-forest catalyst."]),
  Object.freeze(["forest_brick", null, "Structure construction and shrine-language builds.", null]),
  Object.freeze(["star_grass", null, "Early fiber and fodder.", "Use the common clearing plant to begin the fiber line."]),
  Object.freeze(["whisper_fern", null, "Bandage analogue and soft materials.", "The understory supplies early recovery materials."]),
  Object.freeze(["pale_reed", "Reed gathered at wet forest edges.", null, "Wet edges connect early gathering to the first weapon path."]),
  Object.freeze(["glow_moss", "Soft-glowing moss found in caves and at night.", null, "Caves turn night comfort into the charm path."]),
  Object.freeze(["mooncap_mushroom", null, "Food and minor-buff consumables.", "Night gathering supports longer forest expeditions."]),
  Object.freeze(["lantern_bloom", "Path flower clustered near lantern posts and lantern hares.", null, "Bloom patches and hare trails identify safer night routes."]),
  Object.freeze(["hollow_lily", null, "Moon-sap catalyst helper.", "Lily pools point toward the forest soft-power line."]),
  Object.freeze(["root_flower", "Colored flower gathered in root zones.", null, "Root zones lead toward bracelet materials and deeper catalysts."]),
  Object.freeze(["briar_vine", "Binding vine gathered in thorn thickets.", null, "Thickets connect binding material to the forest combat line."]),
  Object.freeze(["ember_thistle", null, "Minor heat-resistance seed.", null]),
  Object.freeze(["mosskip_fawn", null, "Its soft moss scraps feed early Moss Bind Glue.", "Fawns point toward does and crowned bucks."]),
  Object.freeze(["mosskip_doe", null, "Moss resin and soft hide support binding and early armor padding.", "Dusk paths lead toward lantern blooms."]),
  Object.freeze(["mosskip_buck", null, null, null]),
  Object.freeze(["lantern_hare", null, "Lantern fur supports badges, hooks, and light trim.", "Its trails mark safer night ground."]),
  Object.freeze(["rootback_boar", null, null, "Deep rooters reveal hollow amber and late forest catalysts."]),
  Object.freeze(["briar_elk", null, null, null]),
  Object.freeze(["rot_wolf", null, null, "Pack howls warn that a thorn stalker may be near."]),
  Object.freeze(["thorn_stalker", null, null, null]),
  Object.freeze(["hollow_widow_spider", null, null, "Root caves connect discovery to the forest's elite craft line."]),
  Object.freeze(["bark_wraith", null, "Hollow amber and moon sap support staff, pendant, and late forest crafting.", null]),
]);

export const CODEX_QUESTION_LABELS = Object.freeze([
  "What did I find?",
  "What can I make?",
  "What should I investigate next?",
]);

export const WHISPERWOOD_CODEX_UI_BY_ID = Object.freeze(Object.fromEntries(rows.map(([id, found, make, next]) => [id, Object.freeze({
  answers: Object.freeze([found, make, next]),
})])));
