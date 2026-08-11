# Ashen plant runtime binding

All ten Packet 002 plants are bound as stable `1.21.80` custom blocks using
native pass-2 geometry and exact source texture bytes. Placement filters are
Ashen-specific: ash soil and cinder fields, hot basalt, vent-adjacent stone,
cave faces, and cliff or log attachments.

This lane does not copy Whisperwood density or supports. It also does not fake
skeletal playback through entity surrogates: the native clips remain editor
evidence because stable custom blocks have no clean entity-animation controller
surface. Ecology feature rules, harvest loot, client rendering, and BDS remain
separate gates.
