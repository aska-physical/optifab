#!/usr/bin/env python3
"""Differential tests: the Lean `plantgate` executable against the oracle.

The oracle is the exact Python gate and plant model in `tests/oracle.py`,
the original the Lean code stands in for. Gate inputs are edge cases, random
cases from a recorded seed, and mutations that put a candidate exactly on
the radius, one unit inside it and one unit outside it, and a cost exactly
at, just under and just over the budget. Design inputs are whole proposed
designs, run through the model, the bounds, the gate and the objective:
designs near the reference plant, designs with a gene exactly on a bound or
a margin exactly on its limit, and designs made of arbitrary integers. Loop
inputs are whole runs, a start design and up to twelve proposals, which go
through the proved `loop` and `changes`. Run from anywhere:

    python3 tests/run_tests.py [--seed N] [--count N] [--designs N] [--loops N]

It builds the executable if it is missing, writes `tests/TEST-RESULTS.md`,
and exits non-zero if any input disagrees.
"""

import argparse
import platform
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import oracle  # noqa: E402

EXE = ROOT / ".lake" / "build" / "bin" / "plantgate"
RESULTS = ROOT / "tests" / "TEST-RESULTS.md"
TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (20, 21, 29)]


def expected(case):
    mode, x, budget, cost, base, cand = case
    radius = oracle.headroom(x, base) if mode == "h" else x
    verdict, remaining = oracle.gate(base, cand, radius, budget, cost)
    return f"{verdict} {remaining}"


# A plant close to the reference campus. The tests perturb it; the real one is pinned by verify.py.
PLANT = dict(p_it_w=10_000_000, cop_ppm=620_000, ua_roof_mw_k=308_500, wall_area_m2=2476, dt_mk=20_000,
             other_w=200_000, passive_w=377_600, aux_w=195_000, loop_cop_milli=28_000,
             fixed=[179100, 563000, 387879, 588180, 176100, 801052, 616000, 607511, 300275, 496948, 769564],
             lo=dict(pcm_kwh=500, capture_ppm=620_000, wall_u_mw=100, floor_kw=0, shed_ppm=0),
             hi=dict(pcm_kwh=5000, capture_ppm=950_000, wall_u_mw=2400, floor_kw=10_000, shed_ppm=1_000_000))
YEAR = dict(outage_min=20, outages_per_year=12, low_demand_fraction_ppm=30_000, low_demand_hours=2000,
            hours_per_year=8760)
NUDGE = dict(pcm_kwh=100, capture_ppm=5000, wall_u_mw=4, floor_kw=20, shed_ppm=25_000)


