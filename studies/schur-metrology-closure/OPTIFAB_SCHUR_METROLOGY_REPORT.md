# Pure-$\mathbb{Z}/\mathbb{Q}$ Schur (`⧄`/`⧅`) Recursive Optical/Lithography Metrology Closure (`aska-physical/optifab`)

**Schema:** `aletheia.optifab_schur_metrology_closure.v1` | **Oracle Class:** `exact` (100% pure Python 3 stdlib $\mathbb{Z}/\mathbb{Q}$, zero IEEE-754 floats, zero external dependencies) | **Novelty:** `N1`

---

## 1. Executive Summary (Own Terms First)

Diagonal limit-state accounting checks each physical subsystem margin in isolation ($A_{ii} > 0$, $D_{jj} > 0$). In coupled precision optical/lithography fabrication and gated facility control (`aska-physical/optifab @ 74d68ea15ab7ed24`), however, **unmeasured off-brane metrology modes** (such as `optifab`'s two missing sensor organs: `N3` rack vibration / sub-wavelength stage jitter and `N4` coolant/recooling thermal drift) enter the effective observed stiffness/compliance matrix through the **Schur complement** $S = A - B D^{-1} B^\top$ (`⧄` / `⧅`). Simultaneously, critical EUV/optical consumables (multilayer mirrors, Sn-droplet collectors, sub-nanometer interferometric standards) enter recursive plant self-fabrication (`F1` / `L8`) through a coupled Leontief/Von Neumann input-output Schur complement $S_{VV} = (1 - a_{VV}) - a_{VL}^\top (I - A_{LL})^{-1} a_{LV}$.

This study certifies **four pure-$\mathbb{Z}/\mathbb{Q}$ theorems** over exact rational arithmetic (`int`, `fractions.Fraction`) with zero floating-point operations, anchored verbatim to real pinned constants from `aska-physical/optifab`:

1. **Pillar 1 — Exact Pure-$\mathbb{Q}$ Anchors from `aska-physical/optifab` (`74d68ea15ab7ed24`) & EUV Rayleigh Metrology:** Recomputes in exact rationals all **12 certified `optifab` campus limit states** (`funi-frame`, `funi-floors`, `venturi-collars`), confirming the binding headroom `floor_punching_collar` $h_1 = 27419/137820$ (`u = 0.801052`, floored plant radius $R^* = 1989/10000$), second-tightest `sensor_power_at_airflow_turndown` $h_2 = 692/3003$ (`u = 0.769564`), exact second-law recooling ceilings ($19792395/493463 \approx 40.109177\,^\circ\text{C}$ at $15\,^\circ\text{C}$ and $20582334/496463 \approx 41.457941\,^\circ\text{C}$ at $18\,^\circ\text{C}$), exact `N3`/`N4` missing-sensor headrooms ($h_{\mathrm{N3}} = 8209/10000$, $h_{\mathrm{N4}} = 474037/970500$), exact load floor $P_{\min} = 13292927/23562500 \approx 0.564156\text{ MW}$, plant vibration tone phase-cancellation ($0/4$ pass at `15 ms`, $4/4$ pass at `0.5 ms`), and High-NA EUV Rayleigh tolerances ($\lambda = 27/2\text{ nm}$, $\mathrm{NA} = 11/20$: $\mathrm{CD}_{\min} = 81/11\text{ nm}$, $\mathrm{DOF} = 2700/121\text{ nm}$, overlay budget $= 81/55\text{ nm}$).
2. **Pillar 2 — Diagonal-vs-Schur Non-Commutativity Obstruction (`⧄`/`⧅`) & Exact Bareiss / Haynsworth Inertia (`⦺`):** Casts `optifab`'s four tightest observed margins $A = \operatorname{diag}(h_1, h_2, h_3, h_4) \succ 0$ and its two coupled missing sensors $D = \begin{pmatrix} h_{\mathrm{N3}} & 1/10 \\ 1/10 & h_{\mathrm{N4}} \end{pmatrix} \succ 0$ into the exact $6\times 6$ block system $M(\tau)$ and $4\times 4$ Schur complement $S(\tau) = A - \tau B D^{-1} B^\top$:
   - **Rank-2 Coupled `N3`/`N4` Block:** Brackets the exact algebraic bifurcation root of $p(\tau) = 1 - \operatorname{tr}(K)\tau + \det(K)\tau^2$ to width $10^{-6}$ (`[186073/250000, 744293/1000000]`). Across $\tau = 1/2 \to 1$, **every standalone diagonal margin remains strictly positive** ($A \succ 0$ `(4,0,0)` and $D \succ 0$ `(2,0,0)`), yet exact fraction-free Bareiss leading principal minors and Lagrange congruence prove $S(\tau)$ flips inertia **`(4, 0, 0) -> (3, 0, 1)`** (and $M$ flips `(6, 0, 0) -> (5, 0, 1)`, obeying Haynsworth additivity and $\det(M) = \det(D)\det(S)$ identically), witnessed by an explicit rational vector $w \in \mathbb{Q}^4$ satisfying $w^\top S w < 0 < w^\top A w$. Calibration precision lift $D \mapsto (1 + \eta)D$ fails at $\eta = 1/4$ (`(3, 0, 1)`) and restores strict SPD **`(4, 0, 0)`** at $\eta = 1/2$, while the subcritical regime certifies the exact off-brane dark-shadow quadratic energy decomposition $E_{\mathrm{full}} = E_{\mathrm{obs,Schur}} + E_{\mathrm{off,shadow}}$ with $E_{\mathrm{off,shadow}} = 215324090/3794319733 > 0$.
   - **Exact Zero-Determinant Common-Mode Bifurcation Surface & Minimal Calibration Threshold:** Over the same real `optifab` blocks $A, D$ with common-mode coupling $B_{\mathrm{cm}} = b_{\mathrm{obs}} v_{\mathrm{off}}^\top$, computes the exact rational critical variance $\tau_{\mathrm{crit}}^{\mathrm{cm}} = 15760468911814196061744/32723997696703734766825$ ($\approx 0.481618$) and exact minimal calibration precision lift $\eta_{\min} = 1/\tau_{\mathrm{crit}}^{\mathrm{cm}} - 1 \approx 1.076334$. Proves exact zero determinant $\det(S) = 0$ and exact null vector $S v_0 = \mathbf{0}$ at the boundary **`(3, 1, 0)`**, collapse **`(3, 0, 1)`** at $\eta = \eta_{\min} - 1/100$, and strict SPD restoration **`(4, 0, 0)`** at $\eta = \eta_{\min} + 1/100$.
3. **Pillar 3 — Exact $\mathbb{Q}^{5\times 5}$ Leontief/Von Neumann EUV-Metrology Consumables Closure:** Couples a locally productive 4-sector campus-fabrication bulk $A_{LL}$ ($\det(I_4 - A_{LL}) = 17923/32000 > 0$, $(I_4 - A_{LL})^{-1} > 0$, Collatz–Wielandt $\rho(A_{LL}) \in [9/20, 1/2] < 1$) to a 5th `euv_optics_consumables` sector: unclosed high import leverage drives $S_{VV} = -25333/89615 < 0$ and $\det(I_5 - A_5) = -25333/160000 < 0$ (all 5 gross outputs strictly negative on unit demand); scaling consumable leverage by exact $\alpha_{\mathrm{crit}} = 71692/97025$ hits $\det(I_5 - A_5) = 0$ identically; design-for-closure restores $S_{VV}' = 72614/89615 > 0$, $\det(I_5 - A_5') = 36307/80000$, all `25/25` entries of $(I_5 - A_5')^{-1} > 0$, and $\rho(A_5') \in [1/2, 13/20] < 1$. Independently replays the exact companion Leontief closure invariants (`83377/160000`, `-331139/833770`, `138867/166754`).
4. **Pillar 4 — Diagonal `PlantGate` Blind Spot vs. Schur-Coupled Metrology Gate & `venturi-collars` Dual-Sensor Closure:** Replays `optifab`'s exact integer-ppm `formal/PlantGate` (`LIMIT = 1,000,000 ppm`, `u0_ppm = [801053, 769564, 616000, 284589]`, `headroom = 198,947 ppm`). An explicit candidate step `uc_ppm = [901053, 879564, 696000, 379589]` satisfies `dist_sq = 37,525,000,000 <= 39,579,908,809 = headroom^2` and keeps every margin `< 902,000 ppm` (**admitted by `PlantGate`**), yet collapses the coupled Schur matrix at subcritical $\tau = 1/2$ from **`(4, 0, 0)` -> `(3, 0, 1)`** (blocked by the Schur-Coupled Gate). Calibrating `N3`/`N4` ($\eta = 1$) restores **`(4, 0, 0)`** and cleanly admits the step. Finally, exact rational `venturi-collars` accounting at `1.8 m/s` turndown (`13/125 mW` harvest) proves `1` `80 uW` node passes (`2311/3003 < 1`) while `2` simultaneous `N3+N4` nodes fail (`4622/3003 > 1`), certifying a minimum of `2` collars for continuous dual-sensor closure (or shared duty cycle $\le 3003/4622$).

