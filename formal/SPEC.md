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
| drive heat | cooling needed at full load: the uncaptured IT heat plus the fixed heat load | cooling the chiller makes from the heat the liquid loop captures at full load: that heat times the COP |
| load floor | the fixed heat load | the cooling the plant gains per kW of IT load, `(1 + COP) × capture − 1`, times the scheduler's load floor |
| outage | IT load not shed plus the fixed heat load, times the length of one outage | what the store holds |

Each is demand over capacity in parts per million, rounded up. A capacity that is not positive reads as 10,000,000, and so does any ratio above ten.

`PlantGate.objective p sc g` is useful IT energy over utility energy for the scenario year, in parts per million and rounded down. Load shed in an outage is lost, and only the utility power that load would have drawn is saved.

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

A proposed design is taken up when none of these refusals applies, and otherwise nothing changes:

| Refusal | When |
|---------|------|
| `same` | the proposed design is identical to the design held |
| `bounds` | some gene lies outside the plant's lowest and highest values |
| any gate verdict above | the gate refuses the move from the margins of the design held to the margins of the one proposed, with the headroom of the design held as the radius and a cost of one |
| `worse` | the objective of the proposed design is lower than that of the design held |
| `headroom` | the objective equals that of the design held, and the proposed design does not strictly widen headroom |

An asymmetric variant `PlantGate.gateAsymmetric limit base cand budget cost` counts only upward margin moves (`posDistSq`) when `0 ≤ headroom limit base`, so pure safety moves of any size are admitted as `ok`. When `headroom limit base < 0`, recovery mode admits a candidate as `okRecovery` iff it strictly widens headroom (`headroom limit base < headroom limit cand`) and satisfies `noNewExcess` (no safe coordinate crosses `limit` and no already-violating coordinate rises further); otherwise it refuses with `noImprovement`.

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
| With a budget above zero and the design held within the limit, a proposed design that differs from it, lies within the bounds and the headroom, and either strictly raises the objective or keeps it equal while strictly widening headroom is taken up, and the budget falls by one. | `PlantGate.Spec.step_complete` |
| A proposal identical to the design held is never taken up. | `PlantGate.Spec.same_design_not_taken_up` |
| An equal-objective proposal that does not strictly widen headroom is refused. | `PlantGate.Spec.tie_headroom_decay_refused` |
| A proposed design that is not taken up changes nothing: the design held and the budget are as they were. | `PlantGate.Spec.step_refusal_changes_nothing` |
| Start from a design whose margins are within the limit, with a budget that is not negative. After any list of proposed designs, the margins of the design held are still within the limit, the budget is not negative, and it has not grown. | `PlantGate.Spec.loop_safe` |
| Start from a design within the bounds. After any list of proposed designs, the design held is still within them. | `PlantGate.Spec.loop_in_bounds` |
| After any list of proposed designs, the objective of the design held is at least what it was at the start. | `PlantGate.Spec.loop_never_worse` |
| After any list of proposed designs, either the objective strictly rose, or it stayed equal and the headroom did not fall. | `PlantGate.Spec.loop_lex_monotone` |
| The number of designs taken up plus the budget left never exceeds the budget at the start. | `PlantGate.Spec.loop_bounded` |
| With the limit at 1,000,000, start from a design whose margins are within it. After any list of proposed designs, the design held satisfies three exact inequalities: the cooling needed at full load is at most what the captured heat can drive, the fixed heat load is at most the cooling gained at the scheduler's floor, and the heat of one outage, from the IT load that is not shed and from the fixed heat load, is at most what the store holds. The three are not independent: for a scheduler floor at or below the IT load, the first follows from the second. | `PlantGate.Spec.loop_keeps_physics` |
| Any well-formed plant, scenario, and design has non-negative fixed heat load, drive demand, and outage heat, strictly positive thermal store capacity, and strictly positive scheduler floor. | `PlantGate.Spec.wellformed_nonneg_demands` |
| On a well-formed plant and scenario starting within bounds and within 1,000,000 ppm, after any list of proposed designs the design held remains well-formed, satisfies all three exact inequalities, and has non-negative drive and outage demands. | `PlantGate.Spec.loop_keeps_wellformed_physics` |
| An asymmetric-gate `.ok` admission has every margin at or below the limit and spends its positive cost within budget. | `PlantGate.Spec.asym_gate_ok_stays_within` |
| Under the asymmetric gate, any non-empty same-length pure safety move from within the limit is admitted as `.ok` regardless of move magnitude. | `PlantGate.Spec.asym_gate_pure_safety_admitted` |
| Under the asymmetric gate, an `.okRecovery` step starts from negative headroom, strictly lowers the worst excess above the limit, creates no new violation or worsening of any existing violation, and spends its positive cost. | `PlantGate.Spec.asym_gate_recovery_lyapunov_descent` |
| Starting within the limit with non-negative budget, any sequence of proposals through `runAsymmetric` stays within the limit, keeps the budget non-negative and non-increasing, and admits at most the starting budget of changes. | `PlantGate.Spec.asym_run_safe_and_bounded` |

