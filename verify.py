#!/usr/bin/env python3
"""Deterministic verifier for aska-physical/optifab v0.3.0.

optifab models one reference data-centre campus as a checked stack and states the contract between
the physical plant and the digital workload. It adds no new measurement. Every number is derived
from certificates and verifier literals of other repositories, pinned in data/.

    python3 verify.py                    re-derive everything and compare with results/certificate.json
    python3 verify.py --write            rewrite the certificate after a deliberate change
    python3 verify.py --upstream ROOT    also re-read every pinned line from clones at ROOT/<owner>/<repo>
    python3 verify.py --upstream ROOT --repin   refresh commits, file hashes and line numbers from the clones

What a pass shows: the derivations follow from the pinned inputs, the gate agrees with Weft's own
vectors, the cross-certificate constants agree, and the lineage graph is well formed.
What it does not show: that the upstream models describe a real building. Nothing here is measured.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import random
import re
import struct
import subprocess
import sys
from pathlib import Path

import sympy as sp

import loop

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CERT_PATH = ROOT / "results" / "certificate.json"
LEDGER_PATH = ROOT / "results" / "ledger.json"
# Recorded runs of outside proposers: certificate key -> (run file, ledger file), both in results/.
RECORDED_RUNS = {"recorded_proposer": ("model_run.json", "model_ledger.json"),
                 "recorded_proposer_given_lessons": ("model_run_2.json", "model_ledger_2.json")}
FORMAL_PATH = ROOT / "results" / "formal.json"
FORMAL_DIR = ROOT / "formal"
FORMAL_SOURCES = ["PlantGate.lean", "PlantGate/Spec.lean", "PlantGate/Proofs.lean", "Main.lean", "comparator.json",
                  "lakefile.toml", "lean-toolchain", "tests/oracle.py", "tests/run_tests.py"]
KELVIN = 273.15
PSF_TO_KPA = 0.04788026
VERSION = "0.3.0"


# --------------------------------------------------------------------------- inputs
def require(condition, message="") -> None:
    """A check that cannot be switched off. `python3 -O` strips every `assert` statement, so none is used here."""
    if not condition:
        raise RuntimeError(f"verification failed: {message}")


def count_asserts(source: str) -> int:
    return sum(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(source)))


def bare_asserts() -> dict:
    """Count `assert` statements in this repository's own Python files. There should be none."""
    files = sorted(p for p in ROOT.rglob("*.py")
                   if not {".lake", ".git", "data", "__pycache__"} & set(p.relative_to(ROOT).parts))
    found = {str(p.relative_to(ROOT)): count_asserts(p.read_text(encoding="utf-8")) for p in files}
    return {"python_files_scanned": len(files), "assert_statements": sum(found.values()),
            "files_with_assert_statements": sorted(f for f, k in found.items() if k),
            "scanner_finds_a_planted_assert": count_asserts("def f(x):\n    assert x\n") == 1}


def _sum_sq(values) -> float:
    """Sum of squares, added left to right, as the gates add them.

    The builtin sum() must not be used on floats here: from Python 3.12 on it compensates for rounding, so
    its last digit differs from 3.11, and a count in the certificate once depended on the interpreter."""
    total = 0.0
    for v in values:
        total += v * v
    return total


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_vendored(item: dict, raw: bytes):
    """Refuse a vendored input whose bytes no longer match the hash in the manifest."""
    if sha256_bytes(raw) != item["sha256"]:
        raise SystemExit(f"ERROR: vendored input changed: {item['file']}")
    return json.loads(raw.decode("utf-8")) if item["file"].endswith(".json") else raw


def load_inputs() -> dict:
    manifest = read_json(DATA / "upstream" / "MANIFEST.json")
    files = {}
    for item in manifest["files"]:
        files[item["id"]] = parse_vendored(item, (DATA / "upstream" / item["file"]).read_bytes())
    pins_doc = read_json(DATA / "pins.json")
    pins = {p["id"]: p for p in pins_doc["pins"]}
    return {
        "manifest": manifest,
        "ff": files["funi-frame"],
        "fl": files["funi-floors"],
        "vc": files["venturi-collars"],
        "weft_vectors": files["weft-vectors"],
        "weft_gate_oracle": files["weft-gate-oracle"],
        "pins": pins,
        "pins_doc": pins_doc,
        "graph": read_json(DATA / "graph.json"),
        "sources": read_json(DATA / "sources.json"),
        "unit": read_json(DATA / "unit.json"),
    }


def pin_value(pins: dict, pid: str, key: str):
    return pins[pid]["value"][key]


# --------------------------------------------------------------------------- symbolic results
def symbolic_theorems() -> dict[str, str]:
    """Five identities, each checked symbolically. They are algebra on the upstream model, not new physics."""
    P, pc, pf = sp.symbols("P PUE_c PUE_f", positive=True)
    extra_it = (P * pc) / pf - P  # same utility supply P*PUE_c, now run at PUE_f
    require(sp.simplify(extra_it - P * (pc - pf) / pf) == 0, 'a symbolic identity does not hold')
    require(sp.simplify(extra_it / (P * (pc - pf)) - 1 / pf) == 0, 'a symbolic identity does not hold')
    # the upstream plant model: cooling power (P - q)/c + a, other overhead o, with q, a and o fixed
    c, q0, a0, o0, P2 = sp.symbols("c q0 a0 o0 P2", positive=True)
    supply = P * pc
    used = lambda load: load + (load - q0) / c + a0 + o0
    grown = sp.solve(sp.Eq(used(P2), supply), P2)
    require(len(grown) == 1 and sp.simplify((grown[0] - P) - (supply - used(P)) / (1 + 1 / c)) == 0, 'a symbolic identity does not hold')

    Th, Ta, Tc, C = sp.symbols("T_h T_a T_c C", positive=True)
    cop_max = (Tc / (Ta - Tc)) * ((Th - Ta) / Th)  # reversible heat-driven chiller between three reservoirs
    ta_max = Tc * Th * (1 + C) / (C * Th + Tc)
    require(sp.simplify(cop_max.subs(Ta, ta_max) - C) == 0, 'a symbolic identity does not hold')
    require(sp.simplify(sp.diff(cop_max, Ta) + Tc * (Th - Tc) / (Th * (Ta - Tc) ** 2)) == 0, 'a symbolic identity does not hold')  # falls as T_a rises

    a, q, Pm = sp.symbols("alpha q_fix P_min", positive=True)
    sol = sp.solve(sp.Eq(a * Pm * C, (1 - a) * Pm + q), Pm)  # drive heat from liquid = air-side load / COP
    require(len(sol) == 1 and sp.simplify(sol[0] - q / ((1 + C) * a - 1)) == 0, 'a symbolic identity does not hold')
    require(sp.simplify(sp.solve(sp.Eq((1 + C) * a - 1, 0), a)[0] - 1 / (1 + C)) == 0, 'a symbolic identity does not hold')  # q_fix = 0: funi-frame Theorem 4

    B, T, s = sp.symbols("B T s", positive=True)
    shed = sp.solve(sp.Eq(B / (P * (1 - s)), T), s)
    require(len(shed) == 1 and sp.simplify(shed[0] - (1 - B / (P * T))) == 0, 'a symbolic identity does not hold')
    phi = sp.symbols("phi", real=True)  # a tone minus its own copy delayed by phase phi
    require(sp.simplify((1 - sp.cos(phi)) ** 2 + sp.sin(phi) ** 2 - 4 * sp.sin(phi / 2) ** 2) == 0, 'a symbolic identity does not hold')
    return {
        "substation_constrained_compute": "dP_IT = (freed utility power)/PUE_f if every overhead grows with load; (freed utility power)/(1 + 1/COP_loop) if only the cooling loop does",
        "tri_thermal_recooling_limit": "COP <= (T_c/(T_a - T_c))*((T_h - T_a)/T_h)  <=>  T_a <= T_c*T_h*(1 + COP)/(COP*T_h + T_c)",
        "minimum_load_for_self_cooling": "P_min = q_fix/((1 + COP)*alpha - 1); q_fix = 0 gives alpha* = 1/(1 + COP)",
        "shed_fraction_for_outage": "s_min = 1 - B/(P*T) for a cooling outage of length T on thermal budget B",
        "delayed_cancellation_residual": "|1 - exp(-i*phi)| = 2*|sin(phi/2)| with phi = 2*pi*f*tau; below 1 within the cycle only if f*tau < 1/6",
    }


# --------------------------------------------------------------------------- plant envelope
def cop_tri_thermal(th_c: float, ta_c: float, tc_c: float) -> float:
    th, ta, tc = th_c + KELVIN, ta_c + KELVIN, tc_c + KELVIN
    return (tc / (ta - tc)) * ((th - ta) / th)


def recooling_limit_c(th_c: float, tc_c: float, cop: float) -> float:
    th, tc = th_c + KELVIN, tc_c + KELVIN
    return tc * th * (1.0 + cop) / (cop * th + tc) - KELVIN


def minimum_load_mw(q_fix_mw: float, alpha: float, cop: float) -> float:
    denom = (1.0 + cop) * alpha - 1.0
    return math.inf if denom <= 0.0 else q_fix_mw / denom


def self_cools(p_mw: float, alpha: float, cop: float, q_fix_mw: float) -> bool:
    """True when the liquid heat captured at this load can drive the sorption stage for the whole air-side load."""
    return alpha * p_mw * cop >= (1.0 - alpha) * p_mw + q_fix_mw