---

## 2. Certified Quantitative Tables

### Pillar 1 — Exact `aska-physical/optifab` (`74d68ea`) Physical & EUV Metrology Anchors

| Quantity | Exact Pure-$\mathbb{Q}$ Value | Decimal (6 dp) | Provenance |
|---|---:|---:|---|
| Binding margin headroom (`floor_punching_collar`) | `27419/137820` | `0.198948` | `optifab` / `funi-floors` |
| Floored plant radius $R^*$ | `1989/10000` | `0.198900` | `optifab` `verify.py` |
| Second-tightest headroom (`sensor_power_at_airflow_turndown`) | `692/3003` | `0.230436` | `optifab` / `venturi-collars` |
| Missing sensor `N3` (`rack_vibration`) headroom | `8209/10000` | `0.820900` | `optifab` / `funi-frame` |
| Missing sensor `N4` (`recooling_C` at $30\,^\circ\text{C}$ vs $T_{a,\max}$) | `474037/970500` | `0.488446` | `optifab` `MODEL.md §2` |
| Max recooling temperature ($15\,^\circ\text{C}$ / $18\,^\circ\text{C}$ chilled) | `19792395/493463` / `20582334/496463` | `40.109177` / `41.457941` | `optifab` `MODEL.md §2` |
| Self-cooling load floor $P_{\min}$ (MW) | `13292927/23562500` | `0.564156` | `optifab` `MODEL.md §3` |
| High-NA EUV $\mathrm{CD}_{\min}$ / $\mathrm{DOF}$ / overlay budget (nm) | `81/11` / `2700/121` / `81/55` | `7.363636` / `22.314050` / `1.472727` | Rayleigh ($\lambda=13.5\text{ nm}, \mathrm{NA}=0.55$) |

