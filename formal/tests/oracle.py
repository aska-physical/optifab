"""The exact plant gate in Python: the original the Lean gate is tested against.

Integers only. `verify.py` at the repository root uses these same functions
to decide every step of the improvement loop, and then replays the recorded
decisions through the Lean executable.
"""


def dist_sq(base, cand):
    return sum((c - b) * (c - b) for b, c in zip(base, cand))


def headroom(limit, base):
    return min(limit - b for b in base) if base else 0


def gate(base, cand, radius, budget, cost):
    """Returns (verdict, remaining budget). A refused step spends nothing."""
    if cost <= 0:
        return "cost", budget
    if budget < cost:
        return "budget", budget
    if len(base) != len(cand) or not base:
        return "shape", budget
    if radius < 0:
        return "radius", budget
    if radius * radius < dist_sq(base, cand):
        return "distance", budget
    return "ok", budget - cost


def evolve(limit, state, cand, cost):
    """One generation: an admitted candidate becomes the baseline."""
    base, budget = state
    verdict, remaining = gate(base, cand, headroom(limit, base), budget, cost)
    return ((cand, remaining) if verdict == "ok" else state), verdict


def line(mode, x, budget, cost, base, cand):
    """One input line for the Lean executable."""
    return f"{mode} {x} {budget} {cost} ; {' '.join(map(str, base))} ; {' '.join(map(str, cand))}"
