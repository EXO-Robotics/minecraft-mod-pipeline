===== DISCLOSED SOURCE: production/features/signal-ruin/reports/candidate-packet.json =====

{
  "schema_version": "1.0.0",
  "label": "INTERNAL TEST BUILD / NOT MARKETPLACE APPROVED / NOT PHYSICAL PS4 CERTIFIED / NOT FOR PUBLIC RELEASE",
  "feature_id": "signal_ruin",
  "base_commit": "0db4c8a5f504106b4a601afa6f7bc225eb697dcd",
  "candidate_commit": "c1f58f18c0658ab5ce77659a52fbbfde402101e8",
  "packet_delivery": "FOLLOW_UP_PACKET_ONLY_COMMIT",
  "branch": "codex/parallel-batch-1/signal-ruin",
  "changed_paths": [
    "production/features/signal-ruin/",
    "prototypes/blockbench/signal_ruin/",
    "tests/test_signal_ruin.py",
    "tools/build_signal_ruin.py"
  ],
  "shared_registration_requests": [
    {
      "owner": "MAIN_CODEX",
      "request": "Register the frozen Signal Ruin behavior/resource packs and qualification scenario without modifying feature-local UUIDs.",
      "behavior_pack_uuid": "556acdce-2ddc-4cbd-b08d-f62681387306",
      "resource_pack_uuid": "f15d006f-c77c-45e5-a6d8-84da52a5db0e"
    },
    {
      "owner": "MAIN_CODEX",
      "request": "Run Blockbench/Creator Tools, stable BDS, desktop, persistence, multiplayer, performance, and physical-console gates against the exact package SHA."
    }
  ],
  "identifiers": [
    "ccoriginal_cc:signal_ruin",
    "ccoriginal_cc:signal_ruin_anchor",
    "ccoriginal_cc:signal_ruin_activation",
    "ccoriginal_cc:signal_ruin_completed",
    "geometry.ccoriginal_cc.signal_ruin_anchor",
    "controller.render.signal_ruin_anchor"
  ],
  "uuids": {
    "behavior_header": "556acdce-2ddc-4cbd-b08d-f62681387306",
    "behavior_data_module": "59c9ac60-a5ba-44a2-8517-c1f7a2fd51e3",
    "behavior_script_module": "45e8f7ad-197e-45ff-99ee-60b6fec7e30d",
    "resource_header": "f15d006f-c77c-45e5-a6d8-84da52a5db0e",
    "resource_module": "214f239c-6fe6-44b1-b69f-38c9b005a3dd"
  },
  "assets_and_packages": [
    {
      "path": "production/features/signal-ruin/dist/signal-ruin-INTERNAL-TEST.mcaddon",
      "sha256": "0b3102c9a57f0e07bf492e5e683e0cf04407994943ad9a7e3dded08153e37180"
    },
    {
      "path": "production/features/signal-ruin/bedrock/behavior_pack/structures/ccoriginal_cc/signal_ruin.mcstructure",
      "sha256": "331fe3449b0335cf08f14d69129c7689e92a287bb0bb27cfb50a6d4ab9df9ded"
    },
    {
      "path": "prototypes/blockbench/signal_ruin/signal_ruin.structure.json",
      "sha256": "0b7c007beb2d0abad51f0c3d21111be6366162ff1428c93f657f3c2544896461"
    },
    {
      "path": "production/features/signal-ruin/bedrock/resource_pack/textures/entity/signal_ruin_anchor.png",
      "sha256": "92e31a20671b9a195f3750584f35707648d9bdf04cfd9a601343a7f2e34cb977"
    }
  ],
  "tests": [
    {
      "command": "<USER_HOME>/Desktop/bedrock-server/minecraft-compiler-baseline/.venv/bin/pytest -q tests/test_signal_ruin.py tests/test_parallel_batch_preflight.py tests/test_resonance_sling.py",
      "result": "PASS",
      "evidence": "17 passed in 0.14s"
    },
    {
      "command": "<USER_HOME>/Desktop/bedrock-server/minecraft-compiler-baseline/.venv/bin/pytest -q tests/test_signal_ruin.py && git status --porcelain=v1 && git diff --exit-code",
      "result": "PASS",
      "evidence": "9 passed after a clean commit; no status or diff output, proving deterministic rebuild preservation."
    },
    {
      "command": "PYTHONPATH=. <USER_HOME>/Desktop/bedrock-server/minecraft-compiler-baseline/.venv/bin/pytest -q",
      "result": "PASS",
      "evidence": "Full repository regression suite exited 0; one pre-existing skip was reported."
    },
    {
      "command": "node --check production/features/signal-ruin/bedrock/behavior_pack/scripts/signal_ruin.js",
      "result": "PASS"
    },
    {
      "command": "git diff --check",
      "result": "PASS"
    }
  ],
  "limitations": [
    "Feature-local tests statically exercise scenario invariants; they are not in-game proof.",
    "No .mcworld is emitted because feature-local production does not own a qualified Bedrock world database.",
    "The anchor model is deterministic JSON authored by the build script; Blockbench GUI/native round-trip is owned by MAIN_CODEX and unexecuted.",
    "Reward command and stable Script API behavior require authoritative BDS qualification."
  ],
  "unexecuted_gates": [
    "Blockbench GUI/native round-trip and visual capture",
    "Creator Tools addon/currentplatform validation",
    "Stable BDS placement, encounter, restart, stress, and cleanup",
    "Bedrock desktop rendering and interaction",
    "Real persistence and multiplayer",
    "Performance profiling",
    "Realm/controller/split-screen/physical PS4",
    "Marketplace partner review"
  ],
  "contamination_status": {
    "status": "CLEAN",
    "third_party_or_java_expression_inspected": false,
    "controlled_chaos_benchmark_inspected": false,
    "resonance_sling_inspected_or_edited": false,
    "inputs": [
      "consumer-safe original production manifest",
      "batch reservations and assignment",
      "generic repository structure tooling search results",
      "Bedrock asset-production skill and Marketplace gate reference"
    ]
  },
  "working_tree_status": "CLEAN_AT_CANDIDATE_COMMIT; PACKET_FILE_ADDED_FOR_FOLLOW_UP_COMMIT",
  "timing_and_effort_metrics": {
    "elapsed_minutes_approximate": 24,
    "requested_reasoning_effort": "light",
    "actual_reasoning_effort": "low",
    "effort_note": "The requested light setting was unavailable; the actual allocation was low."
  },
  "revision": {
    "disposition_addressed": "FINAL_BOUNDED_REVISION",
    "supersedes_candidate_commit": "38d33913b9a7daa18080be1a4d3e4c6f4c7c9550",
    "findings_closed": [
      "Evidence-preserving deterministic rebuild",
      "Two-active-instance hard cap before mutation",
      "Eighty-second encounter cleanup ceiling",
      "Spatially distinct two-instance stress placement",
      "Generated JavaScript and authoring template have no trailing whitespace"
    ]
  },
  "recommendation": "ACCEPT_FOR_MAIN_CODEX_QUALIFICATION_ONLY; DO_NOT PUBLICLY RELEASE OR CLAIM MARKETPLACE OR PHYSICAL PS4 READINESS"
}


===== DISCLOSED SOURCE: production/features/gloamwing-stalker/reports/candidate-packet.json =====

