"""Exact rational intervals (`QI`) and certified transcendental enclosures over `fractions.Fraction`.

Strictly pure-Q (`L0`): zero floats, zero `math`/`numpy` imports, zero bare `assert`s.
Every transcendental enclosure returns a proven rational bracket `[lo, hi]` with outward
rounding so rational denominators stay compact while mathematical containment stays exact.
Error messages are formatted lazily with bit-length previews so large `Fraction` endpoints
never trigger Python's `int_max_str_digits` `ValueError`.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

Q = Fraction

MAX_Q_STR_DIGITS = 800
MAX_INPUT_BITS = 4096
MAX_TERMS = 128
MAX_PREC_BITS = 512
MIN_SQRT_TOL = Fraction(1, 10**100)
_DEFAULT_PREC_BITS = 96
_MAX_EXP_ABS = Fraction(500, 1)
_PREVIEW_MAX_BITS = 256


class QError(ValueError):
    """Structured fail-closed error for L0 rational arithmetic and enclosures."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _short_q(val: Fraction) -> str:
    """Format a `Fraction` safely without risking `int_max_str_digits` `ValueError`."""
    n_bits = val.numerator.bit_length()
    d_bits = val.denominator.bit_length()
    if n_bits > _PREVIEW_MAX_BITS or d_bits > _PREVIEW_MAX_BITS:
        sign = "-" if val.numerator < 0 else ""
        return f"<{sign}Fraction num_bits={n_bits}, den_bits={d_bits}>"
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def _require_fraction(val: Any, label: str) -> Fraction:
    if type(val) is not Fraction:
        raise QError("TYPE_ERROR", f"{label}: expected exact Fraction, got {type(val).__name__}")
    return val


def _check_input_bits(val: Fraction, label: str) -> None:
    if val.numerator.bit_length() > MAX_INPUT_BITS or val.denominator.bit_length() > MAX_INPUT_BITS:
        raise QError(
            "RANGE_ERROR",
            f"{label}: bit length ({val.numerator.bit_length()}/{val.denominator.bit_length()}) > {MAX_INPUT_BITS}",
        )


def q_from_int(val: Any, label: str = "value") -> Fraction:
    """Construct an exact `Fraction` from a strict `int` (rejecting `bool`, `float`, and subclasses)."""
    if type(val) is not int:
        raise QError("TYPE_ERROR", f"{label}: expected exact int, got {type(val).__name__}")
    return Fraction(val, 1)


def q_from_str(raw: Any, *, max_digits: int = MAX_Q_STR_DIGITS, label: str = "rational") -> Fraction:
    """Parse an exact canonical reduced rational string `[-]N` or `[-]N/D` with pre-`int()` digit caps.

    Rejects non-canonical forms (`-0`, leading zeros like `007` or `1/02`, unreduced `2/4`, `+3`, `3/-4`).
    """
    if type(raw) is not str:
        raise QError("TYPE_ERROR", f"{label}: expected str, got {type(raw).__name__}")
    if type(max_digits) is not int or max_digits < 1 or max_digits > MAX_Q_STR_DIGITS:
        raise QError("RANGE_ERROR", f"max_digits must be in [1, {MAX_Q_STR_DIGITS}]")
    if len(raw) == 0:
        raise QError("PARSE_ERROR", f"{label}: empty rational string")
    if len(raw) > 2 * max_digits + 2:
        raise QError("DIGIT_CAP", f"{label}: string length {len(raw)} exceeds cap")
    if "/" in raw:
        parts = raw.split("/")
        if len(parts) != 2:
            raise QError("PARSE_ERROR", f"{label}: malformed slash syntax")
        num_s, den_s = parts
        has_slash = True
    else:
        num_s, den_s = raw, "1"
        has_slash = False
    if len(num_s) == 0 or len(den_s) == 0:
        raise QError("PARSE_ERROR", f"{label}: empty numerator or denominator")
    neg = num_s[0] == "-"
    num_digits = num_s[1:] if neg else num_s
    if len(num_digits) == 0 or not (num_digits.isascii() and num_digits.isdigit()):
        raise QError("PARSE_ERROR", f"{label}: invalid numerator")
    if not (den_s.isascii() and den_s.isdigit()):
        raise QError("PARSE_ERROR", f"{label}: invalid denominator")
    if len(num_digits) > max_digits:
        raise QError("DIGIT_CAP", f"{label}: numerator digits {len(num_digits)} > {max_digits}")
    if len(den_s) > max_digits:
        raise QError("DIGIT_CAP", f"{label}: denominator digits {len(den_s)} > {max_digits}")
    if len(num_digits) > 1 and num_digits[0] == "0":
        raise QError("NONCANONICAL_RATIONAL", f"{label}: leading zero in numerator")
    if len(den_s) > 1 and den_s[0] == "0":
        raise QError("NONCANONICAL_RATIONAL", f"{label}: leading zero in denominator")
    if neg and num_digits == "0":
        raise QError("NONCANONICAL_RATIONAL", f"{label}: negative zero forbidden")
    if has_slash and den_s == "1":
        raise QError("NONCANONICAL_RATIONAL", f"{label}: explicit '/1' denominator is non-canonical")
    num = -int(num_digits) if neg else int(num_digits)
    den = int(den_s)
    if den <= 0:
        raise QError("DIV_BY_ZERO", f"{label}: denominator must be positive")
    val = Fraction(num, den)
    if val.denominator != den:
        raise QError("NONCANONICAL_RATIONAL", f"{label}: rational must be reduced in lowest terms")
    return val


