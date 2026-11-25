"""The exact plant gate and plant model in Python: the original the Lean code is tested against.

Integers only. `verify.py` at the repository root uses these same functions
to compute every margin and decide every step of the improvement loop, and
then replays the recorded decisions through the Lean executable.
"""

GENES = ("pcm_kwh", "capture_ppm", "wall_u_mw", "floor_kw", "shed_ppm")
PLANT = ("p_it_w", "cop_ppm", "ua_roof_mw_k", "wall_area_m2", "dt_mk", "other_w", "passive_w", "aux_w",
         "loop_cop_milli")
SCENARIO = ("outage_min", "outages_per_year", "low_demand_fraction_ppm", "low_demand_hours", "hours_per_year")
TOP = 10_000_000  # what a margin reads when its capacity is not positive, or its ratio is above ten


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


def pos_diff(b, c):
    return c - b if b < c else 0


def pos_dist_sq(base, cand):
    return sum(pos_diff(b, c) * pos_diff(b, c) for b, c in zip(base, cand))


def no_new_excess(limit, base, cand):
    return all(c <= max(b, limit) for b, c in zip(base, cand))


def gate_asymmetric(limit, base, cand, budget, cost):
    """Asymmetric upward gate with strict Lyapunov out-of-limit recovery."""
    if cost <= 0:
        return "cost", budget
    if budget < cost:
        return "budget", budget
    if len(base) != len(cand) or not base:
        return "shape", budget
    r = headroom(limit, base)
    if r < 0:
        if r < headroom(limit, cand) and no_new_excess(limit, base, cand):
            return "okRecovery", budget - cost
        return "noImprovement", budget
    if r * r < pos_dist_sq(base, cand):
        return "distance", budget
    return "ok", budget - cost


def evolve_asymmetric(limit, state, cand, cost):
    """One generation under the asymmetric gate."""
    base, budget = state
    verdict, remaining = gate_asymmetric(limit, base, cand, budget, cost)
    return ((cand, remaining) if verdict in ("ok", "okRecovery") else state), verdict


def asym_line(limit, budget, cost, base, cand):
    """One asymmetric-gate input line for the Lean executable."""
    return f"a {limit} {budget} {cost} ; {' '.join(map(str, base))} ; {' '.join(map(str, cand))}"


def asym_expected(limit, budget, cost, base, cand):
    verdict, remaining = gate_asymmetric(limit, base, cand, budget, cost)
    return f"{verdict} {remaining}"


def line(mode, x, budget, cost, base, cand):
    """One input line for the Lean executable."""
    return f"{mode} {x} {budget} {cost} ; {' '.join(map(str, base))} ; {' '.join(map(str, cand))}"


# ---------------------------------------------------------------- the plant model and the loop over designs
def ceil_div(a, b):
    return (a + b - 1) // b


def ppm(num, den):
    """Demand over capacity in parts per million, rounded up."""
    return TOP if den <= 0 else min(TOP, ceil_div(1_000_000 * num, den))


def q_fix(p, g):
    return (p["ua_roof_mw_k"] + g["wall_u_mw"] * p["wall_area_m2"]) * p["dt_mk"] + p["other_w"] * 1_000_000


def drive_num(p, g):
    return ((1_000_000 - g["capture_ppm"]) * (p["p_it_w"] * 1_000_000) + 1_000_000 * q_fix(p, g)) * 1_000_000


def drive_den(p, g):
    return p["cop_ppm"] * g["capture_ppm"] * (p["p_it_w"] * 1_000_000)


def cool_gain(p, g):
    return (1_000_000 + p["cop_ppm"]) * g["capture_ppm"] - 1_000_000_000_000


def floor_num(p, g):
    return q_fix(p, g) * 1000


def outage_num(p, sc, g):
    return (p["p_it_w"] * (1_000_000 - g["shed_ppm"]) + q_fix(p, g)) * sc["outage_min"]


def outage_den(g):
    return 60_000_000_000 * g["pcm_kwh"]


def moving_margins(p, sc, g):
    gain = cool_gain(p, g)
    floor = TOP if gain <= 0 or g["floor_kw"] <= 0 else ppm(floor_num(p, g), gain * g["floor_kw"])
    return [ppm(drive_num(p, g), drive_den(p, g)), floor, ppm(outage_num(p, sc, g), outage_den(g))]


def margins(p, sc, g):
    return list(p["fixed"]) + moving_margins(p, sc, g)


def utility(p, x):
    return x * p["loop_cop_milli"] + (x - p["passive_w"] * 1_000_000) * 1000 \
        + (p["aux_w"] + p["other_w"]) * 1_000_000 * p["loop_cop_milli"]


def objective(p, sc, g):
    full = p["p_it_w"] * 1_000_000
    low = sc["low_demand_fraction_ppm"] * p["p_it_w"]
    it_low = max(low, g["floor_kw"] * 1_000_000_000)
    shed_p = g["shed_ppm"] * p["p_it_w"]
    t_full = (sc["hours_per_year"] - sc["low_demand_hours"]) * 60
    t_low = sc["low_demand_hours"] * 60
    t_out = sc["outage_min"] * sc["outages_per_year"]
    useful = full * t_full + low * t_low - shed_p * t_out
    used = utility(p, full) * t_full + utility(p, it_low) * t_low \
        - (utility(p, full) - utility(p, full - shed_p)) * t_out
    return 0 if used <= 0 else (1_000_000 * useful * p["loop_cop_milli"]) // used


