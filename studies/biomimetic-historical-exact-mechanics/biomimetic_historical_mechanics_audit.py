#!/usr/bin/env python3
"""Pure-Z/Q Biomimetic x Global-Historical Structural & Hydraulic Unification Audit.

Strictly add-only pure-stdlib (`int` + strict 2-arg `fractions.Fraction`) study
for `aska-physical/optifab` classifying exact structural isomorphisms, exact
Schur/Sylvester inertia equivalences, and provable algebraic obstructions across
biomimetic and classical civil-engineering mechanics:
  - U1: Cascaded leaky weir statics (beaver-dam cascade vs. Petra Siq 36-basin
        stepped conduit & Roman Lyon Gier 9-pipe siphon) + provable obstructions
        against nonlinear non-reciprocal Belanger hydraulic jumps (Machu Picchu /
        Tipon) and state-dependent choke/piping conductance feedback.
  - U2: Exact identity-bijection graph isomorphism between the 2-ring 6-spoke
        orb-web lattice G_orb(6,2) and the Amazonian Casarabe C_{2,6} causeway
        network (n=13, m=24, beta_1=12), unified beta_1 >= 1 passive Kirchhoff
        circulation & cut survival, plus provable obstructions for non-symmetric
        upwind convective transport (A != A^T) and weighted stiffness-hierarchy
        LODF non-invariance (kappa = 100).
  - U3: Discrete SPD Volkersen shear-lag & perforation-tear interior optimum
        (tailorbird stitched seam / CFRP anchor arrays) vs. East Asian Dougong
        bilinear Coulomb friction hysteresis and Housner dry-stone rocking, with
        provable zero-cyclic-work and perforation-cliff obstructions.
  - U4: Equal-order 8x8 Sylvester inertia non-congruence separating passive
        hydraulic/structural M-matrices (neg == 0, matching `optifab/q/inertia.py`
        `Inertia(pos,neg,zero)`, e.g. 8x8 anchored tension-only orb web `(8, 0, 0)`
        and 13x13 Casarabe PSD Laplacian `(12, 0, 1)`) from 8x8 H_8 indefinite
        auxetic fold-sheaf Hessians `(4, 4, 0)`, 8x8 compressed-cable buckling
        `(0, 8, 0)`, and 2x2 hyperbolic pivots `(1, 1, 0)`.
  - U5: Euplectella 4x4 cylindrical checkerboard bracing Maxwell-Calladine
        rank-nullity & exact Z/2Z zigzag parity obstruction (eliminated by a
        single parity-breaking bridge or continuous longitudinal spicules).
  - U6: Hardened self-certifying AST zero-float guard (rejecting float/complex
        literals, `ast.Div`/`FloorDiv`/`Mod`, unsafe `ast.Pow`, unsafe or rebound
        `Fraction(...)`, float/format/dunder calls, and unlisted module imports) +
        strict `MODEL` / `CHECKER` scope declaration.

Zero floats on trust paths. Zero `ast.Div`/`FloorDiv`/`Mod`. Zero `import math`.
Zero bare `assert`s. Zero uncontrolled laptop energy claims.
"""

from __future__ import annotations

import argparse
import ast
from fractions import Fraction
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple
import unicodedata

SCHEMA_ID = "aska-physical.optifab.biomimetic-historical-exact-mechanics.v1"
CLAIM_SCOPE = "model_and_checker_only_no_bench_measurement"
ENERGY_POLICY_STATUS = "UNCONTROLLED_LAPTOP_NOT_CLAIMED"

MAX_JSON_DEPTH = 24
MAX_JSON_BYTES = 1_048_576
MAX_STRING_CHARS = 16_384
MAX_INT_DIGITS = 400
MAX_SAFE_POW_EXP = 64
MAX_MATRIX_DIM = 48
MAX_GRAPH_EDGES = 64

_HEX_LOWER = frozenset("0123456789abcdef")
_CERT_KEYS = frozenset((
    "schema",
    "claim_scope",
    "energy_power_status",
    "payload",
    "payload_sha256",
    "certificate_sha256",
))
_ALLOWED_IMPORTS = frozenset((
    "__future__",
    "argparse",
    "ast",
    "fractions",
    "hashlib",
    "hmac",
    "json",
    "os",
    "pathlib",
    "re",
    "stat",
    "sys",
    "typing",
    "unicodedata",
))
_ALLOWED_OS_ATTRS = frozenset((
    "open",
    "fstat",
    "read",
    "write",
    "close",
    "O_RDONLY",
    "O_WRONLY",
    "O_CREAT",
    "O_TRUNC",
    "O_NOFOLLOW",
    "O_NONBLOCK",
))
_FORBIDDEN_CALLS = frozenset((
    "float",
    "complex",
    "round",
    "format",
    "format_map",
    "__format__",
    "divmod",
    "__divmod__",
    "__rdivmod__",
    "eval",
    "exec",
    "from_float",
    "from_decimal",
    "fromhex",
    "as_integer_ratio",
    "memoryview",
    "truediv",
    "rtruediv",
    "itruediv",
    "__truediv__",
    "__rtruediv__",
    "__itruediv__",
    "floordiv",
    "__floordiv__",
    "__rfloordiv__",
    "__ifloordiv__",
    "__mod__",
    "__rmod__",
    "__imod__",
    "pow",
    "rpow",
    "ipow",
    "__pow__",
    "__rpow__",
    "__ipow__",
    "__float__",
    "__complex__",
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "vars",
    "__import__",
    "literal_eval",
    "open",
    "conjugate",
    "system",
    "popen",
    "fork",
    "log",
    "log2",
    "log10",
    "exp",
    "sqrt",
))
_FORBIDDEN_ATTRS = frozenset((
    "__truediv__",
    "__rtruediv__",
    "__itruediv__",
    "__floordiv__",
    "__rfloordiv__",
    "__ifloordiv__",
    "__mod__",
    "__rmod__",
    "__imod__",
    "__divmod__",
    "__rdivmod__",
    "__format__",
    "format",
    "format_map",
    "__pow__",
    "__rpow__",
    "__ipow__",
    "__float__",
    "__complex__",
    "__builtins__",
    "__globals__",
    "__subclasses__",
    "__getattribute__",
    "__dict__",
    "__class__",
    "__base__",
    "__bases__",
    "__mro__",
    "__loader__",
    "__spec__",
    "real",
    "imag",
    "conjugate",
    "modules",
    "float_info",
    "meta_path",
    "path_hooks",
    "path_importer_cache",
    "_getframe",
    "system",
    "popen",
    "fork",
    "pi",
    "tau",
    "inf",
    "nan",
    "from_float",
    "from_decimal",
    "fromhex",
    "as_integer_ratio",
    "literal_eval",
))
_FORBIDDEN_NAMES = frozenset((
    "__builtins__",
    "builtins",
    "getattr",
    "setattr",
    "delattr",
    "eval",
    "exec",
    "compile",
    "__import__",
    "globals",
    "locals",
    "vars",
    "round",
    "format",
    "divmod",
    "pow",
    "open",
    "memoryview",
))
_FORBIDDEN_IMPORTED_SYMBOLS = _FORBIDDEN_CALLS | _FORBIDDEN_NAMES | _FORBIDDEN_ATTRS

# Reference Energy-Claim Value Guard (NFKC -> NFKD -> strip Cf/Mn -> casefold)
# with strictly O(N) non-overlapping _NUM/_SEP quantifiers (zero ReDoS backtracking).
_CAMEL_BOUNDARY_RE = re.compile(r"([a-z0-9])([A-Z])")
_KEY_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PFX = r"(?:p|n|u|\u03bc|m|k|g|t|pico|nano|micro|milli|kilo|mega|giga|tera)"
_UNIT_MULTI = r"(?:watt[^a-z0-9]{0,4}hours?|watthours?|wattage|watts?|joules?|whrs?|wh|tdp|hp)"
_UNIT = rf"(?:{_UNIT_MULTI}|w|j)"
_SEP = r"[^a-z0-9.,]{0,8}"
_NUM = r"(?:(?<![0-9a-f])0x[0-9a-f]+|(?<![0-9])(?<!\d[.,])\d+(?:[.,]\d+){0,4}(?:e[+-]?\d+)?)"
_DEC_NUM = r"(?<![0-9])\d+[.,]\d+(?:e[+-]?\d+)?"
_NUM_WORD = (
    r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion)"
)
_SPELLED_NUM = rf"(?<![a-z0-9]){_NUM_WORD}(?:[-\s]{{0,4}}{_NUM_WORD}){{0,3}}(?![a-z0-9])"
ENERGY_VALUE_RE = re.compile(
    "(?:"
    rf"{_NUM}{_SEP}(?:{_PFX}{_SEP})?{_UNIT}(?![a-z0-9])(?!/\s)(?!/o(?![a-z0-9]))"
    rf"|{_NUM}{_SEP}(?:m|k)?(?:amps?|a)(?![a-z0-9])[^0-9]{{1,16}}{_NUM}{_SEP}(?:m|k)?(?:volts?|v)(?![a-z0-9])"
    rf"|{_NUM}{_SEP}(?:m|k)?(?:volts?|v)(?![a-z0-9])[^0-9]{{1,16}}{_NUM}{_SEP}(?:m|k)?(?:amps?|a)(?![a-z0-9])"
    rf"|{_SPELLED_NUM}\s+(?:(?:{_PFX}{_SEP})?{_UNIT_MULTI}|{_PFX}{_SEP}(?:w|j))(?![a-z0-9])"
    rf"|(?<![a-z0-9])(?:energy|power|wattage)(?:\s*[:=]\s*|\s+){_NUM}"
    rf"|(?<![a-z0-9])(?:(?:{_PFX}{_SEP})?{_UNIT_MULTI}|{_PFX}{_SEP}(?:w|j))\s*[:=]\s*{_NUM}"
    rf"|(?<![a-z0-9])(?:w|j)\s*(?::\s*{_NUM}|=\s*{_DEC_NUM})"
    rf"|(?<![a-z0-9])tdp{_SEP}{_NUM}"
    rf"|^[^a-z0-9]*(?:{_PFX}{_SEP})?{_UNIT}[^a-z0-9]*$"
    rf"|\b(?:energy|power|wattage|joules?|watts?|(?:{_PFX}{_SEP})(?:whrs?|wh|w|j)|whrs?|wh|j)\s*(?:per|/)\s*tok(?:en)?s?\b"
    rf"|\bw(?:\s+per\s+|/)tok(?:en)?s?\b"
    rf"|{_NUM}{_SEP}w\s*/\s*tok(?:en)?s?\b"
    rf"|(?<![a-z0-9])tok(?:en)?s?(?:\s*(?:per|/)\s*|_per_)(?:{_PFX}{_SEP})?(?:joules?|j|watts?|wh|kwh)(?![a-z0-9])"
    r"|\b(?:less|lower|reduced|fewer)\s+(?:in\s+)?(?:energy|power)\b"
    r"|\b(?:energy|power|wattage)\s+(?:use|usage|reduction|savings?|dropped|consumption|draw|limit|budget)\b"
    r"|(?<![a-z0-9])(?:rapl|nvml|nvidia[^a-z0-9]{0,4}smi(?![a-z0-9]))"
    ")"
)
_FORBIDDEN_GLUED_KEY_TOKEN_RE = re.compile(
    rf"^(?:{_PFX}(?:watthours?|wattage|watts?|joules?|whrs?|wh|w|j)"
    r"|(?:power|energy|watt|wattage|joule)(?:draw|usage|use|used|limit|cap|avg|mean|min|max|sum|total|budget|consumption|saving|savings|drop|sensor|reading|telemetry)s?"
    r"|(?:draw|limit|cap|avg|mean|min|max|total)(?:watts?|wattage|joules?|power|energy|kwh|whrs?|wh))$"
)
LEAK_VALUE_RE = re.compile(
    r"(?:"
    r"/" + r"home/"
    r"|/" + r"users/"
    r"|/" + r"root/"
    r"|\$home(?![a-z0-9_])"
    r"|c:[\\/]" + r"users[\\/]"
    r"|(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}"
    r"|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}"
    r")"
)
FORBIDDEN_KEY_TOKENS = frozenset((
    "rapl",
    "nvml",
    "energy",
    "power",
    "watt",
    "watts",
    "wattage",
    "watthour",
    "watthours",
    "joule",
    "joules",
    "tdp",
    "kwh",
    "whr",
    "whrs",
    "wh",
    "mw",
    "kw",
    "uw",
    "nw",
    "pw",
    "gw",
    "tw",
    "mj",
    "uj",
    "nj",
    "pj",
    "kj",
    "gj",
    "tj",
    "w",
    "j",
    "hp",
))
_ALLOWED_MODEL_ENERGY_KEYS = frozenset((
    "energy_power_status",
    "ventilation_tree_power_q",
    "ventilation_ring_power_q",
    "ventilation_casarabe_power_q",
    "pin_checker1_torsion_energy_q",
    "pin_checker1_zigzag_energy_q",
    "tailorbird_w_cap_star_q",
))


