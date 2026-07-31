# MacBook-local persistent tester

The tester consumes only committed `tester_intake/**/*.json` messages. Each
executable intake carries one validated `crazycraft-remote-v1`
`BDS_QUALIFICATION` request and exact `git_path`/commit bindings for the BP, RP,
and MCAddon. Candidate bytes are read with `git show`; product worktrees and
repositories are never edited.

The service allows two active jobs total and one active job per pack. Docker is
invoked only through the fixed `/opt/crazycraft/bin/qualify-exact-package`
route. Request fields cannot provide a command, executable, shell, mount, or
environment variable. The only accepted tester image is the digest in
`local-tester-config.json`.

Cursor, process, lock, and scratch state is ignored under `runtime/`. After a
job reaches a terminal result, the service validates the exact candidate
hashes, result payload hash, cleanup status, and receipt inventory. It then
appends one new `TEST_PASS`, `TEST_FAIL_PRODUCT`, or
`TEST_FAIL_INFRASTRUCTURE` result message on the mailbox authority branch.
Existing messages are never overwritten. Result publication uses an exclusive
mailbox Git lock, requires a clean mailbox worktree, and creates one commit
containing only the new result path.

Before dispatch selection, the tester reconstructs terminal jobs from committed
result messages. A historical-invalid intake may be suppressed only by an exact
compatibility entry binding its add commit, repository path, and raw SHA-256,
plus its superseding intake and terminal results. Unknown invalid intakes are
recorded as pack-local ignored-runtime rejections; they do not halt validation
or dispatch of later valid intakes. Neither disposition permits BDS execution,
and a terminal committed result prevents the bound job from being re-executed
after runtime-state loss.
