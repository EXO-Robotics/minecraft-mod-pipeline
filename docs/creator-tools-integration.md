# Creator Tools integration

The planned integration invokes a pinned, hash-verified official Minecraft Creator Tools build and stores the exact executable identity, selected suites, raw output, normalized findings, policy decisions, and timestamps.

Coverage should include Add-On structure, manifests, module dependencies, stable/beta/experimental use, script analysis, namespaces, identifiers, resources, textures, size, file counts, platform targets, integrity, sharing, and Marketplace-oriented warnings.

```yaml
creator_tools:
  version: UNPINNED
  artifact_sha256: null
  suites: []
  errors: null
  warnings: null
  marketplace_approval_implied: false
  status: NOT_RUN
```

Compiler errors fail. Every warning receives a versioned policy disposition or explicit approval. Reports preserve raw findings. Passing Creator Tools proves only the selected automated checks for the tested artifact; it never implies Marketplace approval.

The current worktree includes a pinned-tool policy adapter and recorded JSON fixtures. Unit tests cover executable discovery, version mismatch, suite rejection, deterministic normalization, and recorded invocation without network access. No live official Creator Tools run against a Benchmark A artifact is claimed.
