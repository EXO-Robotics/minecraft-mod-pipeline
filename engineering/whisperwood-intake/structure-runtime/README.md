# Whisperwood structure runtime map

Run `python3 build_structure_runtime_map.py` to regenerate the Markdown and JSON maps from the frozen Creative contract, Packet 001 briefs/exports, the Wave 1 decision ledger, and the static G7 engineering patterns.

Run `python3 -m unittest test_structure_runtime_map.py -v` for the bounded deterministic checks. This lane produces planning authority only and never edits behavior/resource packs or authors `.mcstructure` bytes.
