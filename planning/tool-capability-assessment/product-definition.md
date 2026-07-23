# Product definition

## Canonical definition

The project is an **evidence-backed, AI-assisted Java-to-Bedrock reconstruction toolkit and deterministic Marketplace-candidate build system**. It inventories supported Java source, JAR, and modpack inputs; preserves provenance in versioned intermediate representations; helps an agent select feature-specific Bedrock strategies; generates data-driven and protected-script scaffolding; packages Add-Ons and worlds; and records static, runtime, performance, rights, and fidelity evidence.

It is not an automatic arbitrary-mod translator, a substitute for gameplay design, a legal-clearance service, a console certification system, or evidence of Marketplace approval.

## Responsibility boundary

| Actor | Responsibility |
|---|---|
| Tool, deterministic | Scan recognized source/JAR patterns; inventory evidence; build IR and dependency facts; expose focused operations; apply accepted plans; generate deterministic scaffolds/packages; validate schemas, API policy, assets, packaging, static budgets, and evidence envelopes; distill a supplied modpack inventory. |
| AI agent | Recover gameplay intent from evidence; compare Bedrock strategies; identify uncertainty; implement protected custom behavior; diagnose failures; propose native redesigns; update IR only with provenance; record fidelity and limitations. |
| Human approver | Confirm intended experience; accept approximations or original replacements; authorize protected changes; make product and scope decisions; determine rights clearance; approve publication. |
| Physical testing | Establish real-client interaction, forms, multiplayer isolation, controller usability, Realm transfer, console performance, split-screen behavior, and asset synchronization. |
| Unsupported or unproven | Arbitrary mixin/coremod semantics, JVM/native libraries, Java custom renderers and networking, arbitrary dimensions/world generation, and broad Java GUI parity. |

Architectural fields and registered handlers are not proof of conversion. Capability claims require the evidence levels defined in `capability-matrix.json`.