{
  "schema_version": "1.0.0",
  "batch_id": "forest-wave-1-parallel-batch-1",
  "feature_id": "gloamwing_stalker",
  "agent_id": "production-agent-gloamwing-stalker",
  "model": "gpt-5.6-sol",
  "requested_reasoning_effort": "light",
  "actual_reasoning_effort": "low",
  "base_commit": "0db4c8a5f504106b4a601afa6f7bc225eb697dcd",
  "candidate_commit": "e3d049606c52546deeb661e2af02638036422695",
  "candidate_commit_scope": "Implementation and generated artifacts before this packet-only evidence commit",
  "branch": "codex/parallel-batch-1/gloamwing-stalker",
  "worktree": "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/gloamwing-stalker",
  "changed_paths": [
    "production/features/gloamwing-stalker/",
    "prototypes/blockbench/gloamwing_stalker/",
    "tools/build_gloamwing_stalker.py",
    "tests/test_gloamwing_stalker.py"
  ],
  "shared_requests": [],
  "reserved_identifiers": [
    "ccoriginal_cc:gloamwing_stalker",
    "geometry.ccoriginal_cc.gloamwing_stalker",
    "animation.ccoriginal_cc.gloamwing_stalker",
    "controller.animation.ccoriginal_cc.gloamwing_stalker",
    "ccoriginal_cc:gloamwing_test"
  ],
  "uuids": {
    "behavior_header": "e2b0816e-74ed-4457-a8af-a9eb889ecbcb",
    "behavior_data_module": "00f4fc42-7b63-4860-bcd2-06d31724130c",
    "behavior_script_module_unused": "09f04f92-c28a-40a4-935e-8968a7ccb3c3",
    "resource_header": "3a750a45-d232-4a26-aef0-4844df456d74",
    "resource_module": "b503a43d-5d18-4147-8958-bd948d2d73b4"
  },
  "assets": {
    "editable_model": "prototypes/blockbench/gloamwing_stalker/gloamwing_stalker.bbmodel",
    "native_geometry": "prototypes/blockbench/gloamwing_stalker/gloamwing_stalker.geo.json",
    "texture": "prototypes/blockbench/gloamwing_stalker/gloamwing_stalker.png",
    "package": "production/features/gloamwing-stalker/packages/gloamwing_stalker.mcaddon"
  },
  "hashes_sha256": {
    "bbmodel": "9ccbbf3c3726b51ff3595ef263325b195de6f6cff479c8f4b43ad95ceb2c7bf1",
    "geometry": "36b960ec289b18041f5fbb4b2345419ca415b9d5d4b4d53336f6851dec1f1635",
    "texture": "0ef6e1d297940c4edb4091454852f14e74b42a3f9193315ccd4e958785062fb7",
    "mcaddon": "dc2fce6347aef51793563334d4b89ea161c9c20aa104d86bfc159531fdf0abb5"
  },
  "validations": [
    {
      "name": "feature_static_tests",
      "command": "direct invocation of four tests in tests/test_gloamwing_stalker.py",
      "status": "PASSED",
      "result": "6 feature tests passed, including native Blockbench structure/preservation and structural trigger graph/cooldown bounds"
    },
    {
      "name": "authoritative_blockbench_gui_review",
      "status": "PASSED",
      "result": "23 cube elements, 10 bones/groups, 1 embedded texture, 5 animations, 1 controller; native export preserves identifier, bone names, and cube count"
    },
    {
      "name": "batch_preflight_and_resonance_regressions",
      "status": "PASSED",
      "result": "8 tests passed"
    },
    {
      "name": "bundled_geometry_validator",
      "status": "PASSED",
      "result": "1 geometry, 10 bones, 23 cubes, 0 locators"
    },
    {
      "name": "bundled_animated_entity_validator",
      "status": "PASSED",
      "result": "5 clips, 1 controller, 7 animated bones, 5 AI goals"
    },
    {
      "name": "deterministic_rebuild",
      "status": "PASSED",
      "result": "Two consecutive builds produced identical mcaddon SHA-256"
    }
  ],
  "performance": {
    "bones": 10,
    "cubes": 23,
    "texture": [64, 64],
    "animation_clips": 5,
    "animation_controllers": 1,
    "simultaneous_entities": 20,
    "pathfinding_radius": 16,
    "scripts_per_tick": 0,
    "natural_spawn_enabled": false,
    "attack_cycle_reachable": true,
    "pounce_cooldown_seconds": [4.0, 7.0],
    "timer_stacking_prevented_by_exclusive_group_transitions": true,
    "classification": "STATIC_BUDGET_PASS_RUNTIME_UNTESTED"
  },
  "cleanup": {
    "stress_count": 20,
    "selector_is_tag_scoped": true,
    "latency_target_ticks": 20,
    "runtime_result": "UNEXECUTED"
  },
  "limitations": [
    "Native behavior timers encode a readable telegraph and recovery, but combat feel requires desktop runtime testing.",
    "No performance, multiplayer, persistence, Realm, split-screen, or physical-console claim is made."
  ],
  "unexecuted_gates": [
    "Creator Tools validation",
    "Stable BDS summon, 1/10/20 stress, cleanup, and restart",
    "Bedrock desktop controller/combat/pathing",
    "Two- and four-player target switching and disconnect",
    "Persistence and performance measurement",
    "Physical PS4 and Marketplace review"
  ],
  "contamination": {
    "java_source_inspected": false,
    "controlled_chaos_expression_inspected": false,
    "third_party_expression_used": false,
    "production_inputs": [
      "original-production-manifest.json",
      "batch reservations",
      "Blockbench Bedrock asset skill references"
    ]
  },
  "metrics": {
    "owned_files": 24,
    "feature_tests": 6,
    "regression_tests": 8,
    "static_validators": 2,
    "test_framework_note": "pytest was unavailable; the four assertion-based feature tests were invoked directly"
  },
  "revision": 3,
  "revision_history": "production/features/gloamwing-stalker/reports/revision-history.json",
  "review_finding_resolution": "Resolved invalid empty editable wrapper by installing the authoritative GUI-saved native Blockbench project and making the builder validate and preserve it as immutable input. Earlier unreachable attack-cycle finding remains resolved.",
  "recommendation": "ACCEPT_FOR_MAIN_CODEX_GUI_AND_RUNTIME_QUALIFICATION"
}


===== DISCLOSED SOURCE: production/features/forest-attunement/reports/candidate-packet.json =====

{
  "schema_version": "1.1.0",
  "candidate": "forest-attunement-INTERNAL-TEST",
  "feature_id": "forest_attunement",
  "production_lane": "ORIGINAL_BEDROCK_NATIVE",
  "authorship": {
    "model": "gpt-5.6-sol",
    "requested_reasoning_effort": "light",
    "actual_reasoning_effort": "low",
    "source_expression_used": false,
    "java_evidence": "NOT_APPLICABLE",
    "provenance": "Original code, writing, recipe, and procedural 32x32 pixel icon authored solely from the consumer-safe production manifest."
  },
  "git": {
    "base_commit": "0db4c8a5f504106b4a601afa6f7bc225eb697dcd",
    "branch": "codex/parallel-batch-1/forest-attunement",
    "implementation_commit": "983b64988c2f6811e10b4fd429770567d5bb0d9d",
    "note": "The packet cannot embed the hash of the commit containing itself; delivery evidence records the final packet commit."
  },
  "revision_history": [
    {
      "revision": 1,
      "commit": "e8346f826afb7c231bb3dcc9ff71a27f5c78f96a",
      "disposition": "REVISE",
      "summary": "Initial candidate; optional presentation incorrectly shared the rollback catch with committed persistence and inventory mutations."
    },
    {
      "revision": 2,
      "commit": "983b64988c2f6811e10b4fd429770567d5bb0d9d",
      "disposition": "CANDIDATE",
      "summary": "Explicit transaction boundary validates the selected sigil, writes state, consumes once with pre-commit rollback, then runs non-transactional presentation that cannot clear committed state."
    }
  ],
  "owned_paths": [
    "production/features/forest-attunement/",
    "prototypes/blockbench/forest_attunement/",
    "tools/build_forest_attunement.py",
    "tests/test_forest_attunement.py"
  ],
  "identifiers": [
    "ccoriginal_cc:forest_attunement_sigil",
    "ccoriginal_cc:forest_attunement_v1",
    "ccoriginal_cc:forest_attunement_reset",
    "ccoriginal_cc:forest_attunement_test"
  ],
  "uuids": {
    "behavior_header": "43b642d0-a651-45cf-ae20-96a0b853fba5",
    "behavior_data_module": "e7798870-c7e2-4522-87bf-d046b08b442f",
    "behavior_script_module": "2db423eb-5691-4207-bb37-01751206657d",
    "resource_header": "0317044d-9b78-4101-aa2e-cb395af4e948",
    "resource_module": "f00200ff-d682-4f87-9873-2e92abe15060"
  },
  "artifacts": [
    {
      "path": "dist/forest-attunement-behavior-INTERNAL-TEST.mcpack",
      "sha256": "49b714e7df850f4cde762f5633a73374427ad2f18048edf6e6d762917cb3e8d2",
      "bytes": 4244
    },
    {
      "path": "dist/forest-attunement-resource-INTERNAL-TEST.mcpack",
      "sha256": "fcb91eaa6134e86125438a8ceff93425678c5f8caba95720623994f67b596bdb",
      "bytes": 1394
    },
    {
      "path": "dist/forest-attunement-INTERNAL-TEST.mcaddon",
      "sha256": "96ecd6c74b135d4ec55b7602e077efc87dca9e23a3111137729c5a0fb019ae27",
      "bytes": 6096
    }
  ],
  "tests": {
    "command": "python3 -m unittest tests/test_forest_attunement.py -v",
    "result": "PASS",
    "count": 11,
    "adjacent_suites": {
      "parallel_batch_preflight": "4/4 PASS by direct pytest-style function invocation",
      "resonance_sling": "4/4 PASS by direct pytest-style function invocation"
    },
    "coverage": [
      "fresh and duplicate activation with exact consumption",
      "post-consumption presentation exception preserves committed state and duplicate refusal",
      "two- and four-player isolation",
      "death, disconnect, reconnect, and restart model",
      "boolean and unversioned-object migrations",
      "unknown-version and corrupt-state preservation",
      "operator reset isolation",
      "one 100-tick global interval and no per-tick scan",
      "reserved identifiers, UUIDs, stable API dependency, JSON and PNG",
      "deterministic package rebuild and internal labels"
    ]
  },
  "metrics": {
    "texture_pixels": [32, 32],
    "persistent_records_per_player": 1,
    "in_memory_records": 0,
    "scheduled_callbacks_global": 1,
    "interval_ticks": 100,
    "global_scans_per_tick": 0,
    "particles_per_activation": 1,
    "modeled_players_max": 4,
    "transactional_mutations_per_fresh_activation": 2,
    "post_commit_property_clear_paths": 0,
    "presentation_failure_regressions": 1
  },
  "contamination": {
    "third_party_assets_or_expression": "NONE",
    "java_source_or_benchmark_expression": "NONE",
    "shared_files_edited": "NONE"
  },
  "unexecuted_gates": [
    "Creator Tools current addon/currentplatform checks",
    "stable BDS boot/load/restart",
    "Bedrock desktop visual and gameplay check",
    "live multiplayer and persistence",
    "performance profiling",
    "Realm/controller/split-screen/physical PS4",
    "Marketplace review"
  ],
  "limitations": [
    "Biome allowlist is an implementation approximation, not a biome-tag query.",
    "Automated tests model Bedrock state and statically inspect script contracts; they do not execute @minecraft/server.",
    "2D item art does not require or claim a Blockbench geometry round trip.",
    "No PS4 compatibility, Marketplace approval, or public-release claim is made."
  ],
  "recommendation": "Accept as an internal-test candidate for Main Codex-owned Creator Tools and stable BDS gates; do not promote beyond internal test until all listed live gates pass."
}


===== DISCLOSED SOURCE: production/features/mossback-forager/reports/candidate-packet.json =====

