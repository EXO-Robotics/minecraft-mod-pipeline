# Research index

Status: baseline research for the reconstruction compiler  
Access date for all linked sources: **2026-07-22**

This directory records the external facts that constrain the compiler. Sources are primary: loader project documentation/source, Microsoft Minecraft Creator documentation and package registry entries, Oracle JDK documentation, Python documentation, and Minecraft's legal terms. A source establishes what a platform accepts; it does not by itself prove that generated content works in a target Bedrock runtime.

- [Java mod and JAR inputs](java-mod-inputs.md)
- [Bedrock add-on target](bedrock-addon-target.md)
- [Tool and format pins](tool-version-pins.md)
- [Licensing and provenance posture](licensing-and-provenance.md)
- [Validation and test limits](validation-and-test-limits.md)

## Research conclusions

1. Loader metadata is useful discovery evidence, not a semantic representation of a mod. Fabric, Quilt, Forge, and NeoForge use different metadata paths and registration conventions.
2. Java source is the highest-fidelity deterministic input. A JAR fallback can recover declarations, bytecode, constants, annotations, and debug line tables, but not original source semantics.
3. Bedrock behavior packs, resource packs, data-driven entities, and Script API are complementary backends. No single layer represents arbitrary Java behavior.
4. The compiler must pin a target Bedrock profile: engine version, manifest format, content format policy, stable Script API module versions, and feature/experiment policy.
5. Static validation, import, activation, and behavioral validation are distinct gates. GameTest is useful but experimental and cannot be the only runtime oracle.
6. Input ownership and redistribution rights must be checked per artifact. Generated output must carry provenance and must not silently copy unlicensed assets or Minecraft-owned content.

