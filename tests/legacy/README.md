# Legacy test quarantine

These fixtures are historical evidence, not normal Wave 1 successor tests.

- `g6/core_beta_g6.py.disabled` asserts G6-specific versions, markers, and runtime
  text. Its archive test invokes `tooling/build.py`, which writes legacy package
  names into the checkout's `dist/` directory.
- `core_v0/core_v0.py.disabled` targets the pre-G6 Core v0 contract and also
  invokes `tooling/build.py` during discovery.

The `.disabled` suffix intentionally excludes both files from `unittest` and
`pytest` discovery. Do not rename or execute them in a successor checkout.
Historical reproduction must happen in an isolated worktree at the matching
generation, with disposable output paths.