{
  "actual_reasoning_effort": "low",
  "assets": {
    "animations": 4,
    "controllers": 1,
    "geometry": "9 bones, 18 cubes, 1 locator",
    "package_sha256": "2decec3b76aa1ec520007bdeaaf0afaaf5761ef53c06230f67cf384801347d64",
    "texture": "64x64 original RGBA PNG"
  },
  "base_commit": "0db4c8a5f504106b4a601afa6f7bc225eb697dcd",
  "blockbench_gui": {
    "counts": {
      "animations": 4,
      "bones": 9,
      "controllers": 1,
      "cubes": 18,
      "elements": 19,
      "locators": 1,
      "textures": 1
    },
    "editable_project_open": "PASS",
    "native_round_trip": "PASS",
    "visual_capture_inventory": "NOT_EXECUTED"
  },
  "branch": "codex/parallel-batch-1/mossback-forager",
  "candidate_commit": "HANDOFF_GIT_HEAD",
  "candidate_commit_convention": "Resolve HANDOFF_GIT_HEAD to the exact commit reported with this frozen packet; a Git commit cannot embed its own object ID.",
  "cleanup": {
    "latency_target_ticks": 20,
    "runtime_zero_count": null,
    "selector_is_tag_scoped": true
  },
  "contamination": {
    "controlled_chaos_expression_inspected": false,
    "java_inspected": false,
    "third_party_assets_used": false
  },
  "display_name": "Mossback Forager",
  "feature_id": "mossback_forager",
  "hash_manifest": "reports/artifact-hashes.json",
  "identifiers": [
    "ccoriginal_cc:mossback_forager",
    "geometry.ccoriginal_cc.mossback_forager",
    "animation.ccoriginal_cc.mossback_forager",
    "controller.animation.ccoriginal_cc.mossback_forager",
    "ccoriginal_cc:mossback_gift",
    "ccoriginal_cc:mossback_test"
  ],
  "limitations": [
    "Native interaction atomicity requires Bedrock runtime confirmation.",
    "Timer persistence/restart behavior requires stable BDS confirmation."
  ],
  "metrics": {
    "animation_clips": 4,
    "animation_controllers": 1,
    "bones": 9,
    "controller_states": 5,
    "cooldown_seconds": 45,
    "cubes": 18,
    "flee_seconds": 5,
    "particles_per_interaction": 0,
    "pathfinding_radius": 8,
    "scripts_per_tick": 0,
    "stress_count": 20,
    "texture": [
      64,
      64
    ]
  },
  "model": "gpt-5.6-sol",
  "owned_paths": [
    "production/features/mossback-forager/",
    "prototypes/blockbench/mossback_forager/",
    "tools/build_mossback_forager.py",
    "tests/test_mossback_forager.py"
  ],
  "performance": {
    "caps_structurally_met": true,
    "runtime_measurements": null,
    "scripts_per_tick": 0,
    "simultaneous_entities_cap": 20
  },
  "recommendation": "Accept as an internal static candidate; hold promotion pending authoritative runtime and platform gates.",
  "requested_reasoning_effort": "light",
  "revision_history": [
    {
      "commit": "2f2b6d6f9960e16470793bb0fe42ec1b1fa64bb4",
      "revision": 1,
      "summary": "Initial complete static vertical slice."
    },
    {
      "commit": "HANDOFF_GIT_HEAD",
      "revision": 2,
      "summary": "Bound flee to five seconds and bound forage playback with cooling-idle controller state."
    },
    {
      "commit": "HANDOFF_GIT_HEAD",
      "revision": 3,
      "summary": "Made candidate metadata independent of the review or integration checkout path."
    },
    {
      "commit": "HANDOFF_GIT_HEAD",
      "revision": 4,
      "summary": "Installed and made reproducible the authoritative GUI-serialized native Blockbench project."
    }
  ],
  "shared_requests": [],
  "tests": {
    "bundled_asset_validators": "UNAVAILABLE_IN_REPOSITORY",
    "deterministic_rebuild": "PASS",
    "json_parse": "PASS",
    "parallel_batch_preflight": "PASS_4_DIRECT_HARNESS",
    "pytest": "UNAVAILABLE_NO_MODULE",
    "python_compileall": "PASS",
    "resonance_regression": "PASS_4_DIRECT_HARNESS",
    "static_feature_tests": "PASS_9_DIRECT_HARNESS"
  },
  "unexecuted_gates": [
    "Blockbench visual capture inventory",
    "Creator Tools",
    "authoritative stable BDS",
    "Bedrock desktop",
    "multiplayer clients",
    "performance profiling",
    "Realm/controller/split-screen",
    "physical PS4",
    "Marketplace submission"
  ],
  "uuids": {
    "behavior_data_module": "73f807d7-55f1-479e-92b7-017aaba56863",
    "behavior_header": "6a67bb25-2953-4be9-9b32-611cf09be04a",
    "resource_header": "698f7eac-f081-49f9-8e82-1e0f362d704d",
    "resource_module": "d25ac1b1-2d66-475c-bc0a-c5f33620fbb2"
  },
  "worktree": "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/mossback-forager"
}


===== DISCLOSED SOURCE: production/features/barkguard-charm/reports/candidate-packet.json =====

{
  "assets": {
    "animation_clips": 2,
    "animation_controllers": 1,
    "cube_count": 7,
    "editable_model": "prototypes/blockbench/barkguard_charm/barkguard_charm.bbmodel",
    "hashes": {
      "production/features/barkguard-charm/bedrock/behavior_pack/functions/barkguard_test.mcfunction": "8065ffe707fb2ec6b5ded7351b26a1a15ea8cffd36b7aac86b63d414ae985114",
      "production/features/barkguard-charm/bedrock/behavior_pack/items/barkguard_charm.json": "05d4f05190bb491d85b3b6d5ba00eb986a4f522250eadd2331e3ba413675b0ed",
      "production/features/barkguard-charm/bedrock/behavior_pack/manifest.json": "3e2c2d41014302c7ca5c4a571d7132650213af0c0cf20b212b7af288c021648f",
      "production/features/barkguard-charm/bedrock/behavior_pack/recipes/barkguard_charm.json": "af490de6c5377c81226f5c277c2f495f8cf860ce39165d930f2aae35b8bf249d",
      "production/features/barkguard-charm/bedrock/behavior_pack/scripts/main.js": "26da5f6f6d8ad3be751c522654574dbbbf18b6519ffc560f6556805a66df9cc9",
      "production/features/barkguard-charm/bedrock/resource_pack/animation_controllers/barkguard_charm.controller.json": "1195955a0a92e27694aef251dbf4ed3f6c374e371dbed152cf39b3289e05f1e4",
      "production/features/barkguard-charm/bedrock/resource_pack/animations/barkguard_charm.animation.json": "6f833538cb8700baff42a01110a8a1daad305b0fcda8146e74f48787bad8bfbc",
      "production/features/barkguard-charm/bedrock/resource_pack/attachables/barkguard_charm.entity.json": "09500285aef19a8699e42be84bdadaf1995d0e6456c8b79b76c7da65c3f806c5",
      "production/features/barkguard-charm/bedrock/resource_pack/manifest.json": "9aca0f7faf6df042d1fa0e75140673c397e134e50e64d095b848966af4ef2e32",
      "production/features/barkguard-charm/bedrock/resource_pack/models/entity/barkguard_charm.geo.json": "09c4cf8c6e6e6a00cb39824b385b8e9d055c5d3aff563469b44be954d132d0c7",
      "production/features/barkguard-charm/bedrock/resource_pack/texts/en_US.lang": "15bb55fdf708549e5bd303b48bbd4786d3acff6c20e36d19e8d5357697914580",
      "production/features/barkguard-charm/bedrock/resource_pack/texts/languages.json": "7dd56a66f8899af87bd2fc690fe0d6387a64c2a28e774287d0774a8b1804f432",
      "production/features/barkguard-charm/bedrock/resource_pack/textures/entity/barkguard_charm.png": "0762f2ee8cb03b2229134afd8b75730d3ee4d58a5209b74bef83fc38fcd82bf3",
      "production/features/barkguard-charm/bedrock/resource_pack/textures/item_texture.json": "52dd43927d5f0aa262b6ffe177ae8ea1d0c123b8ab3946a54e5a6d9d5b77887f",
      "production/features/barkguard-charm/bedrock/resource_pack/textures/items/barkguard_charm.png": "0762f2ee8cb03b2229134afd8b75730d3ee4d58a5209b74bef83fc38fcd82bf3",
      "prototypes/blockbench/barkguard_charm/barkguard_charm.bbmodel": "d2337fef1236533f6fcbb130ec939af83a480c204d1dc12623539e861596134b",
      "prototypes/blockbench/barkguard_charm/barkguard_charm.geo.json": "09c4cf8c6e6e6a00cb39824b385b8e9d055c5d3aff563469b44be954d132d0c7",
      "prototypes/blockbench/barkguard_charm/barkguard_charm.png": "0762f2ee8cb03b2229134afd8b75730d3ee4d58a5209b74bef83fc38fcd82bf3",
      "prototypes/blockbench/barkguard_charm/originality-and-authoring.json": "ee25b9b29bc60fa7e63f42cdcab4f238f855236f4aa4d0219bfb80d23cf8eaf5"
    },
    "native_geometry": "prototypes/blockbench/barkguard_charm/barkguard_charm.geo.json",
    "texture_size": [
      32,
      32
    ]
  },
  "authorship": {
    "lane": "ORIGINAL_BEDROCK_NATIVE",
    "model_reasoning": "Seven-cube layered medallion uses an asymmetric leaf and three protruding binding notches to remain readable at offhand scale.",
    "source_expression_used": false,
    "third_party_materials": []
  },
  "base_commit": "0db4c8a5f504106b4a601afa6f7bc225eb697dcd",
  "branch": "codex/parallel-batch-1/barkguard-charm",
  "cleanup": {
    "disconnect": "delete one ephemeral duplicate guard entry",
    "persistent_cleanup_required": false,
    "restart": "ephemeral cooldown and duplicate guard reset safely; inventory durability remains native"
  },
  "contamination": {
    "controlled_chaos_expression_used": false,
    "java_material_used": false,
    "shared_paths_modified": false
  },
  "feature": "Barkguard Charm",
  "feature_id": "barkguard_charm",
  "identifiers": [
    "ccoriginal_cc:barkguard_charm",
    "geometry.ccoriginal_cc.barkguard_charm",
    "animation.ccoriginal_cc.barkguard_charm",
    "controller.animation.ccoriginal_cc.barkguard_charm",
    "ccoriginal_cc:barkguard_test"
  ],
  "implementation_head_at_build": "24748af8d8f1d2b13bdd6010b875c043a22e3b3a",
  "labels": [
    "INTERNAL TEST BUILD",
    "NOT MARKETPLACE APPROVED",
    "NOT PHYSICAL PS4 CERTIFIED",
    "NOT FOR PUBLIC RELEASE"
  ],
  "limitations": [
    "Activation animation uses a conservative visual query proxy because stable script state is not exported to Molang.",
    "Cooldown may safely reset after restart as explicitly allowed by the contract.",
    "Static and model tests are not runtime evidence."
  ],
  "metrics": {
    "cooldown_ticks": 240,
    "damage_threshold": 2,
    "durability": 96,
    "durability_cost": 1,
    "effect": "resistance I",
    "effect_ticks": 60
  },
  "owned_paths": [
    "production/features/barkguard-charm/",
    "prototypes/blockbench/barkguard_charm/",
    "tools/build_barkguard_charm.py",
    "tests/test_barkguard_charm.py"
  ],
  "package": {
    "bytes": 6349,
    "files": 15,
    "path": "production/features/barkguard-charm/dist/barkguard-charm-INTERNAL-TEST.mcaddon",
    "sha256": "1cc4920ae51dc237a6e9bf633480546ccb744b2dc0c2a979498a71399b0afbbe"
  },
  "performance": {
    "callbacks_per_damage_event_max": 1,
    "global_scans_per_tick": 0,
    "persistent_records": 0,
    "scheduled_callbacks": 0,
    "simultaneous_players_design_cap": 4
  },
  "reasoning_allocation": {
    "actual": "low",
    "honest_note": "Requested allocation was unavailable.",
    "requested": "light"
  },
  "recommendation": "ACCEPT_FOR_MAIN_CODEX_QUALIFICATION",
  "schema_version": "1.0.0",
  "tests": {
    "command": "python3 -m unittest tests.test_barkguard_charm",
    "coverage": [
      "offhand detection",
      "damage threshold",
      "effect/cooldown",
      "exact durability and break",
      "duplicate event path",
      "2/4-player isolation",
      "death/reconnect/restart model",
      "no per-tick scan/custom persistence",
      "deterministic hashes and labels"
    ]
  },
  "unexecuted_gates": [
    "Blockbench GUI native round-trip and visual evidence (MAIN_CODEX owner)",
    "Creator Tools",
    "stable BDS (MAIN_CODEX owner)",
    "Bedrock desktop",
    "multiplayer clients",
    "physical PS4",
    "Marketplace review"
  ],
  "uuids": {
    "behavior_data_module": "1ace8116-c3de-4fa4-b083-c6a3b2c79d39",
    "behavior_header": "2985974d-139b-4142-9c25-ae1aba1f95bf",
    "behavior_script_module": "a8cbf915-0ec4-4c20-95c0-5905667428fd",
    "resource_header": "29eb411e-8ad2-4666-bb55-756efbd4944c",
    "resource_module": "5580dd51-6b31-414b-b15e-0160f5f5b34f"
  },
  "worktree": "<USER_HOME>/Desktop/bedrock-server/.derivedData/worktrees/parallel-batch-1/barkguard-charm"
}