class MechanicsAuditError(ValueError):
    """Fail-closed typed error (never stripped under python3 -O)."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"[{code}] {detail}")


def require_ok(cond: bool, code: str, detail: str) -> None:
    if not cond:
        raise MechanicsAuditError(code, detail)


# ---------------------------------------------------------------------------
# Pure-Z/Q Arithmetic, Strict JSON, Energy/Leak Guard, & AST Zero-Float Guard
# ---------------------------------------------------------------------------


def is_hex64(val: Any) -> bool:
    return (
        type(val) is str
        and len(val) == 64
        and all(ch in _HEX_LOWER for ch in val)
    )


def require_int(val: Any, label: str, lo: Optional[int] = None, hi: Optional[int] = None) -> int:
    require_ok(type(val) is int, "BAD_INT", f"{label} must be strict int")
    if lo is not None:
        require_ok(val >= lo, "INT_LOW", f"{label} < {lo}")
    if hi is not None:
        require_ok(val <= hi, "INT_HIGH", f"{label} > {hi}")
    return val


def require_frac(val: Any, label: str) -> Fraction:
    require_ok(type(val) is Fraction, "BAD_FRAC", f"{label} must be strict Fraction")
    return val


def require_pos_frac(val: Any, label: str) -> Fraction:
    q = require_frac(val, label)
    require_ok(q.numerator > 0, "NON_POS_FRAC", f"{label} must be > 0")
    return q


def q_frac(num: int, den: int) -> Fraction:
    n = require_int(num, "num")
    d = require_int(den, "den")
    require_ok(d != 0, "ZERO_DEN", "denominator must be nonzero")
    return Fraction(n, d)


def q_div(a: Fraction, b: Fraction) -> Fraction:
    """Exact pure-integer Fraction division without Python's `ast.Div` (`/`)."""
    qa = require_frac(a, "a")
    qb = require_frac(b, "b")
    require_ok(qb.numerator != 0, "ZERO_DIV", "division by zero")
    return Fraction(qa.numerator * qb.denominator, qa.denominator * qb.numerator)


def fmt_q(q: Fraction) -> str:
    r = require_frac(q, "q")
    return f"{r.numerator}/{r.denominator}"


def inertia_dict(triple: Tuple[int, int, int]) -> Dict[str, int]:
    """Named Sylvester inertia record matching `optifab/q/inertia.py` convention."""
    return {"pos": triple[0], "neg": triple[1], "zero": triple[2]}


def int_comb(n: int, k: int) -> int:
    nn = require_int(n, "n", lo=0)
    kk = require_int(k, "k", lo=0, hi=nn)
    kk = min(kk, nn - kk)
    acc = Fraction(1, 1)
    for i in range(1, kk + 1):
        acc = acc * Fraction(nn - kk + i, i)
    return acc.numerator


def wrap_index(idx: int, mod: int) -> int:
    """Exact cyclic index reduction on [-mod, 2*mod) without ast.Mod (`%`)."""
    i = require_int(idx, "idx")
    m = require_int(mod, "mod", lo=1, hi=MAX_MATRIX_DIM)
    require_ok(-m <= i < 2 * m, "IDX_RANGE", "idx out of single-wrap range")
    if i < 0:
        return i + m
    if i >= m:
        return i - m
    return i


def _atan_inv_partial_q(inv_x: int, terms: int) -> Fraction:
    """Alternating Taylor partial sum for arctan(1/inv_x) over exact Q (zero ast.Div)."""
    m = require_int(inv_x, "inv_x", lo=2)
    t = require_int(terms, "terms", lo=1, hi=32)
    acc = Fraction(0, 1)
    pow_m = m
    m2 = m * m
    for k in range(t):
        term = Fraction(1, (2 * k + 1) * pow_m)
        if (k & 1) == 0:
            acc += term
        else:
            acc -= term
        pow_m *= m2
    return acc


def machin_pi_bracket_q() -> Tuple[Fraction, Fraction]:
    """First-principles pure-Q Machin alternating-series bracket: PI_LO < pi < PI_HI."""
    lo = Fraction(16, 1) * _atan_inv_partial_q(5, 12) - Fraction(4, 1) * _atan_inv_partial_q(239, 5)
    hi = Fraction(16, 1) * _atan_inv_partial_q(5, 13) - Fraction(4, 1) * _atan_inv_partial_q(239, 4)
    return lo, hi


PI_LO, PI_HI = machin_pi_bracket_q()


def normalize_text(text: str) -> str:
    require_ok(type(text) is str, "BAD_TEXT", "Expected str")
    s = unicodedata.normalize("NFKD", unicodedata.normalize("NFKC", text))
    return "".join(
        ch for ch in s if unicodedata.category(ch) not in ("Cf", "Mn")
    ).casefold()


def has_non_ascii_letter(text: str) -> bool:
    require_ok(type(text) is str, "BAD_TEXT", "Expected str")
    return any(
        not ch.isascii() and ch.isalpha() and ch not in ("\u03bc", "\u00b5")
        for ch in text
    )


def is_forbidden_energy_value(text: str) -> bool:
    n = normalize_text(text)
    return has_non_ascii_letter(n) or bool(ENERGY_VALUE_RE.search(n))


def is_forbidden_energy_key(key: str) -> bool:
    require_ok(type(key) is str, "BAD_KEY", "JSON key must be str")
    if key in _ALLOWED_MODEL_ENERGY_KEYS:
        return False
    spaced = _CAMEL_BOUNDARY_RE.sub(r"\1 \2", key).replace("_", " ")
    if is_forbidden_energy_value(spaced):
        return True
    norm = normalize_text(spaced)
    tokens = set(_KEY_TOKEN_RE.findall(norm))
    if tokens & FORBIDDEN_KEY_TOKENS:
        return True
    return any(bool(_FORBIDDEN_GLUED_KEY_TOKEN_RE.match(tok)) for tok in tokens)


def validate_json_value(root: Any, max_depth: int = MAX_JSON_DEPTH) -> None:
    """Iterative zero-float, depth-capped, digit-capped, energy/leak-guarded JSON validator."""
    lim = require_int(max_depth, "max_depth", lo=0, hi=MAX_JSON_DEPTH)
    max_int = int("9" * MAX_INT_DIGITS)
    stack: List[Tuple[Any, int]] = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        require_ok(depth <= lim, "JSON_DEPTH", "JSON nesting depth exceeded")
        if type(node) is dict:
            for k, v in node.items():
                require_ok(not is_forbidden_energy_key(k), "FORBIDDEN_ENERGY_KEY", f"Forbidden key {k}")
                require_ok(not LEAK_VALUE_RE.search(normalize_text(k)), "FORBIDDEN_LEAK", "Forbidden token in key")
                stack.append((v, depth + 1))
        elif type(node) is list:
            for item in node:
                stack.append((item, depth + 1))
        elif type(node) is int:
            require_ok(abs(node) <= max_int, "INT_TOO_LARGE", "Integer exceeds digit cap")
        elif type(node) is str:
            require_ok(len(node) <= MAX_STRING_CHARS, "STRING_TOO_LARGE", "String exceeds character cap")
            require_ok(not is_forbidden_energy_value(node), "FORBIDDEN_ENERGY_VALUE", "Forbidden energy/homoglyph value")
            require_ok(not LEAK_VALUE_RE.search(normalize_text(node)), "FORBIDDEN_LEAK", "Forbidden host path/MAC/email")
        elif type(node) is bool or node is None:
            continue
        elif type(node) is float:
            raise MechanicsAuditError("FLOAT_FORBIDDEN", "IEEE-754 floats are forbidden on trust paths")
        else:
            raise MechanicsAuditError("BAD_JSON_TYPE", "Unsupported JSON value type")


def _reject_float_tok(tok: str) -> Any:
    raise MechanicsAuditError("JSON_FLOAT_FORBIDDEN", f"Float literal forbidden: {tok}")


def _reject_const_tok(tok: str) -> Any:
    raise MechanicsAuditError("JSON_CONST_FORBIDDEN", f"Constant literal forbidden: {tok}")


def _parse_int_tok(tok: str) -> int:
    require_ok(tok != "-0", "NEG_ZERO_FORBIDDEN", "Negative zero integer token -0 is forbidden")
    digits = tok[1:] if tok.startswith("-") else tok
    require_ok(
        all((1 <= len(digits) <= MAX_INT_DIGITS, all("0" <= ch <= "9" for ch in digits))),
        "INT_DIGIT_LIMIT",
        "Integer must be ASCII decimal within digit cap",
    )
    return int(tok)


