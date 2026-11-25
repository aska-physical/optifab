/-
  The code under proof: an exact gate for a plant, and the loop that runs on it.

  Every quantity is an integer. Margins are in parts per million of their
  limit, budgets and costs in whatever unit the caller fixes (watt-hours of
  heat for a thermal budget, counted changes for a change budget). There is
  no floating point anywhere, so there is nothing to round.

  `gate` is the gate. `evolve` applies one proposed change: an admitted
  candidate becomes the new baseline. `run` applies a whole list of
  proposals, whatever proposed them.

  The second half is the plant model and the loop over designs. A `Genome`
  is a design: three hardware numbers and two software numbers. `margins`
  turns a design into the margin vector and `objective` scores it. `step`
  applies one proposed design, `loop` a whole list of them.
-/

namespace PlantGate

/-- Sum of the squared moves, coordinate by coordinate. -/
def distSq : List Int → List Int → Int
  | b :: bs, c :: cs => (c - b) * (c - b) + distSq bs cs
  | _, _ => 0

/-- The smallest distance from any baseline margin to the limit.
    Negative when some margin is already past the limit. -/
def headroom (limit : Int) : List Int → Int
  | [] => 0
  | b :: bs =>
    match bs with
    | [] => limit - b
    | _ :: _ => min (limit - b) (headroom limit bs)

/-- Why a step was refused, or `ok`. -/
inductive Verdict where
  | ok
  | cost
  | budget
  | shape
  | radius
  | distance
  deriving DecidableEq, Repr

/-- A verdict and the budget left after it. -/
structure Outcome where
  verdict : Verdict
  remaining : Int

/-- The gate. A step is admitted when its cost is positive and within the
    budget, the two states have the same non-zero length, the radius is not
    negative, and the candidate lies within the radius of the baseline.
    A refused step leaves the budget as it was. -/
def gate (base cand : List Int) (radius budget cost : Int) : Outcome :=
  if cost ≤ 0 then ⟨.cost, budget⟩
  else if budget < cost then ⟨.budget, budget⟩
  else if base.length ≠ cand.length ∨ base = [] then ⟨.shape, budget⟩
  else if radius < 0 then ⟨.radius, budget⟩
  else if radius * radius < distSq base cand then ⟨.distance, budget⟩
  else ⟨.ok, budget - cost⟩

/-- One generation. The radius is the headroom of the current baseline.
    An admitted candidate becomes the new baseline and its cost is spent.
    A refused candidate changes nothing. -/
def evolve (limit : Int) (s : List Int × Int) (cand : List Int) (cost : Int) : List Int × Int :=
  let o := gate s.1 cand (headroom limit s.1) s.2 cost
  if o.verdict = Verdict.ok then (cand, o.remaining) else s

/-- Any number of generations, one proposal after another. -/
def run (limit : Int) : List Int × Int → List (List Int × Int) → List Int × Int
  | s, [] => s
  | s, (cand, cost) :: rest => run limit (evolve limit s cand cost) rest

/-- How many of the proposals were admitted. -/
def acceptedCount (limit : Int) : List Int × Int → List (List Int × Int) → Nat
  | _, [] => 0
  | s, (cand, cost) :: rest =>
    (if (gate s.1 cand (headroom limit s.1) s.2 cost).verdict = Verdict.ok then 1 else 0)
      + acceptedCount limit (evolve limit s cand cost) rest

/-! ## The plant model -/

/-- A design: what the loop may change. -/
structure Genome where
  /-- Thermal store, kWh of heat. Hardware. -/
  pcm : Int
  /-- Share of the IT heat captured in liquid, parts per million. Hardware. -/
  capture : Int
  /-- Wall U-value, mW/m²K. Hardware. -/
  wallU : Int
  /-- The scheduler's load floor, kW. Software. -/
  floor : Int
  /-- Share of the load the scheduler sheds in a cooling outage, parts per million. Software. -/
  shed : Int
  deriving DecidableEq

