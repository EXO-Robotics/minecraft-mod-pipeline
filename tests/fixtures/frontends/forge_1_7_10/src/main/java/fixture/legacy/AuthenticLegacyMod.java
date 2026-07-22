package fixture.legacy;

import cpw.mods.fml.common.Mod;
import cpw.mods.fml.common.Mod.EventHandler;
import cpw.mods.fml.common.event.FMLInitializationEvent;
import cpw.mods.fml.common.event.FMLPreInitializationEvent;
import cpw.mods.fml.common.network.NetworkRegistry;
import cpw.mods.fml.common.network.simpleimpl.SimpleNetworkWrapper;
import cpw.mods.fml.common.registry.EntityRegistry;
import cpw.mods.fml.common.registry.GameRegistry;
import cpw.mods.fml.relauncher.Side;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import cpw.mods.fml.common.eventhandler.SubscribeEvent;

@Mod(modid = AuthenticLegacyMod.MODID, name = "Authentic Legacy Fixture", version = "1.0.0")
public final class AuthenticLegacyMod {
    public static final String MODID = "authentic_legacy";
    private static final Object WAND = new Object();
    private static final Object MACHINE = new Object();
    private static final Object RECIPE_OUTPUT = new Object();
    private final SimpleNetworkWrapper network = NetworkRegistry.INSTANCE.newSimpleChannel("legacy_channel");

    @EventHandler
    public void preInit(FMLPreInitializationEvent event) {
        GameRegistry.registerItem(WAND, "legacy_wand");
        GameRegistry.registerBlock(MACHINE, "legacy_machine");
        GameRegistry.registerTileEntity(LegacyMachineTile.class, "authentic_legacy:legacy_machine");
        EntityRegistry.registerModEntity(LegacyGolem.class, "legacy_golem", 1, this, 64, 3, true);
        GameRegistry.addRecipe(RECIPE_OUTPUT, " X ", " X ", 'X', WAND);
        GameRegistry.addSmelting(WAND, RECIPE_OUTPUT, 0.5f);
        network.registerMessage(LegacyHandler.class, LegacyMessage.class, 0, Side.SERVER);
    }

    @EventHandler
    public void init(FMLInitializationEvent event) {
        MinecraftForge.EVENT_BUS.register(this);
    }

    @SubscribeEvent
    public void onLivingHurt(LivingHurtEvent event) {}

    public static final class LegacyMachineTile {}
    public static final class LegacyGolem {}
    public static final class LegacyHandler {}
    public static final class LegacyMessage {}
}
