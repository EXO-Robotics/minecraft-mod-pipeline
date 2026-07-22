package progressive.cooldown;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@ModContent(kind="item", id="progressive:blink_charm")
@Behavior(id="progressive:blink_charm/use", ownerKind="item", owner="progressive:blink_charm", trigger="item_use", actions="teleport,start_cooldown", conditions="cooldown_ready")
public final class Fixture {}
