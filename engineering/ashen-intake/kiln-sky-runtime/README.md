# Kiln Sky dedicated runtime service

This lane implements the ratified Kiln Sky session, reward, and migration semantics without activating them in the shared runtime event loop.

Status: `DEDICATED_SERVICE_COMPLETE_ACTIVATION_WITHHELD`.

The safety boundary is deliberate. `behavior_pack/scripts/runtime.js` is unchanged. Activation requires the integration owner to approve and apply the narrow composition described in `ACTIVATION_WITHHELD.md`, followed by targeted source checks before any package or BDS claim.

Proof in this lane is limited to source semantics and deterministic evidence. It makes no build, package, client, or BDS claim.
