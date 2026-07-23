===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/batch-preflight.json =====

{
  "schema_version": "1.0.0",
  "batch_id": "forest-wave-1-parallel-batch-1",
  "status": "BATCH_PREFLIGHT_READY",
  "prepared_from_branch": "codex/forest-wave-1-resonance-sling",
  "immutable_base_commit": "e9009b70502f4e0db57986ea52cf8d4f7998cc1b",
  "integration_branch": "codex/forest-wave-1-parallel-batch-1",
  "production_model": "gpt-5.6-sol",
  "production_reasoning_effort": "light",
  "wave_policy": {
    "maximum_child_concurrency": 3,
    "wave_a": [
      "signal_ruin",
      "gloamwing_stalker",
      "forest_attunement"
    ],
    "wave_b": [
      "mossback_forager",
      "barkguard_charm"
    ],
    "start_wave_b_when_slot_free": true
  },
  "contracts": {
    "signal_ruin": "production/reconstruction-waves/forest-wave-1/signal_ruin/original-production-manifest.json",
    "gloamwing_stalker": "production/reconstruction-waves/forest-wave-1/gloamwing_stalker/original-production-manifest.json",
    "forest_attunement": "production/reconstruction-waves/forest-wave-1/forest_attunement/original-production-manifest.json",
    "mossback_forager": "production/reconstruction-waves/forest-wave-1/mossback_forager/original-production-manifest.json",
    "barkguard_charm": "production/reconstruction-waves/forest-wave-1/barkguard_charm/original-production-manifest.json"
  },
  "assignment_directory": "production/batches/forest-wave-1-parallel-batch-1/assignments",
  "reservation_manifest": "production/batches/forest-wave-1-parallel-batch-1/reservations.json",
  "shared_registration_request_schema": {
    "kind": "identifier|uuid|localization|script-entry|texture-atlas|spawn|structure|persistence",
    "requested_value": "string",
    "feature_local_source": "repository-relative path",
    "integration_action": "string",
    "collision_check": "PASS|FAIL",
    "required": true
  },
  "resource_ownership": {
    "authoritative_bds": "MAIN_CODEX_SERIALIZED",
    "stable_installation": "production/features/resonance-sling/runtime/stable-server-seed",
    "preview_installation": "production/features/resonance-sling/runtime/preview-server-seed",
    "runtime_copy_policy": "REUSE_ONE_INSTALLATION_PER_VERSION_DO_NOT_COPY_TO_WORKTREES",
    "blockbench_gui": "MAIN_CODEX_SERIALIZED",
    "desktop_minecraft": "MAIN_CODEX_ONLY",
    "creator_tools": "MAIN_CODEX_ONLY"
  },
  "integration_order": [
    "forest_attunement",
    "barkguard_charm",
    "mossback_forager",
    "gloamwing_stalker",
    "signal_ruin"
  ],
  "acceptance": {
    "candidate_dispositions": [
      "ACCEPT_CANDIDATE",
      "ACCEPT_WITH_LIMITATIONS",
      "REVISE",
      "REJECT",
      "BLOCKED",
      "QUARANTINED"
    ],
    "required_before_acceptance": [
      "Contract compliance",
      "Write-scope compliance",
      "Originality and contamination scan",
      "Stable API validation",
      "Feature-local deterministic tests",
      "Main-Codex authoritative qualification",
      "Resolved critical and high red-team findings",
      "Deterministic cleanup",
      "Clean candidate worktree"
    ],
    "unavailable_gates": {
      "desktop_client": "PENDING",
      "physical_ps4": "PENDING_PHYSICAL_HARDWARE",
      "marketplace_submission": "NOT_SUBMITTED"
    }
  },
  "batch_stop_conditions": [
    "Shared identifier or UUID ownership cannot be trusted",
    "Multiple candidates mutate the same unassigned shared state",
    "Qualification infrastructure produces contradictory results",
    "Resonance Sling frozen artifacts or source require destructive mutation",
    "Systemic critical originality, persistence, or world-integrity failure"
  ],
  "protected_paths": [
    "production/features/resonance-sling",
    "production/reconstruction-waves/forest-wave-1/resonance_sling",
    "prototypes/blockbench/phase_anchor_test.bbmodel",
    "production/batches/forest-wave-1-parallel-batch-1",
    "Combined manifests and global registries"
  ],
  "release_restrictions": [
    "NO_PUSH",
    "NO_TAG",
    "NO_RELEASE",
    "NO_REALM_DEPLOYMENT",
    "NO_MARKETPLACE_SUBMISSION",
    "NO_PHYSICAL_PS4_CLAIM"
  ]
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reservations.json =====

{
  "schema_version": "1.0.0",
  "batch_id": "forest-wave-1-parallel-batch-1",
  "runtime_namespace": "ccoriginal_cc",
  "features": {
    "signal_ruin": {
      "identifier_prefixes": [
        "ccoriginal_cc:signal_ruin"
      ],
      "reserved_identifiers": [
        "ccoriginal_cc:signal_ruin_anchor",
        "ccoriginal_cc:signal_ruin_cache",
        "ccoriginal_cc:signal_ruin_activation",
        "ccoriginal_cc:signal_ruin_completed",
        "ccoriginal_cc:signal_ruin_test"
      ],
      "dynamic_property_prefix": "ccoriginal_cc:signal_ruin_",
      "uuids": {
        "behavior_header": "556acdce-2ddc-4cbd-b08d-f62681387306",
        "behavior_data_module": "59c9ac60-a5ba-44a2-8517-c1f7a2fd51e3",
        "behavior_script_module": "45e8f7ad-197e-45ff-99ee-60b6fec7e30d",
        "resource_header": "f15d006f-c77c-45e5-a6d8-84da52a5db0e",
        "resource_module": "214f239c-6fe6-44b1-b69f-38c9b005a3dd"
      }
    },
    "gloamwing_stalker": {
      "identifier_prefixes": [
        "ccoriginal_cc:gloamwing"
      ],
      "reserved_identifiers": [
        "ccoriginal_cc:gloamwing_stalker",
        "geometry.ccoriginal_cc.gloamwing_stalker",
        "animation.ccoriginal_cc.gloamwing_stalker",
        "controller.animation.ccoriginal_cc.gloamwing_stalker",
        "ccoriginal_cc:gloamwing_test"
      ],
      "dynamic_property_prefix": "ccoriginal_cc:gloamwing_",
      "uuids": {
        "behavior_header": "e2b0816e-74ed-4457-a8af-a9eb889ecbcb",
        "behavior_data_module": "00f4fc42-7b63-4860-bcd2-06d31724130c",
        "behavior_script_module": "09f04f92-c28a-40a4-935e-8968a7ccb3c3",
        "resource_header": "3a750a45-d232-4a26-aef0-4844df456d74",
        "resource_module": "b503a43d-5d18-4147-8958-bd948d2d73b4"
      }
    },
    "forest_attunement": {
      "identifier_prefixes": [
        "ccoriginal_cc:forest_attunement"
      ],
      "reserved_identifiers": [
        "ccoriginal_cc:forest_attunement_sigil",
        "ccoriginal_cc:forest_attunement_v1",
        "ccoriginal_cc:forest_attunement_reset",
        "ccoriginal_cc:forest_attunement_test"
      ],
      "dynamic_property_prefix": "ccoriginal_cc:forest_attunement_",
      "uuids": {
        "behavior_header": "43b642d0-a651-45cf-ae20-96a0b853fba5",
        "behavior_data_module": "e7798870-c7e2-4522-87bf-d046b08b442f",
        "behavior_script_module": "2db423eb-5691-4207-bb37-01751206657d",
        "resource_header": "0317044d-9b78-4101-aa2e-cb395af4e948",
        "resource_module": "f00200ff-d682-4f87-9873-2e92abe15060"
      }
    },
    "mossback_forager": {
      "identifier_prefixes": [
        "ccoriginal_cc:mossback"
      ],
      "reserved_identifiers": [
        "ccoriginal_cc:mossback_forager",
        "geometry.ccoriginal_cc.mossback_forager",
        "animation.ccoriginal_cc.mossback_forager",
        "controller.animation.ccoriginal_cc.mossback_forager",
        "ccoriginal_cc:mossback_gift",
        "ccoriginal_cc:mossback_test"
      ],
      "dynamic_property_prefix": "ccoriginal_cc:mossback_",
      "uuids": {
        "behavior_header": "6a67bb25-2953-4be9-9b32-611cf09be04a",
        "behavior_data_module": "73f807d7-55f1-479e-92b7-017aaba56863",
        "behavior_script_module": "3b8fc604-2517-451e-8a51-e321aa9dbc77",
        "resource_header": "698f7eac-f081-49f9-8e82-1e0f362d704d",
        "resource_module": "d25ac1b1-2d66-475c-bc0a-c5f33620fbb2"
      }
    },
    "barkguard_charm": {
      "identifier_prefixes": [
        "ccoriginal_cc:barkguard"
      ],
      "reserved_identifiers": [
        "ccoriginal_cc:barkguard_charm",
        "geometry.ccoriginal_cc.barkguard_charm",
        "animation.ccoriginal_cc.barkguard_charm",
        "controller.animation.ccoriginal_cc.barkguard_charm",
        "ccoriginal_cc:barkguard_test"
      ],
      "dynamic_property_prefix": "ccoriginal_cc:barkguard_",
      "uuids": {
        "behavior_header": "2985974d-139b-4142-9c25-ae1aba1f95bf",
        "behavior_data_module": "1ace8116-c3de-4fa4-b083-c6a3b2c79d39",
        "behavior_script_module": "a8cbf915-0ec4-4c20-95c0-5905667428fd",
        "resource_header": "29eb411e-8ad2-4666-bb55-756efbd4944c",
        "resource_module": "5580dd51-6b31-414b-b15e-0160f5f5b34f"
      }
    }
  }
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/assignments/signal_ruin.json =====

{
  "batch_id": "forest-wave-1-parallel-batch-1",
  "agent_id": "production-agent-signal-ruin",
  "model": "gpt-5.6-sol",
  "reasoning_effort": "light",
  "feature_id": "signal_ruin",
  "feature_name": "Signal Ruin",
  "wave": "A",
  "base_commit": "PREFLIGHT_COMMIT",
  "branch": "codex/parallel-batch-1/signal-ruin",
  "worktree": "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/signal-ruin",
  "contract": "production/reconstruction-waves/forest-wave-1/signal_ruin/original-production-manifest.json",
  "reservations": "production/batches/forest-wave-1-parallel-batch-1/reservations.json",
  "owned_paths": [
    "production/features/signal-ruin/",
    "prototypes/blockbench/signal_ruin/",
    "tools/build_signal_ruin.py",
    "tests/test_signal_ruin.py"
  ],
  "required_outputs": [
    "Original mcstructure and deterministic authoring input",
    "Anchor entity and encounter script",
    "Loot table and internal placement, stress, and cleanup functions",
    "Behavior and resource packs",
    "Feature-local tests and deterministic packages",
    "reports/candidate-packet.json"
  ],
  "authoritative_bds_owner": "MAIN_CODEX",
  "blockbench_gui_owner": "MAIN_CODEX",
  "shared_files_may_be_edited": false,
  "stop_conditions": [
    "Contract ambiguity beyond permitted latitude",
    "Stable API cannot guarantee reward idempotency",
    "World or persistence integrity risk",
    "Write-scope collision",
    "Third-party contamination"
  ]
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/assignments/gloamwing_stalker.json =====

{
  "batch_id": "forest-wave-1-parallel-batch-1",
  "agent_id": "production-agent-gloamwing-stalker",
  "model": "gpt-5.6-sol",
  "reasoning_effort": "light",
  "feature_id": "gloamwing_stalker",
  "feature_name": "Gloamwing Stalker",
  "wave": "A",
  "base_commit": "PREFLIGHT_COMMIT",
  "branch": "codex/parallel-batch-1/gloamwing-stalker",
  "worktree": "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/gloamwing-stalker",
  "contract": "production/reconstruction-waves/forest-wave-1/gloamwing_stalker/original-production-manifest.json",
  "reservations": "production/batches/forest-wave-1-parallel-batch-1/reservations.json",
  "owned_paths": [
    "production/features/gloamwing-stalker/",
    "prototypes/blockbench/gloamwing_stalker/",
    "tools/build_gloamwing_stalker.py",
    "tests/test_gloamwing_stalker.py"
  ],
  "required_outputs": [
    "Editable Blockbench source, native geometry, original texture, animations, and controller",
    "Client and behavior entity definitions, loot, and disabled-by-default spawn rule",
    "Internal summon, stress, and cleanup functions",
    "Feature-local tests and deterministic packages",
    "reports/candidate-packet.json"
  ],
  "authoritative_bds_owner": "MAIN_CODEX",
  "blockbench_gui_owner": "MAIN_CODEX",
  "shared_files_may_be_edited": false,
  "stop_conditions": [
    "Contract ambiguity beyond permitted latitude",
    "Stable components cannot express a bounded readable pounce",
    "Write-scope collision",
    "Performance caps cannot be met",
    "Third-party contamination"
  ]
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/assignments/forest_attunement.json =====

{
  "batch_id": "forest-wave-1-parallel-batch-1",
  "agent_id": "production-agent-forest-attunement",
  "model": "gpt-5.6-sol",
  "reasoning_effort": "light",
  "feature_id": "forest_attunement",
  "feature_name": "Forest Attunement",
  "wave": "A",
  "base_commit": "PREFLIGHT_COMMIT",
  "branch": "codex/parallel-batch-1/forest-attunement",
  "worktree": "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/forest-attunement",
  "contract": "production/reconstruction-waves/forest-wave-1/forest_attunement/original-production-manifest.json",
  "reservations": "production/batches/forest-wave-1-parallel-batch-1/reservations.json",
  "owned_paths": [
    "production/features/forest-attunement/",
    "prototypes/blockbench/forest_attunement/",
    "tools/build_forest_attunement.py",
    "tests/test_forest_attunement.py"
  ],
  "required_outputs": [
    "Original sigil icon and item",
    "Stable versioned per-player persistence implementation",
    "Migration, corruption, reset, multiplayer, reconnect, and restart tests",
    "Behavior and resource packs",
    "Feature-local deterministic packages",
    "reports/candidate-packet.json"
  ],
  "authoritative_bds_owner": "MAIN_CODEX",
  "blockbench_gui_owner": "MAIN_CODEX",
  "shared_files_may_be_edited": false,
  "stop_conditions": [
    "Stable API cannot safely preserve unknown persistence versions",
    "World or player-state integrity risk",
    "Write-scope collision",
    "Third-party contamination"
  ]
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/assignments/mossback_forager.json =====

{
  "batch_id": "forest-wave-1-parallel-batch-1",
  "agent_id": "production-agent-mossback-forager",
  "model": "gpt-5.6-sol",
  "reasoning_effort": "light",
  "feature_id": "mossback_forager",
  "feature_name": "Mossback Forager",
  "wave": "B",
  "base_commit": "PREFLIGHT_COMMIT",
  "branch": "codex/parallel-batch-1/mossback-forager",
  "worktree": "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/mossback-forager",
  "contract": "production/reconstruction-waves/forest-wave-1/mossback_forager/original-production-manifest.json",
  "reservations": "production/batches/forest-wave-1-parallel-batch-1/reservations.json",
  "owned_paths": [
    "production/features/mossback-forager/",
    "prototypes/blockbench/mossback_forager/",
    "tools/build_mossback_forager.py",
    "tests/test_mossback_forager.py"
  ],
  "required_outputs": [
    "Editable Blockbench source, native geometry, original texture, animations, and controller",
    "Client and behavior entity definitions, interaction and death loot, and disabled-by-default spawn rule",
    "Internal summon, stress, and cleanup functions",
    "Feature-local tests and deterministic packages",
    "reports/candidate-packet.json"
  ],
  "authoritative_bds_owner": "MAIN_CODEX",
  "blockbench_gui_owner": "MAIN_CODEX",
  "shared_files_may_be_edited": false,
  "stop_conditions": [
    "Contract ambiguity beyond permitted latitude",
    "Native interaction cannot enforce contention safety",
    "Write-scope collision",
    "Performance caps cannot be met",
    "Third-party contamination"
  ]
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/assignments/barkguard_charm.json =====

{
  "batch_id": "forest-wave-1-parallel-batch-1",
  "agent_id": "production-agent-barkguard-charm",
  "model": "gpt-5.6-sol",
  "reasoning_effort": "light",
  "feature_id": "barkguard_charm",
  "feature_name": "Barkguard Charm",
  "wave": "B",
  "base_commit": "PREFLIGHT_COMMIT",
  "branch": "codex/parallel-batch-1/barkguard-charm",
  "worktree": "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/barkguard-charm",
  "contract": "production/reconstruction-waves/forest-wave-1/barkguard_charm/original-production-manifest.json",
  "reservations": "production/batches/forest-wave-1-parallel-batch-1/reservations.json",
  "owned_paths": [
    "production/features/barkguard-charm/",
    "prototypes/blockbench/barkguard_charm/",
    "tools/build_barkguard_charm.py",
    "tests/test_barkguard_charm.py"
  ],
  "required_outputs": [
    "Original icon, editable Blockbench attachable source, native geometry, animation, and texture",
    "Item, recipe, attachable, stable damage-event script, and internal grant function",
    "Feature-local multiplayer, durability, cooldown, reconnect, and deterministic-package tests",
    "Behavior and resource packs",
    "reports/candidate-packet.json"
  ],
  "authoritative_bds_owner": "MAIN_CODEX",
  "blockbench_gui_owner": "MAIN_CODEX",
  "shared_files_may_be_edited": false,
  "stop_conditions": [
    "Stable damage events cannot safely identify the offhand item",
    "Durability or duplicate-trigger integrity risk",
    "Write-scope collision",
    "Third-party contamination"
  ]
}


===== DISCLOSED SOURCE: production/reconstruction-waves/forest-wave-1/signal_ruin/original-production-manifest.json =====

{
  "schema_version": "1.0.0",
  "contract_revision": 1,
  "feature_id": "signal_ruin",
  "runtime_namespace": "ccoriginal_cc",
  "display_name": "Signal Ruin",
  "production_lane": "ORIGINAL_BEDROCK_NATIVE",
  "authorship_mode": "ORIGINAL_AUTHORSHIP",
  "java_evidence": "NOT_APPLICABLE",
  "java_fidelity_claimed": false,
  "source_expression_used": false,
  "execution_authorized": true,
  "product_role": "Compact discoverable forest landmark and one-shot cooperative encounter initializer.",
  "identity": {
    "shape_grammar": "An asymmetrical low stone ring around a split cedar-like signal mast, with three original rune plates and one interaction plinth.",
    "palette": "Muted moss green, charcoal stone, pale lichen, and restrained amber activation accents.",
    "player_loop": "Discover, activate once per structure instance, survive a bounded three-wave native-mob encounter, and claim one shared completion reward."
  },
  "explicit_non_goals": [
    "No copied structure layout, branding, lore, or visual expression",
    "No custom dimension, custom GUI, boss, terrain rewrite, or forced progression",
    "No dependency on another unfinished Forest Wave feature",
    "No natural world-generation rule in this pilot; internal placement is command-driven"
  ],
  "dependencies": [
    "Minecraft Bedrock behavior and resource packs",
    "@minecraft/server stable 2.0.0",
    "Repository-local deterministic world and package tooling"
  ],
  "extension_interfaces": [
    "ccoriginal_cc:signal_ruin_completed world event marker for later original progression",
    "A later encounter may replace the native test mobs without changing placement or reward idempotency"
  ],
  "gameplay": {
    "placement": "One original mcstructure with deterministic internal-test placement function and no automatic generation.",
    "activation": "Interact with the structure-local signal anchor entity; server rejects duplicate or concurrent activation.",
    "encounter": "Three scheduled waves over no more than 80 seconds, at most 12 encounter mobs active, using native Minecraft mobs in the pilot.",
    "completion": "When all tagged wave mobs are gone after the final wave, grant the activating party one shared cache and mark the structure complete.",
    "failure": "If no eligible player remains within 32 blocks for 20 seconds, remove tagged encounter mobs and return the instance to ready.",
    "reward": "One loot-table-driven cache per structure instance; duplicate interactions and restart recovery cannot grant it twice."
  },
  "multiplayer": {
    "state_owner": "Canonical signal anchor entity dynamic properties",
    "lock": "First valid activation owns the encounter; later attempts receive status feedback",
    "party": "Eligible players are those within 32 blocks at completion; the physical cache is shared rather than duplicated per player",
    "disconnect": "Ownership is not required after activation; nearby eligible players may finish",
    "late_join": "Observes current phase and may participate without replaying completed waves",
    "server_authority": true
  },
  "persistence": {
    "schema_version": 1,
    "states": [
      "READY",
      "ACTIVE_WAVE_1",
      "ACTIVE_WAVE_2",
      "ACTIVE_WAVE_3",
      "REWARD_READY",
      "COMPLETE"
    ],
    "restart_recovery": "ACTIVE states remove stale tagged mobs and resume from the recorded wave without creating duplicate rewards; COMPLETE remains complete.",
    "corrupt_state": "Unknown state values fail closed to READY only when no reward-issued marker exists; reward-issued always resolves to COMPLETE."
  },
  "cleanup": {
    "entity_cap": 12,
    "scheduled_callback_cap": 4,
    "global_scans_per_tick": 0,
    "cleanup_latency_ticks": 40,
    "path": "Remove structure-instance-tagged encounter mobs and cancel future phase tokens."
  },
  "performance_caps": {
    "structure_dimensions_max": [13, 9, 13],
    "structure_uncompressed_bytes_max": 131072,
    "active_instances_max": 2,
    "mobs_per_instance_max": 12,
    "particles_per_activation_max": 16,
    "animation_controllers_max": 0,
    "persistent_properties_per_instance_max": 8
  },
  "required_tests": [
    "JSON and mcstructure parse",
    "deterministic package rebuild",
    "single activation and three-wave completion",
    "two-player activation contention",
    "four-player shared completion",
    "duplicate reward refusal",
    "disconnect and late join",
    "restart in every active phase",
    "corrupt-state fallback",
    "failure cleanup to zero",
    "two-instance worst-credible load"
  ],
  "permitted_creative_latitude": [
    "Original block palette within vanilla blocks",
    "Exact structure proportions within the cap",
    "Rune texture design, activation particles, encounter pacing, and loot weights"
  ],
  "forbidden_design_changes": [
    "Natural generation",
    "Per-player duplicate rewards",
    "Unbounded entity queries or spawn loops",
    "Experimental APIs",
    "Third-party assets or source-derived structure layouts"
  ],
  "release_status": {
    "internal_test_build": true,
    "marketplace_approved": false,
    "physical_ps4_certified": false,
    "public_release_authorized": false
  }
}


===== DISCLOSED SOURCE: production/reconstruction-waves/forest-wave-1/gloamwing_stalker/original-production-manifest.json =====

{
  "schema_version": "1.0.0",
  "contract_revision": 1,
  "feature_id": "gloamwing_stalker",
  "runtime_namespace": "ccoriginal_cc",
  "display_name": "Gloamwing Stalker",
  "production_lane": "ORIGINAL_BEDROCK_NATIVE",
  "authorship_mode": "ORIGINAL_AUTHORSHIP",
  "java_evidence": "NOT_APPLICABLE",
  "java_fidelity_claimed": false,
  "source_expression_used": false,
  "execution_authorized": true,
  "product_role": "Escalating nocturnal regional threat with a readable stalk-then-pounce rhythm.",
  "identity": {
    "shape_grammar": "A low six-limbed glider with broad leaf-shaped shoulder fins, a lantern-like throat patch, and a short counterbalancing tail.",
    "palette": "Deep indigo, desaturated teal, warm throat amber, and pale claw tips.",
    "player_loop": "Notice the throat flash, create distance or block, survive a short pounce, then counterattack during recovery."
  },
  "explicit_non_goals": [
    "No flight simulation, invisibility, teleportation, wall climbing, custom shader, or boss phases",
    "No copied creature silhouette, texture language, animation timing, sound, name, or lore",
    "No dependency on another Forest Wave feature",
    "No natural spawning until server stress qualification passes"
  ],
  "dependencies": [
    "Minecraft Bedrock behavior and resource packs",
    "Native entity components and animation controllers",
    "Repository-local asset and qualification tooling"
  ],
  "extension_interfaces": [
    "Family tag ccoriginal_cc:gloamwing for later original encounter selection",
    "Loot table may later include an independently authored progression ingredient"
  ],
  "gameplay": {
    "health": 24,
    "movement": "Ground navigation with short native leap/pounce behavior; no script tick loop.",
    "detection_radius_blocks": 16,
    "melee_damage": 4,
    "pounce_cooldown_seconds_min": 4,
    "pounce_cooldown_seconds_max": 7,
    "telegraph": "Throat and fins brighten for at least 0.45 seconds before the pounce state.",
    "recovery": "At least 0.6 seconds of reduced pursuit after landing.",
    "loot": "Bounded original loot table using vanilla materials."
  },
  "multiplayer": {
    "targeting": "Nearest valid survival player selected by native priority and range",
    "retargeting": "Native target ownership may change after damage or target loss",
    "rewards": "One entity loot roll; no per-player script reward",
    "disconnect": "Native target clears and the entity returns to bounded roam",
    "server_authority": true
  },
  "persistence": {
    "custom_records": 0,
    "restart_recovery": "Entity component state is native and may safely return to base stalking state after restart."
  },
  "cleanup": {
    "natural_spawn_enabled": false,
    "stress_function_count": 20,
    "cleanup_function": "Removes only tagged Gloamwing test entities",
    "cleanup_latency_ticks": 20
  },
  "performance_caps": {
    "bones_max": 10,
    "cubes_max": 24,
    "texture_size_max": [64, 64],
    "animation_clips_max": 5,
    "animation_controllers_max": 1,
    "simultaneous_entities_max": 20,
    "pathfinding_search_radius_max": 16,
    "particles_per_pounce_max": 6,
    "scripts_per_tick": 0
  },
  "required_tests": [
    "Blockbench source and native geometry round trip",
    "texture, geometry, animation, controller, client, and behavior reference validation",
    "idle, stalk, telegraph, pounce, landing, damage, and death state checks",
    "two- and four-player target switching",
    "disconnect and restart fallback",
    "1, 10, and 20 entity stress",
    "cleanup to zero",
    "deterministic package rebuild"
  ],
  "permitted_creative_latitude": [
    "Original proportions, fin construction, texture expression, locomotion poses, pounce timing within limits, and vanilla-material loot weights"
  ],
  "forbidden_design_changes": [
    "Natural spawn activation before qualification",
    "Per-tick script scans",
    "Experimental APIs",
    "Persistent player tracking",
    "Third-party or source-derived expression"
  ],
  "release_status": {
    "internal_test_build": true,
    "marketplace_approved": false,
    "physical_ps4_certified": false,
    "public_release_authorized": false
  }
}


===== DISCLOSED SOURCE: production/reconstruction-waves/forest-wave-1/forest_attunement/original-production-manifest.json =====

{
  "schema_version": "1.0.0",
  "contract_revision": 1,
  "feature_id": "forest_attunement",
  "runtime_namespace": "ccoriginal_cc",
  "display_name": "Forest Attunement",
  "production_lane": "ORIGINAL_BEDROCK_NATIVE",
  "authorship_mode": "ORIGINAL_AUTHORSHIP",
  "java_evidence": "NOT_APPLICABLE",
  "java_fidelity_claimed": false,
  "source_expression_used": false,
  "execution_authorized": true,
  "product_role": "Optional per-player persistent unlock proving additive progression, migration, isolation, and recovery.",
  "identity": {
    "player_loop": "Use an independently authored Attunement Sigil once to unlock a subtle forest-trail benefit and receive clear status feedback.",
    "benefit": "While in ordinary forest biomes, an attuned player receives a short low-amplifier Speed effect at a bounded low-frequency interval."
  },
  "explicit_non_goals": [
    "No mandatory campaign gate, custom skill tree, custom GUI, dimension, or world lock",
    "No dependency on Signal Ruin or another unfinished feature",
    "No copied progression system, names, writing, iconography, balance, or state layout",
    "No global per-tick player scan"
  ],
  "dependencies": [
    "Minecraft Bedrock behavior and resource packs",
    "@minecraft/server stable 2.0.0",
    "Repository-local deterministic package and qualification tooling"
  ],
  "extension_interfaces": [
    "Read-only exported helper isForestAttuned(player)",
    "Versioned player property ccoriginal_cc:forest_attunement_v1",
    "Administrative reset function operates on the invoking player only"
  ],
  "gameplay": {
    "acquisition": "Internal-test recipe and grant function produce one Attunement Sigil.",
    "activation": "Use the sigil; consume exactly one only if the player is not already attuned.",
    "duplicate_use": "Already-attuned players keep the item and receive status feedback.",
    "benefit_interval_ticks": 100,
    "benefit": "Speed I for 120 ticks only when the player is in a vanilla forest-tagged biome approximation defined by the implementation contract.",
    "reset": "Operator-only internal test function clears the invoking player's state."
  },
  "multiplayer": {
    "state_owner": "Individual player dynamic property",
    "isolation": "One player's unlock, reset, death, reconnect, or migration cannot alter another player's record",
    "simultaneous_activation": "Each player consumes at most one sigil and receives one state transition",
    "server_authority": true
  },
  "persistence": {
    "schema_version": 1,
    "current_shape": {
      "version": 1,
      "unlocked": true
    },
    "legacy_inputs": [
      "Boolean true",
      "JSON object with unlocked=true and no version"
    ],
    "migration": "Migrate known legacy values once to version 1; reject unknown versions without overwriting them.",
    "corrupt_state": "Fail closed as not attuned, preserve a diagnostic warning, and do not consume an activation item until a valid write succeeds.",
    "reconnect": "Read the player's property on demand; no duplicate global cache."
  },
  "cleanup": {
    "persistent_records_per_player": 1,
    "in_memory_records": 0,
    "scheduled_callbacks_global_max": 1,
    "global_scans_per_tick": 0,
    "unsubscribe_required": false
  },
  "performance_caps": {
    "player_check_interval_ticks": 100,
    "players_modeled_max": 4,
    "dynamic_properties_per_player_max": 1,
    "script_callbacks_per_interval_max": 4,
    "particles_per_activation_max": 8,
    "texture_size_max": [32, 32]
  },
  "required_tests": [
    "Fresh activation and exact item consumption",
    "Duplicate activation refusal",
    "Two- and four-player state isolation",
    "Death, disconnect, reconnect, and restart persistence",
    "Known legacy migrations",
    "Unknown-version and corrupt-state handling",
    "Administrative reset isolation",
    "Bounded interval and no per-tick scan",
    "Deterministic package rebuild"
  ],
  "permitted_creative_latitude": [
    "Original sigil icon, recipe ingredients, feedback wording, bounded particle expression, and exact forest-biome approximation"
  ],
  "forbidden_design_changes": [
    "World-owned unlock",
    "Mandatory progression",
    "Unversioned persistence",
    "Unknown-state overwrite",
    "Per-tick player scanning",
    "Experimental APIs or third-party expression"
  ],
  "release_status": {
    "internal_test_build": true,
    "marketplace_approved": false,
    "physical_ps4_certified": false,
    "public_release_authorized": false
  }
}


===== DISCLOSED SOURCE: production/reconstruction-waves/forest-wave-1/mossback_forager/original-production-manifest.json =====

{
  "schema_version": "1.0.0",
  "contract_revision": 1,
  "feature_id": "mossback_forager",
  "runtime_namespace": "ccoriginal_cc",
  "display_name": "Mossback Forager",
  "production_lane": "ORIGINAL_BEDROCK_NATIVE",
  "authorship_mode": "ORIGINAL_AUTHORSHIP",
  "java_evidence": "NOT_APPLICABLE",
  "java_fidelity_claimed": false,
  "source_expression_used": false,
  "execution_authorized": true,
  "product_role": "Passive regional creature that rewards patient noncombat interaction.",
  "identity": {
    "shape_grammar": "A squat four-legged root-nosed browser carrying three uneven shelf-like moss pads and a curled twig tail.",
    "palette": "Warm umber body, fern green pads, small cream mushrooms, and dark berry nose.",
    "player_loop": "Observe it forage, offer a sweet berry, and receive one bounded vanilla-material forage gift after a cooldown."
  },
  "explicit_non_goals": [
    "No taming, mounting, breeding, inventory, custom GUI, combat role, or permanent owner",
    "No copied creature silhouette, texture language, animation, sound, name, or lore",
    "No dependency on another Forest Wave feature",
    "No natural spawning until server stress qualification passes"
  ],
  "dependencies": [
    "Minecraft Bedrock behavior and resource packs",
    "Native entity components and animation controllers",
    "Repository-local asset and qualification tooling"
  ],
  "extension_interfaces": [
    "Family tag ccoriginal_cc:mossback for later original encounter selection",
    "Loot table may later include independently authored progression ingredients"
  ],
  "gameplay": {
    "health": 18,
    "movement_speed": 0.18,
    "interaction_item": "minecraft:sweet_berries",
    "interaction": "Consume one berry, play a short forage response, and drop exactly one bounded gift if off cooldown.",
    "cooldown_seconds": 45,
    "defense": "Flee the last attacker for a bounded duration; never retaliate.",
    "loot": "Ordinary death loot and interaction gift use separate original loot tables based on vanilla materials."
  },
  "multiplayer": {
    "cooldown_owner": "Entity property shared by all players",
    "contention": "Only the first valid interaction during the ready state consumes an item and emits a gift",
    "disconnect": "No player record persists",
    "late_join": "Observes the entity's current cooldown state",
    "server_authority": true
  },
  "persistence": {
    "entity_properties": 1,
    "restart_recovery": "A cooling entity remains cooling or safely returns ready without duplicating a gift; no player state exists."
  },
  "cleanup": {
    "natural_spawn_enabled": false,
    "stress_function_count": 20,
    "cleanup_function": "Removes only tagged Mossback test entities",
    "cleanup_latency_ticks": 20
  },
  "performance_caps": {
    "bones_max": 9,
    "cubes_max": 22,
    "texture_size_max": [64, 64],
    "animation_clips_max": 5,
    "animation_controllers_max": 1,
    "simultaneous_entities_max": 20,
    "pathfinding_search_radius_max": 12,
    "particles_per_interaction_max": 6,
    "scripts_per_tick": 0
  },
  "required_tests": [
    "Blockbench source and native geometry round trip",
    "texture, geometry, animation, controller, client, and behavior reference validation",
    "idle, walk, forage, interaction, flee, damage, and death state checks",
    "two-player interaction contention",
    "four-player observation and isolation",
    "restart during cooldown",
    "1, 10, and 20 entity stress",
    "cleanup to zero",
    "deterministic package rebuild"
  ],
  "permitted_creative_latitude": [
    "Original proportions, pad construction, texture expression, animation poses, cooldown feedback, and vanilla-material loot weights"
  ],
  "forbidden_design_changes": [
    "Natural spawn activation before qualification",
    "Per-tick script scans",
    "Experimental APIs",
    "Permanent player ownership",
    "Third-party or source-derived expression"
  ],
  "release_status": {
    "internal_test_build": true,
    "marketplace_approved": false,
    "physical_ps4_certified": false,
    "public_release_authorized": false
  }
}


===== DISCLOSED SOURCE: production/reconstruction-waves/forest-wave-1/barkguard_charm/original-production-manifest.json =====

{
  "schema_version": "1.0.0",
  "contract_revision": 1,
  "feature_id": "barkguard_charm",
  "runtime_namespace": "ccoriginal_cc",
  "display_name": "Barkguard Charm",
  "production_lane": "ORIGINAL_BEDROCK_NATIVE",
  "authorship_mode": "ORIGINAL_AUTHORSHIP",
  "java_evidence": "NOT_APPLICABLE",
  "java_fidelity_claimed": false,
  "source_expression_used": false,
  "execution_authorized": true,
  "product_role": "Controller-friendly defensive equipment upgrade with bounded reactive protection.",
  "identity": {
    "shape_grammar": "A small layered wooden medallion with an offset leaf inlay and three visible binding notches.",
    "palette": "Dark bark, honey wood, fern green, and a restrained pale rim.",
    "player_loop": "Equip in the offhand; taking meaningful damage triggers short resistance, consumes durability, and starts a visible cooldown."
  },
  "explicit_non_goals": [
    "No armor replacement, invulnerability, damage reflection, custom slot, custom GUI, aura, or permanent stat",
    "No copied equipment design, icon, model, texture, sound, name, lore, or balance",
    "No dependency on another Forest Wave feature"
  ],
  "dependencies": [
    "Minecraft Bedrock behavior and resource packs",
    "@minecraft/server stable 2.0.0",
    "Repository-local deterministic package and qualification tooling"
  ],
  "extension_interfaces": [
    "Item family ccoriginal_cc:barkguard may accept later independently authored variants",
    "Recipe ingredients may later bind to original Forest Wave drops"
  ],
  "gameplay": {
    "acquisition": "Craft from vanilla wood, leather, and amethyst; internal test function grants one.",
    "slot": "Offhand through ordinary inventory interaction.",
    "trigger": "After receiving at least 2 damage while the charm is in offhand and not cooling down.",
    "effect": "Resistance I for 60 ticks.",
    "cooldown_ticks": 240,
    "durability": 96,
    "durability_cost_per_trigger": 1,
    "break_behavior": "Remove the exhausted charm after the triggering event and emit bounded feedback.",
    "small_damage": "Damage below 2 does not trigger or consume durability."
  },
  "multiplayer": {
    "state_owner": "Individual player's offhand item and item cooldown",
    "isolation": "Triggers, durability, death, reconnect, and cooldown are per player",
    "duplicate_prevention": "One after-damage event may produce at most one effect and one durability increment",
    "server_authority": true
  },
  "persistence": {
    "custom_records": 0,
    "restart_recovery": "Inventory durability persists natively; custom cooldown may safely reset without granting an extra reward or corrupting the item."
  },
  "cleanup": {
    "global_scans_per_tick": 0,
    "persistent_records": 0,
    "scheduled_callbacks_global_max": 0,
    "particles_per_trigger_max": 6
  },
  "performance_caps": {
    "texture_size_max": [32, 32],
    "attachable_cubes_max": 8,
    "animation_clips_max": 2,
    "animation_controllers_max": 1,
    "simultaneous_players_max": 4,
    "callbacks_per_damage_event_max": 1
  },
  "required_tests": [
    "Item, recipe, icon, attachable, animation, and script reference validation",
    "Offhand detection",
    "Damage threshold boundaries",
    "Effect duration and cooldown",
    "Exact durability consumption and break behavior",
    "Two- and four-player isolation",
    "Death, disconnect, reconnect, and restart",
    "No per-tick scan or custom persistence",
    "Deterministic package rebuild"
  ],
  "permitted_creative_latitude": [
    "Original icon, attachable proportions, texture expression, activation animation, recipe shape, and feedback wording"
  ],
  "forbidden_design_changes": [
    "Mainhand-only activation",
    "Permanent passive resistance",
    "Per-tick inventory scans",
    "Experimental APIs",
    "Third-party or source-derived expression"
  ],
  "release_status": {
    "internal_test_build": true,
    "marketplace_approved": false,
    "physical_ps4_certified": false,
    "public_release_authorized": false
  }
}
