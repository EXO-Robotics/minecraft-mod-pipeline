# Licensing and provenance posture

Accessed: **2026-07-22**

This is an engineering policy, not legal advice.

## Rules

1. Scanning permission is not redistribution permission. Record each input artifact's source, hash, declared license, author, version and acquisition evidence.
2. Loader metadata license fields are hints, not conclusive grants. Fabric recommends SPDX identifiers, while Forge/NeoForge metadata may contain arbitrary strings. Verify the actual bundled license file and project source.
3. Do not emit copied code, textures, models, sounds, localization or structures unless the user owns them or the license/permission permits the intended transformation and distribution.
4. Preserve attribution, notices, source-offer obligations, share-alike terms and modification markings as required. Incompatible or unknown licensing becomes a blocked asset with a replacement recommendation.
5. Never package Minecraft client/server code, vanilla assets, Marketplace content, or a modded game distribution. Generated identifiers and original compatibility code are separate from Mojang/Microsoft content.
6. Do not imply endorsement. Product naming and UI must carry an appropriate unofficial-project disclaimer.
7. Keep optional AI services asset-blind by default; sending third-party source/assets to a service is a separate disclosure and authorization decision.

Minecraft's EULA says original Java mods may be distributed but modded versions of the game may not, and ownership extends only to the creator's work—not Minecraft code/content. The Usage Guidelines require mods to be distributed separately and prohibit implying official status. Sources: [Minecraft EULA](https://www.minecraft.net/en-us/eula), [Minecraft Usage Guidelines](https://www.minecraft.net/en-us/usage-guidelines), [Java mods help article](https://help.minecraft.net/hc/en-us/articles/4409139065613-Mods-for-Minecraft-Java-Edition).

Bedrock add-ons are behavior and/or resource packs. Marketplace/commercial distribution has additional program and policy requirements; local technical success does not confer Marketplace rights. Sources: [Bedrock Add-Ons FAQ](https://help.minecraft.net/hc/en-us/articles/4409140076813-Minecraft-Add-Ons-for-Bedrock-Versions-FAQ), [Minecraft Partner Program](https://www.minecraft.net/en-us/partner).

## Tool licenses

- Python is distributed under the Python Software Foundation License and historical component licenses: [Python license](https://docs.python.org/3/license.html).
- OpenJDK is GPLv2 with the Classpath Exception; distribution terms depend on the chosen JDK vendor/build: [OpenJDK legal documents](https://openjdk.org/legal/).
- Microsoft Minecraft samples carry their repository license; copy only from a pinned revision and retain its notice: [minecraft-samples repository](https://github.com/microsoft/minecraft-samples).
- `@minecraft/server` and `@minecraft/server-ui` npm declaration packages currently identify MIT licensing on their registry pages: [`@minecraft/server`](https://www.npmjs.com/package/@minecraft/server), [`@minecraft/server-ui`](https://www.npmjs.com/package/@minecraft/server-ui).

## Required provenance output

For every generated file or copied asset, record output path, source artifact hash/path, extraction or generation rule, transformations, license finding, attribution destination, confidence, override provenance and whether redistribution is cleared. A build may still produce a private diagnostic report when packaging is blocked; it must not quietly omit the licensing failure.

