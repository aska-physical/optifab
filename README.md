# optifab

Modelling the ideal datacenter.

**Status: v0.3.2, claimed.** An AI agent wrote this version and no person has reviewed it. Nothing in it is
measured. Every number is derived from the certificates of other repositories, which are themselves models.

optifab is the design of one physical structure that holds the work of four organisations, so that the digital
and the physical infrastructure are a single unit. It treats a data-centre campus as one checked stack, from the
mathematics under its structure to the rule that governs the software running in it. The idea of one structure
comes from the Terrafab documents named in [issue 1](https://github.com/aska-physical/optifab/issues/1);
[docs/STRUCTURE.md](docs/STRUCTURE.md) gives every repository its place in the structure and shows which parts
of the loop are checked. [docs/VISION.md](docs/VISION.md) says how close this is to a formally verified system
that improves its own hardware and software, part by part. The work it joins:

- **aska-physical** designed the building, its thermal plant and its sensors
  ([funi-frame](https://github.com/aska-physical/funi-frame),
  [funi-floors](https://github.com/aska-physical/funi-floors),
  [venturi-collars](https://github.com/aska-physical/venturi-collars),
  [impedence-analyzers](https://github.com/aska-physical/impedence-analyzers)).
- **Foundation-0** holds the mathematics and physics those designs build on, and the scale that says how far a
  claim has been checked.
- **Moissanite-Labs** wrote the gate that decides whether an adaptive model may change itself
  ([weft](https://github.com/Moissanite-Labs/weft)).
- **Proven-Commons** sets the bar for calling software verified.

The reference campus is funi-frame's: 10 MW of IT load on a 2,500 m² plan, two storeys.

## What it finds

Each line is derived in [docs/MODEL.md](docs/MODEL.md) and recomputed by `verify.py`. Labels follow the
Foundation-0 standard: PROVEN (written proof, checked symbolically), VERIFIED (finite check).

| # | Finding | Label |
|---|---|---|
| 1 | **Less compute is unlocked than the plant certificate implied. Adopted upstream.** funi-frame v0.1.0 multiplied 3.06 MW of freed utility power by a value per MW of compute. The IT load that power can carry is 2.85 to 2.96 MW, depending on how much of the overhead grows with load, so its revenue figures were 3.6% to 7.4% high if the value is per MW of IT load. funi-frame v0.1.1 reports the IT power, and its certificate now agrees with the derivation here. Whether the value is per MW of IT load is still the owner's to confirm. | PROVEN, VERIFIED. Agreement with the upstream certificate is checked. |
| 2 | **The plant model left out a temperature that decides whether it works. Adopted upstream.** A sorption chiller with the claimed COP of 0.62, driven at 58 °C and making water at 15 to 18 °C, must reject heat below 41.5 °C at best (40.1 °C if the water is 15 °C). funi-frame v0.1.0 carried no recooling temperature. v0.1.1 carries the same limit, 41.46 °C, and a design recooling temperature of 30 °C, which it marks as a proposal awaiting the owner's confirmation. Nothing measures it. | PROVEN, VERIFIED. Agreement with the upstream certificate is checked. |
| 3 | **The workload has a load floor.** Below about 0.56 MW of IT load (5.6% of nameplate) the captured heat can no longer drive the chiller, and the campus stops cooling itself. With the steel-pinned wall that funi-frame rejects, the floor is 51% higher. | PROVEN under two stated assumptions |
| 4 | **Thermal storage is a budget.** The PCM skid holds 2,500 kWh_th: 15 minutes at full load, 30 minutes if half the load is shed, or a 10% burst for 2.5 hours. These count IT heat only, as funi-frame does. With the fixed heat load counted, the first figure is 14.69 minutes. | VERIFIED |
| 5 | **The tightest margin in the building is in the floor.** Of 11 certified limit states, the floor punching collar sits at 80.1% of capacity. A twelfth margin derived here, sensor power at low airflow, is at 77.0%. A change that moves the margin vector by no more than 0.1989 stays inside every limit. | PROVEN, VERIFIED |
| 6 | **One gate can guard weights and plant.** Weft's gate predicate, rewritten here, passes all 15 of Weft's weight-update vectors and agrees with Weft's own function on 100,000 generated cases. Until now its budget had no physical unit. Here the budget is finding 4 and the radius is finding 5. | VERIFIED. Its use on a plant is a proposal. |
| 7 | **Hand-copied numbers are now checked.** Six values are repeated by hand across funi-frame, funi-floors and venturi-collars. All six agree today, and a change upstream now fails a test. | VERIFIED |
| 8 | **The organisations' work is mapped, link by link.** 41 repositories and 43 links, each cited to a line at a pinned commit. Before this version the only thing joining aska-physical and Moissanite-Labs was issue 1 of this repository. | VERIFIED against pinned clones |
| 9 | **The physical stack is unreviewed.** Of its 13 repositories, 10 are claimed, 1 is a preprint and 2 claim no result. None is peer reviewed, replicated, deployed or formally verified. | VERIFIED. Levels for aska-physical repositories were assigned here. |
| 10 | **The contract fits in one 64-byte frame.** The 12 margins, the budget, the load, the recooling temperature and the time fill the 16 floats of the frame Weft already uses for telemetry. Since funi-frame v0.1.1 the design point fills the recooling slot from the certificate's design value, and a frame with that slot empty is reported as not measured. | VERIFIED. The slot meanings are a proposal. |
| 11 | **The Terrafab latency figures hold in direction, and this campus does not need them.** A 15 ms loop can counter none of the four plant vibration tones within its cycle; a 0.5 ms loop can counter all four. Passive isolation already holds rack vibration at 17.9% of its limit, and every term of the contract moves over seconds to minutes. | PROVEN (identity), VERIFIED |
| 12 | **Every repository has a place, and the loop is open.** 32 of 41 repositories are placed in the structure and 9 are listed as having no place. Of the 10 interfaces that would close the loop between structure and intelligence, 4 are checked. | VERIFIED (the accounting). Statuses were assigned here. |
| 13 | **The gate and the loop over designs are proved in Lean, with the plant model inside the proved code.** Sixteen theorems, accepted by `lake comparator --paranoid` under six kernels. Eight are about an exact integer gate. Eight are about designs, with the three moving margins and the objective computed inside the proved code. From a start within its limits and bounds, whatever designs are proposed, the design held stays within every modelled limit and within its bounds, its objective never falls, and the number of changes is at most the budget a person set. The model itself is defined, not proved. An independent read found five defects in it. v0.3.1 fixes two and part of a third, and [formal/SPEC.md](formal/SPEC.md) lists what is still open. The Proven Commons bar check passes items 2 to 6. It is not verified: no reviewer has approved the specification. | Machine-checked proof. Bar item 1 open. |
| 14 | **Hardware and software improve together under that gate.** A loop proposed 48 changes to three hardware and two software parameters. 45 were admitted (31 hardware, 14 software) and 3 refused. The objective rose from 0.914210 to 0.918990 and never fell, and every decision was worked out again in Lean from the two designs with no mismatch. It runs on a model: no sensor, load or machine is involved. | VERIFIED on a model. The scenario is a choice, so the figures are illustrations. |
| 15 | **A design that sits exactly on a limit cannot change.** Started with one margin at its limit, the loop admitted nothing. A proposer with no reserve had 99 of 161 proposals refused and finished lower. Headroom is what makes change possible. | VERIFIED on a model |
| 16 | **A margin within its limit means a physical inequality, with no rounding in it.** Proved for every design the loop can reach from a start within its limits: the captured heat can drive the cooling needed at full load, the plant cools itself at the scheduler's load floor, and the store holds the heat of one outage. The first follows from the second for any floor up to the IT load, so these are two independent facts, not three. This is a statement about the model. Its constants are claimed, not measured. | Machine-checked proof about a model |
| 17 | **A language model has proposed through the same interface, and a second run built on the first one's notes.** Given only the loop's printed state, the first made 12 proposals in a limit of 40. 7 were taken up, 2 of them changing hardware and software in one step. The objective reached 0.919529, the best a direct search finds possible. The seeded search reached 0.918990 (89.9%) with 48 proposals. A second instance of the same model, with no memory of the first run, was given the notes the first left. It reached 0.919529 in 5 proposals with 0 refused. Both runs were made again for v0.3.1, against the corrected model. The runs made against v0.3.0 are kept in [results/v0.3.0/](results/v0.3.0/): only 2 of their 15 proposals would be decided the same way now. | VERIFIED (the replays). Two runs are anecdotes, not an experiment. |
| 18 | **An adversary cannot move the design out of its envelope.** 3,006 proposals built to break the loop: genes out of bounds, margins past limits, designs that score lower, then random ones. 64 were taken up, which is the whole budget, and no more. Every design held stayed within every limit and every bound, and the objective never fell. | VERIFIED on the Python copy. The property itself is proved in Lean. |
| 19 | **A campus's load floor is a property of its site.** If the chiller keeps its design share of the reversible COP, the floor is 0.564 MW with recooling at 30 °C, 2.804 MW at 38 °C and 6.113 MW at 40 °C. At 41 °C the campus cannot cool itself at any load, though 41 °C is under the limit of finding 2. One cool and one warm campus cannot idle below 3.368 MW, 16.8% of their nameplate. In the plant model, moving load between campuses changes no energy, so a placement optimum needs a model with a site-dependent cost first. | VERIFIED under assumption A-4 |

Findings 1 and 2 concern funi-frame and are written up for its maintainers in [HANDOFF.md](HANDOFF.md).

## The contract between plant and workload

The findings add up to an interface. A scheduler that places work on this campus should respect four things,
and can rely on four in return.

| The workload must | The plant offers, per its certificates |
|---|---|
| keep IT load above the load floor, or ask for the air-side load to move to the aquifer loop | PUE 1.074 and no water use, if recooling stays below about 41 °C |
| charge every cooling outage and every burst above cooling capacity to the thermal budget | 15 minutes of ride-through at full load, counting IT heat only |
| keep the margin vector within 0.1989 of the certified design point | rack vibration at 17.9% of the switch limit |
| plan capacity in IT power, not in utility power | 2.85 to 2.96 MW more IT load than a conventional plant on the same supply |

The left column is what `plant_gate` checks. All of the right column is claimed, not measured.

## Check it

Needs Python 3.10 or newer and SymPy. The certificate is the same under Python 3.10, 3.11, 3.12, 3.13 and 3.14
with SymPy 1.14, and CI checks each of them. Other SymPy versions, and platforms other than Linux on
x86-64, are untested here.

```bash
pip install sympy
python3 verify.py
```

This recomputes every figure from the pinned inputs, runs the improvement loop, replays the recorded runs, runs 29 must-fail controls, and
compares the result with [results/certificate.json](results/certificate.json) and the two ledgers in
[results/](results/). It reads no network and needs no Lean. Its checks are not `assert` statements, so `python3 -O` does not switch
them off. It checks that the committed
formal record matches the current Lean sources and ledger.

To rebuild the proofs and replay the ledger in Lean (needs Linux, [elan](https://github.com/leanprover/elan)
and bubblewrap):

```bash
python3 verify.py --formal
# [FORMAL] comparator accepts 16 theorems under 6 kernels; 405000 differential tests, 0 failures;
#          ledger replay 3072 decisions, 0 mismatches
```

To propose a design yourself, or to let a model do it:

```bash
python3 tools/propose.py my_run.json new
python3 tools/propose.py my_run.json try pcm_kwh=2700 shed_ppm=250000 --why "more store, so shed less"
```

To re-read every cited line from the source repositories:

```bash
python3 tools/fetch_upstream.py ../upstream     # clones 36 public repositories at their pinned commits
python3 verify.py --upstream ../upstream
```

## What a pass does not show

- That the building would behave as modelled. No input is a measurement.
- That the upstream certificates are right. funi-frame's verifier was re-run here and reproduces its
  certificate. The verifiers of funi-floors and venturi-collars were not re-run. Weft's gate module is run, as
  the oracle of the differential test.
- Anything about more than one campus. A network of campuses is the next step, not this one.
- That the gate is safe to put in control of a plant. Its arithmetic is proved. The margins it is fed are not,
  and it can only refuse a step. Nothing here commands anything.
- That the loop's gains are real. The loop is proved to keep its model within the model's limits. The model's
  constants, the objective and the scenario are choices, and none is measured. Two mistakes in the model were
  corrected in v0.3.1, and [formal/SPEC.md](formal/SPEC.md) lists the defects that are still open.
- That a language model is a good proposer, or that notes always help the next one. Two recorded runs show
  the interface and the hand-over work. They measure nothing.
- Anything the Terrafab documents claim. They are the source of the idea and are not used as evidence.

## Layout

```
verify.py                 the verifier: derivations, the gates, the frame, the loop, graph and unit checks, 29 must-fail controls
loop.py                   the improvement loop: the seeded proposer, the replay of recorded proposals, the ledger
formal/                   the exact gate, the plant model and the loop, proved in Lean, in the Proven Commons layout
results/certificate.json  what verify.py must reproduce
results/ledger.json       every decision of the loop, hash-chained
results/model_run.json    the proposals a language model made through the interface, each with its reason
results/model_ledger.json the decisions on them, hash-chained
results/model_lessons.md  the notes that proposer left, word for word
results/v0.3.0/           the same three kinds of file for the runs made against the model of v0.3.0, kept as they were
results/model_run_2.json  a second run, by an instance that was given those notes; model_ledger_2.json and
                          model_lessons_2.md are its ledger and its own notes
results/formal.json       the record of the last formal run: comparator, differential tests, Lean replay
data/upstream/            byte-exact copies of three certificates, Weft's vectors and Weft's gate (the test oracle)
data/pins.json            every literal and line read from another repository
data/graph.json           the cross-organisation map: repositories, links, citations
data/unit.json            the structure: each element, where it sits, whose work it rests on, and its status
data/sources.json         pinned commit and file hashes for each repository
docs/VISION.md            how close this is to the vision, part by part
docs/PROPOSALS.md         eight systems proposed for the open gaps, and how far each has got
docs/STRUCTURE.md         one structure: the unit, the loop, the plant frame, and the Terrafab claims one by one
docs/MODEL.md             each result, its derivation and its assumptions
docs/CONVERGENCE.md       the map as tables, generated from data/graph.json
tools/                    propose.py (the proposer's command line), fetch_upstream.py and render_map.py
HANDOFF.md                what was learned, what failed, and what to do next
```

## Licence

Noncommercial use is allowed. Commercial use needs the owner's written permission.

- Code: [PolyForm Noncommercial License 1.0.0](LICENSE).
- Text and data: [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE-docs).
- Files from other projects keep their own licences. [NOTICE](NOTICE) lists them.

## Credit and disclosure

- The certificates, designs and theorems used here belong to the repositories named above and their authors.
  [docs/CONVERGENCE.md](docs/CONVERGENCE.md) lists each one with its commit.
- Weft's conformance vectors and gate module are copied under the Apache License 2.0, and short passages of the Weft corpus are
  quoted under CC BY 4.0. See [NOTICE](NOTICE).
- This version was prepared by an AI agent (Claude, Anthropic) working for the owner of aska-physical. Under the
  Foundation-0 rule that a person signs, nothing here counts until a named person has reviewed it.
