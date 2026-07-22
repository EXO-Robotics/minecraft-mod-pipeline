package progressive.basic;
@interface ModContent { String kind(); String id(); }
@ModContent(kind="item", id="progressive:copper_token")
@interface ItemMarker {}
@ModContent(kind="block", id="progressive:polished_frame")
@interface BlockMarker {}
@ModContent(kind="recipe", id="progressive:polished_frame_recipe")
public final class Fixture {}
