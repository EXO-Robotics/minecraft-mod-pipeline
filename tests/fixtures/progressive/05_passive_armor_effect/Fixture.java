package progressive.armor;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@ModContent(kind="item", id="progressive:glider_chestplate")
@Behavior(id="progressive:glider_chestplate/tick", ownerKind="item", owner="progressive:glider_chestplate", trigger="scheduled_tick", actions="apply_effect", conditions="equipped_armor_match")
public final class Fixture {}
