package fixture.api;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.util.LinkedHashMap;
import java.util.Map;

/** Dependency-free vocabulary that resembles the signals emitted by real mod APIs. */
public final class FixtureApi {
    private FixtureApi() {}

    @Retention(RetentionPolicy.RUNTIME) @Target({ElementType.TYPE, ElementType.FIELD})
    public @interface Register { String kind(); String id(); }

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
    public @interface Trigger { String value(); }

    @Retention(RetentionPolicy.RUNTIME) @Target({ElementType.TYPE, ElementType.METHOD})
    public @interface Tick { int interval(); }

    @Retention(RetentionPolicy.RUNTIME) @Target({ElementType.TYPE, ElementType.METHOD})
    public @interface State { String[] keys(); String scope(); boolean persistent() default true; }

    @Retention(RetentionPolicy.RUNTIME) @Target({ElementType.TYPE, ElementType.METHOD})
    public @interface Phase { int value(); String condition(); }

    @Retention(RetentionPolicy.RUNTIME) @Target({ElementType.TYPE, ElementType.METHOD})
    public @interface FormReplacement { String id(); String title(); String purpose(); }

    @Retention(RetentionPolicy.RUNTIME) @Target({ElementType.TYPE, ElementType.METHOD})
    public @interface Approximation { String reason(); String bedrockStrategy(); }

    @Retention(RetentionPolicy.RUNTIME) @Target({ElementType.TYPE, ElementType.METHOD})
    public @interface Unsupported { String reason(); String javaFeature(); }

    public static final class Registry {
        private static final Map<String, Object> ENTRIES = new LinkedHashMap<>();
        public static <T> T register(String kind, String id, T value) {
            ENTRIES.put(kind + ":" + id, value);
            return value;
        }
        public static Map<String, Object> entries() { return Map.copyOf(ENTRIES); }
    }

    public static class Context {
        private final Map<String, Integer> state = new LinkedHashMap<>();
        public int get(String key) { return state.getOrDefault(key, 0); }
        public void set(String key, int value) { state.put(key, value); }
        public void addEffect(String id, int ticks, int amplifier) {}
        public void cooldown(String itemId, int ticks) {}
        public void spawnProjectile(String id, double speed) {}
        public void explode(float power, boolean breaksBlocks) {}
        public void damage(int amount) {}
        public void playSound(String id) {}
        public void openForm(String id) {}
        public void placeStructure(String id) {}
        public void setBlock(String id) {}
        public void dropLoot(String table) {}
    }
}
