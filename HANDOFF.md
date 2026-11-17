# Handoff: aska-physical/optifab v0.2.0

Written under the group ethos: leave everything the next agent needs so nothing has to be derived twice.

optifab v0.1.0 and v0.2.0 were prepared by an AI agent on 2026-11-17. They are claimed work. No person has
reviewed them.

## 1. What was learned and checked

The aim, stated by the owner and in [issue 1](https://github.com/aska-physical/optifab/issues/1), is one
physical structure that holds all four organisations' work, with digital and physical infrastructure as a
single unit. [docs/STRUCTURE.md](docs/STRUCTURE.md) is the design of that unit as far as it can be checked today.

The fifteen findings are in [README.md](README.md) and derived in [docs/MODEL.md](docs/MODEL.md). In one line each:

1. The 3.06 MW of utility power that funi-frame's plant frees carries 2.85 to 2.96 MW of IT load, depending on
   how much of the overhead grows with load.
2. The sorption stage needs a heat sink below 41.5 °C at best to reach its claimed COP. The plant model has no
   recooling temperature.
3. The campus stops cooling itself below about 0.56 MW of IT load. A worse wall raises that floor.
4. The PCM skid is a budget of 2,500 kWh_th that outages and bursts draw on.
5. The tightest certified margin in the building is the floor punching collar, at 80.1%.
6. Weft's gate predicate, rewritten here, passes Weft's 15 weight-update vectors, agrees with Weft's own
   function on 100,000 generated cases, and can take the plant's budget and margin radius as its inputs.
7. Six hand-copied values across three repositories agree and are now under test.
8. The four organisations' relevant work is one cited graph of 41 repositories and 43 links.
9. The physical stack is at "claimed" on the Ledger scale, with one preprint.
10. The contract's whole state fits the 64-byte frame Weft uses for telemetry.
11. The Terrafab latency figures hold in direction for the plant's vibration tones, and the campus as designed
    does not need a fast loop.
12. 32 of 41 repositories have a place in the structure. Of the 10 interfaces that would close the loop between
    structure and intelligence, 4 are checked, and the loop is open in three places.
13. An exact integer gate and the loop built on it are proved in Lean (eight theorems, six kernels, standard
    axioms). The Proven Commons bar check passes items 2 to 6. Item 1, a reviewer's approval, is open.
14. A loop changed three hardware and two software parameters together under that gate: 45 of 50 proposals
    admitted, the objective up from 0.914228 to 0.919009, every decision replayed in Lean.
15. A design that sits exactly on a limit cannot change under this gate, and a proposer with no reserve slows
    itself.

[docs/VISION.md](docs/VISION.md) sets these against the vision, part by part.

## 2. Negative findings. Do not re-derive.

1. **There is no energy data on the digital side.** A search of Weft's runtime, documents and papers, and of
   weft-loom's experiments and notes, finds no figure in watts, joules or kWh and no PUE. Weft's only
   temperature is a formula of CPU load (`weft/runtime/telemetry/host_metrics.py:45`). weft-loom lists "energy
   per adapter write" as a measurement still to make. exo-os quotes small-device power figures from outside
   sources under the line "Do not trust any mW number without a test." So tokens per joule, or energy per model
   update, cannot be computed from anything the four organisations hold today. It has to be measured.
2. **One lattice link is closed, and the others are only proposals.** incentre-lattices, fibral-rigidity and
   siliquant all work with lattices, which suggests a shared result. siliquant checked whether the certificate
   coefficients of incentre-lattices bear on weight rounding and recorded "Real, unrelated"
   (`siliquant/notes/brief-check.md:39`). The graph keeps that link with type `checked_unrelated`. The same
   note lists its other links to the lattice tracks as proposals that were not evaluated. Do not present any of
   them as a result without a construction.
3. **Two upstreams of venturi-collars hold no results.** Foundation-0/ductricity is a project definition and
   Foundation-0/thermal-capture is a research direction. Both say so. venturi-collars inherits a question from
   them, not evidence. The graph marks these links `direction`.
4. **The liquid capture fraction has no optimum to find.** In funi-frame's model more capture is always better:
   the drive heat needed falls and the surplus rises. There is nothing to optimise there.
5. **The second-law bound cannot confirm the COP, only limit it.** It says where 0.62 is impossible. Whether a
   real machine reaches 0.62 at a 58 °C drive needs a manufacturer's curve.
6. **The Ledger scale does not fit runtime code.** Weft, abios, synbios and the like are tested software, not
   research claims. They are left unrated here.
7. **Lineage by repository over-reaches.** Weft builds on Foundation-0/project-asma in its identifiability gate,
   a different module from the one optifab uses. For that reason the evidence table covers only the physical
   layers, L0 to L3.
8. **Only the gate predicate carries over from Weft.** Weft's default radius of 120, its tension bound and its
   royalty split have no meaning for a plant. The 12 vectors that test them are out of scope.

9. **The Terrafab documents are not evidence, and Weft has already audited them.** Do not audit them again.
   Weft's digest (`weft/docs/corpus/sources/B-top1.md`) records that the latency figures are asserted (line
   220), that the benchmark is rigged (line 142), that the Lean proofs they cite do not exist, and that the
   gate header neither keeps its own invariant nor bounds a physical quantity (line 227). Weft repaired that
   header into the gate it ships (`invariants.py:11`). optifab uses the idea of one structure and the repaired
   gate, and nothing else from those documents.
