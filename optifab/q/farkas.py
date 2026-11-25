"""Exact pure-Q Farkas infeasibility certificate verifiers (equality and inequality forms)."""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction

from .interval import _short_q
from .linalg import _as_rect_matrix, _as_vector, dot


def verify_farkas_eq(
    A: Sequence[Sequence[Fraction]],
    b: Sequence[Fraction],
    p: Sequence[Fraction],
) -> tuple[bool, str]:
    """Verify an exact Farkas equality refusal certificate for `A y = b`: `p^T A = 0` and `p^T b != 0`.

    Never trusts a stored verdict; recomputes every inner product directly from `(A, b, p)`.
    """
    am = _as_rect_matrix(A, "A")
    bv = _as_vector(b, "b")
    pv = _as_vector(p, "p")
    m = len(am)
    n = len(am[0])
    if len(bv) != m:
        return False, f"len(b)={len(bv)} != rows(A)={m}"
    if len(pv) != m:
        return False, f"len(p)={len(pv)} != rows(A)={m}"
    for j in range(n):
        col_dot = Fraction(0, 1)
        for i in range(m):
            col_dot += pv[i] * am[i][j]
        if col_dot != 0:
            return False, f"(p^T A)[{j}] = {_short_q(col_dot)} != 0"
    pb = dot(pv, bv)
    if pb == 0:
        return False, "p^T b == 0 (no contradiction)"
    return True, "ok"


def verify_farkas_ineq(
    A: Sequence[Sequence[Fraction]],
    b: Sequence[Fraction],
    p: Sequence[Fraction],
) -> tuple[bool, str]:
    """Verify an exact Farkas inequality refusal certificate for `A x <= b`: `p >= 0`, `p^T A = 0`, `p^T b < 0`."""
    am = _as_rect_matrix(A, "A")
    bv = _as_vector(b, "b")
    pv = _as_vector(p, "p")
    m = len(am)
    n = len(am[0])
    if len(bv) != m:
        return False, f"len(b)={len(bv)} != rows(A)={m}"
    if len(pv) != m:
        return False, f"len(p)={len(pv)} != rows(A)={m}"
    for i, entry in enumerate(pv):
        if entry < 0:
            return False, f"p[{i}] = {_short_q(entry)} < 0"
    for j in range(n):
        col_dot = Fraction(0, 1)
        for i in range(m):
            col_dot += pv[i] * am[i][j]
        if col_dot != 0:
            return False, f"(p^T A)[{j}] = {_short_q(col_dot)} != 0"
    pb = dot(pv, bv)
    if pb >= 0:
        return False, f"p^T b = {_short_q(pb)} >= 0 (must be strictly negative)"
    return True, "ok"