===== DISCLOSED SOURCE: production/features/signal-ruin/reports/artifact-manifest.json =====

{
  "artifacts": [
    {
      "bytes": 1253,
      "path": "production/features/signal-ruin/bedrock/behavior_pack/entities/signal_ruin_anchor.json",
      "sha256": "85f422e54eca695ea08bdca6763e229691ca4102e67462353df795d7b97039c3"
    },
    {
      "bytes": 101,
      "path": "production/features/signal-ruin/bedrock/behavior_pack/functions/ccoriginal_cc/signal_ruin/INTERNAL-TEST-ONLY.txt",
      "sha256": "e7b89713fbdb3ceeddaef396eddcc72bc416bb96c38048d0fff6130a864f3331"
    },
    {
      "bytes": 193,
      "path": "production/features/signal-ruin/bedrock/behavior_pack/functions/ccoriginal_cc/signal_ruin/cleanup.mcfunction",
      "sha256": "6e75750dacf7686d5e81380cb3949c4ffb34c41886922bee186f267281236775"
    },
    {
      "bytes": 203,
      "path": "production/features/signal-ruin/bedrock/behavior_pack/functions/ccoriginal_cc/signal_ruin/place.mcfunction",
      "sha256": "6f4e65e857ca9bd3cd1347e30bb3d693447d3cc7862ff6ac72b96778a9437f1d"
    },
    {
      "bytes": 349,
      "path": "production/features/signal-ruin/bedrock/behavior_pack/functions/ccoriginal_cc/signal_ruin/stress.mcfunction",
      "sha256": "82cedba1ad930784854a9e098b251af961d1a6be6bab3a9ff901e20c133ef3cd"
    },
    {
      "bytes": 811,
      "path": "production/features/signal-ruin/bedrock/behavior_pack/loot_tables/ccoriginal_cc/signal_ruin_cache.json",
      "sha256": "626699ac189bfcbffa7c5d2ef52c2e22b40cff9370d36475980ead82c895ff0f"
    },
    {
      "bytes": 1198,
      "path": "production/features/signal-ruin/bedrock/behavior_pack/manifest.json",
      "sha256": "d3e430c98e9f66a4d06a31217dd1d727dc5b13f7cf4d38124134f53ce1b159f7"
    },
    {
      "bytes": 4221,
      "path": "production/features/signal-ruin/bedrock/behavior_pack/scripts/signal_ruin.js",
      "sha256": "b49c5164dda9e88da899d67af06e9bc4e5af2c0a589dcfe57fb4268390ebbb5b"
    },
    {
      "bytes": 9279,
      "path": "production/features/signal-ruin/bedrock/behavior_pack/structures/ccoriginal_cc/signal_ruin.mcstructure",
      "sha256": "2e03a94a0957b18584e450eddae429cfb58bbe95112ffe2d2fc58141ad34689d"
    },
    {
      "bytes": 482,
      "path": "production/features/signal-ruin/bedrock/resource_pack/entity/signal_ruin_anchor.entity.json",
      "sha256": "c1df016747f406beb5b9c58d00f79e5c84c0955b7ed980bc4ed8fdebe9d74730"
    },
    {
      "bytes": 821,
      "path": "production/features/signal-ruin/bedrock/resource_pack/manifest.json",
      "sha256": "3b00e8d1d52364b49e640bd6949bfaf33ebdfc73c8642953a5c238e123989465"
    },
    {
      "bytes": 1175,
      "path": "production/features/signal-ruin/bedrock/resource_pack/models/entity/signal_ruin_anchor.geo.json",
      "sha256": "42e93e298466af2793e5dcea811ab957572265a7e42dd3386dc21f89d95f4cea"
    },
    {
      "bytes": 291,
      "path": "production/features/signal-ruin/bedrock/resource_pack/render_controllers/signal_ruin.render_controllers.json",
      "sha256": "2dcbfdbd2a5f6b33bde0c232e78138d48cb9150574f871898215e8839790d722"
    },
    {
      "bytes": 222,
      "path": "production/features/signal-ruin/bedrock/resource_pack/texts/en_US.lang",
      "sha256": "6c96a5e7a4e743eef3bde214ff3d250e6b663607f8ef57d96cd04e0535632553"
    },
    {
      "bytes": 14,
      "path": "production/features/signal-ruin/bedrock/resource_pack/texts/languages.json",
      "sha256": "7dd56a66f8899af87bd2fc690fe0d6387a64c2a28e774287d0774a8b1804f432"
    },
    {
      "bytes": 96,
      "path": "production/features/signal-ruin/bedrock/resource_pack/textures/entity/signal_ruin_anchor.png",
      "sha256": "92e31a20671b9a195f3750584f35707648d9bdf04cfd9a601343a7f2e34cb977"
    },
    {
      "bytes": 351,
      "path": "production/features/signal-ruin/dist/README-INTERNAL-TEST.txt",
      "sha256": "0f68a34ef6b30ac8206a22f00365d053a1191c67bb2a530072dbd3eb828f2d9b"
    },
    {
      "bytes": 7771,
      "path": "production/features/signal-ruin/dist/signal-ruin-INTERNAL-TEST.mcaddon",
      "sha256": "b9890cf0037c8d76ee616d05631233b431bc0c26b827563b3488290677a8b6e9"
    },
    {
      "bytes": 469,
      "path": "production/features/signal-ruin/tests/scenarios.json",
      "sha256": "f831b2cfe50f26f126bbef0329f43b639188837c368018b5da729d744d3164c3"
    },
    {
      "bytes": 470,
      "path": "prototypes/blockbench/signal_ruin/originality-and-authoring.json",
      "sha256": "ff1e03cb8d559f39c4c87f1d91c160e73ec574f1f280bb37236d7f7956a7f7bf"
    },
    {
      "bytes": 5509,
      "path": "prototypes/blockbench/signal_ruin/signal_ruin.structure.json",
      "sha256": "0b7c007beb2d0abad51f0c3d21111be6366162ff1428c93f657f3c2544896461"
    }
  ],
  "label": "INTERNAL TEST BUILD / NOT MARKETPLACE APPROVED / NOT PHYSICAL PS4 CERTIFIED / NOT FOR PUBLIC RELEASE",
  "mcworld": "NOT_EMITTED_NO_QUALIFIED_WORLD_DATABASE",
  "package_sha256": {
    "mcaddon": "b9890cf0037c8d76ee616d05631233b431bc0c26b827563b3488290677a8b6e9"
  }
}


===== DISCLOSED SOURCE: production/features/signal-ruin/reports/revision-history.json =====

{
  "schema_version": "1.0.0",
  "label": "INTERNAL TEST BUILD / NOT MARKETPLACE APPROVED / NOT PHYSICAL PS4 CERTIFIED / NOT FOR PUBLIC RELEASE",
  "feature_id": "signal_ruin",
  "revisions": [
    {
      "candidate_commit": "fb33af831cbc147199b119f7efc8cf7011e61da8",
      "packet_commit": "701314d73f6598de57821d42762efd9d5b56480a",
      "disposition": "REVISE",
      "findings": [
        "Build removed candidate/review evidence",
        "Active-instance cap was not enforced",
        "Encounter had no hard 80-second ceiling",
        "Stress placements overlapped"
      ]
    },
    {
      "candidate_commit": "38d33913b9a7daa18080be1a4d3e4c6f4c7c9550",
      "packet_delivery": "FOLLOW_UP_PACKET_ONLY_COMMIT",
      "disposition": "READY_FOR_MAIN_CODEX_REVIEW",
      "closures": [
        "Build replaces only generated BP/RP/dist and preserves report/prototype evidence",
        "Third activation is rejected before any anchor mutation when two instances are active",
        "Each active encounter resets at the 80-second interval boundary",
        "Stress function places instances 24 blocks apart"
      ]
    },
    {
      "candidate_commit": "c1f58f18c0658ab5ce77659a52fbbfde402101e8",
      "packet_delivery": "FOLLOW_UP_PACKET_ONLY_COMMIT",
      "disposition": "READY_FOR_MAIN_CODEX_REVIEW",
      "closures": [
        "Removed trailing whitespace from the JavaScript build template",
        "Regenerated the runtime script and deterministic package",
        "Exact base-to-candidate git diff --check passes"
      ]
    }
  ]
}