### Pillar 2 — Block-Schur Off-Brane Inertia (`(n_pos, n_zero, n_neg)`) & Calibration Closure

| System / Regime | $\tau$ | Calibration $\eta$ | Standalone $A, D$ SPD? | Schur $S$ Inertia | Full $M$ Inertia | $\det(S)$ Sign / Closure |
|---|---:|---:|---|---|---|---|
| Rank-2 `N3`/`N4` Subcritical | `1/2` | `0` | `True, True` | `[4, 0, 0]` | `[6, 0, 0]` | `> 0` (**SPD CLOSED**) |
| Rank-2 Sturm Bracket Lower | `186073/250000` | `0` | `True, True` | `[4, 0, 0]` | `[6, 0, 0]` | `> 0` (**SPD**) |
| Rank-2 Sturm Bracket Upper | `744293/1000000` | `0` | `True, True` | `[3, 0, 1]` | `[5, 0, 1]` | `< 0` (**COLLAPSED**) |
| Rank-2 Supercritical Uncalibrated | `1` | `0` | `True, True` | `[3, 0, 1]` | `[5, 0, 1]` | `< 0` (**COLLAPSED**) |
| Rank-2 Under-Calibrated | `1` | `1/4` | `True, True` | `[3, 0, 1]` | `[5, 0, 1]` | `< 0` (**COLLAPSED**) |
| Rank-2 Calibrated Closure | `1` | `1/2` | `True, True` | `[4, 0, 0]` | `[6, 0, 0]` | `> 0` (**SPD RESTORED**) |
| Common-Mode Subcritical | `2/5` | `0` | `True, True` | `[4, 0, 0]` | `[6, 0, 0]` | `> 0` (**SPD**) |
| Common-Mode Exact Bifurcation | $\tau_{\mathrm{crit}}^{\mathrm{cm}} \approx 0.481618$ | `0` | `True, True` | `[3, 1, 0]` | `[5, 1, 0]` | `= 0` (**EXACT NULL $S v_0 = 0$**) |
| Common-Mode Supercritical | `1` | `0` | `True, True` | `[3, 0, 1]` | `[5, 0, 1]` | `< 0` (**COLLAPSED**) |
| Common-Mode Below Minimal Cal | `1` | $\eta_{\min} - 1/100$ | `True, True` | `[3, 0, 1]` | `[5, 0, 1]` | `< 0` (**COLLAPSED**) |
| Common-Mode Exact Minimal Cal | `1` | $\eta_{\min} \approx 1.076334$ | `True, True` | `[3, 1, 0]` | `[5, 1, 0]` | `= 0` (**EXACT BOUNDARY**) |
| Common-Mode Restored Closure | `1` | $\eta_{\min} + 1/100$ | `True, True` | `[4, 0, 0]` | `[6, 0, 0]` | `> 0` (**SPD RESTORED**) |

