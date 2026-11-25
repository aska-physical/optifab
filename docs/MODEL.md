# The model

This note derives each result in the README, states what it assumes, and says where every input comes from.
`python3 verify.py` recomputes all of it and compares the outcome with `results/certificate.json`.

Labels follow the Foundation-0 repository standard: **PROVEN** (written proof, checked symbolically),
**VERIFIED** (finite deterministic check, not a proof), **KNOWN** (cited), **CONJECTURE**. On the Foundation-0
Ledger's evidence scale the whole of optifab is **claimed**: an AI agent wrote it and no person has reviewed it.

Nothing here is measured. The inputs are the outputs of other repositories' models. A result marked PROVEN is
proved about those models, not about a building.

## Inputs

The reference campus is the one in [funi-frame](https://github.com/aska-physical/funi-frame): 10 MW of IT load, a
square 2,500 m² plan, two storeys.

| Quantity | Value | Source | Kind |
|---|---|---|---|
| IT load $P$ | 10 MW | funi-frame certificate | design basis |
| Heat captured by liquid, by air | 8.5 MW, 1.5 MW | funi-frame certificate | design basis |
| Sorption chiller COP | 0.62 | funi-frame `verify.py:144` | literal in the verifier |
| Drive and chilled-water temperatures | 58 °C, 15 to 18 °C | funi-frame `HANDOFF.md:14` | prose only |
| Aquifer loop COP, plant auxiliaries | 28, 0.195 MW | funi-frame `verify.py:147` | literals |
| Conventional chiller COP, auxiliaries | 3.0, 0.27 MW | funi-frame `verify.py:147` | literals |
| Non-cooling overhead | 0.2 MW | funi-frame `verify.py:159` | literal |
| PCM skid energy | 2,500 kWh_th | funi-frame `verify.py:143` | literal |
| Roof and wall U-values, building height | 0.1234, 0.1316 W/(m²·K), 12.38 m | funi-frame certificate | computed upstream |
| Limit-state demands and capacities | see section 5 | funi-frame, funi-floors, venturi-collars certificates | computed upstream, except where noted |
| Gate conformance vectors | 15 weight-update vectors | Weft `vectors.json` | test data |
| Gate oracle | Weft's own gate function | Weft `invariants.py` | code, run only as a test oracle |
| Telemetry frame layout | 16 little-endian float32, 64 bytes | Weft `frame64.py:24` | definition |
| Plant vibration tones | 29.5, 49, 60, 120 Hz | funi-frame `verify.py:112` | literals |
| Two loop latencies | 15 ms, 0.5 ms | weft-corpus `weft/terrafab.md:67` | test values only, not evidence |
| Evidence scale | claimed 1 to formally verified 5 | f0 `docs/charter/page.js:317` | definition |
| Lineage depth bound | 12 | Weft `ProvenanceRegistry.sol:7` | constant |

The three certificates, the Weft vectors and Weft's gate module are copied byte for byte into `data/upstream/`
with their hashes.
Literals and prose are pinned by repository, commit, file, line and text in `data/pins.json`.

## 1. Compute unlocked at a fixed utility supply

**PROVEN** (two identities). **VERIFIED** (numbers).

**Adopted upstream.** funi-frame v0.1.1 reports the extra IT power derived below, and `verify.py` now checks
that its certificate and this derivation agree. What follows is the derivation, and the comparison with
v0.1.0 that prompted the change.

funi-frame v0.1.0 reported 3.06 MW of "freed substation power" and multiplied it by a value of compute per MW. Freed
utility power is not IT power, because new racks need cooling and overhead of their own. How much IT load the
freed power carries depends on how the overhead grows.

- **If every overhead grows with the load**, the PUE holds, and a supply of $P\,\mathrm{PUE}_c$ carries
  $P\,\mathrm{PUE}_c/\mathrm{PUE}_f$:

  $$\Delta P_{IT} = \frac{\text{freed utility power}}{\mathrm{PUE}_f}.$$

- **If only the cooling loop grows**, as funi-frame's own verifier has it (aquifer loop at a COP of 28, with
  the plant auxiliaries, the other overhead and the passive sinks all fixed), each extra MW of IT load costs
  $1 + 1/28$ MW of supply:

  $$\Delta P_{IT} = \frac{\text{freed utility power}}{1 + 1/\mathrm{COP}_{loop}}.$$

