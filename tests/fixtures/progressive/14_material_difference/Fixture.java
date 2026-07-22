package progressive.different;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@ModContent(kind="item", id="progressive:difference_wand")
@Behavior(id="progressive:difference/use", ownerKind="item", owner="progressive:difference_wand", trigger="item_use", actions="spawn_projectile", conditions="cooldown_ready")
final class SafeStyle {}
@Behavior(id="progressive:difference/use", ownerKind="item", owner="progressive:difference_wand", trigger="item_use", actions="create_explosion", conditions="cooldown_ready")
public final class Fixture {}