def in_bounds(lo, hi, g):
    return all(lo[k] <= g[k] <= hi[k] for k in GENES)


def well_formed_plant(p, sc):
    lo, hi = p["lo"], p["hi"]
    return (
        p["p_it_w"] > 0 and p["cop_ppm"] > 0 and p["ua_roof_mw_k"] >= 0
        and p["wall_area_m2"] >= 0 and p["dt_mk"] >= 0 and p["other_w"] >= 0
        and p["passive_w"] >= 0 and p["aux_w"] >= 0 and p["loop_cop_milli"] > 0
        and lo["pcm_kwh"] > 0 and lo["pcm_kwh"] <= hi["pcm_kwh"]
        and 0 <= lo["capture_ppm"] <= hi["capture_ppm"] <= 1_000_000
        and 0 <= lo["wall_u_mw"] <= hi["wall_u_mw"]
        and 0 <= lo["floor_kw"] <= hi["floor_kw"]
        and 0 <= lo["shed_ppm"] <= hi["shed_ppm"] <= 1_000_000
        and sc["outage_min"] > 0 and sc["outages_per_year"] >= 0
        and 0 <= sc["low_demand_fraction_ppm"] <= 1_000_000
        and 0 <= sc["low_demand_hours"] <= sc["hours_per_year"]
        and sc["hours_per_year"] > 0
    )


def well_formed_genome(g):
    return (
        g["pcm_kwh"] > 0
        and 0 <= g["capture_ppm"] <= 1_000_000
        and g["wall_u_mw"] >= 0
        and g["floor_kw"] > 0
        and 0 <= g["shed_ppm"] <= 1_000_000
    )


def well_formed(p, sc, g):
    return well_formed_plant(p, sc) and well_formed_genome(g)


def well_formed_line(p, sc, g):
    """One well-formedness check line for the Lean executable."""
    return " ; ".join([
        "w",
        " ".join(str(p[k]) for k in PLANT),
        " ".join(str(sc[k]) for k in SCENARIO),
        _genes(p["lo"]),
        _genes(p["hi"]),
        _genes(g),
    ])


def well_formed_expected(p, sc, g):
    return "ok" if well_formed(p, sc, g) else "malformed"


def lex_improves(p, sc, limit, held, cand):
    o_held, o_cand = objective(p, sc, held), objective(p, sc, cand)
    if o_cand > o_held:
        return True
    if o_cand == o_held:
        return headroom(limit, margins(p, sc, cand)) > headroom(limit, margins(p, sc, held))
    return False


def design_step(p, sc, limit, state, cand):
    """One generation over designs. Returns the new state and the verdict."""
    held, budget = state
    base = margins(p, sc, held)
    cand_m = margins(p, sc, cand)
    verdict, remaining = gate(base, cand_m, headroom(limit, base), budget, 1)
    if all(cand[k] == held[k] for k in GENES):
        name = "same"
    elif not in_bounds(p["lo"], p["hi"], cand):
        name = "bounds"
    elif verdict != "ok":
        name = verdict
    else:
        o_held, o_cand = objective(p, sc, held), objective(p, sc, cand)
        if o_cand < o_held:
            name = "worse"
        elif o_cand == o_held and headroom(limit, cand_m) <= headroom(limit, base):
            name = "headroom"
        else:
            name = "ok"
    return ((cand, remaining) if name == "ok" else state), name


def _genes(g):
    return " ".join(str(g[k]) for k in GENES)


def design_line(limit, budget, p, sc, held, cand):
    """One input line for the Lean executable: a proposed design."""
    return " ; ".join([f"g {limit} {budget}", " ".join(str(p[k]) for k in PLANT),
                       " ".join(str(sc[k]) for k in SCENARIO), _genes(p["lo"]), _genes(p["hi"]),
                       " ".join(map(str, p["fixed"])), _genes(held), _genes(cand)])


def design_expected(limit, budget, p, sc, held, cand):
    """What the Lean executable must print for that line."""
    (_, after), name = design_step(p, sc, limit, (held, budget), cand)
    return (f"{name} {after} {objective(p, sc, held)} {objective(p, sc, cand)} ; "
            + " ".join(map(str, margins(p, sc, cand))))


def run_designs(p, sc, limit, state, cands):
    """A whole run: every proposed design in turn. Returns the final state and the number taken up."""
    taken = 0
    for cand in cands:
        state, name = design_step(p, sc, limit, state, cand)
        taken += name == "ok"
    return state, taken


def loop_line(limit, budget, p, sc, start, cands):
    """One input line for the Lean executable: a whole run through `loop` and `changes`."""
    return " ; ".join([f"l {limit} {budget}", " ".join(str(p[k]) for k in PLANT),
                       " ".join(str(sc[k]) for k in SCENARIO), _genes(p["lo"]), _genes(p["hi"]),
                       " ".join(map(str, p["fixed"])), _genes(start)] + [_genes(c) for c in cands])


def loop_expected(limit, budget, p, sc, start, cands):
    """What the Lean executable must print for that line: final design, budget left, designs taken up."""
    (held, left), taken = run_designs(p, sc, limit, (start, budget), cands)
    return f"{_genes(held)} {left} {taken}"
