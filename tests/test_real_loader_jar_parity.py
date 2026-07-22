from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from mccompiler.frontends.javap_analyzer import analyze_archive, available
from mccompiler.scan import scan_path


FIXTURES = Path(__file__).parent / "fixtures" / "frontends"
JDK = Path("/opt/homebrew/opt/openjdk/bin")
JAVAC = str(JDK / "javac") if (JDK / "javac").is_file() else (shutil.which("javac") or "javac")
JAR = str(JDK / "jar") if (JDK / "jar").is_file() else (shutil.which("jar") or "jar")


def _working_jdk() -> tuple[bool, str]:
    missing = [path for path in (JAVAC, JAR) if not Path(path).is_file()]
    if missing:
        return False, f"JDK tools missing: {', '.join(missing)}"
    for tool, version_flag in ((JAVAC, "-version"), (JAR, "--version")):
        try:
            probe = subprocess.run([tool, version_flag], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            return False, f"JDK tool probe failed for {tool}: {exc}"
        if probe.returncode:
            message = (probe.stderr or probe.stdout).strip()
            return False, f"JDK tool is not usable: {tool}: {message}"
    return True, "working javac, jar, and javap required"


WORKING_JDK, JDK_SKIP_REASON = _working_jdk()


STUBS = {
    "net/fabricmc/api/ModInitializer.java": "package net.fabricmc.api; public interface ModInitializer { void onInitialize(); }",
    "net/minecraft/item/Item.java": "package net.minecraft.item; public class Item { public Item(Settings s){} public static class Settings{} }",
    "net/minecraft/block/Block.java": "package net.minecraft.block; public class Block { public Block(Object x){} }",
    "net/minecraft/registry/Registries.java": "package net.minecraft.registry; public final class Registries { public static final Object ITEM=new Object(), BLOCK=new Object(), ENTITY_TYPE=new Object(), BLOCK_ENTITY_TYPE=new Object(); }",
    "net/minecraft/registry/Registry.java": "package net.minecraft.registry; public final class Registry { public static <T>T register(Object r,Object id,T value){return value;} }",
    "net/minecraft/util/Identifier.java": "package net.minecraft.util; public final class Identifier { public static Identifier of(String n,String p){return new Identifier();} }",
    "net/minecraft/world/PersistentState.java": "package net.minecraft.world; public class PersistentState {}",
    "net/fabricmc/fabric/api/event/player/UseItemCallback.java": "package net.fabricmc.fabric.api.event.player; public interface UseItemCallback { Object call(Object a,Object b,Object c); Event EVENT=new Event(); class Event { public void register(UseItemCallback c){} } }",
    "net/fabricmc/fabric/api/event/player/AttackEntityCallback.java": "package net.fabricmc.fabric.api.event.player; public interface AttackEntityCallback { Object call(Object a,Object b,Object c,Object d,Object e); Event EVENT=new Event(); class Event { public void register(AttackEntityCallback c){} } }",
    "net/fabricmc/fabric/api/event/lifecycle/v1/ServerTickEvents.java": "package net.fabricmc.fabric.api.event.lifecycle.v1; public final class ServerTickEvents { public interface EndTick { void call(Object s); } public static final Event END_SERVER_TICK=new Event(); public static class Event { public void register(EndTick c){} } }",
    "net/fabricmc/fabric/api/networking/v1/ServerPlayNetworking.java": "package net.fabricmc.fabric.api.networking.v1; public final class ServerPlayNetworking { public interface Handler { void call(Object p,Object c); } public static void registerGlobalReceiver(Object id,Handler h){} }",
    "org/spongepowered/asm/mixin/Mixin.java": "package org.spongepowered.asm.mixin; import java.lang.annotation.*; @Retention(RetentionPolicy.RUNTIME) public @interface Mixin { Class<?> value(); }",
    "org/spongepowered/asm/mixin/injection/At.java": "package org.spongepowered.asm.mixin.injection; import java.lang.annotation.*; @Retention(RetentionPolicy.RUNTIME) public @interface At { String value(); }",
    "org/spongepowered/asm/mixin/injection/Inject.java": "package org.spongepowered.asm.mixin.injection; import java.lang.annotation.*; @Retention(RetentionPolicy.RUNTIME) public @interface Inject { String method(); At at(); }",
    "cpw/mods/fml/common/Mod.java": "package cpw.mods.fml.common; import java.lang.annotation.*; @Retention(RetentionPolicy.RUNTIME) public @interface Mod { String modid(); String name(); String version(); @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD) public @interface EventHandler{} }",
    "cpw/mods/fml/common/event/FMLPreInitializationEvent.java": "package cpw.mods.fml.common.event; public class FMLPreInitializationEvent{}",
    "cpw/mods/fml/common/event/FMLInitializationEvent.java": "package cpw.mods.fml.common.event; public class FMLInitializationEvent{}",
    "cpw/mods/fml/common/eventhandler/SubscribeEvent.java": "package cpw.mods.fml.common.eventhandler; import java.lang.annotation.*; @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD) public @interface SubscribeEvent{}",
    "cpw/mods/fml/common/network/NetworkRegistry.java": "package cpw.mods.fml.common.network; import cpw.mods.fml.common.network.simpleimpl.SimpleNetworkWrapper; public final class NetworkRegistry { public static final NetworkRegistry INSTANCE=new NetworkRegistry(); public SimpleNetworkWrapper newSimpleChannel(String s){return new SimpleNetworkWrapper();} }",
    "cpw/mods/fml/common/network/simpleimpl/SimpleNetworkWrapper.java": "package cpw.mods.fml.common.network.simpleimpl; import cpw.mods.fml.relauncher.Side; public class SimpleNetworkWrapper { public void registerMessage(Class<?> h,Class<?> m,int i,Side s){} }",
    "cpw/mods/fml/common/registry/GameRegistry.java": "package cpw.mods.fml.common.registry; public final class GameRegistry { public static void registerItem(Object x,String s){} public static void registerBlock(Object x,String s){} public static void registerTileEntity(Class<?> x,String s){} public static void addRecipe(Object... x){} public static void addSmelting(Object a,Object b,float c){} }",
    "cpw/mods/fml/common/registry/EntityRegistry.java": "package cpw.mods.fml.common.registry; public final class EntityRegistry { public static void registerModEntity(Class<?> a,String b,int c,Object d,int e,int f,boolean g){} }",
    "cpw/mods/fml/relauncher/Side.java": "package cpw.mods.fml.relauncher; public enum Side { CLIENT, SERVER }",
    "cpw/mods/fml/relauncher/IFMLLoadingPlugin.java": "package cpw.mods.fml.relauncher; public interface IFMLLoadingPlugin{}",
    "net/minecraftforge/common/MinecraftForge.java": "package net.minecraftforge.common; public final class MinecraftForge { public static final Bus EVENT_BUS=new Bus(); public static class Bus { public void register(Object x){} } }",
    "net/minecraftforge/event/entity/living/LivingHurtEvent.java": "package net.minecraftforge.event.entity.living; public class LivingHurtEvent{}",
}


def _compile_fixture(root: Path, temp: Path, archive_name: str) -> Path:
    stubs = temp / "stubs"
    for relative, source in STUBS.items():
        target = stubs / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    classes = temp / "classes"
    classes.mkdir()
    sources = sorted((root / "src/main/java").rglob("*.java")) + sorted(stubs.rglob("*.java"))
    subprocess.run([str(JAVAC), "-g", "-d", str(classes), *map(str, sources)], check=True, text=True)
    archive = temp / archive_name
    subprocess.run([str(JAR), "--create", "--file", str(archive), "-C", str(classes), "."], check=True)
    for metadata in ("fabric.mod.json", "mcmod.info"):
        if (root / metadata).exists():
            subprocess.run([str(JAR), "--update", "--file", str(archive), "-C", str(root), metadata], check=True)
    if (root / "META-INF").exists():
        subprocess.run([str(JAR), "--update", "--file", str(archive), "-C", str(root), "META-INF"], check=True)
    return archive


class BytecodeDiagnosticTests(unittest.TestCase):
    def test_unavailable_and_dependency_failures_are_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "broken.jar"
            with zipfile.ZipFile(archive, "w") as jar:
                jar.writestr("fixture/Missing.class", b"not-a-class")
            with patch("mccompiler.frontends.javap_analyzer._javap", return_value=None):
                unavailable = analyze_archive(archive)
            self.assertIn("bytecode_analyzer_unavailable", {row["code"] for row in unavailable["diagnostics"]})
            failed = SimpleNamespace(returncode=1, stdout="", stderr="Error: class not found: missing.Dependency")
            with patch("mccompiler.frontends.javap_analyzer._javap", return_value="/usable/javap"), patch("mccompiler.frontends.javap_analyzer.subprocess.run", return_value=failed):
                dependency = analyze_archive(archive)
            self.assertIn("bytecode_dependency_unavailable", {row["code"] for row in dependency["diagnostics"]})


@unittest.skipUnless(available() and WORKING_JDK, JDK_SKIP_REASON if not WORKING_JDK else "working javap required")
class RealLoaderJarParityTests(unittest.TestCase):
    def test_authentic_fabric_source_jar_supported_fact_parity(self):
        root = FIXTURES / "fabric_modern"
        with tempfile.TemporaryDirectory() as directory:
            jar_ir = scan_path(_compile_fixture(root, Path(directory), "fabric.jar"))
        source_ir = scan_path(root)
        expected_content = {("item", "authentic_fabric:wand"), ("block", "authentic_fabric:machine")}
        self.assertEqual(expected_content, {(x["kind"], x["identifier"]) for x in jar_ir["content"]})
        self.assertEqual({"item_use", "entity_hit", "object_tick"}, {x["trigger"]["type"] for x in jar_ir["behaviors"]})
        self.assertEqual({x["id"] for x in source_ir["state"]}, {x["id"] for x in jar_ir["state"]})
        self.assertEqual(len(source_ir["networking_intent"]), len(jar_ir["networking_intent"]))
        self.assertTrue(any(x.get("feature") == "fabric_mixin:bytecode" for x in jar_ir["unsupported_hooks"]))
        self._assert_fact_contract(jar_ir)

    def test_unresolved_obfuscated_archive_is_diagnosed(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            source = temp / "a.java"
            source.write_text("public final class a { public void a() {} }", encoding="utf-8")
            classes = temp / "classes"; classes.mkdir()
            subprocess.run([JAVAC, "-d", str(classes), str(source)], check=True)
            archive = temp / "obfuscated.jar"
            subprocess.run([JAR, "--create", "--file", str(archive), "-C", str(classes), "."], check=True)
            ir = scan_path(archive)
        self.assertIn("bytecode_obfuscation_suspected", {row["code"] for row in ir["diagnostics"]})

    def test_authentic_forge_source_jar_supported_fact_parity(self):
        root = FIXTURES / "forge_1_7_10"
        with tempfile.TemporaryDirectory() as directory:
            jar_ir = scan_path(_compile_fixture(root, Path(directory), "forge.jar"))
        source_ir = scan_path(root)
        supported = {("item", "authentic_legacy:legacy_wand"), ("block", "authentic_legacy:legacy_machine"), ("block_entity", "authentic_legacy:legacy_machine"), ("entity", "authentic_legacy:legacy_golem")}
        self.assertEqual(supported, {(x["kind"], x["identifier"]) for x in jar_ir["content"] if x["kind"] in {"item", "block", "block_entity", "entity"}})
        self.assertEqual({"entity_hurt"}, {x["trigger"]["type"] for x in jar_ir["behaviors"]})
        self.assertEqual(len(source_ir["networking_intent"]), len(jar_ir["networking_intent"]))
        self.assertTrue(any(str(x.get("feature", "")).startswith("forge_coremod_source:") for x in jar_ir["unsupported_hooks"]))
        self._assert_fact_contract(jar_ir)

    def _assert_fact_contract(self, ir: dict) -> None:
        fact_types = {row.get("fact_type") for row in ir["bytecode_evidence"]}
        self.assertTrue({"class", "annotation", "method", "invoke", "constant", "resource"} <= fact_types)
        semantic_evidence = [e for section in ("content", "behaviors", "state", "networking_intent") for row in ir[section] for e in row.get("evidence", [])]
        self.assertTrue(semantic_evidence)
        self.assertTrue(all(e["source_mode"] == "bytecode-javap" and e["confidence"] < 1 for e in semantic_evidence))


if __name__ == "__main__":
    unittest.main()
