"""Exact symmetric linear algebra over `fractions.Fraction` (`LDL^T`, solve, quad form, Schur block split)."""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import Any

from .interval import QError

MatrixQ = tuple[tuple[Fraction, ...], ...]
VectorQ = tuple[Fraction, ...]


def _as_vector(vec: Sequence[Any], label: str = "vector") -> VectorQ:
    if not isinstance(vec, Sequence) or isinstance(vec, (str, bytes, bytearray)) or len(vec) == 0:
        raise QError("SHAPE_ERROR", f"{label}: expected non-empty sequence")
    out: list[Fraction] = []
    for idx, item in enumerate(vec):
        if type(item) is not Fraction:
            raise QError("TYPE_ERROR", f"{label}[{idx}]: expected exact Fraction, got {type(item).__name__}")
        out.append(item)
    return tuple(out)


def _as_rect_matrix(mat: Sequence[Sequence[Any]], label: str = "matrix") -> MatrixQ:
    if not isinstance(mat, Sequence) or isinstance(mat, (str, bytes, bytearray)) or len(mat) == 0:
        raise QError("SHAPE_ERROR", f"{label}: expected non-empty matrix")
    rows: list[VectorQ] = []
    cols = -1
    for r_idx, row in enumerate(mat):
        v = _as_vector(row, f"{label}[{r_idx}]")
        if cols < 0:
            cols = len(v)
        elif len(v) != cols:
            raise QError("SHAPE_ERROR", f"{label}[{r_idx}]: ragged row length {len(v)} != {cols}")
        rows.append(v)
    return tuple(rows)


def _as_symmetric_matrix(mat: Sequence[Sequence[Any]], label: str = "M") -> MatrixQ:
    m = _as_rect_matrix(mat, label)
    n = len(m)
    if len(m[0]) != n:
        raise QError("SHAPE_ERROR", f"{label}: expected square matrix, got {n}x{len(m[0])}")
    for i in range(n):
        for j in range(i + 1, n):
            if m[i][j] != m[j][i]:
                raise QError("SYMMETRY_ERROR", f"{label}[{i}][{j}] != {label}[{j}][{i}]")
    return m


def dot(a: Sequence[Fraction], b: Sequence[Fraction]) -> Fraction:
    """Exact inner product `a^T b` over `Fraction`."""
    va = _as_vector(a, "a")
    vb = _as_vector(b, "b")
    if len(va) != len(vb):
        raise QError("SHAPE_ERROR", f"dot length mismatch: {len(va)} != {len(vb)}")
    acc = Fraction(0, 1)
    for x, y in zip(va, vb):
        acc += x * y
    return acc


def mat_vec(A: Sequence[Sequence[Fraction]], x: Sequence[Fraction]) -> VectorQ:
    """Exact matrix-vector product `A x` over `Fraction`."""
    mat = _as_rect_matrix(A, "A")
    vx = _as_vector(x, "x")
    if len(mat[0]) != len(vx):
        raise QError("SHAPE_ERROR", f"mat_vec shape mismatch: cols {len(mat[0])} != len(x) {len(vx)}")
    return tuple(dot(row, vx) for row in mat)


def quad_form(M: Sequence[Sequence[Fraction]], v: Sequence[Fraction]) -> Fraction:
    """Exact quadratic form `v^T M v` for symmetric `M`."""
    sym = _as_symmetric_matrix(M, "M")
    vv = _as_vector(v, "v")
    if len(sym) != len(vv):
        raise QError("SHAPE_ERROR", f"quad_form shape mismatch: {len(sym)} != {len(vv)}")
    return dot(vv, mat_vec(sym, vv))


def ldlt_exact(M: Sequence[Sequence[Fraction]]) -> tuple[MatrixQ, VectorQ]:
    """Exact unpivoted symmetric `LDL^T` factorization over `Fraction`. Fails closed on zero pivot."""
    sym = _as_symmetric_matrix(M, "M")
    n = len(sym)
    L: list[list[Fraction]] = [
        [Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n)]
        for i in range(n)
    ]
    d: list[Fraction] = [Fraction(0, 1)] * n
    for j in range(n):
        acc = Fraction(0, 1)
        for k in range(j):
            acc += L[j][k] * L[j][k] * d[k]
        pivot = sym[j][j] - acc
        if pivot == 0:
            raise QError("ZERO_PIVOT", f"exact LDL^T encountered zero pivot at index {j}")
        d[j] = pivot
        for i in range(j + 1, n):
            acc_ij = Fraction(0, 1)
            for k in range(j):
                acc_ij += L[i][k] * L[j][k] * d[k]
            L[i][j] = (sym[i][j] - acc_ij) / pivot
    return tuple(tuple(row) for row in L), tuple(d)