10. **This campus has no job for a sub-millisecond loop.** Passive isolation holds rack vibration at 17.9% of the
    limit and every term of the contract moves over seconds to minutes. A fast loop matters only for active
    vibration control or a fabrication machine, and neither exists.
11. **No fabrication machine exists anywhere.** The "hands" of the Terrafab loop are an idea. The nearest real
    inputs are process limits already in the certificates, such as the Fe-SMA activation energy in funi-floors
    (0.3227 against a cap of 0.5 kWh/m²).

12. **The loop's proposer is not an intelligence, and its gains are not predictions.** It is a seeded search on
    a three-parameter thermal model, scored on a scenario chosen here. What carries over is the mechanism and
    the behaviours in finding 15, not the 0.5%.
13. **Do not name the gate function `admit` in Lean.** `admit` is Lean's keyword for an unfinished proof, and
    the Proven Commons checker rightly flags every use. The function is `gate`.
14. **The comparator needs bubblewrap, and the bar check needs every definition a statement uses to be listed**
    in `bar.toml`, constructors and projections included (`Verdict.ok`, `Outcome.verdict`, `Outcome.remaining`).

## 3. Notes for upstream maintainers

These concern other repositories. Nothing was changed there except the profile fix in item 4.

These three funi-frame notes are implemented in aska-physical/funi-frame#4 (draft). When it merges,
optifab's verifier fails on purpose (must-fail control 1 and the recooling-field check), because findings 1 and
2 will then be out of date: refresh the vendored certificate, run `--repin`, and restate them.

1. **funi-frame, compute revenue.** `results/certificate.json` reports `freed_substation_power_MW` of 3.06 and
   `unlocked_annual_revenue_low_M_usd` of 76.62, the product of that power and $25M per MW-year
   (`verify.py:162-163`). The power is utility power. The IT load it supports is 2.854 MW if every overhead
   grows with load and 2.959 MW if only the aquifer loop does, which is how the verifier models it. The low-end
   revenue on that is $71.35M to $73.97M. Suggested change: report the extra IT power, say which kind of MW the
   dollar value refers to, and compute the revenue from the matching figure.
2. **funi-frame, recooling temperature.** The sorption COP of 0.62 is a literal (`verify.py:144`) with no
   temperature attached. Suggested change: carry the drive, recooling and chilled-water temperatures in the
   certificate, make the COP depend on them, and add a must-fail control for dry recooling on a hot day.
3. **funi-frame, controls that compare constants.** Must-fail control 10 (`verify.py:181`) compares 0.068 with
   0.050 and 0.014 with 0.020, and both left-hand values are constants written 25 lines above it
   (`verify.py:156`). It cannot fail. Parts of three others are the same: control 5 tests the literal 0.72
   (`:99`, `:176`), control 11 tests the literal 0.0 and a ratio of two literals (`:152`, `:182`), and control
   12 tests the literal 0.0 for water use (`:161`, `:183`). The claims may well be right. The verifier does not
   test them.
