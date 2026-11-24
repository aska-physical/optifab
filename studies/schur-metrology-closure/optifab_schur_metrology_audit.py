#!/usr/bin/env python3
"""Hardened CLI, Full Pure-Z/Q Replay & Deep Secondary Auditor for Schur Metrology Closure.

100% pure Python 3 stdlib, zero IEEE-754 floats, zero bare asserts, zero .isdigit(),
zero mathematical RNG (secrets.token_hex used strictly for atomic temp filename uniqueness).
"""
from __future__ import annotations

import errno
from fractions import Fraction
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import stat
import sys
import threading
from typing import Any, Sequence

_THIS_DIR = str(Path(__file__).resolve().parent)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import optifab_schur_metrology_oracle as oracle  # noqa: E402

MAX_JSON_BYTES = 1_048_576
MAX_ALLOWED_CAP_BYTES = 64 * 1024 * 1024
_READ_CHUNK_BYTES = 65_536
MAX_JSON_DEPTH = 64
MAX_JSON_INT_DIGITS = oracle.MAX_INT_DIGITS
_EXACT_PATH_TYPES = (Path, type(Path()))
_HEX_LOWER = frozenset("0123456789abcdef")
_ASCII_DIGITS = frozenset("0123456789")
_DIR_OPEN_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_DARWIN_SYSTEM_ROOT_ALIASES: tuple[tuple[str, str], ...] = (
    ("/var", "/private/var"),
    ("/tmp", "/private/tmp"),
    ("/etc", "/private/etc"),
)
_TEMP_NAME_LOCK = threading.Lock()
_TEMP_COUNTER = 0

_CERT_KEYS = frozenset({"schema_version", "track_id", "payload_sha256", "certificate_sha256", "payload"})
_PAYLOAD_KEYS = frozenset({
    "track_id",
    "portal_ref",
    "novelty_class",
    "prior_literature_n0",
    "pillar1_optifab_physical_anchors",
    "pillar2_schur_offbrane_inertia_closure",
    "pillar3_leontief_euv_consumables_closure",
    "pillar4_plantgate_vs_schur_gate",
    "summary",
})
_P1_KEYS = frozenset({
    "optifab_pin_commit",
    "limit_state_count",
    "binding_limit_state",
    "binding_headroom_q",
    "plant_radius_floored_q",
    "second_tightest_limit_state",
    "second_tightest_headroom_q",
    "missing_sensor_n3_headroom_q",
    "missing_sensor_n4_headroom_q",
    "recooling_max_15C_q",
    "recooling_max_15C_dec6",
    "recooling_max_18C_q",
    "recooling_max_18C_dec6",
    "load_floor_p_min_mw_q",
    "load_floor_p_min_mw_dec6",
    "vibration_tones_hz_q",
    "slow_15ms_tones_passing",
    "fast_0p5ms_tones_passing",
    "euv_rayleigh_metrology",
    "limit_states",
    "all_verified",
})
_P1_EUV_KEYS = frozenset({
    "wavelength_nm_q",
    "numerical_aperture_q",
    "cd_min_nm_q",
    "cd_min_nm_dec6",
    "dof_nm_q",
    "dof_nm_dec6",
    "overlay_budget_nm_q",
    "overlay_budget_nm_dec6",
})
_P1_ROW_KEYS = frozenset({
    "limit_state",
    "source",
    "demand_q",
    "capacity_q",
    "utilisation_q",
    "headroom_q",
    "utilisation_dec6",
})
_P2_KEYS = frozenset({
    "observed_modes",
    "off_brane_modes",
    "rank2_coupled_n3_n4",
    "exact_common_mode_bifurcation",
    "all_verified",
})
_P2_R2_KEYS = frozenset({
    "char_poly_tr_K_q",
    "char_poly_det_K_q",
    "tau_crit_sturm_bracket_q",
    "tau_crit_bracket_width_q",
    "subcritical_tau_1_2",
    "bracket_lower_spd",
    "bracket_upper_collapsed",
    "supercritical_collapsed_tau_1",
    "insufficient_calibration_eta_1_4",
    "restored_calibration_eta_1_2",
    "s37_dark_shadow_energy",
})
_P2_CM_KEYS = frozenset({
    "tau_crit_exact_q",
    "tau_crit_exact_dec6",
    "eta_min_calibration_exact_q",
    "eta_min_calibration_dec6",
    "null_vector_q",
    "null_vector_exact_zero_residual",
    "subcritical_spd",
    "critical_zero_det_boundary",
    "supercritical_collapsed",
    "calibration_below_min_collapsed",
    "calibration_exact_min_boundary",
    "calibration_above_min_restored_spd",
})
_SCHUR_REGIME_KEYS = frozenset({
    "tau_q",
    "eta_cal_q",
    "standalone_A_spd",
    "standalone_D_spd",
    "schur_leading_minors_q",
    "schur_det_q",
    "full_det_q",
    "block_det_identity_exact",
    "schur_inertia_pos_zero_neg",
    "full_inertia_pos_zero_neg",
    "haynsworth_additivity_exact",
    "schur_strictly_spd",
    "negative_witness_vec_q",
    "witness_wT_S_w_q",
    "witness_wT_A_w_q",
})
_SHADOW_KEYS = frozenset({
    "tau_q",
    "det_m_q",
    "det_d_eff_q",
    "det_s_q",
    "schur_det_identity_exact",
    "schur_matches_full_solve_exact",
    "full_energy_q",
    "obs_schur_energy_q",
    "off_brane_shadow_energy_q",
    "shadow_energy_strictly_positive",
    "energy_decomposition_exact",
})
_P3_KEYS = frozenset({
    "bulk_sectors",
    "vitamin_sector",
    "bulk_matrix_q",
    "bulk_leading_minors_q",
    "bulk_det_I_minus_ALL_q",
    "bulk_collatz_wielandt_rho_q",
    "unclosed_consumables_blocked",
    "critical_leverage_scale_alpha_q",
    "critical_zero_det_boundary",
    "design_for_closure_restored",
    "s46_bridge04_crosscheck",
    "all_verified",
})
_P3_BLOCKED_KEYS = frozenset({
    "a_lv_q",
    "a_vl_q",
    "a_vv_q",
    "bulk_det_I_minus_ALL_q",
    "vitamin_leverage_q",
    "schur_complement_S_VV_q",
    "det_I_minus_A5_q",
    "block_det_identity_exact",
    "schur_strictly_positive",
    "unit_demand_solution_q",
    "coupled_inverse_all_positive",
    "unit_demand_all_negative",
})
_P3_CRIT_KEYS = frozenset({
    "a_lv_q",
    "a_vl_q",
    "a_vv_q",
    "bulk_det_I_minus_ALL_q",
    "vitamin_leverage_q",
    "schur_complement_S_VV_q",
    "det_I_minus_A5_q",
    "block_det_identity_exact",
    "schur_strictly_positive",
    "exact_zero_determinant_bifurcation",
})
_P3_RESTORED_KEYS = frozenset({
    "a_lv_q",
    "a_vl_q",
    "a_vv_q",
    "bulk_det_I_minus_ALL_q",
    "vitamin_leverage_q",
    "schur_complement_S_VV_q",
    "det_I_minus_A5_q",
    "block_det_identity_exact",
    "schur_strictly_positive",
    "unit_demand_solution_q",
    "coupled_inverse_all_positive",
    "unit_demand_all_negative",
    "collatz_wielandt_rho_bounds_q",
    "rho_strictly_lt_1",
})
_P3_S46_KEYS = frozenset({
    "s46_bulk_det_q",
    "s46_schur_blocked_q",
    "s46_schur_restored_q",
    "exact_match",
})
_P4_KEYS = frozenset({
    "limit_ppm",
    "operating_tau_q",
    "baseline_u0_ppm",
    "candidate_uc_ppm",
    "diagonal_plant_gate_result",
    "baseline_schur_regime",
    "candidate_uncalibrated_schur_regime",
    "candidate_calibrated_eta_1_schur_regime",
    "diagonal_gate_blind_spot_proven",
    "schur_gate_blocks_uncalibrated_step",
    "schur_gate_admits_calibrated_step",
    "venturi_collar_dual_sensor_power_closure",
    "all_verified",
})
_P4_GATE_KEYS = frozenset({
    "admitted",
    "headroom_radius_ppm",
    "dist_sq_ppm2",
    "radius_sq_ppm2",
    "remaining_budget",
    "all_cand_below_limit",
})
_P4_VENTURI_KEYS = frozenset({
    "harvest_1p8ms_mw_q",
    "single_node_power_mw_q",
    "one_node_utilisation_q",
    "two_nodes_n3_n4_utilisation_q",
    "large_150uW_node_utilisation_q",
    "single_collar_supports_n3_plus_n4",
    "min_collars_for_continuous_n3_n4",
    "max_single_collar_shared_duty_q",
})
_SUMMARY_KEYS = frozenset({
    "pillar_count",
    "all_four_pillars_verified",
    "float_count_on_trust_path",
    "bare_assert_count",
    "rng_calls",
})


