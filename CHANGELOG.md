# Changelog

Machine-checked milestones for `aska-physical/optifab`.

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