def design_inputs(seed, count):
    """Proposed designs: near the reference plant, on its edges, and arbitrary integers.
    Returns the cases and how many sit on an edge."""
    rng = random.Random(seed + 1)
    cases, edges = [], 0

    def push(limit, budget, plant, year, held, cand, edge=False):
        nonlocal edges
        if len(cases) < count:
            cases.append((limit, budget, plant, year, held, cand))
            edges += edge

    def signed(bits):
        return rng.getrandbits(bits) - (1 << (bits - 1))

    while len(cases) < count:
        budget = rng.choice([0, 1, 2, 64])
        limit = rng.choice([1_000_000, 1_000_000, 950_000])
        if rng.random() < 0.7:
            plant = dict(PLANT)
            if rng.random() < 0.3:  # another plant of the same kind
                plant["cop_ppm"] = rng.randint(400_000, 900_000)
                plant["other_w"] = rng.randint(0, 600_000)
                plant["fixed"] = [rng.randint(0, 1_050_000) for _ in range(rng.randint(0, 12))]
            lo, hi = plant["lo"], plant["hi"]
            held = {k: rng.randint(lo[k], hi[k]) for k in oracle.GENES}
            if rng.random() < 0.6:  # a design that is likely to be within its limits
                held.update(pcm_kwh=rng.randint(2400, 5000), capture_ppm=rng.randint(800_000, 950_000),
                            floor_kw=rng.randint(450, 900), shed_ppm=rng.randint(0, 400_000))
            gene = rng.choice(oracle.GENES)
            cand = dict(held)
            cand[gene] += rng.choice([1, -1]) * rng.choice([1, NUDGE[gene], 8 * NUDGE[gene]])
            push(limit, budget, plant, YEAR, held, cand)
            for edge in (lo[gene] - 1, lo[gene], hi[gene], hi[gene] + 1):  # a gene on and past a bound
                push(limit, budget, plant, YEAR, held, dict(held, **{gene: edge}), True)
            gain = oracle.cool_gain(plant, held)
            if gain > 0:  # the scheduler's floor exactly at, just above and just below the plant's
                at = oracle.ceil_div(oracle.floor_num(plant, held), gain)
                for f in (at - 1, at, at + 1):
                    push(limit, budget, plant, YEAR, held, dict(held, floor_kw=f), True)
            need = oracle.ceil_div(oracle.outage_num(plant, YEAR, held), 60_000_000_000)  # does not move with the store
            for store in (need - 1, need, need + 1):  # the store exactly at, above and below one outage
                push(limit, budget, plant, YEAR, held, dict(held, pcm_kwh=store), True)
            push(limit, budget, plant, YEAR, held, dict(held), True)  # no change at all
        else:  # arbitrary integers: every function is total
            bits = rng.choice([3, 12, 24, 45])
            plant = {k: signed(bits) for k in oracle.PLANT}
            plant["fixed"] = [signed(bits) for _ in range(rng.randint(0, 4))]
            plant["lo"] = {k: signed(bits) for k in oracle.GENES}
            plant["hi"] = {k: plant["lo"][k] + rng.getrandbits(bits) for k in oracle.GENES}
            year = {k: signed(bits) for k in oracle.SCENARIO}
            held = {k: signed(bits) for k in oracle.GENES}
            cand = {k: held[k] + rng.choice([0, 0, 1, -1, signed(bits // 2 + 1)]) for k in oracle.GENES}
            push(rng.choice([limit, signed(bits)]), rng.choice([budget, signed(bits)]), plant, year, held, cand)
    return cases, edges


def loop_inputs(seed, count):
    """Whole runs: a start design and up to twelve proposals, near the reference plant or arbitrary."""
    rng = random.Random(seed + 2)
    cases = []
    while len(cases) < count:
        budget = rng.choice([0, 1, 2, 3, 64])
        limit = rng.choice([1_000_000, 1_000_000, 950_000])
        if rng.random() < 0.85:
            plant, year = dict(PLANT), YEAR
            start = dict(pcm_kwh=rng.randint(2400, 5000), capture_ppm=rng.randint(800_000, 950_000),
                         wall_u_mw=rng.randint(100, 400), floor_kw=rng.randint(450, 900), shed_ppm=rng.randint(0, 400_000))
            cands, held = [], dict(start)
            for _ in range(rng.randint(0, 12)):
                cand = dict(held)
                for gene in rng.sample(oracle.GENES, rng.randint(0, 3)):  # none at all is a proposal too
                    cand[gene] += rng.choice([1, -1]) * rng.choice([1, NUDGE[gene], 3 * NUDGE[gene]])
                cands.append(cand)
                if rng.random() < 0.7:
                    held = cand  # the proposer assumes it was taken up, which may be wrong
        else:
            bits = rng.choice([3, 12, 24])
            signed = lambda: rng.getrandbits(bits) - (1 << (bits - 1))
            plant = {k: signed() for k in oracle.PLANT}
            plant["fixed"] = [signed() for _ in range(rng.randint(0, 3))]
            plant["lo"] = {k: signed() for k in oracle.GENES}
            plant["hi"] = {k: plant["lo"][k] + rng.getrandbits(bits) for k in oracle.GENES}
            year = {k: signed() for k in oracle.SCENARIO}
            start = {k: signed() for k in oracle.GENES}
            cands = [{k: start[k] + rng.choice([0, 1, -1, signed()]) for k in oracle.GENES} for _ in range(rng.randint(0, 6))]
        cases.append((limit, budget, plant, year, start, cands))
    return cases


def inputs(seed, count):
    """Edge cases, then random cases, each followed by its mutations.
    Returns the cases and how many of them are mutations."""
    cases = [
        ("r", 0, 1, 1, [], []), ("r", 5, 1, 1, [0], []), ("r", 5, 1, 1, [0, 0], [0]),
        ("r", 0, 1, 1, [7], [7]), ("r", -1, 1, 1, [7], [7]), ("r", 5, 0, 1, [0], [0]),
        ("r", 5, 1, 0, [0], [0]), ("r", 5, 1, -1, [0], [0]), ("r", 5, -3, -5, [0], [0]),
        ("h", 1000000, 10, 1, [], []), ("h", 1000000, 10, 1, [1000000], [1000000]),
        ("h", 1000000, 10, 1, [1000001], [1000001]), ("h", 1000000, 10, 1, [801052, 769564], [1000000, 769564]),
        ("h", 1000000, 10, 1, [801052, 769564], [1000001, 769564]),
        ("r", 2**100, 2**70, 2**69, [2**90, -2**90], [2**90 + 2**99, -2**90]),
    ]
    rng = random.Random(seed)
    mutated = 0

    def push(case, is_mutation=False):
        nonlocal mutated
        if len(cases) < count:
            cases.append(case)
            mutated += is_mutation

    while len(cases) < count:
        n = rng.randint(1, 6)
        bits = rng.choice([4, 10, 20, 40, 90])
        base = [rng.getrandbits(bits) - (1 << (bits - 1)) for _ in range(n)]
        cand = [b + rng.randint(-(1 << (bits // 2)), 1 << (bits // 2)) for b in base]
        budget = rng.choice([0, 1, 2, 64, 2500000, rng.getrandbits(bits)])
        cost = rng.choice([1, 1, 1, budget, budget + 1, max(budget - 1, 0), 0, -1])
        if rng.random() < 0.5:
            radius = rng.choice([0, 1, rng.getrandbits(bits // 2 + 1), -1])
            push(("r", radius, budget, cost, base, cand))
            r = abs(radius) + 1
            for move in (r - 1, r, r + 1):  # one coordinate at, on and past a radius of r
                c = list(base)
                c[rng.randrange(n)] += rng.choice([1, -1]) * move
                push(("r", r, budget, cost, base, c), True)
            if n >= 2:  # two coordinates on an exact circle: a² + b² = (kc)²
                a, b, c3 = rng.choice(TRIPLES)
                k = rng.randint(1, 1 << (bits // 3 + 1))
                c = list(base)
                c[0] += a * k
                c[1] -= b * k
                for rr in (c3 * k - 1, c3 * k, c3 * k + 1):
                    push(("r", rr, budget, cost, base, c), True)
        else:
            limit = max(base) + rng.choice([-1, 0, 1, rng.getrandbits(bits // 2 + 1)])
            push(("h", limit, budget, cost, base, cand))
            room = oracle.headroom(limit, base)
            for move in (room - 1, room, room + 1):  # the tightest margin moved to, onto and past the limit
                c = list(base)
                c[base.index(max(base))] += move
                push(("h", limit, budget, cost, base, c), True)
        if rng.random() < 0.05:
            push(("r", 5, budget, cost, base, cand + [0]), True)
    return cases[:count], mutated


def split_output_lines(stdout: str) -> list[str]:
    """Split process stdout into exact lines, stripping at most one trailing newline."""
    if stdout == "":
        return []
    if stdout.endswith("\n"):
        return stdout[:-1].split("\n")
    return stdout.split("\n")


def compare_outputs(inputs_all, want, stdout):
    """Compare Lean stdout lines against expected outputs, failing on any length mismatch."""
    out = split_output_lines(stdout)
    failures = [(c, got) for c, w, got in zip(inputs_all, want, out) if got != w]
    if len(out) != len(want):
        failures.append(("output line count mismatch", f"got {len(out)} lines, expected {len(want)}"))
    return failures


def asym_inputs(seed, count):
    """Asymmetric-gate inputs: pure safety moves, OOB recovery, boundary mutations, and random cases."""
    cases = [
        (1_000_000, 10, 1, [], []),
        (1_000_000, 10, 1, [900_000], []),
        (1_000_000, 10, 0, [900_000], [800_000]),
        (1_000_000, 0, 1, [900_000], [800_000]),
        # Pure safety move larger than symmetric headroom (pcm 2500 -> 5000 kWh outage margin)
        (1_000_000, 64, 1, [801_052, 961_695], [801_052, 480_848]),
        # At exact limit (headroom = 0): pure safety move admitted, upward move refused
        (1_000_000, 64, 1, [1_000_000, 800_000], [950_000, 800_000]),
        (1_000_000, 64, 1, [1_000_000, 800_000], [1_000_001, 800_000]),
        # OOB baseline recovery (pcm = 2350 -> 2500 kWh): strict Lyapunov descent, no new excess
        (1_000_000, 64, 1, [801_052, 1_023_079], [801_052, 961_695]),
        (1_000_000, 64, 1, [801_052, 1_023_079], [801_052, 1_001_765]),
        # OOB non-improving or creating a new violation -> refused
        (1_000_000, 64, 1, [801_052, 1_023_079], [801_052, 1_023_079]),
        (1_000_000, 64, 1, [801_052, 1_023_079], [1_005_000, 961_695]),
    ]
    rng = random.Random(seed + 3)

    def push(case):
        if len(cases) < count:
            cases.append(case)

    while len(cases) < count:
        n = rng.randint(1, 6)
        bits = rng.choice([4, 12, 22, 40])
        base = [rng.getrandbits(bits) - (1 << (bits - 1)) for _ in range(n)]
        budget = rng.choice([0, 1, 2, 64, rng.getrandbits(bits)])
        cost = rng.choice([1, 1, budget, budget + 1, 0, -1])
        if rng.random() < 0.65:
            # Safe baseline
            limit = max(base) + rng.choice([0, 1, rng.getrandbits(bits // 2 + 1)])
            room = oracle.headroom(limit, base)
            cand = [b + rng.randint(-(1 << (bits // 2)), 1 << (bits // 2)) for b in base]
            push((limit, budget, cost, base, cand))
            # Large pure safety drop (way beyond room)
            safe_cand = [b - rng.randint(0, max(1, 10 * room + 100)) for b in base]
            push((limit, budget, cost, base, safe_cand))
            # One coordinate moved upward to, onto, and past room while another drops far
            for move in (room - 1, room, room + 1):
                c = list(base)
                idx = rng.randrange(n)
                c[idx] += move
                if n >= 2:
                    c[(idx + 1) % n] -= abs(move) + room + 5
                push((limit, budget, cost, base, c))
        else:
            # Out-of-limit baseline (headroom < 0)
            limit = max(base) - rng.randint(1, max(2, 1 << (bits // 2)))
            idx = base.index(max(base))
            # Valid recovery step
            c_rec = [min(b, limit) for b in base]
            c_rec[idx] = base[idx] - rng.randint(1, max(1, base[idx] - limit + 5))
            push((limit, budget, cost, base, c_rec))
            # Non-improving step
            c_same = list(base)
            push((limit, budget, cost, base, c_same))
            # Step that reduces worst excess but pushes a safe coordinate past limit
            if n >= 2:
                c_bad = list(c_rec)
                other = (idx + 1) % n
                if base[other] <= limit:
                    c_bad[other] = limit + 1
                    push((limit, budget, cost, base, c_bad))
    return cases[:count]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261117)
    ap.add_argument("--count", type=int, default=300_000)
    ap.add_argument("--designs", type=int, default=100_000)
    ap.add_argument("--loops", type=int, default=5_000)
    ap.add_argument("--asym", type=int, default=25_000)
    args = ap.parse_args()

    if not EXE.exists():
        subprocess.run(["lake", "build", "plantgate"], cwd=ROOT, check=True)

    cases, mutated = inputs(args.seed, args.count)
    designs, edges = design_inputs(args.seed, args.designs)
    loops = loop_inputs(args.seed, args.loops)
    asyms = asym_inputs(args.seed, args.asym)
    stdin = (
        "".join(oracle.line(*c) + "\n" for c in cases)
        + "".join(oracle.design_line(*d) + "\n" for d in designs)
        + "".join(oracle.loop_line(*r) + "\n" for r in loops)
        + "".join(oracle.asym_line(*a) + "\n" for a in asyms)
    )
    stdout = subprocess.run([str(EXE)], input=stdin, capture_output=True,
                            text=True, check=True).stdout
    want = (
        [expected(c) for c in cases]
        + [oracle.design_expected(*d) for d in designs]
        + [oracle.loop_expected(*r) for r in loops]
        + [oracle.asym_expected(*a) for a in asyms]
    )
    failures = compare_outputs(cases + designs + loops + asyms, want, stdout)
    verdicts, design_verdicts, asym_verdicts = {}, {}, {}
    for w in want[:len(cases)]:
        verdicts[w.split()[0]] = verdicts.get(w.split()[0], 0) + 1
    for w in want[len(cases):len(cases) + len(designs)]:
        design_verdicts[w.split()[0]] = design_verdicts.get(w.split()[0], 0) + 1
    for w in want[len(cases) + len(designs) + len(loops):]:
        asym_verdicts[w.split()[0]] = asym_verdicts.get(w.split()[0], 0) + 1
    proposals = sum(len(r[5]) for r in loops)
    taken = sum(int(w.split()[-1]) for w in want[len(cases) + len(designs):len(cases) + len(designs) + len(loops)])

    lean = subprocess.run(["lake", "env", "lean", "--version"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    lines = [
        "# Test results",
        "",
        "Written by `tests/run_tests.py`. Rerun it to check these numbers.",
        "",
        f"- Oracle: Python {platform.python_version()} exact gate and plant model in `tests/oracle.py`",
        f"- Lean: {lean}",
        f"- Seed: {args.seed}",
        f"- Inputs: {len(want)}",
        f"- Gate inputs: {len(cases)}",
        f"- Mutated: {mutated} of the gate inputs sit on, just inside or just outside a radius, a limit or a length",
        "- Verdicts: " + ", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())),
        f"- Design inputs: {len(designs)}, each a proposed design run through the model, the bounds, the gate and the objective",
        f"- Design edges: {edges} of the design inputs have a gene on or just past a bound, or a margin on or just past its limit",
        "- Design verdicts: " + ", ".join(f"{k} {v}" for k, v in sorted(design_verdicts.items())),
        f"- Loop inputs: {len(loops)}, each a whole run through `loop` and `changes`: {proposals} proposals in all, {taken} taken up",
        f"- Asymmetric gate inputs: {len(asyms)}",
        "- Asymmetric verdicts: " + ", ".join(f"{k} {v}" for k, v in sorted(asym_verdicts.items())),
        f"- Failures: {len(failures)}",
        "",
    ]
    if failures:
        lines += ["## Failures", ""]
        lines += [f"- `{c}`: Lean printed `{got}`" for c, got in failures[:50]]
        lines.append("")
    RESULTS.write_text("\n".join(lines))
    print(f"{len(want) - len(failures)}/{len(want)} inputs agree; "
          f"results in {RESULTS}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
