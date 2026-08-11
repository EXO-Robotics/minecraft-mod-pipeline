# Whisperwood resource registry

This slice registers the ten Packet 001 resource identities as inert Bedrock items. It binds canonical `aionbound:` identifiers, approved display names, Creative-contract rarity/role metadata, item-atlas keys, and English localization.

Stack limits are inventory-shape categories, not drop probabilities or gameplay effects: common bulk materials stack to 64, uncommon/refined materials to 32, and rare/elite/prestige materials to 16. The slice deliberately adds no recipes, loot tables, use effects, or progression behavior.

Run the bounded closure check with:

```sh
python3 -m unittest tests.test_whisperwood_resource_registry
```

The test intentionally fails if any expected icon file is absent or empty. Icon manufacture belongs to the separate presentation lane; this registry does not create or edit PNGs.
