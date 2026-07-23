from __future__ import annotations

from typing import Any, Callable

from mccompiler.project.store import ProjectError, ProjectStore

from . import analysis_ops, blockbench_ops, distillation_ops, gameplay_distillation_ops, generation_ops, intent_ops, planning_ops, project_ops, query_ops, reconstruction_ops, reporting_ops, safe_edit_ops, validation_ops
from .envelope import OperationError, failure, success


Handler = Callable[..., tuple[Any, ProjectStore, list[dict[str, Any]]]]


REQUIRED_OPERATION_CATALOG: dict[str, tuple[str, ...]] = {
    "project": (
        "create_conversion_project", "open_conversion_project", "get_project_status",
        "list_unresolved_work", "list_blocking_failures", "get_next_recommended_task",
    ),
    "analysis": (
        "scan_mod", "scan_modpack", "list_mods", "inspect_mod", "list_content",
        "inspect_item", "inspect_block", "inspect_entity", "inspect_recipe", "inspect_structure",
        "inspect_worldgen", "inspect_behavior", "inspect_state", "inspect_asset", "inspect_mixin",
        "inspect_coremod", "inspect_packet", "inspect_gui", "trace_dependency", "trace_callers",
        "trace_callees", "show_evidence", "compare_source_and_jar",
    ),
    "intent": (
        "extract_behavior_intent", "propose_behavior_intent", "accept_behavior_intent",
        "edit_behavior_intent", "reject_behavior_intent", "list_ambiguous_behaviors",
        "list_unsupported_operations",
    ),
    "planning": (
        "compare_bedrock_strategies", "plan_feature", "set_strategy", "accept_approximation",
        "reject_approximation", "record_manual_redesign", "select_pattern", "apply_override",
        "estimate_fidelity", "estimate_performance",
    ),
    "generation": (
        "author_blockbench_asset",
        "generate_item", "generate_block", "generate_entity", "generate_projectile",
        "generate_recipe", "generate_loot", "generate_structure", "generate_spawn_rules",
        "generate_animation", "generate_form", "generate_script_scaffold", "generate_pack",
        "generate_world", "package_mcaddon",
    ),
    "validation": (
        "validate_ir", "validate_api_symbols", "validate_marketplace_profile", "validate_rights",
        "validate_static", "validate_scripts", "validate_assets", "validate_performance",
        "install_test_pack", "start_test_runtime", "run_behavior_test", "run_multiplayer_test",
        "verify_persistence", "inspect_content_log", "compare_expected_behavior",
        "generate_conversion_report",
    ),
    "distillation": (
        "analyze_modpack_identity", "cluster_gameplay_systems", "score_feature_value",
        "estimate_conversion_effort", "estimate_console_cost", "estimate_pattern_reuse",
        "identify_progression_dependencies", "select_quarter_scope", "explain_selection",
        "generate_conversion_roadmap", "record_distillation_adjustment",
    ),
    "gameplay_distillation": (
        "create_rights_strategy", "register_rights_material", "inspect_rights_material",
        "build_gameplay_intent", "validate_gameplay_intent", "export_clean_room_contract",
        "screen_product_similarity", "build_experience_graph",
        "calculate_experience_coverage", "plan_production_wave",
        "validate_production_wave", "show_production_wave",
    ),
    "reconstruction": (
        "prepare_reconstruction_wave",
    ),
}


def _not_available(name: str, category: str, reason: str) -> Handler:
    def handler(store: ProjectStore, parameters: dict[str, Any], expected_revision: int | None = None) -> tuple[Any, ProjectStore, list[dict[str, Any]]]:
        raise OperationError(
            "NOT_AVAILABLE",
            f"{name} is declared but not available from current project artifacts",
            details={
                "status": "NOT_AVAILABLE", "operation": name, "category": category,
                "blocker": reason, "project_revision": store.revision,
                "mutated": False, "success_implied": False,
            },
        )
    return handler


