# Specification: the plant gate, the plant model and the loop over designs

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

The second half is about designs.

- A **design** (`PlantGate.Genome`) is five integers: the thermal store in kWh of heat, the share of IT heat captured in liquid in parts per million, the wall U-value in mW/m²K, the scheduler's load floor in kW, and the share of load the scheduler sheds in a cooling outage in parts per million. The first three are hardware and the last two are software.
- The **plant** (`PlantGate.Plant`) is what no gene changes: the IT load, the chiller and loop COPs, the envelope, the overheads, the certified margins that are carried as constants, and the lowest and highest value of each gene that could be built or set.
- The **scenario** (`PlantGate.Scenario`) is the year the objective is scored on.

`PlantGate.margins p sc g` is the margin vector of a design: the certified constants, then three margins that move with the genes.

| Margin | Demand | Capacity |
|--------|--------|----------|
| drive heat | heat the sorption chiller needs at full load: the uncaptured IT heat plus the fixed heat load, over the COP | heat the liquid loop captures at full load |
| load floor | the fixed heat load | the cooling the plant gains per kW of IT load, `(1 + COP) × capture − 1`, times the scheduler's load floor |
| outage | IT load not shed, times the length of one outage | what the store holds |

Each is demand over capacity in parts per million, rounded up. A capacity that is not positive reads as 10,000,000, and so does any ratio above ten.

`PlantGate.objective p sc g` is useful IT energy over utility energy for the scenario year, in parts per million and rounded down.

`PlantGate.step p sc limit s cand` applies one proposed design to a pair of the design held and the budget. `PlantGate.loop` applies a list of them. `PlantGate.changes` counts the designs taken up.

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

A proposed design is taken up when all three of these hold, and otherwise nothing changes:

| Refusal | When |
|---------|------|
| `bounds` | some gene lies outside the plant's lowest and highest values |
| any gate verdict above | the gate refuses the move from the margins of the design held to the margins of the one proposed, with the headroom of the design held as the radius and a cost of one |
| `worse` | the objective of the proposed design is lower than that of the design held |

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
| A proposed design within the bounds, within the headroom and with an objective that is not lower is taken up, and the budget falls by one. | `PlantGate.Spec.step_complete` |
| Start from a design whose margins are within the limit, with a budget that is not negative. After any list of proposed designs, the margins of the design held are still within the limit, the budget is not negative, and it has not grown. | `PlantGate.Spec.loop_safe` |
| The design held never leaves the bounds it started in. | `PlantGate.Spec.loop_in_bounds` |
| After any list of proposed designs, the objective of the design held is at least what it was at the start. | `PlantGate.Spec.loop_never_worse` |
| The number of designs taken up plus the budget left never exceeds the budget at the start. | `PlantGate.Spec.loop_bounded` |
| With the limit at 1,000,000, start from a design whose margins are within it. After any list of proposed designs, the design held satisfies three exact inequalities: the drive heat needed is at most the heat captured, the fixed heat load is at most the cooling gained at the scheduler's floor, and the heat of one outage is at most what the store holds. | `PlantGate.Spec.loop_keeps_physics` |

The first, third, fourth, fifth and sixth are safety properties. A gate that refuses everything meets them all, so the second is there to rule that gate out.

`run_safe` and `run_bounded` are about the loop over margin vectors, and they hold for every list of proposals. Nothing is assumed about who or what proposes: a search, a model, or an adversary. `run_safe` says no proposer can push a margin past its limit or overdraw the budget through this gate. `run_bounded` says the number of changes the system can make to itself is at most the budget someone gave it.

The six statements about designs go one step further. In them the margins are not an input: the model inside the proved code computes them from the design. `step_complete` rules out a loop that takes nothing up. `loop_never_worse` is what makes the loop an improvement loop: no proposer can make the design held score lower. `loop_keeps_physics` says what a margin within the limit means, as inequalities with no rounding in them, so a reviewer can check the model against the physics without reading the rounding.

## What the specification does not say

- That the model is a true description of a plant, or that its constants are right. They are pinned from other repositories' certificates.
- That the bounds are what could really be built, or that the scenario is the right year to score.

- That margins fed to the gate from outside are true. The eleven certified margins come from other verifiers and, one day, from sensors. A wrong margin gives a wrong verdict.
- That a candidate inside the radius is a good change. The gate bounds harm. It does not measure benefit.
- That the limit is the right limit. It is a number the caller supplies.
- Anything about time. The gate is a pure function and takes no account of how fast a state changes.

## Oracle

The original this stands in for is the exact Python gate, plant model and step in `tests/oracle.py`, which the optifab verifier uses to compute every margin and decide every step of its improvement loop.
