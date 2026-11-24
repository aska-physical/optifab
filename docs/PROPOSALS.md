# Proposals

Eight systems, one for each open place in the loop or gap in the evidence. Each says what is missing and how
that is known, what to build, the first slice with a test that can fail, and what it rests on. They are
proposals: none is built. Each has an issue on GitHub where it can be claimed, changed or rejected.

The element and interface codes (N3, L5 and so on) are those of [STRUCTURE.md](STRUCTURE.md).

| # | System | Closes | First slice |
|---|---|---|---|
| 1 | Plant sense: two sensors and a frame emitter | N3, N4, L1, L2 | A bench rig whose recorded frames pass the contract check |
| 2 | Load control with an energy reading | L5 | One Weft or Exo job that sheds on request and reports joules |
| 3 | A model as the proposer | "intelligence" in the vision | A recorded run in which a model's proposals go through the gate |
| 4 | Structural genes | "hardware" in the vision | funi-frame's verifier re-run with one changed input inside the loop |
| 5 | Specification review for the gate | R2, bar item 1 | One named reviewer approves `formal/SPEC.md` |
| 6 | Signed ledger and command channel | K2, L9 | The ledger's head signed and checked by a second implementation |
| 7 | A first fabrication cell under the gate | F1, L8 | Fe-SMA activation of one cassette as a gated process |
| 8 | A network of campuses | the "network" in the objective | Two campuses, one shared workload, an exact optimum for a small case |

## 1. Plant sense: two sensors and a frame emitter

**The gap.** Two quantities in the contract have a limit and nothing that measures them: rack vibration
(0.0005 g, certified in funi-frame) and recooling temperature (41.5 °C at best, derived here). Nothing reads
any sensor into a frame. Weft's only temperature is a formula of CPU load (`host_metrics.py:45`).

**The system.** A sensor node per rack row (a MEMS accelerometer, band 10 to 200 Hz) and a temperature probe
on the recooling loop, each powered within the venturi-collars budget (0.080 mW per node at low airflow), and
a small emitter that packs the 16-slot plant frame defined in `verify.py`.

**First slice.** A bench rig: one accelerometer on a shaker and one temperature probe in a water bath. Record
an hour of frames. Done when `decode_plant_frame` reads every frame, the contract check reports the excursions
that were deliberately applied, and the node's measured power is within the collar's harvest.

**Rests on.** venturi-collars (power), impedence-analyzers (the leak channel can share the node), Weft's frame
layout. **Decision needed from Weft:** whether the plant frame shares its telemetry bus.

## 2. Load control with an energy reading

**The gap.** Neither Weft nor Exo can shed or defer compute on request, and neither measures the energy it
uses. A search of Weft's runtime, documents and experiment records finds no figure in watts or joules. Without
this the scheduler side of the contract has nothing to act on.

**The system.** Two calls on the compute side: `shed(fraction, seconds)` returns what was actually shed, and
`energy()` returns joules since the last call, read from the platform's power interface (RAPL on x86, the
power metrics interface on Apple Silicon). Both report into the plant frame's load slot.

**First slice.** One Weft experiment (the swarm benchmark already in weft-loom is a candidate) run with and
without a 50% shed request, with measured joules for each. Done when the measured energy falls by a stated
amount and the record is committed with its preregistration, under weft-loom's own rules.

**Rests on.** Weft's plasm and telemetry, weft-loom's experiment format. This would also be the first energy
measurement anywhere in the four organisations.

## 3. A model as the proposer

**The gap.** The loop's proposer is a seeded search. Nothing that learns takes part.

**The system.** The proposer becomes an interface: it receives the current genome, margins and the last
verdicts, and returns one proposed change. Any proposer can sit behind it. The gate and the ledger do not
change, and `run_safe` already holds for whatever is plugged in.

**First slice.** A recorded run in which a language model proposes each change through that interface, with
its prompts and replies kept beside the ledger. Done when the ledger replays in Lean with no mismatch and the
run is compared with the seeded search on the same budget. A second slice lets a Weft cell propose.

**Rests on.** `loop.py`, abios for the message format, the model's API. **Boundary:** the model proposes and
the gate decides. Nothing here gives a model authority to act.

**Status, v0.3.0.** The interface exists (`tools/propose.py`) and the first slice is done twice. A language
model made 11 proposals, 10 were taken up, and the ledger replays in Lean
([results/model_run.json](../results/model_run.json)). A second instance of the same model, given the first run's notes
([results/model_lessons.md](../results/model_lessons.md)), reached the same objective in 4. Open: many runs
with a stated protocol, so that a comparison means something; a Weft cell or an Exo agent as the proposer;
a format for the notes that a program can check; and an objective that does not drive the design onto a
limit, where it can no longer change.

