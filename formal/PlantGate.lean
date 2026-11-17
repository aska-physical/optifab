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

/-- Heat the sorption chiller needs at full load. -/
def driveNum (p : Plant) (g : Genome) : Int :=
  ((1000000 - g.capture) * (p.pIt * 1000000) + 1000000 * qFix p g) * 1000000

/-- Heat the liquid loop captures at full load, times the chiller's COP,
    in the unit of `driveNum`. -/
def driveDen (p : Plant) (g : Genome) : Int :=
  p.cop * g.capture * (p.pIt * 1000000)

/-- Cooling gained per unit of IT load beyond what that load itself needs:
    `(1 + COP) × capture − 1`, in parts per million squared. -/
def coolGain (p : Plant) (g : Genome) : Int :=
  (1000000 + p.cop) * g.capture - 1000000000000

/-- The fixed heat load, in the unit of `coolGain p g * g.floor`. -/
def floorNum (p : Plant) (g : Genome) : Int := qFix p g * 1000

/-- Heat the store must take in one outage, after shedding. -/
def outageNum (p : Plant) (sc : Scenario) (g : Genome) : Int :=
  p.pIt * (1000000 - g.shed) * sc.outMin

/-- What the store holds, in the unit of `outageNum`. -/
def outageDen (g : Genome) : Int := 60000000000 * g.pcm

/-- Margin: drive heat needed over drive heat captured. -/
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
    to reach its floor is not useful. Load shed in an outage is lost. -/
def objective (p : Plant) (sc : Scenario) (g : Genome) : Int :=
  let full := p.pIt * 1000000
  let low := sc.lowPpm * p.pIt
  let itLow := max low (g.floor * 1000000000)
  let shedP := g.shed * p.pIt
  let tFull := (sc.hours - sc.lowH) * 60
  let tLow := sc.lowH * 60
  let tOut := sc.outMin * sc.nOut
  let useful := full * tFull + low * tLow - shedP * tOut
  let used := utility p full * tFull + utility p itLow * tLow - utility p shedP * tOut
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

/-- Whether a proposed design is taken up. It must lie within the bounds,
    pass the gate, and not lower the objective. -/
def accepts (p : Plant) (sc : Scenario) (limit : Int) (s : Genome × Int) (cand : Genome) : Bool :=
  inBounds p.lo p.hi cand && decide ((judge p sc limit s cand).verdict = Verdict.ok)
    && decide (objective p sc s.1 ≤ objective p sc cand)

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
    needs at full load. -/
def DriveHeatSuffices (p : Plant) (g : Genome) : Prop :=
  0 < driveDen p g ∧ driveNum p g ≤ driveDen p g

/-- At the scheduler's load floor the plant still cools itself. -/
def SelfCoolsAtFloor (p : Plant) (g : Genome) : Prop :=
  0 < coolGain p g ∧ 0 < g.floor ∧ floorNum p g ≤ coolGain p g * g.floor

/-- The store holds the heat of one outage, after shedding. -/
def RidesThrough (p : Plant) (sc : Scenario) (g : Genome) : Prop :=
  0 < outageDen g ∧ outageNum p sc g ≤ outageDen g

end PlantGate
