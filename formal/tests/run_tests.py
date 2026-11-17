#!/usr/bin/env python3
"""Differential tests: the Lean `plantgate` executable against the oracle.

The oracle is the exact Python gate in `tests/oracle.py`, the original the
Lean code stands in for. Inputs are edge cases, random cases from a recorded
seed, and mutations that put a candidate exactly on the radius, one unit
inside it and one unit outside it, and a cost exactly at, just under and
just over the budget. Run from anywhere:

    python3 tests/run_tests.py [--seed N] [--count N]

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20261117)
    ap.add_argument("--count", type=int, default=300_000)
    args = ap.parse_args()

    if not EXE.exists():
        subprocess.run(["lake", "build", "plantgate"], cwd=ROOT, check=True)

    cases, mutated = inputs(args.seed, args.count)
    stdin = "".join(oracle.line(*c) + "\n" for c in cases)
    out = subprocess.run([str(EXE)], input=stdin, capture_output=True,
                         text=True, check=True).stdout.split("\n")
    failures = [(c, got) for c, got in zip(cases, out) if got != expected(c)]
    if len(out) < len(cases):
        failures.append(("missing output", f"{len(out)} lines"))
    verdicts = {}
    for c in cases:
        v = expected(c).split()[0]
        verdicts[v] = verdicts.get(v, 0) + 1

    lean = subprocess.run(["lake", "env", "lean", "--version"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    lines = [
        "# Test results",
        "",
        "Written by `tests/run_tests.py`. Rerun it to check these numbers.",
        "",
        f"- Oracle: Python {platform.python_version()} exact gate in `tests/oracle.py`",
        f"- Lean: {lean}",
        f"- Seed: {args.seed}",
        f"- Inputs: {len(cases)}",
        f"- Mutated: {mutated} of the inputs sit on, just inside or just outside a radius, a limit or a length",
        "- Verdicts: " + ", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())),
        f"- Failures: {len(failures)}",
        "",
    ]
    if failures:
        lines += ["## Failures", ""]
        lines += [f"- `{c}`: Lean printed `{got}`" for c, got in failures[:50]]
        lines.append("")
    RESULTS.write_text("\n".join(lines))
    print(f"{len(cases) - len(failures)}/{len(cases)} inputs agree; "
          f"results in {RESULTS}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
