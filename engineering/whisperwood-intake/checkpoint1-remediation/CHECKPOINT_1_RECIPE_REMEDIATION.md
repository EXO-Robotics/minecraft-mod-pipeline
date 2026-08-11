# Checkpoint 1 recipe remediation

Stable BDS activated and reopened the exact Whisperwood package, but reported four duplicate crafting-table recipe warnings. Five inherited recipe files had drifted to the same `stick + amethyst_shard` formula.

This repair restores the exact ingredient relations already authored in `tooling/build.py`. It adds no item, recipe, loot, or creative identity and does not modify G7.

A replacement Checkpoint 1 package must now pass the same bounded two-cycle Stable BDS smoke with those four warnings absent before the Whisperwood pattern is declared sound.