4. **aska-physical profile.** The fibral-rigidity row says pull request 1 awaits human sign-off. That pull
   request is merged (`0652052`, 2026-11-16). The cfrp-truss row is missing a column separator, which breaks the
   table. Both are fixed in the profile change that indexes optifab. That change adds a row, so the profile
   lines pinned here move down by one when it merges: run `--repin` afterwards.
5. **fibral-rigidity certificate.** Its `repository` field reads `Foundation-0/fibral-rigidity`. The repository
   is at aska-physical/fibral-rigidity.
6. **Weft.** Its telemetry has no physical input, and its telemetry line carries an unkeyed hash that its
   roadmap describes as "integrity against accidents, not authentication". A plant that takes commands from a
   scheduler needs signed messages. Moissanite-Labs/synmerit already defines signed records.
7. **Weft, one edge case in the gate.** With a locked mask, a locked value beyond the float32 range makes
   `verify_weight_update_safety_ex` raise `OverflowError` instead of returning a rejection
   (`invariants.py:52-54`, reached from the locked-mask check at `:69-71`). The differential test here found it. `plant_gate` copies the behaviour
   so that the two agree.
8. **venturi-collars.** Its certificate names a 0.150 mW sensor node. At low airflow (1.8 m/s) the collar
   harvests 0.104 mW, so that node would need 144% of the harvest. Only the 0.080 mW node is powered there.

## 4. Artifacts

- [verify.py](verify.py): the derivations, both gates, the plant frame, the loop, the graph and unit checks, 24
  must-fail controls. `--formal` rebuilds the proofs and replays the ledger in Lean.
- [loop.py](loop.py): the improvement loop. [formal/](formal/README.md): the Lean project.
- [results/ledger.json](results/ledger.json) and [results/formal.json](results/formal.json): every decision of
  the loop, and the record of the last formal run.
- [results/certificate.json](results/certificate.json): the outputs `verify.py` must reproduce.
- [data/](data/): vendored inputs with hashes, 48 pins, the graph, the unit, and the commit of each of 36
  repositories.
- [docs/VISION.md](docs/VISION.md), [docs/PROPOSALS.md](docs/PROPOSALS.md), [docs/STRUCTURE.md](docs/STRUCTURE.md),
  [docs/MODEL.md](docs/MODEL.md) and [docs/CONVERGENCE.md](docs/CONVERGENCE.md). The tables in STRUCTURE.md and
  all of CONVERGENCE.md are generated.
- [tools/fetch_upstream.py](tools/fetch_upstream.py) and [tools/render_map.py](tools/render_map.py).

To move an element of the unit forward, change its status in `data/unit.json`. `verify.py` refuses to report the
loop closed unless every interface is marked checked, and it fails if a repository on the map is neither placed
nor listed as not placed.

To change a pin: edit `data/pins.json` or `data/graph.json`, then run
`python3 verify.py --upstream ROOT --repin`, `python3 verify.py --write` and `python3 tools/render_map.py`.
`--repin` finds each cited text again and records the new commit, file hash and line. It fails if the text is
gone, which is the signal that an upstream claim changed.

## 5. Next-agent build queue

The larger pieces are written up as eight proposals in [docs/PROPOSALS.md](docs/PROPOSALS.md), each with an
issue on GitHub. The list below is the working queue, and its first four items are proposals 1, 2 and 7.
Items 1 to 4 close the open places in the loop ([docs/STRUCTURE.md](docs/STRUCTURE.md), interfaces L1, L2, L5
and L8).

To change the formal project: edit `formal/`, then run `python3 verify.py --formal --write`. Any change to a
Lean source, the oracle or the ledger makes must-fail control 24 fail until the formal run is repeated.

1. **Agree the plant frame with Weft (interface L2, element W1).** The 16 slots are defined and tested here.
   Weft's owners decide whether the frame shares their telemetry bus or travels as an abios line. Done when one
   fixture file is parsed by both sides. This gives Weft a real temperature in place of its estimate.
2. **Design the two missing sensors (interface L1, elements N3 and N4).** Rack vibration and recooling
   temperature each have a certified limit and nothing that measures them.
3. **A way to shed load, with an energy reading (interface L5).** Neither Weft nor Exo can defer or shed compute
   on request, and neither measures energy. Until one does, the scheduler side of the contract has nothing to
   act on.
