/-
  The code under proof: an exact gate for a plant, and the loop that runs on it.

  Every quantity is an integer. Margins are in parts per million of their
  limit, budgets and costs in whatever unit the caller fixes (watt-hours of
  heat for a thermal budget, counted changes for a change budget). There is
  no floating point anywhere, so there is nothing to round.

  `gate` is the gate. `evolve` applies one proposed change: an admitted
  candidate becomes the new baseline. `run` applies a whole list of
  proposals, whatever proposed them.
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

end PlantGate
