# Changelog

Machine-checked milestones for `aska-physical/optifab`.

## [0.3.0] - 2026-11-17

The proof now covers the plant model and the loop over designs, and two new proposers have used the loop.

### Added

- **The plant model in Lean.** `formal/PlantGate.lean` holds the model that turns a design into margins and an
  objective, the bounds on each gene, and the step that takes a design up. Six theorems about designs
  (`step_complete`, `loop_safe`, `loop_in_bounds`, `loop_never_worse`, `loop_bounded`, `loop_keeps_physics`)
  join the eight about the gate. `lake comparator --paranoid` accepts all fourteen under six kernels.
- **A proposer's command line**, `tools/propose.py`, and `loop.run_proposals`, which replays any recorded list
  of proposals.
- **A recorded run by a language model** (`results/model_run.json`, `results/model_ledger.json`): 11 proposals,
  10 taken up, objective 0.919548. Its closing notes are in `results/model_lessons.md`.
- **A second recorded run**, by a model given those notes (`results/model_run_2.json`): the same objective in
  4 proposals. Its notes are in `results/model_lessons_2.md`.
- **An adversarial proposer** (3,006 proposals) and a **first look at a network** (assumption A-4, section 13
  of the model note).
- Must-fail controls 25 to 27. Findings 16 to 19 in the README.

### Changed

- `loop.py` computes margins and the objective with the exact model in `formal/tests/oracle.py` in place of
  floating point. The figures of the seeded run are unchanged.
- The ledger records both designs of every decision. `--formal` replays three ledgers (3,071 decisions) by
  giving Lean the designs, so the margins, the objective, the verdict and the budget are all worked out again.
- The step over designs refuses a design outside the bounds (`bounds`) and one that lowers the objective
  (`worse`), in addition to the gate's refusals.
- Differential tests: 400,000 inputs (300,000 gate decisions and 100,000 proposed designs).
- `results/formal.json` holds one hash per ledger.

## [0.2.0] - 2026-11-17

Status: claimed. Prepared by an AI agent; not reviewed by a person. Nothing is called verified.

### Added

- **`formal/`**: a Lean 4 project with no dependencies, in the Proven Commons layout. An exact integer gate,
  the generation step and the loop over any list of proposals, with eight theorems. `lake comparator
  --paranoid` accepts them under six kernels. 300,000 differential tests against the Python oracle agree. The
  Proven Commons bar check reports items 2 to 6 PASS and item 1 OPEN (`formal/BAR-REPORT.md`).
- **`loop.py`**: the improvement loop. Three hardware genes, two software genes and the proposer's own step
  scale, changed one gated step at a time. On the scenario in the file: 50 proposals, 45 admitted (30
  hardware, 15 software), objective 0.914228 to 0.919009.
- **`results/ledger.json`** and **`results/formal.json`**: the hash-chained record of every decision, and the
  record of the last formal run. `verify.py --formal` rebuilds the proofs and replays the ledger in Lean
  (50 decisions, 0 mismatches). The plain verifier fails if that record does not match the current Lean
  sources and ledger.
- **`docs/VISION.md`**: how close this is to a formally verified system that improves its own hardware and
  software, part by part. **`docs/PROPOSALS.md`**: eight systems for the open gaps.
- **Licences**: PolyForm Noncommercial 1.0.0 for code, CC BY-NC 4.0 for text and data.
- **Two workflows**: the Proven Commons bar check on `formal/`, and a rerun of `verify.py`.
- Five must-fail controls (24 in all). The unit now has 30 elements and 10 loop interfaces, 4 of them checked.

## [0.1.0] - 2026-11-17

First version. Status: claimed. Prepared by an AI agent; not reviewed by a person.

### Added

- **`verify.py` and `results/certificate.json`.** One command recomputes every figure from pinned inputs and
  runs 19 must-fail controls. Five identities are checked symbolically with SymPy.
- **`docs/STRUCTURE.md` and `data/unit.json`**: one structure. Every repository on the map is placed in the
  physical unit or listed as having no place: 32 placed, 9 not. The loop between structure and intelligence has
  9 interfaces, of which 3 are checked. The idea comes from the Terrafab documents named in issue 1.
- **Plant frame**: the contract's state in the 64-byte layout of Weft's telemetry frame, with a contract check
  that reads one frame.
- **Loop timing**: the two latencies quoted in the Terrafab documents, tried on the four plant vibration tones
  in funi-frame's isolation model.
- **Plant envelope**, from the funi-frame certificate and the literals in its verifier:
  - extra IT load at a fixed utility supply: 2.854 to 2.959 MW, against 3.06 MW of freed utility power;
  - recooling limit of the sorption stage: 41.5 °C at 18 °C chilled water, 40.1 °C at 15 °C;
  - load floor for self-cooling: 0.564 MW with the certified wall, 0.850 MW with a steel-pinned wall;
  - thermal budget: 2,500 kWh_th, with the load to shed for outages of 10 to 60 minutes.
- **Margin vector** of 12 limit states from funi-frame, funi-floors and venturi-collars (11 certified upstream,
  1 derived here), and the plant radius 0.1989 set by the floor punching collar.
- **`plant_gate`**, a re-implementation of the Weft I3 predicate. It passes Weft's 15 weight-update vectors,
  agrees with Weft's own function on 100,000 generated cases, and is run on five plant cases.
- **Interface checks** on six values repeated by hand across repositories.
- **`data/graph.json`**: 41 repositories and 43 cited links across aska-physical, Foundation-0,
  Moissanite-Labs and Proven-Commons, with lineage checked to be acyclic and within Weft's depth bound of 12.
  The first links in repository contents between aska-physical and Moissanite-Labs.
- **`data/pins.json` and `data/sources.json`**: 48 pins and the commits of 36 repositories with the hashes of
  every cited file.
  `verify.py --upstream ROOT` re-reads every cited line.
- **`docs/MODEL.md`**, **`docs/CONVERGENCE.md`** (generated), **`HANDOFF.md`**, **`NOTICE`**, and the tools
  `fetch_upstream.py` and `render_map.py`.
