# Worker receipt contract

Required fields:

```json
{
  "schema_version": "1.0.0",
  "worker_id": "opaque-id",
  "role": "production-or-repair",
  "assignment_sha256": "64 lowercase hex",
  "sanitized_contract_sha256": "64 lowercase hex",
  "production_repository": "/absolute/path",
  "production_commit": "git commit",
  "launcher": {
    "command_sha256": "64 lowercase hex",
    "started": true,
    "exit_code": 0
  },
  "authentication": {
    "explicitly_authorized": true,
    "used_for_startup_only": true,
    "values_logged": false,
    "values_hashed": false,
    "copied_into_repository": false,
    "temporary_copies_remaining": false
  },
  "negative_access": [
    {
      "class": "evidence",
      "target": "opaque-or-redacted",
      "denied": true
    }
  ],
  "cleanup": {
    "startup_temp_scanned": true,
    "production_root_scanned": true,
    "credential_files_found": 0,
    "canaries_found": 0
  }
}
```

Do not record raw authentication paths when the receipt will enter production
lineage. Use an opaque class or a redacted basename.