The first, third, fourth, fifth and sixth are safety properties. A gate that refuses everything meets them all, so the second is there to rule that gate out.

`run_safe` and `run_bounded` are about the loop over margin vectors, and they hold for every list of proposals. Nothing is assumed about who or what proposes: a search, a model, or an adversary. `run_safe` says no proposer can push a margin past its limit or overdraw the budget through this gate. `run_bounded` says the number of changes the system can make to itself is at most the budget someone gave it.

The twelve statements about designs and well-formedness go one step further. In them the three margins that move with the genes are not an input: the model inside the proved code computes them from the design. The eleven margins carried as constants still are an input. `step_complete` rules out a loop that takes nothing up, and `step_refusal_changes_nothing` rules out one that loses the design or the budget when it refuses. `loop_never_worse` and `loop_lex_monotone` say no proposer can make the design held score lower or erode headroom at a tied objective. `loop_keeps_physics` and `loop_keeps_wellformed_physics` say what a margin within the limit means, as non-vacuous inequalities with no rounding in them, so a reviewer can check the model against the physics without reading the rounding.

The final four statements formalize the asymmetric upward gate (`gateAsymmetric`) and its out-of-limit recovery mode (`okRecovery`), closing the symmetric-distance refusal of large safety moves and providing strict Lyapunov descent from out-of-limit baselines without sacrificing the `≤ limit` invariant inside the envelope.

## Defects found by an independent read

A separate read of this specification (2026-11-17) found five defects in the model. A second, independent check reproduced all five in exact arithmetic. All five are now fixed:

Fixed in v0.3.1:

- **The objective's outage term.** It subtracted the whole utility power of the shed load during an outage, including the part that does not depend on load, so an outage with nothing shed raised the objective. It now subtracts only what the shed load would have drawn. Every objective is about 18 ppm lower than in v0.3.0. With no shedding the objective is the same with twelve outages as with none.
- **The outage margin.** It counted IT heat only. It now counts the fixed heat load as well, about 71 kWh in a twenty-minute outage for the reference design. A store of 2,400 kWh with 30% shed passed in v0.3.0 and is refused now, at 1,001,765 ppm.
- **A proposal identical to the design held** was taken up and charged. It is now refused as `same`, and `same_design_not_taken_up` says so.

Fixed in this revision (Refs #14):

- **Equal-objective headroom decay (`#14.3`).** `accepts` now requires `lexImproves`: either a strictly higher objective, or an equal objective with strictly wider headroom. Equal-objective proposals that hold or erode headroom are refused as `headroom`, proved by `tie_headroom_decay_refused` and `loop_lex_monotone`.
- **Well-formedness of inputs (`#14.4`).** `WellFormedPlant`, `WellFormedGenome`, and `WellFormed` rule out negative loads, zero-length outages, `shed > 1,000,000`, `capture > 1,000,000`, and `floor ≤ 0`. `wellformed_nonneg_demands` and `loop_keeps_wellformed_physics` prove that demands remain non-negative and capacities strictly positive across arbitrary proposal sequences, and `verify.py` checks `well_formed` for the pinned plant and scenario.
- **Refusal of large safety moves and out-of-limit recovery (`#14.5`).** `gateAsymmetric` measures upward margin moves only (`posDistSq`) inside the limit—admitting pure safety moves of arbitrary size (`asym_gate_pure_safety_admitted`) while preserving `≤ limit` (`asym_gate_ok_stays_within`, `asym_run_safe_and_bounded`)—and provides strict Lyapunov excess descent (`okRecovery`, `asym_gate_recovery_lyapunov_descent`) from out-of-limit baselines without introducing new violations.

## What the specification does not say

- That the model is a true description of a plant, or that its constants are right. They are pinned from other repositories' certificates.
- That the bounds are what could really be built, or that the scenario is the right year to score.

- That margins fed to the gate from outside are true. Of the eleven carried as constants, ten come from other verifiers and one is derived in `verify.py`. One day they should come from sensors. A wrong margin gives a wrong verdict.
- That a candidate inside the radius is a good change. The gate bounds harm. It does not measure benefit.
- That the limit is the right limit. It is a number the caller supplies.
- Anything about time. The gate is a pure function and takes no account of how fast a state changes.

## Oracle

The original this stands in for is the exact Python gate, plant model and step in `tests/oracle.py`, which the optifab verifier uses to compute every margin and decide every step of its improvement loop.