def plant_envelope(inp: dict, design_dt_k: float = 20.0) -> dict:
    ff, pins = inp["ff"], inp["pins"]
    ts = ff["domain_5_6_three_tier_tes_and_closed_loop_cooling"]
    P, q_liq, q_air = ts["P_it_MW"], ts["Q_liquid_w45_MW"], ts["Q_air_rdhx_MW"]
    cop = pin_value(pins, "ff.cop_ads", "cop_ads")
    cp = pins["ff.cooling_power"]["value"]
    other = pin_value(pins, "ff.pue_overhead", "other_overhead_MW")
    sky_fraction = pin_value(pins, "ff.q_ates", "sky_fraction")

    # 1. Reproduce both PUE values from the certificate and the pinned literals.
    passive = ts["Q_energy_piles_MW"] + sky_fraction * ts["Q_sky_roof_peak_MW"]
    q_ates = q_liq + q_air - passive  # the drive heat cancels in the upstream expression
    pc_funi = q_ates / cp["ates_cop"] + cp["funi_aux_MW"]
    pc_conv = P / cp["conv_chiller_cop"] + cp["conv_aux_MW"]
    pue_f, pue_c = (P + pc_funi + other) / P, (P + pc_conv + other) / P
    reproduction = {
        "liquid_plus_air_equals_it_load": abs(q_liq + q_air - P) < 1e-9,
        "Q_ates_MW": round(q_ates, 4),
        "passive_sinks_MW": round(passive, 4),
        "PUE_funi_reproduced": round(pue_f, 5),
        "PUE_conventional_reproduced": round(pue_c, 5),
        "matches_certificate": round(pue_f, 3) == ts["PUE_funi_frame"] and round(pue_c, 3) == ts["PUE_conventional"],
        "annual_heat_to_aquifer_GWh_th": round(q_ates * 8.760, 2),
    }

    # 2. Compute unlocked at a fixed utility supply.
    freed_utility = pc_conv - pc_funi
    extra_scaled = P * (pue_c - pue_f) / pue_f  # every overhead grows with the load, so the PUE holds
    extra_fixed = freed_utility / (1.0 + 1.0 / cp["ates_cop"])  # only the aquifer loop grows, as in the upstream model
    rev = pin_value(pins, "ff.revenue_low", "revenue_low_M_usd_per_MW_yr")
    substation = {
        "freed_utility_power_MW": round(freed_utility, 3),
        "certificate_freed_substation_power_MW": ts["freed_substation_power_MW"],
        "extra_it_if_all_overhead_scales_MW": round(extra_scaled, 3),
        "extra_it_if_auxiliaries_are_fixed_MW": round(extra_fixed, 3),
        "one_over_PUE_funi": round(1.0 / pue_f, 4),
        "marginal_PUE_with_fixed_auxiliaries": round(1.0 + 1.0 / cp["ates_cop"], 4),
        "certificate_revenue_low_M_usd": ts["unlocked_annual_revenue_low_M_usd"],
        "revenue_low_on_extra_it_M_usd": [round(extra_scaled * rev, 2), round(extra_fixed * rev, 2)],
        "revenue_overstatement_pct": [round((freed_utility / extra_fixed - 1.0) * 100.0, 1),
                                      round((freed_utility / extra_scaled - 1.0) * 100.0, 1)],
    }

    # 3. Second-law envelope of the sorption stage.
    t_drive = pin_value(pins, "ff.temps", "T_drive_C")
    t_chw_lo, t_chw_hi = pin_value(pins, "ff.temps", "T_chilled_C")
    def keys(node):
        if isinstance(node, dict):
            for k, v in node.items():
                yield k.lower()
                yield from keys(v)
        elif isinstance(node, list):
            for v in node:
                yield from keys(v)

    second_law = {
        "T_drive_C": t_drive, "T_chilled_C": [t_chw_lo, t_chw_hi], "COP_ads_claimed": cop,
        "max_recooling_C_at_chilled_15C": round(recooling_limit_c(t_drive, t_chw_lo, cop), 2),
        "max_recooling_C_at_chilled_18C": round(recooling_limit_c(t_drive, t_chw_hi, cop), 2),
        "reversible_COP_by_recooling_C": {
            f"chilled_{tc:g}C": {str(t): round(cop_tri_thermal(t_drive, t, tc), 3) for t in (25, 30, 35, 40, 45)}
            for tc in (t_chw_lo, t_chw_hi)},
        "second_law_efficiency_at_30C_recooling": [round(cop / cop_tri_thermal(t_drive, 30.0, t_chw_hi), 3),
                                                   round(cop / cop_tri_thermal(t_drive, 30.0, t_chw_lo), 3)],
        "certificate_has_a_recooling_field": any("recool" in k or "reject" in k or "condens" in k for k in keys(ff)),
    }

    # 4. Minimum IT load that still drives the sorption stage.
    alpha = q_liq / P
    area = pin_value(pins, "ff.floor_mass", "floor_area_m2")
    perimeter = pin_value(pins, "ff.geometry", "perimeter_m")
    height = ff["domain_4_top_down_seismic_cellular_frame"]["total_building_height_m"]
    u_roof = ff["domain_1_funicular_radiative_roof"]["U_roof_W_m2K"]
    wall = ff["domain_2_vibro_thermal_sandwich_wall"]
    ua_roof = u_roof * area
    ua_wall, ua_wall_steel = wall["U_wall_cfrp_W_m2K"] * perimeter * height, wall["U_wall_steel_pcsp_W_m2K"] * perimeter * height
    q_env = (ua_roof + ua_wall) * design_dt_k * 1e-6
    q_env_steel = (ua_roof + ua_wall_steel) * design_dt_k * 1e-6
    p_min_env = minimum_load_mw(q_env, alpha, cop)
    p_min = minimum_load_mw(q_env + other, alpha, cop)
    p_min_steel = minimum_load_mw(q_env_steel + other, alpha, cop)
    q_fix = q_env + other
    min_load = {
        "liquid_capture_fraction": round(alpha, 4),
        "threshold_capture_fraction_no_fixed_load": round(1.0 / (1.0 + cop), 4),
        "design_temperature_difference_K": design_dt_k,
        "envelope_gain_MW": round(q_env, 5),
        "envelope_gain_steel_pinned_wall_MW": round(q_env_steel, 5),
        "other_overhead_MW": other,
        "P_min_envelope_only_MW": round(p_min_env, 4),
        "P_min_envelope_plus_overhead_MW": round(p_min, 4),
        "P_min_as_pct_of_nameplate": round(p_min / P * 100.0, 2),
        "P_min_steel_pinned_wall_MW": round(p_min_steel, 4),
        "floor_rise_with_steel_pinned_wall_pct": round((p_min_steel / p_min - 1.0) * 100.0, 1),
        "required_capture_fraction_by_utilisation": {
            str(u): round((1.0 + q_fix / (u * P)) / (1.0 + cop), 4) for u in (1.0, 0.5, 0.25, 0.1)},
        "drive_heat_with_fixed_load_MW": round((q_air + q_fix) / cop, 3),
        "drive_heat_available_MW": q_liq,
    }

    # 5. Thermal budget and ride-through.
    budget = pin_value(pins, "ff.pcm_energy", "pcm_energy_kWh_th")
    leak = pin_value(pins, "ff.heat_leak", "heat_leak_kW")
    liner = wall["passive_ride_through_with_mpcm_min"] * leak / 60.0
    p_kw = P * 1000.0
    thermal = {
        "pcm_budget_kWh_th": budget,
        "wall_liner_budget_kWh_th": round(liner, 2),
        "full_load_ride_through_min": round(budget / p_kw * 60.0, 2),
        "ride_through_min_by_shed_fraction": {
            str(s): round(budget / (p_kw * (1.0 - s)) * 60.0, 2) for s in (0.0, 0.25, 0.5, 0.75)},
        "shed_fraction_to_bridge_outage_min": {
            str(t): round(max(0.0, 1.0 - budget / (p_kw * t / 60.0)), 4) for t in (10, 15, 30, 60)},
        "burst_hours_at_10pct_over_cooling_capacity": round(budget / (0.10 * p_kw), 2),
    }
    return {"pue_reproduction": reproduction, "substation": substation, "second_law": second_law,
            "minimum_load": min_load, "thermal_budget": thermal}


# --------------------------------------------------------------------------- margins
def margin_vector(inp: dict) -> list[dict]:
    """Demand over capacity for every certified limit state of the reference campus."""
    ff, fl, vc, pins = inp["ff"], inp["fl"], inp["vc"], inp["pins"]
    rf, vb = ff["domain_1_funicular_radiative_roof"], ff["domain_3_broadband_vibration_cascade"]
    se, ts = ff["domain_4_top_down_seismic_cellular_frame"], ff["domain_5_6_three_tier_tes_and_closed_loop_cooling"]
    cas, fire = fl["funicular_cassette_9mx3m_313psf"], fl["iso834_120min_fire_crossover"]
    dg, col = fl["dg11_vibration_benchmark"]["active_prestressed_cassette"], fl["aci318_punching_collar_313psf"]["funi_floor_with_collar"]
    sweep = {row["U_duct_m_s"]: row for row in vc["hybrid_cfrp_pcb_coil_sweep"]}
    node_mw = sweep[4.0]["P_total_harvested_mW"] / vc["telemetry_power_margin_at_4ms_x"]
    k_up = pin_value(pins, "ff.uplift_factor", "uplift_factor")
    lim = pin_value(pins, "ff.deflection_limit", "span_over_delta_limit")
    rows = [
        ("rack_vibration", "funi-frame", vb["oem_utilization_pct"] / 100.0 * vb["oem_switch_limit_g_rms"], vb["oem_switch_limit_g_rms"]),
        ("storey_drift", "funi-frame", se["top_down_story_drift_aska_pct"], se["risk_cat_iv_drift_limit_pct"]),
        ("roof_crown_compression", "funi-frame", rf["fc_crown_MPa"], rf["fc_allow_service_MPa"]),
        ("roof_tornado_uplift_factored", "funi-frame", k_up * rf["tornado_net_uplift_kN"], rf["tornado_tiedown_capacity_kN"]),
        ("roof_service_deflection_mm", "funi-frame", rf["delta_vault_mm"], rf["span_m"] * 1000.0 / lim),
        ("sorption_drive_heat", "funi-frame", ts["Q_drive_for_adsorption_MW"], ts["Q_liquid_w45_MW"]),
        ("floor_punching_collar", "funi-floors", col["Vu_313psf_kN"], col["phi_Vn_active_collar_kN"]),
        ("floor_walking_vibration", "funi-floors", dg["ap_pct_g"], dg["office_limit_pct_g"]),
        ("floor_crown_compression", "funi-floors", cas["fc_crown_service_MPa"], cas["fc_service_limit_0.45fc_MPa"]),
        ("floor_fire_120min_thrust", "funi-floors", fire["H_fire_120min_demand_kN"], fire["H_cap_hybrid_fesma_mortar_120min_kN"]),
        ("floor_duct_hole_shear", "funi-floors", cas["V_quarter_mep_demand_uls_kN"], cas["phi_V_45deg_octagonal_mep_hole_kN"]),
        ("sensor_power_at_airflow_turndown", "venturi-collars", node_mw, sweep[1.8]["P_total_harvested_mW"]),
    ]
    derived = {"sensor_power_at_airflow_turndown"}  # the certificate states this margin at 4 m/s only
    return [{"limit_state": n, "source": s, "demand": round(d, 6), "capacity": round(c, 6),
             "utilisation": round(d / c, 6), "basis": "derived here" if n in derived else "certified"}
            for n, s, d, c in rows]


def sensor_alternative(inp: dict) -> dict:
    """The collar at low airflow against the larger node its own certificate names."""
    vc = inp["vc"]
    sweep = {row["U_duct_m_s"]: row for row in vc["hybrid_cfrp_pcb_coil_sweep"]}
    names = " ".join(c["control"] for c in vc["must_fail_controls"])
    larger_mw = int(re.search(r"_(\d+)uW_", names).group(1)) / 1000.0
    return {"larger_node_mW": larger_mw, "harvest_at_turndown_mW": sweep[1.8]["P_total_harvested_mW"],
            "utilisation_with_larger_node": round(larger_mw / sweep[1.8]["P_total_harvested_mW"], 4)}


def plant_radius(margins: list[dict]) -> dict:
    worst = max(margins, key=lambda m: m["utilisation"])
    ordered = sorted(margins, key=lambda m: -m["utilisation"])
    return {"plant_radius": math.floor((1.0 - worst["utilisation"]) * 1e4) / 1e4,  # rounded down, never optimistic
            "binding_limit_state": worst["limit_state"],
            "binding_source": worst["source"], "second_tightest": ordered[1]["limit_state"],
            "second_tightest_utilisation": ordered[1]["utilisation"]}


