"""Execute the unchanged script entrypoint extracted from an exact .mcaddon.

This is a Node-hosted integration proof with a Bedrock API mock. It proves
archive membership, manifest wiring, byte identity, module loading, and startup
subscriptions. It is not BDS, client, gameplay, or console proof.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADDON = ROOT / "dist/aionbound-core-content-beta-g7.mcaddon"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_addon_sha256(addon: Path) -> str:
    supplied = os.environ.get("AIONBOUND_EXPECTED_MCADDON_SHA256")
    if supplied:
        if len(supplied) != 64 or any(character not in "0123456789abcdef" for character in supplied):
            raise AssertionError("AIONBOUND_EXPECTED_MCADDON_SHA256 must be lowercase SHA-256")
        return supplied
    manifest_path = ROOT / "dist/g7-artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    relative = addon.relative_to(ROOT).as_posix()
    matches = [artifact for artifact in manifest["artifacts"] if artifact["path"] == relative]
    if len(matches) != 1:
        raise AssertionError(
            "set AIONBOUND_EXPECTED_MCADDON_SHA256 when testing a package not uniquely bound by dist/g7-artifact-manifest.json"
        )
    return matches[0]["sha256"]


def safe_member(name: str) -> PurePosixPath:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts or not member.parts:
        raise AssertionError(f"unsafe archive member: {name!r}")
    return member


def behavior_pack_bytes(addon: Path) -> tuple[str, bytes]:
    with zipfile.ZipFile(addon) as outer:
        candidates = []
        for info in outer.infolist():
            safe_member(info.filename)
            if info.is_dir() or not info.filename.endswith(".mcpack"):
                continue
            payload = outer.read(info)
            with zipfile.ZipFile(__import__("io").BytesIO(payload)) as nested:
                names = set(nested.namelist())
                if "manifest.json" not in names:
                    continue
                manifest = json.loads(nested.read("manifest.json"))
                if any(module.get("type") == "script" for module in manifest.get("modules", [])):
                    candidates.append((info.filename, payload))
        if len(candidates) != 1:
            raise AssertionError(f"expected one scripted behavior pack, found {len(candidates)}")
        return candidates[0]


def extract_pack(payload: bytes, destination: Path) -> dict[str, bytes]:
    import io

    archived = {}
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for info in archive.infolist():
            member = safe_member(info.filename)
            if info.is_dir():
                continue
            data = archive.read(info)
            archived[member.as_posix()] = data
            target = destination.joinpath(*member.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return archived


MOCK_SERVER = r'''
const signal=()=>({callbacks:[],subscribe(callback){this.callbacks.push(callback);return callback;}});
export const world={
  afterEvents:{itemUse:signal(),itemCompleteUse:signal(),playerBreakBlock:signal(),playerInteractWithEntity:signal(),entityHitEntity:signal(),entityHurt:signal(),entityDie:signal()},
  beforeEvents:{playerInteractWithBlock:signal()},
  getDynamicProperty(){return undefined;},setDynamicProperty(){},getAllPlayers(){return[];},
  getDimension(){return{getEntities(){return[];}};}
};
export const system={beforeEvents:{startup:signal()},currentTick:0,queue:[],intervals:[],run(callback){this.queue.push(callback);},runInterval(callback,ticks){this.intervals.push([callback,ticks]);}};
export class ItemStack{constructor(typeId,amount){this.typeId=typeId;this.amount=amount;}}
export const EquipmentSlot={Offhand:"Offhand",Head:"Head",Chest:"Chest",Legs:"Legs",Feet:"Feet"};
export const EntityComponentTypes={Equippable:"minecraft:equippable"};
'''

MOCK_SERVER_UI = r'''
export class ActionFormData {
  title(){return this;}
  body(){return this;}
  button(){return this;}
  show(){return Promise.resolve({canceled:true});}
}
'''

HARNESS = r'''
import { world, system } from "@minecraft/server";
await import(process.env.AIONBOUND_EXTRACTED_ENTRYPOINT_URL);
const subscriptions = {
  itemUse: world.afterEvents.itemUse.callbacks.length,
  itemCompleteUse: world.afterEvents.itemCompleteUse.callbacks.length,
  playerBreakBlock: world.afterEvents.playerBreakBlock.callbacks.length,
  playerInteractWithBlock: world.beforeEvents.playerInteractWithBlock.callbacks.length,
  playerInteractWithEntity: world.afterEvents.playerInteractWithEntity.callbacks.length,
  entityHitEntity: world.afterEvents.entityHitEntity.callbacks.length,
  entityHurt: world.afterEvents.entityHurt.callbacks.length,
  entityDie: world.afterEvents.entityDie.callbacks.length,
  intervals: system.intervals.length,
  deferred: system.queue.length,
  startup: system.beforeEvents.startup.callbacks.length
};
console.log(JSON.stringify(subscriptions));
'''


class ArchiveExtractedShippedEntrypointProof(unittest.TestCase):
    def test_archive_extracted_entrypoint_registers_expected_startup_wiring(self):
        addon = Path(os.environ.get("AIONBOUND_PACKAGE_UNDER_TEST", DEFAULT_ADDON)).resolve()
        self.assertTrue(addon.is_file(), f"missing package: {addon}")
        self.assertEqual(sha256_file(addon), expected_addon_sha256(addon))
        pack_name, payload = behavior_pack_bytes(addon)

        with tempfile.TemporaryDirectory(prefix="aionbound-packaged-entrypoint-") as temp:
            pack_root = Path(temp) / "behavior_pack"
            archived = extract_pack(payload, pack_root)
            manifest = json.loads(archived["manifest.json"])
            expected_version = os.environ.get("AIONBOUND_EXPECTED_PACK_VERSION")
            if expected_version:
                self.assertEqual(
                    manifest["header"]["version"],
                    [int(part) for part in expected_version.split(".")],
                )
            script_modules = [module for module in manifest["modules"] if module.get("type") == "script"]
            self.assertEqual(len(script_modules), 1)
            entry = safe_member(script_modules[0]["entry"])
            entry_name = entry.as_posix()
            self.assertIn(entry_name, archived)
            entry_path = pack_root.joinpath(*entry.parts)
            self.assertEqual(entry_path.read_bytes(), archived[entry_name])

            script_bytes_before = {
                name: sha256_bytes(data)
                for name, data in archived.items()
                if name.startswith("scripts/") and name.endswith(".js")
            }
            self.assertGreater(len(script_bytes_before), 1)

            # Node metadata and the Bedrock mock are harness-only additions.
            # Every shipped script remains byte-for-byte unchanged after extraction.
            (pack_root / "package.json").write_text('{"type":"module"}\n')
            mock_root = pack_root / "node_modules/@minecraft/server"
            mock_root.mkdir(parents=True)
            (mock_root / "package.json").write_text('{"name":"@minecraft/server","type":"module","exports":"./index.js"}\n')
            (mock_root / "index.js").write_text(MOCK_SERVER)
            mock_ui_root = pack_root / "node_modules/@minecraft/server-ui"
            mock_ui_root.mkdir(parents=True)
            (mock_ui_root / "package.json").write_text(
                '{"name":"@minecraft/server-ui","type":"module","exports":"./index.js"}\n'
            )
            (mock_ui_root / "index.js").write_text(MOCK_SERVER_UI)
            harness = pack_root / "archive-entrypoint-harness.mjs"
            harness.write_text(HARNESS)

            environment = dict(os.environ)
            environment["AIONBOUND_EXTRACTED_ENTRYPOINT_URL"] = entry_path.as_uri()
            completed = subprocess.run(
                ["node", harness.name],
                cwd=pack_root,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            expected_marker = os.environ.get("AIONBOUND_EXPECTED_STARTUP_MARKER")
            if expected_marker:
                self.assertEqual(completed.stderr.count(expected_marker), 1, completed.stderr)
            output = json.loads(completed.stdout.strip().splitlines()[-1])
            expected_startup = 1 if b"registerWhisperwoodRegrowth" in archived[entry_name] else 0
            expected_break = int(any(
                b"playerBreakBlock.subscribe" in data
                for name, data in archived.items()
                if name.startswith("scripts/") and name.endswith(".js")
            ))
            self.assertEqual(output, {
                "itemUse": 1,
                "itemCompleteUse": 1,
                "playerBreakBlock": expected_break,
                "playerInteractWithBlock": 1,
                "playerInteractWithEntity": 1,
                "entityHitEntity": 1,
                "entityHurt": 1,
                "entityDie": 1,
                "intervals": 1,
                "deferred": 1,
                "startup": expected_startup,
            })

            script_bytes_after = {
                name: sha256_bytes((pack_root / name).read_bytes())
                for name in script_bytes_before
            }
            self.assertEqual(script_bytes_after, script_bytes_before)
            self.assertEqual(sha256_bytes(entry_path.read_bytes()), sha256_bytes(archived[entry_name]))
            self.assertTrue(pack_name.endswith(".mcpack"))


if __name__ == "__main__":
    unittest.main()