# ============================================================================
# 1. Zone-B Path, CWD, Atomic dir_fd Traversal & Durable 0o600 Atomic Write
# ============================================================================

def _require_utf8_no_surrogate(text: Any, label: str) -> str:
    if type(text) is not str:
        raise oracle.OptifabSchurError("INVALID_STR", f"{label}: exact str required")
    oracle.require_ok("\x00" not in text, "NUL_BYTE_FORBIDDEN", f"{label}: NUL byte forbidden")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise oracle.OptifabSchurError("INVALID_UTF8_SURROGATE", f"{label}: lone UTF-16 surrogate forbidden") from exc
    return text


def _require_concrete_path(path: Any, label: str) -> Path:
    oracle.require_ok(type(path) in _EXACT_PATH_TYPES, "INVALID_PATH_TYPE", f"{label}: concrete pathlib.Path required")
    _require_utf8_no_surrogate(str(path), label)
    return path


def _normalize_darwin_system_prefix(path: Path, *, allow_exact: bool = False) -> Path:
    """Map verified root-owned macOS /var, /tmp, /etc aliases to /private/* without resolving user symlinks."""
    if sys.platform != "darwin" or not path.is_absolute():
        return path
    parts = path.parts
    min_parts = 2 if allow_exact else 3
    if len(parts) < min_parts or ".." in parts:
        return path
    top = "/" + parts[1]
    for alias, canonical in _DARWIN_SYSTEM_ROOT_ALIASES:
        if top != alias:
            continue
        try:
            st = os.lstat(alias)
            if not stat.S_ISLNK(st.st_mode) or st.st_uid != 0:
                return path
            target = os.readlink(alias)
            if target not in (canonical, canonical.lstrip("/")):
                return path
        except OSError:
            return path
        return Path(canonical, *parts[2:])
    return path


def _safe_cwd(label: str) -> Path:
    try:
        return Path.cwd()
    except OSError as exc:
        raise oracle.OptifabSchurError("CWD_UNAVAILABLE", f"{label}: CWD unavailable ({type(exc).__name__})") from exc


