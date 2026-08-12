# Skyreach representative creature runtime

This lane binds only the three Skyreach creatures with exact native representative PASS evidence: Cloud Goat, Gale Hawk, and Wind Roc.

Cloud Goat and Gale Hawk receive conservative, mountain-scoped natural ecology. Wind Roc is a summonable, non-spawnable arena shell only; Storm Nest encounter, terminal, reward, seal, and completion semantics remain deferred. The seven other Packet 004 creature identities are recorded as withheld pending native repair proof.

Run:

```sh
python3 engineering/skyreach-intake/entity-runtime/build_skyreach_entity_runtime.py
python3 -m unittest engineering/skyreach-intake/entity-runtime/test_skyreach_entity_runtime.py
```

This lane does not run a build, BDS, client, multiplayer, console, Marketplace, or release gate.
