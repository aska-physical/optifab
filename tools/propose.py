#!/usr/bin/env python3
"""The proposer's side of the improvement loop, as a command line.

Anything can propose: a person, a model, a script. It sees the design held, its margins, the objective
and the budget, and it answers with new values for one or more genes and a sentence saying why. The
step function decides (formal/PlantGate.lean, `step`), and the proposal and its reason are appended to
the run file. The run file is the whole state: every call replays it from the start.

    python3 tools/propose.py RUN.json show
    python3 tools/propose.py RUN.json try pcm_kwh=2600 shed_ppm=250000 --why "more store, so shed less"
    python3 tools/propose.py RUN.json new --budget 64 --turns 40 --proposer "who or what proposes"

`verify.py` replays the committed run file and checks that it gives the committed ledger.

The rules printed by `show` are reworded after each pair of recorded runs, from what the proposers said was
unclear. After the runs against v0.3.0: whole numbers, a refusal using a turn, the verdict words, and equal
objectives being allowed. After the runs against v0.3.1: that a margin may reach the limit, and that a refused
proposal still prints the margins and the objective it would have had. Each pair of runs saw the wording
before its own changes.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import loop  # noqa: E402
import verify  # noqa: E402

UNITS = {"pcm_kwh": "thermal store, kWh of heat", "capture_ppm": "share of IT heat captured in liquid, ppm",
         "wall_u_mw": "wall U-value, mW/m2K", "floor_kw": "scheduler's load floor, kW",
         "shed_ppm": "share of load shed in a cooling outage, ppm"}


def plant() -> dict:
    inp = verify.load_inputs()
    env = verify.plant_envelope(inp)
    return verify.loop_plant(inp, env, verify.margin_vector(inp))


def show(run: dict, pl: dict) -> str:
    ledger = loop.run_proposals(pl, run["start"], run["budget"], run["proposals"])
    held = ledger["final_genome"]
    m = loop.model(held, pl)
    room = loop.oracle.headroom(loop.LIMIT, m["vector"])
    out = ["THE LOOP", "",
           "You hold one design of a data-centre campus and may propose another. Gene values are whole numbers.",
           "A proposal is taken up, with the verdict `ok`, when:",
           "  0. it differs from the design held (if not, the verdict is `same`);",
           "  1. every gene is within its bounds (if not, the verdict is `bounds`);",
           "  2. the margin vector moves no farther than the radius, as a straight-line distance over all",
           "     margins (if not, `distance`). The radius is the headroom of the design held: the smallest gap",
           f"     between any of its margins and the limit of {loop.LIMIT:,};",
           "  3. the objective, in whole parts per million, is not lower (if it is, `worse`). Equal is allowed.",
           "A proposal that is taken up costs 1 from the budget and becomes the design held. A refused one",
           "costs nothing from the budget, but it does use a turn. With no budget left the verdict is `budget`.",
           "Margins are demand over capacity in parts per million, rounded up: lower is safer. A margin may",
           f"reach {loop.LIMIT:,} and no more. A refused proposal still prints the margins and the objective it",
           "would have had.",
           "", "DESIGN HELD", ""]
    for k in loop.oracle.GENES:
        kind = "hardware" if k in loop.HARDWARE else "software"
        out.append(f"  {k:12} = {held[k]:>8}   bounds {pl['lo'][k]} to {pl['hi'][k]}   {kind}: {UNITS[k]}")
    out += ["", "MARGINS (ppm of limit)", ""]
    for name, value in m["margins"].items():
        moves = "  moves with the genes" if name in loop.MOVING else ""
        out.append(f"  {name:36} {value:>9}{moves}")
    out += ["", f"radius now      {room}", f"objective       {m['eta_ppm']} ppm (useful IT energy over utility energy)",
            f"budget left     {ledger['final_budget']} of {run['budget']} changes",
            f"turns left      {run['turns'] - len(run['proposals'])} of {run['turns']} proposals", ""]
    if ledger["entries"]:
        out += ["DECISIONS SO FAR", ""]
        for e in ledger["entries"]:
            dist = math.isqrt(loop.oracle.dist_sq(e["base_ppm"], e["cand_ppm"]))
            sets = " ".join(f"{k}={v}" for k, v in e["set"].items())
            out.append(f"  {e['turn']:>2}  {e['verdict']:8}  {sets:44}  moved {dist} of radius {e['radius_ppm']}, "
                       f"objective {e['eta_before_ppm']} -> {e['eta_after_ppm']}")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    ap.add_argument("command", choices=["show", "try", "new"])
    ap.add_argument("sets", nargs="*", help="GENE=VALUE, one or more")
    ap.add_argument("--why", default="")
    ap.add_argument("--budget", type=int, default=verify.LOOP_BUDGET)
    ap.add_argument("--turns", type=int, default=40)
    ap.add_argument("--proposer", default="")
    ap.add_argument("--lessons", default="", help="with new: a file of lessons the proposer was given, relative to the repository")
    args = ap.parse_args()
    pl = plant()

    if args.command == "new":
        if args.run.exists():
            print(f"{args.run} exists; a run is never overwritten", file=sys.stderr)
            return 2
        run = {"schema": "optifab-proposals/1", "proposer": args.proposer, "budget": args.budget, "turns": args.turns,
               "start": loop.genes(verify.LOOP_START), "proposals": []}
        if args.lessons:
            run["lessons_file"] = args.lessons
        args.run.write_text(json.dumps(run, indent=1) + "\n", encoding="utf-8")
        print(show(run, pl))
        return 0

    run = json.loads(args.run.read_text(encoding="utf-8"))
    if args.command == "try":
        if len(run["proposals"]) >= run["turns"]:
            print("no turns left", file=sys.stderr)
            return 2
        try:
            sets = {k: int(v) for k, v in (item.split("=", 1) for item in args.sets)}
        except ValueError:
            print("each proposal is GENE=WHOLE NUMBER", file=sys.stderr)
            return 2
        unknown = sorted(set(sets) - set(loop.oracle.GENES))
        if unknown or not sets or not args.why.strip():
            print(f"unknown genes {unknown}" if unknown else "a proposal needs at least one GENE=VALUE and a --why",
                  file=sys.stderr)
            return 2
        run["proposals"].append({"set": sets, "why": args.why.strip()})
        args.run.write_text(json.dumps(run, indent=1) + "\n", encoding="utf-8")
        last = loop.run_proposals(pl, run["start"], run["budget"], run["proposals"])["entries"][-1]
        print(f"VERDICT: {last['verdict']}" + ("" if last["verdict"] == "ok" else "  (nothing changed)"))
        print("margins the proposal would give: "
              + ", ".join(f"{n} {v}" for n, v in zip(loop.MOVING, last["cand_ppm"][-len(loop.MOVING):])))
        print()
    print(show(run, pl))
    return 0


if __name__ == "__main__":
    sys.exit(main())