/-- The pinned plant: what no gene changes. -/
structure Plant where
  /-- IT load, W. -/
  pIt : Int
  /-- COP of the sorption chiller, parts per million. -/
  cop : Int
  /-- Roof conductance, mW/K. -/
  uaRoof : Int
  /-- Wall area, m². -/
  wallArea : Int
  /-- Design temperature difference across the envelope, mK. -/
  dT : Int
  /-- Other overhead, W. -/
  other : Int
  /-- Heat taken by the passive sinks, W. -/
  passive : Int
  /-- Auxiliaries, W. -/
  aux : Int
  /-- COP of the cooling loop, thousandths. -/
  loopCop : Int
  /-- The certified margins no gene moves, parts per million of their limits. -/
  fixed : List Int
  /-- The smallest value of each gene that could be built or set. -/
  lo : Genome
  /-- The largest value of each gene that could be built or set. -/
  hi : Genome

/-- The year the objective is scored on. -/
structure Scenario where
  /-- Length of one cooling outage, minutes. -/
  outMin : Int
  /-- Cooling outages in the year. -/
  nOut : Int
  /-- Demand in the low period as a share of the IT load, parts per million. -/
  lowPpm : Int
  /-- Hours of low demand in the year. -/
  lowH : Int
  /-- Hours in the year. -/
  hours : Int

/-- `a / b` rounded up, for a positive `b`. -/
def ceilDiv (a b : Int) : Int := (a + b - 1) / b

/-- A demand over a capacity, in parts per million and rounded up, so that
    a margin is never understated. A capacity that is not positive cannot
    be met at all and reads as ten times the limit. So does any ratio
    above ten. -/
def ppm (num den : Int) : Int :=
  if den ≤ 0 then 10000000 else min 10000000 (ceilDiv (1000000 * num) den)

/-- The fixed heat load in microwatts: what comes through the roof and the
    walls, plus the other overhead. -/
def qFix (p : Plant) (g : Genome) : Int :=
  (p.uaRoof + g.wallU * p.wallArea) * p.dT + p.other * 1000000

/-- Cooling the plant needs at full load: the IT heat the liquid loop does
    not capture, plus the fixed heat load. Scaled to the unit of `driveDen`. -/
def driveNum (p : Plant) (g : Genome) : Int :=
  ((1000000 - g.capture) * (p.pIt * 1000000) + 1000000 * qFix p g) * 1000000

/-- Cooling the sorption chiller can make at full load: the heat the liquid
    loop captures, times the chiller's COP. -/
def driveDen (p : Plant) (g : Genome) : Int :=
  p.cop * g.capture * (p.pIt * 1000000)

/-- Cooling gained per unit of IT load beyond what that load itself needs:
    `(1 + COP) × capture − 1`, in parts per million squared. -/
def coolGain (p : Plant) (g : Genome) : Int :=
  (1000000 + p.cop) * g.capture - 1000000000000

/-- The fixed heat load, in the unit of `coolGain p g * g.floor`. -/
def floorNum (p : Plant) (g : Genome) : Int := qFix p g * 1000

/-- Heat the store must take in one outage: the IT load that is not shed,
    plus the fixed heat load, for the length of the outage. -/
def outageNum (p : Plant) (sc : Scenario) (g : Genome) : Int :=
  (p.pIt * (1000000 - g.shed) + qFix p g) * sc.outMin

/-- What the store holds, in the unit of `outageNum`. -/
def outageDen (g : Genome) : Int := 60000000000 * g.pcm

/-- Margin: cooling needed over cooling the captured heat can drive. -/
def driveMargin (p : Plant) (g : Genome) : Int := ppm (driveNum p g) (driveDen p g)

/-- Margin: the plant's load floor over the scheduler's load floor. -/
def floorMargin (p : Plant) (g : Genome) : Int :=
  if coolGain p g ≤ 0 ∨ g.floor ≤ 0 then 10000000
  else ppm (floorNum p g) (coolGain p g * g.floor)

/-- Margin: outage heat over what the store holds. -/
def outageMargin (p : Plant) (sc : Scenario) (g : Genome) : Int :=
  ppm (outageNum p sc g) (outageDen g)

/-- The margin vector of a design: the certified margins, then the three
    that move with the genes. -/
def margins (p : Plant) (sc : Scenario) (g : Genome) : List Int :=
  p.fixed ++ [driveMargin p g, floorMargin p g, outageMargin p sc g]

/-- Utility power for an IT load `x` in microwatts, times the loop COP. -/
def utility (p : Plant) (x : Int) : Int :=
  x * p.loopCop + (x - p.passive * 1000000) * 1000 + (p.aux + p.other) * 1000000 * p.loopCop

