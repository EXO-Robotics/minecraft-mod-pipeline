package fixture.fabric;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.item.Item;
import net.minecraft.block.Block;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;
import net.minecraft.world.PersistentState;

public final class AuthenticFabricMod implements ModInitializer {
    public static final String MOD_ID = "authentic_fabric";
    public static final Item WAND = Registry.register(Registries.ITEM, Identifier.of(MOD_ID, "wand"), new Item(new Item.Settings()));
    public static final Block MACHINE = Registry.register(Registries.BLOCK, Identifier.of(MOD_ID, "machine"), new Block(null));

    @Override
    public void onInitialize() {
        UseItemCallback.EVENT.register((player, world, hand) -> null);
        AttackEntityCallback.EVENT.register((player, world, hand, entity, hit) -> null);
        ServerTickEvents.END_SERVER_TICK.register(server -> {});
        ServerPlayNetworking.registerGlobalReceiver(NetworkPayload.ID, (payload, context) -> {});
    }

    public static final class FixtureWorldState extends PersistentState {}
    public static final class NetworkPayload { public static final Object ID = new Object(); }
}