def ldlt_reconstruct(L: Sequence[Sequence[Fraction]], d: Sequence[Fraction]) -> MatrixQ:
    """Recompute `L @ diag(d) @ L^T` exactly."""
    lm = _as_rect_matrix(L, "L")
    dv = _as_vector(d, "d")
    n = len(dv)
    if len(lm) != n or len(lm[0]) != n:
        raise QError("SHAPE_ERROR", f"L must be {n}x{n}, got {len(lm)}x{len(lm[0])}")
    out: list[VectorQ] = []
    for i in range(n):
        row: list[Fraction] = []
        for j in range(n):
            acc = Fraction(0, 1)
            for k in range(n):
                acc += lm[i][k] * dv[k] * lm[j][k]
            row.append(acc)
        out.append(tuple(row))
    return tuple(out)


def verify_ldlt_admit(
    M: Sequence[Sequence[Fraction]],
    L: Sequence[Sequence[Fraction]],
    d: Sequence[Fraction],
) -> bool:
    """Replay an `ADMIT(ldlt)` witness: `L` unit lower-triangular, every `d_i > 0`, and `M == L diag(d) L^T`."""
    sym = _as_symmetric_matrix(M, "M")
    lm = _as_rect_matrix(L, "L")
    dv = _as_vector(d, "d")
    n = len(sym)
    if len(lm) != n or len(lm[0]) != n or len(dv) != n:
        return False
    for i in range(n):
        if dv[i] <= 0:
            return False
        if lm[i][i] != 1:
            return False
        for j in range(i + 1, n):
            if lm[i][j] != 0:
                return False
    return ldlt_reconstruct(lm, dv) == sym


def verify_refuse_witness(
    M: Sequence[Sequence[Fraction]],
    v: Sequence[Fraction],
) -> tuple[bool, Fraction]:
    """Replay a non-PD `REFUSE(Schur(v))` witness: `v != 0` and `v^T M v <= 0` (proves `not PosDef M`).

    Accepts `v^T M v == 0` (semidefinite boundary) as a valid proof that `M` is not strictly positive definite.
    """
    sym = _as_symmetric_matrix(M, "M")
    vv = _as_vector(v, "v")
    if len(sym) != len(vv):
        raise QError("SHAPE_ERROR", f"witness length {len(vv)} != matrix dim {len(sym)}")
    qv = quad_form(sym, vv)
    nonzero = any(entry != 0 for entry in vv)
    return (nonzero and qv <= 0), qv


def solve_ldlt(
    L: Sequence[Sequence[Fraction]],
    d: Sequence[Fraction],
    b: Sequence[Fraction],
) -> VectorQ:
    """Solve `(L diag(d) L^T) x = b` exactly via forward, diagonal, and backward substitution."""
    lm = _as_rect_matrix(L, "L")
    dv = _as_vector(d, "d")
    bv = _as_vector(b, "b")
    n = len(dv)
    if len(lm) != n or len(lm[0]) != n or len(bv) != n:
        raise QError("SHAPE_ERROR", "incompatible dimensions in solve_ldlt")
    for i in range(n):
        if lm[i][i] != 1:
            raise QError("UNIT_LOWER_ERROR", f"L[{i}][{i}] != 1")
        for j in range(i + 1, n):
            if lm[i][j] != 0:
                raise QError("UNIT_LOWER_ERROR", f"L[{i}][{j}] != 0 above diagonal")
        if dv[i] == 0:
            raise QError("ZERO_PIVOT", f"d[{i}] == 0 in solve_ldlt")
    y: list[Fraction] = [Fraction(0, 1)] * n
    for i in range(n):
        acc = Fraction(0, 1)
        for k in range(i):
            acc += lm[i][k] * y[k]
        y[i] = bv[i] - acc
    z = [y[i] / dv[i] for i in range(n)]
    x: list[Fraction] = [Fraction(0, 1)] * n
    for i in range(n - 1, -1, -1):
        acc = Fraction(0, 1)
        for k in range(i + 1, n):
            acc += lm[k][i] * x[k]
        x[i] = z[i] - acc
    return tuple(x)


