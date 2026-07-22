# Licensing Review

This is an engineering triage document, not legal advice. Before vendoring code,
redistributing generated assets, or publishing a converted modpack, inspect the
current license files and the source mod's license.

| Project | Reported license/source | Integration posture |
|---|---|---|
| Geyser | MIT | Reference or dependency candidate, subject to current license file |
| Hydraulic | MIT | Reference; runtime problem differs from this compiler |
| Rainbow | MIT | Reference/dependency candidate |
| MCProtocolLib | MIT | Optional runtime probe dependency |
| PackConverter | Repository license file; verify exact current terms before linking | Adapter candidate; do not copy assets automatically |
| JavaParser | LGPL or Apache option, depending on distribution terms | Good candidate; make the selected license explicit |
| Spoon | MIT/CeCILL-C dual license | Candidate with license selection review |
| ASM | BSD-style OW2 license | Candidate bytecode dependency |
| CFR | Verify current repository license before redistribution | Optional executable/tool adapter |
| Vineflower | Verify current repository license before redistribution | Optional executable/tool adapter |
| LLVM | Apache-2.0 with LLVM exception | Architecture reference; no need to embed LLVM now |
| Babel | MIT | Architecture reference or future JS generator dependency |
| TypeScript | Apache-2.0 | Optional script generator/build dependency |
| Roslyn | MIT | Architecture reference only; not a Java frontend |

## User-provided mod content

The safe default is local conversion:

```text
user supplies legally obtained JAR/modpack
  -> compiler reads locally
  -> compiler emits local scaffold
  -> compiler does not redistribute the source JAR or unlicensed assets
```

The generated report should preserve source provenance and flag assets that were
copied. Distribution permissions remain the user's responsibility.

