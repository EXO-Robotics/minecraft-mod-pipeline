# Creator Tools integration

The integration invokes pinned official Minecraft Creator Tools 0.17.6 and stores the selected suites, exit codes, normalized findings, exact input hash, policy result, and non-approval statement.

Coverage should include Add-On structure, manifests, module dependencies, stable/beta/experimental use, script analysis, namespaces, identifiers, resources, textures, size, file counts, platform targets, integrity, sharing, and Marketplace-oriented warnings.

```yaml
creator_tools:
  version: 0.17.6
  artifact_sha256: SHA256_OF_EXACT_MCADDON
  suites: [addon, currentplatform]
  errors: 0
  warnings: 0
  marketplace_approval_implied: false
  status: PASSED_SELECTED_SUITES
```

Compiler errors fail. Every warning receives a versioned policy disposition or explicit approval. Reports preserve raw findings. Passing Creator Tools proves only the selected automated checks for the tested artifact; it never implies Marketplace approval.

Archive validation is cache-safe: the integration copies each input to a temporary filename containing its SHA-256 before invoking the pinned CLI. Any reported behavior/resource path absent from that exact archive is rejected as `STALE_CACHE_PATH`. Creator Tools 0.17.6 may emit a timestamped debug line to stdout before otherwise valid JSON even with `--offline --json`; the integration preserves that prelude as evidence and accepts only a complete JSON object consuming the remainder of stdout.

Live pinned runs exist for Benchmark A and the partial Benchmark B technical package. Both passed the required `addon` and `currentplatform` suites with zero errors and warnings. Those results apply only to their hash-bound artifacts and do not establish gameplay, rights, quality, console behavior, Marketplace suitability, submission, or approval.
