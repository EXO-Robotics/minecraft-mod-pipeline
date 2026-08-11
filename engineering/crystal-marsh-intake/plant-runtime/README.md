# Crystal Marsh plant runtime

All ten Packet 003 plants are bound as stable `1.21.80` custom blocks using
the native pass-2 geometry and exact packet texture bytes. Five water-facing
plants explicitly contain water; all plants have non-colliding, bounded
selection and placement rules tied to Crystal Marsh ground, shade, or channel
supports.

The blocks bind the ten exact self-harvest loot paths. The separate Crystal
economy lane owns those table bytes, so this lane does not duplicate them.

Native animation clips remain evidence only. Stable custom blocks do not offer
a clean entity-style skeletal controller binding, and this implementation does
not introduce entity surrogates, Script API components, or new runtime systems.

This is source/static closure. It does not prove live placement, harvest,
waterlogging, rendering, distribution, Creator Tools, BDS, client, console, or
release behavior.