===== DISCLOSED SOURCE: production/features/gloamwing-stalker/reports/build-report.json =====

{
  "attack_cycle": {
    "cooldown_seconds": [
      4.0,
      7.0
    ],
    "initial_trigger": "minecraft:entity_spawned -> ready environment sensor",
    "pounce_seconds": 0.4,
    "recovery_seconds": 0.7,
    "telegraph_seconds": 0.5,
    "timer_stacking_prevented": true
  },
  "counts": {
    "attack_state_groups": 5,
    "bones": 10,
    "clips": 5,
    "controllers": 1,
    "cubes": 23,
    "stress_entities": 20
  },
  "editable_source": {
    "blockbench_native": true,
    "builder_policy": "IMMUTABLE_INPUT_NOT_REGENERATED",
    "counts": {
      "animation_controllers": 1,
      "animations": 5,
      "elements": 23,
      "outliner": 1,
      "textures": 1
    },
    "validation": "PASSED"
  },
  "hashes": {
    "bbmodel": "9ccbbf3c3726b51ff3595ef263325b195de6f6cff479c8f4b43ad95ceb2c7bf1",
    "geometry": "36b960ec289b18041f5fbb4b2345419ca415b9d5d4b4d53336f6851dec1f1635",
    "mcaddon": "045e7d41e5a02ea2b6112db9657bb38305a884d4cf76d916fe46510aafacba98",
    "texture": "0ef6e1d297940c4edb4091454852f14e74b42a3f9193315ccd4e958785062fb7"
  },
  "labels": {
    "marketplace_approved": false,
    "ps4_verified": false
  },
  "status": "STATIC_CANDIDATE"
}


===== DISCLOSED SOURCE: production/features/gloamwing-stalker/reports/revision-history.json =====

{
  "revisions": [
    {
      "disposition": "REVISE",
      "finding": "Telegraph entry event was unreachable and no 4-7 second cooldown existed.",
      "implementation_commit": "e86d4ed1f99676a5bf8660a9bd2864f3aa0d46a9",
      "package_sha256": "385de156c907dcc9f225103d7262c21bf1bea791e2510ed60d5cc5104060035e",
      "revision": 1
    },
    {
      "changes": [
        "Added spawn-armed target sensor",
        "Made all attack-cycle groups mutually exclusive through explicit remove/add transitions",
        "Added randomized non-looping 4-7 second cooldown before re-arm",
        "Added structural event and component-group reachability test"
      ],
      "disposition": "READY_FOR_MAIN_CODEX_REVIEW",
      "package_sha256": "045e7d41e5a02ea2b6112db9657bb38305a884d4cf76d916fe46510aafacba98",
      "revision": 2
    },
    {
      "changes": [
        "Installed authoritative Blockbench GUI-saved native project",
        "Builder now validates and preserves editable source as immutable input",
        "Added structural checks for real elements, outliner, embedded texture, animations, and controller"
      ],
      "disposition": "READY_FOR_MAIN_CODEX_REVIEW",
      "revision": 3
    }
  ],
  "schema_version": "1.0.0"
}


===== DISCLOSED SOURCE: production/features/forest-attunement/reports/artifact-manifest.json =====

