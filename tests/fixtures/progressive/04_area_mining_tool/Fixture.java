package progressive.mining;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@ModContent(kind="item", id="progressive:vein_hammer")
@Behavior(id="progressive:vein_hammer/break", ownerKind="item", owner="progressive:vein_hammer", trigger="block_break", actions="break_block,modify_item_durability", conditions="held_item_match")
public final class Fixture {}