def block_split(
    A: Sequence[Sequence[Fraction]],
    B0: Sequence[Sequence[Fraction]],
    D: Sequence[Sequence[Fraction]],
    *,
    eta: Fraction = Fraction(1, 1),
) -> MatrixQ:
    """Build symmetric coupled block matrix `[[A, eta * B0], [eta * B0^T, D]]`."""
    if type(eta) is not Fraction:
        raise QError("TYPE_ERROR", f"eta expected exact Fraction, got {type(eta).__name__}")
    am = _as_symmetric_matrix(A, "A")
    bm = _as_rect_matrix(B0, "B0")
    dm = _as_symmetric_matrix(D, "D")
    na = len(am)
    nd = len(dm)
    if len(bm) != na or len(bm[0]) != nd:
        raise QError("SHAPE_ERROR", f"B0 must be {na}x{nd}, got {len(bm)}x{len(bm[0])}")
    n = na + nd
    out: list[list[Fraction]] = [[Fraction(0, 1)] * n for _ in range(n)]
    for i in range(na):
        for j in range(na):
            out[i][j] = am[i][j]
        for j in range(nd):
            val = eta * bm[i][j]
            out[i][na + j] = val
            out[na + j][i] = val
    for i in range(nd):
        for j in range(nd):
            out[na + i][na + j] = dm[i][j]
    return tuple(tuple(row) for row in out)


def signed_laplacian(W: Sequence[Sequence[int | Fraction]]) -> MatrixQ:
    """Construct the Dale-signed Laplacian `L` from square directed weight matrix `W`.

    `s_ij = W_ij + W_ji`, `L_ii = sum_{j != i} |s_ij|`, `L_ij = -s_ij` (`i != j`).
    """
    if not isinstance(W, Sequence) or isinstance(W, (str, bytes, bytearray)) or len(W) == 0:
        raise QError("SHAPE_ERROR", "W must be a non-empty square matrix")
    n = len(W)
    wq: list[list[Fraction]] = []
    for i, row in enumerate(W):
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes, bytearray)) or len(row) != n:
            raise QError("SHAPE_ERROR", f"W[{i}] must have length {n}")
        qrow: list[Fraction] = []
        for j, val in enumerate(row):
            if type(val) is int:
                qrow.append(Fraction(val, 1))
            elif type(val) is Fraction:
                qrow.append(val)
            else:
                raise QError("TYPE_ERROR", f"W[{i}][{j}] expected exact int or Fraction, got {type(val).__name__}")
        wq.append(qrow)
    L: list[list[Fraction]] = [[Fraction(0, 1)] * n for _ in range(n)]
    for i in range(n):
        diag_acc = Fraction(0, 1)
        for j in range(n):
            if i == j:
                continue
            s_ij = wq[i][j] + wq[j][i]
            diag_acc += abs(s_ij)
            L[i][j] = -s_ij
        L[i][i] = diag_acc
    return tuple(tuple(row) for row in L)


def permute_symmetric(M: Sequence[Sequence[Fraction]], order: Sequence[int]) -> MatrixQ:
    """Permute rows and columns symmetrically according to bijection `order`."""
    sym = _as_symmetric_matrix(M, "M")
    n = len(sym)
    if not isinstance(order, Sequence) or isinstance(order, (str, bytes, bytearray)):
        raise QError("PERMUTATION_ERROR", f"order must be a Sequence permutation of 0..{n - 1}")
    perm = tuple(order)
    if len(perm) != n or any(type(idx) is not int for idx in perm) or sorted(perm) != list(range(n)):
        raise QError("PERMUTATION_ERROR", f"order must be a permutation of 0..{n - 1}")
    return tuple(tuple(sym[perm[i]][perm[j]] for j in range(n)) for i in range(n))
