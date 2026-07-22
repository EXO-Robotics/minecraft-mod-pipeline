package fixture.representative;

import fixture.api.FixtureApi.Approximation;
import fixture.api.FixtureApi.Context;
import fixture.api.FixtureApi.FormReplacement;
import fixture.api.FixtureApi.Phase;
import fixture.api.FixtureApi.Register;
import fixture.api.FixtureApi.Registry;
import fixture.api.FixtureApi.State;
import fixture.api.FixtureApi.Tick;
import fixture.api.FixtureApi.Trigger;
import fixture.api.FixtureApi.Unsupported;

/** One deterministic mod whose source deliberately exercises every Phase 0 behavior family. */
public final class RepresentativeMod {
    public static final String MOD_ID = "representative";

    @Register(kind = "item", id = "representative:phase_blade")
    public static final PhaseBlade PHASE_BLADE = Registry.register("item", "representative:phase_blade", new PhaseBlade());

    @Register(kind = "item", id = "representative:storm_orb")
    public static final StormOrb STORM_ORB = Registry.register("item", "representative:storm_orb", new StormOrb());

    @Register(kind = "block", id = "representative:aether_machine")
    public static final AetherMachine AETHER_MACHINE = Registry.register("block", "representative:aether_machine", new AetherMachine());

    @Register(kind = "entity", id = "representative:clockwork_golem")
    public static final ClockworkGolem GOLEM = Registry.register("entity", "representative:clockwork_golem", new ClockworkGolem());

    @Register(kind = "entity", id = "representative:rift_boss")
    public static final RiftBoss BOSS = Registry.register("entity", "representative:rift_boss", new RiftBoss());

    public void onInitialize() {
        Registry.register("recipe", "representative:phase_blade", "data/representative/recipes/phase_blade.json");
        Registry.register("recipe", "representative:aether_smelting", "data/representative/recipes/aether_smelting.json");
        Registry.register("loot_table", "representative:blocks/aether_machine", "data/representative/loot_tables/blocks/aether_machine.json");
        Registry.register("sound", "representative:machine_hum", "assets/representative/sounds.json");
        Registry.register("structure", "representative:rift_arena", "data/representative/structures/rift_arena.json");
        Registry.register("spawn_rule", "representative:clockwork_golem", "data/representative/spawn_rules/clockwork_golem.json");
        Registry.register("player_state", "representative:rift_attunement", new PlayerProgress());
    }

    @State(keys = {"rift_attunement", "bosses_defeated"}, persistent = true)
    public static final class PlayerProgress {
        @Trigger("player_join")
        public void restore(Context context) {
            context.set("rift_attunement", context.get("rift_attunement"));
        }

        @Trigger("entity_killed")
        public void onBossDefeated(Context context) {
            context.set("bosses_defeated", context.get("bosses_defeated") + 1);
            context.set("rift_attunement", 1);
        }
    }

    public static final class PhaseBlade {
        @Trigger("item_use")
        public void use(Context context) {
            context.addEffect("minecraft:speed", 100, 1);
            context.cooldown("representative:phase_blade", 40);
            context.playSound("representative:phase_blade_activate");
        }

        @Trigger("item_use_on_block")
        public void useOnBlock(Context context) {
            context.setBlock("representative:charged_aether_block");
            context.addEffect("minecraft:night_vision", 200, 0);
        }

        @Trigger("entity_hit")
        public void hitEntity(Context context) {
            context.damage(7);
            context.addEffect("minecraft:slowness", 60, 1);
        }

        @Trigger("block_break")
        public void postMine(Context context) {
            context.dropLoot("representative:bonus_crystal");
            context.set("blade_charge", Math.min(100, context.get("blade_charge") + 5));
        }
    }

    public static final class StormOrb {
        @Trigger("item_use")
        public void throwOrb(Context context) {
            context.spawnProjectile("representative:storm_projectile", 1.6);
            context.cooldown("representative:storm_orb", 80);
        }

        @Trigger("projectile_impact")
        public void onImpact(Context context) {
            context.explode(2.5f, false);
            context.addEffect("minecraft:weakness", 120, 1);
            context.playSound("representative:storm_burst");
        }
    }

    @State(keys = {"energy", "progress", "owner"}, persistent = true)
    @Tick(interval = 20)
    public static final class AetherMachine {
        @Tick(interval = 20)
        @Trigger("server_tick")
        public void tick(Context context) {
            int energy = context.get("energy");
            if (energy >= 10) {
                context.set("energy", energy - 10);
                context.set("progress", context.get("progress") + 1);
                if (context.get("progress") >= 5) {
                    context.dropLoot("representative:refined_aether");
                    context.set("progress", 0);
                }
            }
        }

        @FormReplacement(title = "Aether Machine", purpose = "Replace the Java container GUI with a Bedrock action form")
        @Trigger("block_interact")
        public void openMachine(Context context) {
            context.openForm("representative:aether_machine_control");
        }
    }

    @State(keys = {"patrol_point", "temper"}, persistent = true)
    public static class ClockworkGolem {
        @Trigger("entity_spawn")
        public void onSpawn(Context context) {
            context.set("temper", 0);
            context.playSound("representative:golem_wake");
        }

        @Trigger("entity_hurt")
        public void onHurt(Context context) {
            context.set("temper", context.get("temper") + 1);
        }
    }

    @State(keys = {"phase", "shield", "arena_initialized"}, persistent = true)
    public static final class RiftBoss extends ClockworkGolem {
        @Phase(value = 1, condition = "health > 0.66")
        public void phaseOne(Context context) {
            context.spawnProjectile("representative:rift_bolt", 1.2);
        }

        @Phase(value = 2, condition = "health <= 0.66 && health > 0.33")
        public void phaseTwo(Context context) {
            context.set("shield", 1);
            context.placeStructure("representative:rift_arena");
            context.explode(1.0f, false);
        }

        @Phase(value = 3, condition = "health <= 0.33")
        public void phaseThree(Context context) {
            context.set("shield", 0);
            context.addEffect("minecraft:strength", 200, 2);
            context.spawnProjectile("representative:rift_barrage", 2.0);
        }
    }

    @Approximation(
        reason = "Java shader-driven screen distortion has no direct Bedrock add-on equivalent",
        bedrockStrategy = "particle ring, fog pulse, camera shake, and positional sound"
    )
    public static final class RiftDistortionRenderer {}

    @Unsupported(
        reason = "Requires arbitrary JVM bytecode injection into another mod at runtime",
        javaFeature = "Mixin redirect targeting third.party.mod.SecretMachine#consume"
    )
    public static final class ThirdPartyMixinInjection {}
}