### Pillars 3 & 4 — Leontief EUV Consumables Closure & `PlantGate` vs. Schur Gate

| Subsystem / Gate Witness | Key Exact $\mathbb{Q}$ Invariant | Verdict |
|---|---|---|
| Bulk 4-sector fabrication ($I_4 - A_{LL}$) | $\det = 17923/32000 > 0$, $\rho(A_{LL}) \in [9/20, 1/2]$ | **PRODUCTIVE** (`16/16` inv $>0$) |
| Unclosed EUV consumables ($I_5 - A_5^{\mathrm{blk}}$) | $S_{VV} = -25333/89615$, $\det = -25333/160000$ | **BLOCKED** (`5/5` unit output $<0$) |
| Critical EUV leverage ($\alpha_{\mathrm{crit}} = 71692/97025$) | $S_{VV} = 0$, $\det(I_5 - A_5) = 0$ | **EXACT BIFURCATION** |
| Restored EUV closure ($I_5 - A_5^{\mathrm{cls}}$) | $S_{VV}' = 72614/89615$, $\det = 36307/80000$, $\rho \le 13/20$ | **CLOSED** (`25/25` inv $>0$) |
| Companion Leontief replay | `83377/160000`, `-331139/833770`, `138867/166754` | **EXACT MATCH** |
| `optifab` `PlantGate` on `uc_ppm` ($\tau = 1/2$) | `dist_sq = 37,525,000,000 <= 39,579,908,809`, `max = 901,053 ppm` | **DIAGONAL PASS / SCHUR FAIL `[3, 0, 1]`** |
| Calibrated Schur-Coupled Gate ($\eta = 1$) | Same `uc_ppm`, Bareiss minors all $> 0$, inertia `[4, 0, 0]` | **BOTH GATES PASS** |
| `venturi-collars` dual-sensor power (`1.8 m/s`) | `1` node `2311/3003 < 1`, `2` nodes `4622/3003 > 1`, duty $\le 3003/4622$ | **MIN `2` COLLARS FOR CONTINUOUS `N3+N4`** |

---

## 3. Prior Art (`N0`), Honest Novelty Tagging (`N1`), & Security Boundaries

- **Prior-Art Foundations (`N0`, full-text checked):**
  - I. Schur (1917), *Über Potenzreihen, die im Innern des Einheitskreises beschränkt sind*, block-matrix complement elimination.
  - E. H. Bareiss (1968), *Sylvester's Identity and Multistep Integer-Preserving Gaussian Elimination*, Math. Comp. 22(103):565–578.
  - E. V. Haynsworth (1968), *Determination of the inertia of a partitioned Hermitian matrix*, Linear Algebra Appl. 1(1):73–81 (and singular extension Carlson, Haynsworth, & Markham, 1974).
  - W. Leontief (1941), D. Hawkins & H. A. Simon (1949), J. von Neumann (1945), & L. Collatz–H. Wielandt input-output productivity and Perron spectral bounds.
  - Lord Rayleigh (1879) / E. Abbe (1873) diffraction resolution and depth-of-focus scaling.
  - `aska-physical/optifab` (`74d68ea15ab7ed24`): 12 certified campus limit states, second-law recooling bound, load floor, `formal/PlantGate`, and missing `N3`/`N4` sensor specification.
- **Contribution (`N1` — Exact Synthesis & Executable Certification):**
  - First pure-$\mathbb{Z}/\mathbb{Q}$, zero-float, stdlib-only executable proof suite coupling `aska-physical/optifab`'s real 12 certified limit states and missing `N3`/`N4` sensor organs to exact Bareiss/Haynsworth off-brane Schur inertia transitions, exact dark-shadow quadratic energy conservation, exact Leontief EUV-consumables Schur closure, and an explicit integer-ppm counterexample proving that `optifab`'s diagonal `PlantGate` admits Schur-collapsing steps until `N3`/`N4` calibration closes the loop.
- **Honest Scope & Security Boundaries:**
  - All `optifab` numerical inputs are pinned model outputs from `aska-physical/optifab @ 74d68ea` (no physical laboratory measurement is claimed).
  - `MAX_INT_BITS = 3,321` is the exact binding fail-closed integer limit across oracle, JSON parser, and rational parser (`MAX_INT_DIGITS = 1,000` pre-parse guard).
  - `optifab_schur_metrology_audit.py` enforces atomic `dir_fd` traversal (`O_RDONLY | O_DIRECTORY | O_NOFOLLOW`) with verified root-owned macOS Darwin system-prefix normalization (`/var`, `/tmp`, `/etc` $\to$ `/private/*` without resolving user symlinks), inode-matched `$PWD` symlink ancestor verification, `65,536`-byte streaming caps, durable `0o600` atomic writes (`os.fsync(fd)` + `st_nlink == 1` + `os.replace(..., dir_fd)` + `os.fsync(dfd)`), zero division on untrusted denominators (`cap > 0` checked explicitly), and strict-type bijective `secondary_audit_payload` verification under both `full_replay=True` and `full_replay=False` (within standard POSIX threat models, excluding root/ptrace adversaries).

