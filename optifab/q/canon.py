"""Exact `zone-canon-v1:ascii:` canonical JSON encoder and profile-prefixed SHA-256 receipts.

Matches the cross-language S98 `v1_ascii` profile:
- Printable ASCII (`0x20..0x7E`) emitted raw (with `"` and `\\` escaped).
- `0x7F` DEL and all non-ASCII code points (`>= 0x80`) escaped as lowercase `\\uXXXX`
  (UTF-16 surrogate pairs for astral scalar values `>= U+10000`).
- Object keys are sorted by Unicode scalar code point (`sorted(keys)`), matching CPython
  `json.dumps(sort_keys=True)` and Rust UTF-8 `BTreeMap<String, _>` order (distinct from
  RFC 8785 UTF-16 code-unit order on mixed `U+E000..U+FFFF` vs astral keys).
- NUL (`U+0000`), lone surrogates (`U+D800..U+DFFF`), floats, and non-str keys rejected.
- Uniform pre-expansion DoS ceilings: `1 MiB` output, value depth `<= 64` (root at depth 0;
  any element inside a depth-64 container sits at depth 65 and is rejected), nodes `<= 4,096`,
  signed 256-bit integers `[-2^255, 2^255 - 1]`.
"""

from __future__ import annotations

import hashlib
from typing import Any

from .interval import QError

ZONE_CANON_V1_ASCII_PREFIX = b"zone-canon-v1:ascii:"
OPTIFAB_CERT_PROFILE_ID = b"zone-canon-v1:ascii:optifab-cert-v1"

MAX_INPUT_BYTES = 1_048_576
MAX_DEPTH = 64
MAX_NODES = 4_096
_INT256_MIN = -(1 << 255)
_INT256_MAX = (1 << 255) - 1
MAX_INT_DIGITS = len(str(_INT256_MIN))  # 78 ASCII chars max (leading '-' + 77 digits for -2^255)

_STD_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def _escape_ascii_string(text: str, remaining_bytes: int) -> str:
    if len(text) + 2 > remaining_bytes:
        raise QError("INPUT_TOO_LARGE", f"canonical output exceeds {MAX_INPUT_BYTES} bytes")
    out: list[str] = ['"']
    written = 2
    for ch in text:
        cp = ord(ch)
        if cp == 0:
            raise QError("NUL_FORBIDDEN", "U+0000 NUL character is forbidden in zone-canon-v1")
        if 0xD800 <= cp <= 0xDFFF:
            raise QError("SURROGATE_FORBIDDEN", f"lone surrogate U+{cp:04X} is forbidden")
        esc = _STD_ESCAPES.get(ch)
        if esc is not None:
            piece = esc
        elif 0x20 <= cp < 0x7F:
            piece = ch
        elif cp <= 0xFFFF:
            piece = f"\\u{cp:04x}"
        else:
            adj = cp - 0x10000
            hi = 0xD800 + (adj >> 10)
            lo = 0xDC00 + (adj & 0x3FF)
            piece = f"\\u{hi:04x}\\u{lo:04x}"
        written += len(piece)
        if written > remaining_bytes:
            raise QError("INPUT_TOO_LARGE", f"canonical output exceeds {MAX_INPUT_BYTES} bytes")
        out.append(piece)
    out.append('"')
    return "".join(out)


