"""Typed factory identities and candidate dispositions."""

from __future__ import annotations

import re
from dataclasses import dataclass


IDENTITY_PREFIXES = {
    "candidate": "C",
    "activation": "A",
    "repair_authority": "RA",
    "t1_run": "T1-R",
    "bds_run": "BDS-R",
    "observation_run": "OBS-R",
    "t10_run": "T10-R",
    "integration_candidate": "I",
}
CANDIDATE_DISPOSITIONS = {
    "PRODUCT_CANDIDATE",
    "DIAGNOSTIC_CANDIDATE",
    "EVIDENCE_ENABLING_REPLACEMENT",
    "PRODUCT_REPAIR",
    "INTEGRATION_REPAIR",
}
CONTROL_ONLY_DISPOSITIONS = {
    "INFRASTRUCTURE_ONLY_RETRY",
    "HOST_AUTHORITY_REBIND",
}


class IdentityError(ValueError):
    pass


def identity(kind: str, ordinal: int) -> str:
    prefix = IDENTITY_PREFIXES.get(kind)
    if prefix is None:
        raise IdentityError(f"unknown identity kind: {kind}")
    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
        raise IdentityError("identity ordinal must be a positive integer")
    return f"{prefix}{ordinal}"


def validate_identity(value: object, kind: str) -> str:
    prefix = IDENTITY_PREFIXES.get(kind)
    if prefix is None:
        raise IdentityError(f"unknown identity kind: {kind}")
    if not isinstance(value, str) or not re.fullmatch(re.escape(prefix) + r"[1-9][0-9]*", value):
        raise IdentityError(f"{kind} identity must use {prefix}# namespace")
    return value


@dataclass(frozen=True)
class LifecycleIdentity:
    candidate_id: str | None
    activation_id: str
    disposition: str

    def validate(self) -> None:
        validate_identity(self.activation_id, "activation")
        if self.disposition in CONTROL_ONLY_DISPOSITIONS:
            if self.candidate_id is not None:
                validate_identity(self.candidate_id, "candidate")
            return
        if self.disposition not in CANDIDATE_DISPOSITIONS:
            raise IdentityError(f"unknown lifecycle disposition: {self.disposition}")
        validate_identity(self.candidate_id, "candidate")