{
  "schema_version": "1.0.0",
  "label": "INTERNAL-TEST",
  "artifacts": [
    {
      "path": "dist/forest-attunement-behavior-INTERNAL-TEST.mcpack",
      "sha256": "ab52f568cf7126b41091d0aa116b08d6d7edaab55d7467a092d2cf2f04c617c6",
      "bytes": 4276
    },
    {
      "path": "dist/forest-attunement-resource-INTERNAL-TEST.mcpack",
      "sha256": "fcb91eaa6134e86125438a8ceff93425678c5f8caba95720623994f67b596bdb",
      "bytes": 1394
    },
    {
      "path": "dist/forest-attunement-INTERNAL-TEST.mcaddon",
      "sha256": "1803664fb6dfced97ec4252fb3c8ad398f4bd9995e6bbea44dc8205ce37945c7",
      "bytes": 6128
    }
  ]
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/candidate-review.json =====

{
  "schema_version": "1.0.0",
  "batch_id": "forest-wave-1-parallel-batch-1",
  "review_owner": "MAIN_CODEX",
  "status": "LOCAL_ACCEPTANCE_COMPLETE_EXTERNAL_RED_TEAM_PENDING",
  "candidates": [
    {
      "feature_id": "signal_ruin",
      "agent_head": "7d7907ecaa5c4be60a3ca0ad2e2351aa2a0631a0",
      "final_package_sha256": "b9890cf0037c8d76ee616d05631233b431bc0c26b827563b3488290677a8b6e9",
      "main_codex_revision_rounds": 2,
      "main_review_finding_count": 7,
      "accepted_repairs": [
        "Preserved review evidence across deterministic rebuilds",
        "Applied a two-instance cap before mutation",
        "Applied an 80-second cleanup ceiling and spatially distinct stress pair",
        "Corrected damage_sensor deals_damage to the supported string enum",
        "Corrected little-endian NBT root and list-of-compound encoding"
      ],
      "disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    },
    {
      "feature_id": "gloamwing_stalker",
      "agent_head": "0dbbb4a",
      "final_package_sha256": "045e7d41e5a02ea2b6112db9657bb38305a884d4cf76d916fe46510aafacba98",
      "main_codex_revision_rounds": 3,
      "main_review_finding_count": 3,
      "accepted_repairs": [
        "Made telegraph, pounce, recovery, and 4-7 second cooldown reachable",
        "Replaced the empty editable wrapper with a native Blockbench project",
        "Replaced invalid summon-event tagging with explicit bounded summon and tag commands"
      ],
      "disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    },
    {
      "feature_id": "forest_attunement",
      "agent_head": "9c7b8a65be389cc21d384fb90711d9f823f8164a",
      "final_package_sha256": "1803664fb6dfced97ec4252fb3c8ad398f4bd9995e6bbea44dc8205ce37945c7",
      "main_codex_revision_rounds": 2,
      "main_review_finding_count": 4,
      "accepted_repairs": [
        "Separated committed persistence and inventory consumption from optional presentation",
        "Added the required modern recipe unlock",
        "Made item-use and player iteration callbacks defensive against incomplete diagnostic payloads"
      ],
      "disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    },
    {
      "feature_id": "mossback_forager",
      "agent_head": "481041c90e09783ab928addf32c8d7cb647d20d0",
      "final_package_sha256": "2decec3b76aa1ec520007bdeaaf0afaaf5761ef53c06230f67cf384801347d64",
      "main_codex_revision_rounds": 3,
      "main_review_finding_count": 3,
      "accepted_repairs": [
        "Bound flee and forage state durations",
        "Replaced the empty editable wrapper with a native Blockbench project",
        "Moved gift loot to the supported interact spawn_items field"
      ],
      "disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    },
    {
      "feature_id": "barkguard_charm",
      "agent_head": "4c2dd216ae7dde60b719c4579a5ecbb4e0de2879",
      "final_package_sha256": "1cc4920ae51dc237a6e9bf633480546ccb744b2dc0c2a979498a71399b0afbbe",
      "main_codex_revision_rounds": 2,
      "main_review_finding_count": 2,
      "accepted_repairs": [
        "Removed sub-unit Box UV dimensions and revalidated the native project",
        "Made the damage callback defensive against incomplete diagnostic payloads"
      ],
      "disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    }
  ],
  "shared_disposition": {
    "no_child_self_accepted_or_integrated": true,
    "grok_finding_count": null,
    "grok_status": "PENDING_EXPLICIT_EXTERNAL_DISCLOSURE_APPROVAL",
    "creator_tools_status": "NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE",
    "physical_ps4_status": "PENDING"
  }
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/workload-measurement.json =====

{
  "schema_version": "1.0.0",
  "batch_id": "forest-wave-1-parallel-batch-1",
  "measurement_policy": {
    "token_usage": "The collaboration runtime did not expose per-agent token usage; null is recorded instead of an estimate.",
    "elapsed_time": "Only Signal Ruin supplied an approximate wall-clock value. Git commit span is retained as a proxy, not relabeled as wall-clock time.",
    "qualification_duration": "Authoritative qualification was shared across the assembled batch: 81.503 Stable seconds plus 194.815 Preview seconds."
  },
  "features": [
    {
      "feature_id": "signal_ruin",
      "elapsed_wall_clock_minutes": 24,
      "commit_span_minutes_proxy": 10.25,
      "agent_token_usage": null,
      "changed_file_count": 28,
      "structured_lines_changed": 1569,
      "editable_asset_count": 1,
      "generated_runtime_artifact_count": 18,
      "automated_test_count": 9,
      "qualification_duration_seconds_shared": 276.318,
      "main_codex_revision_count": 2,
      "main_review_finding_count": 7,
      "red_team_finding_count": null,
      "blocker_count": 0,
      "final_disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    },
    {
      "feature_id": "gloamwing_stalker",
      "elapsed_wall_clock_minutes": null,
      "commit_span_minutes_proxy": 32.133,
      "agent_token_usage": null,
      "changed_file_count": 25,
      "structured_lines_changed": 2414,
      "editable_asset_count": 1,
      "generated_runtime_artifact_count": 15,
      "automated_test_count": 6,
      "qualification_duration_seconds_shared": 276.318,
      "main_codex_revision_count": 3,
      "main_review_finding_count": 3,
      "red_team_finding_count": null,
      "blocker_count": 0,
      "final_disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    },
    {
      "feature_id": "forest_attunement",
      "elapsed_wall_clock_minutes": null,
      "commit_span_minutes_proxy": 8.883,
      "agent_token_usage": null,
      "changed_file_count": 24,
      "structured_lines_changed": 789,
      "editable_asset_count": 1,
      "generated_runtime_artifact_count": 15,
      "automated_test_count": 11,
      "qualification_duration_seconds_shared": 276.318,
      "main_codex_revision_count": 2,
      "main_review_finding_count": 4,
      "red_team_finding_count": null,
      "blocker_count": 0,
      "final_disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    },
    {
      "feature_id": "mossback_forager",
      "elapsed_wall_clock_minutes": null,
      "commit_span_minutes_proxy": 28.167,
      "agent_token_usage": null,
      "changed_file_count": 29,
      "structured_lines_changed": 2396,
      "editable_asset_count": 1,
      "generated_runtime_artifact_count": 20,
      "automated_test_count": 9,
      "qualification_duration_seconds_shared": 276.318,
      "main_codex_revision_count": 3,
      "main_review_finding_count": 3,
      "red_team_finding_count": null,
      "blocker_count": 0,
      "final_disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    },
    {
      "feature_id": "barkguard_charm",
      "elapsed_wall_clock_minutes": null,
      "commit_span_minutes_proxy": 25.917,
      "agent_token_usage": null,
      "changed_file_count": 23,
      "structured_lines_changed": 1830,
      "editable_asset_count": 1,
      "generated_runtime_artifact_count": 16,
      "automated_test_count": 8,
      "qualification_duration_seconds_shared": 276.318,
      "main_codex_revision_count": 2,
      "main_review_finding_count": 2,
      "red_team_finding_count": null,
      "blocker_count": 0,
      "final_disposition": "ACCEPT_LOCALLY_PENDING_GROK"
    }
  ],
  "batch_blockers": [
    "External Grok repository-content disclosure requires explicit user approval."
  ]
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/blockbench-round-trip.json =====

{
  "schema_version": "1.0.0",
  "owner": "MAIN_CODEX",
  "application": {
    "name": "Blockbench",
    "version": "5.1.5",
    "access": "SERIALIZED_GUI"
  },
  "assets": [
    {
      "feature_id": "gloamwing_stalker",
      "source": "prototypes/blockbench/gloamwing_stalker/gloamwing_stalker.bbmodel",
      "sha256": "9ccbbf3c3726b51ff3595ef263325b195de6f6cff479c8f4b43ad95ceb2c7bf1",
      "elements": 23,
      "bones": 10,
      "textures": 1,
      "animations": 5,
      "controllers": 1,
      "round_trip_identifier_preserved": true,
      "round_trip_bone_names_preserved": true,
      "round_trip_cube_count_preserved": true,
      "warnings": 0,
      "status": "PASSED"
    },
    {
      "feature_id": "mossback_forager",
      "source": "prototypes/blockbench/mossback_forager/mossback_forager.bbmodel",
      "sha256": "685b5803ff93f84bb6b16a0a340eea5e0306db9221e0f921ff7c778a7587f1e5",
      "elements": 19,
      "cubes": 18,
      "locators": 1,
      "bones": 9,
      "textures": 1,
      "animations": 4,
      "controllers": 1,
      "round_trip_identifier_preserved": true,
      "round_trip_bone_names_preserved": true,
      "round_trip_cube_count_preserved": true,
      "round_trip_locator_count_preserved": true,
      "warnings": 0,
      "status": "PASSED"
    },
    {
      "feature_id": "barkguard_charm",
      "source": "prototypes/blockbench/barkguard_charm/barkguard_charm.bbmodel",
      "sha256": "d2337fef1236533f6fcbb130ec939af83a480c204d1dc12623539e861596134b",
      "elements": 7,
      "bones": 4,
      "textures": 1,
      "animations": 2,
      "controllers": 1,
      "round_trip_identifier_preserved": true,
      "round_trip_bone_names_preserved": true,
      "round_trip_cube_count_preserved": true,
      "box_uv_subunit_warnings": 0,
      "status": "PASSED"
    }
  ],
  "non_blockbench_assets": [
    {
      "feature_id": "signal_ruin",
      "reason": "Editable deterministic block-composition JSON, not a geometry project."
    },
    {
      "feature_id": "forest_attunement",
      "reason": "Two-dimensional item icon; no geometry round trip required."
    }
  ]
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/creator-tools.json =====

{
  "schema_version": "1.0.0",
  "status": "NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE",
  "passed": false,
  "reason": "Minecraft Creator Tools was not available in the execution environment.",
  "claims": {
    "creator_tools_validated": false,
    "client_rendering_verified": false,
    "controller_verified": false,
    "physical_ps4_verified": false
  }
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/integration-artifact-manifest.json =====

{
  "artifacts": {
    "mcaddon": {
      "bytes": 48712,
      "files": 98,
      "path": "production/batches/forest-wave-1-parallel-batch-1/dist/forest-wave-1-parallel-batch-1-INTERNAL-TEST.mcaddon",
      "sha256": "6a6d4ed26b936bfd4a717047c5f94e6cba27ecdf8275f4a7205ad4619af406d5"
    },
    "mcworld": {
      "behavior_pack_count": 6,
      "bytes": 57717,
      "pack_hash": "2b1f3af1dcbd55f508170e7a668167a35a06c0a4b804ea3f20f898cdb62af891",
      "path": "production/batches/forest-wave-1-parallel-batch-1/dist/forest-wave-1-parallel-batch-1-INTERNAL-TEST.mcworld",
      "resource_pack_count": 6,
      "sha256": "dc110378a76a3f9be30bb6e9a3f730aab1cd5bb038715f15d89bb53c2bc3f667"
    }
  },
  "batch_id": "forest-wave-1-parallel-batch-1",
  "claims": {
    "bds_qualified": false,
    "creator_tools_executed": false,
    "marketplace_approved": false,
    "physical_ps4_verified": false,
    "realm_deployed": false
  },
  "features": [
    {
      "behavior": {
        "name": "Resonance Sling INTERNAL TEST BP",
        "uuid": "61e0bbf4-0051-4bb0-a5bb-19e1cd68db0f",
        "version": [
          1,
          0,
          0
        ]
      },
      "feature_id": "resonance_sling",
      "resource": {
        "name": "Resonance Sling INTERNAL TEST RP",
        "uuid": "ae5d1908-8fbe-4282-83a4-8509606aceda",
        "version": [
          1,
          0,
          0
        ]
      }
    },
    {
      "behavior": {
        "name": "Signal Ruin - INTERNAL TEST BUILD / NOT MARKETPLACE APPROVED / NOT PHYSICAL PS4 CERTIFIED / NOT FOR PUBLIC RELEASE",
        "uuid": "556acdce-2ddc-4cbd-b08d-f62681387306",
        "version": [
          0,
          1,
          0
        ]
      },
      "feature_id": "signal_ruin",
      "resource": {
        "name": "Signal Ruin Resources - INTERNAL TEST BUILD / NOT MARKETPLACE APPROVED / NOT PHYSICAL PS4 CERTIFIED / NOT FOR PUBLIC RELEASE",
        "uuid": "f15d006f-c77c-45e5-a6d8-84da52a5db0e",
        "version": [
          0,
          1,
          0
        ]
      }
    },
    {
      "behavior": {
        "name": "Gloamwing Stalker BP (Internal)",
        "uuid": "e2b0816e-74ed-4457-a8af-a9eb889ecbcb",
        "version": [
          1,
          0,
          0
        ]
      },
      "feature_id": "gloamwing_stalker",
      "resource": {
        "name": "Gloamwing Stalker RP (Internal)",
        "uuid": "3a750a45-d232-4a26-aef0-4844df456d74",
        "version": [
          1,
          0,
          0
        ]
      }
    },
    {
      "behavior": {
        "name": "Forest Attunement BP [INTERNAL TEST]",
        "uuid": "43b642d0-a651-45cf-ae20-96a0b853fba5",
        "version": [
          1,
          0,
          0
        ]
      },
      "feature_id": "forest_attunement",
      "resource": {
        "name": "Forest Attunement RP [INTERNAL TEST]",
        "uuid": "0317044d-9b78-4101-aa2e-cb395af4e948",
        "version": [
          1,
          0,
          0
        ]
      }
    },
    {
      "behavior": {
        "name": "Mossback Forager INTERNAL TEST BP",
        "uuid": "6a67bb25-2953-4be9-9b32-611cf09be04a",
        "version": [
          1,
          0,
          0
        ]
      },
      "feature_id": "mossback_forager",
      "resource": {
        "name": "Mossback Forager INTERNAL TEST RP",
        "uuid": "698f7eac-f081-49f9-8e82-1e0f362d704d",
        "version": [
          1,
          0,
          0
        ]
      }
    },
    {
      "behavior": {
        "name": "Barkguard Charm INTERNAL TEST BP",
        "uuid": "2985974d-139b-4142-9c25-ae1aba1f95bf",
        "version": [
          1,
          0,
          0
        ]
      },
      "feature_id": "barkguard_charm",
      "resource": {
        "name": "Barkguard Charm INTERNAL TEST RP",
        "uuid": "29eb411e-8ad2-4666-bb55-756efbd4944c",
        "version": [
          1,
          0,
          0
        ]
      }
    }
  ],
  "labels": [
    "INTERNAL TEST BUILD",
    "NOT MARKETPLACE APPROVED",
    "NOT PHYSICAL PS4 CERTIFIED",
    "NOT FOR PUBLIC RELEASE"
  ],
  "preview_diagnostic": {
    "bytes": 62333,
    "diagnostic_pack_uuid": "f510b35e-62c1-44d7-804e-10d742b80fd5",
    "never_ship": true,
    "path": "production/batches/forest-wave-1-parallel-batch-1/runtime/preview-simulated-player.mcworld",
    "preview_only": true,
    "production_pack_module_overrides": [
      {
        "from": "2.0.0",
        "manifest": "behavior_packs/Barkguard_Charm_INTERNAL_TEST_BP-2985974d/manifest.json",
        "module": "@minecraft/server",
        "to": "2.10.0"
      },
      {
        "from": "2.0.0",
        "manifest": "behavior_packs/Forest_Attunement_BP__INTERNAL_TEST-43b642d0/manifest.json",
        "module": "@minecraft/server",
        "to": "2.10.0"
      },
      {
        "from": "2.0.0",
        "manifest": "behavior_packs/Resonance_Sling_INTERNAL_TEST_BP-61e0bbf4/manifest.json",
        "module": "@minecraft/server",
        "to": "2.10.0"
      },
      {
        "from": "2.0.0",
        "manifest": "behavior_packs/Signal_Ruin_-_INTERNAL_TEST_BUILD___NOT_MARKETPLACE_APPROVED___NOT_PHYSICAL_PS4_CERTIFIED___NOT_FOR_PUBLIC_RELEASE-556acdce/manifest.json",
        "module": "@minecraft/server",
        "to": "2.10.0"
      }
    ],
    "sha256": "171bdbe71f6ab0d9ba840ffac47bdf324777736c26e393571ae4910d794e6879"
  },
  "protected_resonance_sling": {
    "mcaddon_sha256": "0bbd00a285cb8c7ccab49cf9a246f2ad95386eeaa239631a1c6463c0c84855ec",
    "mcworld_sha256": "061501b67b0886296ad2765f1b7c5246efbe38d64b9494303a05b9ee81a58d9a",
    "unchanged": true
  },
  "schema_version": "1.0.0",
  "status": "INTEGRATION_ARTIFACT_BUILT"
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/bds-qualification-summary.json =====

{
  "batch_id": "forest-wave-1-parallel-batch-1",
  "channels": {
    "preview": {
      "artifact_sha256": "171bdbe71f6ab0d9ba840ffac47bdf324777736c26e393571ae4910d794e6879",
      "bds_version": "1.26.50.20",
      "passed": true,
      "status": "BDS_DIAGNOSTIC_BOOT_VERIFIED"
    },
    "stable": {
      "artifact_sha256": "dc110378a76a3f9be30bb6e9a3f730aab1cd5bb038715f15d89bb53c2bc3f667",
      "bds_version": "1.26.33.2",
      "passed": true,
      "status": "BDS_DIAGNOSTIC_BOOT_VERIFIED"
    }
  },
  "claims": {
    "creator_tools_executed": false,
    "marketplace_approved": false,
    "physical_ps4_verified": false
  },
  "passed": true,
  "schema_version": "1.0.0"
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/stable-bds-result.json =====

{
  "artifact": {
    "path": "<WORKSPACE>/production/batches/forest-wave-1-parallel-batch-1/dist/forest-wave-1-parallel-batch-1-INTERNAL-TEST.mcworld",
    "sha256": "dc110378a76a3f9be30bb6e9a3f730aab1cd5bb038715f15d89bb53c2bc3f667"
  },
  "checks": [
    {
      "check_id": "stable-barkguard-cycle-1",
      "classification": "bds_restart_diagnostic",
      "expect_output": "[barkguard-charm] stable_api=2.0.0",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "stable-resonance-cycle-1",
      "classification": "bds_restart_diagnostic",
      "expect_output": "[resonance-sling] script runtime initialized stable_api=2.0.0",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "stable-barkguard-cycle-2",
      "classification": "bds_restart_diagnostic",
      "expect_output": "[barkguard-charm] stable_api=2.0.0",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "stable-resonance-cycle-2",
      "classification": "bds_restart_diagnostic",
      "expect_output": "[resonance-sling] script runtime initialized stable_api=2.0.0",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "stable-barkguard-cycle-3",
      "classification": "bds_restart_diagnostic",
      "expect_output": "[barkguard-charm] stable_api=2.0.0",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "stable-resonance-cycle-3",
      "classification": "bds_restart_diagnostic",
      "expect_output": "[resonance-sling] script runtime initialized stable_api=2.0.0",
      "matched": true,
      "status": "PASSED"
    }
  ],
  "claims": {
    "adapter_integration_verified": false,
    "bds_boot_verified": true,
    "console_verified": false,
    "diagnostic_state_persistence_verified": false,
    "gameplay_verified": false,
    "marketplace_approval_implied": false,
    "migrated_state_restart_verified": false,
    "multiplayer_verified": false,
    "nonempty_state_migration_verified": false,
    "persistence_verified": false,
    "simulated_player_integration_verified": false
  },
  "execution": {
    "cycles": [
      {
        "analysis": {
          "bedrock_build_id": "47564860",
          "bedrock_version": "1.26.33.2",
          "booted": true,
          "clean": true,
          "critical_lines": [],
          "line_count": 54,
          "migrated_lock_values": [],
          "migrated_state_records": [],
          "persistent_boot_values": [],
          "script_initialized": true
        },
        "console_probes": [],
        "container_exit_code": 0,
        "cycle": 1,
        "elapsed_seconds": 27.365,
        "log_probes": [
          {
            "check_id": "stable-barkguard-cycle-1",
            "classification": "bds_restart_diagnostic",
            "expect_output": "[barkguard-charm] stable_api=2.0.0",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "stable-resonance-cycle-1",
            "classification": "bds_restart_diagnostic",
            "expect_output": "[resonance-sling] script runtime initialized stable_api=2.0.0",
            "matched": true,
            "status": "PASSED"
          }
        ],
        "passed": true,
        "stop_exit_code": 0,
        "timed_out": false,
        "timeout_seconds": 180
      },
      {
        "analysis": {
          "bedrock_build_id": "47564860",
          "bedrock_version": "1.26.33.2",
          "booted": true,
          "clean": true,
          "critical_lines": [],
          "line_count": 53,
          "migrated_lock_values": [],
          "migrated_state_records": [],
          "persistent_boot_values": [],
          "script_initialized": true
        },
        "console_probes": [],
        "container_exit_code": 0,
        "cycle": 2,
        "elapsed_seconds": 27.099,
        "log_probes": [
          {
            "check_id": "stable-barkguard-cycle-2",
            "classification": "bds_restart_diagnostic",
            "expect_output": "[barkguard-charm] stable_api=2.0.0",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "stable-resonance-cycle-2",
            "classification": "bds_restart_diagnostic",
            "expect_output": "[resonance-sling] script runtime initialized stable_api=2.0.0",
            "matched": true,
            "status": "PASSED"
          }
        ],
        "passed": true,
        "stop_exit_code": 0,
        "timed_out": false,
        "timeout_seconds": 180
      },
      {
        "analysis": {
          "bedrock_build_id": "47564860",
          "bedrock_version": "1.26.33.2",
          "booted": true,
          "clean": true,
          "critical_lines": [],
          "line_count": 53,
          "migrated_lock_values": [],
          "migrated_state_records": [],
          "persistent_boot_values": [],
          "script_initialized": true
        },
        "console_probes": [],
        "container_exit_code": 0,
        "cycle": 3,
        "elapsed_seconds": 27.038,
        "log_probes": [
          {
            "check_id": "stable-barkguard-cycle-3",
            "classification": "bds_restart_diagnostic",
            "expect_output": "[barkguard-charm] stable_api=2.0.0",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "stable-resonance-cycle-3",
            "classification": "bds_restart_diagnostic",
            "expect_output": "[resonance-sling] script runtime initialized stable_api=2.0.0",
            "matched": true,
            "status": "PASSED"
          }
        ],
        "passed": true,
        "stop_exit_code": 0,
        "timed_out": false,
        "timeout_seconds": 180
      }
    ],
    "elapsed_seconds": 81.503,
    "restart_count": 3
  },
  "log": {
    "bedrock_build_id": "47564860",
    "bedrock_version": "1.26.33.2",
    "booted": true,
    "clean": true,
    "critical_lines": [],
    "line_count": 163,
    "migrated_lock_values": [],
    "migrated_state_records": [],
    "path": "<WORKSPACE>/production/batches/forest-wave-1-parallel-batch-1/runtime/stable-bds/content.log",
    "persistent_boot_values": [],
    "script_initialized": true,
    "sha256": "f8f589db76922b27096b7e50fc69775e0b228cd342f85a6ad14133b0031483ee"
  },
  "passed": true,
  "runtime": {
    "adapter": "docker-bds",
    "image": "itzg/minecraft-bedrock-server@sha256:12c7047cc149bd517d6dbc2339163cf62a4f1044c10e759c45c8b387e9784e39",
    "level_name": "Forest Wave 1 Parallel Batch 1 INTERNAL TEST",
    "network": "bridge",
    "preview_channel": false,
    "published_ports": false,
    "requested_bds_version": "1.26.33.2"
  },
  "schema_version": "1.0.0",
  "status": "BDS_DIAGNOSTIC_BOOT_VERIFIED",
  "upgrade": null
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/preview-simulated-player-result.json =====

{
  "artifact": {
    "path": "<WORKSPACE>/production/batches/forest-wave-1-parallel-batch-1/runtime/preview-simulated-player.mcworld",
    "sha256": "171bdbe71f6ab0d9ba840ffac47bdf324777736c26e393571ae4910d794e6879"
  },
  "checks": [
    {
      "check_id": "batch-ticking-area-1",
      "classification": "adapter_integration",
      "command": "tickingarea add circle 8 64 8 2 forest_batch_q true",
      "expect_output": "Added ticking area",
      "matched": true,
      "sent": true,
      "status": "PASSED"
    },
    {
      "check_id": "batch-arm-1",
      "classification": "adapter_integration",
      "command": "setblock 8 64 8 gold_block",
      "expect_output": "Block placed",
      "matched": true,
      "sent": true,
      "status": "PASSED"
    },
    {
      "check_id": "batch-arm-2",
      "classification": "adapter_integration",
      "command": "setblock 8 64 8 gold_block",
      "expect_output": "Block placed",
      "matched": true,
      "sent": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-barkguard-damage-event-harness-limit-observed",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] barkguard_damage_event_harness_limit_observed=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-bounded-custom-entity-load",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] bounded_custom_entity_load=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-checkpoint-written",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] checkpoint_written=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-custom-items-registered",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] custom_items_registered=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-deterministic-cleanup",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] deterministic_cleanup=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-forest-inventory-isolation",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] forest_inventory_isolation=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-forest-item-use-harness-limit-observed",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] forest_item_use_harness_limit_observed=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-forest-state-roundtrip",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] forest_state_roundtrip=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-four-players-created",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] four_players_created=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-gloamwing-stress-spawn",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] gloamwing_stress_spawn=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-mossback-stress-spawn",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] mossback_stress_spawn=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-player-state-isolation",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] player_state_isolation=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-resonance-global-cap",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] resonance_global_cap=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-signal-interaction-event-harness-limit-observed",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] signal_interaction_event_harness_limit_observed=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-signal-ruin-instances-spawn",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] signal_ruin_instances_spawn=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-worst-credible-combined-load",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] worst_credible_combined_load=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-restart-restart-checkpoint-recovered",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] restart_checkpoint_recovered=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-restart-restart-cleanup-preserved",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] restart_cleanup_preserved=passed",
      "matched": true,
      "status": "PASSED"
    },
    {
      "check_id": "preview-restart-restart-simulated-player-identity-limit-observed",
      "classification": "simulated_player_integration",
      "expect_output": "[forest-batch-1:preview] restart_simulated_player_identity_limit_observed=passed",
      "matched": true,
      "status": "PASSED"
    }
  ],
  "claims": {
    "adapter_integration_verified": true,
    "bds_boot_verified": true,
    "console_verified": false,
    "diagnostic_state_persistence_verified": false,
    "gameplay_verified": false,
    "marketplace_approval_implied": false,
    "migrated_state_restart_verified": false,
    "multiplayer_verified": false,
    "nonempty_state_migration_verified": false,
    "persistence_verified": false,
    "simulated_player_integration_verified": true
  },
  "execution": {
    "cycles": [
      {
        "analysis": {
          "bedrock_build_id": "47971866",
          "bedrock_version": "1.26.50.20",
          "booted": true,
          "clean": true,
          "critical_lines": [],
          "line_count": 82,
          "migrated_lock_values": [],
          "migrated_state_records": [],
          "persistent_boot_values": [],
          "script_initialized": true
        },
        "console_probes": [
          {
            "check_id": "batch-ticking-area-1",
            "classification": "adapter_integration",
            "command": "tickingarea add circle 8 64 8 2 forest_batch_q true",
            "expect_output": "Added ticking area",
            "matched": true,
            "sent": true,
            "status": "PASSED"
          },
          {
            "check_id": "batch-arm-1",
            "classification": "adapter_integration",
            "command": "setblock 8 64 8 gold_block",
            "expect_output": "Block placed",
            "matched": true,
            "sent": true,
            "status": "PASSED"
          }
        ],
        "container_exit_code": 0,
        "cycle": 1,
        "elapsed_seconds": 97.372,
        "log_probes": [
          {
            "check_id": "preview-barkguard-damage-event-harness-limit-observed",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] barkguard_damage_event_harness_limit_observed=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-bounded-custom-entity-load",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] bounded_custom_entity_load=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-checkpoint-written",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] checkpoint_written=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-custom-items-registered",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] custom_items_registered=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-deterministic-cleanup",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] deterministic_cleanup=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-forest-inventory-isolation",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] forest_inventory_isolation=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-forest-item-use-harness-limit-observed",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] forest_item_use_harness_limit_observed=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-forest-state-roundtrip",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] forest_state_roundtrip=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-four-players-created",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] four_players_created=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-gloamwing-stress-spawn",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] gloamwing_stress_spawn=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-mossback-stress-spawn",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] mossback_stress_spawn=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-player-state-isolation",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] player_state_isolation=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-resonance-global-cap",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] resonance_global_cap=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-signal-interaction-event-harness-limit-observed",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] signal_interaction_event_harness_limit_observed=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-signal-ruin-instances-spawn",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] signal_ruin_instances_spawn=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-worst-credible-combined-load",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] worst_credible_combined_load=passed",
            "matched": true,
            "status": "PASSED"
          }
        ],
        "passed": true,
        "stop_exit_code": 0,
        "timed_out": false,
        "timeout_seconds": 240
      },
      {
        "analysis": {
          "bedrock_build_id": "47971866",
          "bedrock_version": "1.26.50.20",
          "booted": true,
          "clean": true,
          "critical_lines": [],
          "line_count": 63,
          "migrated_lock_values": [],
          "migrated_state_records": [],
          "persistent_boot_values": [],
          "script_initialized": true
        },
        "console_probes": [
          {
            "check_id": "batch-arm-2",
            "classification": "adapter_integration",
            "command": "setblock 8 64 8 gold_block",
            "expect_output": "Block placed",
            "matched": true,
            "sent": true,
            "status": "PASSED"
          }
        ],
        "container_exit_code": 0,
        "cycle": 2,
        "elapsed_seconds": 97.441,
        "log_probes": [
          {
            "check_id": "preview-restart-restart-checkpoint-recovered",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] restart_checkpoint_recovered=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-restart-restart-cleanup-preserved",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] restart_cleanup_preserved=passed",
            "matched": true,
            "status": "PASSED"
          },
          {
            "check_id": "preview-restart-restart-simulated-player-identity-limit-observed",
            "classification": "simulated_player_integration",
            "expect_output": "[forest-batch-1:preview] restart_simulated_player_identity_limit_observed=passed",
            "matched": true,
            "status": "PASSED"
          }
        ],
        "passed": true,
        "stop_exit_code": 0,
        "timed_out": false,
        "timeout_seconds": 240
      }
    ],
    "elapsed_seconds": 194.815,
    "restart_count": 2
  },
  "log": {
    "bedrock_build_id": "47971866",
    "bedrock_version": "1.26.50.20",
    "booted": true,
    "clean": true,
    "critical_lines": [],
    "line_count": 147,
    "migrated_lock_values": [],
    "migrated_state_records": [],
    "path": "<WORKSPACE>/production/batches/forest-wave-1-parallel-batch-1/runtime/preview-simulated-player/content.log",
    "persistent_boot_values": [],
    "script_initialized": true,
    "sha256": "eb3a9d42ec3a08f4eb97cdcc96e38a61a37b1ab75f7114bd5c6e20a25ba46daf"
  },
  "passed": true,
  "runtime": {
    "adapter": "docker-bds",
    "image": "itzg/minecraft-bedrock-server@sha256:12c7047cc149bd517d6dbc2339163cf62a4f1044c10e759c45c8b387e9784e39",
    "level_name": "Forest Wave 1 Parallel Batch 1 INTERNAL TEST",
    "network": "bridge",
    "preview_channel": true,
    "published_ports": false,
    "requested_bds_version": "1.26.50.20"
  },
  "schema_version": "1.0.0",
  "status": "BDS_DIAGNOSTIC_BOOT_VERIFIED",
  "upgrade": null
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/checkpoint-manifest.json =====

