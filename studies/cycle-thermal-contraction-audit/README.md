# Exact-$\mathbb{Z}/\mathbb{Q}$ Thermal Outage (`#14`), $K$-Stage Surge Contraction & $\beta_1 \ge 1$ Passive Multi-Sink Loop Audit (`aska-physical/optifab`)

Strictly add-only receiving-side **`MODEL` / `CHECKER`** study (`aska-physical/dock#8` labeling: exact pure-$\mathbb{Z}/\mathbb{Q}$ algebra anchored to pinned literals on `origin/main @ 74d68ea15ab7ed24`; **not** a physical plant measurement) leaving `verify.py`, `loop.py`, `formal/`, and `results/` completely untouched.

## What Is Checked (Zero Floats, Zero Bare `assert`s)

1. **Part A — Exact-$\mathbb{Q}$ Audit of `optifab#14` Defects #1 & #2 (`loop.py:42-75`) + `MODEL.md` §2 Second-Law Ceiling:**
   - **Defect #2 (`qFix` omitted from `outage_ride_through`):** Using exact pinned values (`P_it = 10,000 kW`, `U_roof = 1234/10000`, `A_roof = 2500 m²`, `U_wall = 132/1000`, `A_wall = 2476 m²`, `ΔT = 20 K`, `other_kw = 200 kW`), exact fixed heat load is $q_{\text{fix}} = 2658833/12500\text{ kW}$ ($\approx 212.71\text{ kW}$), adding `2658833/37500 ≈ 70.90 kWh_th` during a `20`-min outage. On the `#14` reference check (`2,400 kWh` store, `30%` shed), IT-only margin is `972,223 ppm <= 1,000,000` (false **`PASS`**) while corrected total heat `90158833/37500 ≈ 2,404.24 kWh_th` gives `1,001,765 ppm > 1,000,000` (**`FAIL`**); the `2,500 kWh` start design passes (`961,695 ppm <= 1,000,000`).
   - **Defect #1 (`utility(0) = 13353/35 ≈ 381.51 kW` subtracted during zero-shed outages):** Confirms `loop.py:73` artificially raises `eta_ppm` under `12` zero-shed outages (`914,237 > 914,218`), whereas subtracting `utility(P) - utility((1 - shed) P)` keeps zero-shed outages invariant.
   - **Second-Law Recooling Ceiling (`MODEL.md` §2):** Exact rational ceiling at `T_h = 58 °C`, `T_c = 18 °C`, `COP = 62/100` confirms `30 °C` passive sinks pass and `42 °C` dry cooler fails.
2. **Part B — Op 2 $K$-Stage Cascaded Thermal-Buffer Surge Contraction (`data/unit.json` `G1`/`L7`):**
   - Exact-$\mathbb{Q}$ recurrence matches negative-binomial closed form across $K \in \{1, 2, 4, 8\}$ ($\alpha = 1/2$), contracting peak impulse flux strictly `1/2 > 1/4 > 5/32 > 429/4096` (exact `2048/429 ≈ 4.77x` attenuation) while conserving energy identically, paired with an honest non-monotone fixed-capacity control (`K = 1, 2, 3`, $\alpha_K = K/4$) and a `6`-step contractive flow-choke (`PASS`) vs positive-feedback runaway (`FAIL`) contrast.
3. **Part C — Op 3 $\beta_1 \ge 1$ Passive Multi-Sink Manifold Closure & Redundancy (`data/unit.json` `G2`):**
   - Exact-$\mathbb{Q}$ Kirchhoff solver (`B q = 0`, Tellegen $\eta^\top q = q^\top G^{-1} q$, diurnal reversal $q(-\eta) = -q(\eta)$) proves: dead-end tree header ($\beta_1 = 0$) has identically `0` passive buoyancy flow and `0` single-pipe survival (`FAIL`); isothermal coboundary loop ($\beta_1 = 1$) has `0` flow (`FAIL`); single buoyancy loop ($\beta_1 = 1$) circulates (`1/4` power, `1` 1-pipe survival, `0` 2-pipe survival); and the `G2` `3`-sink parallel manifold (`aquifer + energy piles + sky-cooling roof` with return riser, `5` nodes, `7` edges, $\beta_1 = 3$) achieves exact passive circulation (`3/5` trunk, `1/5` per sink), `100%` (`1`) single-pipe isolation survival, and `6/7` (`85.7%`) double-pipe survival (`PASS`).

## Files

- `optifab_bio_thermal_audit.py` — Pure-$\mathbb{Z}/\mathbb{Q}$ checker, canonical zero-float certificate emitter, and fail-closed `--check` verifier.
- `test_optifab_bio_thermal_r5.py` — Assertion-free `unittest` R5 suite (positive proofs, negative controls, adversarial JSON/symlink/cap/CLI hardening).
- `optifab_bio_thermal_certificate.json` — Committed canonical zero-float JSON certificate (byte-identical to `--standalone --json`).

## Independent Reproduction (Isolated Mode)

```bash
python3 -I -B studies/cycle-thermal-contraction-audit/optifab_bio_thermal_audit.py --standalone --json | cmp -s - studies/cycle-thermal-contraction-audit/optifab_bio_thermal_certificate.json
python3 -I -O -B studies/cycle-thermal-contraction-audit/optifab_bio_thermal_audit.py --check studies/cycle-thermal-contraction-audit/optifab_bio_thermal_certificate.json
python3 -I -O -B studies/cycle-thermal-contraction-audit/test_optifab_bio_thermal_r5.py -v
```
