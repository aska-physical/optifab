# optifab

Modelling the ideal datacenter.

**Status: v0.2.0, claimed.** An AI agent wrote this version and no person has reviewed it. Nothing in it is
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

## What v0.1.0 finds

Each line is derived in [docs/MODEL.md](docs/MODEL.md) and recomputed by `verify.py`. Labels follow the
Foundation-0 standard: PROVEN (written proof, checked symbolically), VERIFIED (finite check).

| # | Finding | Label |
|---|---|---|
| 1 | **Less compute is unlocked than the plant certificate implies.** funi-frame multiplies 3.06 MW of freed utility power by a value per MW of compute. The IT load that power can carry is 2.85 to 2.96 MW, depending on how much of the overhead grows with load. If the value is per MW of IT load, its revenue figures are 3.6% to 7.4% high. | PROVEN, VERIFIED |
| 2 | **The plant model leaves out a temperature that decides whether it works.** A sorption chiller with the claimed COP of 0.62, driven at 58 °C and making water at 15 to 18 °C, must reject heat below 41.5 °C at best (40.1 °C if the water is 15 °C). No recooling temperature appears in the certificate. | PROVEN, VERIFIED |
| 3 | **The workload has a load floor.** Below about 0.56 MW of IT load (5.6% of nameplate) the captured heat can no longer drive the chiller, and the campus stops cooling itself. With the steel-pinned wall that funi-frame rejects, the floor is 51% higher. | PROVEN under two stated assumptions |
| 4 | **Thermal storage is a budget.** The PCM skid holds 2,500 kWh_th: 15 minutes at full load, 30 minutes if half the load is shed, or a 10% burst for 2.5 hours. | VERIFIED |
| 5 | **The tightest margin in the building is in the floor.** Of 11 certified limit states, the floor punching collar sits at 80.1% of capacity. A twelfth margin derived here, sensor power at low airflow, is at 77.0%. A change that moves the margin vector by no more than 0.1989 stays inside every limit. | PROVEN, VERIFIED |
| 6 | **One gate can guard weights and plant.** Weft's gate predicate, rewritten here, passes all 15 of Weft's weight-update vectors and agrees with Weft's own function on 100,000 generated cases. Until now its budget had no physical unit. Here the budget is finding 4 and the radius is finding 5. | VERIFIED. Its use on a plant is a proposal. |
| 7 | **Hand-copied numbers are now checked.** Six values are repeated by hand across funi-frame, funi-floors and venturi-collars. All six agree today, and a change upstream now fails a test. | VERIFIED |
| 8 | **The organisations' work is mapped, link by link.** 41 repositories and 43 links, each cited to a line at a pinned commit. Before this version the only thing joining aska-physical and Moissanite-Labs was issue 1 of this repository. | VERIFIED against pinned clones |
| 9 | **The physical stack is unreviewed.** Of its 13 repositories, 10 are claimed, 1 is a preprint and 2 claim no result. None is peer reviewed, replicated, deployed or formally verified. | VERIFIED. Levels for aska-physical repositories were assigned here. |
| 10 | **The contract fits in one 64-byte frame.** The 12 margins, the budget, the load, the recooling temperature and the time fill the 16 floats of the frame Weft already uses for telemetry. The design point as certified cannot fill the recooling slot. | VERIFIED. The slot meanings are a proposal. |
| 11 | **The Terrafab latency figures hold in direction, and this campus does not need them.** A 15 ms loop can counter none of the four plant vibration tones within its cycle; a 0.5 ms loop can counter all four. Passive isolation already holds rack vibration at 17.9% of its limit, and every term of the contract moves over seconds to minutes. | PROVEN (identity), VERIFIED |
| 12 | **Every repository has a place, and the loop is open.** 32 of 41 repositories are placed in the structure and 9 are listed as having no place. Of the 10 interfaces that would close the loop between structure and intelligence, 4 are checked. | VERIFIED (the accounting). Statuses were assigned here. |
| 13 | **The gate and the loop built on it are proved in Lean.** Eight theorems about an exact integer gate, accepted by `lake comparator --paranoid` under six kernels. Whatever is proposed, no margin passes its limit and the budget is never overdrawn; the number of changes is at most the budget a person set. The Proven Commons bar check passes items 2 to 6. It is not verified: no reviewer has approved the specification. | Machine-checked proof. Bar item 1 open. |
| 14 | **Hardware and software improve together under that gate.** A loop proposed 50 changes to three hardware and two software parameters. 45 were admitted (30 hardware, 15 software) and 5 refused. The objective rose from 0.914228 to 0.919009 and never fell, and every decision was replayed in Lean with no mismatch. It runs on a model: no sensor, load or machine is involved. | VERIFIED on a model. The scenario is a choice, so the figures are illustrations. |
| 15 | **A design that sits exactly on a limit cannot change.** Started with one margin at its limit, the loop admitted nothing. A proposer with no reserve had 126 of 186 proposals refused and finished lower. Headroom is what makes change possible. | VERIFIED on a model |

