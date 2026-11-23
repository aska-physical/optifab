"""Fail-closed finiteness and Zone-B canonical JSON guards for aska-physical/optifab.

Closes:
- F2: IEEE-754 NaN-swallowing in ``max(...)`` / ``min(...)`` expressions
  (e.g. ``max(0.0, float('nan')) == 0.0`` and ``ball_in_box_check`` / ``plant_radius``
  silently dropping NaN coordinates or margins).
- F3/F4: Zone-B certificate/ledger verification bypasses and unguarded ``json.loads`` crashes
  (symlinks, directories, UTF-8 BOM, CRLF, duplicate keys, NaN/Infinity/1e500, huge integers,
  deep nesting, non-canonical formatting, bool/int/float Python ``==`` coercion).
"""

from __future__ import annotations

import functools
import hashlib
import hmac
import json
import math
import stat
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

MAX_JSON_BYTES = 10485760
MAX_JSON_DEPTH = 64
MAX_INT_DIGITS = 1000
_EXACT_PATH_TYPES = (Path, type(Path(".")))


def require_finite(value: Any, name: str = "value") -> float:
    """Require an exact int or float (rejecting bool, NaN, +/-Inf, float overflow) and return float."""
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be exact int or float, got {type(value).__name__}")
    try:
        out = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} overflows IEEE-754 float") from exc
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return out


def fail_closed_cli(fn: Callable[[], int]) -> Callable[[], int]:
    """Wrap a CLI main() entrypoint so ValueError prints to stderr and returns exit code 1."""
    @functools.wraps(fn)
    def _wrapped() -> int:
        try:
            return fn()
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    return _wrapped


def strict_finite_max(a: Any, b: Any) -> float:
    """Fail-closed ``max(a, b)`` that never silently swallows NaN or non-finite values."""
    fa = require_finite(a, "a")
    fb = require_finite(b, "b")
    return max(fa, fb)


def strict_finite_max_iter(values: Iterable[Any], name: str = "values") -> float:
    """Fail-closed ``max(values)`` rejecting empty iterables, bools, NaN, and +/-Inf."""
    cleaned = [require_finite(v, name) for v in values]
    if not cleaned:
        raise ValueError(f"{name} must be non-empty")
    return max(cleaned)


def coerce_exact_path(path: str | Path) -> Path:
    """Accept exact ``str`` or exact ``Path`` (rejecting subclasses, empty strings, NUL bytes)."""
    if type(path) is str:
        if not path or "\x00" in path:
            raise ValueError("path must be a non-empty string without NUL bytes")
        return Path(path)
    if type(path) in _EXACT_PATH_TYPES:
        if "\x00" in str(path):
            raise ValueError("path must not contain NUL bytes")
        return path
    raise ValueError(f"path must be exact str or Path, got {type(path).__name__}")


def reject_symlinks_on_path(path: Path) -> None:
    """Reject a symlink target or any symlink ancestor component."""
    if path.is_symlink():
        raise ValueError(f"symlink path rejected: {path}")
    for parent in path.parents:
        if parent.is_symlink():
            raise ValueError(f"symlink ancestor rejected: {parent}")


def _reject_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant rejected: {token}")


def _strict_parse_int(token: str) -> int:
    digits = token[1:] if token.startswith("-") else token
    if len(digits) > MAX_INT_DIGITS:
        raise ValueError(f"JSON integer exceeds {MAX_INT_DIGITS}-digit limit")
    return int(token)


def _strict_parse_float(token: str) -> float:
    val = float(token)
    if not math.isfinite(val):
        raise ValueError(f"non-finite JSON float rejected: {token}")
    return val


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key rejected: {key!r}")
        out[key] = val
    return out


def _check_depth(obj: Any, max_depth: int) -> None:
    stack: list[tuple[Any, int]] = [(obj, 0)]
    while stack:
        cur, depth = stack.pop()
        if isinstance(cur, (dict, list)):
            next_depth = depth + 1
            if next_depth > max_depth:
                raise ValueError(f"JSON nesting depth exceeds {max_depth}")
            children = cur.values() if isinstance(cur, dict) else cur
            for child in children:
                stack.append((child, next_depth))


