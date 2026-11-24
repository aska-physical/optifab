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
  and of the one proposed, and the margins of the one proposed. A line that
  starts with `l` is a whole run: the same seven parts with the start design
  in place of HELD, then any number of proposed designs, each after a `;`.
  It goes through the proved `loop` and `changes` and prints the design held
  at the end, the budget left and the number of designs taken up. It calls
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

def plantOf (pl fixed : List Int) (lo hi : Genome) : Option Plant :=
  match pl with
  | [pIt, cop, uaRoof, wallArea, dT, other, passive, aux, loopCop] =>
    some ⟨pIt, cop, uaRoof, wallArea, dT, other, passive, aux, loopCop, fixed, lo, hi⟩
  | _ => none

def scenarioOf : List Int → Option Scenario
  | [outMin, nOut, lowPpm, lowH, hours] => some ⟨outMin, nOut, lowPpm, lowH, hours⟩
  | _ => none

/-- One proposed design. `accepts` and `step` decide; the name of a refusal is for the reader. -/
def design (limit budget : Int) (p : Plant) (y : Scenario) (b c : Genome) : String :=
  let j := judge p y limit (b, budget) c
  let name :=
    if accepts p y limit (b, budget) c = true then "ok"
    else if inBounds p.lo p.hi c = false then "bounds"
    else if j.verdict ≠ Verdict.ok then verdictName j.verdict
    else "worse"
  let after := step p y limit (b, budget) c
  let ms := " ".intercalate ((margins p y c).map toString)
  s!"{name} {after.2} {objective p y b} {objective p y c} ; {ms}"

/-- A whole list of proposed designs, through the proved `loop` and `changes`. -/
def wholeLoop (limit budget : Int) (p : Plant) (y : Scenario) (start : Genome) (cands : List Genome) : String :=
  let fin := loop p y limit (start, budget) cands
  s!"{fin.1.pcm} {fin.1.capture} {fin.1.wallU} {fin.1.floor} {fin.1.shed} {fin.2} {changes p y limit (start, budget) cands}"

def answer (line : String) : String :=
  match line.splitOn ";" with
  | head :: pl :: sc :: lo :: hi :: fixed :: held :: rest =>
    match words head, ints pl, ints sc, (ints lo).bind genomeOf, (ints hi).bind genomeOf, ints fixed,
        (ints held).bind genomeOf, rest.mapM (fun r => (ints r).bind genomeOf) with
    | [mode, limit, budget], some pl, some sc, some lo, some hi, some fixed, some held, some cands =>
      match limit.toInt?, budget.toInt?, plantOf pl fixed lo hi, scenarioOf sc with
      | some limit, some budget, some p, some y =>
        if mode = "g" then
          match cands with
          | [cand] => design limit budget p y held cand
          | _ => "error"
        else if mode = "l" then wholeLoop limit budget p y held cands
        else "error"
      | _, _, _, _ => "error"
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
