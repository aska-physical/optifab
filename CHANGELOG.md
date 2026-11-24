# Changelog

Machine-checked milestones for `aska-physical/optifab`.

## [0.3.1] - 2026-11-24

Corrects the plant model. An independent read of v0.3.0 found five defects in it (issue 14). This version
fixes two and part of a third. Every objective figure and the outage margin change.

### Fixed

- **The objective's outage term.** It subtracted the whole utility power of the shed load during an outage,
  including the part that does not depend on load, so an outage with nothing shed raised the objective. It now
  subtracts only what the shed load would have drawn. Every objective is about 18 ppm lower: the start is
  0.914210 (was 0.914228).
- **The outage margin left out the fixed heat load**, about 71 kWh in a twenty-minute outage. It is now counted.
  The start design's outage margin is 961,695 ppm (was 933,334), which makes it the tightest margin at the
  start and cuts the first radius from 59,652 to 38,305 ppm.
- **A proposal identical to the design held was taken up and charged.** It is now refused as `same`. New
  theorem `same_design_not_taken_up`, sixteen in all. `step_complete` gains the hypothesis that the proposed
  design differs from the one held.

### Changed

- The seeded run: 45 of 48 proposals admitted, objective 0.914210 to 0.918990 (was 45 of 50, 0.914228 to 0.919009).
- **Both recorded runs were made again.** Replayed under the corrected model, only 2 of the 15 proposals
  recorded against v0.3.0 are decided the same way, so those runs could not be carried over. They are kept
  unchanged in `results/v0.3.0/`. The new first run made 12 proposals and reached 0.919529; the new second run,
  given the first one's notes, made 5 and reached 0.919529. The best a direct search finds is 0.919529.
- The variant that starts with a margin exactly on its limit now uses a wall of 125 mW/m²K and 27.1236% shed,
  which puts the corrected outage margin at exactly 1,000,000 ppm.
- The adversarial proposer also sends a proposal that changes nothing, and expects `same`.
- `plant.thermal_budget` gains the full-load ride-through with the fixed heat load counted: 14.69 minutes
  against funi-frame's 15.

### Still open

Three of the five defects need a design decision and are unchanged: a different design that scores the same
is taken up, nothing requires the inputs to make sense, and the loop can refuse a safer design and cannot
repair an unsafe start. `formal/SPEC.md` lists them.

## [0.3.0] - 2026-11-17

The proof now covers the plant model and the loop over designs, and two new proposers have used the loop.

### Added

- **The plant model in Lean.** `formal/PlantGate.lean` holds the model that turns a design into margins and an
  objective, the bounds on each gene, and the step that takes a design up. Seven theorems about designs
  (`step_complete`, `step_refusal_changes_nothing`, `loop_safe`, `loop_in_bounds`, `loop_never_worse`,
  `loop_bounded`, `loop_keeps_physics`) join the eight about the gate. `lake comparator --paranoid` accepts all
  fifteen under six kernels.
- **A whole-run mode in the Lean executable.** A line starting with `l` goes through the proved `loop` and
  `changes`. `--formal` runs each of the four ledgers through it in one piece as well as decision by decision,
  and `loop.check_continuity` checks that each ledger entry starts from the outcome of the one before.
- **A proposer's command line**, `tools/propose.py`, and `loop.run_proposals`, which replays any recorded list
  of proposals.
- **A recorded run by a language model** (`results/model_run.json`, `results/model_ledger.json`): 11 proposals,
  10 taken up, objective 0.919548. Its closing notes are in `results/model_lessons.md`.
- **A second recorded run**, by a model given those notes (`results/model_run_2.json`): the same objective in
  4 proposals. Its notes are in `results/model_lessons_2.md`.
- **An adversarial proposer** (3,006 proposals) and a **first look at a network** (assumption A-4, section 13
  of the model note).
- Must-fail controls 25 to 29. Findings 16 to 19 in the README.

### Fixed

- **`python3 -O verify.py` skipped every check.** The verifier's 21 checks were `assert` statements, which
  Python strips under `-O`: a failing control wrote a certificate and exited 0. They are now calls to
  `require()`, which raises `RuntimeError` whatever the flags. Must-fail control 29 fails if an `assert`
  statement appears in any of this repository's own Python files. Found by the review of pull request 13.
  This defect was also in v0.1.0 and v0.2.0.
- **The certificate depended on the Python version.** The differential test built its boundary cases with the
  builtin `sum()`, which rounds floats differently from Python 3.12 on. Under 3.11 two tallies in
  `gate.differential_test.agreed_by_reason` differed from the committed ones by 103 cases, and
  `python3 verify.py` reported a mismatch. The sums are now added left to right, as the gates add them, so the
  boundary cases sit exactly on the gate's own distance in every version. The tallies change once (`ok` 41,772
  to 41,875, `baseline_distance_exceeded` 18,444 to 18,341). Mismatches stay at 0. CI now runs the verifier
  under Python 3.10 to 3.14. Reported in the review of pull request 13. This defect was also in v0.1.0 and
  v0.2.0.
- The docstring of `verify.py` said v0.2.0.

### Known defects

An independent read by a separate agent found five defects in the plant model, listed in `formal/SPEC.md` and
in section 11 of the model note. The two that change numbers: the objective is about 18 ppm too high for every
design, and the outage margin leaves out the fixed heat load. They are disclosed and not fixed in this version.
The same read found prose that claimed more than the statements say. That prose is corrected.

### Changed

- `loop.py` computes margins and the objective with the exact model in `formal/tests/oracle.py` in place of
  floating point. The figures of the seeded run are unchanged.
- The ledger records both designs of every decision. `--formal` replays three ledgers (3,071 decisions) by
  giving Lean the designs, so the margins, the objective, the verdict and the budget are all worked out again.
- The step over designs refuses a design outside the bounds (`bounds`) and one that lowers the objective
  (`worse`), in addition to the gate's refusals.
- Differential tests: 405,000 inputs (300,000 gate decisions, 100,000 proposed designs and 5,000 whole runs).
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