4. **A first fabrication element (interface L8, element F1).** Pick one aska-physical process that already has
   certified limits, state its gate inputs, and run the gate on them. Fe-SMA activation in funi-floors is the
   obvious candidate.
5. **Apply notes 1 and 2 of section 3 in funi-frame.** Done when its certificate carries the extra IT power
   and a recooling temperature, and optifab's pins are refreshed.
6. **A year at part load (optifab, with funi-frame issue 2).** Run an hourly utilisation trace against the load
   floor and the thermal budget. Report hours below the floor and the budget drawn. Share the trace with
   funi-frame's aquifer balance, which injects 84.3 GWh_th a year in one direction.
7. **Carry the proof over to Weft's floating-point gate (Weft, Proven-Commons; element R2).** The exact gate is
   proved in `formal/`. What remains is Weft's open Milestone I.3: a statement relating its float gate to the
   exact one, and a reviewer for the specification (proposal 5). The Proven-Commons reviewer list is empty
   today, so no project can yet pass bar item 1.
8. **A second verifier that shares no code (optifab).** The Foundation-0 physics rule asks for two. A different
   agent, or a different language, should recompute sections 1 to 5 of the model note from the same pins.
9. **A network of campuses (optifab).** v0.1.0 models one. With N campuses, each with a load floor, a thermal
   budget and a margin radius, placing work becomes an optimisation: most compute per unit of utility energy,
   subject to every gate. State that problem and solve a small case exactly.
10. **Replicate the top of the stack (Foundation-0, aska-physical).** incentre-lattices' results sit under 6
    repositories of the stack and nhanes-bioimpedance under 5. An independent replication there lifts the most
    work. See the evidence table in [docs/CONVERGENCE.md](docs/CONVERGENCE.md).
11. **Choose a telemetry transport with a parser near the bar (Proven-Commons, element W3).** MQTT, CBOR, NTP and
    protobuf are all candidates in progress and none is verified. If item 1 picks a transport, prefer one whose
    parser is closest to the verified bar.

## 6. Decisions for a person

- **Licence.** Added at the owner's request: PolyForm Noncommercial 1.0.0 for code and CC BY-NC 4.0 for text
  and data, so noncommercial use is open and commercial use is reserved. The owner should confirm the
  copyright line in NOTICE ("Aska Physical and the optifab contributors"). The sibling aska-physical
  repositories still have no licence. Weft's files are redistributed under Apache-2.0.
- **Whether funi-frame should adopt notes 1 to 3.** They change published figures.
- **Whether the plant gate is a direction worth pursuing.** Its arithmetic is now proved, and it has been run
  on a model. It has never seen a sensor or a machine.
- **Who reviews `formal/SPEC.md`.** Until a person who did not write it approves it, nothing here may be
  called verified.
- **Sign-off.** Nothing here counts until a named person reviews it.

## 7. How this session worked

- Read: every repository listed in [docs/CONVERGENCE.md](docs/CONVERGENCE.md), at the commits listed there, plus
  the twelve under "Surveyed and not connected". The three Terrafab documents named in issue 1 were read in
  full, with Weft's digest of them. Two read-only survey agents located data files and status
  lines; every value used here was then re-read directly and is pinned.
- Ran: funi-frame's `verify.py`, which reproduces its certificate (12/12 controls). optifab's own verifier,
  offline and against the clones.
- Ran: Weft's `invariants.py`, as the oracle of the differential test. Lean 4.35.0, `lake comparator --paranoid`
  and the Proven Commons bar checker (`bar/check.py` at mission `7b22e54`) on `formal/`.
- Did not run: the verifiers of the other aska-physical repositories. Their certificates were read as data.
- Reviewed: a second AI agent, given the code and not the conclusions, re-derived the results and tested the
  gate against Weft's. It found that the gate disagreed with Weft's at floating-point boundaries, that the
  compute figure should be a range, that the recooling limit was stated too tightly, that one margin was not
  certified upstream, that the lineage depth rule was off by one, and that several controls could not fail.
  All of these are fixed in this version. No person has reviewed it.
- Did not read: Moissanite-Labs/exo and the four Proven-Commons protocol repositories. They appear in the graph
  as "named only". Private repositories were not touched.
