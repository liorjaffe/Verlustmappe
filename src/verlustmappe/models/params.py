"""Adapter between the registry and the new core (D28). The ONLY new-core module allowed to
import legacy code, and only `registry.py`, read-only. It copies values into immutable
objects and never writes back.

Blocks REJECTED and SUPERSEDED entries (D11, D26/D28). UNCERTAINTY_NOT_ASSESSED entries stay
readable: the status is passed on (D26), computation is never blocked by u = 0.0.
"""
from dataclasses import dataclass

from .. import registry as _registry

BLOCKED_STATUSES = ("REJECTED", "SUPERSEDED")


class BlockedParameterError(KeyError):
    """The registry entry exists but its status forbids use in the new core."""


@dataclass(frozen=True)
class Param:
    key: str
    value: object
    unit: str
    status: str
    uncertainty: float


def get_param(key):
    """Immutable copy of one registry entry; unknown keys raise KeyError, blocked ones
    raise BlockedParameterError."""
    e = _registry.REGISTRY[key]
    if e["status"] in BLOCKED_STATUSES:
        raise BlockedParameterError(f"{key} is {e['status']} and must not feed the new core")
    return Param(key=key, value=e["value"], unit=e["unit"], status=e["status"],
                 uncertainty=e["uncertainty"])

