"""Validated frontend boundaries.

`java_common` is the currently proven semantic profile. Loader adapters enrich
registration metadata; `jar_bytecode` provides conservative class evidence.
"""

SUPPORTED_PROFILES = ("java-common", "fabric-source")
ADAPTER_BOUNDARIES = ("fabric", "neoforge", "forge-modern", "forge-legacy", "jar-bytecode")