Findings 1 and 2 concern funi-frame and are written up for its maintainers in [HANDOFF.md](HANDOFF.md).

## The contract between plant and workload

The findings add up to an interface. A scheduler that places work on this campus should respect four things,
and can rely on four in return.

| The workload must | The plant offers, per its certificates |
|---|---|
| keep IT load above the load floor, or ask for the air-side load to move to the aquifer loop | PUE 1.074 and no water use, if recooling stays below about 41 °C |
| charge every cooling outage and every burst above cooling capacity to the thermal budget | 15 minutes of ride-through at full load |
| keep the margin vector within 0.1989 of the certified design point | rack vibration at 17.9% of the switch limit |
| plan capacity in IT power, not in utility power | 2.85 to 2.96 MW more IT load than a conventional plant on the same supply |

The left column is what `plant_gate` checks. All of the right column is claimed, not measured.

## Check it

Needs Python 3.10 or newer and SymPy. Tested with Python 3.13 and SymPy 1.14 only.

```bash
pip install sympy
python3 verify.py
```

This recomputes every figure from the pinned inputs, runs the improvement loop, runs 24 must-fail controls, and
compares the result with [results/certificate.json](results/certificate.json) and
[results/ledger.json](results/ledger.json). It reads no network and needs no Lean. It checks that the committed
formal record matches the current Lean sources and ledger.

To rebuild the proofs and replay the ledger in Lean (needs Linux, [elan](https://github.com/leanprover/elan)
and bubblewrap):

```bash
python3 verify.py --formal
# [FORMAL] comparator accepts 8 theorems under 6 kernels; 300000 differential tests, 0 failures;
#          ledger replay 50 decisions, 0 mismatches
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
- That the loop's gains are real. Its plant model, objective and scenario are unproved choices.
- Anything the Terrafab documents claim. They are the source of the idea and are not used as evidence.

## Layout

```
verify.py                 the verifier: derivations, the gates, the frame, the loop, graph and unit checks, 24 must-fail controls
loop.py                   the improvement loop: genome, plant model, proposer, ledger
formal/                   the exact gate and the loop, proved in Lean, in the Proven Commons layout
results/certificate.json  what verify.py must reproduce
results/ledger.json       every decision of the loop, hash-chained
results/formal.json       the record of the last formal run: comparator, differential tests, Lean replay
data/upstream/            byte-exact copies of three certificates, Weft's vectors and Weft's gate (the test oracle)
data/pins.json            every literal and line read from another repository
data/graph.json           the cross-organisation map: repositories, links, citations
data/unit.json            the structure: each element, where it sits, whose work it rests on, and its status
data/sources.json         pinned commit and file hashes for each repository
docs/VISION.md            how close this is to the vision, part by part
docs/PROPOSALS.md         eight systems proposed for the open gaps
docs/STRUCTURE.md         one structure: the unit, the loop, the plant frame, and the Terrafab claims one by one
docs/MODEL.md             each result, its derivation and its assumptions
docs/CONVERGENCE.md       the map as tables, generated from data/graph.json
tools/                    fetch_upstream.py and render_map.py
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
