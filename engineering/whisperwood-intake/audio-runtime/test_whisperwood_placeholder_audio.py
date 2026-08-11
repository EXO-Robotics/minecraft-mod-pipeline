#!/usr/bin/env python3
"""Deterministic static checks for the bounded Whisperwood placeholder audio pass."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "engineering/whisperwood-intake/audio-runtime"
MAP_PATH = RUNTIME / "WHISPERWOOD_PLACEHOLDER_AUDIO_MAP.json"
SCHEMA_PATH = RUNTIME / "WHISPERWOOD_PLACEHOLDER_AUDIO_MAP.schema.json"
SOUNDS_PATH = ROOT / "resource_pack/sounds.json"
TICKET_PATH = ROOT / "engineering/authority/support-tickets/W1-ASSET-AUDIO-001.json"

EXPECTED_IDS = {
    "aionbound:bark_wraith",
    "aionbound:briar_elk",
    "aionbound:hollow_widow_spider",
    "aionbound:lantern_hare",
    "aionbound:mosskip_buck",
    "aionbound:mosskip_doe",
    "aionbound:mosskip_fawn",
    "aionbound:rootback_boar",
    "aionbound:rot_wolf",
    "aionbound:thorn_stalker",
}

# Exact identifiers inspected in Mojang bedrock-samples resource_pack/sounds.json.
REVIEWED_VANILLA_EVENTS = {
    "mob.goat.ambient",
    "mob.goat.death",
    "mob.goat.hurt",
    "mob.pig.death",
    "mob.pig.say",
    "mob.rabbit.death",
    "mob.rabbit.hurt",
    "mob.rabbit.idle",
    "mob.ravager.ambient",
    "mob.ravager.death",
    "mob.ravager.hurt",
    "mob.spider.death",
    "mob.spider.say",
    "mob.vex.ambient",
    "mob.vex.death",
    "mob.vex.hurt",
    "mob.wolf.bark",
    "mob.wolf.death",
    "mob.wolf.hurt",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    mapping = load_json(MAP_PATH)
    schema = load_json(SCHEMA_PATH)
    sounds = load_json(SOUNDS_PATH)
    ticket = load_json(TICKET_PATH)

    assert mapping["schema"] == "aionbound.wave1.whisperwood.placeholder_audio.v1"
    assert mapping["status"] == "EARLY_PLACEHOLDER_STATIC_BINDING_ONLY"
    assert schema["properties"]["status"]["const"] == mapping["status"]
    assert mapping["scope"]["ecosystem"] == "WHISPERWOOD"
    assert mapping["scope"]["entity_count"] == 10
    assert mapping["scope"]["events_bound"] == ["ambient", "hurt", "death"]

    mapped = {entry["entity_id"]: entry for entry in mapping["entities"]}
    bound = sounds["entity_sounds"]["entities"]
    assert set(mapped) == EXPECTED_IDS
    assert set(bound) == EXPECTED_IDS

    for entity_id in sorted(EXPECTED_IDS):
        entry = mapped[entity_id]
        rp_entry = bound[entity_id]
        assert rp_entry["events"] == entry["events"]
        assert rp_entry["pitch"] == entry["pitch"]
        assert rp_entry["volume"] == entry["volume"]
        assert set(entry["events"]) == {"ambient", "hurt", "death"}
        assert set(entry["events"].values()) <= REVIEWED_VANILLA_EVENTS
        assert entry["signature_action"]["status"] == "WITHHELD"

        short_id = entity_id.split(":", 1)[1]
        behavior = load_json(ROOT / f"behavior_pack/entities/{short_id}.entity.json")
        description = behavior["minecraft:entity"]["description"]
        components = behavior["minecraft:entity"]["components"]
        assert description["identifier"] == entity_id
        assert components["minecraft:ambient_sound_interval"] == entry["ambient_interval"]
        interval = entry["ambient_interval"]
        assert interval["event_name"] == "ambient"
        assert 8 <= interval["value"] <= 14
        assert 8 <= interval["range"] <= 12

    implementation = mapping["implementation"]
    assert implementation["audio_bytes_added"] is False
    assert implementation["sound_definitions_added"] is False
    assert implementation["client_entity_sound_effect_aliases_added"] is False
    assert implementation["animation_sound_timelines_added"] is False

    media = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "resource_pack").rglob("*")
        if path.is_file() and path.suffix.lower() in {".ogg", ".wav", ".fsb"}
    )
    assert media == [], f"unexpected audio bytes in placeholder pass: {media}"
    assert not (ROOT / "resource_pack/sounds/sound_definitions.json").exists()

    blocker = mapping["proof_boundary"]["final_exit_blocker"]
    assert blocker == "W1-ASSET-AUDIO-001"
    assert ticket["ticket_id"] == blocker
    assert ticket["status"] == "OPEN_BLOCKING_WAVE_1_EXIT_NOT_WHISPERWOOD_CHECKPOINT"
    assert "custom_audio_complete" in ticket["engineering_boundary"]["claims_forbidden"]
    assert "sound_identity_pass" in ticket["engineering_boundary"]["claims_forbidden"]

    print(
        json.dumps(
            {
                "schema": "aionbound.wave1.whisperwood.placeholder_audio.validation.v1",
                "status": "PASS_STATIC_ONLY",
                "entity_count": len(mapped),
                "event_binding_count": sum(len(entry["events"]) for entry in mapped.values()),
                "signature_actions_withheld": len(mapped),
                "audio_byte_count": len(media),
                "final_exit_blocker": blocker,
                "claims": ["JSON_PARSE", "REFERENCE_CLOSURE", "NO_AUDIO_BYTES"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
