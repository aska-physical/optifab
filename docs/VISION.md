# How close to the vision

The vision, in the owner's words: a fully end-to-end formally verified, recursively improving intelligence
system that evolves its hardware and software together, as one cohesive unit.

This note takes that sentence apart. For each part it says what exists today, with the file or the certificate
figure that shows it, and what does not exist. Nothing here is measured, and the word "verified" is not claimed
for anything.

## Part by part

| Part of the vision | What exists | What is missing |
|---|---|---|
| **Formally verified** | Eight theorems about the gate and the loop built on it, proved in Lean with no dependencies ([formal/](../formal/README.md)). `lake comparator --paranoid` accepts them under six kernels with the standard axioms only. The Proven Commons bar check passes items 2 to 6. | A reviewer's approval of the specification, which is bar item 1 and cannot happen yet because the Proven Commons reviewer list is empty. Proofs about anything but the gate: the plant model, the margins, the proposer and the Python are unproved. |
| **End to end** | One command re-runs a chain from pinned certificates to margins, to the gate, to a ledger, to a replay of every ledger decision in Lean (50 decisions, 0 mismatches). | Both ends. No sensor feeds the chain and no valve, load or machine obeys it. Four of the ten interfaces in [STRUCTURE.md](STRUCTURE.md) are checked. |
| **Recursively improving** | A loop ([loop.py](../loop.py)) in which each admitted change becomes the baseline of the next generation. The proposer's own step scale is part of the genome: it doubles after a success, halves after a refusal, and is recorded. 45 of 50 proposals were admitted and the objective rose from 0.914228 to 0.919009 without ever falling. | The proposer is a seeded search, not an intelligence. It tunes one number about itself. It does not learn, and it does not improve the gate, the model or its own code. |
| **Intelligence system** | Weft's adaptive models and Exo's agents have a place in the structure, and the floating-point gate here agrees with Weft's own on 100,000 generated cases. | No model runs in the loop. Neither Weft nor Exo proposes anything, and neither can yet shed load or report the energy it uses. |
| **Evolving hardware and software** | One genome with three hardware genes (thermal store, liquid capture, wall U-value) and two software genes (scheduler load floor, load shed in an outage), under one gate and in one ledger. 30 hardware and 15 software changes were admitted. Hardware changes open headroom and software changes use it. | The hardware is three numbers in a thermal model. The eleven certified structural margins are constants, because the verifiers that compute them were not run with changed inputs. Nothing is built. |
| **Cohesive and unified** | One predicate for weights and plant, one 64-byte frame, one margin vector, one record. 32 of 41 repositories from four organisations have a place in one structure. | The organisations share no interface in code yet. Weft does not know the plant frame, Synmerit does not sign the ledger, and no Proven Commons parser is on the telemetry path. |

## What the proofs cover

```
proved in Lean        gate, generation step, loop over any proposals        formal/PlantGate.lean
tested against it     Python exact gate (300,000 cases), ledger replay      formal/tests/, results/formal.json
tested, not proved    floating-point gate against Weft's (100,000 cases)    verify.py
computed, not proved  margins, load floor, thermal budget, objective        verify.py, loop.py
taken on trust        the three upstream certificates                       data/upstream/
absent                sensors, load control, machines, a model that proposes
```

The two theorems that matter most for a system that changes itself:

- **`run_safe`**: start with every margin at or below its limit and a budget that is not negative. After any
  list of proposals whatever, every margin is still at or below its limit and the budget is not overdrawn.
  The statement puts no condition on the proposer. It holds for a search, a model or an adversary.
- **`run_bounded`**: the number of changes the loop admits, plus the budget left, never exceeds the budget at
  the start. Whoever sets the budget sets the most changes the system can ever make to itself.

Both are about the gate's arithmetic. They say nothing about whether the margins fed to the gate are true.
That is the real gap between a proved gate and a safe plant, and it is why the margins need sensors and
independent verifiers behind them.

## What running the loop showed

These come from the certificate (`improvement_loop`) and can be re-run. The scenario is a choice made in
`loop.py`, so the sizes are illustrations. The behaviours are properties of the gate.

1. **A design that sits exactly on a limit cannot change at all.** The radius is the headroom of the worst
   margin. Started with one margin at exactly its limit, the loop admitted 0 of 14 proposals. funi-frame sizes
   its thermal store for exactly 15 minutes at full load, so against a 15-minute requirement it would be frozen
   under this gate. Headroom is what makes change possible.
2. **A proposer with no caution slows itself.** Allowed to run margins right up to the limit, it had 126 of 186
   proposals refused and finished lower (0.916009) than one that kept a 5% reserve (0.919009 from 50
   proposals).
3. **Hardware and software have to take turns.** Software alone runs into the plant's load floor. More capture,
   a better wall and a larger store open headroom. The scheduler then uses it. In the run, the store grew from
   2,500 to 4,350 kWh_th, capture from 85% to 95%, and the scheduler stopped shedding load in outages.
4. **The most tempting change is the one the gate refuses.** Dropping the scheduler's floor below the plant's
   load floor raises the objective by 0.25% in one step. It puts a margin at 113% of its limit and is refused.
5. **The loop stops where a person told it to.** With a budget of 3 it made exactly 3 changes.

## The shortest path from here

Each step has a proposal in [PROPOSALS.md](PROPOSALS.md) and an issue on GitHub.

1. Put measurements behind the margins: the two missing sensors and a frame emitter (proposal 1).
2. Give the loop something to act on: a way to shed or defer compute, with an energy reading (proposal 2).
3. Let a model propose: a Weft cell or an Exo agent in place of the seeded search, speaking through the gate
   (proposal 3).
4. Bring structure into the genome: run the upstream verifiers with changed inputs, so structural margins
   move (proposal 4).
5. Get the specification reviewed, so the gate can be called verified (proposal 5).
6. Sign the ledger (proposal 6), close the first fabrication loop (proposal 7), and go from one campus to a
   network (proposal 8).

## What would have to be true before the vision's words apply

- **"Formally verified"**: a reviewer who did not write `formal/SPEC.md` approves it, and the bar check runs
  in CI on the default branch. Then the gate is verified. The system is not, until the margins are trustworthy.
- **"End to end"**: at least one margin in the vector comes from a sensor, and at least one admitted step
  changes something real.
- **"Recursively improving intelligence"**: a model proposes, and what it learns from refusals changes what it
  proposes next. Today the only thing that adapts is a step size.
- **"Hardware and software"**: an admitted hardware change is one a machine could make, with its own process
  limits in the margin vector.

None of these is true today. The gate, the loop and the record are in place for them to plug into.