def ball_in_box_check(u0: list[float], radius: float, samples: int = 20000) -> dict:
    """Every point within `radius` of u0 keeps each coordinate at or below 1.

    A coordinate is largest at the axis point u0 + radius*e_i, so those n points decide the matter. Random
    points on the sphere are sampled as well, and the check is shown to fail for a slightly larger radius.
    """
    n, state, worst = len(u0), 20261117, 0.0
    for _ in range(samples):
        direction = []
        for _ in range(n):
            state = (state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
            direction.append((state >> 11) / float(1 << 53) * 2.0 - 1.0)
        norm = math.sqrt(_sum_sq(direction)) or 1.0
        worst = max(worst, max(u + radius * d / norm for u, d in zip(u0, direction)))
    axis = max(u + radius for u in u0)
    return {"samples": samples, "max_coordinate_at_axis_points": round(axis, 6), "max_coordinate_sampled": round(worst, 6),
            "all_within_limits": max(axis, worst) <= 1.0,
            "fails_if_radius_grows_by_0.001": max(u + radius + 1e-3 for u in u0) > 1.0}


# --------------------------------------------------------------------------- the gate
REASONS = {"ok", "non_finite_parameters", "non_positive_budget_or_cost", "insufficient_metabolic_budget",
           "shape_mismatch", "non_finite_weights", "baseline_distance_exceeded"}


def _flat(values) -> list[float]:
    """Nested lists and tuples as one list of floats. Strings such as "NaN" are parsed, as in Weft's vectors."""
    if not isinstance(values, (list, tuple)):
        return [float(values)]
    out: list[float] = []
    for item in values:
        out.extend(_flat(item) if isinstance(item, (list, tuple)) else [float(item)])
    return out


def _f32(x: float) -> bytes:
    return struct.pack("<f", x)  # raises OverflowError beyond the float32 range, as Weft's gate does


def _masked_distance(x: list[float], y: list[float], locked) -> float | None:
    """Distance over the unlocked coordinates, or None if a value is not finite or a locked coordinate moved.

    A scaled sum of squares with a compensation term. The order of operations follows Weft's reference so
    that the two agree to the last bit.
    """
    scale, ssq, comp = 0.0, 1.0, 0.0
    for i, (xi, yi) in enumerate(zip(x, y)):
        if not (math.isfinite(xi) and math.isfinite(yi)):
            return None
        if int(locked[i]) != 0:
            if not (xi == 0.0 and yi == 0.0) and _f32(xi) != _f32(yi):
                return None
            continue
        step = abs(yi - xi)
        if step == 0.0:
            continue
        if scale < step:
            ratio_sq = (scale / step) * (scale / step)
            ssq, comp, scale = 1.0 + ssq * ratio_sq, comp * ratio_sq, step
        else:
            term = (step / scale) * (step / scale)
            total = ssq + term
            comp += (ssq - total) + term if abs(ssq) >= term else (term - total) + ssq
            ssq = total
    distance = 0.0 if scale == 0.0 else scale * math.sqrt(ssq + comp)
    return distance if math.isfinite(distance) else None


def plant_gate(baseline, candidate, radius, budget, cost, locked=None):
    """Admission predicate of Weft interface I3.

    A step is admitted when the state stays within `radius` of the baseline (Euclidean distance) and
    `budget >= cost > 0`. Returns (accepted, distance, remaining_budget, reason). A rejected step never
    spends budget, except that an underflow reports the deficit so the caller can see it.

    Written from Weft's interface note, its conformance vectors and the list path of its reference
    implementation. No Weft code is imported or copied. The arithmetic at the boundary is deliberately the
    same, and `differential_test` checks the two against each other.
    """
    b, c, r = float(budget), float(cost), float(radius)
    if not all(map(math.isfinite, (b, c, r))):
        return False, math.inf, math.nan, "non_finite_parameters"
    if c <= 0.0:
        return False, math.inf, b, "non_positive_budget_or_cost"
    if b <= 0.0 or r < 0.0:
        return False, math.inf, b - c, "non_positive_budget_or_cost"
    if b < c:
        return False, math.inf, b - c, "insufficient_metabolic_budget"
    x, y = _flat(baseline), _flat(candidate)
    if not x or len(x) != len(y) or (locked is not None and len(locked) != len(x)):
        return False, math.inf, b, "shape_mismatch"
    if locked is None:
        total = 0.0
        for xi, yi in zip(x, y):
            if not (math.isfinite(xi) and math.isfinite(yi)):
                return False, math.inf, b, "non_finite_weights"
            total += (yi - xi) * (yi - xi)
        distance = math.sqrt(total)
        if not math.isfinite(distance):
            return False, math.inf, b, "non_finite_weights"
    else:
        distance = _masked_distance(x, y, locked)
        if distance is None:
            return False, math.inf, b, "non_finite_weights"
    if distance > r:
        return False, distance, b, "baseline_distance_exceeded"
    return True, distance, b - c, "ok"


def _same(a, b) -> bool:
    """Equal results, with NaN equal to NaN."""
    if isinstance(a, float) and isinstance(b, float):
        return (math.isnan(a) and math.isnan(b)) or a == b
    return a == b


def differential_test(oracle_source: bytes, cases: int = 100000, seed: int = 20261117, gate=None) -> dict:
    """plant_gate against Weft's own gate on generated inputs, in the manner of a differential test.

    Weft's module is loaded from the vendored, hash-checked copy and used only as the oracle. The generator
    is deterministic. It aims at the places two implementations drift apart: radii within one unit in the
    last place of the true distance, magnitudes that overflow or underflow a square, locked coordinates that
    move by one float32 step, signed zeros, values that are not finite, nested lists and wrong shapes.
    """
    namespace: dict = {"__name__": "weft_gate_oracle", "__file__": "invariants.py"}
    exec(compile(oracle_source, "invariants.py", "exec"), namespace)
    oracle = namespace["verify_weight_update_safety_ex"]
    gate = gate or plant_gate
    state = seed

    def rnd() -> float:
        nonlocal state
        state = (state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        return (state >> 11) / float(1 << 53)

    def pick(options):
        return options[int(rnd() * len(options))]

    scales = [1e-200, 1e-160, 1e-30, 1e-8, 1e-3, 1.0, 1.0, 1.0, 37.0, 1e3, 1e8, 1e30, 1e150, 1e200]
    special = [math.nan, math.inf, -math.inf, "NaN", "Inf", 0.0, -0.0, 3.5e38, 1e39]
    budgets = [(10.0, 1.0), (1.0, 1.0), (0.5, 1.0), (0.0, 1.0), (-1.0, 1.0), (10.0, 0.0), (10.0, -1.0),
               (math.nan, 1.0), (10.0, math.inf), (1e-300, 1e-300), (2500.0, 1666.7), (1.0, 1.0000000000000002)]
    mismatches, by_reason, raised = [], {}, 0
    for case in range(cases):
        n = 1 + int(rnd() * 6)
        scale = pick(scales)
        base = [(rnd() - 0.5) * 2.0 * scale for _ in range(n)]
        move = pick([0.0, 1e-12, 1e-6, 1e-3, 1.0, 1.0, 5.0])
        cand = [v + (rnd() - 0.5) * 2.0 * scale * move for v in base]
        locked = None
        if rnd() < 0.4:
            locked = [1 if rnd() < 0.5 else 0 for _ in range(n)]
            for i in range(n):
                if locked[i]:
                    how = rnd()
                    cand[i] = base[i] if how < 0.6 else (math.nextafter(base[i], math.inf) if how < 0.8 else cand[i])
                    if how > 0.95:
                        base[i], cand[i] = 0.0, -0.0
        if rnd() < 0.08:
            (cand if rnd() < 0.5 else base)[int(rnd() * n)] = pick(special)
        shape = rnd()
        if shape < 0.03:
            cand = cand[:-1]
        elif shape < 0.05:
            base, cand = [], []
        elif shape < 0.08 and locked is not None:
            locked = locked + [0]
        elif shape < 0.12 and n >= 2:
            base, cand = [base[:1], base[1:]], [cand[:1], tuple(cand[1:])]
        try:
            flat_b, flat_c = _flat(base), _flat(cand)
            true = math.sqrt(_sum_sq(q - p for p, q, m in zip(flat_b, flat_c, locked or [0] * len(flat_b)) if not m))
        except (ValueError, OverflowError):
            true = 1.0
        if not math.isfinite(true):
            true = 1.0
        near = [true, true, math.nextafter(true, math.inf), math.nextafter(true, 0.0), true * (1 + 1e-15),
                true * (1 - 1e-15), true * 1.001, true * 0.999]
        radius = pick(near) if rnd() < 0.85 else pick([0.0, -0.25, 120.0, 1e300, math.nan, math.inf, 0.1989])
        budget, cost = (10.0, 1.0) if rnd() < 0.75 else pick(budgets)
        results = []
        for fn in (gate, oracle):
            try:
                results.append(tuple(fn(base, cand, radius, budget, cost, locked)))
            except Exception as err:  # the two must fail alike as well
                results.append(("raised", type(err).__name__))
        mine, theirs = results
        if len(mine) != len(theirs) or not all(_same(m, t) for m, t in zip(mine, theirs)):
            mismatches.append(case)
        elif mine[0] == "raised":
            raised += 1
        else:
            by_reason[mine[3]] = by_reason.get(mine[3], 0) + 1
    return {"oracle": "Moissanite-Labs/weft weft/runtime/invariants/invariants.py: verify_weight_update_safety_ex",
            "cases": cases, "seed": seed, "mismatches": len(mismatches), "first_mismatches": mismatches[:5],
            "agreed_by_reason": dict(sorted(by_reason.items())), "both_raised_the_same_error": raised}


def _close(x: float, y: float) -> bool:
    if math.isinf(x) or math.isinf(y):
        return x == y
    return math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12)


def weft_conformance(vectors_doc: dict) -> dict:
    failed = []
    for v in vectors_doc["weight_update_vectors"]:
        if v["expected_reason"] not in REASONS:
            raise ValueError(f"Weft vector uses a reason this gate does not know: {v['expected_reason']}")
        ok, dist, rem, reason = plant_gate(v["baseline"], v["candidate"], v["r_invariant"], v["budget"], v["cost"],
                                           v.get("locked_mask"))
        want_dist = float(v["expected_distance"])
        if not (ok == v["expected_accepted"] and reason == v["expected_reason"] and _close(dist, want_dist)
                and _close(rem, float(v["expected_remaining_budget"]))):
            failed.append(v["name"])
    total = len(vectors_doc["weight_update_vectors"])
    return {"schema": vectors_doc["schema"], "weight_update_vectors": total, "passed": total - len(failed),
            "failed": failed, "tension_and_royalty_vectors_out_of_scope": len(vectors_doc["tension_vectors"])
            + len(vectors_doc["royalty_vectors"])}


def worked_admissions(margins: list[dict], radius: float, envelope: dict, p_it_mw: float) -> list[dict]:
    """The gate on plant numbers. Budget is the PCM skid in kWh_th; state is the utilisation vector."""
    u0 = [m["utilisation"] for m in margins]
    names = [m["limit_state"] for m in margins]
    k = names.index("floor_punching_collar")
    budget = envelope["thermal_budget"]["pcm_budget_kWh_th"]
    p_kw = p_it_mw * 1000.0
    out = []

    def run(label, candidate, bud, cost):
        ok, dist, rem, reason = plant_gate(u0, candidate, radius, bud, cost)
        out.append({"case": label, "accepted": ok, "reason": reason, "distance": None if math.isinf(dist) else round(dist, 4),
                    "cost_kWh_th": round(cost, 1), "remaining_kWh_th": round(rem, 1)})
        return rem if ok else bud

    left = run("cooling outage, 10 min at full load", u0, budget, p_kw * 10 / 60)
    left = run("second 10 min outage before recharge, full load", u0, left, p_kw * 10 / 60)
    left = run("same outage after shedding 60 percent of load", u0, left, 0.4 * p_kw * 10 / 60)
    moved = list(u0)  # illustrative: one margin moved, the others held; a real candidate comes from re-running the upstream verifiers
    moved[k] = u0[k] * 1.20
    run("floor punching demand up 20 percent, 5 min outage", moved, budget, p_kw * 5 / 60)
    moved[k] = u0[k] * 1.26
    run("floor punching demand up 26 percent, 5 min outage", moved, budget, p_kw * 5 / 60)
    return out


# --------------------------------------------------------------------------- loop timing
def residual(f_hz: float, tau_s: float) -> float:
    """Amplitude left when a tone is countered by its own copy delayed by tau. 1 means no change, 2 the worst case."""
    return 2.0 * abs(math.sin(math.pi * f_hz * tau_s))


def loop_timing(inp: dict, env: dict) -> dict:
    """The two loop latencies quoted in the Terrafab documents, tried on this building's certified dynamics."""
    pins, fl, vc = inp["pins"], inp["fl"], inp["vc"]
    slow = pin_value(pins, "corpus.latency", "slow_ms") / 1000.0
    fast = pin_value(pins, "corpus.latency", "fast_ms") / 1000.0
    tones = pin_value(pins, "ff.tones", "tones_Hz")
    rows = []
    for f in tones:
        r_slow, r_fast = residual(f, slow), residual(f, fast)
        rows.append({"tone_Hz": f, "cycles_of_delay_slow": round(f * slow, 4), "residual_slow": round(r_slow, 3),
                     "change_dB_slow": round(20.0 * math.log10(r_slow), 1),
                     "cycles_of_delay_fast": round(f * fast, 4), "residual_fast": round(r_fast, 3),
                     "change_dB_fast": round(20.0 * math.log10(r_fast), 1),
                     "longest_delay_that_helps_within_the_cycle_ms": round(1000.0 / (6.0 * f), 2)})
    tb = env["thermal_budget"]
    return {
        "slow_latency_ms": slow * 1000.0, "fast_latency_ms": fast * 1000.0, "plant_tones": rows,
        "tones_countered_within_cycle_slow": sum(1 for f in tones if f * slow < 1.0 / 6.0),
        "tones_countered_within_cycle_fast": sum(1 for f in tones if f * fast < 1.0 / 6.0),
        "tones_amplified_slow": sum(1 for f in tones if residual(f, slow) > 1.0),
        "highest_frequency_countered_within_cycle_slow_Hz": round(1.0 / (6.0 * slow), 2),
        "highest_frequency_countered_within_cycle_fast_Hz": round(1.0 / (6.0 * fast), 2),
        "other_structural_frequencies_Hz": {
            "isolation_stage_1": pin_value(pins, "ff.stages", "stage_Hz")[0],
            "isolation_stage_2": pin_value(pins, "ff.stages", "stage_Hz")[1],
            "floor_cassette": fl["dg11_vibration_benchmark"]["active_prestressed_cassette"]["fn_Hz"],
            "sensor_reed_flutter": vc["hybrid_cfrp_pcb_coil_sweep"][0]["f_flutter_Hz"]},
        "contract_timescales_s": {"thermal_budget_at_full_load": round(tb["full_load_ride_through_min"] * 60.0, 1),
                                  "wall_liner_ride_through": round(tb["wall_liner_budget_kWh_th"] / pin_value(pins, "ff.heat_leak", "heat_leak_kW") * 3600.0, 1)},
        "slow_latency_as_fraction_of_thermal_budget_time": round(slow / (tb["full_load_ride_through_min"] * 60.0), 7),
    }


# --------------------------------------------------------------------------- plant frame
PLANT_FRAME = struct.Struct("<16f")  # the byte layout of Weft's telemetry frame: 16 little-endian float32
FRAME_TAIL = ["thermal_budget_kWh_th", "it_load_MW", "recooling_C", "time_s"]


def encode_plant_frame(utilisations: list[float], budget_kwh: float, it_load_mw: float, recooling_c: float,
                       time_s: float) -> bytes:
    if len(utilisations) != 16 - len(FRAME_TAIL):
        raise ValueError("a plant frame carries exactly 12 margins")
    return PLANT_FRAME.pack(*utilisations, budget_kwh, it_load_mw, recooling_c, time_s)


def decode_plant_frame(raw: bytes) -> dict:
    values = PLANT_FRAME.unpack(raw)
    n = 16 - len(FRAME_TAIL)
    return {"utilisations": list(values[:n]), **dict(zip(FRAME_TAIL, values[n:]))}


def contract_check(frame: dict, load_floor_mw: float, recooling_limit_c: float) -> list[str]:
    """What a decoded frame says about the contract. An empty list means every term holds."""
    found = []
    if not all(map(math.isfinite, frame["utilisations"])):
        found.append("margin_not_measured")
    elif max(frame["utilisations"]) > 1.0:
        found.append("limit_exceeded")
    budget, load, recool = frame["thermal_budget_kWh_th"], frame["it_load_MW"], frame["recooling_C"]
    if not math.isfinite(budget):
        found.append("budget_not_measured")
    elif budget <= 0.0:
        found.append("thermal_budget_exhausted")
    if not math.isfinite(load):
        found.append("load_not_measured")
    elif load < load_floor_mw:
        found.append("below_load_floor")
    if not math.isfinite(recool):
        found.append("recooling_not_measured")
    elif recool >= recooling_limit_c:
        found.append("recooling_above_limit")
    return found


def plant_frame_checks(inp: dict, margins: list[dict], radius: float, env: dict) -> dict:
    spec = inp["pins"]["weft.frame_struct"]["value"]
    u0 = [m["utilisation"] for m in margins]
    k = [m["limit_state"] for m in margins].index("floor_punching_collar")
    budget = env["thermal_budget"]["pcm_budget_kWh_th"]
    p_it = inp["ff"]["domain_5_6_three_tier_tes_and_closed_loop_cooling"]["P_it_MW"]
    floor = env["minimum_load"]["P_min_envelope_plus_overhead_MW"]
    limit = env["second_law"]["max_recooling_C_at_chilled_18C"]  # the looser of the two, so never too strict

    def frame(u=u0, load=p_it, recool=30.0, bud=budget):
        return decode_plant_frame(encode_plant_frame(u, bud, load, recool, 0.0))

    design_raw = encode_plant_frame(u0, budget, p_it, 30.0, 0.0)
    design = decode_plant_frame(design_raw)
    heavy = list(u0)
    heavy[k] = u0[k] * 1.26
    cases = {
        "design point, recooling at 30 C": contract_check(design, floor, limit),
        "design point as certified, no recooling temperature": contract_check(frame(recool=math.nan), floor, limit),
        "idle campus at 0.3 MW": contract_check(frame(load=0.3), floor, limit),
        "recooling at 42 C": contract_check(frame(recool=42.0), floor, limit),
        "floor punching demand up 26 percent": contract_check(frame(u=heavy), floor, limit),
        "thermal budget spent": contract_check(frame(bud=0.0), floor, limit),
    }
    gate_ok = plant_gate(design["utilisations"], design["utilisations"], radius, design["thermal_budget_kWh_th"], 1.0)
    gate_heavy = plant_gate(design["utilisations"], frame(u=heavy)["utilisations"], radius, design["thermal_budget_kWh_th"], 1.0)
    return {
        "layout": spec["struct"], "bytes": len(design_raw), "floats": 16,
        "matches_weft_frame_layout": PLANT_FRAME.format == spec["struct"] and len(design_raw) == spec["bytes"] and spec["floats"] == 16,
        "slots": [m["limit_state"] for m in margins] + FRAME_TAIL,
        "round_trip_max_error": float(f"{max(abs(a - b) for a, b in zip(u0, design['utilisations'])):.1e}"),
        "design_frame_sha256": sha256_bytes(design_raw),
        "contract_check": cases,
        "gate_from_frame": {"design point": gate_ok[3], "floor punching demand up 26 percent": gate_heavy[3]},
    }


# --------------------------------------------------------------------------- the unit
def check_unit(unit: dict, graph: dict) -> dict:
    """Every repository of the map is either placed in the structure or listed as not placed, never both."""
    node_ids = {n["id"] for n in graph["nodes"]}
    placed: set[str] = set()
    for e in unit["elements"]:
        if e["status"] not in unit["statuses"] or e["organ"] not in unit["organs"]:
            raise ValueError(f"unit element {e['id']} has an unknown status or organ")
        for repo in e["repos"]:
            if repo not in node_ids:
                raise ValueError(f"unit element {e['id']} names a repository that is not on the map: {repo}")
            placed.add(repo)
    not_placed = {x["repo"] for x in unit["not_placed"]}
    if placed & not_placed:
        raise ValueError(f"both placed and not placed: {sorted(placed & not_placed)}")
    if (placed | not_placed) != node_ids:
        raise ValueError(f"not accounted for: {sorted(node_ids - placed - not_placed)}; unknown: {sorted((placed | not_placed) - node_ids)}")
    for i in unit["interfaces"]:
        if i["status"] not in unit["interface_statuses"]:
            raise ValueError(f"interface {i['id']} has an unknown status")
    count = lambda items: {s: sum(1 for x in items if x["status"] == s) for s in sorted({x["status"] for x in items})}
    by_org: dict[str, int] = {}
    for repo in placed:
        by_org[org_of(repo)] = by_org.get(org_of(repo), 0) + 1
    return {
        "elements": len(unit["elements"]), "elements_by_status": count(unit["elements"]),
        "elements_with_no_repository": [e["id"] for e in unit["elements"] if not e["repos"]],
        "repositories_placed": len(placed), "repositories_placed_by_org": dict(sorted(by_org.items())),
        "repositories_not_placed": len(not_placed),
        "loop_interfaces": len(unit["interfaces"]), "loop_interfaces_by_status": count(unit["interfaces"]),
        "loop_closed": all(i["status"] == "checked" for i in unit["interfaces"]),
    }


# --------------------------------------------------------------------------- the improvement loop
LOOP_START = {"pcm_kwh": 2500, "capture_ppm": 850000, "wall_u_mw": 132, "floor_kw": 600, "shed_ppm": 300000,
              "step_ppm": 1000000}
LOOP_BUDGET = 64


def _exact(x: float, scale: int, what: str) -> int:
    """A pinned decimal as an integer in a finer unit. Fails if the unit is not fine enough."""
    v = round(x * scale)
    require(abs(x * scale - v) < 1e-6, f"{what} = {x} is not a whole number of 1/{scale}: use a finer unit")
    return v


def loop_plant(inp: dict, env: dict, margins: list[dict]) -> dict:
    """The pinned upstream values the loop's plant model needs, as exact integers."""
    ff, pins = inp["ff"], inp["pins"]
    cp = pins["ff.cooling_power"]["value"]
    fixed = {m["limit_state"]: math.ceil(m["utilisation"] * 1e6 - 1e-9) for m in margins
             if m["limit_state"] != "sorption_drive_heat"}  # the certified margins no gene of the loop can move
    ua_roof = ff["domain_1_funicular_radiative_roof"]["U_roof_W_m2K"] * pin_value(pins, "ff.floor_mass", "floor_area_m2")
    wall = pin_value(pins, "ff.geometry", "perimeter_m") * ff["domain_4_top_down_seismic_cellular_frame"]["total_building_height_m"]
    return {
        "p_it_w": _exact(ff["domain_5_6_three_tier_tes_and_closed_loop_cooling"]["P_it_MW"], 10**6, "IT load in MW"),
        "cop_ppm": _exact(pin_value(pins, "ff.cop_ads", "cop_ads"), 10**6, "sorption COP"),
        "ua_roof_mw_k": _exact(ua_roof, 1000, "roof conductance in W/K"),
        "wall_area_m2": _exact(wall, 1, "wall area in m2"),
        "dt_mk": _exact(env["minimum_load"]["design_temperature_difference_K"], 1000, "design temperature difference in K"),
        "other_w": _exact(env["minimum_load"]["other_overhead_MW"], 10**6, "other overhead in MW"),
        "passive_w": _exact(env["pue_reproduction"]["passive_sinks_MW"], 10**6, "passive sinks in MW"),
        "aux_w": _exact(cp["funi_aux_MW"], 10**6, "auxiliaries in MW"),
        "loop_cop_milli": _exact(cp["ates_cop"], 1000, "loop COP"),
        "fixed": list(fixed.values()), "fixed_names": list(fixed),
        # what could be built or set: declared here, not derived
        "lo": {k: loop.BOUNDS[k][0] for k in loop.oracle.GENES}, "hi": {k: loop.BOUNDS[k][1] for k in loop.oracle.GENES},
    }


def network_first_look(inp: dict, env: dict, plant: dict) -> dict:
    """What a site does to one campus's load floor, and what that means for a network of two.

    Assumption A-4, made here: at any recooling temperature the sorption chiller reaches the same share of
    its reversible COP as at the design point (58 C drive, 18 C chilled water, 30 C recooling). The 30 C
    is the design value proposed in aska-physical/funi-frame#4, not a certified one."""
    pins, ml, sl = inp["pins"], env["minimum_load"], env["second_law"]
    cop = pin_value(pins, "ff.cop_ads", "cop_ads")
    t_drive, t_chw = sl["T_drive_C"], sl["T_chilled_C"][1]
    share = cop / cop_tri_thermal(t_drive, 30.0, t_chw)
    alpha, q_fix = ml["liquid_capture_fraction"], ml["envelope_gain_MW"] + ml["other_overhead_MW"]
    nameplate = plant["p_it_w"] / 1e6

    def site(t_recool: float) -> dict:
        c = share * cop_tri_thermal(t_drive, t_recool, t_chw)
        gain = (1.0 + c) * alpha - 1.0
        floor = q_fix / gain if gain > 0 else math.inf
        return {"recooling_C": t_recool, "sorption_cop": round(c, 3),
                "load_floor_MW": round(floor, 3) if floor <= nameplate else None,
                "load_floor_share_of_nameplate": round(floor / nameplate, 3) if floor <= nameplate else None,
                "cools_itself_at_some_load": floor <= nameplate}

    sites = [site(t) for t in (30.0, 34.0, 36.0, 38.0, 40.0, 41.0)]
    cool, warm = sites[0], sites[3]
    slope = 1.0 + 1000.0 / plant["loop_cop_milli"]
    return {
        "assumption": "A-4: the chiller keeps its design share of the reversible COP at every recooling temperature",
        "share_of_reversible_cop_at_design": round(share, 4),
        "sites": sites,
        "two_campuses": {
            "recooling_C": [cool["recooling_C"], warm["recooling_C"]],
            "load_floors_MW": [cool["load_floor_MW"], warm["load_floor_MW"]],
            "network_load_floor_MW": round(cool["load_floor_MW"] + warm["load_floor_MW"], 3),
            "network_load_floor_share_of_nameplate": round((cool["load_floor_MW"] + warm["load_floor_MW"]) / (2 * nameplate), 3),
            "warm_floor_over_cool_floor": round(warm["load_floor_MW"] / cool["load_floor_MW"], 2),
        },
        # In the upstream plant model utility power is a straight line in IT load, and its slope does not
        # depend on the site. So moving load between campuses changes no energy: placement is degenerate.
        "utility_MW_per_MW_of_IT_load_at_every_site": round(slope, 4),
        "placement_between_campuses_changes_energy_use": False,
    }


def formal_sources_hash() -> str:
    return sha256_bytes(b"".join((FORMAL_DIR / f).read_bytes() for f in FORMAL_SOURCES))


def float_gate_agreement(ledger: dict) -> dict:
    """The floating-point gate against the exact one on every decision of the ledger."""
    agree = skipped = 0
    for e in ledger["entries"]:
        base, cand = [x / 1e6 for x in e["base_ppm"]], [x / 1e6 for x in e["cand_ppm"]]
        exact_dist = math.sqrt(oracle_dist_sq(e["base_ppm"], e["cand_ppm"])) / 1e6
        if abs(exact_dist - e["radius_ppm"] / 1e6) < 1e-9:
            skipped += 1  # too close to the boundary for floating point to be trusted either way
            continue
        ok = plant_gate(base, cand, e["radius_ppm"] / 1e6, float(e["budget_before"]), float(e["cost"]))[0]
        agree += ok == (e["verdict"] == "ok")
    return {"decisions": len(ledger["entries"]), "agree": agree, "within_1e-9_of_boundary_skipped": skipped}


def oracle_dist_sq(base: list[int], cand: list[int]) -> int:
    return loop.oracle.dist_sq(base, cand)


def improvement_loop(inp: dict, env: dict, margins: list[dict]) -> tuple[dict, dict]:
    """Run the loop, and three variants that show what the gate and the proposer each contribute."""
    plant = loop_plant(inp, env, margins)
    ledger = loop.run_loop(plant, LOOP_START, LOOP_BUDGET)
    main = loop.summary(ledger)
    reserve = loop.RESERVE
    loop.RESERVE = loop.LIMIT  # a proposer with no caution of its own
    try:
        naive = loop.summary(loop.run_loop(plant, LOOP_START, LOOP_BUDGET))
    finally:
        loop.RESERVE = reserve
    small = loop.summary(loop.run_loop(plant, LOOP_START, 3))
    frozen_start = dict(LOOP_START, shed_ppm=250000)  # the outage margin sits exactly on its limit
    frozen = loop.summary(loop.run_loop(plant, frozen_start, LOOP_BUDGET))
    below = dict(LOOP_START, floor_kw=500)  # a scheduler floor under the load floor of the plant
    base_m, below_m = loop.model(LOOP_START, plant), loop.model(below, plant)
    refused = (loop.decide(plant, LOOP_START, LOOP_BUDGET, below, "0" * 64)["verdict"],)
    keep = ("decisions", "admitted", "refused", "budget_left", "eta_final_ppm", "worst_margin_ever_admitted_ppm")
    report = {
        "scenario": loop.SCENARIO, "limit_ppm": loop.LIMIT, "proposer_reserve_ppm": reserve,
        "genes": {"hardware": list(loop.HARDWARE), "software": list(loop.SOFTWARE), "proposer": list(loop.META)},
        "margins_in_the_vector": len(base_m["vector"]),
        **main,
        "final_margins_ppm": ledger["final_margins_ppm"],
        "float_gate_on_the_same_decisions": float_gate_agreement(ledger),
        "variants": {
            "proposer_without_reserve": {k: naive[k] for k in keep},
            "budget_of_three": {k: small[k] for k in keep},
            "start_with_a_margin_exactly_at_its_limit": {k: frozen[k] for k in keep},
            "scheduler_floor_below_the_plant_floor": {"objective_gain_ppm": below_m["eta_ppm"] - base_m["eta_ppm"],
                                                      "load_floor_margin_ppm": below_m["margins"]["load_floor"],
                                                      "verdict": refused[0]},
        },
    }
    return ledger, report


def reference_optimum(plant: dict) -> dict:
    """The best objective found by direct search, to measure a proposer against.

    The objective reads only the two software genes, and falls as the scheduler's floor rises. So the
    hardware genes are set to their most generous bounds, and for each of 41 shed levels the floors are
    tried upwards until the design is within every limit."""
    hardware = {"pcm_kwh": plant["hi"]["pcm_kwh"], "capture_ppm": plant["hi"]["capture_ppm"], "wall_u_mw": plant["lo"]["wall_u_mw"]}
    best = None
    for shed in range(plant["lo"]["shed_ppm"], plant["hi"]["shed_ppm"] + 1, 25000):
        for floor in range(plant["lo"]["floor_kw"], plant["hi"]["floor_kw"] + 1):
            design = dict(hardware, floor_kw=floor, shed_ppm=shed)
            m = loop.model(design, plant)
            if max(m["vector"]) <= loop.LIMIT:
                if best is None or m["eta_ppm"] > best[0]:
                    best = (m["eta_ppm"], design)
                break
    return {"objective_ppm": best[0], "design": best[1]}


def held_states_ok(ledger: dict, plant: dict) -> dict:
    """Walk a ledger and check every design that was taken up, without using the step function."""
    ok = [e for e in ledger["entries"] if e["verdict"] == "ok"]
    return {
        "every_design_held_within_limit": all(max(e["cand_ppm"]) <= loop.LIMIT for e in ok),
        "every_design_held_within_bounds": all(plant["lo"][k] <= e["proposed"][k] <= plant["hi"][k]
                                               for e in ok for k in loop.oracle.GENES),
        "objective_never_fell": all(e["eta_after_ppm"] >= e["eta_before_ppm"] for e in ok),
        "changes_within_budget": len(ok) + ledger["final_budget"] == ledger["head"]["budget"] and ledger["final_budget"] >= 0,
    }


def adversary_run(plant: dict, proposals: int = 3000, seed: int = 20261117) -> tuple[dict, dict]:
    """A proposer that tries to break the loop: designs out of bounds, past a limit and worse, then random ones."""
    rng = random.Random(seed)
    start = loop.genes(LOOP_START)
    props = [{"set": {"capture_ppm": 2_000_000}}, {"set": {"pcm_kwh": -1}}, {"set": {"floor_kw": 0}},
             {"set": {"floor_kw": 500}}, {"set": {"floor_kw": 620}}, {"set": {"pcm_kwh": 2400, "shed_ppm": 200_000}}]
    for _ in range(proposals):
        chosen = rng.sample(loop.oracle.GENES, rng.randint(1, 5))
        if rng.random() < 0.5:  # anywhere, including just outside the bounds
            props.append({"set": {g: rng.randint(plant["lo"][g] - 50, plant["hi"][g] + 50) for g in chosen}})
        else:  # near the start, where the gate may say yes
            props.append({"set": {g: start[g] + rng.randint(-3, 3) * loop.STEP[g] for g in chosen}})
    ledger = loop.run_proposals(plant, start, LOOP_BUDGET, props)
    verdicts: dict[str, int] = {}
    for e in ledger["entries"]:
        verdicts[e["verdict"]] = verdicts.get(e["verdict"], 0) + 1
    report = {"proposals": len(props), "seed": seed, "verdicts": dict(sorted(verdicts.items())),
              "first_six_verdicts": [e["verdict"] for e in ledger["entries"][:6]],
              "taken_up": verdicts.get("ok", 0), "budget": LOOP_BUDGET, "budget_left": ledger["final_budget"],
              "eta_start_ppm": ledger["head"]["start_eta_ppm"], "eta_final_ppm": ledger["final_eta_ppm"],
              **held_states_ok(ledger, plant), "chain_intact": loop.check_chain(ledger),
              "entries_follow_from_one_another": loop.check_continuity(ledger), "final_hash": ledger["final_hash"]}
    return ledger, report


def proposer_run(plant: dict, seeded: dict, run_file: str) -> tuple[dict | None, dict]:
    """Replay the recorded run of an outside proposer and compare it with the seeded search."""
    if not (ROOT / "results" / run_file).exists():
        return None, {"present": False}
    run = read_json(ROOT / "results" / run_file)
    ledger = loop.run_proposals(plant, run["start"], run["budget"], run["proposals"])
    s = loop.summary(ledger)
    best = reference_optimum(plant)
    gain = lambda eta: round((eta - s["eta_start_ppm"]) / (best["objective_ppm"] - s["eta_start_ppm"]), 4)
    edited = copy.deepcopy(run["proposals"])
    for prop in edited:  # change the first proposal that was taken up by one unit
        gene = next(iter(prop["set"]))
        prop["set"][gene] += 1
        break
    report = {
        "present": True, "proposer": run["proposer"], "run_file": f"results/{run_file}",
        **({"lessons_file": run["lessons_file"]} if "lessons_file" in run else {}),
        "turns_allowed": run["turns"], "proposals": len(run["proposals"]),
        "every_proposal_has_a_reason": all(p.get("why", "").strip() for p in run["proposals"]),
        **{k: s[k] for k in ("admitted", "refused", "admitted_hardware_changes", "admitted_software_changes",
                             "admitted_changes_to_both_at_once", "budget_start", "budget_left", "eta_start_ppm",
                             "eta_final_ppm", "worst_margin_ever_admitted_ppm", "final_genome", "chain_intact",
                             "entries_follow_from_one_another", "final_hash")},
        **held_states_ok(ledger, plant),
        "final_margins_ppm": ledger["final_margins_ppm"],
        "best_objective_found_by_direct_search": best,
        "share_of_the_possible_gain_reached": gain(s["eta_final_ppm"]),
        "against_the_seeded_search": {
            "seeded": {"proposals": seeded["decisions"], "changes": seeded["admitted"], "eta_final_ppm": seeded["eta_final_ppm"],
                       "share_of_the_possible_gain_reached": gain(seeded["eta_final_ppm"])},
            "recorded": {"proposals": len(run["proposals"]), "changes": s["admitted"], "eta_final_ppm": s["eta_final_ppm"],
                         "share_of_the_possible_gain_reached": gain(s["eta_final_ppm"])},
        },
        "edited_proposal_changes_the_ledger":
            loop.run_proposals(plant, run["start"], run["budget"], edited)["final_hash"] != ledger["final_hash"],
    }
    return ledger, report


def formal_record(ledgers: dict) -> dict:
    """What the committed formal record must say about the current ledgers and Lean sources."""
    if not FORMAL_PATH.exists():
        return {"present": False}
    rec = read_json(FORMAL_PATH)
    return {"present": True, "lean": rec["lean"], "theorems": rec["theorems"], "comparator": rec["comparator"],
            "replay": rec["replay"], "differential_tests": rec["differential_tests"], "bar": rec["bar"],
            "matches_current_lean_sources": rec["sources_sha256"] == formal_sources_hash(),
            "matches_current_ledgers": rec.get("ledger_hashes") == {k: l["final_hash"] for k, l in ledgers.items()},
            "matches_current_ledger": rec.get("ledger_hashes", {}).get("seeded_search") == ledgers["seeded_search"]["final_hash"]}


def run_formal(ledgers: dict) -> int:
    """Rebuild the proofs, run the comparator and the differential tests, and replay every ledger in Lean."""
    def sh(cmd, **kw):
        return subprocess.run(cmd, cwd=FORMAL_DIR, capture_output=True, text=True, **kw)

    build = sh(["lake", "build"])
    if build.returncode:
        print(build.stdout[-2000:] + build.stderr[-2000:], file=sys.stderr)
        return 1
    comparator = sh(["lake", "comparator", "--paranoid"])
    accepted = comparator.returncode == 0 and "Your solution is okay!" in comparator.stdout
    kernels = sorted(set(re.findall(r"^(.+?) kernel accepts the solution$", comparator.stdout, flags=re.M)))
    tests = sh([sys.executable, "tests/run_tests.py"])
    results = (FORMAL_DIR / "tests" / "TEST-RESULTS.md").read_text(encoding="utf-8")
    field = lambda name: re.search(rf"^- {name}: (.+)$", results, flags=re.M).group(1)
    replay, mismatches = {}, 0
    for name, ledger in ledgers.items():
        lines = loop.replay_lines(ledger)
        out = sh([str(FORMAL_DIR / ".lake" / "build" / "bin" / "plantgate")], input="\n".join(lines) + "\n").stdout.split("\n")
        bad = sum(1 for want, got in zip(loop.replay_expected(ledger), out) if got != want) + max(0, len(lines) - len(out))
        whole, want_whole = loop.replay_whole(ledger)  # the same run in one piece, through the proved `loop` and `changes`
        got_whole = sh([str(FORMAL_DIR / ".lake" / "build" / "bin" / "plantgate")], input=whole + "\n").stdout.strip()
        bad += got_whole != want_whole
        replay[name] = {"decisions": len(lines), "mismatches": bad, "whole_run_through_lean_loop_agrees": got_whole == want_whole}
        mismatches += bad
    decisions = sum(r["decisions"] for r in replay.values())
    lean = sh(["lake", "env", "lean", "--version"]).stdout.strip()
    record = {
        "schema": "optifab-formal/1", "lean": lean,
        "theorems": read_json(FORMAL_DIR / "comparator.json")["theorem_names"],
        "comparator": {"command": "lake comparator --paranoid", "accepted": accepted, "kernels": kernels},
        "differential_tests": {"inputs": int(field("Inputs")), "seed": int(field("Seed")), "failures": int(field("Failures")),
                               "passed": tests.returncode == 0},
        "replay": {"decisions": decisions, "mismatches": mismatches, "by_ledger": replay},
        "bar": "Proven Commons bar check: items 2 to 6 pass; item 1 is open (no reviewer has approved the specification). See formal/BAR-REPORT.md.",
        "sources_sha256": formal_sources_hash(), "ledger_hashes": {k: l["final_hash"] for k, l in ledgers.items()},
    }
    ok = accepted and tests.returncode == 0 and not mismatches and int(field("Failures")) == 0
    if ok:
        FORMAL_PATH.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[FORMAL] comparator {'accepts' if accepted else 'REJECTS'} {len(record['theorems'])} theorems under {len(kernels)} kernels; "
          f"{record['differential_tests']['inputs']} differential tests, {record['differential_tests']['failures']} failures; "
          f"ledger replay {decisions} decisions, {mismatches} mismatches")
    return 0 if ok else 1