{
  "schema_version": "1.0.0",
  "batch_id": "forest-wave-1-parallel-batch-1",
  "status": "BLOCKED_PENDING_REQUIRED_EXTERNAL_GROK_REVIEW",
  "final_accepted": false,
  "artifacts": {
    "mcaddon_sha256": "6a6d4ed26b936bfd4a717047c5f94e6cba27ecdf8275f4a7205ad4619af406d5",
    "mcworld_sha256": "dc110378a76a3f9be30bb6e9a3f730aab1cd5bb038715f15d89bb53c2bc3f667",
    "preview_diagnostic_mcworld_sha256": "171bdbe71f6ab0d9ba840ffac47bdf324777736c26e393571ae4910d794e6879"
  },
  "gates": {
    "static_repository_suite": "PASSED_363_TESTS_1_SKIPPED_107_SUBTESTS",
    "blockbench_authoritative_round_trip": "PASSED",
    "stable_bds_three_restart": "PASSED",
    "preview_bds_two_cycle_simulated_player": "PASSED_WITH_DOCUMENTED_HARNESS_LIMITS",
    "creator_tools": "NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE",
    "external_grok_red_team": "PENDING_EXPLICIT_USER_APPROVAL",
    "bedrock_desktop_client": "PENDING",
    "live_multiplayer_clients": "PENDING",
    "realm": "NOT_DEPLOYED",
    "physical_ps4": "PENDING",
    "marketplace": "NOT_SUBMITTED"
  },
  "protected_resonance_sling": {
    "mcaddon_sha256": "0bbd00a285cb8c7ccab49cf9a246f2ad95386eeaa239631a1c6463c0c84855ec",
    "mcworld_sha256": "061501b67b0886296ad2765f1b7c5246efbe38d64b9494303a05b9ee81a58d9a",
    "unchanged": true
  },
  "external_actions": {
    "push": false,
    "tag": false,
    "release": false,
    "realm_deployment": false,
    "marketplace_submission": false,
    "physical_ps4_claim": false
  }
}


