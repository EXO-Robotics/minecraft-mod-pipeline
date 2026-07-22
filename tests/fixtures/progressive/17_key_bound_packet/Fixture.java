package progressive.packet;
@interface ModContent { String kind(); String id(); }
@interface Behavior { String id(); String ownerKind(); String owner(); String trigger(); String actions(); String conditions() default ""; }
@interface NetworkIntent { String id(); String direction(); String trigger(); String payload(); String authority(); String action(); String replacement(); }
@ModContent(kind="item", id="progressive:dash_emblem")
@NetworkIntent(id="progressive:dash_packet", direction="client_to_server", trigger="key_press.g", payload="player_id,direction", authority="server", action="apply_velocity", replacement="item_use")
@Behavior(id="progressive:dash_emblem/use", ownerKind="item", owner="progressive:dash_emblem", trigger="item_use", actions="apply_velocity,start_cooldown", conditions="cooldown_ready,client_server_side")
public final class Fixture {}
