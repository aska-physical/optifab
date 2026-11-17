# plantgate: an exact gate for a plant, proved in Lean

This is the formal core of [optifab](../README.md). It is a gate that decides whether a proposed change to a plant may go ahead, and the loop that applies such changes generation after generation. It follows the layout and the rules of the Proven Commons [verified bar](https://github.com/Proven-Commons/mission/blob/main/playbook/verified-bar.md).

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

The statements are in `PlantGate/Spec.lean`, the proofs in `PlantGate/Proofs.lean`. The command-line tool in `Main.lean` calls the proved `PlantGate.gate` and `PlantGate.headroom` directly.

## What is not proved

- That the margins given to the gate are true. They are computed by other verifiers from models. No sensor exists yet.
- That an admitted change is an improvement. The gate bounds harm and says nothing about benefit.
- The floating-point gate `plant_gate` in `verify.py`, which is tested against Weft's own gate and compared with this one away from the boundary, but has no proof.
- Parsing the input lines and printing the results in `Main.lean`. The differential tests cover them.
- The Python code that proposes changes, evaluates them and keeps the ledger.
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

`lake comparator --paranoid` builds the project in a sandbox, checks that each theorem in `PlantGate/Proofs.lean` proves exactly the statement in `PlantGate/Spec.lean`, checks that it uses only the axioms `propext`, `Classical.choice`, and `Quot.sound`, and replays it through every kernel shipped with Lean. The test script compares the tool with the oracle on 300,000 inputs and rewrites `tests/TEST-RESULTS.md`.

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
- `tests/oracle.py`: the exact Python gate.
- `tests/run_tests.py`: differential tests against the oracle.