optifab first rebuilds both PUE values from the certificate and the pinned literals (1.38033 and 1.07387, which
round to the certificate's 1.380 and 1.074). Then:

| | Value |
|---|---|
| Freed utility power | 3.065 MW (certificate: 3.06) |
| Extra IT load, every overhead growing with load | 2.854 MW |
| Extra IT load, auxiliaries fixed | 2.959 MW |
| Low-end revenue on the v0.1.0 certificate | $76.62M a year |
| Low-end revenue on the extra IT load | $71.35M to $73.97M a year |
| Extra IT load on the v0.1.1 certificate | 2.85 to 2.96 MW |
| Low-end revenue on the v0.1.1 certificate | $71.35M a year |

Either way it is less than 3.06 MW. If the dollar value is per MW of IT load, the v0.1.0 revenue figures
were 3.6% to 7.4% high. v0.1.1 assumes it is per MW of IT load and says the owner has still to confirm that.
The source of the value is not pinned here. Both cases assume the freed power is used in the same plant.

The rebuild also gives the heat sent to the aquifer store: 9.62 MW, or 84.3 GWh_th a year, all in one direction.
funi-frame already lists the yearly aquifer balance as open work.

## 2. A recooling limit for the sorption stage

**PROVEN** from the first and second laws. **VERIFIED** (numbers).

A heat-driven chiller takes heat $Q_h$ at $T_h$, lifts heat $Q_c$ from $T_c$, and rejects $Q_h+Q_c$ at $T_a$. It
cannot destroy entropy, so $(Q_h+Q_c)/T_a \ge Q_h/T_h + Q_c/T_c$. Rearranged:

$$\mathrm{COP} = \frac{Q_c}{Q_h} \le \frac{T_c}{T_a-T_c}\cdot\frac{T_h-T_a}{T_h}
\quad\Longleftrightarrow\quad
T_a \le \frac{T_c\,T_h\,(1+\mathrm{COP})}{\mathrm{COP}\cdot T_h+T_c}.$$

Temperatures are absolute. $T_h$ is the hottest temperature at which heat is supplied and $T_c$ the warmest at
which heat is taken up. funi-frame gives a 58 °C drive and chilled water at 15 to 18 °C. Taking 18 °C as the
warmest temperature at which the chiller takes up heat, which holds for a machine that evaporates at one
temperature at or below the water it produces, the claimed COP of 0.62 gives:

| Chilled water | Highest possible recooling temperature |
|---|---|
| 18 °C | 41.5 °C |
| 15 °C | 40.1 °C |

| Recooling temperature | 25 °C | 30 °C | 35 °C | 40 °C | 45 °C |
|---|---|---|---|---|---|
| Reversible COP, 18 °C chilled water | 4.145 | 2.051 | 1.190 | 0.719 | 0.423 |
| Reversible COP, 15 °C chilled water | 2.871 | 1.624 | 1.001 | 0.627 | 0.377 |

So the claimed COP needs a heat sink below about 41 °C, and at 30 °C it is 30% to 38% of the reversible limit.
A real machine does worse than these bounds for three reasons: the drive water cools as it passes through, the
evaporator is colder than the water it chills, and the condenser is warmer than the water that cools it. A
machine that took up heat along the whole range of a warmer return stream could be bounded less tightly; the
certificate gives no return temperature.

**Adopted upstream.** The funi-frame v0.1.0 certificate had no recooling temperature in it, and no stream
temperature as a value at all. v0.1.1 carries the drive, chilled-water and recooling temperatures, the same
limit of 41.46 °C, and a must-fail control for dry recooling at 45 °C. `verify.py` checks that its limit and
its reversible COP agree with the ones derived here. Its design recooling temperature of 30 °C is marked in
the certificate as a proposal with no source, awaiting the owner's confirmation. Its
design does provide cool sinks: the aquifer loop, the energy piles and the sky-cooling roof. The point is that
the zero-water claim and the COP claim both depend on those sinks. Dry coolers alone cannot hold the COP on a
day hotter than about 41 °C minus their approach.

## 3. A load floor for the workload

**PROVEN** (algebra) under assumptions A-1 and A-2. **VERIFIED** (numbers).

funi-frame's Theorem 4 says the campus cools itself when the liquid capture fraction $\alpha$ exceeds
$1/(1+\mathrm{COP}) = 61.73\%$. That holds when every heat load scales with the IT load. Some do not. Let
$q_{fix}$ be the air-side load that stays when the racks idle. The chiller must remove $(1-\alpha)P + q_{fix}$,
which needs drive heat $((1-\alpha)P + q_{fix})/\mathrm{COP}$, and the liquid loop supplies $\alpha P$. The campus
cools itself only when

$$P \ge P_{min} = \frac{q_{fix}}{(1+\mathrm{COP})\,\alpha - 1}.$$

With $q_{fix}=0$ this is Theorem 4 again.

- **A-1.** The 0.2 MW of non-cooling overhead in funi-frame's PUE is a fixed load that ends as heat in the hall air.
- **A-2.** The envelope gain is $(U_{roof}A_{roof}+U_{wall}A_{wall})\,\Delta T$ at $\Delta T = 20$ K, with the
  certified U-values, a 2,500 m² roof and 200 m × 12.38 m of wall. The 20 K is a choice made here. Solar gain,
  infiltration and people are left out. Each would raise the floor.
- **A-3.** The capture fraction (0.85), the COP (0.62) and the 58 °C drive temperature are held at their design
  values at part load. A real plant at low load may not hold them.

| Case | $q_{fix}$ | Load floor |
|---|---|---|
| Envelope only (A-2) | 0.013 MW | 0.034 MW |
| Envelope and overhead (A-1, A-2) | 0.213 MW | 0.564 MW, 5.6% of nameplate |
| Same, with the steel-pinned wall funi-frame rejects | 0.320 MW | 0.850 MW |

Below the floor the building does not fail. The air-side load has to move to the aquifer loop or a chiller, which
is a change of operating mode that a workload scheduler should know about. The wall result ties two of
funi-frame's domains together: the wall that removes the thermal bridge also lowers the load floor by a third.

The same balance gives the capture fraction needed at part load: 0.630 at full load, 0.644 at half, 0.670 at a
quarter, 0.749 at a tenth.

## 4. The thermal budget

**VERIFIED** (arithmetic on pinned values).

The PCM skid holds 2,500 kWh_th. If cooling stops and the campus sheds a fraction $s$ of its load, the skid lasts
$t = B/(P(1-s))$. To bridge an outage of length $T$ the campus must shed $s_{min} = 1 - B/(PT)$.

| Outage | 10 min | 15 min | 30 min | 60 min |
|---|---|---|---|---|
| Load to shed | none | none | 50% | 75% |

These figures count IT heat only, as funi-frame's 15 minutes does. The fixed heat load of section 3 also
reaches the store when cooling stops. With it counted, full load lasts 14.69 minutes, not 15.

The same budget covers a burst of 10% above cooling capacity for 2.5 hours. The wall liner adds 354 kWh_th on the
air side (funi-frame's 28.3 min at a 750 kW heat leak).

## 5. Margins and the plant radius

**PROVEN** (three lines below). **VERIFIED** (the axis points, 20,000 sampled points, and a slightly larger
radius that fails).

Each certificate states demands and capacities for its limit states. Their ratios form one vector $u_0$ for the
campus:

| Limit state | Source | Demand | Capacity | Utilisation |
|---|---|---|---|---|
| Floor punching collar | funi-floors | 2,208 kN | 2,756 kN | 0.801 |
| Sensor power at airflow turndown (derived here) | venturi-collars | 0.080 mW | 0.104 mW | 0.770 |
| Floor walking vibration | funi-floors | 0.308% g | 0.5% g | 0.616 |
| Floor crown compression | funi-floors | 13.67 MPa | 22.5 MPa | 0.608 |
| Roof tornado uplift, factored 1.5 | funi-frame | 460.5 kN | 783 kN | 0.588 |
| Storey drift | funi-frame | 0.563% | 1.00% | 0.563 |
| Floor duct-hole shear | funi-floors | 185.6 kN | 373.5 kN | 0.497 |
| Roof crown compression | funi-frame | 9.60 MPa | 24.75 MPa | 0.388 |
| Floor fire thrust, 120 min | funi-floors | 1,172 kN | 3,903 kN | 0.300 |
| Sorption drive heat | funi-frame | 2.419 MW | 8.5 MW | 0.285 |
| Rack vibration | funi-frame | 0.00009 g | 0.0005 g | 0.179 |
| Roof service deflection | funi-frame | 11.7 mm | 66.7 mm | 0.176 |

Let $R^* = 1 - \max_i u_{0,i}$, which is 0.19895 and is rounded down to 0.1989 so that it is never
optimistic. If a change moves the vector to $u$ with $\lVert u-u_0\rVert_2 \le R^*$,
then for every $i$

$$u_i \le u_{0,i} + \lvert u_i-u_{0,i}\rvert \le u_{0,i} + \lVert u-u_0\rVert_2 \le u_{0,i} + 1 - \max_j u_{0,j} \le 1,$$

so no limit is passed. The bound is tight: moving the tightest margin alone by the unrounded $R^*$ reaches its
limit exactly.

What this gives and what it does not:

- It is a sufficient test. The exact safe set is the box $u_i \le 1$, which is larger.
- The tightest margin in the whole building is in the floor, not the shell: the punching collar at 80%.
  Punching demand can rise 24.8% before it binds.
- Eleven of the twelve are certified upstream as a demand and a capacity. The twelfth, sensor power at low
  airflow, is derived here: the venturi-collars certificate states its margin at 4 m/s only, and the node power
  (0.080 mW) is that harvest divided by that margin. It is the second tightest. If the workload idles and the
  air handlers turn down, the sensors that watch the plant are the first thing to lose margin.
- The same certificate names a larger 0.150 mW node. At low airflow the collar harvests 0.104 mW, so that node
  would need 144% of the harvest. The collar powers the small node at turndown and not the large one.
- The utilisations come from different design codes with different safety factors built in. The vector treats
  them alike.
- In funi-frame's verifier the tornado tie-down capacity (783 kN) is a literal, not a computed value.

## 6. One gate for weights and plant

**VERIFIED**: the predicate conforms to Weft's vectors. Using it on a plant is a **proposal**.

Weft commits a change to a model's weights only if the weights stay within a radius of a saved baseline and the
step's cost fits a budget: $\lVert W-W_0\rVert_F \le R$ and budget ≥ cost > 0. This is Weft interface I3.
`plant_gate` in `verify.py` is written from three sources: Weft's interface note, its conformance vectors, and
the list path of its reference implementation, which alone defines the locked-mask rule. No Weft code is
imported or copied into the gate. The arithmetic at the boundary is deliberately the same as Weft's, so that the
two agree to the last bit.

Two checks. It passes all 15 of Weft's weight-update vectors, including the two locked-mask cases. And a
differential test runs it against Weft's own function, loaded from a hash-checked copy, on 100,000 generated
cases with a fixed seed: 0 mismatches. The generator aims at the places two implementations drift apart: radii
within one unit in the last place of the true distance, magnitudes whose squares overflow or underflow, locked
coordinates that move by one float32 step, signed zeros, values that are not finite, nested lists and wrong
shapes. Must-fail control 19 shows the test has teeth: a gate that sums the squares with `math.hypot`, which is
equally valid in exact arithmetic, is caught. Weft's 8 tension vectors and 4 royalty vectors cover other
predicates and are out of scope.

In Weft the budget is a simulation unit, and the only temperature Weft reads is a formula of CPU load
(`host_metrics.py:45`). Neither Weft nor its experiment records contain a measured watt or joule. The plant
supplies both missing quantities:

| Gate term | In Weft | On the plant |
|---|---|---|
| Baseline | saved weights $W_0$ | certified margin vector $u_0$ (section 5) |
| Candidate | proposed weights | margin vector after a proposed change, from re-running the upstream verifiers |
| Radius | 120 by default | $R^* = 0.1989$ |
| Budget | abstract units | PCM skid, kWh_th (section 4) |
| Cost | abstract units | heat not rejected during the step, kWh_th |
| Locked mask | frozen core weights | margins a scheduler may never move, such as life-safety limits (proposal) |

Worked cases, all run through the same function that passed Weft's vectors:

| Step | Result |
|---|---|
| Cooling outage, 10 min at full load (1,667 kWh_th) | admitted, 833 kWh_th left |
| A second 10 min outage before the skid recharges | rejected: budget too small |
| The same outage after shedding 60% of load (667 kWh_th) | admitted, 167 kWh_th left |
| Punching demand up 20%, 5 min outage | admitted, distance 0.160 |
| Punching demand up 26%, 5 min outage | rejected: distance 0.208 exceeds 0.1989 |

The last two move one margin and hold the others, to show the radius at work. A real candidate vector comes
from re-running the upstream verifiers with the changed inputs.

Why share the gate rather than write a plant-specific rule: there is one predicate to audit, Weft already plans
a Lean proof of it (roadmap Milestone I.3, still open) and a hardware comparator, and a plant that uses the same
predicate inherits both.

## 7. Values copied by hand between repositories

**VERIFIED**.

| Quantity | Downstream | Upstream | Agree |
|---|---|---|---|
| Floor dead mass | 195.12 kg/m² in funi-frame `verify.py` | funi-floors certificate, 195.12 | yes |
| Conventional floor mass | 744 kg/m² in funi-frame `verify.py` | funi-floors mass and reduction, 743.9 | yes |
| Fe-SMA recovery stress | 423.47 MPa from funi-frame's formula | funi-floors certificate, 423.47 | yes |
| Rack live load | 15.0 kPa in funi-frame `verify.py` | funi-floors 313 psf case, 14.99 kPa | yes |
| Leak-sensor reactance shift | 46.16% in funi-frame's study text | funi-floors certificate, 46.16 | yes |
| Sensor node power | 0.080 mW in the venturi-collars README | harvest over margin in its certificate, 0.080 | yes |

All six agree today. They were not checked by anything before: a change in funi-floors would have left
funi-frame's copy stale without a failing test. Must-fail control 14 changes the floor mass and confirms the
check fires.

## 8. Context from the Ledger

The Foundation-0 Ledger holds one deployed entry on data-centre cooling: machine learning cut the energy used
to cool a Google data centre by up to 40%, a 15% lower PUE overhead (2016, evidence: deployed). funi-frame's
model gives an 85% cut in cooling electricity and an 80.5% lower PUE overhead (evidence: claimed). The
comparison is context, not a check. It shows how far the funi-frame figure sits beyond the only deployed result
on record, and what kind of evidence would move it up the scale: a built plant.

## 9. The plant frame

**VERIFIED** (round trip, layout, contract check). The slot meanings are a **proposal**.

Weft's telemetry frame is 16 little-endian 32-bit floats, 64 bytes. The contract needs 16 numbers: the 12
margins of section 5, the thermal budget left, the IT load, the recooling temperature and the time. `verify.py`
packs the design point into that layout, unpacks it, and runs the gate and a contract check on the result. The
largest rounding error on a margin is 3e-8.

The contract check reads one frame and reports which terms fail: a margin past its limit, a spent budget, a load
below the floor of section 3, a recooling temperature at or above the limit of section 2, or a quantity that
was not measured. The design point passes with the certificate's design recooling temperature of 30 °C. With the
recooling slot left empty the check reports `recooling_not_measured`. Until funi-frame v0.1.1 the certified
design point could not fill that slot at all.

The byte layout is Weft's and is pinned. What each slot means is new here, and Weft's owners decide whether the
frame may share their bus. [STRUCTURE.md](STRUCTURE.md) lists the slots.

## 10. Loop latency against the building's own dynamics

**PROVEN** (identity). **VERIFIED** (numbers). An ideal case, so an upper bound on benefit.

The Terrafab documents quote two control-loop latencies, 15 ms and 0.5 ms. Weft's audit records that they are
asserted. They are used here only as two test values. If a loop counters a tone of frequency $f$ with a copy
that arrives late by $\tau$, the amplitude left is

$$\lvert 1 - e^{-i\varphi}\rvert = 2\,\lvert\sin(\varphi/2)\rvert,\qquad \varphi = 2\pi f\tau,$$

which is below 1 within the same cycle only when $f\tau < 1/6$. On the four plant tones in funi-frame's
isolation model, 15 ms meets that condition for none and leaves three of them larger than before; 0.5 ms meets
it for all four, with reductions of 8.5 to 20.7 dB. So the direction of the claim holds for this building's
tones.

The building does not need the fast loop. Its passive isolation holds rack vibration at 17.9% of the limit, and
the contract's own timescales are long: the thermal budget lasts 900 s at full load, against which 15 ms is
0.002%. The table is in [STRUCTURE.md](STRUCTURE.md).

## 11. The exact gate and its proofs

**Machine-checked proof** in Lean. Not verified in the Proven Commons sense: no reviewer has approved the
specification.

The floating-point gate of section 6 has boundary cases that depend on rounding. For a plant that is
unnecessary: margins can be integers. [formal/](../formal/README.md) defines an exact gate over integers, with
margins in parts per million of their limit, and proves eight theorems about it. The two about the loop:

- `run_safe`: from a start within the limit, after any list of proposals every margin is still at or below
  the limit and the budget is not negative.
- `run_bounded`: the number of admitted changes plus the budget left never exceeds the budget at the start.

Those eight take the margins as given. Since v0.3.0 the plant model of section 12 is in the same Lean file,
as exact integer arithmetic, with the bounds on each gene, the objective and the step that takes a design up.
Eight more theorems are about designs. In them the three margins that move with the genes are computed
inside the proved code. The eleven carried as constants are still inputs.

- `step_complete`: with budget left and the design held within the limit, a different design within the
  bounds and the headroom that does not lower the objective is taken up.
- `same_design_not_taken_up`: a proposal identical to the design held is never taken up.
- `step_refusal_changes_nothing`: a design that is not taken up leaves the design held and the budget as
  they were.
- `loop_safe`, `loop_in_bounds`, `loop_bounded`: from a start within the limit and the bounds, after any list
  of proposed designs, the margins of the design held are within the limit, its genes are within their bounds,
  and the changes are within the budget.
- `loop_never_worse`: after any list of proposed designs, the objective is at least what it was at the start.
  It may be equal.
- `loop_keeps_physics`: with the limit at 1,000,000 ppm and a start within it, the design held satisfies
  three exact inequalities. The cooling needed at full load is at most what the captured heat can drive. The
  fixed heat load is at most the cooling gained at the scheduler's floor. The heat of one outage, from the IT
  load not shed and the fixed heat load, is at most what the store holds. Rounding plays no part in them. The first follows from the second for any scheduler
  floor up to the IT load.

`lake comparator --paranoid` accepts all sixteen under six kernels with the standard axioms only. A Python
copy of the gate, the model and the step agrees with the Lean executable on 405,000 generated inputs: 300,000
gate decisions, 100,000 proposed designs and 5,000 whole runs through the Lean `loop`. The Proven Commons bar check reports items 2 to 6 as passing
([formal/BAR-REPORT.md](../formal/BAR-REPORT.md)).

What the eight do not say: that the model describes a real plant, or that it is free of mistakes. Its
constants are pinned from certificates that are claimed and not measured, eleven of its fourteen margins are
carried as constants, and the bounds and the scenario are declared by a person.

**Defects found, and what v0.3.1 did.** A separate agent read the statements against this prose and the
earlier floating-point model. It confirmed the units and that the integer model matches the floating-point
one. It also found five defects. A second, independent check reproduced all five in exact arithmetic.

1. Fixed. The objective subtracted the whole utility power of the shed load in an outage, including the part
   that does not depend on load. Every objective in v0.3.0 was about 18 ppm too high. The start was published
   as 0.914228 and is 0.914210.
2. Fixed. The outage margin counted IT heat and left out the fixed heat load, about 71 kWh in a 20-minute
   outage. With it counted, the start design's outage margin is 961,695 ppm, not 933,334, and it becomes the
   tightest margin at the start.
3. Fixed in part. A proposal identical to the design held was taken up and charged. It is now refused as
   `same`. A different design that scores the same is still taken up: the hardware changes that open headroom
   all score the same, so demanding a strict gain would stop the loop. So "never worse" is what is proved.
4. Open. Nothing requires the plant, the bounds or the start to make sense.
5. Open. A large move towards safety is refused as too far, and a start past a limit can never be repaired.

The two fixes changed every objective and margin figure in this note, and the loop's path with them. The two
runs recorded against v0.3.0 could not be carried over: replayed under the corrected model, only 2 of
their 15 proposals are decided the same way. They are kept in `results/v0.3.0/` and both runs were made
again.

## 12. The improvement loop

**VERIFIED** on a model (deterministic, replayed in Lean). Its safety, its bound and the fact that it never
gets worse are **machine-checked** (section 11). The plant model, the objective and the scenario are choices.
The figures illustrate the mechanism and predict nothing.

A genome holds three hardware genes (thermal store in kWh_th, liquid capture fraction, wall U-value), two
software genes (the scheduler's load floor, the share of load shed in a cooling outage) and the proposer's own
step scale. The plant model turns a genome into 14 margins: ten certified upstream and held constant, the
sensor margin of section 5, and three that move with the genes (sorption drive heat, load floor, outage
ride-through). The objective is useful IT energy per unit of utility energy over a scenario year with 12
outages of 20 minutes and 2,000 hours at 3% demand.

Each generation the proposer tries six single-gene changes. On even generations they are software changes,
scored by the objective. On odd generations they are hardware changes, scored by the headroom they open. The
best goes to the step function with a cost of one unit against a budget of 64. The step takes it up if it is
within the bounds, passes the exact gate and does not lower the objective. A design that is taken up becomes
the one held. The step scale doubles after an admission and halves after a refusal.

| | Run | Proposer with no reserve | Budget of 3 | Start on a limit |
|---|---|---|---|---|
| Proposals | 48 | 161 | 3 | 17 |
| Admitted | 45 | 62 | 3 | 0 |
| Refused by the gate | 3 | 99 | 0 | 17 |
| Objective at the end | 0.918990 | 0.916016 | 0.914210 | 0.914211 |

The start is 0.914210, except in the last column, which starts at 0.914211 and does not move. The run ended
with budget to spare because every hardware gene had reached the edge of
its search range. The ledger records both designs of every decision. `python3 verify.py --formal` gives the
two designs to the Lean executable, which works out the margins, the objective, the verdict and the budget
again: no mismatch on any of the 50. The floating-point gate of section 6 gives the same verdict on all 50.

Two other proposers have used the same step function.

**A recorded run by a language model.** `tools/propose.py` prints the design held, its margins, the radius,
the objective and the budget, and takes a proposal for one or more genes with a sentence of reasons. A
language model was given that output and nothing else, with a limit of 40 proposals. It made 12. 7
were taken up (3 hardware, 2 software, 2 changing both at once) and the rest were refused
(4 as `distance`, 1 as `worse`). The objective went from 0.914210 to 0.919529. A direct search over the software genes, with the
hardware genes at their most generous bounds, finds 0.919529 to be the best any design within the limits can
score, so the run reached 100.0% of the possible gain. The seeded search reached 89.9%. The proposals
and the reasons are in `results/model_run.json`. `verify.py` replays them and must reproduce
`results/model_ledger.json`.

**A second run, given the first one's notes.** The first run's closing notes were saved word for word in
`results/model_lessons.md`. A second instance of the same model, with no memory of the first run, was given
those notes and the same interface. It made 5 proposals and 5 were taken up, 4 of them changing
hardware and software together. It reached 0.919529, which is 100.0% of the possible gain. To reach the
objective both runs got to, the first needed 12 proposals and the second 5. Its own notes are in
`results/model_lessons_2.md`.

These are two runs of one model. They show that the interface is enough to work from and that notes can be
handed on. They do not measure how good a proposer a model is. Both runs end with the `load_floor` margin at 999,215 ppm, 785 from its limit: the
objective rewards a lower floor and nothing rewards headroom, so a good proposer drives the design to where it
can no longer change.

**An adversary.** `adversary_run` makes 3,007 proposals meant to break the loop: a capture fraction of 200%,
a negative store, a scheduler floor of zero and one below the plant's floor, a design that scores lower, a
store too small for one outage, a proposal that changes nothing, then random designs, half of them anywhere
in or just outside the bounds and half near the start. The verdicts were 55 `bounds`, 456 `budget`, 2389 `distance`, 64 `ok`, 38 `same`, 5 `worse`. The budget of 64 was spent
and not one change more was made. Every design held stayed within every limit and bound and the objective
never fell. The theorems of section 11 say this must be so for the Lean code. This run checks it on the
Python copy, and `--formal` replays all of it in Lean.

[VISION.md](VISION.md) discusses what the loop shows and how far it is from the system it stands in for.

## 13. A first look at a network: the load floor depends on the site

**VERIFIED** under assumption A-4. A-4, made here: at any recooling temperature the sorption chiller reaches
the same share of its reversible COP as at the design point. With 58 °C drive, 18 °C chilled water and 30 °C
recooling the reversible COP is 2.051, so the claimed 0.62 is a share of 0.302. The 30 °C is the design value
in funi-frame's certificate since v0.1.1, where it is marked as a proposal awaiting the owner's confirmation.

Section 3 gave the load floor as `q_fix / ((1 + COP) α − 1)`. Under A-4 the COP falls as the recooling
temperature rises, and the floor rises with it:

| Recooling | Sorption COP | Load floor | Share of nameplate |
|---|---|---|---|
| 30 °C | 0.620 | 0.564 MW | 5.6% |
| 34 °C | 0.399 | 1.127 MW | 11.3% |
| 36 °C | 0.325 | 1.687 MW | 16.9% |
| 38 °C | 0.266 | 2.804 MW | 28.0% |
| 40 °C | 0.217 | 6.113 MW | 61.1% |
| 41 °C | 0.196 | none: it cannot cool itself at any load | |

So the 41.5 °C of section 2 is a limit of principle and not a working limit. Well below it the campus has to
run most of its nameplate just to cool itself.

For a network this gives two results. A cool campus and a warm one (30 °C and 38 °C) cannot idle below
3.368 MW together, 16.8% of their nameplate, and the warm one's floor is 4.97 times the cool
one's. And in the upstream plant model utility power is a straight line in IT load whose slope, 1.0357 MW
per MW, does not depend on the site. Moving load from one campus to the other therefore changes no energy.
The placement problem of proposal 8 has no single optimum in this model: any split that keeps both campuses
above their floors uses the same energy. A useful network model needs a cost that differs by site first.

## Limits

- No measurement of any kind. Every input is the output of another model.
- The physical stack sits at "claimed" on the Ledger scale, apart from one preprint. See
  [CONVERGENCE.md](CONVERGENCE.md).
- funi-frame's verifier was re-run here and reproduces its certificate. The verifiers of funi-floors and
  venturi-collars were not re-run; their certificates were read as data.
- Tested on Python 3.13 only. The certificate rounds every figure, which should absorb differences between
  maths libraries, but no other version has been tried.
- One campus only. A network of campuses is not modelled.
- The loop between structure and intelligence is open. Four of its ten interfaces are checked. No sensor is
  read, no load is shed and no machine is driven. See [STRUCTURE.md](STRUCTURE.md).
- The improvement loop runs on a three-parameter thermal model with a seeded search as its proposer. See
  [VISION.md](VISION.md) for what that does and does not show.
- The load floor and the margin vector are steady-state. No transient is modelled.
