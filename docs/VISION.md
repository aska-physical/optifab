# How close to the vision

The vision, in the owner's words: a fully end-to-end formally verified, recursively improving intelligence
system that evolves its hardware and software together, as one cohesive unit.

This note takes that sentence apart. For each part it says what exists today, with the file or the certificate
figure that shows it, and what does not exist. Nothing here is measured, and the word "verified" is not claimed
for anything.

## Part by part

| Part of the vision | What exists | What is missing |
|---|---|---|
| **Formally verified** | Sixteen theorems, proved in Lean with no dependencies ([formal/](../formal/README.md)). Eight are about the gate. Eight are about designs: the plant model, the bounds, the objective and the step are inside the proved code, so the three margins that move are no longer handed to the gate from outside. `lake comparator --paranoid` accepts them under six kernels with the standard axioms only. The Proven Commons bar check passes items 2 to 6. | A reviewer's approval of the specification, which is bar item 1 and cannot happen yet because the Proven Commons reviewer list is empty. Any proof that the model describes the plant: its constants are claimed, eleven of its fourteen margins are carried as constants, and of five defects an independent read found in it, two and part of a third are fixed ([formal/SPEC.md](../formal/SPEC.md)). The proposers and the floating-point gate are unproved. |
| **End to end** | One command re-runs a chain from pinned certificates to a design, to margins and an objective, to the step, to a ledger. A second works every recorded decision out again in Lean from the two designs (3,072 decisions across four ledgers, 0 mismatches). | Both ends. No sensor feeds the chain and no valve, load or machine obeys it. Four of the ten interfaces in [STRUCTURE.md](STRUCTURE.md) are checked. |
| **Recursively improving** | A loop ([loop.py](../loop.py)) in which each admitted change becomes the baseline of the next generation. The proposer's own step scale is part of the genome: it doubles after a success, halves after a refusal, and is recorded. 45 of 48 proposals were admitted and the objective rose from 0.914210 to 0.918990. That it can never fall is now a theorem (`loop_never_worse`), for any proposer. And what one proposer learned has been handed to the next: a second instance given the first run's notes reached 0.919529 in 5 proposals, where the first reached 0.919529 in 12. | The hand-over was done once, by hand, with notes written in prose. Nothing improves the gate, the plant model or the proposer's own code. The objective is a choice. |
| **Intelligence system** | A language model has proposed through the loop's interface in two separate runs, seeing only the printed state. The first made 12 proposals, 7 taken up, and reached 0.919529 against 0.918990 for the seeded search. The second, given the first one's notes, reached 0.919529 in 5. Their reasons are recorded with their proposals. Weft's adaptive models and Exo's agents have a place in the structure, and the floating-point gate here agrees with Weft's own on 100,000 generated cases. | These are two recorded runs of one model. Neither Weft nor Exo proposes anything, and neither can yet shed load or report the energy it uses. |
| **Evolving hardware and software** | One genome with three hardware genes (thermal store, liquid capture, wall U-value) and two software genes (scheduler load floor, load shed in an outage), under one gate and in one ledger. 30 hardware and 15 software changes were admitted. Hardware changes open headroom and software changes use it. | The hardware is three numbers in a thermal model. The eleven certified structural margins are constants, because the verifiers that compute them were not run with changed inputs. Nothing is built. |
| **Cohesive and unified** | One predicate for weights and plant, one 64-byte frame, one margin vector, one record. 32 of 41 repositories from four organisations have a place in one structure. | The organisations share no interface in code yet. Weft does not know the plant frame, Synmerit does not sign the ledger, and no Proven Commons parser is on the telemetry path. |

## What the proofs cover

```
proved in Lean        gate, plant model, bounds, objective, step,           formal/PlantGate.lean
                      loop over any proposed designs
tested against it     Python gate, model and step (405,000 cases),          formal/tests/, results/formal.json
                      replay of four ledgers, decision by decision and
                      as whole runs through the Lean loop
tested, not proved    floating-point gate against Weft's (100,000 cases)    verify.py
computed, not proved  the plant envelope, the eleven constant margins,      verify.py
                      the site-dependent load floor
recorded, not proved  what a language model proposed in two runs, why,     results/model_run*.json,
                      and the notes one run left for the next               results/model_lessons*.md
taken on trust        the three upstream certificates, the bounds,          data/upstream/, loop.py
                      the scenario
absent                sensors, load control, machines
```

The two theorems that matter most for a system that changes itself:

- **`run_safe`**: start with every margin at or below its limit and a budget that is not negative. After any
  list of proposals whatever, every margin is still at or below its limit and the budget is not overdrawn.
  The statement puts no condition on the proposer. It holds for a search, a model or an adversary.