def _check_pwd_no_symlinks(label: str) -> None:
    pwd = os.environ.get("PWD", "")
    if not pwd.startswith("/"):
        return
    _require_utf8_no_surrogate(pwd, f"{label} PWD")
    try:
        st_pwd = os.stat(pwd)
        st_dot = os.stat(".")
    except OSError:
        return
    if (st_pwd.st_dev, st_pwd.st_ino) != (st_dot.st_dev, st_dot.st_ino):
        return
    pwd_path = _normalize_darwin_system_prefix(Path(pwd), allow_exact=True)
    try:
        dfd = os.open("/", _DIR_OPEN_FLAGS)
    except OSError as exc:
        raise oracle.OptifabSchurError("CWD_UNAVAILABLE", f"{label}: cannot open root for PWD") from exc
    try:
        for part in pwd_path.parts[1:]:
            if part == ".":
                continue
            try:
                next_fd = os.open(part, _DIR_OPEN_FLAGS, dir_fd=dfd)
            except OSError as exc:
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise oracle.OptifabSchurError(
                        "SYMLINK_ANCESTOR_FORBIDDEN", f"{label}: symlink PWD ancestor forbidden"
                    ) from exc
                raise oracle.OptifabSchurError(
                    "CWD_UNAVAILABLE", f"{label}: PWD ancestor unavailable ({type(exc).__name__})"
                ) from exc
            os.close(dfd)
            dfd = next_fd
    finally:
        os.close(dfd)


def _open_dir_chain(target: Path, label: str, *, create_parents: bool) -> tuple[int, str]:
    if target.is_absolute():
        norm_target = _normalize_darwin_system_prefix(target)
        parts = norm_target.parts[1:]
    else:
        cwd = _normalize_darwin_system_prefix(_safe_cwd(label), allow_exact=True)
        _check_pwd_no_symlinks(label)
        parts = cwd.parts[1:] + target.parts
    oracle.require_ok(
        len(parts) >= 1 and parts[-1] not in ("", ".", ".."),
        "NOT_A_REGULAR_FILE",
        f"{label}: path does not name a regular file leaf",
    )
    parent_parts = parts[:-1]
    leaf = parts[-1]
    err_code = "FILE_WRITE_ERROR" if create_parents else "FILE_READ_ERROR"
    try:
        dfd = os.open("/", _DIR_OPEN_FLAGS)
    except OSError as exc:
        raise oracle.OptifabSchurError(err_code, f"{label}: cannot open root") from exc
    try:
        for part in parent_parts:
            if part == ".":
                continue
            try:
                next_fd = os.open(part, _DIR_OPEN_FLAGS, dir_fd=dfd)
            except OSError as exc:
                if create_parents and exc.errno == errno.ENOENT:
                    try:
                        os.mkdir(part, 0o755, dir_fd=dfd)
                    except FileExistsError:
                        pass
                    except OSError as mk_exc:
                        raise oracle.OptifabSchurError(
                            "FILE_WRITE_ERROR", f"{label}: mkdir failed ({type(mk_exc).__name__})"
                        ) from mk_exc
                    try:
                        next_fd = os.open(part, _DIR_OPEN_FLAGS, dir_fd=dfd)
                    except OSError as re_exc:
                        raise oracle.OptifabSchurError(
                            "FILE_WRITE_ERROR", f"{label}: cannot open created dir ({type(re_exc).__name__})"
                        ) from re_exc
                elif exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise oracle.OptifabSchurError(
                        "SYMLINK_FORBIDDEN", f"{label}: symlink or non-directory ancestor forbidden"
                    ) from exc
                else:
                    raise oracle.OptifabSchurError(
                        err_code, f"{label}: cannot traverse ancestor ({type(exc).__name__})"
                    ) from exc
            os.close(dfd)
            dfd = next_fd
        return dfd, leaf
    except BaseException:
        os.close(dfd)
        raise


