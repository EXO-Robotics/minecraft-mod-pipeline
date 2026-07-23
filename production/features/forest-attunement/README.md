# Forest Attunement

Original Bedrock-native internal-test vertical slice. Use an Attunement Sigil once to store a versioned per-player unlock. Every 100 ticks, attuned players in the implementation's conservative vanilla forest-biome set receive Speed I for 120 ticks.

Build with `python3 tools/build_forest_attunement.py`. Operators may run `/function forest_attunement_test` to grant a sigil and `/function forest_attunement_reset` to reset only themselves. Unknown or corrupt property values fail closed and remain untouched until an operator reset.

This is not a public-release, Marketplace, desktop-client, Realm, multiplayer-live, or physical-PS4 qualification claim.
