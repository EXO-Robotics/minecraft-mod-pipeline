package progressive.mixin;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@interface Unsupported { String feature(); String reason(); }
@ModContent(kind="item", id="progressive:reach_ring")
@Behavior(id="progressive:reach_ring/use", ownerKind="item", owner="progressive:reach_ring", trigger="item_use", actions="send_player_feedback")
@Unsupported(feature="mixin_reach_patch", reason="Bytecode injection into vanilla reach calculation is unsupported; item feedback is independently reconstructable")
public final class Fixture {}
