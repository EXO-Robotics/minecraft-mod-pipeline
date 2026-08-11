# Whisperwood structure assembly lane

Run:

```sh
python3 engineering/whisperwood-intake/structure-assemblies/author_whisperwood_structures.py
python3 engineering/whisperwood-intake/structure-assemblies/author_whisperwood_structures.py --check
python3 -m unittest engineering/whisperwood-intake/structure-assemblies/test_whisperwood_structure_assemblies.py -v
python3 engineering/whisperwood-intake/structure-assemblies/validate_whisperwood_structures.py
python3 engineering/whisperwood-intake/structure-assemblies/validate_whisperwood_structures.py --check
```

This lane authors only eight block-built structures and their stable feature registrations. It deliberately does not bind loot tables, reward identities, runtime interactions, the two direct custom props, or candidate/BDS claims.
