package progressive.progression;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@interface StateRequirement { String id(); String scope(); String type(); int defaultValue() default 0; String persistence(); }
@ModContent(kind="item", id="progressive:memory_crystal")
@StateRequirement(id="progressive:player_rank", scope="player", type="number", persistence="persistent")
@Behavior(id="progressive:memory_crystal/use", ownerKind="item", owner="progressive:memory_crystal", trigger="item_use", actions="update_persistent_state,send_player_feedback", conditions="state_comparison")
public final class Fixture {}
