# Evidence-derived receipt format

`derive_receipt.py` accepts captured check observations and derives both
per-check and overall status. The input is deliberately forbidden from
supplying either status field.

Each check must bind:

- the exact command argument vector and exit code;
- at least one named expected/actual assertion;
- at least one retained evidence file, whose SHA-256 and size are calculated by
  the derivation step;
- whether the check is required for the overall result.

The candidate binding requires an ID, commit, tree, and exact `.mcaddon`
SHA-256. A receipt passes only when every required check exited zero and every
assertion matched. Missing evidence fails closed before a receipt is written.

This format does not prove that a command was honestly captured. The final
qualification runner must create observation files directly from subprocess
results, retain stdout/stderr as evidence files, and run the derivation tool in
the qualifier workspace. A receipt is not BDS or gameplay evidence by itself.

The output contract is `evidence-receipt.schema.json`.
