#!/usr/bin/env python3
"""Author authority-gated presentation shells for five Packet 006 identities.

This generator intentionally creates no acquisition, recipe, loot, runtime,
effect, progression, sidegrade, encounter, or finale behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
BASE_COMMIT = "c60848db75954822e187e6675e6a198148c5089e"
BASE_TREE = "f05961009bbda650ea646d2462c952257946f251"

ASSETS = {
    "surveyor_medallion": {
        "name": "Surveyor Medallion",
        "native": "engineering/native-assets/packet006-missing/evidence/surveyor_medallion",
        "clip": None,
    },
    "surveyor_staff": {
        "name": "Surveyor Staff",
        "native": "engineering/native-assets/packet006-missing/evidence/surveyor_staff",
        "clip": "hold",
    },
    "trail_compass": {
        "name": "Trail Compass",
        "native": "engineering/native-assets/packet006-missing/evidence/trail_compass",
        "clip": "needle_idle",
    },
    "warden_sigil": {
        "name": "Warden Sigil",
        "native": "engineering/native-assets/packet006-missing/evidence/warden_sigil",
        "clip": "pulse",
    },
    "twinbond_relic": {
        "name": "Twinbond Relic",
        "native": "engineering/native-assets/twinbond/evidence/twinbond_relic",
        "clip": "dual_pulse",
    },
}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def item_doc(asset: str) -> dict:
    # No menu_category: these identities are not Creative acquisition paths.
    return {
        "format_version": "1.21.80",
        "minecraft:item": {
            "description": {"identifier": f"aionbound:{asset}"},
            "components": {
                "minecraft:display_name": {"value": f"item.aionbound:{asset}.name"},
                "minecraft:icon": {"textures": {"default": asset}},
                "minecraft:max_stack_size": 1,
            },
        },
    }


def attachable_doc(asset: str, clip: str | None) -> dict:
    description: dict[str, object] = {
        "identifier": f"aionbound:{asset}",
        "materials": {"default": "entity_alphatest"},
        "textures": {"default": f"textures/aionbound/wave1/packet006/models/{asset}"},
        "geometry": {"default": f"geometry.aionbound.{asset}"},
        "render_controllers": ["controller.render.aionbound.default"],
    }
    if clip:
        description["animations"] = {clip: f"animation.aionbound.{asset}.{clip}"}
        description["scripts"] = {"animate": [clip]}
    return {"format_version": "1.10.0", "minecraft:attachable": {"description": description}}


def icon(asset: str, output: Path) -> None:
    """Draw one original, transparent, pixel-readable inventory icon."""
    transparent = (0, 0, 0, 0)
    ink = (29, 31, 39, 255)
    brass = (190, 139, 57, 255)
    gold = (243, 204, 105, 255)
    teal = (54, 174, 173, 255)
    pale = (198, 238, 224, 255)
    ember = (224, 89, 55, 255)
    tide = (61, 132, 210, 255)
    violet = (146, 91, 206, 255)
    im = Image.new("RGBA", (32, 32), transparent)
    d = ImageDraw.Draw(im)

    if asset == "surveyor_medallion":
        d.line((16, 3, 16, 8), fill=brass, width=2)
        d.ellipse((7, 7, 25, 25), fill=ink, outline=gold, width=2)
        d.polygon([(16, 9), (19, 15), (23, 16), (19, 18), (16, 23), (13, 18), (9, 16), (13, 14)], fill=teal, outline=pale)
        d.rectangle((15, 13, 17, 19), fill=gold)
    elif asset == "surveyor_staff":
        d.line((9, 28, 20, 7), fill=ink, width=5)
        d.line((10, 28, 21, 7), fill=brass, width=2)
        d.ellipse((16, 3, 27, 14), fill=ink, outline=gold, width=2)
        d.polygon([(21, 5), (25, 9), (21, 13), (17, 9)], fill=teal, outline=pale)
        d.line((7, 24, 14, 28), fill=gold, width=2)
    elif asset == "trail_compass":
        d.ellipse((5, 5, 27, 27), fill=ink, outline=brass, width=3)
        d.ellipse((9, 9, 23, 23), outline=pale, width=1)
        d.polygon([(16, 7), (19, 16), (16, 14), (13, 16)], fill=ember, outline=gold)
        d.polygon([(16, 25), (13, 16), (16, 18), (19, 16)], fill=teal, outline=pale)
        d.rectangle((15, 15, 17, 17), fill=gold)
    elif asset == "warden_sigil":
        d.polygon([(16, 3), (26, 9), (24, 22), (16, 29), (8, 22), (6, 9)], fill=ink, outline=brass)
        d.polygon([(16, 7), (22, 11), (21, 20), (16, 25), (11, 20), (10, 11)], fill=violet, outline=gold)
        d.rectangle((14, 10, 18, 21), fill=pale)
        d.rectangle((11, 14, 21, 18), fill=pale)
        d.rectangle((15, 13, 17, 19), fill=ink)
    elif asset == "twinbond_relic":
        d.ellipse((4, 8, 17, 23), fill=ember, outline=gold, width=2)
        d.ellipse((15, 8, 28, 23), fill=tide, outline=pale, width=2)
        d.polygon([(16, 5), (22, 16), (16, 28), (10, 16)], fill=ink, outline=gold)
        d.polygon([(16, 9), (19, 16), (16, 23), (13, 16)], fill=violet, outline=pale)
        d.rectangle((15, 14, 17, 18), fill=gold)
    else:
        raise ValueError(asset)

    output.parent.mkdir(parents=True, exist_ok=True)
    im.save(output, format="PNG", optimize=False)


def replace_language(lines: list[str]) -> list[str]:
    prefixes = [f"item.aionbound:{asset}.name=" for asset in ASSETS]
    markers = {
        "# BEGIN AUTHORITY-GATED PACKET 006 PRESENTATION SHELLS",
        "# END AUTHORITY-GATED PACKET 006 PRESENTATION SHELLS",
    }
    kept = [
        line for line in lines
        if line not in markers and not any(line.startswith(prefix) for prefix in prefixes)
    ]
    while kept and kept[-1] == "":
        kept.pop()
    entries = ["# BEGIN AUTHORITY-GATED PACKET 006 PRESENTATION SHELLS"]
    entries.extend(f"item.aionbound:{asset}.name={spec['name']}" for asset, spec in ASSETS.items())
    entries.append("# END AUTHORITY-GATED PACKET 006 PRESENTATION SHELLS")
    return kept + [""] + entries


def author() -> dict:
    outputs: list[Path] = []
    atlas_path = RP / "textures/item_texture.json"
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))

    for asset, spec in ASSETS.items():
        native = ROOT / spec["native"]
        sources = {
            "geometry": native / "native-exports/pass-2.geo.json",
            "animation": native / "native-exports/pass-2.animation.json",
            "model_texture": native / f"native-project/textures/{asset}.png",
        }
        if not all(path.is_file() for path in sources.values()):
            raise FileNotFoundError(asset)

        targets = {
            "geometry": RP / f"models/aionbound/wave1/packet006/{asset}.geo.json",
            "animation": RP / f"animations/aionbound/wave1/packet006/{asset}.animation.json",
            "model_texture": RP / f"textures/aionbound/wave1/packet006/models/{asset}.png",
        }
        for key, target in targets.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(sources[key], target)
            outputs.append(target)

        item = BP / f"items/{asset}.item.json"
        attachable = RP / f"attachables/{asset}.attachable.json"
        inventory_icon = RP / f"textures/aionbound/wave1/packet006/icons/{asset}.png"
        write_json(item, item_doc(asset))
        write_json(attachable, attachable_doc(asset, spec["clip"]))
        icon(asset, inventory_icon)
        outputs.extend((item, attachable, inventory_icon))
        atlas["texture_data"][asset] = {
            "textures": f"textures/aionbound/wave1/packet006/icons/{asset}"
        }

    write_json(atlas_path, atlas)
    lang_path = RP / "texts/en_US.lang"
    lang_path.write_text("\n".join(replace_language(lang_path.read_text(encoding="utf-8").splitlines())) + "\n", encoding="utf-8")
    outputs.extend((atlas_path, lang_path))

    report = {
        "schema": "aionforge.wave1.packet006.presentation_shells.v1",
        "status": "PRESENTATION_SHELLS_SOURCE_COMPLETE_AUTHORITY_GATED",
        "base": {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "identities": list(ASSETS),
        "counts": {"items": 5, "attachables": 5, "native_geometries": 5, "native_animation_documents": 5, "native_model_textures": 5, "handcrafted_inventory_icons": 5},
        "native_binding": {
            asset: {
                "geometry": f"{spec['native']}/native-exports/pass-2.geo.json",
                "animation": f"{spec['native']}/native-exports/pass-2.animation.json",
                "model_texture": f"{spec['native']}/native-project/textures/{asset}.png",
                "presentation_clip": spec["clip"],
            }
            for asset, spec in ASSETS.items()
        },
        "authority_gate": {
            "state": "DORMANT_PRESENTATION_IDENTITY_ONLY",
            "requires_future_authority": ["acquisition", "recipes", "loot", "runtime_effects", "equipment_roles", "progression", "encounter_rewards", "finale", "sidegrades"],
            "creative_005": "DEFERRED_UNCHANGED_NO_SIDEGRADES",
        },
        "invariants": {
            "new_recipes": 0,
            "new_loot_tables": 0,
            "new_runtime_handlers": 0,
            "new_persistence_domains": 0,
            "new_progression_edges": 0,
            "new_finale_behavior": 0,
            "new_sidegrades": 0,
            "menu_category_exposure": False,
        },
        "artifacts": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}
            for path in sorted(set(outputs))
        ],
        "proof_boundary": "SOURCE IDENTITY, EXACT NATIVE PASS-2 BYTE BINDING, ATTACHABLE REFERENCES, PNG DECODE, ATLAS, LANGUAGE, AND TARGETED SEMANTIC TESTS ONLY; NO ACQUISITION, GAMEPLAY, PACKAGE, BDS, CLIENT, MULTIPLAYER, CONSOLE, CANDIDATE, MARKETPLACE, OR RELEASE PROOF",
    }
    write_json(HERE / "PACKET006_PRESENTATION_SHELLS_REPORT.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report_path = HERE / "PACKET006_PRESENTATION_SHELLS_REPORT.json"
    before = sha(report_path) if args.check and report_path.is_file() else None
    report = author()
    if args.check and before != sha(report_path):
        raise SystemExit("nondeterministic presentation-shell report")
    print(json.dumps({"status": report["status"], "counts": report["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