## 4. Structural genes

**The gap.** The loop changes three thermal parameters. The eleven certified structural margins are constants
in it, because the verifiers that compute them take no inputs. So "evolving its hardware" covers a thermal
store, a capture fraction and a wall, and no member of the structure.

**The system.** Give each aska-physical verifier a parameter file with its design inputs and a `--inputs`
option, so that the loop can ask "what are the margins if the floor load is 5% higher". The margin vector
then moves with structural genes.

**First slice.** funi-frame's `verify.py` reads its roof and wall inputs from a file. The loop gains one gene,
the rack floor load, and re-runs funi-frame and funi-floors for each candidate. Done when a proposal that
raises the floor load past the punching collar's capacity is refused with the margin computed by the upstream
verifier and not by a scaling rule.

**Rests on.** funi-frame, funi-floors. This is also what makes the six hand-copied values in section 7 of the
model note unnecessary.

## 5. Specification review for the gate

**The gap.** The gate's proofs pass every mechanical item of the Proven Commons bar. Item 1 is open: the
specification has not been approved by a reviewer who did not write it, and the reviewer list in
Proven-Commons/mission is empty. An AI agent wrote the specification.

**The system.** None to build. A person reviews `formal/SPEC.md` and `formal/PlantGate/Spec.lean`, tries to
write a wrong gate that still meets the statements, and records the approval in `formal/bar.toml`.

**First slice.** Proven Commons names its first reviewers. One of them reviews this specification. Done when
`bar/check.py` reports item 1 as PASS.

**Rests on.** Proven-Commons/mission. A second step would prove Weft's own floating-point gate against the
exact one, which is Weft's open Milestone I.3.

## 6. Signed ledger and command channel

**The gap.** The ledger is hash-chained, so an edit is detected, but nothing says who wrote it. Weft's
telemetry hash is unkeyed and its roadmap calls it "integrity against accidents, not authentication". A plant
that takes requests from a scheduler needs to know who asked.

**The system.** Each ledger head and each budget grant is a Synmerit record, signed by the person who set the
budget. The gate's `run_bounded` theorem then has a named person behind the number it bounds.

**First slice.** The current `results/ledger.json` head, with its budget of 64, signed as a Synmerit bundle and
checked by Synmerit's conformance script. Done when a ledger with an altered budget fails that check.

**Rests on.** Synmerit v0.1. Its open issue on small-order keys should be closed first.

## 7. A first fabrication cell under the gate

**The gap.** The Terrafab documents describe machines that make the structure's own parts under the gate. No
machine exists in any repository.

**The system.** One real process with certified limits, run as a gated sequence of steps. The margins are the
process limits and the budget is the energy the step may use.

**First slice.** Joule activation of the Fe-SMA ties in one funi-floors cassette. The certificate gives the
energy (0.3227 kWh/m² against a cap of 0.5) and the target recovery stress. Model the activation as steps of
current and time, gate each step, and log it. Done on a model first, then on a coupon in a lab.

**Rests on.** funi-floors, cfrp-truss. **Boundary:** a model and then a supervised bench test. No autonomous
machine.

## 8. A network of campuses

**The gap.** The objective this repository was opened with names a network. Everything here is one campus.

**The system.** N campuses, each with its own load floor, thermal budget and margin radius, and a shared
workload. Placing work becomes an optimisation: most useful compute per unit of utility energy, subject to
every campus's gate.

**First slice.** Two campuses with different recooling temperatures and one workload with a daily cycle.
State the problem as a linear programme, solve it exactly, and check the answer against brute force on a
coarse grid. Done when the certificate holds the optimum and a must-fail control shows that the unconstrained
optimum breaks a load floor.

**Rests on.** The contract in this repository. funi-frame's open issue on dispatch against negative prices
is the natural second slice.

**Status, v0.3.0.** A first look is in the certificate (`network_first_look`, section 13 of the model note).
It changes the first slice. In the upstream plant model utility power is a straight line in IT load with the
same slope at every site (1.0357 MW per MW), so moving load between campuses changes no energy and the
linear programme has no single optimum. What does differ by site is the load floor: 0.564 MW at 30 °C
recooling and 2.804 MW at 38 °C, if the chiller keeps its design share of the reversible COP. So the
first slice should be one of: a loop COP that depends on the site, a choice to switch a campus off (which
no certificate covers), or a cost for moving work. The owners should pick.