def _no_dup_pairs(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in pairs:
        require_ok(k not in out, "JSON_DUP_KEY", f"Duplicate JSON key: {k}")
        out[k] = v
    return out


def parse_strict_json(text: str) -> Any:
    require_ok(type(text) is str, "BAD_JSON_INPUT", "JSON input must be str")
    require_ok(len(text.encode("utf-8")) <= MAX_JSON_BYTES, "JSON_TOO_LARGE", "JSON exceeds byte cap")
    try:
        parsed = json.loads(
            text,
            parse_int=_parse_int_tok,
            parse_float=_reject_float_tok,
            parse_constant=_reject_const_tok,
            object_pairs_hook=_no_dup_pairs,
        )
    except MechanicsAuditError:
        raise
    except (ValueError, TypeError, RecursionError) as exc:
        raise MechanicsAuditError("JSON_PARSE_ERR", str(exc)) from exc
    validate_json_value(parsed)
    return parsed


def canonical_json_bytes(obj: Any) -> bytes:
    validate_json_value(obj)
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def render_certificate_bytes(cert: Dict[str, Any]) -> bytes:
    validate_json_value(cert)
    return (json.dumps(cert, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def _reject_symlink_components(path: Path, err_code: str) -> None:
    """Reject symlink leaf or any symlinked ancestor component without resolving."""
    cur = path
    while True:
        require_ok(not cur.is_symlink(), err_code, "Symlink path or ancestor component is forbidden")
        parent = cur.parent
        if parent == cur:
            break
        cur = parent


def _read_regular_bytes_nofollow(path: Path, max_bytes: int, err_code: str) -> bytes:
    """Atomically open a regular non-symlink file via O_NOFOLLOW + fstat and read up to max_bytes."""
    require_ok(isinstance(path, Path), err_code, "path must be pathlib.Path")
    _reject_symlink_components(path, err_code)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise MechanicsAuditError(err_code, f"Failed to open non-symlink file: {exc}") from exc
    try:
        st = os.fstat(fd)
        require_ok(stat.S_ISREG(st.st_mode), err_code, "Target must be a regular file")
        chunks: List[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            total += len(chunk)
            require_ok(total <= max_bytes, err_code, "File exceeds byte cap")
            chunks.append(chunk)
        return b"".join(chunks)
    except OSError as exc:
        raise MechanicsAuditError(err_code, f"Failed to read file descriptor: {exc}") from exc
    finally:
        os.close(fd)


def _read_source_file(path: Path) -> Tuple[str, str]:
    """Read a regular non-symlink LF-only UTF-8 Python source file and return (text, sha256)."""
    raw = _read_regular_bytes_nofollow(path, MAX_JSON_BYTES, "BAD_SELF_SOURCE")
    require_ok(b"\r" not in raw, "BAD_SELF_SOURCE", "Verifier source must use LF line endings")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MechanicsAuditError("BAD_SELF_SOURCE", f"Invalid UTF-8 in source: {exc}") from exc
    return text, hashlib.sha256(raw).hexdigest()


def audit_source_zero_float_ast(
    source_text: str,
    raise_on_violation: bool = True,
) -> Dict[str, bool]:
    """Counter-derived AST guard rejecting floats, ast.Div, unsafe ast.Pow, bare assert, unsafe Fraction, and dynamic/dunder escapes."""
    require_ok(type(source_text) is str, "BAD_SOURCE", "source_text must be str")
    require_ok(type(raise_on_violation) is bool, "BAD_BOOL", "raise_on_violation must be bool")
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        raise MechanicsAuditError("AST_SYNTAX_ERR", str(exc)) from exc

    violations: List[Tuple[str, str]] = []
    stmt_count = len(tree.body)
    if stmt_count == 0:
        violations.append(("AST_EMPTY", "Parsed AST contains zero statements"))

    max_ast_int = int("9" * MAX_INT_DIGITS)
    float_literals = 0
    ast_divs = 0
    unsafe_pows = 0
    unsafe_fractions = 0
    float_imports = 0
    float_calls = 0
    bare_asserts = 0
    dynamic_escapes = 0

    allowed_name_ids = set()
    for node in ast.walk(tree):
        ann_roots: List[ast.AST] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is not None:
            ann_roots.append(node.returns)
        elif isinstance(node, ast.arg) and node.annotation is not None:
            ann_roots.append(node.annotation)
        elif isinstance(node, ast.AnnAssign):
            ann_roots.append(node.annotation)
        for root in ann_roots:
            if not any(isinstance(sub, ast.NamedExpr) for sub in ast.walk(root)):
                for sub in ast.walk(root):
                    if isinstance(sub, ast.Name) and sub.id == "Fraction":
                        allowed_name_ids.add(id(sub))
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "Fraction":
                allowed_name_ids.add(id(node.func))
            elif (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "fractions"
                and node.func.attr == "Fraction"
            ):
                allowed_name_ids.add(id(node.func))
        elif (
            isinstance(node, ast.Compare)
            and len(node.ops) == 1
            and isinstance(node.ops[0], (ast.Is, ast.IsNot))
        ):
            if (
                isinstance(node.comparators[0], ast.Name)
                and node.comparators[0].id in ("Fraction", "float", "complex")
            ):
                allowed_name_ids.add(id(node.comparators[0]))
            if (
                isinstance(node.left, ast.Call)
                and isinstance(node.left.func, ast.Name)
                and node.left.func.id == "type"
                and len(node.left.args) == 1
                and not isinstance(node.left.args[0], ast.Starred)
                and len(node.left.keywords) == 0
            ):
                allowed_name_ids.add(id(node.left.func))
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in ("sys", "os", "fractions", "json"):
                allowed_name_ids.add(id(node.value))

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if type(node.value) is float or type(node.value) is complex:
                float_literals += 1
                violations.append(("AST_FLOAT_LITERAL", "Float/complex literal forbidden"))
            elif type(node.value) is int and abs(node.value) > max_ast_int:
                unsafe_pows += 1
                violations.append(("AST_UNSAFE_POW", "Integer literal exceeds MAX_INT_DIGITS"))
        elif isinstance(node, ast.FormattedValue) and node.format_spec is not None:
            float_calls += 1
            violations.append(("AST_FLOAT_CALL", "f-string format_spec is forbidden"))
        elif isinstance(node, ast.Assert):
            bare_asserts += 1
            violations.append(("AST_ASSERT_FORBIDDEN", "Bare assert statement is forbidden"))
        elif isinstance(node, (ast.Div, ast.FloorDiv, ast.Mod)):
            ast_divs += 1
            violations.append(("AST_DIV_FORBIDDEN", "Division/modulo operator (`/`, `//`, `%`) is forbidden"))
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            exp_node = node.right
            base_is_pow = isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Pow)
            exp_ok = (
                isinstance(exp_node, ast.Constant)
                and type(exp_node.value) is int
                and 0 <= exp_node.value <= MAX_SAFE_POW_EXP
            )
            if base_is_pow or not exp_ok:
                unsafe_pows += 1
                violations.append((
                    "AST_UNSAFE_POW",
                    f"Exponentiation (`**`) requires non-nested integer literal exponent in [0, {MAX_SAFE_POW_EXP}]",
                ))
        elif isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Pow):
            unsafe_pows += 1
            violations.append(("AST_UNSAFE_POW", "In-place exponentiation (`**=`) is forbidden"))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                root_mod = alias.name.split(".")[0]
                if root_mod not in _ALLOWED_IMPORTS:
                    float_imports += 1
                    violations.append(("AST_FLOAT_IMPORT", f"Disallowed module import: {alias.name}"))
                elif root_mod in ("sys", "os", "fractions", "json") and alias.asname is not None:
                    dynamic_escapes += 1
                    violations.append(("AST_DYNAMIC_ESCAPE", f"Aliasing {root_mod} import is forbidden"))
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                dynamic_escapes += 1
                violations.append(("AST_DYNAMIC_ESCAPE", "Relative import is forbidden"))
            mod = (node.module or "").split(".")[0]
            if mod not in _ALLOWED_IMPORTS:
                float_imports += 1
                violations.append(("AST_FLOAT_IMPORT", f"Disallowed from-import: {node.module}"))
            elif mod in ("sys", "os", "json"):
                dynamic_escapes += 1
                violations.append(("AST_DYNAMIC_ESCAPE", f"from-{mod} import is forbidden"))
            for alias in node.names:
                if alias.name in _FORBIDDEN_IMPORTED_SYMBOLS:
                    dynamic_escapes += 1
                    violations.append(("AST_DYNAMIC_ESCAPE", f"Forbidden imported symbol: {alias.name}"))
                if mod == "fractions" and alias.asname is not None:
                    float_imports += 1
                    violations.append(("AST_FRACTION_ALIAS", "Aliasing fractions imports is forbidden"))
        elif isinstance(node, ast.Name):
            if node.id in _FORBIDDEN_NAMES:
                dynamic_escapes += 1
                violations.append(("AST_DYNAMIC_ESCAPE", f"Forbidden dynamic builtin reference: {node.id}"))
            elif node.id == "Fraction" and id(node) not in allowed_name_ids:
                unsafe_fractions += 1
                violations.append(("AST_UNSAFE_FRACTION", "Rebinding or first-class reference to Fraction is forbidden"))
            elif node.id in ("float", "complex") and id(node) not in allowed_name_ids:
                float_calls += 1
                violations.append(("AST_FLOAT_CALL", f"Rebinding or first-class reference to {node.id} is forbidden"))
            elif node.id in ("sys", "os", "fractions", "json", "type") and id(node) not in allowed_name_ids:
                dynamic_escapes += 1
                violations.append(("AST_DYNAMIC_ESCAPE", f"Rebinding or unsanctioned reference to {node.id} is forbidden"))
        elif isinstance(node, ast.Attribute):
            if node.attr in _FORBIDDEN_ATTRS:
                dynamic_escapes += 1
                violations.append(("AST_DYNAMIC_ESCAPE", f"Forbidden attribute access: {node.attr}"))
            elif (
                isinstance(node.value, ast.Name)
                and node.value.id == "os"
                and node.attr not in _ALLOWED_OS_ATTRS
            ):
                dynamic_escapes += 1
                violations.append(("AST_DYNAMIC_ESCAPE", f"Disallowed os attribute: {node.attr}"))
            elif node.attr == "Fraction" and id(node) not in allowed_name_ids:
                unsafe_fractions += 1
                violations.append(("AST_UNSAFE_FRACTION", "Non-fractions.Fraction attribute is forbidden"))
        elif isinstance(node, ast.Call):
            fn = node.func
            call_name = ""
            is_os_open = (
                isinstance(fn, ast.Attribute)
                and isinstance(fn.value, ast.Name)
                and fn.value.id == "os"
                and fn.attr == "open"
            )
            if isinstance(fn, ast.Name):
                call_name = fn.id
            elif isinstance(fn, ast.Attribute) and not is_os_open:
                call_name = fn.attr
            if call_name in _FORBIDDEN_CALLS:
                float_calls += 1
                violations.append(("AST_FLOAT_CALL", f"Forbidden call: {call_name}"))
            elif call_name == "loads":
                kw_map = {kw.arg: kw.value for kw in node.keywords if kw.arg is not None}
                pf = kw_map.get("parse_float")
                pc = kw_map.get("parse_constant")
                pi = kw_map.get("parse_int")
                if (
                    pf is None
                    or pc is None
                    or pi is None
                    or (isinstance(pf, ast.Constant) and pf.value is None)
                    or (isinstance(pc, ast.Constant) and pc.value is None)
                    or (isinstance(pi, ast.Constant) and pi.value is None)
                ):
                    float_calls += 1
                    violations.append((
                        "AST_FLOAT_CALL",
                        "json.loads() requires explicit non-None parse_int, parse_float, and parse_constant",
                    ))
            if call_name == "Fraction":
                if len(node.args) != 2 or len(node.keywords) != 0:
                    unsafe_fractions += 1
                    violations.append(("AST_UNSAFE_FRACTION", "Fraction() must use strict 2-arg integer form Fraction(num, den)"))
                else:
                    for arg in node.args:
                        if isinstance(arg, ast.Starred) or (
                            isinstance(arg, ast.Constant) and type(arg.value) is not int
                        ):
                            unsafe_fractions += 1
                            violations.append(("AST_UNSAFE_FRACTION", "Fraction() arguments must be unstarred exact ints"))

    if raise_on_violation and violations:
        raise MechanicsAuditError(violations[0][0], violations[0][1])

    return {
        "has_nonempty_ast": stmt_count > 0,
        "zero_float_literals": float_literals == 0,
        "zero_ast_div": ast_divs == 0,
        "zero_unsafe_pow": unsafe_pows == 0,
        "zero_unsafe_fraction_calls": unsafe_fractions == 0,
        "zero_float_imports": float_imports == 0,
        "zero_float_calls": float_calls == 0,
        "zero_bare_asserts": bare_asserts == 0,
        "zero_dynamic_escapes": dynamic_escapes == 0,
    }


# ---------------------------------------------------------------------------
# Pure-Q Exact Linear Algebra (Zero ast.Div, Zero Floats)
# ---------------------------------------------------------------------------


def solve_linear_multi_q(
    matrix: Sequence[Sequence[Fraction]],
    rhs_rows: Sequence[Sequence[Fraction]],
) -> List[List[Fraction]]:
    """Exact Gauss-Jordan multi-RHS linear solver A X = B over Q (zero ast.Div)."""
    n = len(matrix)
    require_ok(1 <= n <= MAX_MATRIX_DIM, "BAD_DIM", "Matrix dimension out of range")
    require_ok(len(rhs_rows) == n, "DIM_MISMATCH", "RHS row count mismatch")
    m_rhs = len(rhs_rows[0])
    require_ok(1 <= m_rhs <= MAX_MATRIX_DIM, "BAD_DIM", "RHS column count out of range")

    aug: List[List[Fraction]] = []
    for i in range(n):
        require_ok(len(matrix[i]) == n and len(rhs_rows[i]) == m_rhs, "RAGGED_MAT", "Ragged matrix/RHS")
        aug.append(
            [require_frac(x, "A") for x in matrix[i]]
            + [require_frac(y, "B") for y in rhs_rows[i]]
        )

    tot = n + m_rhs
    for col in range(n):
        piv = -1
        for r in range(col, n):
            if aug[r][col] != Fraction(0, 1):
                piv = r
                break
        require_ok(piv >= 0, "SINGULAR_MATRIX", f"Singular matrix at column {col}")
        if piv != col:
            aug[col], aug[piv] = aug[piv], aug[col]
        pv = aug[col][col]
        piv_row = [q_div(x, pv) for x in aug[col]]
        aug[col] = piv_row
        nz = [(j, v) for j, v in enumerate(piv_row) if v != Fraction(0, 1)]
        for r in range(n):
            if r != col and aug[r][col] != Fraction(0, 1):
                fac = aug[r][col]
                row_r = aug[r]
                for j, v in nz:
                    row_r[j] -= fac * v
    return [aug[i][n:tot] for i in range(n)]


def solve_linear_q(matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]) -> List[Fraction]:
    sol = solve_linear_multi_q(matrix, [[x] for x in rhs])
    return [row[0] for row in sol]


def rank_and_nullspace_q(rows: Sequence[Sequence[Fraction]], ncols: int) -> Tuple[int, List[List[Fraction]]]:
    """Exact RREF rank and nullspace basis over Q (zero ast.Div)."""
    nc = require_int(ncols, "ncols", lo=1, hi=MAX_GRAPH_EDGES)
    nrows = len(rows)
    require_ok(1 <= nrows <= MAX_GRAPH_EDGES * 2, "BAD_DIM", "Row count out of range")
    mat: List[List[Fraction]] = []
    for raw_r in rows:
        require_ok(len(raw_r) == nc, "RAGGED_MAT", "Row length mismatch")
        mat.append([require_frac(x, "M") for x in raw_r])

    piv_cols: List[int] = []
    r = 0
    for c in range(nc):
        piv = -1
        for i in range(r, nrows):
            if mat[i][c] != Fraction(0, 1):
                piv = i
                break
        if piv < 0:
            continue
        if piv != r:
            mat[r], mat[piv] = mat[piv], mat[r]
        pv = mat[r][c]
        nz_cols: List[Tuple[int, Fraction]] = []
        for j in range(c, nc):
            v = mat[r][j]
            if v != Fraction(0, 1):
                v = q_div(v, pv)
                mat[r][j] = v
                nz_cols.append((j, v))
        for i in range(nrows):
            if i != r and mat[i][c] != Fraction(0, 1):
                fac = mat[i][c]
                row_i = mat[i]
                for j, rv in nz_cols:
                    row_i[j] -= fac * rv
        piv_cols.append(c)
        r += 1
        if r == nrows:
            break

    piv_set = set(piv_cols)
    basis: List[List[Fraction]] = []
    for fc in range(nc):
        if fc in piv_set:
            continue
        vec = [Fraction(0, 1)] * nc
        vec[fc] = Fraction(1, 1)
        for row_idx, pc in enumerate(piv_cols):
            vec[pc] = -mat[row_idx][fc]
        basis.append(vec)
    return r, basis


def sylvester_inertia_q(matrix: Sequence[Sequence[Fraction]]) -> Tuple[int, int, int]:
    """Exact Bunch-Kaufman 1x1/2x2 symmetric congruence Sylvester inertia (pos, neg, zero) over Q."""
    n = len(matrix)
    require_ok(1 <= n <= MAX_MATRIX_DIM, "BAD_DIM", "Matrix dimension out of range")
    a: List[List[Fraction]] = []
    for i in range(n):
        require_ok(len(matrix[i]) == n, "RAGGED_MAT", "Matrix must be square")
        a.append([require_frac(x, "S") for x in matrix[i]])
    for i in range(n):
        for j in range(i + 1, n):
            require_ok(a[i][j] == a[j][i], "NON_SYMMETRIC", f"Asymmetry at ({i},{j})")

    n_pos = 0
    n_neg = 0
    n_zero = 0
    k = 0
    while k < n:
        diag_piv = -1
        for i in range(k, n):
            if a[i][i] != Fraction(0, 1):
                diag_piv = i
                break
        if diag_piv >= 0:
            if diag_piv != k:
                a[k], a[diag_piv] = a[diag_piv], a[k]
                for row in a:
                    row[k], row[diag_piv] = row[diag_piv], row[k]
            d = a[k][k]
            if d > Fraction(0, 1):
                n_pos += 1
            else:
                n_neg += 1
            for i in range(k + 1, n):
                f = q_div(a[i][k], d)
                if f != Fraction(0, 1):
                    for j in range(k + 1, n):
                        a[i][j] -= f * a[k][j]
            k += 1
            continue

        off_i = -1
        off_j = -1
        for i in range(k, n):
            for j in range(i + 1, n):
                if a[i][j] != Fraction(0, 1):
                    off_i = i
                    off_j = j
                    break
            if off_i >= 0:
                break
        if off_i < 0:
            n_zero += n - k
            break
        if off_i != k:
            a[k], a[off_i] = a[off_i], a[k]
            for row in a:
                row[k], row[off_i] = row[off_i], row[k]
        if off_j != k + 1:
            a[k + 1], a[off_j] = a[off_j], a[k + 1]
            for row in a:
                row[k + 1], row[off_j] = row[off_j], row[k + 1]
        b = a[k][k + 1]
        n_pos += 1
        n_neg += 1
        for i in range(k + 2, n):
            c0 = q_div(a[i][k + 1], b)
            c1 = q_div(a[i][k], b)
            for j in range(k + 2, n):
                a[i][j] -= c0 * a[k][j] + c1 * a[k + 1][j]
        k += 2
    return (n_pos, n_neg, n_zero)


def build_grounded_laplacian_q(
    n_nodes: int,
    edges: Sequence[Tuple[int, int, Fraction]],
    shunts: Sequence[Tuple[int, Fraction]] = (),
) -> List[List[Fraction]]:
    """Build exact symmetric graph Laplacian L + diag(shunts) over Q.

    When `shunts=()` is empty on a connected n-node graph, returns the ungrounded
    PSD Laplacian with trivial constant nullspace ker(L)=span{1} and inertia (n-1, 0, 1).
    """
    n = require_int(n_nodes, "n_nodes", lo=2, hi=MAX_MATRIX_DIM - 1)
    require_ok(len(edges) >= 1, "BAD_GRAPH", "edges must be non-empty")
    mat = [[Fraction(0, 1) for _ in range(n)] for _ in range(n)]
    for u, v, g in edges:
        require_int(u, "u", lo=0, hi=n - 1)
        require_int(v, "v", lo=0, hi=n - 1)
        require_ok(u != v, "SELF_LOOP", "Self-loop forbidden")
        gf = require_pos_frac(g, "g")
        mat[u][u] += gf
        mat[v][v] += gf
        mat[u][v] -= gf
        mat[v][u] -= gf
    for node, gs in shunts:
        require_int(node, "shunt_node", lo=0, hi=n - 1)
        gsf = require_frac(gs, "shunt_g")
        require_ok(gsf >= Fraction(0, 1), "NEG_SHUNT", "Shunt conductance must be >= 0")
        mat[node][node] += gsf
    return mat


def schur_pushforward_q(
    lap: Sequence[Sequence[Fraction]],
    boundary: Sequence[int],
) -> List[List[Fraction]]:
    n = len(lap)
    require_ok(n >= 2, "BAD_DIM", "lap must have >= 2 nodes")
    b_idx = [require_int(b, "b", lo=0, hi=n - 1) for b in boundary]
    b_set = set(b_idx)
    require_ok(len(b_set) == len(b_idx) and 1 <= len(b_idx) < n, "BAD_BOUNDARY", "Invalid boundary partition")
    i_idx = [idx for idx in range(n) if idx not in b_set]
    l_bb = [[lap[u][v] for v in b_idx] for u in b_idx]
    l_bi = [[lap[u][v] for v in i_idx] for u in b_idx]
    l_ib = [[lap[u][v] for v in b_idx] for u in i_idx]
    l_ii = [[lap[u][v] for v in i_idx] for u in i_idx]
    inv_lib = solve_linear_multi_q(l_ii, l_ib)
    nb = len(b_idx)
    ni = len(i_idx)
    schur = [[Fraction(0, 1) for _ in range(nb)] for _ in range(nb)]
    for r in range(nb):
        for c in range(nb):
            acc = l_bb[r][c]
            for k in range(ni):
                acc -= l_bi[r][k] * inv_lib[k][c]
            schur[r][c] = acc
    return schur


def laplacian_pseudoinverse_q(
    n_nodes: int,
    edges: Sequence[Tuple[int, int, Fraction]],
) -> Tuple[List[List[Fraction]], List[List[Fraction]]]:
    lap = build_grounded_laplacian_q(n_nodes, edges)
    n = len(lap)
    bordered = [row + [Fraction(1, 1)] for row in lap] + [[Fraction(1, 1)] * n + [Fraction(0, 1)]]
    inv_n = Fraction(1, n)
    rhs = [
        [(Fraction(1, 1) if i == j else Fraction(0, 1)) - inv_n for j in range(n)]
        for i in range(n)
    ] + [[Fraction(0, 1)] * n]
    sol = solve_linear_multi_q(bordered, rhs)
    return lap, sol[:n]


def _is_connected(n: int, edges: Sequence[Tuple[int, int]], skip: Sequence[int] = ()) -> bool:
    skip_set = set(skip)
    adj: List[List[int]] = [[] for _ in range(n)]
    for idx, (u, v) in enumerate(edges):
        if idx not in skip_set:
            adj[u].append(v)
            adj[v].append(u)
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for w in adj[u]:
            if w not in seen:
                seen.add(w)
                stack.append(w)
    return len(seen) == n


# ---------------------------------------------------------------------------
# U1: Cascaded Leaky Weir Statics x Petra Siq / Lyon Gier & Belanger Jump
# ---------------------------------------------------------------------------


def analyze_head_cascade_q(total_head: Fraction, stage_heads: Sequence[Fraction]) -> Dict[str, Any]:
    h_tot = require_pos_frac(total_head, "total_head")
    require_ok(len(stage_heads) >= 1, "BAD_STAGES", "Need >= 1 stage")
    hs = [require_pos_frac(h, "stage_head") for h in stage_heads]
    require_ok(sum(hs, Fraction(0, 1)) == h_tot, "HEAD_SUM", "Stage heads must sum to total_head")
    k = len(hs)
    f_mono = Fraction(1, 2) * h_tot * h_tot
    m_mono = Fraction(1, 6) * h_tot * h_tot * h_tot
    f_total = sum((Fraction(1, 2) * h * h for h in hs), Fraction(0, 1))
    m_peak = max(Fraction(1, 6) * h * h * h for h in hs)
    sum_sq = sum((h * h for h in hs), Fraction(0, 1))
    pairwise_sq = sum(((hs[i] - hs[j]) ** 2 for i in range(k) for j in range(i + 1, k)), Fraction(0, 1))
    jensen_excess = sum_sq - q_div(h_tot * h_tot, Fraction(k, 1))
    return {
        "stages": k,
        "shear_reduction_ratio": q_div(f_mono, f_total),
        "peak_moment_reduction_ratio": q_div(m_mono, m_peak),
        "jensen_excess": jensen_excess,
        "jensen_identity_exact": jensen_excess == q_div(pairwise_sq, Fraction(k, 1)),
    }


def evaluate_belanger_jump_q(k_ratio: Fraction, y1: Fraction) -> Dict[str, Any]:
    """Exact pure-Q Belanger hydraulic jump (Machu Picchu / Tipon); rejects k <= 1."""
    k = require_pos_frac(k_ratio, "k_ratio")
    y_up = require_pos_frac(y1, "y1")
    require_ok(k > Fraction(1, 1), "NON_SUPERCRITICAL", "Hydraulic jump requires k = y2/y1 > 1")
    g = Fraction(49, 5)
    y2 = k * y_up
    fr1_sq = q_div(k * (k + Fraction(1, 1)), Fraction(2, 1))
    q_sq = fr1_sq * g * (y_up ** 3)
    v1_sq = q_div(q_sq, y_up * y_up)
    v2_sq = q_div(q_sq, y2 * y2)
    fr2_sq = q_div(v2_sq, g * y2)
    m1 = q_div(y_up * y_up, Fraction(2, 1)) + q_div(q_sq, g * y_up)
    m2 = q_div(y2 * y2, Fraction(2, 1)) + q_div(q_sq, g * y2)
    e1 = y_up + q_div(v1_sq, Fraction(2, 1) * g)
    e2 = y2 + q_div(v2_sq, Fraction(2, 1) * g)
    delta_e = e1 - e2
    delta_e_closed = q_div((y2 - y_up) ** 3, Fraction(4, 1) * y_up * y2)
    return {
        "fr1_sq": fr1_sq,
        "fr2_sq": fr2_sq,
        "momentum_conserved": m1 == m2,
        "delta_e": delta_e,
        "closed_form_match": delta_e == delta_e_closed,
    }


def simulate_conductance_feedback_q(g0: Fraction, coupling: Fraction, steps: int, mode: str) -> Fraction:
    g = require_pos_frac(g0, "g0")
    c = require_pos_frac(coupling, "coupling")
    n_steps = require_int(steps, "steps", lo=1, hi=6)
    require_ok(mode in ("choke", "piping"), "BAD_MODE", "mode must be 'choke' or 'piping'")
    for _ in range(n_steps):
        fac = Fraction(1, 1) + c * g * g
        g = q_div(g, fac) if mode == "choke" else g * fac
    return g


def certify_u1_hydraulic_unification() -> Dict[str, Any]:
    """U1: Beaver-dam cascade x Petra Siq / Roman Gier Schur & Belanger obstruction."""
    beaver_k4 = analyze_head_cascade_q(Fraction(8, 1), [Fraction(2, 1)] * 4)
    beaver_nonunif = analyze_head_cascade_q(
        Fraction(8, 1),
        [Fraction(4, 1), Fraction(4, 3), Fraction(4, 3), Fraction(4, 3)],
    )
    petra_k36 = analyze_head_cascade_q(Fraction(72, 1), [Fraction(2, 1)] * 36)

    chain_edges = [(i, i + 1, Fraction(2, 1)) for i in range(6)]
    lap_unvented = build_grounded_laplacian_q(7, chain_edges)
    lap_vented = build_grounded_laplacian_q(7, chain_edges, [(i, Fraction(1, 1)) for i in range(1, 6)])
    schur_unv = schur_pushforward_q(lap_unvented, (0, 6))
    schur_vent = schur_pushforward_q(lap_vented, (0, 6))
    surge_unv = -schur_unv[0][1]
    surge_vent = -schur_vent[0][1]
    in_vent_full = sylvester_inertia_q(lap_vented)
    in_vent_ii = sylvester_inertia_q([[lap_vented[i][j] for j in range(1, 6)] for i in range(1, 6)])
    in_vent_s = sylvester_inertia_q(schur_vent)
    haynsworth_vent_ok = all(in_vent_full[k] == in_vent_ii[k] + in_vent_s[k] for k in range(3))

    gier_edges = [(0, p, Fraction(2, 1)) for p in range(1, 10)] + [(p, 10, Fraction(2, 1)) for p in range(1, 10)]
    lap_gier = build_grounded_laplacian_q(11, gier_edges)
    schur_gier = schur_pushforward_q(lap_gier, (0, 10))
    in_gier_full = sylvester_inertia_q(lap_gier)
    in_gier_ii = sylvester_inertia_q([[lap_gier[i][j] for j in range(1, 10)] for i in range(1, 10)])
    in_gier_s = sylvester_inertia_q(schur_gier)
    haynsworth_gier_ok = all(in_gier_full[k] == in_gier_ii[k] + in_gier_s[k] for k in range(3))

    jump_k2 = evaluate_belanger_jump_q(Fraction(2, 1), Fraction(1, 5))
    jump_k4 = evaluate_belanger_jump_q(Fraction(4, 1), Fraction(1, 5))
    jump_nonlin_ratio = q_div(jump_k4["delta_e"], jump_k2["delta_e"])
    y_rev = Fraction(1, 5)
    y2_rev = Fraction(1, 2) * y_rev
    rev_delta_e = q_div((y2_rev - y_rev) ** 3, Fraction(4, 1) * y_rev * y2_rev)

    g_choke = simulate_conductance_feedback_q(Fraction(1, 1), Fraction(1, 4), 5, "choke")
    g_piping = simulate_conductance_feedback_q(Fraction(1, 1), Fraction(1, 4), 5, "piping")
    feedback_ratio = q_div(g_piping, g_choke)

    passed = all((
        beaver_k4["peak_moment_reduction_ratio"] == Fraction(64, 1),
        beaver_k4["shear_reduction_ratio"] == Fraction(4, 1),
        beaver_k4["jensen_identity_exact"],
        beaver_nonunif["jensen_excess"] > Fraction(0, 1),
        petra_k36["peak_moment_reduction_ratio"] == Fraction(46656, 1),
        petra_k36["shear_reduction_ratio"] == Fraction(36, 1),
        surge_unv == Fraction(1, 3),
        surge_vent == Fraction(64, 1365),
        haynsworth_vent_ok,
        in_vent_full == (7, 0, 0),
        schur_gier[0][0] == Fraction(9, 1),
        haynsworth_gier_ok,
        in_gier_full == (10, 0, 1),
        jump_k2["momentum_conserved"],
        jump_k2["closed_form_match"],
        jump_k4["closed_form_match"],
        jump_nonlin_ratio == Fraction(27, 2),
        rev_delta_e < Fraction(0, 1),
        feedback_ratio > Fraction(500, 1),
    ))
    return {
        "gate": "U1_HYDRAULIC_SCHUR_WEIR_AND_BELANGER_OBSTRUCTION",
        "classification": {
            "beaver_cascade_vs_petra_36_basins": "EXACT_ISOMORPHISM",
            "beaver_leaky_weir_vs_petra_gier_schur": "EXACT_SCHUR_INERTIA_EQUIVALENCE",
            "linear_schur_weir_vs_machu_picchu_belanger_jump": "PROVABLE_OBSTRUCTION",
            "linear_schur_weir_vs_choke_piping_feedback": "PROVABLE_OBSTRUCTION",
        },
        "beaver_k4_moment_collapse": fmt_q(beaver_k4["peak_moment_reduction_ratio"]),
        "petra_k36_moment_collapse": fmt_q(petra_k36["peak_moment_reduction_ratio"]),
        "petra_beaver_unvented_surge_q": fmt_q(surge_unv),
        "petra_beaver_vented_surge_q": fmt_q(surge_vent),
        "vented_haynsworth_inertia": inertia_dict(in_vent_full),
        "gier_9pipe_schur_conductance_q": fmt_q(schur_gier[0][0]),
        "gier_haynsworth_inertia": inertia_dict(in_gier_full),
        "belanger_k2_delta_e_q": fmt_q(jump_k2["delta_e"]),
        "belanger_k4_delta_e_q": fmt_q(jump_k4["delta_e"]),
        "belanger_k4_over_k2_nonlinear_ratio_q": fmt_q(jump_nonlin_ratio),
        "belanger_reversed_k_half_forbidden_delta_e_q": fmt_q(rev_delta_e),
        "piping_over_choke_t5_gt_500": feedback_ratio > Fraction(500, 1),
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# U2: Orb-Web G_orb(6,2) ~= Casarabe C_{2,6}, Kirchhoff Ventilation, &
#     Non-Symmetric Convective Transport Obstruction
# ---------------------------------------------------------------------------


def solve_kirchhoff_ventilation_q(
    n_nodes: int,
    edges: Sequence[Tuple[int, int]],
    conductances: Sequence[Fraction],
    forcing: Sequence[Fraction],
) -> Dict[str, Any]:
    m = len(edges)
    require_ok(len(conductances) == m and len(forcing) == m, "DIM_MISMATCH", "Edge/conductance/forcing mismatch")
    w_edges = [(u, v, g) for (u, v), g in zip(edges, conductances)]
    _, lp = laplacian_pseudoinverse_q(n_nodes, w_edges)
    rhs = [Fraction(0, 1)] * n_nodes
    for (u, v), g, eta in zip(edges, conductances, forcing):
        rhs[u] -= g * eta
        rhs[v] += g * eta
    p = [sum((lp[i][j] * rhs[j] for j in range(n_nodes)), Fraction(0, 1)) for i in range(n_nodes)]
    q = [g * (eta - (p[v] - p[u])) for (u, v), g, eta in zip(edges, conductances, forcing)]

    b_rows = [[Fraction(0, 1)] * m for _ in range(n_nodes)]
    for idx, (u, v) in enumerate(edges):
        b_rows[u][idx] = Fraction(-1, 1)
        b_rows[v][idx] = Fraction(1, 1)
    _, cycle_basis = rank_and_nullspace_q(b_rows, m)
    beta1 = m - n_nodes + 1
    if beta1 == 0:
        q_cycle = [Fraction(0, 1)] * m
    else:
        r_mat = [
            [
                sum((q_div(cycle_basis[a][e] * cycle_basis[b][e], conductances[e]) for e in range(m)), Fraction(0, 1))
                for b in range(beta1)
            ]
            for a in range(beta1)
        ]
        c_eta = [sum((cycle_basis[a][e] * forcing[e] for e in range(m)), Fraction(0, 1)) for a in range(beta1)]
        loop_f = solve_linear_q(r_mat, c_eta)
        q_cycle = [
            sum((loop_f[a] * cycle_basis[a][e] for a in range(beta1)), Fraction(0, 1))
            for e in range(m)
        ]
    p_eta = sum((e_val * q_e for e_val, q_e in zip(forcing, q)), Fraction(0, 1))
    p_diss = sum((q_div(q_e * q_e, g) for q_e, g in zip(q, conductances)), Fraction(0, 1))
    return {
        "beta1": beta1,
        "flows": q,
        "cycle_basis_exact_match": q == q_cycle,
        "advective_power": p_eta,
        "power_balance_exact": p_eta == p_diss,
    }


def exact_cut_survival_q(n: int, edges: Sequence[Tuple[int, int]]) -> Tuple[Fraction, Fraction, Fraction]:
    m = len(edges)
    require_ok(m >= 3, "BAD_GRAPH", "Need >= 3 edges for 1/2/3-cut survival")
    s1 = sum(1 for i in range(m) if _is_connected(n, edges, (i,)))
    s2 = sum(1 for i in range(m) for j in range(i + 1, m) if _is_connected(n, edges, (i, j)))
    s3 = sum(
        1
        for i in range(m)
        for j in range(i + 1, m)
        for k in range(j + 1, m)
        if _is_connected(n, edges, (i, j, k))
    )
    return (
        Fraction(s1, m),
        Fraction(s2, int_comb(m, 2)),
        Fraction(s3, int_comb(m, 3)),
    )


def shifted_laplacian_pd_q(n: int, edges: Sequence[Tuple[int, int]], mu: Fraction) -> bool:
    """Sylvester inertia check: L(G) + J_n - mu*I_n > 0 iff lambda_2(G) > mu (since lambda_2(G) <= n for simple graphs)."""
    lap = build_grounded_laplacian_q(n, [(u, v, Fraction(1, 1)) for u, v in edges])
    shifted = [
        [lap[i][j] + Fraction(1, 1) - (mu if i == j else Fraction(0, 1)) for j in range(n)]
        for i in range(n)
    ]
    return sylvester_inertia_q(shifted) == (n, 0, 0)


def sherman_morrison_remote_max_lodf_q(kappa: int) -> Fraction:
    """Exact remote outer-spiral max |LODF| on G_orb(6,2) = Casarabe C_{2,6} at radial/spiral ratio kappa."""
    kp = require_int(kappa, "kappa", lo=1, hi=1000)
    rad_inner = [(0, i, Fraction(kp, 1)) for i in range(1, 7)]
    rad_outer = [(i, i + 6, Fraction(kp, 1)) for i in range(1, 7)]
    sp_inner = [(i, 1 + wrap_index(i, 6), Fraction(1, 1)) for i in range(1, 7)]
    sp_outer = [(i + 6, 7 + wrap_index(i, 6), Fraction(1, 1)) for i in range(1, 7)]
    edges = rad_inner + rad_outer + sp_inner + sp_outer
    _, lp = laplacian_pseudoinverse_q(13, edges)
    cut_idx = 18
    eu, ev, k_cut = edges[cut_idx]

    def quad(u: int, v: int, x: int, y: int) -> Fraction:
        return lp[u][x] - lp[u][y] - lp[v][x] + lp[v][y]

    denom = Fraction(1, 1) - k_cut * quad(eu, ev, eu, ev)
    remote_vals: List[Fraction] = []
    for idx in range(12, 24):
        if idx in (12, 18):
            continue
        u, v, k_e = edges[idx]
        remote_vals.append(abs(q_div(k_e * quad(u, v, eu, ev), denom)))
    return max(remote_vals)


def certify_u2_topology_ventilation_and_convective_obstruction() -> Dict[str, Any]:
    """U2: Exact G_orb(6,2) ~= Casarabe C_{2,6} isomorphism, ventilation unification, & convective obstruction."""
    casarabe_edges = (
        [(0, i) for i in range(1, 7)]
        + [(i, 1 + wrap_index(i, 6)) for i in range(1, 7)]
        + [(i, i + 6) for i in range(1, 7)]
        + [(i + 6, 7 + wrap_index(i, 6)) for i in range(1, 7)]
    )
    orb_edges = (
        [(0, 1 + j) for j in range(6)]
        + [(1 + j, 7 + j) for j in range(6)]
        + [(1 + j, 1 + wrap_index(j + 1, 6)) for j in range(6)]
        + [(7 + j, 7 + wrap_index(j + 1, 6)) for j in range(6)]
    )
    tree_edges = [(0, i) for i in range(1, 7)] + [(i, i + 6) for i in range(1, 7)]
    ring_edges = [(i, wrap_index(i + 1, 13)) for i in range(13)]
    upano_edges = (
        [(r * 4 + c, r * 4 + c + 1) for r in range(4) for c in range(3)]
        + [(r * 4 + c, (r + 1) * 4 + c) for r in range(3) for c in range(4)]
    )

    exact_iso = {tuple(sorted(e)) for e in casarabe_edges} == {tuple(sorted(e)) for e in orb_edges}

    s1_c, s2_c, s3_c = exact_cut_survival_q(13, casarabe_edges)
    s1_t, s2_t, _ = exact_cut_survival_q(13, tree_edges)
    s1_r, s2_r, _ = exact_cut_survival_q(13, ring_edges)
    s1_u, s2_u, _ = exact_cut_survival_q(16, upano_edges)
    lam2_casarabe_ok = all((
        shifted_laplacian_pd_q(13, casarabe_edges, Fraction(11, 8)),
        not shifted_laplacian_pd_q(13, casarabe_edges, Fraction(7, 5)),
    ))
    lam2_tree_ok = all((
        shifted_laplacian_pd_q(13, tree_edges, Fraction(19, 50)),
        not shifted_laplacian_pd_q(13, tree_edges, Fraction(2, 5)),
    ))
    lam2_ring_ok = all((
        shifted_laplacian_pd_q(13, ring_edges, Fraction(11, 50)),
        not shifted_laplacian_pd_q(13, ring_edges, Fraction(6, 25)),
    ))

    vent_tree = solve_kirchhoff_ventilation_q(
        13, tree_edges, [Fraction(1, 1)] * len(tree_edges), [Fraction(1, 1)] + [Fraction(0, 1)] * 11
    )
    vent_ring = solve_kirchhoff_ventilation_q(
        13, ring_edges, [Fraction(1, 1)] * len(ring_edges), [Fraction(1, 1)] + [Fraction(0, 1)] * 12
    )
    vent_casarabe = solve_kirchhoff_ventilation_q(
        13, casarabe_edges, [Fraction(1, 1)] * len(casarabe_edges), [Fraction(1, 1)] + [Fraction(0, 1)] * 23
    )

    c4_lap = build_grounded_laplacian_q(4, [(i, wrap_index(i + 1, 4), Fraction(1, 1)) for i in range(4)])
    gamma = Fraction(1, 1)
    a_conv = [[c4_lap[i][j] for j in range(4)] for i in range(4)]
    for i in range(4):
        a_conv[i][i] += gamma
        a_conv[i][wrap_index(i - 1, 4)] -= gamma
    skew_frob_sq = Fraction(0, 1)
    for i in range(4):
        for j in range(4):
            s_ij = q_div(a_conv[i][j] - a_conv[j][i], Fraction(2, 1))
            skew_frob_sq += s_ij * s_ij
    conv_rejected_as_nonsym = False
    try:
        sylvester_inertia_q(a_conv)
    except MechanicsAuditError as exc:
        conv_rejected_as_nonsym = exc.code == "NON_SYMMETRIC"

    lodf_k1 = sherman_morrison_remote_max_lodf_q(1)
    lodf_k100 = sherman_morrison_remote_max_lodf_q(100)
    lodf_ratio = q_div(lodf_k1, lodf_k100)

    passed = all((
        exact_iso,
        s1_c == Fraction(1, 1),
        s2_c == Fraction(1, 1),
        s3_c == Fraction(1009, 1012),
        s1_t == Fraction(0, 1),
        s2_t == Fraction(0, 1),
        s1_r == Fraction(1, 1),
        s2_r == Fraction(0, 1),
        s1_u == Fraction(1, 1),
        s2_u == Fraction(68, 69),
        lam2_casarabe_ok,
        lam2_tree_ok,
        lam2_ring_ok,
        vent_tree["beta1"] == 0,
        vent_tree["advective_power"] == Fraction(0, 1),
        vent_tree["cycle_basis_exact_match"],
        vent_ring["beta1"] == 1,
        vent_ring["advective_power"] == Fraction(1, 13),
        vent_ring["cycle_basis_exact_match"],
        vent_casarabe["beta1"] == 12,
        vent_casarabe["advective_power"] > vent_ring["advective_power"],
        vent_casarabe["cycle_basis_exact_match"],
        vent_casarabe["power_balance_exact"],
        skew_frob_sq == Fraction(2, 1),
        conv_rejected_as_nonsym,
        lodf_ratio > Fraction(20, 1),
    ))
    return {
        "gate": "U2_ORB_CASARABE_ISOMORPHISM_VENTILATION_AND_CONVECTIVE_OBSTRUCTION",
        "classification": {
            "orb_web_g6_2_vs_casarabe_c2_6_unweighted": "EXACT_ISOMORPHISM",
            "insect_burrow_betti1_vs_amazonian_cut_ventilation": "EXACT_SCHUR_INERTIA_EQUIVALENCE",
            "symmetric_laplacian_vs_upwind_convective_transport": "PROVABLE_OBSTRUCTION",
            "unweighted_casarabe_cuts_vs_weighted_kappa100_lodf": "PROVABLE_OBSTRUCTION",
        },
        "g_orb_6_2_exact_isomorphic_to_casarabe_c2_6": exact_iso,
        "casarabe_s1_s2_s3_q": [fmt_q(s1_c), fmt_q(s2_c), fmt_q(s3_c)],
        "upano_s2_q": fmt_q(s2_u),
        "ventilation_tree_power_q": fmt_q(vent_tree["advective_power"]),
        "ventilation_ring_power_q": fmt_q(vent_ring["advective_power"]),
        "ventilation_casarabe_power_q": fmt_q(vent_casarabe["advective_power"]),
        "c4_upwind_skew_frob_sq_q": fmt_q(skew_frob_sq),
        "convective_operator_rejected_by_symmetric_inertia": conv_rejected_as_nonsym,
        "lodf_remote_max_k1_q": fmt_q(lodf_k1),
        "lodf_remote_max_k100_q": fmt_q(lodf_k100),
        "lodf_k1_over_k100_ratio_q": fmt_q(lodf_ratio),
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# U3: Discrete Volkersen Shear-Lag x Dougong Friction Hysteresis & Housner
# ---------------------------------------------------------------------------


def solve_volkersen_discrete_q(bay_lengths: Sequence[Fraction], alpha_total: Fraction) -> Dict[str, Any]:
    require_ok(len(bay_lengths) >= 1, "BAD_BAYS", "Need >= 1 bay")
    bays = [require_pos_frac(d, "bay") for d in bay_lengths]
    alpha = require_pos_frac(alpha_total, "alpha_total")
    l_tot = sum(bays, Fraction(0, 1))
    lams = [q_div(alpha * d, l_tot) for d in bays]
    n = len(bays)
    mat = [[Fraction(0, 1)] * n for _ in range(n)]
    rhs = [Fraction(0, 1)] * n
    for i in range(n):
        mat[i][i] = Fraction(2, 1) + Fraction(2, 1) * lams[i]
        if i > 0:
            mat[i][i - 1] = Fraction(-1, 1)
        if i + 1 < n:
            mat[i][i + 1] = Fraction(-1, 1)
        rhs[i] = lams[i] + (Fraction(1, 1) if i == n - 1 else Fraction(0, 1))
    t_vec = solve_linear_q(mat, rhs)
    ts = [Fraction(0, 1)] + t_vec + [Fraction(1, 1)]
    forces = [ts[i + 1] - ts[i] for i in range(n + 1)]
    inertia = sylvester_inertia_q(mat)
    return {
        "rivet_forces": forces,
        "max_rivet_force": max(forces),
        "force_sum_exact": sum(forces, Fraction(0, 1)) == Fraction(1, 1),
        "stiffness_inertia": inertia,
    }


def dougong_hysteresis_q(k: Fraction, u_y: Fraction, u_m: Fraction, alpha: Fraction) -> Dict[str, Any]:
    kf = require_pos_frac(k, "k")
    uy = require_pos_frac(u_y, "u_y")
    um = require_pos_frac(u_m, "u_m")
    af = require_frac(alpha, "alpha")
    require_ok(um > uy, "NO_SLIP", "Peak drift u_m must exceed u_y")
    require_ok(Fraction(0, 1) <= af <= Fraction(1, 1), "BAD_ALPHA", "alpha must lie in [0, 1]")
    f_y = kf * uy
    f_m = f_y + af * kf * (um - uy)
    verts = (
        (um, f_m),
        (um - Fraction(2, 1) * uy, f_m - Fraction(2, 1) * f_y),
        (-um, -f_m),
        (-um + Fraction(2, 1) * uy, -f_m + Fraction(2, 1) * f_y),
    )
    twice_area = Fraction(0, 1)
    for i in range(4):
        x1, y1 = verts[i]
        x2, y2 = verts[wrap_index(i + 1, 4)]
        twice_area += x1 * y2 - x2 * y1
    e_shoelace = q_div(abs(twice_area), Fraction(2, 1))
    e_formula = Fraction(4, 1) * f_y * (um - uy) * (Fraction(1, 1) - af)
    e_elastic = Fraction(1, 2) * f_m * um
    pi_zeta = q_div(e_shoelace, Fraction(4, 1) * e_elastic)
    zeta_lo = q_div(pi_zeta, PI_HI)
    zeta_hi = q_div(pi_zeta, PI_LO)
    return {
        "e_diss": e_shoelace,
        "area_residual_zero": e_shoelace == e_formula,
        "pi_times_zeta": pi_zeta,
        "in_15_to_30_pct": zeta_lo >= Fraction(15, 100) and zeta_hi <= Fraction(30, 100),
    }


def housner_rocking_q(aspect_b_over_h: Fraction) -> Dict[str, Any]:
    bh = require_pos_frac(aspect_b_over_h, "b_over_h")
    require_ok(bh <= Fraction(1, 1), "NON_ROCKING", "b/h must be <= 1 for vertical ashlar rocking")
    sin2 = q_div(bh * bh, Fraction(1, 1) + bh * bh)
    r_sqrt = Fraction(1, 1) - Fraction(3, 2) * sin2
    r = r_sqrt * r_sqrt
    return {"restitution_r": r, "dissipation_loss": Fraction(1, 1) - r}


def certify_u3_seam_hysteresis_and_dissipation_obstruction() -> Dict[str, Any]:
    """U3: Tailorbird Volkersen shear-lag x Dougong hysteresis & Machu Picchu Housner rocking."""
    caps: List[Fraction] = []
    for m in range(1, 10):
        if m == 1:
            fmax = Fraction(1, 1)
        else:
            sol = solve_volkersen_discrete_q([q_div(Fraction(10, 1), Fraction(m - 1, 1))] * (m - 1), Fraction(4, 1))
            fmax = sol["max_rivet_force"]
        w_pull = q_div(Fraction(1, 1), fmax)
        w_tear = Fraction(5, 1) * (Fraction(1, 1) - Fraction(m, 10))
        caps.append(w_pull if w_pull <= w_tear else w_tear)
    best_cap = max(caps)
    m_star = caps.index(best_cap) + 1

    unif_4 = solve_volkersen_discrete_q([Fraction(1, 3)] * 3, Fraction(4, 1))
    grad_4 = solve_volkersen_discrete_q([Fraction(1, 6), Fraction(2, 3), Fraction(1, 6)], Fraction(4, 1))
    w_tear_4 = Fraction(3, 1)
    cap_unif_4 = min(q_div(Fraction(1, 1), unif_4["max_rivet_force"]), w_tear_4)
    cap_grad_4 = min(q_div(Fraction(1, 1), grad_4["max_rivet_force"]), w_tear_4)
    graded_gain = q_div(cap_grad_4, cap_unif_4)
    volk_6 = solve_volkersen_discrete_q([Fraction(1, 5)] * 5, Fraction(6, 1))

    dg_coulomb = dougong_hysteresis_q(Fraction(12, 1), Fraction(2, 1), Fraction(3, 1), Fraction(0, 1))
    dg_elastic = dougong_hysteresis_q(Fraction(12, 1), Fraction(2, 1), Fraction(3, 1), Fraction(1, 1))

    h_stout = housner_rocking_q(Fraction(2, 3))
    h_slender = housner_rocking_q(Fraction(1, 4))
    housner_ratio = q_div(h_stout["dissipation_loss"], h_slender["dissipation_loss"])

    passed = all((
        m_star == 4,
        best_cap == Fraction(28, 11),
        unif_4["stiffness_inertia"] == (3, 0, 0),
        grad_4["stiffness_inertia"] == (3, 0, 0),
        volk_6["stiffness_inertia"] == (5, 0, 0),
        cap_unif_4 == Fraction(28, 11),
        cap_grad_4 == Fraction(20, 7),
        graded_gain == Fraction(55, 49),
        dg_coulomb["area_residual_zero"],
        dg_coulomb["pi_times_zeta"] == Fraction(2, 3),
        dg_coulomb["in_15_to_30_pct"],
        dg_elastic["area_residual_zero"],
        dg_elastic["e_diss"] == Fraction(0, 1),
        h_stout["restitution_r"] == Fraction(49, 169),
        h_stout["dissipation_loss"] == Fraction(120, 169),
        housner_ratio == Fraction(9248, 2197),
    ))
    return {
        "gate": "U3_TAILORBIRD_VOLKERSEN_DOUGONG_HOUSNER_TAXONOMY",
        "classification": {
            "volkersen_tridiagonal_vs_spd_m_matrix_schur": "EXACT_SCHUR_INERTIA_EQUIVALENCE",
            "elastic_volkersen_seam_vs_dougong_hysteresis": "PROVABLE_OBSTRUCTION",
            "dougong_monotonic_ductility_vs_tailorbird_postage_stamp_tear": "PROVABLE_OBSTRUCTION",
        },
        "tailorbird_m_star": m_star,
        "tailorbird_w_cap_star_q": fmt_q(best_cap),
        "tailorbird_graded_cap_m4_q": fmt_q(cap_grad_4),
        "tailorbird_graded_gain_ratio_q": fmt_q(graded_gain),
        "volkersen_m6_inertia": inertia_dict(volk_6["stiffness_inertia"]),
        "dougong_coulomb_e_diss_q": fmt_q(dg_coulomb["e_diss"]),
        "dougong_coulomb_pi_zeta_q": fmt_q(dg_coulomb["pi_times_zeta"]),
        "elastic_closed_cycle_e_diss_q": fmt_q(dg_elastic["e_diss"]),
        "machu_picchu_stout_loss_q": fmt_q(h_stout["dissipation_loss"]),
        "machu_picchu_stout_over_slender_q": fmt_q(housner_ratio),
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# U4: Sylvester Inertia Non-Congruence (H_8 Indefinite vs. Passive M-Matrices)
# ---------------------------------------------------------------------------


def build_anchored_orb_stress_int_q(
    n_spokes: int,
    w_sp: Fraction,
    w_in: Fraction,
    w_out: Fraction,
) -> List[List[Fraction]]:
    """(n_spokes+1)x(n_spokes+1) interior Connelly-Whiteley stress matrix Omega_int for an anchored orb web."""
    ns = require_int(n_spokes, "n_spokes", lo=3, hi=24)
    ws = require_frac(w_sp, "w_sp")
    wi = require_frac(w_in, "w_in")
    wo = require_frac(w_out, "w_out")
    dim = ns + 1
    mat = [[Fraction(0, 1)] * dim for _ in range(dim)]
    for k in range(ns):
        u = 1 + k
        v = 1 + wrap_index(k + 1, ns)
        mat[0][0] += wi
        mat[u][u] += wi + wo + Fraction(2, 1) * ws
        mat[0][u] -= wi
        mat[u][0] -= wi
        mat[u][v] -= ws
        mat[v][u] -= ws
    return mat


def build_coupled_auxetic_h8_hessian_q() -> List[List[Fraction]]:
    """Non-diagonal zero-diagonal 8x8 coupled bilinear fold-sheaf Hessian [[0, B], [B^T, 0]] with SPD tridiagonal B."""
    b_block = [
        [
            Fraction(2, 1) if i == j else (Fraction(-1, 1) if abs(i - j) == 1 else Fraction(0, 1))
            for j in range(4)
        ]
        for i in range(4)
    ]
    h8 = [[Fraction(0, 1)] * 8 for _ in range(8)]
    for i in range(4):
        for j in range(4):
            h8[i][4 + j] = b_block[i][j]
            h8[4 + j][i] = b_block[i][j]
    return h8


def certify_u4_sylvester_non_congruence() -> Dict[str, Any]:
    """U4: Equal-order 8x8 Sylvester inertia non-congruence separating passive M-matrices from H_8 & compressed cables."""
    orb_8d_tension = build_anchored_orb_stress_int_q(7, Fraction(1, 1), Fraction(10, 1), Fraction(11, 1))
    orb_8d_compress = build_anchored_orb_stress_int_q(7, Fraction(1, 1), Fraction(-10, 1), Fraction(-9, 1))
    orb_tension_in = sylvester_inertia_q(orb_8d_tension)
    orb_compress_in = sylvester_inertia_q(orb_8d_compress)

    h8_hessian = build_coupled_auxetic_h8_hessian_q()
    h8_inertia = sylvester_inertia_q(h8_hessian)

    hyp_2x2 = [[Fraction(0, 1), Fraction(3, 1)], [Fraction(3, 1), Fraction(0, 1)]]
    hyp_inertia = sylvester_inertia_q(hyp_2x2)

    casarabe_edges = (
        [(0, i, Fraction(1, 1)) for i in range(1, 7)]
        + [(i, 1 + wrap_index(i, 6), Fraction(1, 1)) for i in range(1, 7)]
        + [(i, i + 6, Fraction(1, 1)) for i in range(1, 7)]
        + [(i + 6, 7 + wrap_index(i, 6), Fraction(1, 1)) for i in range(1, 7)]
    )
    # Ungrounded 13-node connected Casarabe graph Laplacian (shunts=()): PSD inertia (12, 0, 1)
    casarabe_in = sylvester_inertia_q(build_grounded_laplacian_q(13, casarabe_edges))

    equal_dim_8d = len(orb_8d_tension) == len(h8_hessian) == 8
    all_passive_zero_neg = all((orb_tension_in[1] == 0, casarabe_in[1] == 0))
    non_congruent_h8 = all((equal_dim_8d, all_passive_zero_neg, h8_inertia == (4, 4, 0)))
    compression_crosses_boundary = all((orb_compress_in[1] >= 1, hyp_inertia == (1, 1, 0)))

    passed = all((
        equal_dim_8d,
        orb_tension_in == (8, 0, 0),
        casarabe_in == (12, 0, 1),
        h8_inertia == (4, 4, 0),
        orb_compress_in == (0, 8, 0),
        hyp_inertia == (1, 1, 0),
        non_congruent_h8,
        compression_crosses_boundary,
    ))
    return {
        "gate": "U4_SYLVESTER_INERTIA_NON_CONGRUENCE",
        "classification": {
            "schur_elimination_method_across_passive_and_auxetic": "EXACT_SCHUR_INERTIA_EQUIVALENCE",
            "passive_biomimetic_historical_vs_h8_auxetic_fold_sheaf": "PROVABLE_OBSTRUCTION",
            "tension_only_web_vs_compressed_cable_buckling": "PROVABLE_OBSTRUCTION",
        },
        "equal_order_dim": 8,
        "orb_8d_tension_only_inertia": inertia_dict(orb_tension_in),
        "orb_8d_compression_neg_ctrl_inertia": inertia_dict(orb_compress_in),
        "casarabe_laplacian_inertia": inertia_dict(casarabe_in),
        "h8_auxetic_fold_sheaf_inertia": inertia_dict(h8_inertia),
        "zero_diag_hyperbolic_2x2_inertia": inertia_dict(hyp_inertia),
        "non_congruence_proven": non_congruent_h8,
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# U5: Euplectella Checkerboard Cylinder Maxwell-Calladine Parity Obstruction
# ---------------------------------------------------------------------------


def analyze_euplectella_4x4_q(pattern: str, continuous_beams: bool) -> Dict[str, Any]:
    require_ok(pattern in ("none", "checker_1", "checker_1_bridge", "full_1"), "BAD_PAT", f"Unknown pattern {pattern}")
    require_ok(type(continuous_beams) is bool, "BAD_BOOL", "continuous_beams must be bool")
    nr, nc = 4, 4
    ny = nr + 1
    n_verts = ny * nc
    ncols = 2 * n_verts

    def vid(r: int, c: int) -> int:
        return r * nc + wrap_index(c, nc)

    rows: List[List[Fraction]] = []
    for r in range(ny):
        for c in range(nc):
            u, v = vid(r, c), vid(r, c + 1)
            row = [Fraction(0, 1)] * ncols
            row[2 * u] = Fraction(-1, 1)
            row[2 * v] = Fraction(1, 1)
            rows.append(row)
    for r in range(nr):
        for c in range(nc):
            u, v = vid(r, c), vid(r + 1, c)
            row = [Fraction(0, 1)] * ncols
            row[2 * u + 1] = Fraction(-1, 1)
            row[2 * v + 1] = Fraction(1, 1)
            rows.append(row)

    n_diags = 0
    for r in range(nr):
        for c in range(nc):
            add = (
                pattern == "full_1"
                or (pattern == "checker_1" and ((r + c) & 1) == 0)
                or (pattern == "checker_1_bridge" and (((r + c) & 1) == 0 or (r == 0 and c == 1)))
            )
            if add:
                u00, u11 = vid(r, c), vid(r + 1, c + 1)
                row = [Fraction(0, 1)] * ncols
                row[2 * u00] = Fraction(-1, 1)
                row[2 * u00 + 1] = Fraction(-1, 1)
                row[2 * u11] = Fraction(1, 1)
                row[2 * u11 + 1] = Fraction(1, 1)
                rows.append(row)
                n_diags += 1

    if continuous_beams:
        for r in range(1, nr):
            for c in range(nc):
                row = [Fraction(0, 1)] * ncols
                row[2 * vid(r - 1, c)] = Fraction(1, 1)
                row[2 * vid(r, c)] = Fraction(-2, 1)
                row[2 * vid(r + 1, c)] = Fraction(1, 1)
                rows.append(row)

    nrows = len(rows)
    rk, mech_basis = rank_and_nullspace_q(rows, ncols)
    rows_t = [[rows[r][c] for r in range(nrows)] for c in range(ncols)]
    rk_t, stress_basis = rank_and_nullspace_q(rows_t, nrows)

    mech_ker_exact = all(
        sum((v * vec[j] for j, v in enumerate(row) if v != Fraction(0, 1)), Fraction(0, 1)) == Fraction(0, 1)
        for vec in mech_basis
        for row in rows
    )
    stress_ker_exact = all(
        sum((v * vec[j] for j, v in enumerate(row_t) if v != Fraction(0, 1)), Fraction(0, 1)) == Fraction(0, 1)
        for vec in stress_basis
        for row_t in rows_t
    )
    internal_dofs = ncols - 2
    floppy = len(mech_basis) - 2
    self_stresses = len(stress_basis)

    torsion_vec: List[Fraction] = []
    zigzag_vec: List[Fraction] = []
    for r in range(ny):
        for c in range(nc):
            torsion_vec.extend([Fraction(r, 1), Fraction(0, 1)])
            zigzag_vec.extend([Fraction(1 if (r & 1) == 0 else -1, 1), Fraction(-1 if (c & 1) == 0 else 1, 1)])
    t_energy = sum(
        (sum((v * torsion_vec[j] for j, v in enumerate(row) if v != Fraction(0, 1)), Fraction(0, 1)) ** 2 for row in rows),
        Fraction(0, 1),
    )
    z_energy = sum(
        (sum((v * zigzag_vec[j] for j, v in enumerate(row) if v != Fraction(0, 1)), Fraction(0, 1)) ** 2 for row in rows),
        Fraction(0, 1),
    )
    return {
        "n_diagonals": n_diags,
        "rank": rk,
        "transpose_rank": rk_t,
        "floppy_modes": floppy,
        "self_stresses": self_stresses,
        "independent_kernels_verified": all((
            rk == rk_t,
            mech_ker_exact,
            stress_ker_exact,
            (floppy - self_stresses) == (internal_dofs - nrows),
        )),
        "torsion_energy": t_energy,
        "zigzag_energy": z_energy,
    }


def certify_u5_euplectella_parity_obstruction() -> Dict[str, Any]:
    """U5: Euplectella 4x4 cylindrical checkerboard half-diagonal stiffening & Z/2Z zigzag parity obstruction."""
    p_none = analyze_euplectella_4x4_q("none", False)
    p_chk1 = analyze_euplectella_4x4_q("checker_1", False)
    p_bridge = analyze_euplectella_4x4_q("checker_1_bridge", False)
    p_full = analyze_euplectella_4x4_q("full_1", False)
    c_chk1 = analyze_euplectella_4x4_q("checker_1", True)

    passed = all((
        p_none["independent_kernels_verified"],
        p_chk1["independent_kernels_verified"],
        p_bridge["independent_kernels_verified"],
        p_full["independent_kernels_verified"],
        c_chk1["independent_kernels_verified"],
        p_none["floppy_modes"] == 7,
        p_none["torsion_energy"] == Fraction(0, 1),
        p_chk1["n_diagonals"] * 2 == p_full["n_diagonals"],
        p_chk1["torsion_energy"] == Fraction(8, 1),
        p_chk1["floppy_modes"] == 1,
        p_chk1["zigzag_energy"] == Fraction(0, 1),
        p_bridge["n_diagonals"] == 9,
        p_bridge["floppy_modes"] == 0,
        c_chk1["floppy_modes"] == 0,
        c_chk1["zigzag_energy"] > Fraction(0, 1),
    ))
    return {
        "gate": "U5_EUPLECTELLA_CHECKERBOARD_PARITY_OBSTRUCTION",
        "classification": {
            "checkerboard_vs_full_torsion_blocking": "EXACT_SCHUR_INERTIA_EQUIVALENCE",
            "pin_jointed_checkerboard_z2_zigzag_mode": "PROVABLE_OBSTRUCTION",
        },
        "pin_none_floppy": p_none["floppy_modes"],
        "pin_checker1_diags": p_chk1["n_diagonals"],
        "pin_full1_diags": p_full["n_diagonals"],
        "pin_checker1_floppy": p_chk1["floppy_modes"],
        "pin_checker1_torsion_energy_q": fmt_q(p_chk1["torsion_energy"]),
        "pin_checker1_zigzag_energy_q": fmt_q(p_chk1["zigzag_energy"]),
        "pin_checker1_bridge_diags": p_bridge["n_diagonals"],
        "pin_checker1_bridge_floppy": p_bridge["floppy_modes"],
        "continuous_spicule_checker1_floppy": c_chk1["floppy_modes"],
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# U6: Hardened AST Zero-Float Self-Audit & Optifab Ecosystem Scope Registry
# ---------------------------------------------------------------------------


ECOSYSTEM_BRIDGES: Tuple[Dict[str, str], ...] = (
    {
        "target": "aska-physical/optifab",
        "modules": "optifab/q/{inertia,farkas,linalg,interval}.py; studies/schur-metrology-closure; studies/cycle-thermal-contraction-audit",
        "gates": "U1, U2, U4",
        "scope_note": "Symmetric Schur pushforward & Haynsworth inertia transfer across passive thermal/hydraulic M-matrices; upwind convective advection (U2) and indefinite off-brane regimes (U4) are explicitly obstructed.",
    },
    {
        "target": "aska-physical/venturi-collars",
        "modules": "studies/cascaded-choke-and-cycle-ventilation-audit; verify.py",
        "gates": "U1, U2",
        "scope_note": "Shares K^3 cascade Jensen statics, vented surge Schur attenuation, and beta_1 >= 1 Kirchhoff circulation; Belanger jumps and high-Mach choked flow are obstructed from linear M-matrix scope.",
    },
    {
        "target": "aska-physical/cfrp-truss",
        "modules": "studies/volkersen-anchor-audit; verify.py",
        "gates": "U3, U5",
        "scope_note": "Shares SPD tridiagonal Volkersen graded anchor spacing (55/49 zero-extra-hole gain) and Maxwell-Calladine checkerboard bracing; elastic Volkersen has 0/1 cyclic dissipation vs Dougong friction hysteresis.",
    },
    {
        "target": "Foundation-0/cave-expedition",
        "modules": "biomimetic & historical pure-Q exact operator studies",
        "gates": "U1, U2, U3, U4, U5",
        "scope_note": "Unifies Schur elimination & Haynsworth additivity while certifying exact Sylvester non-congruence between equal-order 8x8 passive M-matrices (8,0,0) and 8D H_8 auxetic fold-sheaves (4,4,0).",
    },
)


def certify_u6_ast_self_audit() -> Dict[str, Any]:
    src, src_sha = _read_source_file(Path(__file__))
    ast_res = audit_source_zero_float_ast(src)
    passed = all((
        is_hex64(src_sha),
        ast_res["has_nonempty_ast"],
        ast_res["zero_float_literals"],
        ast_res["zero_ast_div"],
        ast_res["zero_unsafe_pow"],
        ast_res["zero_unsafe_fraction_calls"],
        ast_res["zero_float_imports"],
        ast_res["zero_float_calls"],
        ast_res["zero_bare_asserts"],
        ast_res["zero_dynamic_escapes"],
        len(ECOSYSTEM_BRIDGES) == 4,
    ))
    return {
        "gate": "U6_AST_ZERO_FLOAT_SELF_AUDIT_AND_SCOPE_REGISTRY",
        "ast_self_audit": ast_res,
        "ecosystem_bridges": [dict(x) for x in ECOSYSTEM_BRIDGES],
        "passed": passed,
    }


def build_payload() -> Dict[str, Any]:
    u1 = certify_u1_hydraulic_unification()
    u2 = certify_u2_topology_ventilation_and_convective_obstruction()
    u3 = certify_u3_seam_hysteresis_and_dissipation_obstruction()
    u4 = certify_u4_sylvester_non_congruence()
    u5 = certify_u5_euplectella_parity_obstruction()
    u6 = certify_u6_ast_self_audit()
    all_passed = all((u1["passed"], u2["passed"], u3["passed"], u4["passed"], u5["passed"], u6["passed"]))
    return {
        "gates": {
            "U1": u1,
            "U2": u2,
            "U3": u3,
            "U4": u4,
            "U5": u5,
            "U6": u6,
        },
        "all_gates_passed": all_passed,
    }


def build_certificate() -> Dict[str, Any]:
    payload = build_payload()
    p_sha = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    body: Dict[str, Any] = {
        "schema": SCHEMA_ID,
        "claim_scope": CLAIM_SCOPE,
        "energy_power_status": ENERGY_POLICY_STATUS,
        "payload": payload,
        "payload_sha256": p_sha,
    }
    c_sha = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    cert = dict(body)
    cert["certificate_sha256"] = c_sha
    return cert


def _verify_certificate_dict_with_live(cert: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    validate_json_value(cert)
    require_ok(type(cert) is dict, "BAD_ROOT", "Certificate root must be dict")
    require_ok(set(cert.keys()) == _CERT_KEYS, "BAD_KEYS", "Certificate top-level keys mismatch")
    require_ok(cert["schema"] == SCHEMA_ID, "BAD_SCHEMA", "Schema mismatch")
    require_ok(cert["claim_scope"] == CLAIM_SCOPE, "BAD_CLAIM_SCOPE", "Claim scope mismatch")
    require_ok(cert["energy_power_status"] == ENERGY_POLICY_STATUS, "BAD_ENERGY_STATUS", "Energy status mismatch")
    got_p_sha = cert["payload_sha256"]
    got_c_sha = cert["certificate_sha256"]
    require_ok(is_hex64(got_p_sha), "BAD_PAYLOAD_SHA", "payload_sha256 must be hex64")
    require_ok(is_hex64(got_c_sha), "BAD_CERT_SHA", "certificate_sha256 must be hex64")

    exp_p_sha = hashlib.sha256(canonical_json_bytes(cert["payload"])).hexdigest()
    require_ok(hmac.compare_digest(got_p_sha, exp_p_sha), "PAYLOAD_SHA_MISMATCH", "payload_sha256 mismatch")
    body = {k: cert[k] for k in cert if k != "certificate_sha256"}
    exp_c_sha = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    require_ok(hmac.compare_digest(got_c_sha, exp_c_sha), "CERT_SHA_MISMATCH", "certificate_sha256 mismatch")

    live_cert = build_certificate()
    require_ok(
        hmac.compare_digest(got_c_sha, live_cert["certificate_sha256"]),
        "RECOMPUTATION_MISMATCH",
        "Certificate does not match exact pure-Z/Q live recomputation",
    )
    live_all_passed = live_cert["payload"]["all_gates_passed"] is True
    require_ok(live_all_passed, "LIVE_GATES_FAILED", "Live recomputation did not pass all gates")
    return (
        {
            "status": "PASS",
            "schema": SCHEMA_ID,
            "claim_scope": CLAIM_SCOPE,
            "payload_sha256": exp_p_sha,
            "certificate_sha256": exp_c_sha,
            "all_gates_passed": live_all_passed,
        },
        live_cert,
    )


def verify_certificate_dict(cert: Any) -> Dict[str, Any]:
    res, _ = _verify_certificate_dict_with_live(cert)
    return res


def verify_self_source_pin(expected_source_sha256: Optional[str] = None) -> str:
    """Read verifier source via O_NOFOLLOW + fstat and enforce optional 64-hex SHA-256 pin across all CLI modes."""
    _, self_sha = _read_source_file(Path(__file__))
    if expected_source_sha256 is not None:
        require_ok(is_hex64(expected_source_sha256), "BAD_SOURCE_SHA", "expected_source_sha256 must be hex64")
        require_ok(
            hmac.compare_digest(self_sha, expected_source_sha256),
            "SOURCE_SHA_MISMATCH",
            "Verifier source SHA-256 mismatch",
        )
    return self_sha


def check_certificate_file(
    path: Path,
    expected_source_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    """Fail-closed verify a certificate JSON file (O_NOFOLLOW + raw-bytes equality + dup-key + live recompute + source pin)."""
    require_ok(isinstance(path, Path), "BAD_PATH", "path must be pathlib.Path")
    self_sha = verify_self_source_pin(expected_source_sha256)
    raw_bytes = _read_regular_bytes_nofollow(path, MAX_JSON_BYTES, "READ_ERR")
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MechanicsAuditError("READ_ERR", f"Invalid UTF-8: {exc}") from exc
    parsed = parse_strict_json(raw_text)
    res, live_cert = _verify_certificate_dict_with_live(parsed)

    # Enforce exact raw-bytes equality against canonical rendered live certificate
    live_bytes = render_certificate_bytes(live_cert)
    got_raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    exp_raw_sha = hashlib.sha256(live_bytes).hexdigest()
    require_ok(
        hmac.compare_digest(got_raw_sha, exp_raw_sha),
        "RAW_BYTES_MISMATCH",
        "Certificate raw file bytes differ from canonical rendered live certificate",
    )
    res["certificate_file_sha256"] = got_raw_sha
    res["verifier_source_sha256"] = self_sha
    return res


def write_certificate_file(
    path: Path,
    expected_source_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    require_ok(isinstance(path, Path), "BAD_PATH", "path must be pathlib.Path")
    verify_self_source_pin(expected_source_sha256)
    _reject_symlink_components(path, "WRITE_ERR")
    cert = build_certificate()
    raw_bytes = render_certificate_bytes(cert)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(path, flags, 0o644)
    except OSError as exc:
        raise MechanicsAuditError("WRITE_ERR", f"Failed to open destination file: {exc}") from exc
    try:
        st = os.fstat(fd)
        require_ok(stat.S_ISREG(st.st_mode), "WRITE_ERR", "Destination must be a regular file")
        offset = 0
        total = len(raw_bytes)
        while offset < total:
            n = os.write(fd, raw_bytes[offset:])
            require_ok(n > 0, "IO_SHORT_WRITE", f"Short or zero-byte write: wrote {offset} of {total} bytes")
            offset += n
    except OSError as exc:
        raise MechanicsAuditError("WRITE_ERR", f"Failed to write certificate: {exc}") from exc
    finally:
        os.close(fd)
    return cert


def _write_stdout_and_flush(text: str) -> None:
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except (OSError, AttributeError) as exc:
        sys.stdout = None  # type: ignore[assignment]
        raise MechanicsAuditError("STDOUT_WRITE_ERR", f"Failed to write stdout: {exc}") from exc


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pure-Z/Q biomimetic x global-historical mechanics audit verifier for optifab"
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--standalone", action="store_true", help="Emit canonical pure-Z/Q certificate (default)")
    group.add_argument("--write", type=Path, help="Write canonical pure-Z/Q certificate to path")
    group.add_argument("--check", type=Path, help="Fail-closed verify a certificate JSON file (raw bytes + schema)")
    parser.add_argument(
        "--expected-source-sha256",
        type=str,
        default=None,
        help="Optional 64-hex SHA-256 pin for this verifier source file (enforced across all modes)",
    )
    args = parser.parse_args(argv)
    try:
        if args.check is not None:
            out: Dict[str, Any] = check_certificate_file(
                args.check,
                expected_source_sha256=args.expected_source_sha256,
            )
            _write_stdout_and_flush(
                json.dumps(out, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
            )
        elif args.write is not None:
            out = write_certificate_file(
                args.write,
                expected_source_sha256=args.expected_source_sha256,
            )
            _write_stdout_and_flush(render_certificate_bytes(out).decode("utf-8"))
        else:
            verify_self_source_pin(args.expected_source_sha256)
            out = build_certificate()
            _write_stdout_and_flush(render_certificate_bytes(out).decode("utf-8"))
        return 0
    except (MechanicsAuditError, ValueError, TypeError, RecursionError, OSError) as exc:
        try:
            sys.stderr.write(f"ERROR: {exc}\n")
            sys.stderr.flush()
        except (OSError, AttributeError):
            sys.stderr = None  # type: ignore[assignment]
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
