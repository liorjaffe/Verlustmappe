"""Adapter between the registry and the new core (D28). The ONLY new-core module allowed to
import legacy code, and only `registry.py`, read-only. It copies values into immutable
objects and never writes back.

Blocks REJECTED and SUPERSEDED entries (D11, D26/D28). UNCERTAINTY_NOT_ASSESSED entries stay
readable: the status is passed on (D26), computation is never blocked by u = 0.0.
"""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType

from .. import registry as _registry
from .status import u_class as _u_class

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
    u_class: str


def get_param(key):
    """Immutable copy of one registry entry; unknown keys raise KeyError, blocked ones
    raise BlockedParameterError."""
    e = _registry.REGISTRY[key]
    if e["status"] in BLOCKED_STATUSES:
        raise BlockedParameterError(f"{key} is {e['status']} and must not feed the new core")
    return Param(key=key, value=e["value"], unit=e["unit"], status=e["status"],
                 uncertainty=e["uncertainty"],
                 u_class=_u_class(key, e["status"], e["uncertainty"]))


def _immutable(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _immutable(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_immutable(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_immutable(item) for item in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported parameter value type: {type(value).__name__}")


@dataclass(frozen=True, init=False)
class ParamSet:
    """Public creation only via from_registry; an API guard, not a security boundary."""

    parameters: tuple[Param, ...]

    def __init__(self) -> None:
        raise TypeError("ParamSet must be created with ParamSet.from_registry()")

    @classmethod
    def from_registry(cls, keys: Iterable[str]) -> "ParamSet":
        captured = tuple(
            replace(p, value=_immutable(p.value)) for p in (get_param(key) for key in keys)
        )
        if len({p.key for p in captured}) != len(captured):
            raise ValueError("duplicate requested parameter keys")
        snapshot = object.__new__(cls)
        object.__setattr__(snapshot, "parameters", captured)
        return snapshot

    def __getitem__(self, key: str) -> Param:
        for parameter in self.parameters:
            if parameter.key == key:
                return parameter
        raise KeyError(key)
