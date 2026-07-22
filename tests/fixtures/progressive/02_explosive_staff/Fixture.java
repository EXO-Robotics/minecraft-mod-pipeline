package progressive.explosive;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@ModContent(kind="item", id="progressive:explosive_staff")
@Behavior(id="progressive:explosive_staff/use", ownerKind="item", owner="progressive:explosive_staff", trigger="item_use", actions="spawn_projectile,create_explosion")
public final class Fixture {}