def read_regular_bytes_capped(path: Path, label: str = "file", max_bytes: int = MAX_JSON_BYTES) -> bytes:
    target = _require_concrete_path(path, label)
    oracle.require_exact_int(max_bytes, "max_bytes", lo=1, hi=MAX_ALLOWED_CAP_BYTES)
    dfd, leaf = _open_dir_chain(target, label, create_parents=False)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        try:
            fd = os.open(leaf, flags, dir_fd=dfd)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise oracle.OptifabSchurError("SYMLINK_FORBIDDEN", f"{label}: symlink leaf forbidden") from exc
            raise oracle.OptifabSchurError(
                "FILE_READ_ERROR", f"{label}: cannot open ({type(exc).__name__})"
            ) from exc
    finally:
        os.close(dfd)

    chunks: list[bytes] = []
    total = 0
    try:
        st_f = os.fstat(fd)
        oracle.require_ok(stat.S_ISREG(st_f.st_mode), "NOT_A_REGULAR_FILE", f"{label}: not a regular file")
        while total <= max_bytes:
            chunk = os.read(fd, min(_READ_CHUNK_BYTES, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
    except oracle.OptifabSchurError:
        raise
    except OSError as exc:
        raise oracle.OptifabSchurError("FILE_READ_ERROR", f"{label}: read failed ({type(exc).__name__})") from exc
    finally:
        os.close(fd)
    oracle.require_ok(total <= max_bytes, "FILE_TOO_LARGE", f"{label}: exceeds {max_bytes} bytes")
    return b"".join(chunks)


def write_regular_bytes_safe(path: Path, payload: bytes, label: str = "output") -> None:
    global _TEMP_COUNTER
    oracle.require_ok(type(payload) is bytes, "INVALID_PAYLOAD_BYTES", f"{label}: payload must be exact bytes")
    target = _require_concrete_path(path, label)
    dfd, leaf = _open_dir_chain(target, label, create_parents=True)
    tmp_name: str | None = None
    try:
        try:
            st_existing = os.lstat(leaf, dir_fd=dfd)
        except FileNotFoundError:
            st_existing = None
        except OSError as exc:
            raise oracle.OptifabSchurError(
                "FILE_WRITE_ERROR", f"{label}: lstat failed ({type(exc).__name__})"
            ) from exc
        if st_existing is not None:
            oracle.require_ok(not stat.S_ISLNK(st_existing.st_mode), "SYMLINK_FORBIDDEN", f"{label}: symlink leaf forbidden")
            oracle.require_ok(stat.S_ISREG(st_existing.st_mode), "NOT_A_REGULAR_FILE", f"{label}: non-regular target")
            oracle.require_ok(st_existing.st_nlink <= 1, "HARDLINK_FORBIDDEN", f"{label}: hardlinked target forbidden")

        pid = os.getpid()
        for _ in range(32):
            with _TEMP_NAME_LOCK:
                _TEMP_COUNTER += 1
                seq_num = _TEMP_COUNTER
                cand = f".s51.{pid}.{seq_num}.{secrets.token_hex(8)}.tmp"
            try:
                fd = os.open(
                    cand,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_NONBLOCK,
                    0o600,
                    dir_fd=dfd,
                )
                tmp_name = cand
                break
            except FileExistsError:
                continue
            except OSError as exc:
                raise oracle.OptifabSchurError(
                    "FILE_WRITE_ERROR", f"{label}: create temp failed ({type(exc).__name__})"
                ) from exc
        else:
            raise oracle.OptifabSchurError("FILE_WRITE_ERROR", f"{label}: exhausted temp file slots")

        try:
            view = memoryview(payload)
            written = 0
            while written < len(view):
                written += os.write(fd, view[written:])
            os.fsync(fd)
            st_tmp = os.fstat(fd)
            oracle.require_ok(st_tmp.st_nlink == 1, "HARDLINK_FORBIDDEN", f"{label}: temp link count altered")
        except oracle.OptifabSchurError:
            raise
        except OSError as exc:
            raise oracle.OptifabSchurError(
                "FILE_WRITE_ERROR", f"{label}: write failed ({type(exc).__name__})"
            ) from exc
        finally:
            os.close(fd)

        try:
            os.replace(tmp_name, leaf, src_dir_fd=dfd, dst_dir_fd=dfd)
            tmp_name = None
            os.fsync(dfd)
        except OSError as exc:
            raise oracle.OptifabSchurError(
                "FILE_WRITE_ERROR", f"{label}: atomic replace failed ({type(exc).__name__})"
            ) from exc
    finally:
        if tmp_name is not None:
            try:
                os.unlink(tmp_name, dir_fd=dfd)
            except OSError:
                pass
        os.close(dfd)


# ============================================================================
# 2. Strict ASCII Parsers, Binding 3,321-Bit Cap & Canonical JSON
# ============================================================================

def require_hex64_lower_ascii(val: Any, label: str = "sha256") -> str:
    s = _require_utf8_no_surrogate(val, label)
    oracle.require_ok(len(s) == 64, "INVALID_HEX64", f"{label}: expected 64-char lowercase ASCII hex")
    for ch in s:
        oracle.require_ok(ch in _HEX_LOWER, "INVALID_HEX64", f"{label}: non-hex-lowercase char")
    return s


def _parse_bounded_int(token: str) -> int:
    s = _require_utf8_no_surrogate(token, "json_int")
    oracle.require_ok(s != "-0", "INVALID_JSON_INT", "negative zero forbidden")
    digits = s[1:] if s.startswith("-") else s
    oracle.require_ok(len(digits) >= 1, "INVALID_JSON_INT", "JSON int has no digits")
    oracle.require_ok(len(digits) <= MAX_JSON_INT_DIGITS, "INT_DIGIT_LIMIT", "JSON int exceeds digit cap")
    oracle.require_ok(digits == "0" or not digits.startswith("0"), "INVALID_JSON_INT", "leading zero forbidden")
    for ch in digits:
        oracle.require_ok(ch in _ASCII_DIGITS, "INVALID_JSON_INT", "non-ASCII digit forbidden")
    val = int(s)
    oracle.require_ok(val.bit_length() <= oracle.MAX_INT_BITS, "INT_BIT_LIMIT", "JSON int exceeds 3,321-bit cap")
    return val


def parse_exact_rational(token: Any, label: str = "rational") -> Fraction:
    s = _require_utf8_no_surrogate(token, label)
    parts = s.split("/")
    oracle.require_ok(len(parts) in (1, 2), "INVALID_RATIONAL", f"{label}: expected 'n' or 'n/d'")
    num = _parse_bounded_int(parts[0])
    if len(parts) == 1:
        return oracle.require_exact_fraction(Fraction(num, 1), label)
    den = _parse_bounded_int(parts[1])
    oracle.require_ok(den >= 2, "INVALID_RATIONAL", f"{label}: denominator must be >= 2")
    oracle.require_ok(math.gcd(abs(num), den) == 1, "NON_CANONICAL_RATIONAL", f"{label}: not in lowest terms")
    return oracle.require_exact_fraction(Fraction(num, den), label)


def _validate_json_tree(root: Any, label: str = "json") -> None:
    stack: list[tuple[Any, int]] = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        oracle.require_ok(depth <= MAX_JSON_DEPTH, "JSON_DEPTH_LIMIT", f"{label}: nesting exceeds {MAX_JSON_DEPTH}")
        t = type(node)
        if node is None or t is bool:
            continue
        if t is int:
            oracle.require_ok(node.bit_length() <= oracle.MAX_INT_BITS, "INT_BIT_LIMIT", f"{label}: int exceeds 3,321 bits")
            continue
        if t is str:
            _require_utf8_no_surrogate(node, label)
            continue
        if t is list:
            nxt = depth + 1
            for item in node:
                stack.append((item, nxt))
            continue
        if t is dict:
            nxt = depth + 1
            for k, v in node.items():
                _require_utf8_no_surrogate(k, f"{label}.key")
                stack.append((v, nxt))
            continue
        raise oracle.OptifabSchurError("FORBIDDEN_JSON_TYPE", f"{label}: unsupported type {t.__name__}")


def _reject_float(token: str) -> Any:
    raise oracle.OptifabSchurError("FLOAT_LITERAL_FORBIDDEN", f"float literal forbidden: {token}")


def _reject_constant(token: str) -> Any:
    raise oracle.OptifabSchurError("NONFINITE_LITERAL_FORBIDDEN", f"non-finite constant forbidden: {token}")


def _strict_pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        _require_utf8_no_surrogate(k, "json_key")
        oracle.require_ok(k not in out, "DUPLICATE_JSON_KEY", f"duplicate key {k!r}")
        out[k] = v
    return out


def parse_strict_json_text(text: Any, *, require_object: bool = True, max_bytes: int = MAX_JSON_BYTES) -> Any:
    s = _require_utf8_no_surrogate(text, "json_text")
    oracle.require_exact_bool(require_object, "require_object")
    oracle.require_exact_int(max_bytes, "max_bytes", lo=1, hi=MAX_ALLOWED_CAP_BYTES)
    oracle.require_ok(len(s.encode("utf-8")) <= max_bytes, "JSON_TOO_LARGE", "JSON text exceeds byte cap")
    try:
        parsed = json.loads(
            s,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
            parse_int=_parse_bounded_int,
            object_pairs_hook=_strict_pairs_hook,
        )
    except oracle.OptifabSchurError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise oracle.OptifabSchurError("JSON_PARSE_ERROR", f"invalid JSON ({type(exc).__name__})") from exc
    _validate_json_tree(parsed, "parsed_json")
    if require_object and type(parsed) is not dict:
        raise oracle.OptifabSchurError("JSON_ROOT_NOT_OBJECT", "JSON root must be an object")
    return parsed


def canonical_json_bytes(obj: Any) -> bytes:
    _validate_json_tree(obj, "canonical_json")
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256_canonical(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


# ============================================================================
# 3. Deep Schema-Safe Secondary Auditor (Live Algebraic & Strict Nested Keys)
# ============================================================================

def _req_dict(val: Any, label: str, expected_keys: frozenset[str]) -> dict[str, Any]:
    oracle.require_ok(type(val) is dict, "INVALID_SCHEMA_DICT", f"{label}: exact dict required")
    oracle.require_ok(frozenset(val.keys()) == expected_keys, "INVALID_SCHEMA_KEYS", f"{label}: key set mismatch")
    return val


def _req_list(val: Any, label: str, exact_len: int) -> list[Any]:
    oracle.require_ok(type(val) is list and len(val) == exact_len, "INVALID_SCHEMA_LIST", f"{label}: list len {exact_len} required")
    return val


def _req_int_f(obj: dict[str, Any], key: str, label: str) -> int:
    return oracle.require_exact_int(obj[key], f"{label}.{key}")


def _req_bool_f(obj: dict[str, Any], key: str, label: str) -> bool:
    return oracle.require_exact_bool(obj[key], f"{label}.{key}")


def _parse_q_matrix(val: Any, dim: int, label: str) -> list[list[Fraction]]:
    rows = _req_list(val, label, dim)
    return [
        [parse_exact_rational(tok, f"{label}[{i}][{j}]") for j, tok in enumerate(_req_list(row, f"{label}[{i}]", dim))]
        for i, row in enumerate(rows)
    ]


def _audit_schur_regime(val: Any, label: str) -> bool:
    rd = _req_dict(val, label, _SCHUR_REGIME_KEYS)
    parse_exact_rational(rd["tau_q"], f"{label}.tau")
    parse_exact_rational(rd["eta_cal_q"], f"{label}.eta")
    minors = [parse_exact_rational(tok, f"{label}.m[{i}]") for i, tok in enumerate(_req_list(rd["schur_leading_minors_q"], f"{label}.minors", 4))]
    det_s = parse_exact_rational(rd["schur_det_q"], f"{label}.det_s")
    parse_exact_rational(rd["full_det_q"], f"{label}.det_m")
    in_s = [_req_int_f({"v": x}, "v", f"{label}.in_s[{i}]") for i, x in enumerate(_req_list(rd["schur_inertia_pos_zero_neg"], f"{label}.in_s", 3))]
    in_m = [_req_int_f({"v": x}, "v", f"{label}.in_m[{i}]") for i, x in enumerate(_req_list(rd["full_inertia_pos_zero_neg"], f"{label}.in_m", 3))]
    return all((
        _req_bool_f(rd, "standalone_A_spd", label),
        _req_bool_f(rd, "standalone_D_spd", label),
        _req_bool_f(rd, "block_det_identity_exact", label),
        _req_bool_f(rd, "haynsworth_additivity_exact", label),
        type(_req_bool_f(rd, "schur_strictly_spd", label)) is bool,
        minors[-1] == det_s,
        sum(in_s) == 4,
        sum(in_m) == 6,
    ))


def secondary_audit_payload(payload: Any) -> dict[str, Any]:
    """Fail-closed strict-nested-keyset + live algebraic cross-check across ALL 4 pillars."""
    _validate_json_tree(payload, "payload")
    pl = _req_dict(payload, "payload", _PAYLOAD_KEYS)
    p1 = _req_dict(pl["pillar1_optifab_physical_anchors"], "p1", _P1_KEYS)
    p1_euv = _req_dict(p1["euv_rayleigh_metrology"], "p1.euv", _P1_EUV_KEYS)
    p2 = _req_dict(pl["pillar2_schur_offbrane_inertia_closure"], "p2", _P2_KEYS)
    p2_r2 = _req_dict(p2["rank2_coupled_n3_n4"], "p2.r2", _P2_R2_KEYS)
    p2_cm = _req_dict(p2["exact_common_mode_bifurcation"], "p2.cm", _P2_CM_KEYS)
    p2_sh = _req_dict(p2_r2["s37_dark_shadow_energy"], "p2.shadow", _SHADOW_KEYS)
    p3 = _req_dict(pl["pillar3_leontief_euv_consumables_closure"], "p3", _P3_KEYS)
    p3_b = _req_dict(p3["unclosed_consumables_blocked"], "p3.blk", _P3_BLOCKED_KEYS)
    p3_c = _req_dict(p3["critical_zero_det_boundary"], "p3.crit", _P3_CRIT_KEYS)
    p3_r = _req_dict(p3["design_for_closure_restored"], "p3.res", _P3_RESTORED_KEYS)
    p3_s46 = _req_dict(p3["s46_bridge04_crosscheck"], "p3.s46", _P3_S46_KEYS)
    p4 = _req_dict(pl["pillar4_plantgate_vs_schur_gate"], "p4", _P4_KEYS)
    p4_g = _req_dict(p4["diagonal_plant_gate_result"], "p4.gate", _P4_GATE_KEYS)
    p4_v = _req_dict(p4["venturi_collar_dual_sensor_power_closure"], "p4.venturi", _P4_VENTURI_KEYS)
    summ = _req_dict(pl["summary"], "summary", _SUMMARY_KEYS)

    ref_p1 = oracle.certify_pillar1_optifab_physical_anchors()
    ref_p2 = oracle.certify_pillar2_schur_offbrane_inertia_closure()
    ref_p3 = oracle.certify_pillar3_leontief_euv_consumables_closure()
    ref_p4 = oracle.certify_pillar4_plantgate_vs_schur_gate()

    # Pillar 1 strict nested checks & rational parse
    ls_rows = _req_list(p1["limit_states"], "p1.limit_states", 12)
    p1_rows_ok = True
    for i, row in enumerate(ls_rows):
        rd = _req_dict(row, f"p1.ls[{i}]", _P1_ROW_KEYS)
        dem = parse_exact_rational(rd["demand_q"], f"p1.ls[{i}].dem")
        cap = parse_exact_rational(rd["capacity_q"], f"p1.ls[{i}].cap")
        oracle.require_ok(cap > oracle.Q0, "INVALID_CAPACITY", f"p1.ls[{i}].cap must be > 0")
        util = parse_exact_rational(rd["utilisation_q"], f"p1.ls[{i}].util")
        hr = parse_exact_rational(rd["headroom_q"], f"p1.ls[{i}].hr")
        if not all((dem == util * cap, oracle.Q1 - util == hr)):
            p1_rows_ok = False
    p1_ok = all((
        _req_int_f(p1, "limit_state_count", "p1") == 12,
        _req_int_f(p1, "slow_15ms_tones_passing", "p1") == 0,
        _req_int_f(p1, "fast_0p5ms_tones_passing", "p1") == 4,
        _req_bool_f(p1, "all_verified", "p1"),
        parse_exact_rational(p1_euv["cd_min_nm_q"], "p1.euv.cd") == Fraction(81, 11),
        p1_rows_ok,
        canonical_json_bytes(p1) == canonical_json_bytes(ref_p1),
    ))

    # Pillar 2 strict regime checks + shadow energy cross-check
    r2_regime_ok = all(
        _audit_schur_regime(p2_r2[k], f"p2.r2.{k}")
        for k in (
            "subcritical_tau_1_2",
            "bracket_lower_spd",
            "bracket_upper_collapsed",
            "supercritical_collapsed_tau_1",
            "insufficient_calibration_eta_1_4",
            "restored_calibration_eta_1_2",
        )
    )
    cm_regime_ok = all(
        _audit_schur_regime(p2_cm[k], f"p2.cm.{k}")
        for k in (
            "subcritical_spd",
            "critical_zero_det_boundary",
            "supercritical_collapsed",
            "calibration_below_min_collapsed",
            "calibration_exact_min_boundary",
            "calibration_above_min_restored_spd",
        )
    )
    e_full = parse_exact_rational(p2_sh["full_energy_q"], "p2.sh.full")
    e_obs = parse_exact_rational(p2_sh["obs_schur_energy_q"], "p2.sh.obs")
    e_off = parse_exact_rational(p2_sh["off_brane_shadow_energy_q"], "p2.sh.off")
    p2_ok = all((
        _req_bool_f(p2, "all_verified", "p2"),
        _req_bool_f(p2_cm, "null_vector_exact_zero_residual", "p2.cm"),
        _req_bool_f(p2_sh, "schur_det_identity_exact", "p2.sh"),
        _req_bool_f(p2_sh, "schur_matches_full_solve_exact", "p2.sh"),
        _req_bool_f(p2_sh, "shadow_energy_strictly_positive", "p2.sh"),
        _req_bool_f(p2_sh, "energy_decomposition_exact", "p2.sh"),
        e_full == e_obs + e_off,
        r2_regime_ok,
        cm_regime_ok,
        canonical_json_bytes(p2) == canonical_json_bytes(ref_p2),
    ))

    # Pillar 3 live Bareiss determinant & block-Schur cross-check
    a_ll = _parse_q_matrix(p3["bulk_matrix_q"], 4, "p3.bulk")
    det_ll_live = oracle.bareiss_det_exact(oracle.identity_minus_q(a_ll))
    s_b = parse_exact_rational(p3_b["schur_complement_S_VV_q"], "p3.b.S")
    d5_b = parse_exact_rational(p3_b["det_I_minus_A5_q"], "p3.b.d5")
    s_c = parse_exact_rational(p3_c["schur_complement_S_VV_q"], "p3.c.S")
    d5_c = parse_exact_rational(p3_c["det_I_minus_A5_q"], "p3.c.d5")
    s_r = parse_exact_rational(p3_r["schur_complement_S_VV_q"], "p3.r.S")
    d5_r = parse_exact_rational(p3_r["det_I_minus_A5_q"], "p3.r.d5")
    p3_ok = all((
        _req_bool_f(p3, "all_verified", "p3"),
        _req_bool_f(p3_b, "block_det_identity_exact", "p3.b"),
        not _req_bool_f(p3_b, "schur_strictly_positive", "p3.b"),
        not _req_bool_f(p3_b, "coupled_inverse_all_positive", "p3.b"),
        _req_bool_f(p3_b, "unit_demand_all_negative", "p3.b"),
        _req_bool_f(p3_c, "block_det_identity_exact", "p3.c"),
        not _req_bool_f(p3_c, "schur_strictly_positive", "p3.c"),
        _req_bool_f(p3_c, "exact_zero_determinant_bifurcation", "p3.c"),
        _req_bool_f(p3_r, "block_det_identity_exact", "p3.r"),
        _req_bool_f(p3_r, "schur_strictly_positive", "p3.r"),
        _req_bool_f(p3_r, "coupled_inverse_all_positive", "p3.r"),
        not _req_bool_f(p3_r, "unit_demand_all_negative", "p3.r"),
        _req_bool_f(p3_r, "rho_strictly_lt_1", "p3.r"),
        _req_bool_f(p3_s46, "exact_match", "p3.s46"),
        parse_exact_rational(p3["bulk_det_I_minus_ALL_q"], "p3.det_ll") == det_ll_live,
        d5_b == det_ll_live * s_b,
        d5_c == det_ll_live * s_c,
        d5_r == det_ll_live * s_r,
        canonical_json_bytes(p3) == canonical_json_bytes(ref_p3),
    ))

    # Pillar 4 exact integer PlantGate + Schur regimes + venturi power check
    p4_regimes_ok = all(
        _audit_schur_regime(p4[k], f"p4.{k}")
        for k in (
            "baseline_schur_regime",
            "candidate_uncalibrated_schur_regime",
            "candidate_calibrated_eta_1_schur_regime",
        )
    )
    r_ppm = _req_int_f(p4_g, "headroom_radius_ppm", "p4.gate")
    p4_ok = all((
        _req_int_f(p4, "limit_ppm", "p4") == 1_000_000,
        _req_bool_f(p4_g, "admitted", "p4.gate"),
        _req_bool_f(p4_g, "all_cand_below_limit", "p4.gate"),
        _req_int_f(p4_g, "dist_sq_ppm2", "p4.gate") <= _req_int_f(p4_g, "radius_sq_ppm2", "p4.gate"),
        _req_int_f(p4_g, "radius_sq_ppm2", "p4.gate") == r_ppm * r_ppm,
        _req_int_f(p4_g, "remaining_budget", "p4.gate") == 63,
        _req_bool_f(p4, "diagonal_gate_blind_spot_proven", "p4"),
        _req_bool_f(p4, "schur_gate_blocks_uncalibrated_step", "p4"),
        _req_bool_f(p4, "schur_gate_admits_calibrated_step", "p4"),
        not _req_bool_f(p4_v, "single_collar_supports_n3_plus_n4", "p4.venturi"),
        _req_int_f(p4_v, "min_collars_for_continuous_n3_n4", "p4.venturi") == 2,
        _req_bool_f(p4, "all_verified", "p4"),
        p4_regimes_ok,
        canonical_json_bytes(p4) == canonical_json_bytes(ref_p4),
    ))

    ok_all = all((
        pl["track_id"] == oracle.TRACK_ID,
        pl["portal_ref"] == oracle.PORTAL_REF,
        pl["novelty_class"] == oracle.NOVELTY_CLASS,
        canonical_json_bytes(pl["prior_literature_n0"]) == canonical_json_bytes(oracle.PRIOR_LITERATURE_N0),
        p1_ok,
        p2_ok,
        p3_ok,
        p4_ok,
        _req_int_f(summ, "pillar_count", "summary") == 4,
        _req_bool_f(summ, "all_four_pillars_verified", "summary"),
        _req_int_f(summ, "float_count_on_trust_path", "summary") == 0,
        _req_int_f(summ, "bare_assert_count", "summary") == 0,
        _req_int_f(summ, "rng_calls", "summary") == 0,
    ))
    oracle.require_ok(ok_all, "SECONDARY_AUDIT_FAILED", "secondary algebraic cross-check failed")
    return {"secondary_audit_passed": True, "pillars_audited": 4}


def build_standalone_certificate() -> dict[str, Any]:
    payload = oracle.build_payload()
    payload_sha = _sha256_canonical(payload)
    outer = {
        "schema_version": oracle.SCHEMA_VERSION,
        "track_id": oracle.TRACK_ID,
        "payload_sha256": payload_sha,
        "payload": payload,
    }
    cert_sha = _sha256_canonical(outer)
    return {
        "schema_version": oracle.SCHEMA_VERSION,
        "track_id": oracle.TRACK_ID,
        "payload_sha256": payload_sha,
        "certificate_sha256": cert_sha,
        "payload": payload,
    }


def verify_certificate_dict(cert: Any, *, full_replay: bool = True) -> dict[str, Any]:
    oracle.require_exact_bool(full_replay, "full_replay")
    oracle.require_ok(type(cert) is dict, "INVALID_CERT_TYPE", "certificate must be exact dict")
    _validate_json_tree(cert, "cert")
    oracle.require_ok(frozenset(cert.keys()) == _CERT_KEYS, "INVALID_CERT_KEYS", "certificate keys mismatch")
    oracle.require_ok(cert["schema_version"] == oracle.SCHEMA_VERSION, "INVALID_SCHEMA", "schema_version mismatch")
    oracle.require_ok(cert["track_id"] == oracle.TRACK_ID, "INVALID_TRACK_ID", "track_id mismatch")
    oracle.require_ok(type(cert["payload"]) is dict, "INVALID_PAYLOAD_TYPE", "payload must be exact dict")

    claimed_p = require_hex64_lower_ascii(cert["payload_sha256"], "payload_sha256")
    claimed_c = require_hex64_lower_ascii(cert["certificate_sha256"], "certificate_sha256")

    actual_p = _sha256_canonical(cert["payload"])
    oracle.require_ok(hmac.compare_digest(claimed_p, actual_p), "PAYLOAD_SHA256_MISMATCH", "payload_sha256 mismatch")

    outer = {
        "schema_version": cert["schema_version"],
        "track_id": cert["track_id"],
        "payload_sha256": claimed_p,
        "payload": cert["payload"],
    }
    actual_c = _sha256_canonical(outer)
    oracle.require_ok(hmac.compare_digest(claimed_c, actual_c), "CERT_SHA256_MISMATCH", "certificate_sha256 mismatch")

    sec = secondary_audit_payload(cert["payload"])
    if full_replay:
        ref = build_standalone_certificate()
        oracle.require_ok(hmac.compare_digest(actual_p, ref["payload_sha256"]), "REPLAY_MISMATCH", "replay mismatch")

    return {
        "valid": True,
        "schema_version": oracle.SCHEMA_VERSION,
        "track_id": oracle.TRACK_ID,
        "payload_sha256": actual_p,
        "certificate_sha256": actual_c,
        "full_replay": full_replay,
        "secondary_audit": sec,
    }


def check_certificate_file(path: Path, *, full_replay: bool = True) -> dict[str, Any]:
    raw = read_regular_bytes_capped(path, "certificate", MAX_JSON_BYTES)
    oracle.require_ok(b"\r" not in raw, "CRLF_FORBIDDEN", "CRLF line endings forbidden")
    oracle.require_ok(raw.endswith(b"\n"), "MISSING_TRAILING_LF", "certificate must end with LF")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise oracle.OptifabSchurError("INVALID_UTF8", "certificate is not valid UTF-8") from exc
    cert = parse_strict_json_text(text, require_object=True)
    canon = canonical_json_bytes(cert)
    oracle.require_ok(raw == canon + b"\n", "NON_CANONICAL_BYTES", "certificate is not canonical ASCII JSON + LF")
    res = verify_certificate_dict(cert, full_replay=full_replay)
    res["canonical_sha256"] = hashlib.sha256(canon).hexdigest()
    res["file_sha256"] = hashlib.sha256(raw).hexdigest()
    return res


def write_certificate_file(path: Path) -> dict[str, Any]:
    cert = build_standalone_certificate()
    canon = canonical_json_bytes(cert)
    raw = canon + b"\n"
    write_regular_bytes_safe(path, raw, "certificate")
    return {
        "written": True,
        "schema_version": oracle.SCHEMA_VERSION,
        "track_id": oracle.TRACK_ID,
        "payload_sha256": cert["payload_sha256"],
        "certificate_sha256": cert["certificate_sha256"],
        "file_sha256": hashlib.sha256(raw).hexdigest(),
    }


# ============================================================================
# 4. Strict Fail-Closed CLI (Space & Equals Flag-Like Rejection)
# ============================================================================

def _reject_bad_path_arg(tok: str, val: str) -> Path:
    oracle.require_ok(bool(val) and not val.startswith("-"), "INVALID_PATH_ARG", f"{tok} path empty or flag-like")
    return Path(val)


def _parse_cli_argv(argv: Sequence[str]) -> tuple[str, Path | None, bool]:
    oracle.require_ok(type(argv) in (list, tuple), "INVALID_ARGV", "argv must be list or tuple")
    for item in argv:
        _require_utf8_no_surrogate(item, "argv_item")

    mode: str | None = None
    target: Path | None = None
    as_json = False
    i = 0
    n = len(argv)
    while i < n:
        tok = argv[i]
        if tok == "--json":
            oracle.require_ok(not as_json, "DUPLICATE_FLAG", "duplicate --json flag")
            as_json = True
            i += 1
        elif tok == "--standalone":
            oracle.require_ok(mode is None, "CONFLICTING_MODE", "multiple mode flags forbidden")
            mode = "standalone"
            i += 1
        elif tok in ("--check", "--write"):
            oracle.require_ok(mode is None, "CONFLICTING_MODE", "multiple mode flags forbidden")
            oracle.require_ok(i + 1 < n, "MISSING_PATH_ARG", f"{tok} requires a path argument")
            target = _reject_bad_path_arg(tok, argv[i + 1])
            mode = "check" if tok == "--check" else "write"
            i += 2
        elif tok.startswith("--check=") or tok.startswith("--write="):
            oracle.require_ok(mode is None, "CONFLICTING_MODE", "multiple mode flags forbidden")
            flag_name, val = tok.split("=", 1)
            target = _reject_bad_path_arg(flag_name, val)
            mode = "check" if flag_name == "--check" else "write"
            i += 1
        else:
            raise oracle.OptifabSchurError("UNKNOWN_FLAG", f"unrecognized CLI argument: {tok}")

    if mode is None:
        mode = "standalone"
    return mode, target, as_json


def main(argv: Sequence[str] | None = None) -> int:
    raw_argv: Any = sys.argv[1:] if argv is None else argv
    try:
        mode, target, as_json = _parse_cli_argv(raw_argv)
        if mode == "standalone":
            out: dict[str, Any] = build_standalone_certificate()
        elif mode == "write":
            out = write_certificate_file(target)  # type: ignore[arg-type]
        else:
            out = check_certificate_file(target)  # type: ignore[arg-type]
    except oracle.OptifabSchurError as exc:
        err = {"valid": False, "error_code": exc.code, "error_message": exc.detail}
        sys.stderr.write(canonical_json_bytes(err).decode("ascii") + "\n")
        return 2

    if as_json:
        sys.stdout.write(canonical_json_bytes(out).decode("ascii") + "\n")
    else:
        sys.stdout.write(
            f"OK {oracle.SCHEMA_VERSION} payload_sha256={out['payload_sha256']} "
            f"certificate_sha256={out['certificate_sha256']}\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
