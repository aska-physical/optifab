# Specification: the plant gate

A reviewer who did not write this approves it together with `PlantGate/Spec.lean` and the page sections listed in `bar.toml`. No one has yet.

## Scope

The gate decides whether one proposed change to a plant may go ahead. It is exact: every quantity is an integer and nothing is rounded.

- A **state** is a list of margins, one per limit state of the plant. Each margin is demand over capacity in parts per million, so a margin of 1,000,000 is exactly at its limit.
- The **baseline** is the last state that was certified. The **candidate** is the state after the proposed change.
- The **radius** bounds how far the candidate may lie from the baseline, as a Euclidean distance. The gate compares squares, so it takes no square root.
- The **budget** is what may still be spent and the **cost** is what this change spends. The unit is the caller's: watt-hours of heat for a cooling outage, counted changes for a change budget.

`PlantGate.gate base cand radius budget cost` returns a verdict and the budget left.

`PlantGate.evolve limit s cand cost` applies one proposal to a pair of baseline and budget. The radius it uses is the headroom of the baseline: the smallest distance from any baseline margin to `limit`. An admitted candidate becomes the new baseline.

`PlantGate.run limit s steps` applies a list of proposals in order.

## Valid inputs and errors

Every input is valid and every function is total. The gate refuses, in this order:

| Verdict | When |
|---------|------|
| `cost` | the cost is zero or negative |
| `budget` | the cost is more than the budget |
| `shape` | the two states differ in length, or the baseline is empty |
| `radius` | the radius is negative |
| `distance` | the candidate is farther from the baseline than the radius |

Otherwise the verdict is `ok` and the cost is taken from the budget. A refused step leaves the budget unchanged.

## What must always hold

Each property below is a theorem in `PlantGate/Spec.lean`.

| Property | Theorem |
|----------|---------|
| An admitted step had a positive cost within the budget, a radius that is not negative, states of equal length and a move within the radius, and it spent exactly its cost. | `PlantGate.Spec.gate_ok_sound` |
| A step that meets all of those conditions, on a baseline that is not empty, is admitted. | `PlantGate.Spec.gate_complete` |
| A refused step spends nothing. | `PlantGate.Spec.refusal_spends_nothing` |
| The budget never grows, and a budget that is not negative never becomes negative. | `PlantGate.Spec.budget_never_grows` |
| Within the radius, no margin rises by more than the radius. | `PlantGate.Spec.no_margin_rises_past_radius` |
| When the radius is the headroom of the baseline, an admitted candidate has every margin at or below the limit. | `PlantGate.Spec.accepted_stays_within` |
| Start within the limit with a budget that is not negative. After any list of proposals, every margin is still at or below the limit, the budget is not negative, and it has not grown. | `PlantGate.Spec.run_safe` |
| The number of admitted changes plus the budget left never exceeds the budget at the start. | `PlantGate.Spec.run_bounded` |

The first, third, fourth, fifth and sixth are safety properties. A gate that refuses everything meets them all, so the second is there to rule that gate out.

The last two are about the loop, and they hold for every list of proposals. Nothing is assumed about who or what proposes: a search, a model, or an adversary. `run_safe` says no proposer can push a margin past its limit or overdraw the budget through this gate. `run_bounded` says the number of changes the system can make to itself is at most the budget someone gave it.

## What the specification does not say

- That the margins fed to the gate are true. They come from other verifiers and, one day, from sensors. A wrong margin gives a wrong verdict.
- That a candidate inside the radius is a good change. The gate bounds harm. It does not measure benefit.
- That the limit is the right limit. It is a number the caller supplies.
- Anything about time. The gate is a pure function and takes no account of how fast a state changes.

## Oracle

The original this stands in for is the exact Python gate in `tests/oracle.py`, which the optifab verifier uses to decide every step of its improvement loop.
