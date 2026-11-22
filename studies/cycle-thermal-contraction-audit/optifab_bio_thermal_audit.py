#!/usr/bin/env python3
"""
Receiving-Side Exact-Z/Q Thermal Outage (`optifab#14` Defects #1 & #2),
Cascaded K-Stage Thermal-Buffer Surge Contraction (Op 2), and
beta_1 >= 1 Passive Multi-Sink Manifold Closure & Redundancy (Op 3) Audit
for `aska-physical/optifab` (`origin/main @ 74d68ea15ab7ed24`).

Evidence classification (`aska-physical/dock#8`): MODEL / CHECKER (exact pure-Z/Q
algebra anchored to `optifab` pinned literals; NOT a physical plant measurement).
Zero floats on trust paths. Zero bare `assert`s (`-O` safe). Zero external dependencies.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import hmac
import json
from math import comb
from pathlib import Path
import sys
from typing import Any

CERT_SCHEMA = "aska-physical.optifab.cycle-thermal-contraction-audit.v1"
UPSTREAM_REPO = "aska-physical/optifab"
UPSTREAM_MAIN_SHA = "74d68ea15ab7ed246c3266de6a9170837f7a7473"
HERE = Path(__file__).resolve().parent
DEFAULT_CERT_PATH = HERE / "optifab_bio_thermal_certificate.json"

MAX_JSON_DEPTH = 32
MAX_JSON_BYTES = 2_000_000
MAX_INT_DIGITS = 400
MAX_INT_BITS = 1329
MAX_SEQ_LEN = 256
MAX_MATRIX_DIM = 32
PPM_SCALE = 1_000_000
_HEX_LOWER = frozenset("0123456789abcdef")
_CERT_KEYS = frozenset({"schema", "upstream_repo", "upstream_main_sha", "payload_sha256", "certificate_sha256", "payload"})


class OptifabBioError(ValueError):
    """Fail-closed typed error (never stripped under python3 -O)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


# ---------------------------------------------------------------------------
# Strict Input Hardening & Iterative Zero-Float Canonical JSON
# ---------------------------------------------------------------------------

def require_int(val: Any, label: str = "int", *, lo: int | None = None, hi: int | None = None) -> int:
    if type(val) is not int:
        raise OptifabBioError("INVALID_INT_TYPE", f"{label} must be strict int")
    if lo is not None and val < lo:
        raise OptifabBioError("INT_BELOW_MIN", f"{label} below min {lo}")
    if hi is not None and val > hi:
        raise OptifabBioError("INT_ABOVE_MAX", f"{label} above max {hi}")
    return val


def require_rat(val: Any, label: str = "rational") -> Fraction:
    if type(val) is Fraction:
        return val
    if type(val) is int:
        return Fraction(val, 1)
    raise OptifabBioError("INVALID_RATIONAL_TYPE", f"{label} must be strict int or Fraction")


def require_nonneg_rat(val: Any, label: str = "nonneg_rational") -> Fraction:
    q = require_rat(val, label)
    if q < 0:
        raise OptifabBioError("NEGATIVE_RATIONAL", f"{label} must be >= 0")
    return q


def require_pos_rat(val: Any, label: str = "pos_rational") -> Fraction:
    q = require_rat(val, label)
    if q <= 0:
        raise OptifabBioError("NON_POSITIVE_RATIONAL", f"{label} must be > 0")
    return q


def require_seq(val: Any, label: str = "seq", *, min_len: int = 1, max_len: int = MAX_SEQ_LEN) -> tuple[Any, ...]:
    if type(val) not in (list, tuple):
        raise OptifabBioError("INVALID_SEQ_TYPE", f"{label} must be strict list or tuple")
    n = len(val)
    if n < min_len:
        raise OptifabBioError("SEQ_TOO_SHORT", f"{label} length {n} < {min_len}")
    if n > max_len:
        raise OptifabBioError("SEQ_TOO_LONG", f"{label} length {n} > {max_len}")
    return tuple(val)


def fmt_q(q: Fraction) -> str:
    r = require_rat(q, "q")
    if r.denominator == 1:
        return str(r.numerator)
    return f"{r.numerator}/{r.denominator}"


def ceil_ppm(q: Fraction) -> int:
    r = require_nonneg_rat(q, "ratio")
    num = r.numerator * PPM_SCALE
    den = r.denominator
    return (num + den - 1) // den


def floor_ppm(q: Fraction) -> int:
    r = require_nonneg_rat(q, "ratio")
    return (r.numerator * PPM_SCALE) // r.denominator


