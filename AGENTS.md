# Bedrock AI Factory agent entrypoint

This repository is a portable factory control plane. It does not contain a
modpack, a finished add-on, Java source, Minecraft assets, Docker images, or
credentials.

When a user asks you to set up or run the factory:

1. Read `README.md`, `JAVA_BEDROCK_CODEX_SKILLS.md`, then
   `docs/factory-overseer.md`.
2. Run `python3.11 tools/bootstrap.py --check-only`.
3. Do not inspect a supplied modpack until the user confirms they are
   authorized to inspect it and gives the exact local path.
4. Install the repository skills only with the user's approval:
   `python3.11 tools/bootstrap.py --install-skills`.
5. Initialize a new local control root with
   `.venv/bin/python tools/factory/init_studio_factory.py --root .mccompiler/factory-v1`.
6. Run the offline synthetic rehearsal and validate one exact factory-platform
   qualification receipt before activating a real campaign. Synthetic control
   flow does not qualify the launcher, broker, authentication, or BDS adapter.
7. Use the `oversee-java-to-bedrock-factory` skill as the conversation-facing
   coordinator. Use bounded role-specific subagents only for ready packets.
8. Treat Git mailbox commits, SQLite records, candidate hashes, and receipts as
   durable authority. Chat prose and runtime projections are not authority.
9. Never import another machine's queues, task IDs, absolute paths, mailbox
   history, credentials, compatibility exceptions, or runtime state.
10. Never claim client, console, Marketplace, legal, release, or full automation
    proof unless the named external gate produced an exact receipt.

The factory is private/local by default. Public publication and release are
separate user decisions.