def encode_zone_canon_v1_ascii(obj: Any) -> bytes:
    """Iteratively validate and encode `obj` into strict `zone-canon-v1:ascii:` canonical bytes."""
    stack: list[tuple[str, Any, int]] = [("VAL", obj, 0)]
    parts: list[str] = []
    nodes = 0
    byte_est = 0

    def _push_emit(lit: str) -> None:
        nonlocal byte_est
        byte_est += len(lit)
        if byte_est > MAX_INPUT_BYTES:
            raise QError("INPUT_TOO_LARGE", f"canonical output exceeds {MAX_INPUT_BYTES} bytes")
        parts.append(lit)

    while stack:
        kind, payload, depth = stack.pop()
        if kind == "EMIT":
            _push_emit(payload)
            continue
        if depth > MAX_DEPTH:
            raise QError("DEPTH_EXCEEDED", f"nesting depth {depth} > {MAX_DEPTH}")
        nodes += 1
        if nodes > MAX_NODES:
            raise QError("NODES_EXCEEDED", f"node count {nodes} > {MAX_NODES}")
        if payload is None:
            _push_emit("null")
        elif type(payload) is bool:
            _push_emit("true" if payload else "false")
        elif type(payload) is int:
            if payload < _INT256_MIN or payload > _INT256_MAX:
                raise QError("INT_OUT_OF_RANGE", "integer outside signed 256-bit zone-canon-v1 range")
            _push_emit(str(payload))
        elif type(payload) is str:
            _push_emit(_escape_ascii_string(payload, MAX_INPUT_BYTES - byte_est))
        elif type(payload) is list or type(payload) is tuple:
            n_items = len(payload)
            if n_items > 0:
                if depth + 1 > MAX_DEPTH:
                    raise QError("DEPTH_EXCEEDED", f"nesting depth {depth + 1} > {MAX_DEPTH}")
                if nodes + n_items > MAX_NODES:
                    raise QError("NODES_EXCEEDED", f"node count exceeds {MAX_NODES}")
            _push_emit("[")
            stack.append(("EMIT", "]", depth))
            for idx in range(n_items - 1, -1, -1):
                stack.append(("VAL", payload[idx], depth + 1))
                if idx > 0:
                    stack.append(("EMIT", ",", depth))
        elif type(payload) is dict:
            n_items = len(payload)
            if n_items > 0:
                if depth + 1 > MAX_DEPTH:
                    raise QError("DEPTH_EXCEEDED", f"nesting depth {depth + 1} > {MAX_DEPTH}")
                if nodes + n_items > MAX_NODES:
                    raise QError("NODES_EXCEEDED", f"node count exceeds {MAX_NODES}")
            for k in payload:
                if type(k) is not str:
                    raise QError("NON_STR_KEY", f"object key must be str, got {type(k).__name__}")
            sorted_keys = sorted(payload.keys())
            _push_emit("{")
            stack.append(("EMIT", "}", depth))
            key_budget = MAX_INPUT_BYTES - byte_est
            for idx in range(n_items - 1, -1, -1):
                k = sorted_keys[idx]
                esc_key = _escape_ascii_string(k, key_budget)
                key_budget -= len(esc_key) + 1 + (1 if idx > 0 else 0)
                if key_budget < 0:
                    raise QError("INPUT_TOO_LARGE", f"canonical output exceeds {MAX_INPUT_BYTES} bytes")
                stack.append(("VAL", payload[k], depth + 1))
                stack.append(("EMIT", esc_key + ":", depth))
                if idx > 0:
                    stack.append(("EMIT", ",", depth))
        else:
            raise QError("UNSUPPORTED_TYPE", f"type {type(payload).__name__!r} is forbidden in zone-canon-v1")

    raw = "".join(parts).encode("ascii")
    if len(raw) > MAX_INPUT_BYTES:
        raise QError("INPUT_TOO_LARGE", f"canonical output exceeds {MAX_INPUT_BYTES} bytes")
    return raw


def sha256_hex(data: bytes) -> str:
    """Compute lowercase hexadecimal SHA-256 digest of exact `bytes`."""
    if type(data) is not bytes:
        raise QError("TYPE_ERROR", f"sha256_hex expects exact bytes, got {type(data).__name__}")
    return hashlib.sha256(data).hexdigest()


def profile_digest(profile_id: bytes, obj: Any) -> str:
    """Compute domain-separated `SHA-256(profile_id || encode_zone_canon_v1_ascii(obj))`.

    Requires `profile_id` to start with `ZONE_CANON_V1_ASCII_PREFIX` plus a non-empty ASCII profile name.
    """
    if type(profile_id) is not bytes or not profile_id.startswith(ZONE_CANON_V1_ASCII_PREFIX):
        raise QError("PROFILE_ID_ERROR", "profile_id must be bytes prefixed with zone-canon-v1:ascii:")
    if len(profile_id) <= len(ZONE_CANON_V1_ASCII_PREFIX):
        raise QError("PROFILE_ID_ERROR", "profile_id must include a non-empty profile name after prefix")
    try:
        profile_id.decode("ascii")
    except UnicodeDecodeError as exc:
        raise QError("PROFILE_ID_ERROR", "profile_id must be pure ASCII") from exc
    return sha256_hex(profile_id + encode_zone_canon_v1_ascii(obj))