/-- The objective: useful IT energy over utility energy for the scenario
    year, in parts per million and rounded down. Load the scheduler adds
    to reach its floor is not useful. Load shed in an outage is lost, and
    only the utility power that the shed load would have drawn is saved:
    the part of utility power that does not depend on load runs on. -/
def objective (p : Plant) (sc : Scenario) (g : Genome) : Int :=
  let full := p.pIt * 1000000
  let low := sc.lowPpm * p.pIt
  let itLow := max low (g.floor * 1000000000)
  let shedP := g.shed * p.pIt
  let tFull := (sc.hours - sc.lowH) * 60
  let tLow := sc.lowH * 60
  let tOut := sc.outMin * sc.nOut
  let useful := full * tFull + low * tLow - shedP * tOut
  let used := utility p full * tFull + utility p itLow * tLow
    - (utility p full - utility p (full - shedP)) * tOut
  if used ≤ 0 then 0 else (1000000 * useful * p.loopCop) / used

/-- Whether `x` lies from `lo` to `hi`. -/
def between (lo hi x : Int) : Bool := decide (lo ≤ x) && decide (x ≤ hi)

/-- Whether every gene lies within what could be built or set. -/
def inBounds (lo hi g : Genome) : Bool :=
  between lo.pcm hi.pcm g.pcm && between lo.capture hi.capture g.capture
    && between lo.wallU hi.wallU g.wallU && between lo.floor hi.floor g.floor
    && between lo.shed hi.shed g.shed

/-! ## The loop over designs -/

/-- The gate's answer for a proposed design. The radius is the headroom
    of the design held now, and a change costs one unit of budget. -/
def judge (p : Plant) (sc : Scenario) (limit : Int) (s : Genome × Int) (cand : Genome) : Outcome :=
  gate (margins p sc s.1) (margins p sc cand) (headroom limit (margins p sc s.1)) s.2 1

/-- Whether `cand` strictly improves the objective, or holds it equal while
    strictly widening headroom. This stops a proposer from spending budget to
    erode headroom at an equal objective while still allowing hardware changes
    that open headroom for later software gains. -/
def lexImproves (p : Plant) (sc : Scenario) (limit : Int) (held cand : Genome) : Bool :=
  decide (objective p sc held < objective p sc cand)
    || (decide (objective p sc held = objective p sc cand)
        && decide (headroom limit (margins p sc held) < headroom limit (margins p sc cand)))

/-- Whether a proposed design is taken up. It must differ from the design
    held, lie within the bounds, pass the gate, and either raise the
    objective or keep it equal while strictly widening headroom. -/
def accepts (p : Plant) (sc : Scenario) (limit : Int) (s : Genome × Int) (cand : Genome) : Bool :=
  decide (cand ≠ s.1) && inBounds p.lo p.hi cand
    && decide ((judge p sc limit s cand).verdict = Verdict.ok)
    && lexImproves p sc limit s.1 cand

/-- One generation over designs. A design that is taken up becomes the
    one held, and the budget falls to what the gate left. Otherwise
    nothing changes. -/
def step (p : Plant) (sc : Scenario) (limit : Int) (s : Genome × Int) (cand : Genome) : Genome × Int :=
  if accepts p sc limit s cand = true then (cand, (judge p sc limit s cand).remaining) else s

/-- Any number of generations, one proposed design after another. -/
def loop (p : Plant) (sc : Scenario) (limit : Int) : Genome × Int → List Genome → Genome × Int
  | s, [] => s
  | s, cand :: rest => loop p sc limit (step p sc limit s cand) rest

/-- How many of the proposed designs were taken up. -/
def changes (p : Plant) (sc : Scenario) (limit : Int) : Genome × Int → List Genome → Nat
  | _, [] => 0
  | s, cand :: rest =>
    (if accepts p sc limit s cand = true then 1 else 0)
      + changes p sc limit (step p sc limit s cand) rest

/-! ## What the limits mean, stated without rounding -/

/-- The captured heat, through the chiller, covers the cooling the plant
    needs at full load. For a scheduler floor at or below the IT load this
    follows from `SelfCoolsAtFloor`. -/
def DriveHeatSuffices (p : Plant) (g : Genome) : Prop :=
  0 < driveDen p g ∧ driveNum p g ≤ driveDen p g