class OperationRegistry:
    def __init__(self) -> None:
        self.handlers: dict[str, Handler] = {
            "create_conversion_project": project_ops.create_conversion_project,
            "open_conversion_project": project_ops.open_conversion_project,
            "get_project_status": project_ops.get_project_status,
            "list_unresolved_work": project_ops.list_unresolved_work,
            "list_blocking_failures": project_ops.list_blocking_failures,
            "get_next_recommended_task": project_ops.get_next_recommended_task,
            "scan_mod": analysis_ops.scan_mod,
            "scan_modpack": analysis_ops.scan_mod,
            "list_mods": analysis_ops.list_mods,
            "inspect_mod": analysis_ops.inspect_mod,
            "list_content": analysis_ops.list_content,
            "inspect_item": analysis_ops.inspect_item,
            "inspect_block": analysis_ops.inspect_block,
            "inspect_entity": analysis_ops.inspect_entity,
            "inspect_recipe": analysis_ops.inspect_recipe,
            "inspect_structure": analysis_ops.inspect_structure,
            "inspect_worldgen": analysis_ops.inspect_worldgen,
            "inspect_behavior": analysis_ops.inspect_behavior,
            "inspect_state": analysis_ops.inspect_state,
            "inspect_asset": analysis_ops.inspect_asset,
            "inspect_mixin": analysis_ops.inspect_mixin,
            "inspect_coremod": analysis_ops.inspect_coremod,
            "inspect_packet": analysis_ops.inspect_packet,
            "inspect_gui": analysis_ops.inspect_gui,
            "trace_dependency": analysis_ops.trace_dependency,
            "show_evidence": analysis_ops.show_evidence,
            "extract_behavior_intent": analysis_ops.inspect_behavior,
            "propose_behavior_intent": intent_ops.propose_behavior_intent,
            "accept_behavior_intent": intent_ops.accept_behavior_intent,
            "edit_behavior_intent": intent_ops.edit_behavior_intent,
            "reject_behavior_intent": intent_ops.reject_behavior_intent,
            "list_ambiguous_behaviors": analysis_ops.list_ambiguous_behaviors,
            "list_unsupported_operations": analysis_ops.list_unsupported_operations,
            "compare_bedrock_strategies": planning_ops.compare_bedrock_strategies,
            "plan_feature": planning_ops.plan_feature,
            "set_strategy": planning_ops.set_strategy,
            "accept_approximation": planning_ops.accept_approximation,
            "reject_approximation": planning_ops.reject_approximation,
            "record_manual_redesign": planning_ops.record_manual_redesign,
            "apply_override": planning_ops.apply_override,
            "select_pattern": query_ops.select_pattern,
            "estimate_fidelity": query_ops.estimate_fidelity,
            "estimate_performance": query_ops.estimate_performance,
            "trace_callers": query_ops.trace_callers,
            "trace_callees": query_ops.trace_callees,
            "compare_source_and_jar": query_ops.compare_source_and_jar,
            "generate_item": generation_ops.generate_item,
            "author_blockbench_asset": blockbench_ops.author_blockbench_asset,
            "generate_block": generation_ops.generate_block,
            "generate_entity": generation_ops.generate_entity,
            "generate_projectile": generation_ops.generate_projectile,
            "generate_recipe": generation_ops.generate_recipe,
            "generate_loot": generation_ops.generate_loot,
            "generate_structure": generation_ops.generate_structure,
            "generate_spawn_rules": generation_ops.generate_spawn_rules,
            "generate_animation": generation_ops.generate_animation,
            "generate_form": generation_ops.generate_form,
            "generate_script_scaffold": generation_ops.generate_script_scaffold,
            "generate_pack": generation_ops.generate_pack,
            "generate_world": generation_ops.generate_world,
            "package_mcaddon": generation_ops.package_mcaddon,
            "validate_ir": reporting_ops.validate_ir,
            "validate_api_symbols": validation_ops.validate_api_symbols,
            "validate_marketplace_profile": validation_ops.validate_marketplace_profile,
            "validate_rights": validation_ops.validate_rights,
            "validate_static": validation_ops.validate_static,
            "validate_scripts": validation_ops.validate_scripts,
            "validate_assets": validation_ops.validate_assets,
            "validate_performance": validation_ops.validate_performance,
            "install_test_pack": validation_ops.install_test_pack,
            "start_test_runtime": validation_ops.start_test_runtime,
            "run_behavior_test": validation_ops.run_behavior_test,
            "run_multiplayer_test": validation_ops.run_multiplayer_test,
            "verify_persistence": validation_ops.verify_persistence,
            "inspect_content_log": validation_ops.inspect_content_log,
            "compare_expected_behavior": validation_ops.compare_expected_behavior,
            "generate_conversion_report": reporting_ops.generate_conversion_report,
            "analyze_modpack_identity": distillation_ops.analyze_modpack_identity,
            "cluster_gameplay_systems": distillation_ops.cluster_gameplay_systems,
            "score_feature_value": distillation_ops.score_feature_value,
            "estimate_conversion_effort": distillation_ops.estimate_conversion_effort,
            "estimate_console_cost": distillation_ops.estimate_console_cost,
            "estimate_pattern_reuse": distillation_ops.estimate_pattern_reuse,
            "identify_progression_dependencies": distillation_ops.identify_progression_dependencies,
            "select_quarter_scope": distillation_ops.select_quarter_scope,
            "explain_selection": distillation_ops.explain_selection,
            "generate_conversion_roadmap": distillation_ops.generate_conversion_roadmap,
            "record_distillation_adjustment": distillation_ops.record_distillation_adjustment,
            "create_rights_strategy": gameplay_distillation_ops.create_rights_strategy,
            "register_rights_material": gameplay_distillation_ops.register_rights_material,
            "inspect_rights_material": gameplay_distillation_ops.inspect_rights_material,
            "build_gameplay_intent": gameplay_distillation_ops.build_gameplay_intent,
            "validate_gameplay_intent": gameplay_distillation_ops.validate_gameplay_intent,
            "export_clean_room_contract": gameplay_distillation_ops.export_clean_room_contract,
            "screen_product_similarity": gameplay_distillation_ops.screen_product_similarity,
            "build_experience_graph": gameplay_distillation_ops.build_experience_graph,
            "calculate_experience_coverage": gameplay_distillation_ops.calculate_experience_coverage,
            "plan_production_wave": gameplay_distillation_ops.plan_production_wave,
            "validate_production_wave": gameplay_distillation_ops.validate_production_wave,
            "show_production_wave": gameplay_distillation_ops.show_production_wave,
            "prepare_reconstruction_wave": reconstruction_ops.prepare_reconstruction_wave,
        }
        unavailable_reasons = {
            "trace_callers": "No persisted call graph exists in analysis/source-index/calls.json",
            "trace_callees": "No persisted call graph exists in analysis/source-index/calls.json",
            "compare_source_and_jar": "Current project artifacts do not retain paired source/JAR semantic snapshots",
            "propose_behavior_intent": "Proposal persistence and review handlers are not implemented",
            "accept_behavior_intent": "Intent decision lifecycle is not implemented",
            "edit_behavior_intent": "Intent decision lifecycle is not implemented",
            "reject_behavior_intent": "Intent decision lifecycle is not implemented",
            "select_pattern": "Pattern selection is owned by the planner and is not exposed as a safe project mutation",
            "estimate_fidelity": "No evidence-calibrated feature fidelity estimator is persisted",
            "estimate_performance": "No measured feature performance evidence is persisted",
            "validate_api_symbols": "Symbol validation is available only inside the existing validator, which is outside this operation milestone",
            "validate_marketplace_profile": "Marketplace profile validation is not exposed as a project-artifact operation",
            "validate_rights": "Human rights review requires the dedicated rights subsystem and attributable review evidence",
            "validate_static": "Aggregate generated-output validation requires a generated build artifact",
            "validate_scripts": "Script validation requires a generated build artifact",
            "validate_assets": "Asset validation requires a generated build artifact",
            "validate_performance": "No measured runtime performance artifact exists",
            "install_test_pack": "Installing packs mutates an external Minecraft installation and has no authorized runtime adapter",
            "start_test_runtime": "No managed Bedrock runtime adapter is configured",
            "run_behavior_test": "No managed runtime or authenticated execution evidence channel is configured",
            "run_multiplayer_test": "No managed multiplayer runtime or clients are configured",
            "verify_persistence": "No runtime restart/rejoin evidence is available",
            "inspect_content_log": "No runtime content log has been ingested into the project",
            "compare_expected_behavior": "No runtime evidence and expected-behavior result pair is persisted",
        }
        generation_reason = "Generation remains in the existing monolithic backend and cannot be safely invoked as a focused project operation within this milestone"
        for category, names in REQUIRED_OPERATION_CATALOG.items():
            for name in names:
                if name not in self.handlers:
                    reason = unavailable_reasons.get(name, generation_reason if category == "generation" else "Required supporting artifact or subsystem is not implemented")
                    self.handlers[name] = _not_available(name, category, reason)

        # Backward-compatible aliases are intentionally outside the required catalog.
        self.handlers.update({
            "list_unresolved": project_ops.list_unresolved_work,
            "list_blocking": project_ops.list_blocking_failures,
            "get_next_task": project_ops.get_next_recommended_task,
            "write_custom_implementation": safe_edit_ops.write_custom_implementation,
            "register_custom_behavior_handler": safe_edit_ops.register_custom_behavior_handler,
            "add_project_pattern": safe_edit_ops.add_project_pattern,
            "patch_ir_with_provenance": safe_edit_ops.patch_ir_with_provenance,
            "add_rights_evidence": safe_edit_ops.add_rights_evidence,
            "resolve_mapping": safe_edit_ops.resolve_mapping,
            "validate_creator_tools": validation_ops.validate_creator_tools,
            "evaluate_marketplace_candidate": validation_ops.evaluate_marketplace_candidate,
        })

    def catalog(self) -> dict[str, dict[str, Any]]:
        available = {name for name, handler in self.handlers.items() if getattr(handler, "__name__", "") != "handler"}
        return {
            name: {"category": category, "status": "AVAILABLE" if name in available else "NOT_AVAILABLE"}
            for category, names in REQUIRED_OPERATION_CATALOG.items() for name in names
        }

    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict):
            return failure("<invalid>", "INVALID_REQUEST", "Operation request must be a JSON object", request_id=None)
        operation = request.get("operation")
        request_id = request.get("request_id")
        unknown = sorted(set(request) - {"schema_version", "request_id", "operation", "project", "parameters", "expected_revision"})
        if unknown:
            return failure(str(operation or "<invalid>"), "INVALID_REQUEST", f"Unknown request fields: {', '.join(unknown)}", request_id=request_id)
        if request.get("schema_version") != "1.0.0":
            return failure(str(operation or "<invalid>"), "UNSUPPORTED_REQUEST_SCHEMA", "schema_version must be 1.0.0", request_id=request_id)
        if operation not in self.handlers:
            return failure(str(operation or "<missing>"), "UNKNOWN_OPERATION", f"Unknown operation: {operation}", request_id=request_id)
        project = request.get("project")
        if not isinstance(project, str) or not project:
            return failure(str(operation), "INVALID_REQUEST", "project must be a non-empty path", request_id=request_id)
        parameters = request.get("parameters", {})
        if not isinstance(parameters, dict):
            return failure(str(operation), "INVALID_REQUEST", "parameters must be an object", request_id=request_id)
        expected_revision = request.get("expected_revision")
        if expected_revision is not None and (isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 1):
            return failure(str(operation), "INVALID_REQUEST", "expected_revision must be a positive integer", request_id=request_id)
        store: ProjectStore | None = None
        try:
            if operation in {"create_conversion_project", "open_conversion_project"}:
                result, store, artifacts = self.handlers[operation](project, parameters, expected_revision)
            else:
                store = ProjectStore.open(project)
                result, store, artifacts = self.handlers[operation](store, parameters, expected_revision)
            return success(str(operation), result, request_id=request_id, revision=store.revision, artifacts=artifacts)
        except ProjectError as exc:
            revision = store.revision if store is not None else None
            if revision is None:
                try:
                    revision = ProjectStore.open(project).revision
                except ProjectError:
                    pass
            return failure(str(operation), exc.code, str(exc), request_id=request_id, revision=revision)
        except OperationError as exc:
            return failure(str(operation), exc.code, str(exc), request_id=request_id, revision=store.revision if store else None, details=exc.details)
        except Exception as exc:
            return failure(str(operation), "INTERNAL_ERROR", str(exc), request_id=request_id, revision=store.revision if store else None)


def execute_request(request: dict[str, Any]) -> dict[str, Any]:
    return OperationRegistry().execute(request)
