package progressive.boss;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@interface StateRequirement { String id(); String scope(); String type(); String persistence(); }
@ModContent(kind="entity", id="progressive:basalt_titan")
@StateRequirement(id="progressive:boss_phase", scope="entity", type="number", persistence="persistent")
@Behavior(id="progressive:basalt_titan/phase", ownerKind="entity", owner="progressive:basalt_titan", trigger="state_transition", actions="set_entity_phase,trigger_behavior", conditions="health_threshold")
public final class Fixture {}