def validate_json_value(obj: Any, *, max_depth: int = MAX_JSON_DEPTH) -> None:
    """Iterative zero-float, depth-capped, bit-length-capped JSON validator (zero recursion)."""
    limit = require_int(max_depth, "max_depth", lo=1, hi=128)
    stack: list[tuple[Any, int]] = [(obj, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth > limit:
            raise OptifabBioError("MAX_DEPTH_EXCEEDED", f"JSON nesting exceeds {limit}")
        t = type(cur)
        if t is dict:
            for k, v in cur.items():
                if type(k) is not str:
                    raise OptifabBioError("NON_STR_KEY", "dict keys must be strict str")
                stack.append((v, depth + 1))
        elif t is list:
            for item in cur:
                stack.append((item, depth + 1))
        elif t is int:
            if cur.bit_length() > MAX_INT_BITS:
                raise OptifabBioError("INT_TOO_LARGE", "integer exceeds bit-length cap")
        elif t in (str, bool) or cur is None:
            continue
        elif t is float:
            raise OptifabBioError("FLOAT_FORBIDDEN", "float values are forbidden")
        else:
            raise OptifabBioError("UNSUPPORTED_JSON_TYPE", f"unsupported type {t.__name__}")


def _reject_float_token(tok: str) -> Any:
    raise OptifabBioError("JSON_FLOAT_FORBIDDEN", f"float literal forbidden: {tok!r}")


def _reject_constant_token(tok: str) -> Any:
    raise OptifabBioError("JSON_CONSTANT_FORBIDDEN", f"non-RFC8259 constant forbidden: {tok!r}")


def _parse_capped_int_token(tok: str) -> int:
    digits = tok[1:] if tok.startswith("-") else tok
    if len(digits) > MAX_INT_DIGITS:
        raise OptifabBioError("INT_DIGIT_LIMIT", f"integer token exceeds {MAX_INT_DIGITS} digits")
    return int(tok)


def _pairs_no_dup(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise OptifabBioError("JSON_DUPLICATE_KEY", f"duplicate JSON key: {k!r}")
        out[k] = v
    return out


def parse_strict_json(text: str) -> Any:
    if type(text) is not str:
        raise OptifabBioError("INVALID_JSON_INPUT", "JSON input must be strict str")
    if len(text.encode("utf-8")) > MAX_JSON_BYTES:
        raise OptifabBioError("JSON_TOO_LARGE", "JSON input exceeds byte cap")
    if not text.strip():
        raise OptifabBioError("EMPTY_JSON", "JSON input must be non-empty")
    try:
        parsed = json.loads(
            text,
            parse_int=_parse_capped_int_token,
            parse_float=_reject_float_token,
            parse_constant=_reject_constant_token,
            object_pairs_hook=_pairs_no_dup,
        )
    except OptifabBioError:
        raise
    except (ValueError, RecursionError) as exc:
        raise OptifabBioError("JSON_PARSE_ERROR", str(exc)) from exc
    validate_json_value(parsed)
    return parsed


def canonical_json_bytes(obj: Any) -> bytes:
    validate_json_value(obj)
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# Exact-Q Linear Solver Core (Zero Floats)
# ---------------------------------------------------------------------------

def solve_linear_q(matrix: Any, rhs: Any) -> list[Fraction]:
    """Exact Gauss-Jordan linear solver over Q (`A x = b`)."""
    rows_raw = require_seq(matrix, "matrix", min_len=1, max_len=MAX_MATRIX_DIM)
    n = len(rows_raw)
    rhs_raw = require_seq(rhs, "rhs", min_len=n, max_len=n)
    aug: list[list[Fraction]] = []
    for i in range(n):
        rseq = require_seq(rows_raw[i], f"row[{i}]", min_len=n, max_len=n)
        aug.append([require_rat(x, f"A[{i}][{j}]") for j, x in enumerate(rseq)] + [require_rat(rhs_raw[i], f"b[{i}]")])
    for col in range(n):
        piv = -1
        for r in range(col, n):
            if aug[r][col] != 0:
                piv = r
                break
        if piv < 0:
            raise OptifabBioError("SINGULAR_MATRIX", f"singular matrix at column {col}")
        if piv != col:
            aug[col], aug[piv] = aug[piv], aug[col]
        pv = aug[col][col]
        row_c = aug[col]
        for j in range(col, n + 1):
            row_c[j] /= pv
        for r in range(n):
            if r != col and aug[r][col] != 0:
                f = aug[r][col]
                row_r = aug[r]
                for j in range(col, n + 1):
                    row_r[j] -= f * row_c[j]
    return [aug[i][n] for i in range(n)]


# ---------------------------------------------------------------------------
# Part A: Exact-Q Audit of `optifab#14` Defects #1 & #2 + Second-Law Ceiling
# ---------------------------------------------------------------------------

def evaluate_optifab_outage_defect2_q(
    pcm_kwh: Any,
    shed_frac: Any,
    *,
    p_it_kw: Any = Fraction(10000),
    wall_u_w_m2k: Any = Fraction(132, 1000),
    outage_min: Any = Fraction(20),
    limit_ppm: int = PPM_SCALE,
) -> dict[str, Any]:
    """
    Exact-Q receiving-side comparison of `loop.py:58` (IT-only outage demand, Defect #2)
    against the fixed-heat-inclusive outage demand (`(P_IT*(1 - shed) + q_fix) * out_h`).
    Anchored to `optifab @ 74d68ea1`: U_roof = 0.1234 W/(m^2*K), A_roof = 2500 m^2,
    A_wall = 200 * 12.38 = 2476 m^2, dT = 20 K, other_kw = 200 kW.
    """
    pcm = require_pos_rat(pcm_kwh, "pcm_kwh")
    shed = require_nonneg_rat(shed_frac, "shed_frac")
    if shed > 1:
        raise OptifabBioError("SHED_ABOVE_ONE", "shed_frac must be <= 1")
    p_it = require_pos_rat(p_it_kw, "p_it_kw")
    u_wall = require_pos_rat(wall_u_w_m2k, "wall_u_w_m2k")
    t_min = require_pos_rat(outage_min, "outage_min")
    lim = require_int(limit_ppm, "limit_ppm", lo=1, hi=10 * PPM_SCALE)

    ua_roof = Fraction(1234, 10000) * Fraction(2500)
    ua_wall = u_wall * Fraction(2476)
    q_env_kw = (ua_roof + ua_wall) * Fraction(20, 1000)
    q_fix_kw = q_env_kw + Fraction(200)
    out_h = t_min / Fraction(60)

    e_it_kwh = p_it * (Fraction(1) - shed) * out_h
    e_fix_kwh = q_fix_kw * out_h
    e_tot_kwh = e_it_kwh + e_fix_kwh

    buggy_ppm = ceil_ppm(e_it_kwh / pcm)
    fixed_ppm = ceil_ppm(e_tot_kwh / pcm)
    return {
        "q_env_kw": fmt_q(q_env_kw),
        "q_fix_kw": fmt_q(q_fix_kw),
        "e_it_only_kwh": fmt_q(e_it_kwh),
        "e_fix_omitted_kwh": fmt_q(e_fix_kwh),
        "e_total_kwh": fmt_q(e_tot_kwh),
        "buggy_it_only_margin_ppm": buggy_ppm,
        "corrected_total_margin_ppm": fixed_ppm,
        "buggy_gate_admits": buggy_ppm <= lim,
        "corrected_gate_admits": fixed_ppm <= lim,
        "false_admission_caught": all((buggy_ppm <= lim, fixed_ppm > lim)),
    }


def evaluate_optifab_defect1_and_second_law_q(
    recooling_c: Any,
    *,
    outages_per_year: int = 12,
    shed_frac: Any = Fraction(0),
) -> dict[str, Any]:
    """
    Exact-Q verification of:
      - `optifab#14` Defect #1: `utility(0) = -passive_kw/loop_cop + aux_kw + other_kw = 13353/35 kW`
        is subtracted during zero-shed outages in `loop.py:73`, artificially raising `eta_ppm`
        whereas `utility(P) - utility((1 - shed)*P) = shed * P * (1 + 1/loop_cop)` leaves zero-shed
        outages invariant.
      - `MODEL.md` section 2 exact-Q Second-Law recooling ceiling (`T_h = 58 C`, `T_c = 18 C`, `COP = 0.62`).
    """
    t_rec = require_rat(recooling_c, "recooling_c")
    n_out = require_int(outages_per_year, "outages_per_year", lo=0, hi=365)
    shed = require_nonneg_rat(shed_frac, "shed_frac")
    if shed > 1:
        raise OptifabBioError("SHED_ABOVE_ONE", "shed_frac must be <= 1")

    p_kw = Fraction(10000)
    passive_kw = Fraction(250) + Fraction(55, 100) * Fraction(232)  # 1888/5 = 377.6 kW
    loop_cop = Fraction(28)
    aux_kw = Fraction(195)
    other_kw = Fraction(200)
    out_h = Fraction(1, 3)  # 20 min
    hours = Fraction(8760)
    low_h = Fraction(2000)
    low_kw = Fraction(300)
    floor_kw = Fraction(600)

    def util(it_kw: Fraction) -> Fraction:
        return it_kw + (it_kw - passive_kw) / loop_cop + aux_kw + other_kw

    util_zero = util(Fraction(0))
    useful = p_kw * (hours - low_h) + low_kw * low_h - shed * p_kw * out_h * n_out
    base_used = util(p_kw) * (hours - low_h) + util(floor_kw) * low_h
    used_buggy = base_used - util(shed * p_kw) * out_h * n_out
    used_fixed = base_used - (util(p_kw) - util((Fraction(1) - shed) * p_kw)) * out_h * n_out

    eta_buggy_ppm = floor_ppm(useful / used_buggy)
    eta_fixed_ppm = floor_ppm(useful / used_fixed)

    # Exact Second-Law tri-thermal ceiling: T_a <= T_c * T_h * (1 + COP) / (COP * T_h + T_c)
    kelvin = Fraction(27315, 100)
    t_h = Fraction(58) + kelvin
    t_c = Fraction(18) + kelvin
    cop = Fraction(62, 100)
    t_a_max_c = (t_c * t_h * (Fraction(1) + cop)) / (cop * t_h + t_c) - kelvin
    return {
        "utility_at_zero_load_kw": fmt_q(util_zero),
        "eta_buggy_ppm": eta_buggy_ppm,
        "eta_fixed_ppm": eta_fixed_ppm,
        "max_recooling_c_exact": fmt_q(t_a_max_c),
        "recooling_c": fmt_q(t_rec),
        "second_law_recooling_pass": t_rec <= t_a_max_c,
    }


# ---------------------------------------------------------------------------
# Part B: Op 2 — K-Stage Thermal-Buffer Surge Contraction & Choke vs Runaway
# ---------------------------------------------------------------------------

def evaluate_thermal_cascade_surge_q(
    n_stages: int,
    release_frac: Any,
    horizon_steps: int = 20,
) -> dict[str, Any]:
    """
    Exact-Q discrete K-stage cascaded leaky thermal buffer impulse response:
      S_1[t] = (1 - a)*S_1[t-1] (initial S_1[0] = 1),
      S_k[t] = (1 - a)*S_k[t-1] + a*S_{k-1}[t-1],
      outflow y_K[t] = a*S_K[t-1] == comb(t - 1, K - 1) * a^K * (1 - a)^(t - K) for t >= K.
    """
    k = require_int(n_stages, "n_stages", lo=1, hi=16)
    a = require_pos_rat(release_frac, "release_frac")
    if a >= 1:
        raise OptifabBioError("RELEASE_GE_ONE", "release_frac must be strictly < 1")
    steps = require_int(horizon_steps, "horizon_steps", lo=k, hi=64)

    stores = [Fraction(0)] * k
    stores[0] = Fraction(1)
    outflows: list[Fraction] = []
    closed_ok = True
    for t in range(1, steps + 1):
        out_t = a * stores[k - 1]
        outflows.append(out_t)
        expected = Fraction(0) if t < k else Fraction(comb(t - 1, k - 1)) * (a ** k) * ((Fraction(1) - a) ** (t - k))
        if out_t != expected:
            closed_ok = False
        new_stores = [Fraction(0)] * k
        new_stores[0] = (Fraction(1) - a) * stores[0]
        for idx in range(1, k):
            new_stores[idx] = (Fraction(1) - a) * stores[idx] + a * stores[idx - 1]
        stores = new_stores

    mass_conserved = (sum(outflows, Fraction(0)) + sum(stores, Fraction(0))) == Fraction(1)
    peak_out = max(outflows)
    return {
        "n_stages": k,
        "release_frac": fmt_q(a),
        "peak_flux_fraction": fmt_q(peak_out),
        "closed_form_negbin_exact": closed_ok,
        "energy_conserved_exact": mass_conserved,
    }


def evaluate_choke_vs_runaway_q(
    g0: Any,
    delta_t: Any,
    feedback_coeff: Any,
    steps: int,
    *,
    mode: str,
) -> dict[str, Any]:
    """
    Exact-Q Lyapunov/contraction contrast:
      - 'contractive_choke': g_{t+1} = g_t / (1 + c * (g_t * dT)^2) (strictly decreasing, bounded)
      - 'positive_runaway':  g_{t+1} = g_t * (1 + c * (g_t * dT)^2) (strictly increasing blow-up).
    """
    g = require_pos_rat(g0, "g0")
    dt = require_pos_rat(delta_t, "delta_t")
    c = require_pos_rat(feedback_coeff, "feedback_coeff")
    n_steps = require_int(steps, "steps", lo=1, hi=12)
    if mode not in ("contractive_choke", "positive_runaway"):
        raise OptifabBioError("UNKNOWN_FEEDBACK_MODE", f"unknown feedback mode: {mode!r}")

    traj = [g]
    for _ in range(n_steps):
        q = g * dt
        factor = Fraction(1) + c * q * q
        g = (g / factor) if mode == "contractive_choke" else (g * factor)
        traj.append(g)

    strictly_contracting = all(traj[i + 1] < traj[i] for i in range(n_steps))
    strictly_expanding = all(traj[i + 1] > traj[i] for i in range(n_steps))
    ratio_final_over_init = traj[-1] / traj[0]
    return {
        "mode": mode,
        "steps": n_steps,
        "final_over_initial_conductance": fmt_q(ratio_final_over_init),
        "strictly_contracting": strictly_contracting,
        "strictly_expanding": strictly_expanding,
        "stability_gate_pass": strictly_contracting,
    }


# ---------------------------------------------------------------------------
# Part C: Op 3 — beta_1 >= 1 Passive Multi-Sink Manifold Closure & Redundancy
# ---------------------------------------------------------------------------

def _is_connected(n_nodes: int, active_edges: list[tuple[int, int]]) -> bool:
    adj: list[list[int]] = [[] for _ in range(n_nodes)]
    for u, v in active_edges:
        adj[u].append(v)
        adj[v].append(u)
    seen = {0}
    stack = [0]
    while stack:
        cur = stack.pop()
        for nb in adj[cur]:
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return len(seen) == n_nodes


def analyze_passive_sink_network_q(
    n_nodes: int,
    edges: Any,
    conductances: Any,
    emf_vec: Any,
) -> dict[str, Any]:
    """
    Exact-Q dual Kirchhoff passive thermosyphon solver & 1-/2-pipe blockage redundancy audit:
      - Computes exact Betti number beta_1 = |E| - |V| + 1 (for connected sink manifold).
      - Solves exact nodal Laplacian L p = B G eta (grounding node 0) -> q_nodal = G (eta - B^T p).
      - Cross-checks exact conservation B q = 0, exact Tellegen power identity eta^T q = q^T G^-1 q,
        exact diurnal/EMF sign reversal q(-eta) == -q(eta), and exact 1-/2-edge blockage survival.
    """
    nv = require_int(n_nodes, "n_nodes", lo=2, hi=16)
    e_raw = require_seq(edges, "edges", min_len=1, max_len=32)
    ne = len(e_raw)
    g_raw = require_seq(conductances, "conductances", min_len=ne, max_len=ne)
    eta_raw = require_seq(emf_vec, "emf_vec", min_len=ne, max_len=ne)

    edge_list: list[tuple[int, int]] = []
    for idx, pair in enumerate(e_raw):
        pseq = require_seq(pair, f"edges[{idx}]", min_len=2, max_len=2)
        u = require_int(pseq[0], f"edges[{idx}][0]", lo=0, hi=nv - 1)
        v = require_int(pseq[1], f"edges[{idx}][1]", lo=0, hi=nv - 1)
        if u == v:
            raise OptifabBioError("SELF_LOOP_FORBIDDEN", f"self-loop at edge {idx}")
        edge_list.append((u, v))
    if not _is_connected(nv, edge_list):
        raise OptifabBioError("DISCONNECTED_NETWORK", "sink manifold must be connected")

    gs = [require_pos_rat(g, f"conductances[{i}]") for i, g in enumerate(g_raw)]
    etas = [require_rat(e, f"emf_vec[{i}]") for i, e in enumerate(eta_raw)]
    beta1 = ne - nv + 1

    def solve_flows(emfs: list[Fraction]) -> list[Fraction]:
        # Reduced (nv - 1) x (nv - 1) grounded Laplacian L_red p_red = rhs_red
        m = nv - 1
        lap = [[Fraction(0)] * m for _ in range(m)]
        rhs = [Fraction(0)] * m
        for (u, v), g, e_val in zip(edge_list, gs, emfs):
            # Oriented edge u -> v: B[u, e] = +1, B[v, e] = -1, q_e = g * (e_val + p[u] - p[v])
            if u > 0:
                lap[u - 1][u - 1] += g
                rhs[u - 1] -= g * e_val
            if v > 0:
                lap[v - 1][v - 1] += g
                rhs[v - 1] += g * e_val
            if u > 0 and v > 0:
                lap[u - 1][v - 1] -= g
                lap[v - 1][u - 1] -= g
        p_red = solve_linear_q(lap, rhs)
        p = [Fraction(0)] + p_red
        return [g * (e_val + p[u] - p[v]) for (u, v), g, e_val in zip(edge_list, gs, emfs)]

    q_fwd = solve_flows(etas)
    q_rev = solve_flows([-e for e in etas])

    # Verify exact Kirchhoff node conservation B q = 0
    node_res = [Fraction(0)] * nv
    for (u, v), q_val in zip(edge_list, q_fwd):
        node_res[u] += q_val
        node_res[v] -= q_val
    kcl_zero = all(r == 0 for r in node_res)

    power_lhs = sum((e_val * q_val for e_val, q_val in zip(etas, q_fwd)), Fraction(0))
    power_rhs = sum((q_val * q_val / g for q_val, g in zip(q_fwd, gs)), Fraction(0))
    tellegen_exact = power_lhs == power_rhs
    reversal_exact = all(q_rev[i] == -q_fwd[i] for i in range(ne))
    nonzero_flux = any(q_val != 0 for q_val in q_fwd)

    # Exhaustive 1-edge and 2-edge pipe-isolation survival fractions
    surv1 = sum(1 for i in range(ne) if _is_connected(nv, [edge_list[k] for k in range(ne) if k != i]))
    frac1 = Fraction(surv1, ne)
    total2 = ne * (ne - 1) // 2
    surv2 = 0
    for i in range(ne):
        for j in range(i + 1, ne):
            if _is_connected(nv, [edge_list[k] for k in range(ne) if k != i and k != j]):
                surv2 += 1
    frac2 = Fraction(surv2, total2) if total2 > 0 else Fraction(0)

    return {
        "n_nodes": nv,
        "n_edges": ne,
        "betti_1": beta1,
        "flows_q": [fmt_q(q_val) for q_val in q_fwd],
        "dissipated_power_q": fmt_q(power_lhs),
        "kcl_residual_zero": kcl_zero,
        "tellegen_identity_exact": tellegen_exact,
        "diurnal_reversal_exact": reversal_exact,
        "passive_circulation_nonzero": nonzero_flux,
        "single_pipe_survival_frac": fmt_q(frac1),
        "double_pipe_survival_frac": fmt_q(frac2),
        "passive_sink_manifold_gate_pass": all((kcl_zero, tellegen_exact, reversal_exact, nonzero_flux, frac1 == 1)),
    }


def build_study_payload() -> dict[str, Any]:
    """Build deterministic exact-Q receiving-side payload for aska-physical/optifab."""
    # Part A: optifab#14 Defect #2 (2400 kWh store, 30% shed -> 972,223 buggy PASS vs 1,001,765 corrected FAIL)
    d2_2400_caught = evaluate_optifab_outage_defect2_q(Fraction(2400), Fraction(3, 10))
    d2_2500_passes = evaluate_optifab_outage_defect2_q(Fraction(2500), Fraction(3, 10))

    # Part A2: optifab#14 Defect #1 (0 outages vs 12 outages at 0% shed) + Second-Law 30 C PASS vs 42 C FAIL
    d1_no_out_30c = evaluate_optifab_defect1_and_second_law_q(Fraction(30), outages_per_year=0, shed_frac=Fraction(0))
    d1_12_out_42c = evaluate_optifab_defect1_and_second_law_q(Fraction(42), outages_per_year=12, shed_frac=Fraction(0))
    defect1_buggy_raises_score = d1_12_out_42c["eta_buggy_ppm"] > d1_no_out_30c["eta_buggy_ppm"]
    defect1_fixed_invariant = d1_12_out_42c["eta_fixed_ppm"] == d1_no_out_30c["eta_fixed_ppm"]

    # Part B: Op 2 K-stage cascaded thermal buffer (K = 1, 2, 4, 8 at alpha = 1/2) + contractive choke vs runaway
    cascades = [evaluate_thermal_cascade_surge_q(k, Fraction(1, 2), horizon_steps=20) for k in (1, 2, 4, 8)]
    peak_fracs = [Fraction(c["peak_flux_fraction"]) for c in cascades]
    strict_peak_contraction = all(peak_fracs[i + 1] < peak_fracs[i] for i in range(3))
    k8_attenuation = peak_fracs[0] / peak_fracs[3]  # 2048/429

    # Honest Law-2b fixed-capacity non-monotone control (a = 1/4, 1/2, 3/4 with K = 1, 2, 3)
    fixed_cap_k1 = evaluate_thermal_cascade_surge_q(1, Fraction(1, 4), horizon_steps=16)
    fixed_cap_k2 = evaluate_thermal_cascade_surge_q(2, Fraction(1, 2), horizon_steps=16)
    fixed_cap_k3 = evaluate_thermal_cascade_surge_q(3, Fraction(3, 4), horizon_steps=16)
    fixed_cap_non_monotone = Fraction(fixed_cap_k3["peak_flux_fraction"]) > Fraction(fixed_cap_k2["peak_flux_fraction"])

    choke_pass = evaluate_choke_vs_runaway_q(Fraction(1), Fraction(1), Fraction(1, 4), 6, mode="contractive_choke")
    runaway_fail = evaluate_choke_vs_runaway_q(Fraction(1), Fraction(1), Fraction(1, 4), 6, mode="positive_runaway")

    # Part C: Op 3 passive thermal-sink topologies (G2: aquifer, energy piles, sky-cooling roof)
    tree_fail = analyze_passive_sink_network_q(
        4, [(0, 1), (0, 2), (0, 3)], [Fraction(1)] * 3, [Fraction(1), Fraction(2), Fraction(3)]
    )
    coboundary_loop_fail = analyze_passive_sink_network_q(
        4, [(0, 1), (1, 2), (2, 3), (3, 0)], [Fraction(1)] * 4, [Fraction(1), Fraction(0), Fraction(-1), Fraction(0)]
    )
    single_loop_pass = analyze_passive_sink_network_q(
        4, [(0, 1), (1, 2), (2, 3), (3, 0)], [Fraction(1)] * 4, [Fraction(1), Fraction(0), Fraction(0), Fraction(0)]
    )
    g2_3sink_pass = analyze_passive_sink_network_q(
        5,
        [(0, 1), (0, 2), (0, 3), (1, 4), (2, 4), (3, 4), (4, 0)],
        [Fraction(1)] * 7,
        [Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(1)],
    )

    all_passed = all((
        d2_2400_caught["buggy_it_only_margin_ppm"] == 972223,
        d2_2400_caught["corrected_total_margin_ppm"] == 1001765,
        d2_2400_caught["false_admission_caught"],
        d2_2500_passes["corrected_gate_admits"],
        d1_no_out_30c["utility_at_zero_load_kw"] == "13353/35",
        defect1_buggy_raises_score,
        defect1_fixed_invariant,
        d1_no_out_30c["second_law_recooling_pass"],
        not d1_12_out_42c["second_law_recooling_pass"],
        all(c["closed_form_negbin_exact"] for c in cascades),
        all(c["energy_conserved_exact"] for c in cascades),
        strict_peak_contraction,
        k8_attenuation == Fraction(2048, 429),
        fixed_cap_non_monotone,
        choke_pass["stability_gate_pass"],
        not runaway_fail["stability_gate_pass"],
        runaway_fail["strictly_expanding"],
        tree_fail["betti_1"] == 0,
        not tree_fail["passive_circulation_nonzero"],
        not tree_fail["passive_sink_manifold_gate_pass"],
        coboundary_loop_fail["betti_1"] == 1,
        not coboundary_loop_fail["passive_circulation_nonzero"],
        not coboundary_loop_fail["passive_sink_manifold_gate_pass"],
        single_loop_pass["passive_sink_manifold_gate_pass"],
        single_loop_pass["double_pipe_survival_frac"] == "0",
        g2_3sink_pass["betti_1"] == 3,
        g2_3sink_pass["passive_sink_manifold_gate_pass"],
        g2_3sink_pass["single_pipe_survival_frac"] == "1",
        g2_3sink_pass["double_pipe_survival_frac"] == "6/7",
        g2_3sink_pass["dissipated_power_q"] == "3/5",
    ))

    return {
        "evidence_label": "model_checker_exact_Q_not_plant_measurement",
        "upstream_anchors": {
            "repo": UPSTREAM_REPO,
            "main_sha": UPSTREAM_MAIN_SHA,
            "targets": "Issue #14 Defects #1 & #2 (loop.py:42-75), MODEL.md §2-§4, data/unit.json G1/G2/L7",
        },
        "part_a_issue14_defects_and_second_law": {
            "defect2_2400kwh_30pct_shed_false_pass_caught": d2_2400_caught,
            "defect2_2500kwh_start_design_passes": d2_2500_passes,
            "defect1_zero_outages_30c_recooling_passes": d1_no_out_30c,
            "defect1_12_outages_42c_recooling_fails": d1_12_out_42c,
            "defect1_buggy_outage_raises_eta": defect1_buggy_raises_score,
            "defect1_fixed_zero_shed_invariant": defect1_fixed_invariant,
        },
        "part_b_op2_cascade_surge_and_choke": {
            "k_stage_impulse_cascades": cascades,
            "strict_peak_contraction_k1_to_k8": strict_peak_contraction,
            "k1_over_k8_peak_attenuation": fmt_q(k8_attenuation),
            "fixed_capacity_non_monotone_control": {
                "k1_a1_4": fixed_cap_k1,
                "k2_a1_2": fixed_cap_k2,
                "k3_a3_4": fixed_cap_k3,
                "non_monotone_confirmed": fixed_cap_non_monotone,
            },
            "contractive_choke_passes": choke_pass,
            "positive_feedback_runaway_fails": runaway_fail,
        },
        "part_c_op3_g2_passive_sink_manifold": {
            "tree_header_beta1_0_fails": tree_fail,
            "single_loop_coboundary_isothermal_fails": coboundary_loop_fail,
            "single_loop_buoyancy_passes_zero_2cut": single_loop_pass,
            "g2_3sink_manifold_beta1_3_passes": g2_3sink_pass,
        },
        "all_passed": all_passed,
    }


# ---------------------------------------------------------------------------
# Fail-Closed Certificate Builder, Checker & CLI
# ---------------------------------------------------------------------------

def _require_sha256_hex(val: Any, label: str) -> str:
    if type(val) is not str:
        raise OptifabBioError("INVALID_DIGEST_TYPE", f"{label} must be strict str")
    if len(val) != 64:
        raise OptifabBioError("INVALID_DIGEST_LEN", f"{label} must have length 64")
    if any(ch not in _HEX_LOWER for ch in val):
        raise OptifabBioError("INVALID_DIGEST_HEX", f"{label} must be lowercase hex")
    return val


def _require_no_symlink_path(path: Path) -> None:
    if path.is_symlink():
        raise OptifabBioError("SYMLINK_FORBIDDEN", f"symlink path forbidden: {path}")
    for parent in path.parents:
        if parent.is_symlink():
            raise OptifabBioError("SYMLINK_ANCESTOR_FORBIDDEN", f"symlink ancestor forbidden: {parent}")


def build_certificate() -> dict[str, Any]:
    payload = build_study_payload()
    payload_sha256 = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    envelope = {
        "schema": CERT_SCHEMA,
        "upstream_repo": UPSTREAM_REPO,
        "upstream_main_sha": UPSTREAM_MAIN_SHA,
        "payload_sha256": payload_sha256,
        "payload": payload,
    }
    certificate_sha256 = hashlib.sha256(canonical_json_bytes(envelope)).hexdigest()
    return {
        "schema": CERT_SCHEMA,
        "upstream_repo": UPSTREAM_REPO,
        "upstream_main_sha": UPSTREAM_MAIN_SHA,
        "payload_sha256": payload_sha256,
        "certificate_sha256": certificate_sha256,
        "payload": payload,
    }


def verify_certificate_dict(cert: Any) -> dict[str, Any]:
    if type(cert) is not dict:
        raise OptifabBioError("CERT_NOT_DICT", "certificate root must be a JSON object")
    if any(type(k) is not str for k in cert):
        raise OptifabBioError("NON_STR_KEY", "certificate root keys must be strict str")
    if set(cert.keys()) != _CERT_KEYS:
        raise OptifabBioError("CERT_SCHEMA_KEYS", f"unexpected keys: {sorted(cert.keys())}")
    if cert["schema"] != CERT_SCHEMA:
        raise OptifabBioError("CERT_SCHEMA_MISMATCH", "schema mismatch")
    if cert["upstream_repo"] != UPSTREAM_REPO:
        raise OptifabBioError("CERT_REPO_MISMATCH", "upstream_repo mismatch")
    if cert["upstream_main_sha"] != UPSTREAM_MAIN_SHA:
        raise OptifabBioError("CERT_SHA_MISMATCH", "upstream_main_sha mismatch")

    stored_payload_sha = _require_sha256_hex(cert["payload_sha256"], "payload_sha256")
    stored_cert_sha = _require_sha256_hex(cert["certificate_sha256"], "certificate_sha256")
    computed_payload_sha = hashlib.sha256(canonical_json_bytes(cert["payload"])).hexdigest()
    if not hmac.compare_digest(stored_payload_sha, computed_payload_sha):
        raise OptifabBioError("PAYLOAD_SHA_MISMATCH", "payload_sha256 mismatch")

    envelope = {
        "schema": cert["schema"],
        "upstream_repo": cert["upstream_repo"],
        "upstream_main_sha": cert["upstream_main_sha"],
        "payload_sha256": stored_payload_sha,
        "payload": cert["payload"],
    }
    computed_cert_sha = hashlib.sha256(canonical_json_bytes(envelope)).hexdigest()
    if not hmac.compare_digest(stored_cert_sha, computed_cert_sha):
        raise OptifabBioError("CERTIFICATE_SHA_MISMATCH", "certificate_sha256 mismatch")

    expected = build_certificate()
    if not hmac.compare_digest(computed_payload_sha, expected["payload_sha256"]):
        raise OptifabBioError("RECOMPUTED_PAYLOAD_DRIFT", "payload digest differs from exact recomputation")

    return {
        "valid": True,
        "schema": CERT_SCHEMA,
        "payload_sha256": computed_payload_sha,
        "certificate_sha256": computed_cert_sha,
    }


def check_certificate_file(path: Path) -> dict[str, Any]:
    if not isinstance(path, Path):
        raise OptifabBioError("INVALID_PATH_TYPE", "path must be a pathlib.Path")
    _require_no_symlink_path(path)
    if not path.is_file():
        raise OptifabBioError("CERT_FILE_NOT_FOUND", f"certificate file not found: {path}")
    if path.stat().st_size > MAX_JSON_BYTES:
        raise OptifabBioError("CERT_FILE_TOO_LARGE", "certificate file exceeds byte cap")
    raw = path.read_bytes()
    if b"\r\n" in raw:
        raise OptifabBioError("CRLF_FORBIDDEN", "CRLF line endings forbidden")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OptifabBioError("INVALID_UTF8", f"invalid UTF-8: {exc}") from exc
    parsed = parse_strict_json(text)
    canonical_raw = canonical_json_bytes(parsed)
    if raw not in (canonical_raw, canonical_raw + b"\n"):
        raise OptifabBioError("NON_CANONICAL_CERT_BYTES", "certificate file is not canonical JSON")
    return verify_certificate_dict(parsed)


def write_certificate_file(path: Path) -> dict[str, Any]:
    _require_no_symlink_path(path)
    cert = build_certificate()
    raw = canonical_json_bytes(cert) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return check_certificate_file(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Exact-Q optifab #14, cascade surge, and passive sink-loop checker")
    parser.add_argument("--standalone", action="store_true", help="Run full standalone exact verification")
    parser.add_argument("--json", action="store_true", help="Emit canonical JSON certificate to stdout")
    parser.add_argument("--write", nargs="?", const=str(DEFAULT_CERT_PATH), help="Write canonical certificate")
    parser.add_argument("--check", type=str, help="Fail-closed verification of a certificate JSON file")
    args = parser.parse_args(argv)

    try:
        if args.check is not None:
            res = check_certificate_file(Path(args.check))
            print(
                f"OK {CERT_SCHEMA} payload_sha256={res['payload_sha256']} "
                f"certificate_sha256={res['certificate_sha256']}"
            )
            return 0
        if args.write is not None:
            res = write_certificate_file(Path(args.write))
            print(
                f"WROTE {CERT_SCHEMA} payload_sha256={res['payload_sha256']} "
                f"certificate_sha256={res['certificate_sha256']}"
            )
            return 0
        cert = build_certificate()
        if args.json:
            sys.stdout.buffer.write(canonical_json_bytes(cert) + b"\n")
            return 0
        print(
            f"OK {CERT_SCHEMA} payload_sha256={cert['payload_sha256']} "
            f"certificate_sha256={cert['certificate_sha256']} "
            f"all_passed={cert['payload']['all_passed']}"
        )
        return 0
    except (OptifabBioError, ValueError, RecursionError, OSError) as exc:
        print(f"REJECT {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