# --------------------------------------------------------------------------- cross-certificate interfaces
def interface_checks(inp: dict, floor_mass_override: float | None = None) -> list[dict]:
    """Values one repository copied by hand from another. Each is compared with its source."""
    ff_pins, fl, vc = inp["pins"], inp["fl"], inp["vc"]
    cas = fl["funicular_cassette_9mx3m_313psf"]
    floor_mass = cas["dead_mass_kg_m2"] if floor_mass_override is None else floor_mass_override
    fe = ff_pins["ff.fesma"]["value"]
    sma = fe["sigma0_MPa"] * math.tanh((fe["T_act_C"] - fe["T0_C"]) / fe["T_scale_C"])
    baseline = floor_mass / (1.0 - cas["dead_mass_reduction_vs_744kg_pt_pct"] / 100.0)
    sweep = {row["U_duct_m_s"]: row for row in vc["hybrid_cfrp_pcb_coil_sweep"]}
    node = sweep[4.0]["P_total_harvested_mW"] / vc["telemetry_power_margin_at_4ms_x"]
    rows = [
        ("floor dead mass, kg/m2", pin_value(ff_pins, "ff.floor_mass", "floor_mass_kg_m2"), floor_mass, 0.005, "funi-frame verify.py", "funi-floors certificate"),
        ("conventional floor mass, kg/m2", pin_value(ff_pins, "ff.conv_floor_mass", "conv_floor_mass_kg_m2"), baseline, 0.5, "funi-frame verify.py", "funi-floors certificate (mass and reduction)"),
        ("Fe-SMA recovery stress, MPa", sma, cas["fe_sma_recovery_stress_MPa"], 0.005, "funi-frame verify.py", "funi-floors certificate"),
        ("rack live load, kPa", pin_value(ff_pins, "ff.rack_live", "rack_live_kPa"), 313.0 * PSF_TO_KPA, 0.05, "funi-frame verify.py", "funi-floors 313 psf case"),
        ("leak-sensor reactance shift, %", pin_value(ff_pins, "ff.eis_text", "eis_shift_pct"), fl["embodied_carbon_and_eis_leak_twin"]["eis_50khz_coolant_leak_reactance_shift_pct"], 0.005, "funi-frame ENGINEERING_STUDIES.md", "funi-floors certificate"),
        ("sensor node power, mW", pin_value(ff_pins, "vc.node_power", "node_power_mW"), node, 0.0005, "venturi-collars README.md", "venturi-collars certificate (harvest over margin)"),
    ]
    return [{"quantity": q, "downstream_value": round(a, 4), "upstream_value": round(b, 4), "tolerance": tol,
             "downstream": dn, "upstream": up, "agrees": abs(a - b) <= tol} for q, a, b, tol, dn, up in rows]


