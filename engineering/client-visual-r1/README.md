# G8 client-visual R1

This lane builds a complete, versioned test `.mcaddon` without changing the
active server packs. It is an A/B client-rendering probe, not a candidate.

## Included corrections

- Trophy Edge uses an explicit player item mapping, the standard item render
  controller, conditional first-/third-person holder animations, an item-slot
  root binding, normalized face-UV objects, and an isolated transparent icon.
- Char Wolf is moved byte-for-byte into Bedrock's previously PS4-proven
  `models/entity` discovery root.
- Cinder Lynx remains unchanged under the old path as the control.
- Both pack manifests advance from `1.3.1` to `1.3.2`, including reciprocal
  dependency versions, to prevent stale client-cache reuse.

The Trophy Edge pivot and rotation are inherited from the bounded G6 test
overlay. They passed static socket preflight but never received physical PS4
confirmation, so they remain a test hypothesis.

## Build and test

```sh
python3 -m unittest discover -s engineering/client-visual-r1/tests -v
python3 engineering/client-visual-r1/build_client_visual_test_pack.py
```

## Physical PS4 observation

Install the generated `.mcaddon` in a disposable copy/new Creative world. Use
freshly summoned entities:

```mcfunction
/summon aionbound:char_wolf
/summon aionbound:cinder_lynx
/give @s aionbound:trophy_edge
```

Record pack version, Bedrock client version, PS4 model/system version, and one
contemporaneous screenshot/video for each:

1. Char Wolf visible versus Cinder Lynx control.
2. Trophy Edge inventory and hotbar icon.
3. Trophy Edge first-person neutral.
4. Trophy Edge third-person front and rear.
5. Trophy Edge during item use.

Do not promote the remaining geometry-path changes until the Wolf/Lynx result is
observed. BDS load or summon success cannot substitute for this client gate.
