package progressive.structure;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@ModContent(kind="structure", id="progressive:sky_ruin")
@ModContent(kind="spawn_rule", id="progressive:sky_ruin_guardian_spawn")
@Behavior(id="progressive:sky_ruin/place", ownerKind="structure", owner="progressive:sky_ruin", trigger="player_join", actions="place_structure", conditions="dimension_match")
public final class Fixture {}
