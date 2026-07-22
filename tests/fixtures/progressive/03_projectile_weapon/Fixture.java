package progressive.projectile;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@ModContent(kind="item", id="progressive:wind_bow")
@Behavior(id="progressive:wind_bow/use", ownerKind="item", owner="progressive:wind_bow", trigger="item_use", actions="spawn_projectile")
public final class Fixture {}
