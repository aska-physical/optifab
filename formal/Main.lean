/-
  Command line front end, used by the differential tests and by the replay
  of the optifab ledger. Each input line is one decision:

      h LIMIT BUDGET COST ; BASE ... ; CAND ...     radius = headroom of BASE under LIMIT
      r RADIUS BUDGET COST ; BASE ... ; CAND ...    radius given

  It prints the verdict and the budget left. It calls the proved functions,
  not copies of them.
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

def answer (line : String) : String :=
  match line.splitOn ";" with
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
