# Contributing

Keep the package portable and campaign-neutral. Do not commit modpacks,
decompiled material, credentials, generated factory state, candidate artifacts,
mailbox history, SQLite databases, absolute workstation paths, or proprietary
Minecraft assets.

Before opening a change:

```bash
python3.11 tools/bootstrap.py --check-only
python3.11 -m unittest discover -s tests -v
```

Changes to generation handling, mailbox idempotency, clean-room boundaries,
write-root enforcement, retry behavior, or candidate immutability require a
negative regression test.