===== DISCLOSED SOURCE: production/batches/forest-wave-1-parallel-batch-1/reports/qualification-report.md =====

# Forest Wave 1 Parallel Batch 1 — Local Qualification

Status: `BLOCKED_PENDING_REQUIRED_EXTERNAL_GROK_REVIEW`

Five isolated `gpt-5.6-sol` production agents were launched across two maximum-concurrency waves, with up to three production agents active simultaneously. The requested child effort label `light` was not supported by the runtime; the closest available level, `low`, was used and recorded. No child was escalated, accepted its own work, or integrated its own candidate.

Main Codex independently reviewed every candidate, serialized the authoritative Blockbench GUI inspection, repaired generator-level defects, assembled six Behavior/Resource Pack pairs including the protected Resonance Sling, and ran the authoritative servers.

## Evidence

- Repository suite: 363 passed, 1 skipped, and 107 subtests passed.
- Stable BDS 1.26.33.2: three clean restart cycles, 81.503 seconds total.
- Preview BDS 1.26.50.20: two clean cycles, 194.815 seconds total.
- Preview load: four SimulatedPlayers, 20 Gloamwings, 20 Mossbacks, two Signal Ruin anchors, 16 capped Resonance projectiles, and 24 ambient entities.
- Cleanup: all diagnostic custom entities, encounter entities, projectiles, and ambient proxies removed.
- Restart: world checkpoint and zero-stale-entity state recovered.
- Blockbench 5.1.5: Gloamwing, Mossback, and Barkguard native projects opened and round-tripped with matching identifiers, bone names, cube counts, and zero remaining warnings.

## SimulatedPlayer boundaries

Preview BDS verified creation, four-player isolation, bounded load, projectile caps, cleanup, and world restart state. It also reproduced documented GameTest limitations:

- Simulated item use was accepted but did not deliver a normal production item-use event payload.
- Simulated damage was accepted but did not deliver a normal production damage event payload.
- Simulated entity interaction was accepted but did not deliver the production interaction event.
- Recreating a SimulatedPlayer after server restart did not recover the prior player identity record.

These are recorded as harness limitations, not as gameplay passes. Real item activation, damage activation, interaction activation, player reconnect persistence, desktop rendering, controller behavior, split screen, Realm behavior, and physical PS4 performance remain pending.

## Remaining gate

The production prompt requires one external Grok adversarial review. That review has not run because it would disclose bounded project content to an external service, and explicit user approval is required. Final acceptance and integration into the main branch remain blocked until that review runs and Main Codex dispositions every finding.

Creator Tools was unavailable and is recorded as `NOT_EXECUTED_ENVIRONMENT_UNAVAILABLE`.

No push, tag, release, Realm deployment, Marketplace submission, or physical PS4 claim occurred.