# --------------------------------------------------------------------------- lineage graph
def org_of(node_id: str) -> str:
    return node_id.split("/")[0]


def check_graph(graph: dict, sources: dict, rank: dict, max_depth: int, require_pinned: bool = True) -> dict:
    nodes = {n["id"]: n for n in graph["nodes"]}
    if len(nodes) != len(graph["nodes"]):
        raise ValueError("duplicate node id")
    lineage_types = set(graph["lineage_types"])
    for n in graph["nodes"]:
        if n["layer"] not in graph["layers"]:
            raise ValueError(f"unknown layer on {n['id']}")
        if n.get("evidence") is not None and n["evidence"] not in rank:
            raise ValueError(f"unknown evidence level on {n['id']}")
    parents: dict[str, set[str]] = {i: set() for i in nodes}
    children: dict[str, set[str]] = {i: set() for i in nodes}
    cites = [e.get("cite") for e in graph["edges"]] + [n["status_cite"] for n in graph["nodes"] if n.get("status_cite")]
    for e in graph["edges"]:
        if e["src"] not in nodes or e["dst"] not in nodes:
            raise ValueError(f"edge names an unknown node: {e['src']} -> {e['dst']}")
        if e["type"] not in graph["edge_types"]:
            raise ValueError(f"unknown edge type {e['type']}")
        if not e.get("cite") or not e["cite"].get("find"):
            raise ValueError(f"edge without a citation: {e['src']} -> {e['dst']}")
        if e["type"] in lineage_types:
            parents[e["dst"]].add(e["src"])
            children[e["src"]].add(e["dst"])
    if require_pinned:
        for c in cites:
            if c["line"] < 1 or c["path"] not in sources["repos"].get(c["repo"], {}).get("files", {}):
                raise ValueError(f"citation not pinned: {c['repo']}:{c['path']}")

    depth: dict[str, int] = {}
    visiting: set[str] = set()

    def longest(i: str) -> int:
        if i in depth:
            return depth[i]
        if i in visiting:
            raise ValueError(f"lineage cycle through {i}")
        visiting.add(i)
        depth[i] = 1 + max((longest(p) for p in parents[i]), default=-1)
        visiting.discard(i)
        return depth[i]

    for i in nodes:
        longest(i)
    deepest = max(depth.values())
    if deepest >= max_depth:  # Weft's registry requires depth < MAX_LINEAGE_DEPTH
        raise ValueError(f"lineage depth {deepest} is not below the bound {max_depth}")

    physical = set(graph["physical_layers"])

    def closure(start: str, rel: dict[str, set[str]]) -> set[str]:
        """Nodes reachable from `start`, walking only through the physical layers."""
        seen, stack = set(), [start]
        while stack:
            for nxt in rel[stack.pop()]:
                if nxt not in seen and nodes[nxt]["layer"] in physical:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    me = "aska-physical/optifab"
    stack_nodes = closure(me, parents) | {me}
    by_evidence: dict[str, int] = {}
    table = []
    for i in sorted(stack_nodes, key=lambda x: (-len(closure(x, children) & stack_nodes), x)):
        ev = nodes[i].get("evidence")
        label = ev or ("no result claimed" if nodes[i]["kind"] == "direction" else "not rated")
        by_evidence[label] = by_evidence.get(label, 0) + 1
        row = {"node": i, "evidence": label, "rank": rank.get(ev, 0),
               "downstream_in_stack": len(closure(i, children) & stack_nodes)}
        if ev:
            row["assigned_by"] = nodes[i].get("evidence_by", "source")
        table.append(row)
    cross: dict[str, int] = {}
    cross_new: dict[str, int] = {}
    for e in graph["edges"]:
        a, b = org_of(e["src"]), org_of(e["dst"])
        if a != b:
            key = " <-> ".join(sorted((a, b)))
            target = cross_new if e.get("new") else cross
            target[key] = target.get(key, 0) + 1
    pair = "Moissanite-Labs <-> aska-physical"
    return {
        "nodes": len(nodes), "edges": len(graph["edges"]),
        "nodes_by_org": {o: sum(1 for i in nodes if org_of(i) == o) for o in sorted({org_of(i) for i in nodes})},
        "nodes_by_layer": {l: sum(1 for n in graph["nodes"] if n["layer"] == l) for l in sorted(graph["layers"])},
        "lineage_edges": sum(1 for e in graph["edges"] if e["type"] in lineage_types),
        "lineage_acyclic": True, "lineage_depth": deepest, "lineage_depth_bound": max_depth,
        "optifab_lineage_depth": depth[me],
        "stack_size": len(stack_nodes), "stack_by_evidence": dict(sorted(by_evidence.items())),
        "strongest_evidence_rank_in_stack": max(r["rank"] for r in table),
        "stack": table,
        "cross_org_links_before": dict(sorted(cross.items())),
        "cross_org_links_added": dict(sorted(cross_new.items())),
        "aska_physical_to_moissanite_links_before": cross.get(pair, 0),
        "aska_physical_to_moissanite_links_added": cross_new.get(pair, 0),
        "checked_and_closed_links": sum(1 for e in graph["edges"] if e["type"] == "checked_unrelated"),
    }


