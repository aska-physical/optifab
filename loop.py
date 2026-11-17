#!/usr/bin/env python3
"""The improvement loop: hardware and software of the campus changed together, one gated step at a time.

A design holds three hardware genes (thermal store size, liquid capture fraction, wall U-value) and two
software genes (the scheduler's load floor and the share of load it sheds in a cooling outage). The
proposer adds one gene of its own, its step scale. Each generation something proposes a design. The plant
model turns it into a vector of margins and an objective, and one step function decides: the design must
lie within the bounds, pass the gate, and not lower the objective. A design that is taken up becomes the
one held. Every decision goes into a hash-chained ledger.

The model, the bounds, the gate, the objective and the step are exact integer arithmetic, written twice:
in Lean (formal/PlantGate.lean), where the properties of the loop are proved for every list of proposals,
and in Python (formal/tests/oracle.py), which this file calls and which is tested against the Lean
executable. What is not proved: that the model describes a real plant, and the proposers. The scenario
is a choice made here, so the efficiency figures are illustrations, not predictions.

Two proposers use the loop. `run_loop` is a seeded search. `run_proposals` replays a recorded list of
proposals made by anything else: a person, a model, an adversary.
"""
from __future__ import annotations

import hashlib
import json
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

MOVING = ("sorption_drive_heat", "load_floor", "outage_ride_through")  # the margins the genes move

# The scenario the objective is scored on. The first four numbers are choices made here.
SCENARIO = {"outage_min": 20, "outages_per_year": 12, "low_demand_fraction_ppm": 30000, "low_demand_hours": 2000,
            "hours_per_year": 8760}


def genes(genome: dict) -> dict:
    """The design part of a genome: the five genes the model reads."""
    return {k: genome[k] for k in oracle.GENES}


def model(genome: dict, plant: dict) -> dict:
    """Margins (ppm of limit) and the objective for one design, from the exact model."""
    vector = oracle.margins(plant, SCENARIO, genes(genome))
    names = list(plant["fixed_names"]) + list(MOVING)
    return {"margins": dict(zip(names, vector)), "names": names, "vector": vector,
            "eta_ppm": oracle.objective(plant, SCENARIO, genes(genome))}


def digest(entry: dict) -> str:
    return hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def decide(plant: dict, held: dict, budget: int, cand: dict, prev: str, **extra) -> dict:
    """One decision of the step function, as a ledger entry."""
    base, m = model(held, plant), model(cand, plant)
    (_, after), verdict = oracle.design_step(plant, SCENARIO, LIMIT, (genes(held), budget), genes(cand))
    entry = {**extra, "held": genes(held), "proposed": genes(cand), "base_ppm": base["vector"], "cand_ppm": m["vector"],
             "radius_ppm": oracle.headroom(LIMIT, base["vector"]), "eta_before_ppm": base["eta_ppm"],
             "eta_after_ppm": m["eta_ppm"], "budget_before": budget, "cost": 1, "verdict": verdict,
             "budget_after": after, "prev": prev}
    entry["hash"] = digest(entry)
    return entry


def head_of(plant: dict, start: dict, budget: int, **extra) -> dict:
    base = model(start, plant)
    return {"start_genome": dict(start), "start_margins_ppm": base["margins"], "start_eta_ppm": base["eta_ppm"],
            "budget": budget, "limit": LIMIT, "scenario": SCENARIO, "plant": plant, **extra}


def run_proposals(plant: dict, start: dict, budget: int, proposals: list[dict]) -> dict:
    """Replay a recorded list of proposals, whoever made them. Each proposal sets one or more genes."""
    genome = genes(start)
    ledger, prev = [], "0" * 64
    for turn, prop in enumerate(proposals):
        cand = dict(genome)
        cand.update({k: int(v) for k, v in prop["set"].items() if k in oracle.GENES})
        kinds = sorted({"hardware" if k in HARDWARE else "software" for k in prop["set"] if cand[k] != genome[k]})
        entry = decide(plant, genome, budget, cand, prev, turn=turn, kind="+".join(kinds) or "none",
                       set={k: cand[k] for k in prop["set"] if k in oracle.GENES})
        ledger.append(entry)
        prev = entry["hash"]
        if entry["verdict"] == "ok":
            genome, budget = cand, entry["budget_after"]
    final = model(genome, plant)
    return {"head": head_of(plant, genes(start), budget if not ledger else ledger[0]["budget_before"]),
            "entries": ledger, "final_genome": genome, "final_margins_ppm": final["margins"],
            "final_eta_ppm": final["eta_ppm"], "final_budget": budget, "final_hash": prev}


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
    head = head_of(plant, genome, budget, seed=seed)
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
        entry = decide(plant, genome, budget, cand, prev, generation=gen, gene=gene,
                       kind="hardware" if gene in HARDWARE else "software", delta=delta, step_ppm=genome["step_ppm"])
        prev = entry["hash"]
        ledger.append(entry)
        verdict, remaining = entry["verdict"], entry["budget_after"]
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
    """One line per ledger decision, for the Lean executable to work out again from the two designs."""
    h = ledger["head"]
    return [oracle.design_line(h["limit"], e["budget_before"], h["plant"], h["scenario"], e["held"], e["proposed"])
            for e in ledger["entries"]]


def replay_expected(ledger: dict) -> list[str]:
    """What Lean must print for each line: verdict, budget left, both objectives and the proposed margins."""
    return [f"{e['verdict']} {e['budget_after']} {e['eta_before_ppm']} {e['eta_after_ppm']} ; "
            + " ".join(map(str, e["cand_ppm"])) for e in ledger["entries"]]


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
        "admitted_changes_to_both_at_once": sum(1 for e in ok if e["kind"] == "hardware+software"),
        "budget_start": ledger["head"]["budget"], "budget_left": ledger["final_budget"],
        "eta_start_ppm": ledger["head"]["start_eta_ppm"], "eta_final_ppm": ledger["final_eta_ppm"],
        "eta_never_fell": all(e["eta_after_ppm"] >= e["eta_before_ppm"] for e in ok),
        "worst_margin_ever_admitted_ppm": worst, "every_admitted_state_within_limit": worst <= LIMIT,
        "start_genome": ledger["head"]["start_genome"], "final_genome": ledger["final_genome"],
        "largest_step_scale_ppm": max([e.get("step_ppm", 0) for e in ledger["entries"]], default=0),
        "chain_intact": check_chain(ledger), "final_hash": ledger["final_hash"],
    }