def strict_loads_json(
    text: str,
    *,
    max_bytes: int = MAX_JSON_BYTES,
    max_depth: int = MAX_JSON_DEPTH,
) -> Any:
    """Parse JSON text fail-closed: rejects BOM, CR/CRLF, dup keys, non-finite constants, huge ints, deep nesting."""
    if type(text) is not str:
        raise ValueError(f"json text must be str, got {type(text).__name__}")
    if not text or len(text) > max_bytes:
        raise ValueError(f"json text length out of bounds (1..{max_bytes})")
    if text.startswith("\ufeff"):
        raise ValueError("UTF-8 BOM rejected")
    if "\r" in text:
        raise ValueError("CR/CRLF line endings rejected")
    try:
        obj = json.loads(
            text,
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_reject_constant,
            parse_int=_strict_parse_int,
            parse_float=_strict_parse_float,
        )
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(f"malformed JSON: {exc}") from exc
    _check_depth(obj, max_depth)
    return obj


def strict_parse_json_bytes(
    raw: bytes,
    *,
    max_bytes: int = MAX_JSON_BYTES,
    max_depth: int = MAX_JSON_DEPTH,
) -> Any:
    """Parse raw UTF-8 JSON bytes fail-closed."""
    if type(raw) is not bytes:
        raise ValueError(f"json payload must be bytes, got {type(raw).__name__}")
    if not raw or len(raw) > max_bytes:
        raise ValueError(f"json byte length out of bounds (1..{max_bytes})")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"invalid UTF-8 JSON payload: {exc}") from exc
    return strict_loads_json(text, max_bytes=max_bytes, max_depth=max_depth)


def _read_regular_bytes(path: Path, max_bytes: int = MAX_JSON_BYTES) -> bytes:
    reject_symlinks_on_path(path)
    try:
        st = path.lstat()
    except OSError as exc:
        raise ValueError(f"cannot stat json file {path}: {exc}") from exc
    if not stat.S_ISREG(st.st_mode):
        raise ValueError(f"path is not a regular file: {path}")
    if st.st_size == 0 or st.st_size > max_bytes:
        raise ValueError(f"file size out of bounds (1..{max_bytes}): {st.st_size}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read json file {path}: {exc}") from exc


def strict_read_json(
    path: str | Path,
    *,
    max_bytes: int = MAX_JSON_BYTES,
    max_depth: int = MAX_JSON_DEPTH,
) -> Any:
    """Read and parse a regular JSON file fail-closed."""
    p = coerce_exact_path(path)
    raw = _read_regular_bytes(p, max_bytes=max_bytes)
    return strict_parse_json_bytes(raw, max_bytes=max_bytes, max_depth=max_depth)


def canonical_json_bytes(
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
) -> bytes:
    """Serialize payload to canonical LF-terminated UTF-8 JSON bytes (forbidding NaN/Infinity)."""
    text = json.dumps(
        payload,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        allow_nan=False,
    ) + "\n"
    return text.encode("utf-8")


def verify_canonical_json_file(
    path: str | Path,
    expected_payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
    max_bytes: int = MAX_JSON_BYTES,
    max_depth: int = MAX_JSON_DEPTH,
) -> str:
    """Verify a certificate/ledger JSON file against canonical expected bytes in constant time; return SHA-256."""
    p = coerce_exact_path(path)
    raw = _read_regular_bytes(p, max_bytes=max_bytes)
    parsed = strict_parse_json_bytes(raw, max_bytes=max_bytes, max_depth=max_depth)
    if type(parsed) is not dict:
        raise ValueError("JSON root must be an object")
    expected_bytes = canonical_json_bytes(
        expected_payload,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
    )
    actual_sha = hashlib.sha256(raw).hexdigest()
    expected_sha = hashlib.sha256(expected_bytes).hexdigest()
    if not hmac.compare_digest(actual_sha, expected_sha):
        raise ValueError(f"canonical JSON SHA-256 mismatch: got {actual_sha}, expected {expected_sha}")
    return actual_sha