# --------------------------------------------------------------------------- must-fail controls
def _rejects(fn) -> bool:
    try:
        fn()
    except (ValueError, SystemExit):
        return True
    return False


def _raises(fn) -> bool:
    try:
        fn()
    except RuntimeError:
        return True
    return False


def must_fail_controls(inp: dict, env: dict, margins: list[dict], radius: dict, rank: dict, max_depth: int,
                       timing: dict, frames: dict, ledger: dict, evolution: dict, formal: dict,
                       adversary: dict, recorded_runs: dict, network: dict, asserts: dict) -> dict:
    pins, graph, sources = inp["pins"], inp["graph"], inp["sources"]
    sub, sl, ml = env["substation"], env["second_law"], env["minimum_load"]
    cop = pin_value(pins, "ff.cop_ads", "cop_ads")
    t_drive = pin_value(pins, "ff.temps", "T_drive_C")
    u0 = [m["utilisation"] for m in margins]
    r_star = radius["plant_radius"]
    k = max(range(len(u0)), key=lambda i: u0[i])
    budget = env["thermal_budget"]["pcm_budget_kWh_th"]
    alpha, q_fix = ml["liquid_capture_fraction"], ml["envelope_gain_MW"] + ml["other_overhead_MW"]
    p_it = inp["ff"]["domain_5_6_three_tier_tes_and_closed_loop_cooling"]["P_it_MW"]
    threshold = ml["threshold_capture_fraction_no_fixed_load"]
    oracle_source = inp["weft_gate_oracle"]

    def over(eps):
        cand = list(u0)
        cand[k] = u0[k] + r_star + eps
        return cand

    def cyclic():
        g = copy.deepcopy(graph)
        g["edges"].append({"src": "aska-physical/funi-frame", "dst": "Foundation-0/incentre-lattices", "type": "builds_on",
                           "cite": {"repo": "x", "path": "x", "find": "x", "line": 1}})
        check_graph(g, sources, rank, max_depth, require_pinned=False)

    def chain(depth: int):
        """The real graph plus a synthetic lineage chain of exactly this depth."""
        g = copy.deepcopy(graph)
        for i in range(depth + 1):
            g["nodes"].append({"id": f"aska-physical/synthetic-{i}", "layer": "L2", "kind": "model"})
            if i:
                g["edges"].append({"src": f"aska-physical/synthetic-{i - 1}", "dst": f"aska-physical/synthetic-{i}",
                                   "type": "builds_on", "cite": {"repo": "x", "path": "x", "find": "x", "line": 1}})
        check_graph(g, sources, rank, max_depth, require_pinned=False)

    def hypot_gate(baseline, candidate, radius, budget, cost, locked=None):
        """A gate that is right in exact arithmetic and differs from Weft only in how it sums the squares."""
        verdict = plant_gate(baseline, candidate, radius, budget, cost, locked)
        if locked is not None or verdict[3] not in ("ok", "baseline_distance_exceeded"):
            return verdict
        distance = math.hypot(*[q - p for p, q in zip(_flat(baseline), _flat(candidate))])
        if distance > float(radius):
            return False, distance, float(budget), "baseline_distance_exceeded"
        return True, distance, float(budget) - float(cost), "ok"

    def uncited():
        g = copy.deepcopy(graph)
        g["edges"][0]["cite"] = {}
        check_graph(g, sources, rank, max_depth, require_pinned=False)

    def tampered_input():
        item = inp["manifest"]["files"][0]
        raw = (DATA / "upstream" / item["file"]).read_bytes()
        parse_vendored(item, raw.replace(b"1.074", b"1.064", 1))  # the same loader, fed an edited certificate

    def unit_gap():
        u = copy.deepcopy(inp["unit"])
        u["not_placed"].pop()
        check_unit(u, graph)

    cc = frames["contract_check"]
    variants = evolution["variants"]
    edited = copy.deepcopy(ledger)
    edited["entries"][0]["verdict"] = "ok" if edited["entries"][0]["verdict"] != "ok" else "distance"
    rehashed = copy.deepcopy(ledger)  # one entry starts from a design nobody held; every hash is then made good again
    rehashed["entries"][1]["held"] = dict(rehashed["entries"][1]["held"], pcm_kwh=rehashed["entries"][1]["held"]["pcm_kwh"] + 1)
    prev = "0" * 64
    for e in rehashed["entries"]:
        e["prev"] = prev
        e["hash"] = prev = loop.digest({k: v for k, v in e.items() if k != "hash"})
    rehashed["final_hash"] = prev
    flipped = copy.deepcopy(inp["weft_vectors"])
    flipped["weight_update_vectors"][1]["expected_accepted"] = False
    drift = interface_checks(inp, floor_mass_override=200.0)
    controls = {
        # Fails, by design, the day funi-frame computes its revenue on IT power: finding 1 is then out of date.
        "must_fail_01_upstream_revenue_is_computed_on_it_power":
            sub["certificate_revenue_low_M_usd"] > 1.02 * max(sub["revenue_low_on_extra_it_M_usd"])
            and sub["extra_it_if_auxiliaries_are_fixed_MW"] < sub["certificate_freed_substation_power_MW"],
        "must_fail_02_recooling_at_45C_keeps_the_claimed_cop_within_the_second_law":
            cop_tri_thermal(t_drive, 45.0, sl["T_chilled_C"][1]) < cop < cop_tri_thermal(t_drive, 30.0, sl["T_chilled_C"][1]),
        "must_fail_03_capture_below_the_threshold_self_cools_at_some_load":
            math.isinf(minimum_load_mw(q_fix, threshold - 0.01, cop)) and math.isfinite(minimum_load_mw(q_fix, alpha, cop)),
        # funi-frame's Theorem 4 threshold is necessary, not sufficient, once a fixed load exists
        "must_fail_04_capture_one_point_above_the_threshold_self_cools_at_nameplate":
            minimum_load_mw(q_fix, threshold + 0.01, cop) > p_it > minimum_load_mw(q_fix, alpha, cop)
            and not self_cools(p_it, threshold + 0.01, cop, q_fix),
        "must_fail_05_steel_pinned_wall_keeps_the_same_load_floor":
            ml["P_min_steel_pinned_wall_MW"] > 1.25 * ml["P_min_envelope_plus_overhead_MW"],
        "must_fail_06_full_load_30min_outage_fits_the_pcm_budget":
            plant_gate(u0, u0, r_star, budget, p_it * 1000.0 * 0.5)[3] == "insufficient_metabolic_budget",
        "must_fail_07_negative_cost_recharges_the_budget":
            plant_gate(u0, u0, r_star, budget, -500.0)[2:] == (budget, "non_positive_budget_or_cost"),
        "must_fail_08_step_past_the_tightest_margin_is_admitted":
            plant_gate(u0, over(1e-4), r_star, budget, 1.0)[3] == "baseline_distance_exceeded"
            and plant_gate(u0, over(1e-4), r_star + 2e-4, budget, 1.0)[0] and over(1e-4)[k] > 1.0,
        "must_fail_09_tampered_vendored_input_is_accepted": _rejects(tampered_input),
        "must_fail_10_lineage_cycle_is_accepted": _rejects(cyclic),
        "must_fail_11_lineage_at_the_weft_depth_bound_is_accepted":
            _rejects(lambda: chain(max_depth)) and not _rejects(lambda: chain(max_depth - 1)),
        "must_fail_12_link_without_citation_is_accepted": _rejects(uncited),
        "must_fail_13_corrupted_weft_vector_goes_unnoticed": weft_conformance(flipped)["failed"] == ["valid_small_move"],
        "must_fail_14_drift_in_a_hand_copied_constant_goes_unnoticed":
            [r["quantity"] for r in drift if not r["agrees"]] == ["floor dead mass, kg/m2", "conventional floor mass, kg/m2"],
        "must_fail_15_slow_loop_counters_a_plant_tone_within_its_cycle":
            timing["tones_countered_within_cycle_slow"] == 0 and timing["tones_countered_within_cycle_fast"] == len(timing["plant_tones"])
            and timing["plant_tones"][0]["residual_slow"] > 1.0 > timing["plant_tones"][0]["residual_fast"],
        "must_fail_16_certified_design_point_fills_a_frame_without_a_recooling_temperature":
            cc["design point as certified, no recooling temperature"] == ["recooling_not_measured"]
            and cc["design point, recooling at 30 C"] == [] and cc["recooling at 42 C"] == ["recooling_above_limit"],
        "must_fail_17_frame_past_a_limit_or_below_the_floor_passes_the_contract":
            cc["floor punching demand up 26 percent"] == ["limit_exceeded"] and cc["idle campus at 0.3 MW"] == ["below_load_floor"]
            and cc["thermal budget spent"] == ["thermal_budget_exhausted"]
            and frames["gate_from_frame"]["floor punching demand up 26 percent"] == "baseline_distance_exceeded",
        "must_fail_18_repository_left_out_of_the_unit_goes_unnoticed": _rejects(unit_gap),
        "must_fail_19_gate_with_a_different_rounding_passes_the_differential_test":
            differential_test(oracle_source, cases=20000, gate=hypot_gate)["mismatches"] > 0,
        "must_fail_20_loop_admits_a_state_past_a_limit":
            evolution["every_admitted_state_within_limit"] and evolution["admitted"] > 0
            and variants["proposer_without_reserve"]["worst_margin_ever_admitted_ppm"] <= loop.LIMIT
            and variants["scheduler_floor_below_the_plant_floor"]["objective_gain_ppm"] > 0
            and variants["scheduler_floor_below_the_plant_floor"]["verdict"] == "distance",
        "must_fail_21_loop_makes_more_changes_than_its_budget":
            variants["budget_of_three"]["admitted"] == 3 and variants["budget_of_three"]["budget_left"] == 0
            and evolution["admitted"] + evolution["budget_left"] == evolution["budget_start"],
        "must_fail_22_design_with_a_margin_at_its_limit_can_still_change":
            variants["start_with_a_margin_exactly_at_its_limit"]["admitted"] == 0
            and variants["start_with_a_margin_exactly_at_its_limit"]["decisions"] > 0,
        "must_fail_23_edited_ledger_entry_keeps_the_chain": loop.check_chain(ledger) and not loop.check_chain(edited),
        "must_fail_24_formal_record_is_stale_or_missing":
            formal.get("present", False) and formal["matches_current_lean_sources"] and formal["matches_current_ledger"]
            and formal["comparator"]["accepted"] and formal["replay"]["mismatches"] == 0
            and formal["matches_current_ledgers"]
            and formal["replay"]["by_ledger"]["seeded_search"]["decisions"] == evolution["decisions"],
        "must_fail_25_adversary_moves_the_design_out_of_its_envelope":
            adversary["first_six_verdicts"] == ["bounds", "bounds", "distance", "distance", "worse", "distance"]
            and adversary["taken_up"] > 0 and adversary["every_design_held_within_limit"]
            and adversary["every_design_held_within_bounds"] and adversary["objective_never_fell"]
            and adversary["changes_within_budget"] and adversary["chain_intact"],
        "must_fail_26_recorded_run_of_an_outside_proposer_breaks_a_rule_or_can_be_edited_unseen":
            recorded_runs["recorded_proposer"]["present"] and all(
                r["every_proposal_has_a_reason"] and r["chain_intact"] and r["every_design_held_within_limit"]
                and r["every_design_held_within_bounds"] and r["objective_never_fell"] and r["changes_within_budget"]
                and r["proposals"] <= r["turns_allowed"] and r["edited_proposal_changes_the_ledger"]
                for r in recorded_runs.values() if r["present"]),
        "must_fail_28_ledger_whose_entries_do_not_follow_from_one_another_passes":
            loop.check_continuity(ledger) and loop.check_chain(rehashed) and not loop.check_continuity(rehashed)
            and adversary["entries_follow_from_one_another"]
            and all(r["entries_follow_from_one_another"] for r in recorded_runs.values() if r["present"])
            and all(r.get("whole_run_through_lean_loop_agrees", False) for r in formal["replay"]["by_ledger"].values()),
        "must_fail_29_check_that_python_O_would_strip":
            asserts["assert_statements"] == 0 and asserts["scanner_finds_a_planted_assert"]
            and _raises(lambda: require(False, "probe")),
        "must_fail_27_warm_site_campus_counted_with_the_design_load_floor":
            abs(network["sites"][0]["load_floor_MW"] - ml["P_min_envelope_plus_overhead_MW"]) < 0.001
            and network["two_campuses"]["warm_floor_over_cool_floor"] > 2.0
            and not network["sites"][-1]["cools_itself_at_some_load"]
            and network["sites"][-1]["recooling_C"] < sl["max_recooling_C_at_chilled_18C"],
    }
    return controls


