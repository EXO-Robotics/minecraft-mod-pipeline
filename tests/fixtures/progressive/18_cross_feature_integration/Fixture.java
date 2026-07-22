package progressive.integration;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@interface StateRequirement { String id(); String scope(); String type(); String persistence(); }
@interface UiIntent { String id(); String title(); String purpose(); String controls(); }
@ModContent(kind="item", id="progressive:rift_key")
@ModContent(kind="block", id="progressive:rift_altar")
@ModContent(kind="entity", id="progressive:rift_guardian")
@ModContent(kind="structure", id="progressive:rift_chamber")
@ModContent(kind="recipe", id="progressive:rift_key_recipe")
@StateRequirement(id="progressive:altar_charge", scope="block", type="number", persistence="persistent")
@UiIntent(id="progressive:rift_altar_form", title="Rift Altar", purpose="Charge and open the rift", controls="charge,open,cancel")
@Behavior(id="progressive:rift_key/charge", ownerKind="item", owner="progressive:rift_key", trigger="item_use_on_block", actions="update_persistent_state,play_sound,start_cooldown", conditions="block_match,cooldown_ready")
@Behavior(id="progressive:rift_altar/open", ownerKind="block", owner="progressive:rift_altar", trigger="state_transition", actions="place_structure,spawn_entity,open_interaction_ui", conditions="state_comparison")
public final class Fixture {}
