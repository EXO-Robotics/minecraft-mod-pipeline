package progressive.entity;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@ModContent(kind="entity", id="progressive:moss_golem")
@Behavior(id="progressive:moss_golem/spawn", ownerKind="entity", owner="progressive:moss_golem", trigger="entity_spawn", actions="play_sound")
public final class Fixture {}
