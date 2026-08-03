# Activation attestation contract

This is a bounded execution record, not a validation receipt. Broad validation
belongs only to `PRE_BDS_MILESTONE` and `FINAL_MOD_MILESTONE`.

Allowed fields:

```json
{
  "schema_version": "bedrock-factory.activation-attestation.v1.0.0",
  "activation_id": "A1",
  "assignment_sha256": "64 lowercase hex",
  "platform_qualification_sha256": "64 lowercase hex",
  "repository_ref": "refs/heads/codex/example",
  "exit_code": 0,
  "cleanup_status": "PASS",
  "candidate_id": "C1"
}
```

`candidate_id`, `candidate_sha256`, and `stop_code` are optional. Do not add
environment dumps, absolute inventories, prompts, commands, negative probes,
package manifests, deterministic-build results, or credential information.