def q_to_str(val: Fraction) -> str:
    """Format an exact `Fraction` as `p` (when `q == 1`) or `p/q`."""
    _require_fraction(val, "val")
    if val.denominator == 1:
        return str(val.numerator)
    return f"{val.numerator}/{val.denominator}"


def _isqrt(n: int) -> int:
    """Exact integer square root floor(sqrt(n)) for n >= 0 without importing `math`."""
    if type(n) is not int or n < 0:
        raise QError("DOMAIN_ERROR", "isqrt requires non-negative int")
    if n < 2:
        return n
    x = 1 << ((n.bit_length() + 1) >> 1)
    while True:
        y = (x + n // x) >> 1
        if y >= x:
            return x
        x = y


def _floor_dyadic(val: Fraction, prec_bits: int) -> Fraction:
    scale = 1 << prec_bits
    return Fraction((val.numerator * scale) // val.denominator, scale)


def _ceil_dyadic(val: Fraction, prec_bits: int) -> Fraction:
    scale = 1 << prec_bits
    return Fraction(-((-val.numerator * scale) // val.denominator), scale)


def _floor_sig(val: Fraction, sig_bits: int) -> Fraction:
    """Outward floor rounding to at least `sig_bits` significant binary bits (strictly preserves sign)."""
    if val == 0:
        return Fraction(0, 1)
    exp2 = abs(val.numerator).bit_length() - val.denominator.bit_length()
    shift = sig_bits - exp2
    if shift >= 0:
        scale = 1 << shift
        return Fraction((val.numerator * scale) // val.denominator, scale)
    unit = 1 << (-shift)
    return Fraction((val.numerator // (val.denominator * unit)) * unit, 1)


def _ceil_sig(val: Fraction, sig_bits: int) -> Fraction:
    """Outward ceiling rounding to at least `sig_bits` significant binary bits (strictly preserves sign)."""
    if val == 0:
        return Fraction(0, 1)
    exp2 = abs(val.numerator).bit_length() - val.denominator.bit_length()
    shift = sig_bits - exp2
    if shift >= 0:
        scale = 1 << shift
        return Fraction(-((-val.numerator * scale) // val.denominator), scale)
    unit = 1 << (-shift)
    return Fraction(-((-val.numerator) // (val.denominator * unit)) * unit, 1)


@dataclass(frozen=True)
class QI:
    """Closed rational interval `[lo, hi]` with exact `Fraction` endpoints and `lo <= hi`."""

    lo: Fraction
    hi: Fraction

    def __post_init__(self) -> None:
        if type(self.lo) is not Fraction:
            raise QError("TYPE_ERROR", f"QI.lo: expected exact Fraction, got {type(self.lo).__name__}")
        if type(self.hi) is not Fraction:
            raise QError("TYPE_ERROR", f"QI.hi: expected exact Fraction, got {type(self.hi).__name__}")
        if self.lo > self.hi:
            raise QError("INTERVAL_ORDER", f"QI requires lo <= hi, got [{_short_q(self.lo)}, {_short_q(self.hi)}]")

    @classmethod
    def point(cls, x: Fraction) -> QI:
        _require_fraction(x, "QI.point")
        return cls(x, x)

    @classmethod
    def from_ints(cls, lo: int, hi: int) -> QI:
        return cls(q_from_int(lo, "lo"), q_from_int(hi, "hi"))

    @property
    def width(self) -> Fraction:
        return self.hi - self.lo

    @property
    def midpoint(self) -> Fraction:
        return (self.lo + self.hi) / 2

    def contains(self, x: Fraction) -> bool:
        _require_fraction(x, "x")
        return self.lo <= x <= self.hi

    def overlaps(self, other: QI) -> bool:
        if type(other) is not QI:
            raise QError("TYPE_ERROR", f"expected QI, got {type(other).__name__}")
        return self.lo <= other.hi and other.lo <= self.hi

    def is_positive(self) -> bool:
        return self.lo > 0

    def is_nonnegative(self) -> bool:
        return self.lo >= 0

    def excludes_zero(self) -> bool:
        return self.lo > 0 or self.hi < 0

    def outward_round(self, prec_bits: int = _DEFAULT_PREC_BITS) -> QI:
        """Outward round endpoints onto the absolute dyadic grid `2^-prec_bits`."""
        if type(prec_bits) is not int or prec_bits < 8 or prec_bits > MAX_PREC_BITS:
            raise QError("RANGE_ERROR", f"prec_bits must be in [8, {MAX_PREC_BITS}]")
        return QI(_floor_dyadic(self.lo, prec_bits), _ceil_dyadic(self.hi, prec_bits))

    def outward_round_sig(self, sig_bits: int = _DEFAULT_PREC_BITS) -> QI:
        """Outward round endpoints to at least `sig_bits` relative significant bits (preserves strict positivity)."""
        if type(sig_bits) is not int or sig_bits < 8 or sig_bits > MAX_PREC_BITS:
            raise QError("RANGE_ERROR", f"sig_bits must be in [8, {MAX_PREC_BITS}]")
        return QI(_floor_sig(self.lo, sig_bits), _ceil_sig(self.hi, sig_bits))

    def __neg__(self) -> QI:
        return QI(-self.hi, -self.lo)

    def __add__(self, other: QI) -> QI:
        if type(other) is not QI:
            return NotImplemented
        return QI(self.lo + other.lo, self.hi + other.hi)

    def __sub__(self, other: QI) -> QI:
        if type(other) is not QI:
            return NotImplemented
        return QI(self.lo - other.hi, self.hi - other.lo)

    def __mul__(self, other: QI) -> QI:
        if type(other) is not QI:
            return NotImplemented
        products = (
            self.lo * other.lo,
            self.lo * other.hi,
            self.hi * other.lo,
            self.hi * other.hi,
        )
        lo = products[0]
        hi = products[0]
        for prod in products[1:]:
            if prod < lo:
                lo = prod
            if prod > hi:
                hi = prod
        return QI(lo, hi)

    def __truediv__(self, other: QI) -> QI:
        if type(other) is not QI:
            return NotImplemented
        if not other.excludes_zero():
            raise QError("DIV_BY_ZERO_INTERVAL", "cannot divide by interval containing zero")
        recip = QI(Fraction(1, 1) / other.hi, Fraction(1, 1) / other.lo)
        return self * recip


PI_QI = QI(Fraction(103993, 33102), Fraction(355, 113))


def sqrt_q(x: Fraction, *, tol: Fraction = Fraction(1, 10**12)) -> QI:
    """Return a certified rational enclosure `[lo, hi]` with `0 <= lo^2 <= x <= hi^2` and `hi - lo <= tol`."""
    _require_fraction(x, "x")
    _require_fraction(tol, "tol")
    _check_input_bits(x, "x")
    if x < 0:
        raise QError("DOMAIN_ERROR", f"sqrt_q requires x >= 0, got {_short_q(x)}")
    if tol <= 0 or tol < MIN_SQRT_TOL:
        raise QError("RANGE_ERROR", f"sqrt_q requires tol >= 10^-100, got {_short_q(tol)}")
    if x == 0:
        return QI.point(Fraction(0, 1))
    p = x.numerator
    q = x.denominator
    inv_tol = (tol.denominator + tol.numerator - 1) // tol.numerator
    need = (inv_tol + q - 1) // q
    shift = (need - 1).bit_length() if need > 1 else 0
    scale = 1 << shift
    r = _isqrt(p * q * scale * scale)
    denom = q * scale
    lo = Fraction(r, denom)
    hi = Fraction(r + 1, denom) if r * r < p * q * scale * scale else lo
    if not (lo * lo <= x <= hi * hi):
        raise QError("ENCLOSURE_INVARIANT", "sqrt_q failed lo^2 <= x <= hi^2")
    return QI(lo, hi)


def qi_sqrt(iv: QI, *, tol: Fraction = Fraction(1, 10**12)) -> QI:
    """Monotone interval square root on `iv >= 0`."""
    if type(iv) is not QI:
        raise QError("TYPE_ERROR", f"expected QI, got {type(iv).__name__}")
    if iv.lo < 0:
        raise QError("DOMAIN_ERROR", f"qi_sqrt requires iv.lo >= 0, got {_short_q(iv.lo)}")
    lo_iv = sqrt_q(iv.lo, tol=tol)
    hi_iv = sqrt_q(iv.hi, tol=tol)
    return QI(lo_iv.lo, hi_iv.hi)


def _exp_small_nonneg(y: Fraction, terms: int) -> QI:
    """Certified enclosure for exp(y) on `0 <= y <= 1/2` using Taylor sum + geometric tail bound."""
    term = Fraction(1, 1)
    partial = Fraction(1, 1)
    for k in range(1, terms + 1):
        term = term * y / k
        partial += term
    next_term = term * y / (terms + 1)
    # Tail: sum_{j>=0} y^(N+1+j)/(N+1+j)! <= next_term / (1 - y/(N+2)) since 0 <= y <= 1/2 < N+2.
    tail = next_term / (Fraction(1, 1) - y / (terms + 2))
    return QI(partial, partial + tail)


def exp_q(x: Fraction, *, terms: int = 24, prec_bits: int = _DEFAULT_PREC_BITS) -> QI:
    """Certified rational enclosure for `exp(x)` via halving, Taylor remainder, and relative-bit outward squaring.

    Always returns strictly positive `[lo, hi]` (`lo > 0`) for every `|x| <= 500`.
    """
    _require_fraction(x, "x")
    _check_input_bits(x, "x")
    if type(terms) is not int or terms < 4 or terms > MAX_TERMS:
        raise QError("RANGE_ERROR", f"terms must be in [4, {MAX_TERMS}]")
    if type(prec_bits) is not int or prec_bits < 16 or prec_bits > MAX_PREC_BITS:
        raise QError("RANGE_ERROR", f"prec_bits must be in [16, {MAX_PREC_BITS}]")
    if abs(x) > _MAX_EXP_ABS:
        raise QError("RANGE_ERROR", f"|x| exceeds {_MAX_EXP_ABS}")
    if x == 0:
        return QI.point(Fraction(1, 1))
    if x < 0:
        pos = exp_q(-x, terms=terms, prec_bits=prec_bits)
        return QI(Fraction(1, 1) / pos.hi, Fraction(1, 1) / pos.lo).outward_round_sig(prec_bits)
    halvings = 0
    y = x
    half = Fraction(1, 2)
    while y > half:
        y /= 2
        halvings += 1
    work_bits = min(MAX_PREC_BITS, prec_bits + halvings + 16)
    iv = _exp_small_nonneg(y, terms).outward_round_sig(work_bits)
    for _ in range(halvings):
        iv = (iv * iv).outward_round_sig(work_bits)
    return iv.outward_round_sig(prec_bits)


def qi_exp(iv: QI, *, terms: int = 24, prec_bits: int = _DEFAULT_PREC_BITS) -> QI:
    """Monotone interval exponential (always strictly positive)."""
    if type(iv) is not QI:
        raise QError("TYPE_ERROR", f"expected QI, got {type(iv).__name__}")
    lo_iv = exp_q(iv.lo, terms=terms, prec_bits=prec_bits)
    hi_iv = exp_q(iv.hi, terms=terms, prec_bits=prec_bits)
    return QI(lo_iv.lo, hi_iv.hi)


def _ln_reduced(r: Fraction, terms: int) -> QI:
    """Certified enclosure for `ln(r)` on `r in [1/2, 2]` via `atanh` series `2 * sum u^(2k+1)/(2k+1)`."""
    u = (r - Fraction(1, 1)) / (r + Fraction(1, 1))
    if u == 0:
        return QI.point(Fraction(0, 1))
    u2 = u * u
    power = u
    partial = Fraction(0, 1)
    for k in range(terms + 1):
        partial += power / (2 * k + 1)
        power *= u2
    partial *= 2
    abs_tail = 2 * abs(power) / ((2 * terms + 3) * (Fraction(1, 1) - u2))
    if u > 0:
        return QI(partial, partial + abs_tail)
    return QI(partial - abs_tail, partial)


def ln_q(x: Fraction, *, terms: int = 24, prec_bits: int = _DEFAULT_PREC_BITS) -> QI:
    """Certified rational enclosure for `ln(x)` (`x > 0`) via binary reduction and `atanh` remainder."""
    _require_fraction(x, "x")
    _check_input_bits(x, "x")
    if type(terms) is not int or terms < 4 or terms > MAX_TERMS:
        raise QError("RANGE_ERROR", f"terms must be in [4, {MAX_TERMS}]")
    if type(prec_bits) is not int or prec_bits < 16 or prec_bits > MAX_PREC_BITS:
        raise QError("RANGE_ERROR", f"prec_bits must be in [16, {MAX_PREC_BITS}]")
    if x <= 0:
        raise QError("DOMAIN_ERROR", f"ln_q requires x > 0, got {_short_q(x)}")
    if x == 1:
        return QI.point(Fraction(0, 1))
    shift = x.numerator.bit_length() - x.denominator.bit_length()
    if shift >= 0:
        r = x / Fraction(1 << shift, 1)
    else:
        r = x * Fraction(1 << (-shift), 1)
    while r > Fraction(2, 1):
        r /= 2
        shift += 1
    while r < Fraction(1, 2):
        r *= 2
        shift -= 1
    work_bits = min(MAX_PREC_BITS, prec_bits + 16)
    ln_r = _ln_reduced(r, terms).outward_round_sig(work_bits)
    if shift == 0:
        return ln_r.outward_round_sig(prec_bits)
    ln_2 = _ln_reduced(Fraction(2, 1), terms).outward_round_sig(work_bits)
    total = QI.point(Fraction(shift, 1)) * ln_2 + ln_r
    return total.outward_round_sig(prec_bits)


def qi_ln(iv: QI, *, terms: int = 24, prec_bits: int = _DEFAULT_PREC_BITS) -> QI:
    """Monotone interval natural logarithm on `iv > 0`."""
    if type(iv) is not QI:
        raise QError("TYPE_ERROR", f"expected QI, got {type(iv).__name__}")
    if iv.lo <= 0:
        raise QError("DOMAIN_ERROR", f"qi_ln requires iv.lo > 0, got {_short_q(iv.lo)}")
    lo_iv = ln_q(iv.lo, terms=terms, prec_bits=prec_bits)
    hi_iv = ln_q(iv.hi, terms=terms, prec_bits=prec_bits)
    return QI(lo_iv.lo, hi_iv.hi)


def qi_pow(base: QI, exponent: QI, *, terms: int = 24, prec_bits: int = _DEFAULT_PREC_BITS) -> QI:
    """Certified interval power `base^exponent = exp(exponent * ln(base))` for strictly positive bases (`base.lo > 0`).

    Non-positive bases (including integer powers of negative bases) are intentionally unsupported and fail closed.
    """
    if type(base) is not QI or type(exponent) is not QI:
        raise QError("TYPE_ERROR", "qi_pow requires QI arguments")
    if base.lo <= 0:
        raise QError("DOMAIN_ERROR", f"qi_pow requires base.lo > 0, got {_short_q(base.lo)}")
    return qi_exp(exponent * qi_ln(base, terms=terms, prec_bits=prec_bits), terms=terms, prec_bits=prec_bits)