/-- At the scheduler's load floor the plant still cools itself. -/
def SelfCoolsAtFloor (p : Plant) (g : Genome) : Prop :=
  0 < coolGain p g ∧ 0 < g.floor ∧ floorNum p g ≤ coolGain p g * g.floor

/-- The store holds the heat of one outage: the IT load not shed and the
    fixed heat load. -/
def RidesThrough (p : Plant) (sc : Scenario) (g : Genome) : Prop :=
  0 < outageDen g ∧ outageNum p sc g ≤ outageDen g

/-! ## Well-formed inputs -/

/-- Physical and domain validity of the fixed plant, its bounds, and the
    scenario year. Rules out negative loads, zero-length outages, capture or
    shed bounds above 1,000,000 ppm, and inverted bounds. -/
def WellFormedPlant (p : Plant) (sc : Scenario) : Prop :=
  0 < p.pIt ∧ 0 < p.cop ∧ 0 ≤ p.uaRoof ∧ 0 ≤ p.wallArea ∧ 0 ≤ p.dT
    ∧ 0 ≤ p.other ∧ 0 ≤ p.passive ∧ 0 ≤ p.aux ∧ 0 < p.loopCop
    ∧ 0 < p.lo.pcm ∧ p.lo.pcm ≤ p.hi.pcm
    ∧ 0 ≤ p.lo.capture ∧ p.lo.capture ≤ p.hi.capture ∧ p.hi.capture ≤ 1000000
    ∧ 0 ≤ p.lo.wallU ∧ p.lo.wallU ≤ p.hi.wallU
    ∧ 0 ≤ p.lo.floor ∧ p.lo.floor ≤ p.hi.floor
    ∧ 0 ≤ p.lo.shed ∧ p.lo.shed ≤ p.hi.shed ∧ p.hi.shed ≤ 1000000
    ∧ 0 < sc.outMin ∧ 0 ≤ sc.nOut
    ∧ 0 ≤ sc.lowPpm ∧ sc.lowPpm ≤ 1000000
    ∧ 0 ≤ sc.lowH ∧ sc.lowH ≤ sc.hours ∧ 0 < sc.hours

/-- Physical validity of a design: positive store and load floor, non-negative
    wall U-value, and capture and shed shares in `[0, 1,000,000]` ppm. -/
def WellFormedGenome (g : Genome) : Prop :=
  0 < g.pcm ∧ 0 ≤ g.capture ∧ g.capture ≤ 1000000 ∧ 0 ≤ g.wallU
    ∧ 0 < g.floor ∧ 0 ≤ g.shed ∧ g.shed ≤ 1000000

/-- A plant, scenario, and design that all make physical sense. -/
def WellFormed (p : Plant) (sc : Scenario) (g : Genome) : Prop :=
  WellFormedPlant p sc ∧ WellFormedGenome g

/-- Executable check for `WellFormedPlant`. -/
def wellFormedPlantBool (p : Plant) (sc : Scenario) : Bool :=
  decide (0 < p.pIt) && decide (0 < p.cop) && decide (0 ≤ p.uaRoof)
    && decide (0 ≤ p.wallArea) && decide (0 ≤ p.dT) && decide (0 ≤ p.other)
    && decide (0 ≤ p.passive) && decide (0 ≤ p.aux) && decide (0 < p.loopCop)
    && decide (0 < p.lo.pcm) && decide (p.lo.pcm ≤ p.hi.pcm)
    && decide (0 ≤ p.lo.capture) && decide (p.lo.capture ≤ p.hi.capture)
    && decide (p.hi.capture ≤ 1000000)
    && decide (0 ≤ p.lo.wallU) && decide (p.lo.wallU ≤ p.hi.wallU)
    && decide (0 ≤ p.lo.floor) && decide (p.lo.floor ≤ p.hi.floor)
    && decide (0 ≤ p.lo.shed) && decide (p.lo.shed ≤ p.hi.shed)
    && decide (p.hi.shed ≤ 1000000)
    && decide (0 < sc.outMin) && decide (0 ≤ sc.nOut)
    && decide (0 ≤ sc.lowPpm) && decide (sc.lowPpm ≤ 1000000)
    && decide (0 ≤ sc.lowH) && decide (sc.lowH ≤ sc.hours) && decide (0 < sc.hours)

