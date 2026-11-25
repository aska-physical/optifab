"""Named `Inertia` record unifying S99, S102, and S86/S101 inertia conventions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .interval import QError


def _require_nonneg_int(val: Any, label: str) -> int:
    if type(val) is not int or val < 0:
        raise QError("TYPE_ERROR", f"{label}: expected non-negative int, got {type(val).__name__}")
    return val


@dataclass(frozen=True)
class Inertia:
    """Named Sylvester inertia triple `(pos, neg, zero)`. Positional tuples are forbidden in IR."""

    pos: int
    neg: int
    zero: int

    def __post_init__(self) -> None:
        _require_nonneg_int(self.pos, "Inertia.pos")
        _require_nonneg_int(self.neg, "Inertia.neg")
        _require_nonneg_int(self.zero, "Inertia.zero")

    @property
    def dim(self) -> int:
        return self.pos + self.neg + self.zero

    @property
    def is_pos_def(self) -> bool:
        return self.pos > 0 and self.neg == 0 and self.zero == 0

    def to_dict(self) -> dict[str, int]:
        return {"pos": self.pos, "neg": self.neg, "zero": self.zero}


def of_s99(a: int, b: int, c: int) -> Inertia:
    """Convert S99 legacy tuple `[n_+, n_0, n_-]` into named `Inertia(pos=a, neg=c, zero=b)`."""
    return Inertia(pos=a, neg=c, zero=b)


def of_s102(a: int, b: int, c: int) -> Inertia:
    """Convert S102 legacy tuple `[n_+, n_-, n_0]` into named `Inertia(pos=a, neg=b, zero=c)`."""
    return Inertia(pos=a, neg=b, zero=c)


def of_pivot(d: Fraction) -> Inertia:
    """Convert a scalar pivot `d` (S86/S101) into a 1D `Inertia`."""
    if type(d) is not Fraction:
        raise QError("TYPE_ERROR", f"of_pivot expects exact Fraction, got {type(d).__name__}")
    if d > 0:
        return Inertia(pos=1, neg=0, zero=0)
    if d < 0:
        return Inertia(pos=0, neg=1, zero=0)
    return Inertia(pos=0, neg=0, zero=1)


def of_ldlt_diag(diag: Sequence[Fraction]) -> Inertia:
    """Compute named `Inertia` from a non-empty exact `LDL^T` diagonal sequence."""
    if not isinstance(diag, Sequence) or isinstance(diag, (str, bytes, bytearray)) or len(diag) == 0:
        raise QError("SHAPE_ERROR", "of_ldlt_diag expects non-empty Sequence of Fraction")
    pos = 0
    neg = 0
    zero = 0
    for idx, val in enumerate(diag):
        if type(val) is not Fraction:
            raise QError("TYPE_ERROR", f"diag[{idx}] expected exact Fraction, got {type(val).__name__}")
        if val > 0:
            pos += 1
        elif val < 0:
            neg += 1
        else:
            zero += 1
    return Inertia(pos=pos, neg=neg, zero=zero)


def legacy_tuple_agree(a: int, b: int, c: int) -> bool:
    """Return True iff `of_s99(a, b, c) == of_s102(a, b, c)` (algebraically equivalent to `b == c`)."""
    return of_s99(a, b, c) == of_s102(a, b, c)
