package showcase.clockwork;

/**
 * Legally original static benchmark vocabulary for Clockwork Gardens.
 *
 * This source is consumed by minecraft-compiler-baseline's evidence scanner. It
 * describes gameplay intent; it is not a claim that Bedrock runtime behavior has
 * been executed or console-tested.
 */
public final class ClockworkGardensShowcase {
    private ClockworkGardensShowcase() {}

    // Content declarations: item, block, recipes, loot, projectile, mob, boss,
    // structure, spawn rules, and player state.
    @ModContent(kind = "item", id = "clockwork_gardens:sunseed_launcher")
    static final Object SUNSEED_LAUNCHER = new Object();

    @ModContent(kind = "item", id = "clockwork_gardens:charged_sunseed")
    static final Object CHARGED_SUNSEED = new Object();

    @ModContent(kind = "item", id = "clockwork_gardens:lumen_ingot")
    static final Object LUMEN_INGOT = new Object();

    @ModContent(kind = "block", id = "clockwork_gardens:lumen_press")
    static final Object LUMEN_PRESS = new Object();

    @ModContent(kind = "recipe", id = "clockwork_gardens:sunseed_launcher_recipe")
    static final Object LAUNCHER_RECIPE = new Object();

    @ModContent(kind = "recipe", id = "clockwork_gardens:lumen_press_processing")
    static final Object PROCESSING_RECIPE = new Object();

    @ModContent(kind = "loot_table", id = "clockwork_gardens:blocks/lumen_press")
    static final Object PRESS_LOOT = new Object();

    @ModContent(kind = "entity", id = "clockwork_gardens:sunseed_projectile")
    static final Object SUNSEED_PROJECTILE = new Object();

    @ModContent(kind = "entity", id = "clockwork_gardens:brass_sprout")
    static final Object BRASS_SPROUT = new Object();

    @ModContent(kind = "entity", id = "clockwork_gardens:verdant_colossus")
    static final Object VERDANT_COLOSSUS = new Object();

    @ModContent(kind = "structure", id = "clockwork_gardens:colossus_grove")
    static final Object COLOSSUS_GROVE = new Object();

    @ModContent(kind = "spawn_rule", id = "clockwork_gardens:brass_sprout")
    static final Object SPROUT_SPAWN = new Object();

    @ModContent(kind = "player_state", id = "clockwork_gardens:garden_rank")
    static final Object GARDEN_RANK = new Object();

    // Stable-script mechanic: launcher use applies an effect, starts a cooldown,
    // and spawns the projectile. Parameters are specified in expected-quality.json.
    @Behavior(id = "clockwork_gardens:sunseed_launcher/use", ownerKind = "item", owner = "clockwork_gardens:sunseed_launcher", trigger = "item_use", actions = "spawn_projectile,apply_effect,start_cooldown,play_sound")
    static void useLauncher() {}

    @Behavior(id = "clockwork_gardens:sunseed_projectile/impact", ownerKind = "entity", owner = "clockwork_gardens:sunseed_projectile", trigger = "projectile_impact", actions = "create_explosion,apply_effect,spawn_particles,play_sound")
    static void impactTarget() {}

    // Persistent, player-scoped progression. The isolation contract below makes
    // per-player ownership and upgrade behavior explicit without claiming a run.
    @StateRequirement(id = "garden_rank", scope = "player", type = "number", defaultValue = 0, persistence = "persistent")
    static int gardenRank;

    @StateRequirement(id = "sunseeds_harvested", scope = "player", type = "number", defaultValue = 0, persistence = "persistent")
    static int sunseedsHarvested;

    @Behavior(id = "clockwork_gardens:progression/restore", ownerKind = "player_state", owner = "clockwork_gardens:garden_rank", trigger = "player_join", actions = "send_player_feedback")
    static void restorePlayerProgress() {}

    @Behavior(id = "clockwork_gardens:progression/award", ownerKind = "player_state", owner = "clockwork_gardens:garden_rank", trigger = "entity_death", actions = "update_persistent_state,send_player_feedback")
    static void awardPlayerProgress() {}

    // Persistent processing machine: bounded object ticks advance progress, emit
    // output, and retain ownership/state required for restart reconstruction.
    @StateRequirement(id = "press_energy", scope = "block", type = "number", defaultValue = 0, persistence = "persistent")
    static int pressEnergy;