- **`run_bounded`**: the number of changes the loop admits, plus the budget left, never exceeds the budget at
  the start. Whoever sets the budget sets the most changes the system can ever make to itself.

Both are about the gate's arithmetic, and take the margins as given. Three more are about designs, with the
margins computed inside the proved code:

- **`loop_safe`**: from a start within the limit, after any list of proposed designs, the margins of the
  design held are within the limit.
- **`loop_never_worse`**: after any list of proposed designs, the objective is at least what it was. No
  proposer, however bad, can make the design held score lower. It can stay the same: a design that ties is
  taken up, so this is "never worse" and not "always better".
- **`loop_keeps_physics`**: what "within the limit" means, as exact inequalities about heat and storage.

They close the gap between the model and the gate. They do not close the gap between the model and the
plant. Whether the model's constants are true is a question for sensors and independent verifiers. And the
model has mistakes of its own: a separate agent, given the code and not these conclusions, found that the
objective is off by a constant, that the outage margin leaves out the fixed heat load, and that a proposer
can spend the whole budget on designs that tie. v0.3.1 corrects the first two and stops an identical proposal from being charged. Every figure in this
note is from the corrected model, and both recorded runs were made again. What is still open is listed in
[formal/SPEC.md](../formal/SPEC.md).

## What running the loop showed

These come from the certificate (`improvement_loop`) and can be re-run. The scenario is a choice made in
`loop.py`, so the sizes are illustrations. The behaviours are properties of the gate.

1. **A design that sits exactly on a limit cannot change at all.** The radius is the headroom of the worst
   margin. Started with one margin at exactly its limit, the loop admitted 0 of 17 proposals. funi-frame sizes
   its thermal store for exactly 15 minutes at full load, so against a 15-minute requirement it would be frozen
   under this gate. Headroom is what makes change possible.
2. **A proposer with no caution slows itself.** Allowed to run margins right up to the limit, it had 99 of 161
   proposals refused and finished lower (0.916016) than one that kept a 5% reserve (0.918990 from 48
   proposals).
3. **Hardware and software have to take turns.** Software alone runs into the plant's load floor. More capture,
   a better wall and a larger store open headroom. The scheduler then uses it. In the run, the store grew from
   2,500 to 4,262 kWh_th, capture from 85% to 95%, and the scheduler stopped shedding load in outages.
4. **The most tempting change is the one the gate refuses.** Dropping the scheduler's floor below the plant's
   load floor raises the objective by 0.25% in one step. It puts a margin at 113% of its limit and is refused.
5. **The loop stops where a person told it to.** With a budget of 3 it made exactly 3 changes.
6. **A model proposes differently from a search.** Shown only the printed state, a language model made 12
   proposals and 7 were taken up, 2 of them moving hardware and software in the same step. It reached
   0.919529, the best a direct search finds possible. The seeded search reached 89.9% of that gain
   with 48 proposals. Its reasons are recorded with its proposals.
7. **What one proposer learned, the next could use.** The first run's closing notes, word for word, were
   given to a second instance of the same model with no memory of that run. It reached 0.919529 in 5
   proposals with 0 refused, where the first had used 12 with 5 refused. It then wrote its own
   notes. That is the smallest version of a system improving its own improver, and it was done by hand,
   once. Both runs were made twice: first against the model of v0.3.0, and again after v0.3.1 corrected it.
8. **A good proposer ends where it cannot move.** Both runs end with the `load_floor` margin at 999,215 ppm, 785 from its limit.
   The objective may not fall, so the design cannot back away from the limit either. A loop that is proved
   safe and proved never to get worse comes to rest at the edge of its envelope. To keep evolving, the
   objective has to give headroom a value, or the plant or its bounds have to change.
9. **An adversary gets nowhere.** 3,007 proposals built to break the loop ended as 55 `bounds`, 456 `budget`, 2389 `distance`, 64 `ok`, 38 `same`, 5 `worse`. The budget ran
   out after 64 changes, and every design held was inside every limit and bound.
10. **A correction to the model can undo a recorded run.** v0.3.1 added the fixed heat load to the outage
    margin. That one term makes the outage margin the tightest at the start and cuts the first radius from
    59,652 to 38,305 ppm. Replayed under the corrected model, only 2 of the 15 proposals in the two
    earlier runs are decided the same way. A recorded run is evidence about one model, not about the plant.

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
  proposes next. Within a recorded run this now happens, and once it has happened across two runs, through
  notes passed by hand. Nothing yet does that without a person, and nothing improves the proposer itself.
- **"Hardware and software"**: an admitted hardware change is one a machine could make, with its own process
  limits in the margin vector.

The first, second and fourth are not true today. The third is true of two recorded runs. The gate, the
model, the loop and the record are in place for the rest to plug into.
