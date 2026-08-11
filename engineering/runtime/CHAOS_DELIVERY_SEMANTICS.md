# Chaos delivery semantics refinement

Status: `AT_MOST_ONCE_TERMINOLOGY_AND_CRASH_WINDOW_RECORDED`

The successor no longer describes Chaos external effects as exactly-once. Bedrock cannot atomically commit dynamic-property journal state together with an item spawn, entity spawn, player effect, discovery stamp, or block edit.

The runtime now records one of three explicit outcomes:

- `completed_in_process` or `temporary_cleanup_completed` with `deliverySemantics=at_most_once` when the live process reaches its terminal step;
- `replay_suppressed_after_uncertain_execution` with `replaySuppressed=true` when restart finds a non-temporary operation already marked `executing`;
- `scheduler_refused_before_execution` with `deliverySemantics=not_started` when bounded scheduling refuses the operation.

An `accepted` operation remains restart-resumable. An `executing` non-temporary operation is never replayed, avoiding duplication at the cost of a documented crash window in which the external effect may or may not have occurred.

Targeted semantic tests passed 14/14. This is source-level/runtime-harness evidence only; it is not Stable BDS restart or gameplay proof.
