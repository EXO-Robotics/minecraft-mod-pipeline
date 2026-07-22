package progressive.equivalent;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@ModContent(kind="item", id="progressive:equivalence_wand")
@Behavior(id="progressive:equivalence/use", ownerKind="item", owner="progressive:equivalence_wand", trigger="item_use", actions="spawn_projectile,start_cooldown", conditions="cooldown_ready")
final class DirectStyle {}
@Behavior( conditions = "cooldown_ready", actions = "spawn_projectile,start_cooldown", trigger = "item_use", owner = "progressive:equivalence_wand", ownerKind = "item", id = "progressive:equivalence/use" )
public final class Fixture {}