/-- Executable check for `WellFormedGenome`. -/
def wellFormedGenomeBool (g : Genome) : Bool :=
  decide (0 < g.pcm) && decide (0 ≤ g.capture) && decide (g.capture ≤ 1000000)
    && decide (0 ≤ g.wallU) && decide (0 < g.floor)
    && decide (0 ≤ g.shed) && decide (g.shed ≤ 1000000)

/-- Executable check for `WellFormed`. -/
def wellFormedBool (p : Plant) (sc : Scenario) (g : Genome) : Bool :=
  wellFormedPlantBool p sc && wellFormedGenomeBool g

/-! ## Asymmetric upward gate and out-of-limit recovery -/

/-- Upward move in one coordinate: `max 0 (c - b)`. A move that lowers a margin
    (toward safety) contributes zero. -/
def posDiff (b c : Int) : Int :=
  if b < c then c - b else 0

/-- Sum of squared upward moves, coordinate by coordinate. -/
def posDistSq : List Int → List Int → Int
  | b :: bs, c :: cs => posDiff b c * posDiff b c + posDistSq bs cs
  | _, _ => 0

/-- Recovery monotonicity: no safe coordinate may cross above `limit`, and no
    already-violating coordinate may rise further. -/
def noNewExcess (limit : Int) : List Int → List Int → Bool
  | b :: bs, c :: cs => decide (c ≤ max b limit) && noNewExcess limit bs cs
  | _, _ => true

/-- Why an asymmetric gate step was refused, or how it was admitted. -/
inductive AsymVerdict where
  | ok
  | okRecovery
  | cost
  | budget
  | shape
  | distance
  | noImprovement
  deriving DecidableEq, Repr

/-- Whether an asymmetric verdict admits the candidate. -/
def AsymVerdict.admitted : AsymVerdict → Bool
  | .ok => true
  | .okRecovery => true
  | _ => false

/-- An asymmetric gate verdict and the budget left after it. -/
structure AsymOutcome where
  verdict : AsymVerdict
  remaining : Int

/-- Asymmetric gate with out-of-limit recovery.
    Within the limit (`0 ≤ headroom limit base`), only upward margin moves
    count against the headroom radius (`posDistSq base cand ≤ r²`), so pure
    safety moves of any size are admitted. Past the limit (`headroom < 0`),
    recovery mode admits a candidate iff it strictly widens headroom (strictly
    lowers the worst excess above `limit`) without creating any new violation
    or worsening any existing one. -/
def gateAsymmetric (limit : Int) (base cand : List Int) (budget cost : Int) : AsymOutcome :=
  if cost ≤ 0 then ⟨.cost, budget⟩
  else if budget < cost then ⟨.budget, budget⟩
  else if base.length ≠ cand.length ∨ base = [] then ⟨.shape, budget⟩
  else
    let r := headroom limit base
    if r < 0 then
      if r < headroom limit cand ∧ noNewExcess limit base cand = true then
        ⟨.okRecovery, budget - cost⟩
      else
        ⟨.noImprovement, budget⟩
    else if r * r < posDistSq base cand then
      ⟨.distance, budget⟩
    else
      ⟨.ok, budget - cost⟩

/-- One generation under the asymmetric gate. -/
def evolveAsymmetric (limit : Int) (s : List Int × Int) (cand : List Int) (cost : Int) : List Int × Int :=
  let o := gateAsymmetric limit s.1 cand s.2 cost
  if o.verdict.admitted = true then (cand, o.remaining) else s

/-- Any number of generations under the asymmetric gate. -/
def runAsymmetric (limit : Int) : List Int × Int → List (List Int × Int) → List Int × Int
  | s, [] => s
  | s, (cand, cost) :: rest => runAsymmetric limit (evolveAsymmetric limit s cand cost) rest

/-- How many proposals were admitted under the asymmetric gate. -/
def asymAcceptedCount (limit : Int) : List Int × Int → List (List Int × Int) → Nat
  | _, [] => 0
  | s, (cand, cost) :: rest =>
    (if (gateAsymmetric limit s.1 cand s.2 cost).verdict.admitted = true then 1 else 0)
      + asymAcceptedCount limit (evolveAsymmetric limit s cand cost) rest

end PlantGate