# --------------------------------------------------------------------------- certificate
def build_certificate(with_ledger: bool = False, check: bool = True):
    inp = load_inputs()
    pins = inp["pins"]
    rank = pins["f0.evidence_rank"]["value"]
    max_depth = pin_value(pins, "weft.max_lineage_depth", "max_lineage_depth")
    theorems = symbolic_theorems()
    env = plant_envelope(inp)
    margins = margin_vector(inp)
    radius = plant_radius(margins)
    ball = ball_in_box_check([m["utilisation"] for m in margins], radius["plant_radius"])
    conformance = weft_conformance(inp["weft_vectors"])
    differential = differential_test(inp["weft_gate_oracle"])
    ts = inp["ff"]["domain_5_6_three_tier_tes_and_closed_loop_cooling"]
    admissions = worked_admissions(margins, radius["plant_radius"], env, ts["P_it_MW"])
    interfaces = interface_checks(inp)
    graph = check_graph(inp["graph"], inp["sources"], rank, max_depth)
    timing = loop_timing(inp, env)
    frames = plant_frame_checks(inp, margins, radius["plant_radius"], env)
    unit = check_unit(inp["unit"], inp["graph"])
    ledger, evolution = improvement_loop(inp, env, margins)
    plant = loop_plant(inp, env, margins)
    adversary_ledger, adversary = adversary_run(plant)
    ledgers = {"seeded_search": ledger, "adversary": adversary_ledger}
    recorded_runs = {}
    for key, (run_file, _) in RECORDED_RUNS.items():
        run_ledger, recorded_runs[key] = proposer_run(plant, evolution, run_file)
        if run_ledger is not None:
            ledgers[key] = run_ledger
    recorded = recorded_runs["recorded_proposer"]
    second = recorded_runs["recorded_proposer_given_lessons"]
    if second["present"]:  # what the lessons of the first run were worth to the second
        first_reached = lambda r, target: next((i + 1 for i, e in enumerate(ledgers[r]["entries"])
                                                if e["verdict"] == "ok" and e["eta_after_ppm"] >= target), None)
        target = min(recorded["eta_final_ppm"], second["eta_final_ppm"])
        second["against_the_first_run"] = {
            "objective_both_runs_reached_ppm": target,
            "proposals_needed_first_run": first_reached("recorded_proposer", target),
            "proposals_needed_with_lessons": first_reached("recorded_proposer_given_lessons", target),
            "refused_first_run": sum(recorded["refused"].values()), "refused_with_lessons": sum(second["refused"].values()),
            "eta_final_first_run_ppm": recorded["eta_final_ppm"], "eta_final_with_lessons_ppm": second["eta_final_ppm"],
            "lessons_file_sha256": sha256_bytes((ROOT / second["lessons_file"]).read_bytes()),
        }
    formal = formal_record(ledgers)
    network = network_first_look(inp, env, plant)
    asserts = bare_asserts()
    controls = must_fail_controls(inp, env, margins, radius, rank, max_depth, timing, frames, ledger, evolution, formal,
                                  adversary, recorded_runs, network, asserts)

    require(env["pue_reproduction"]["liquid_plus_air_equals_it_load"] and env["pue_reproduction"]["matches_certificate"], 'the plant heat balance does not reproduce the upstream certificate')
    require(not env["second_law"]["certificate_has_a_recooling_field"], "funi-frame now carries a recooling field: revisit finding 2")
    require(ball["all_within_limits"] and ball["fails_if_radius_grows_by_0.001"], 'the ball of the plant radius does not stay within every limit, or the check cannot fail')
    require(not conformance["failed"], conformance["failed"])
    require(differential["mismatches"] == 0, differential["first_mismatches"])
    require(all(r["agrees"] for r in interfaces), [r["quantity"] for r in interfaces if not r["agrees"]])
    require([a["accepted"] for a in admissions] == [True, False, True, True, False], admissions)
    require(graph["aska_physical_to_moissanite_links_before"] == 0 and graph["aska_physical_to_moissanite_links_added"] >= 1, 'the cross-organisation link count is not what the map claims')
    require(frames["matches_weft_frame_layout"] and frames["gate_from_frame"]["design point"] == "ok", "the plant frame does not match Weft's layout, or the design point does not pass the gate")
    require(not unit["loop_closed"], "the loop is reported closed; check data/unit.json before believing it")
    require(not check or all(controls.values()), [k for k, v in controls.items() if not v])

    overhead_cut = (ts["PUE_conventional"] - ts["PUE_funi_frame"]) / (ts["PUE_conventional"] - 1.0) * 100.0
    data_files = ["pins.json", "graph.json", "sources.json", "unit.json", "upstream/MANIFEST.json"]
    cert = {
        "repository": "aska-physical/optifab", "version": VERSION,
        "inputs": {
            "vendored": {f["file"]: f["sha256"] for f in inp["manifest"]["files"]},
            "data": {f: sha256_bytes((DATA / f).read_bytes()) for f in data_files},
            "pinned_repositories": len(inp["sources"]["repos"]),
            "pinned_lines": sum(1 for p in pins.values() if p["kind"] == "line"),
        },
        "symbolic_theorems": theorems,
        "plant": env,
        "margins": {"vector": margins, **radius, "ball_in_box": ball, "sensor_with_larger_node": sensor_alternative(inp)},
        "gate": {"weft_conformance": conformance, "differential_test": differential, "worked_admissions": admissions},
        "interfaces": interfaces,
        "ledger_context": {
            "ledger_entry": "deepmind-datacenter-cooling-40pct",
            "ledger_evidence": pins["f0.ledger_dc_cooling_evidence"]["equals"],
            "ledger_result": pins["f0.ledger_dc_cooling"]["equals"],
            "funi_frame_cooling_electricity_cut_pct": ts["cooling_electricity_reduction_pct"],
            "funi_frame_pue_overhead_cut_pct": round(overhead_cut, 1),
            "funi_frame_evidence": "claimed",
        },
        "improvement_loop": evolution,
        "network_first_look": network,
        "adversarial_proposer": adversary,
        **recorded_runs,
        "formal": formal,
        "loop_timing": timing,
        "plant_frame": frames,
        "unit": unit,
        "graph": graph,
        "checks_that_survive_python_O": asserts,
        "must_fail_controls": controls,
        "controls_passed": f"{sum(controls.values())}/{len(controls)}",
    }
    return (cert, ledgers) if with_ledger else cert