    @StateRequirement(id = "press_progress", scope = "block", type = "number", defaultValue = 0, persistence = "persistent")
    static int pressProgress;

    @StateRequirement(id = "press_owner", scope = "block", type = "number", defaultValue = 0, persistence = "persistent")
    static int pressOwner;

    @Behavior(id = "clockwork_gardens:lumen_press/process", ownerKind = "block", owner = "clockwork_gardens:lumen_press", trigger = "object_tick", conditions = "state_comparison", actions = "update_persistent_state,remove_item,add_item,spawn_particles,play_sound")
    static void processLumen() {}

    // Approved controller redesign: a Java-style container/key interaction is
    // replaced with one labeled, cancelable action form.
    @UiIntent(id = "clockwork_gardens:lumen_press_controls", title = "Lumen Press", purpose = "Start processing or inspect owner-scoped progress", controls = "Start Process,Inspect Progress,Cancel")
    static final Object PRESS_FORM = new Object();

    @Register(kind = "block", id = "clockwork_gardens:lumen_press")
    static final class LumenPress {
        @Trigger("block_interact")
        public void openControls(Context context) {
            context.openForm("clockwork_gardens:lumen_press_controls");
        }
    }

    @NetworkIntent(id = "clockwork_gardens:press_key_redesign", direction = "client_to_server", trigger = "java_key_binding", payload = "requested_press_action", authority = "server", action = "open_controller_form", replacement = "block interaction opens a stable server-ui action form")
    static final Object PRESS_INTERACTION_REDESIGN = new Object();

    // Data-driven mechanic: the sprout's spawn rule and deterministic spawn setup
    // are reconstructed from stable entity data plus an evidence-backed event.
    @Behavior(id = "clockwork_gardens:brass_sprout/on_spawn", ownerKind = "entity", owner = "clockwork_gardens:brass_sprout", trigger = "entity_spawn", actions = "set_entity_phase,spawn_particles,play_sound")
    static void initializeSprout() {}

    @StateRequirement(id = "boss_phase", scope = "entity", type = "number", defaultValue = 1, persistence = "persistent")
    static int bossPhase;

    @StateRequirement(id = "boss_instance_guard", scope = "entity", type = "number", defaultValue = 0, persistence = "persistent")
    static int bossInstanceGuard;

    @Behavior(id = "clockwork_gardens:verdant_colossus/phase_one", ownerKind = "entity", owner = "clockwork_gardens:verdant_colossus", trigger = "state_transition", conditions = "health_threshold", actions = "set_entity_phase,spawn_projectile,send_player_feedback")
    static void bossPhaseOne() {}

    @Behavior(id = "clockwork_gardens:verdant_colossus/phase_two", ownerKind = "entity", owner = "clockwork_gardens:verdant_colossus", trigger = "state_transition", conditions = "health_threshold", actions = "set_entity_phase,place_structure,spawn_entity,send_player_feedback")
    static void bossPhaseTwo() {}

    @Behavior(id = "clockwork_gardens:verdant_colossus/phase_three", ownerKind = "entity", owner = "clockwork_gardens:verdant_colossus", trigger = "state_transition", conditions = "health_threshold", actions = "set_entity_phase,spawn_projectile,apply_effect,send_player_feedback")
    static void bossPhaseThree() {}

    // Deliberately unsupported mechanic: the compiler must report and omit this.
    @Unsupported(feature = "clockwork_gardens:desktop_shader_portal", reason = "Requires arbitrary desktop GPU shader injection and cannot be honestly reconstructed with stable Marketplace Add-On APIs")
    static final class DesktopShaderPortal {}
}

@interface ModContent { String kind(); String id(); }
@interface Register { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@interface StateRequirement { String id(); String scope(); String type(); int defaultValue() default 0; String persistence(); }
@interface Trigger { String value(); }
@interface UiIntent { String id(); String title(); String purpose(); String controls(); }
@interface NetworkIntent { String id(); String direction(); String trigger(); String payload(); String authority(); String action(); String replacement(); }
@interface Unsupported { String feature(); String reason(); }

final class Context {
    public void openForm(String id) {}
}
