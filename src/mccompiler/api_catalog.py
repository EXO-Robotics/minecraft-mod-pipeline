from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


def _version(value: str) -> tuple[int, ...]:
    base = value.split("-", 1)[0]
    try:
        return tuple(int(part) for part in base.split("."))
    except ValueError as exc:
        raise ValueError(f"invalid API version: {value}") from exc


@dataclass(frozen=True)
class ApiSymbol:
    module: str
    symbol: str
    minimum_stable_version: str
    engine_version: str
    stability: str
    experiments_required: tuple[str, ...]
    marketplace_candidate: bool
    realm_candidate: bool
    bds_only: bool
    replacement_strategies: tuple[str, ...]

    @classmethod
    def from_json(cls, value: dict[str, Any]) -> "ApiSymbol":
        return cls(
            module=str(value["module"]),
            symbol=str(value["symbol"]),
            minimum_stable_version=str(value["minimum_stable_version"]),
            engine_version=str(value["engine_version"]),
            stability=str(value["stability"]),
            experiments_required=tuple(value.get("experiments_required", [])),
            marketplace_candidate=bool(value.get("marketplace_candidate")),
            realm_candidate=bool(value.get("realm_candidate")),
            bds_only=bool(value.get("bds_only")),
            replacement_strategies=tuple(value.get("replacement_strategies", [])),
        )


class ApiCatalog:
    def __init__(self, document: dict[str, Any]):
        self.schema_version = str(document["schema_version"])
        self.catalog_version = str(document["catalog_version"])
        self.last_verified = str(document["last_verified"])
        self.symbols = {
            (symbol.module, symbol.symbol): symbol
            for symbol in (ApiSymbol.from_json(row) for row in document.get("symbols", []))
        }

    @classmethod
    def load_default(cls) -> "ApiCatalog":
        path = Path(__file__).with_name("capabilities") / "stable-script-api.json"
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def require(self, module: str, symbol: str) -> ApiSymbol:
        try:
            return self.symbols[(module, symbol)]
        except KeyError as exc:
            raise ValueError(f"uncatalogued Script API symbol: {module}:{symbol}") from exc

    def resolve_versions(
        self,
        requirements: Iterable[tuple[str, str]],
        *,
        marketplace: bool,
    ) -> tuple[dict[str, str], list[dict[str, Any]]]:
        versions: dict[str, str] = {}
        evidence: list[dict[str, Any]] = []
        for module, name in sorted(set(requirements)):
            symbol = self.require(module, name)
            if symbol.stability != "stable":
                raise ValueError(f"non-stable Script API symbol: {module}:{name}")
            if symbol.experiments_required:
                raise ValueError(f"experimental Script API symbol: {module}:{name}")
            if marketplace and (not symbol.marketplace_candidate or symbol.bds_only):
                raise ValueError(f"Script API symbol is not Marketplace-candidate: {module}:{name}")
            current = versions.get(module)
            if current is None or _version(symbol.minimum_stable_version) > _version(current):
                versions[module] = symbol.minimum_stable_version
            evidence.append(
                {
                    "module": module,
                    "symbol": name,
                    "minimum_stable_version": symbol.minimum_stable_version,
                    "engine_version": symbol.engine_version,
                    "stability": symbol.stability,
                    "experiments_required": list(symbol.experiments_required),
                    "marketplace_candidate": symbol.marketplace_candidate,
                    "realm_candidate": symbol.realm_candidate,
                    "bds_only": symbol.bds_only,
                    "replacement_strategies": list(symbol.replacement_strategies),
                    "catalog_version": self.catalog_version,
                    "last_verified": self.last_verified,
                }
            )
        return versions, evidence

