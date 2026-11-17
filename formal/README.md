# plantgate: an exact gate, plant model and improvement loop, proved in Lean

This is the formal core of [optifab](../README.md). It is a gate that decides whether a proposed change to a plant may go ahead, a model that turns a design into its margins and its objective, and the loop that takes up proposed designs generation after generation. It follows the layout and the rules of the Proven Commons [verified bar](https://github.com/Proven-Commons/mission/blob/main/playbook/verified-bar.md).

Status: in progress. The specification has not been approved by a reviewer, so this is not verified.

## What is proved

| Claim | Theorem |
|-------|---------|
| A step the gate admits had a positive cost within the budget, a radius that is not negative, states of equal length and a move within the radius, and it spent exactly its cost. | `PlantGate.Spec.gate_ok_sound` |
| A step that meets all of those conditions, on a baseline that is not empty, is admitted. | `PlantGate.Spec.gate_complete` |
| A refused step spends nothing. | `PlantGate.Spec.refusal_spends_nothing` |
| The budget never grows, and a budget that is not negative never becomes negative. | `PlantGate.Spec.budget_never_grows` |
| Within the radius, no margin rises by more than the radius. | `PlantGate.Spec.no_margin_rises_past_radius` |
| When the radius is the headroom of the baseline, an admitted candidate has every margin at or below the limit. | `PlantGate.Spec.accepted_stays_within` |
| Whatever is proposed, and in whatever order, the loop keeps every margin at or below the limit and never overdraws the budget. | `PlantGate.Spec.run_safe` |
| The number of changes the loop admits is at most the budget it was given. | `PlantGate.Spec.run_bounded` |
| A proposed design that lies within the bounds, stays within the headroom and does not lower the objective is taken up, for one unit of budget. | `PlantGate.Spec.step_complete` |
| Whatever designs are proposed, the margins of the design held, as the model computes them, stay at or below the limit, and the budget is never overdrawn. | `PlantGate.Spec.loop_safe` |
| The design held never leaves the bounds it started in. | `PlantGate.Spec.loop_in_bounds` |
| Whatever designs are proposed, the objective of the design held never falls. | `PlantGate.Spec.loop_never_worse` |
| The number of designs taken up is at most the budget. | `PlantGate.Spec.loop_bounded` |
| With the limit at 1,000,000 parts per million, the design held always has enough captured heat to drive its chiller, always cools itself at the scheduler's load floor, and always holds one outage in its store. These are exact inequalities, free of rounding. | `PlantGate.Spec.loop_keeps_physics` |

The statements are in `PlantGate/Spec.lean`, the proofs in `PlantGate/Proofs.lean`. The command-line tool in `Main.lean` calls the proved `PlantGate.gate` and `PlantGate.headroom` directly for a gate line, and the proved `PlantGate.accepts`, `PlantGate.step`, `PlantGate.margins` and `PlantGate.objective` for a design line.

The first eight theorems are about the gate and take margins as given. The last six are about designs: the margins and the objective are computed inside the proved code, so nothing is passed across by hand between the model, the gate and the loop.

## What is not proved

- That the model describes a real plant. `loop_keeps_physics` is about the model's own inequalities. Its constants come from other repositories' certificates, which are claimed and not measured. No sensor exists yet.
- That the eleven certified margins the model carries as constants are true. They are computed by other verifiers.
- That the bounds are what could really be built or set. They are declared by a person.
- That a higher objective is a better campus. `loop_never_worse` says the objective never falls. The objective and its scenario are choices.
- That the gate alone admits only improvements. The gate bounds harm. It is the step over designs that also asks for the objective not to fall.
- The floating-point gate `plant_gate` in `verify.py`, which is tested against Weft's own gate and compared with this one away from the boundary, but has no proof.
- Parsing the input lines and printing the results in `Main.lean`. The differential tests cover them.
- The proposers, and the Python code that keeps the ledger. The Python copy of the model and the step is tested against the Lean one, and every ledger decision is worked out again in Lean from the two designs.
- How fast it runs.

## What you must trust

- The Lean kernel and the external kernels shipped with Lean, which all check the proofs.
- The Lean compiler and runtime, which turn the proved definitions into the program that runs.
- The hardware it runs on.
- Python, as the oracle in the differential tests.

There are no other dependencies. The project uses Lean's core library only.

## Re-check it

Needs Linux, [elan](https://github.com/leanprover/elan), and bubblewrap (`apt install bubblewrap`).

```
lake build
lake comparator --paranoid
python3 tests/run_tests.py
```

`lake comparator --paranoid` builds the project in a sandbox, checks that each theorem in `PlantGate/Proofs.lean` proves exactly the statement in `PlantGate/Spec.lean`, checks that it uses only the axioms `propext`, `Classical.choice`, and `Quot.sound`, and replays it through every kernel shipped with Lean. The test script compares the tool with the oracle on 400,000 inputs (300,000 gate decisions and 100,000 proposed designs) and rewrites `tests/TEST-RESULTS.md`.

To run the Proven Commons bar check on it, from a clone of Proven-Commons/mission:

```
python3 bar/check.py /path/to/optifab/formal --offline
```

## Layout

- `PlantGate.lean`: the code under proof.
- `PlantGate/Spec.lean`: the statements, with `sorry` for proofs. This is the file a reviewer approves.
- `PlantGate/Proofs.lean`: the proofs, under the same names.
- `Main.lean`: the command-line tool used by the tests and by the ledger replay.
- `lakefile.toml`: the build. It names the libraries and the executable, and sets nothing else.
- `comparator.json`: which theorems `lake comparator` checks, and which axioms it allows.
- `bar.toml`: the project's record for the bar check.
- `SPEC.md`: the specification in plain words.
- `tests/oracle.py`: the exact Python gate, plant model and step.
- `tests/run_tests.py`: differential tests against the oracle.
