/-
  Command line front end, used by the differential tests and by the replay
  of the optifab ledger. Each input line is one decision:

      h LIMIT BUDGET COST ; BASE ... ; CAND ...     radius = headroom of BASE under LIMIT
      r RADIUS BUDGET COST ; BASE ... ; CAND ...    radius given

  It prints the verdict and the budget left. A line with eight parts is
  one proposed design, run through the model, the bounds, the gate and the
  objective:

      g LIMIT BUDGET ; PLANT (9) ; SCENARIO (5) ; LOW (5) ; HIGH (5) ; FIXED ... ; HELD (5) ; PROPOSED (5)

  It prints the verdict, the budget left, the objective of the design held
  and of the one proposed, and the margins of the one proposed. It calls
  the proved functions, not copies of them.
-/

import PlantGate

open PlantGate

def words (s : String) : List String :=
  (s.splitOn " ").filter (· ≠ "")

def verdictName : Verdict → String
  | .ok => "ok"
  | .cost => "cost"
  | .budget => "budget"
  | .shape => "shape"
  | .radius => "radius"
  | .distance => "distance"

def ints (s : String) : Option (List Int) :=
  (words s).mapM String.toInt?

def genomeOf : List Int → Option Genome
  | [a, b, c, d, e] => some ⟨a, b, c, d, e⟩
  | _ => none

/-- One proposed design. `accepts` and `step` decide; the name of a refusal is for the reader. -/
def design (limit budget : Int) (pl sc lo hi fixed held cand : List Int) : String :=
  match pl, sc, genomeOf lo, genomeOf hi, genomeOf held, genomeOf cand with
  | [pIt, cop, uaRoof, wallArea, dT, other, passive, aux, loopCop], [outMin, nOut, lowPpm, lowH, hours],
    some lo, some hi, some b, some c =>
    let p : Plant := ⟨pIt, cop, uaRoof, wallArea, dT, other, passive, aux, loopCop, fixed, lo, hi⟩
    let y : Scenario := ⟨outMin, nOut, lowPpm, lowH, hours⟩
    let j := judge p y limit (b, budget) c
    let name :=
      if accepts p y limit (b, budget) c = true then "ok"
      else if inBounds p.lo p.hi c = false then "bounds"
      else if j.verdict ≠ Verdict.ok then verdictName j.verdict
      else "worse"
    let after := step p y limit (b, budget) c
    let ms := " ".intercalate ((margins p y c).map toString)
    s!"{name} {after.2} {objective p y b} {objective p y c} ; {ms}"
  | _, _, _, _, _, _ => "error"

def answer (line : String) : String :=
  match line.splitOn ";" with
  | [head, pl, sc, lo, hi, fixed, held, cand] =>
    match words head, ints pl, ints sc, ints lo, ints hi, ints fixed, ints held, ints cand with
    | ["g", limit, budget], some pl, some sc, some lo, some hi, some fixed, some held, some cand =>
      match limit.toInt?, budget.toInt? with
      | some limit, some budget => design limit budget pl sc lo hi fixed held cand
      | _, _ => "error"
    | _, _, _, _, _, _, _, _ => "error"
  | [head, base, cand] =>
    match words head, (words base).mapM String.toInt?, (words cand).mapM String.toInt? with
    | [mode, x, budget, cost], some b, some c =>
      match x.toInt?, budget.toInt?, cost.toInt? with
      | some x, some budget, some cost =>
        if mode = "h" ∨ mode = "r" then
          let radius := if mode = "h" then headroom x b else x
          let o := gate b c radius budget cost
          s!"{verdictName o.verdict} {o.remaining}"
        else "error"
      | _, _, _ => "error"
    | _, _, _ => "error"
  | _ => "error"

def main : IO Unit := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  repeat
    let line ← stdin.getLine
    if line.isEmpty then break
    stdout.putStrLn (answer line.trimAscii.toString)
