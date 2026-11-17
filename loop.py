#!/usr/bin/env python3
"""The improvement loop: hardware and software of the campus changed together, one gated step at a time.

A genome holds three hardware genes (thermal store size, liquid capture fraction, wall U-value), two
software genes (the scheduler's load floor and the share of load it sheds in a cooling outage) and one
gene of the proposer itself (its step scale). Each generation the proposer suggests changes, the plant
model turns each candidate into a vector of margins, and the exact gate in formal/ decides. Hardware
changes are scored by the headroom they open, software changes by the objective they gain. An admitted
candidate becomes the baseline of the next generation. Every decision goes into a hash-chained ledger.

What is proved (in Lean, formal/): no list of proposals can push a margin past its limit or overdraw
the change budget through the gate. What is not: the plant model, the objective, the proposer and this
file. The scenario is a choice made here, so the efficiency figures are illustrations, not predictions.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "formal" / "tests"))
import oracle  # noqa: E402  the exact gate, tested against the Lean executable

LIMIT = 1_000_000  # a margin of 1,000,000 ppm is exactly at its limit
RESERVE = 950_000  # the proposer's own caution; the gate does not know about it
HARDWARE = ("pcm_kwh", "capture_ppm", "wall_u_mw")
SOFTWARE = ("floor_kw", "shed_ppm")
META = ("step_ppm",)
STEP = {"pcm_kwh": 100, "capture_ppm": 5000, "wall_u_mw": 4, "floor_kw": 20, "shed_ppm": 25000}
BOUNDS = {"pcm_kwh": (500, 5000), "capture_ppm": (620000, 950000), "wall_u_mw": (100, 2400),
          "floor_kw": (0, 10000), "shed_ppm": (0, 1000000), "step_ppm": (125000, 8000000)}

# The scenario the objective is scored on. These four numbers are choices made here.
SCENARIO = {"outage_min": 20, "outages_per_year": 12, "low_demand_fraction_ppm": 30000, "low_demand_hours": 2000}


def model(genome: dict, plant: dict) -> dict:
    """Margins (ppm of limit) and the objective for one genome. `plant` holds the pinned upstream values."""
    p_kw = plant["p_it_kw"]
    alpha = genome["capture_ppm"] / 1e6
    cop = plant["cop_ads"]
    q_env_kw = (plant["ua_roof_w_k"] + genome["wall_u_mw"] / 1000.0 * plant["wall_area_m2"]) * plant["design_dt_k"] / 1000.0
    q_fix_kw = q_env_kw + plant["other_kw"]
    denom = (1.0 + cop) * alpha - 1.0
    p_min_kw = math.inf if denom <= 0 else q_fix_kw / denom
    shed = genome["shed_ppm"] / 1e6
    outage_h = SCENARIO["outage_min"] / 60.0

    def ppm(x: float) -> int:  # rounded up, so a margin is never understated
        return 10 * LIMIT if not math.isfinite(x) else min(10 * LIMIT, math.ceil(x * 1e6 - 1e-9))

    moving = {
        "sorption_drive_heat": ppm(((1.0 - alpha) * p_kw + q_fix_kw) / cop / (alpha * p_kw)),
        "load_floor": ppm(p_min_kw / genome["floor_kw"]) if genome["floor_kw"] > 0 else 10 * LIMIT,
        "outage_ride_through": ppm(p_kw * (1.0 - shed) * outage_h / genome["pcm_kwh"]),
    }
    margins = dict(plant["fixed_margins_ppm"])
    margins.update(moving)

    # Objective: useful IT energy delivered per unit of utility energy over the scenario year.
    hours, low_h = 8760.0, SCENARIO["low_demand_hours"]
    low_kw = SCENARIO["low_demand_fraction_ppm"] / 1e6 * p_kw
    it_low = max(low_kw, genome["floor_kw"])  # the scheduler fills up to its floor; the filler is not useful
    lost = shed * p_kw * outage_h * SCENARIO["outages_per_year"]
    useful = p_kw * (hours - low_h) + low_kw * low_h - lost

    def utility(it_kw: float) -> float:  # the upstream plant model: cooling loop, auxiliaries, other overhead
        return it_kw + (it_kw - plant["passive_kw"]) / plant["loop_cop"] + plant["aux_kw"] + plant["other_kw"]

    used = utility(p_kw) * (hours - low_h) + utility(it_low) * low_h - utility(shed * p_kw) * outage_h * SCENARIO["outages_per_year"]
    return {"margins": margins, "names": list(margins), "vector": list(margins.values()),
            "eta_ppm": math.floor(useful / used * 1e6), "p_min_kw": round(p_min_kw, 1)}


def digest(entry: dict) -> str:
    return hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run_loop(plant: dict, start: dict, budget: int, generations: int = 400, seed: int = 20261117) -> dict:
    """Run the loop and return the ledger. Deterministic for a given seed."""
    state = seed

    def rnd() -> float:
        nonlocal state
        state = (state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        return (state >> 11) / float(1 << 53)

    genome = dict(start)
    base = model(genome, plant)
    ledger, prev = [], "0" * 64
    head = {"start_genome": dict(genome), "start_margins_ppm": base["margins"], "start_eta_ppm": base["eta_ppm"],
            "budget": budget, "limit": LIMIT, "scenario": SCENARIO, "seed": seed}
    idle = 0
    for gen in range(generations):
        if budget <= 0 or idle >= 40:
            break
        # The proposer alternates. On even generations it tries software changes and keeps the one that
        # raises the objective most. On odd generations it tries hardware changes and keeps the one that
        # opens the most headroom without lowering the objective. Hardware makes room; software uses it.
        phase = SOFTWARE if gen % 2 == 0 else HARDWARE
        room = oracle.headroom(LIMIT, base["vector"])
        best = None
        for _ in range(6):
            gene = phase[int(rnd() * len(phase))]
            delta = (1 if rnd() < 0.5 else -1) * max(1, round(STEP[gene] * genome["step_ppm"] / 1e6))
            cand = dict(genome)
            cand[gene] = min(BOUNDS[gene][1], max(BOUNDS[gene][0], cand[gene] + delta))
            if cand[gene] == genome[gene]:
                continue
            m = model(cand, plant)
            if phase is SOFTWARE:  # the proposer keeps a reserve: it does not ask to run a margin above RESERVE
                gain = m["eta_ppm"] - base["eta_ppm"] if max(m["vector"]) <= RESERVE else 0
            else:
                gain = oracle.headroom(LIMIT, m["vector"]) - room if m["eta_ppm"] >= base["eta_ppm"] else 0
            if gain > 0 and (best is None or gain > best[4]):
                best = (cand, m, gene, cand[gene] - genome[gene], gain)
        if best is None:
            idle += 1
            genome["step_ppm"] = max(BOUNDS["step_ppm"][0], genome["step_ppm"] // 2)  # nothing better: look closer
            continue
        cand, m, gene, delta, _ = best
        radius = oracle.headroom(LIMIT, base["vector"])
        verdict, remaining = oracle.gate(base["vector"], m["vector"], radius, budget, 1)
        entry = {"generation": gen, "gene": gene, "kind": "hardware" if gene in HARDWARE else "software",
                 "delta": delta, "step_ppm": genome["step_ppm"], "base_ppm": base["vector"], "cand_ppm": m["vector"],
                 "radius_ppm": radius, "eta_before_ppm": base["eta_ppm"], "eta_after_ppm": m["eta_ppm"],
                 "budget_before": budget, "cost": 1, "verdict": verdict, "budget_after": remaining, "prev": prev}
        entry["hash"] = prev = digest(entry)
        ledger.append(entry)
        if verdict == "ok":
            step = min(BOUNDS["step_ppm"][1], genome["step_ppm"] * 2)  # it worked: reach further next time
            genome, base, budget, idle = dict(cand), m, remaining, 0
            genome["step_ppm"] = step
        else:
            idle += 1
            genome["step_ppm"] = max(BOUNDS["step_ppm"][0], genome["step_ppm"] // 2)  # refused: step back
    final = model(genome, plant)
    return {"head": head, "entries": ledger, "final_genome": genome, "final_margins_ppm": final["margins"],
            "final_eta_ppm": final["eta_ppm"], "final_budget": budget, "final_hash": prev}


def check_chain(ledger: dict) -> bool:
    prev = "0" * 64
    for e in ledger["entries"]:
        body = {k: v for k, v in e.items() if k != "hash"}
        if e["prev"] != prev or digest(body) != e["hash"]:
            return False
        prev = e["hash"]
    return prev == ledger["final_hash"]


def replay_lines(ledger: dict) -> list[str]:
    """One line per ledger decision, for the Lean executable to decide again."""
    return [oracle.line("h", ledger["head"]["limit"], e["budget_before"], e["cost"], e["base_ppm"], e["cand_ppm"])
            for e in ledger["entries"]]


def summary(ledger: dict) -> dict:
    ok = [e for e in ledger["entries"] if e["verdict"] == "ok"]
    refused: dict[str, int] = {}
    for e in ledger["entries"]:
        if e["verdict"] != "ok":
            refused[e["verdict"]] = refused.get(e["verdict"], 0) + 1
    worst = max(max(e["cand_ppm"]) for e in ok) if ok else max(ledger["head"]["start_margins_ppm"].values())
    return {
        "decisions": len(ledger["entries"]), "admitted": len(ok), "refused": dict(sorted(refused.items())),
        "admitted_hardware_changes": sum(1 for e in ok if e["kind"] == "hardware"),
        "admitted_software_changes": sum(1 for e in ok if e["kind"] == "software"),
        "budget_start": ledger["head"]["budget"], "budget_left": ledger["final_budget"],
        "eta_start_ppm": ledger["head"]["start_eta_ppm"], "eta_final_ppm": ledger["final_eta_ppm"],
        "eta_never_fell": all(e["eta_after_ppm"] >= e["eta_before_ppm"] for e in ok),
        "worst_margin_ever_admitted_ppm": worst, "every_admitted_state_within_limit": worst <= LIMIT,
        "start_genome": ledger["head"]["start_genome"], "final_genome": ledger["final_genome"],
        "largest_step_scale_ppm": max([e["step_ppm"] for e in ledger["entries"]], default=0),
        "chain_intact": check_chain(ledger), "final_hash": ledger["final_hash"],
    }
