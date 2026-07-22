package fixture.companion;

import java.util.LinkedHashMap;
import java.util.Map;

/** A second dependency-free source unit used to test modpack boundaries and cross-mod references. */
public final class CompatCompanion {
    public static final String MOD_ID = "compat_companion";
    public static final Map<String, String> REGISTRATIONS = new LinkedHashMap<>();

    public void onInitialize() {
        REGISTRATIONS.put("item:compat_companion:attuned_token", "texture=compat_companion:item/attuned_token");
        REGISTRATIONS.put("recipe:compat_companion:attuned_token", "ingredient=representative:phase_blade");
        REGISTRATIONS.put("behavior:item_use", "effect=minecraft:glowing;cooldown=20");
    }
}
