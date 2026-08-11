# Ashen resource runtime registry

This bounded slice registers only the ten Packet 002 warehouse resource IDs as
inert stable Bedrock items. It adds exact `aionbound:` identifiers, item-atlas
bindings to the previously authored Ashen icons, and English localization.

It deliberately adds no acquisition, harvesting, recipes, loot, derived or
nonwarehouse items, equipment, gameplay components, scripts, persistence,
build, BDS, or candidate claim.

The resources use flat inventory icons with no custom geometry, rig, locator,
UV layout, or animation, so native Blockbench work is `NOT_APPLICABLE` for this
slice. Packet `.bbmodel` files are not copied or treated as native proof.

Run the deterministic author and bounded tests with:

```sh
python3 engineering/ashen-intake/resource-runtime/build_ashen_resource_runtime.py
python3 -m unittest engineering/ashen-intake/resource-runtime/test_ashen_resource_runtime.py
```