---

## 4. Verification Receipts & Frozen Artifact Manifest

- **Frozen Certificate (`optifab_schur_metrology_certificate.json`, `20,799` bytes, `0o600`):**
  - `file_sha256`: `412a6ff68d687536288718970e9cabbfc2defc4476a5c2faa4fed3623a3d033e`
  - `canonical_sha256`: `50e8830664ee685534cbc09797bf320115279dbf5780ee33a6866590e944ae0e`
  - `payload_sha256`: `c93c4f29e1b5a9e97aa0dee4ff0e97a83063ccf22b6e3df7b4727d29a0b8ca30`
  - `certificate_sha256`: `5fb998a1ac54a4e0f26a1f9d3799a13a9cfd58217081b750d8320b31cb2fd10d`
- **Frozen Code & Certificate Manifest (excluding this report):**

| File | Lines | Bytes | Mode | SHA-256 |
|---|---:|---:|---:|---|
| `optifab_schur_metrology_oracle.py` | `1,061` | `46,322` | `0o644` | `e73d061dd44331e165db7dfe0e59451fc724ecd922e9e56d9218056d52d70161` |
| `optifab_schur_metrology_audit.py` | `1,035` | `40,859` | `0o644` | `1ac33d231f12e5fe55744f07b050752663ed41b75d5c09a1b7d1cfb93e277d5e` |
| `test_optifab_schur_metrology_r5.py` | `829` | `48,898` | `0o644` | `ba9116adfebf0805719e5cc0312533c3d9fcd238f7aa74a93e45fe66cb9d44e6` |
| `optifab_schur_metrology_certificate.json` | `1` | `20,799` | `0o600` | `412a6ff68d687536288718970e9cabbfc2defc4476a5c2faa4fed3623a3d033e` |

- **Verification Gates (`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`):**
  - **Isolated Interpreter Parity (`-I -B`, `-I -O -B`, `-I -B -W error`, `PYTHONHASHSEED=42 -B`, plus `umask 077`):** `--standalone --json` bit-identical (`412a6ff6...`), `--check --json` bit-identical (`80d79972...`), `test_optifab_schur_metrology_r5.py` **`8/8 OK`** across all modes and `umask 077` (`50` re-signed `full_replay=False` tamper kills incl. `capacity_q="0"` zero-denom guard, direct `secondary_audit_payload` float/subclass checks, `assemble_block_matrix_q` row-type/width guards, scratch `os.mkfifo` ONLY, `16T/80T` `0o600` bursts, Linux-only `550` `renameat2(RENAME_EXCHANGE)` & `550` hardlink races, mocked macOS Darwin prefix checks).
  - **Exhaustive Leaf Tamper Walk:** **`633/633` leaves, `2,178` mutations** across both `verify_certificate_dict(..., full_replay=False)` and direct `secondary_audit_payload(...)` (including same-value runtime `float`s and `True`/`False`-in-`int`) -> **`0` accepted, `0` raw crashes**.
  - **Live Mutation Testing (`--guards require_ok --max-mutants 0`):** `optifab_schur_metrology_oracle.py` **`36/36`** + `optifab_schur_metrology_audit.py` **`74/74`** = **`110/110` (`100.0%`, `survived=0`, `truncated=False`) KILLED**.
  - **Whole-File AST `BoolOp` Mutation Sweep:** `optifab_schur_metrology_oracle.py` **`37/37`** + `optifab_schur_metrology_audit.py` **`33/33`** = **`70/70` (`100.0%`, `surv=[]`) KILLED**.
  - **4-Surface Adversarial Boundary Fuzzer:** CLI `--check` **`25/25`** + `verify_certificate_dict(full_replay=True)` **`19/19`** + `verify_certificate_dict(full_replay=False)` **`19/19`** + direct `secondary_audit_payload` **`19/19`** = **`82/82` (`100.0%`, `bypasses=0`, `crashes=0`) PASS**.
  - **Static & Ancestor Audit (`--strict-ancestors --safety-scan`):** **`PASS`** (`5` files, `2/2` parity scripts, `0` findings, `0` bare asserts, `0` AST floats, `0` leaks, `0` `__pycache__`).
