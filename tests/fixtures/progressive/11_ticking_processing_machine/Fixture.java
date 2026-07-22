package progressive.machine;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@interface StateRequirement { String id(); String scope(); String type(); String persistence(); }
@ModContent(kind="block", id="progressive:crystal_press")
@StateRequirement(id="progressive:press_progress", scope="block", type="number", persistence="persistent")
@Behavior(id="progressive:crystal_press/tick", ownerKind="block", owner="progressive:crystal_press", trigger="object_tick", actions="update_persistent_state,add_item", conditions="state_comparison")
public final class Fixture {}
