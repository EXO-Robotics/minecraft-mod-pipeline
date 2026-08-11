# Whisperwood entity-runtime map

Run:

```sh
python3 engineering/whisperwood-intake/entity-runtime/build_entity_runtime_map.py
python3 -m unittest engineering/whisperwood-intake/entity-runtime/test_entity_runtime_map.py -v
```

The generator consumes the binding Creative files, the checked-in Whisperwood intake map, and hash-bound G7 successor patterns. It writes only the JSON and Markdown maps in this directory. It does not produce or modify pack content.