# --------------------------------------------------------------------------- upstream re-check
def repo_dir(root: Path, repo: str) -> Path:
    owner, name = repo.split("/")
    for cand in (root / owner / name, root / owner.lower() / name):
        if cand.is_dir():
            return cand
    raise SystemExit(f"ERROR: no clone of {repo} under {root} (expected {root / owner / name})")


def all_cites(pins_doc: dict, graph: dict) -> list[dict]:
    cites = [p for p in pins_doc["pins"]]
    cites += [e["cite"] for e in graph["edges"]]
    cites += [n["status_cite"] for n in graph["nodes"] if n.get("status_cite")]
    return cites


def resolve_pointer(doc, pointer):
    for step in pointer:
        if isinstance(step, dict):
            doc = next(item for item in doc if all(item.get(k) == v for k, v in step.items()))
        else:
            doc = doc[step]
    return doc


def upstream_check(root: Path, repin: bool) -> int:
    pins_doc, graph = read_json(DATA / "pins.json"), read_json(DATA / "graph.json")
    sources = read_json(DATA / "sources.json") if (DATA / "sources.json").exists() else {"schema": "optifab-sources/1", "repos": {}}
    problems: list[str] = []
    seen: dict[str, dict] = {}
    for c in all_cites(pins_doc, graph):
        base = repo_dir(root, c["repo"])
        raw = (base / c["path"]).read_bytes()
        digest = sha256_bytes(raw)
        entry = seen.setdefault(c["repo"], {"commit": subprocess.run(
            ["git", "-C", str(base), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip(),
            "files": {}})
        entry["files"][c["path"]] = digest
        if c.get("kind") == "json":
            if resolve_pointer(json.loads(raw.decode("utf-8")), c["pointer"]) != c["equals"]:
                problems.append(f"{c['repo']}:{c['path']} value at pointer changed ({c['id']})")
            continue
        lines = raw.decode("utf-8").splitlines()
        hits = [i + 1 for i, text in enumerate(lines) if c["find"] in text]
        if not hits:
            problems.append(f"{c['repo']}:{c['path']} no longer contains: {c['find'][:70]}")
        elif repin:
            c["line"] = hits[0]
        elif c["line"] not in hits:
            problems.append(f"{c['repo']}:{c['path']} line {c['line']} moved to {hits[0]}")
        if not repin and sources["repos"].get(c["repo"], {}).get("files", {}).get(c["path"]) != digest:
            problems.append(f"{c['repo']}:{c['path']} content differs from the pinned hash")
    def head(base: Path) -> str:
        return subprocess.run(["git", "-C", str(base), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()

    for s in pins_doc.get("searches", []):
        pattern, hits = re.compile(s["pattern"]), 0
        for repo in s["repos"]:
            base = repo_dir(root, repo)
            seen.setdefault(repo, {"commit": head(base), "files": {}})  # a search is pinned to a commit too
            for path in sorted(base.rglob("*")):
                if ".git" in path.parts[len(base.parts):] or not path.is_file() or path.stat().st_size > 2_000_000:
                    continue
                try:
                    hits += len(pattern.findall(path.read_text(encoding="utf-8")))
                except (UnicodeDecodeError, OSError):
                    continue
        if hits != s["expect_hits"]:
            problems.append(f"search {s['id']}: {hits} hits, expected {s['expect_hits']}")
    manifest = read_json(DATA / "upstream" / "MANIFEST.json")
    for item in manifest["files"]:
        base = repo_dir(root, item["repo"])
        if sha256_bytes((base / item["path"]).read_bytes()) != item["sha256"]:
            problems.append(f"vendored copy of {item['repo']}:{item['path']} differs from the clone")
        seen.setdefault(item["repo"], {"commit": subprocess.run(
            ["git", "-C", str(base), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip(),
            "files": {}})["files"][item["path"]] = item["sha256"]
    if problems:
        print("\n".join("UPSTREAM: " + p for p in problems), file=sys.stderr)
        return 1
    if repin:
        sources = {"schema": "optifab-sources/1",
                   "repos": {r: {"commit": seen[r]["commit"], "files": dict(sorted(seen[r]["files"].items()))}
                             for r in sorted(seen, key=str.lower)}}
        for path, doc in ((DATA / "pins.json", pins_doc), (DATA / "graph.json", graph), (DATA / "sources.json", sources)):
            path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[REPIN] {len(seen)} repositories, {sum(len(v['files']) for v in seen.values())} files pinned")
        return 0
    moved = [r for r in seen if sources["repos"][r]["commit"] != seen[r]["commit"]]
    note = f" ({len(moved)} clones are at a later commit; the cited files are unchanged)" if moved else ""
    print(f"[UPSTREAM] {len(all_cites(pins_doc, graph))} citations and {len(pins_doc.get('searches', []))} searches hold against {root}{note}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true", help="rewrite results/certificate.json")
    ap.add_argument("--upstream", type=Path, help="root holding clones as <owner>/<repo>")
    ap.add_argument("--repin", action="store_true", help="with --upstream: refresh commits, hashes and line numbers")
    ap.add_argument("--formal", action="store_true",
                    help="rebuild the Lean proofs, run the comparator and the differential tests, replay the ledger "
                         "in Lean and rewrite results/formal.json (needs elan and bubblewrap)")
    args = ap.parse_args()
    if args.upstream:
        status = upstream_check(args.upstream.resolve(), args.repin)
        if status or args.repin:
            return status
    if args.formal:
        if run_formal(build_certificate(with_ledger=True, check=False)[1]):
            return 1
    cert, ledgers = build_certificate(with_ledger=True)
    ledger = ledgers["seeded_search"]
    if args.write:
        CERT_PATH.parent.mkdir(parents=True, exist_ok=True)
        CERT_PATH.write_text(json.dumps(cert, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        LEDGER_PATH.write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        for key, (_, ledger_file) in RECORDED_RUNS.items():
            if key in ledgers:
                (ROOT / "results" / ledger_file).write_text(json.dumps(ledgers[key], indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if not CERT_PATH.exists() or read_json(CERT_PATH) != cert:
        print("ERROR: results/certificate.json does not match verify.py. Run with --write after a deliberate change.", file=sys.stderr)
        return 1
    if not LEDGER_PATH.exists() or read_json(LEDGER_PATH) != ledger:
        print("ERROR: results/ledger.json does not match the loop. Run with --write after a deliberate change.", file=sys.stderr)
        return 1
    for key, (run_file, ledger_file) in RECORDED_RUNS.items():
        path = ROOT / "results" / ledger_file
        if key in ledgers and (not path.exists() or read_json(path) != ledgers[key]):
            print(f"ERROR: results/{ledger_file} does not match results/{run_file}. Run with --write.", file=sys.stderr)
            return 1
    g, m, p = cert["graph"], cert["margins"], cert["plant"]
    print(f"[PASS] optifab v{VERSION}: {cert['controls_passed']} controls, "
          f"Weft vectors {cert['gate']['weft_conformance']['passed']}/{cert['gate']['weft_conformance']['weight_update_vectors']}, "
          f"plant radius {m['plant_radius']} ({m['binding_limit_state']}), "
          f"differential test {cert['gate']['differential_test']['cases']} cases, "
          f"extra IT {p['substation']['extra_it_if_all_overhead_scales_MW']} to {p['substation']['extra_it_if_auxiliaries_are_fixed_MW']} MW, "
          f"recooling limit {p['second_law']['max_recooling_C_at_chilled_18C']} C, "
          f"lineage depth {g['optifab_lineage_depth']} of {g['lineage_depth_bound']}, "
          f"loop {cert['improvement_loop']['admitted']} changes admitted of {cert['improvement_loop']['decisions']} proposed, "
          f"recorded proposer {cert['recorded_proposer']['admitted']} of {cert['recorded_proposer']['proposals']}, "
          f"adversary held to the envelope over {cert['adversarial_proposer']['proposals']} proposals, "
          f"Lean replay {cert['formal']['replay']['decisions']} decisions {cert['formal']['replay']['mismatches']} mismatches, "
          f"unit {cert['unit']['repositories_placed']} repositories placed, "
          f"{cert['unit']['loop_interfaces_by_status'].get('checked', 0)} of {cert['unit']['loop_interfaces']} interfaces checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
