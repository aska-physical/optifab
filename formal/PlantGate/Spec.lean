/-
  The specification as Lean statements: the challenge file.

  A reviewer who did not write this file approves it, and `bar.toml` records
  the SHA-256 it had then. The proofs live in `PlantGate/Proofs.lean`;
  `lake comparator` checks that each one proves exactly the statement written
  here. The `sorry` below is expected in this file only.
-/

import PlantGate

open PlantGate

/-- Safety of the gate: an admitted step had a positive cost within the
    budget, a radius that is not negative, states of equal length, a move
    within the radius, and it spent exactly its cost. -/
theorem PlantGate.Spec.gate_ok_sound (base cand : List Int) (radius budget cost : Int)
    (h : (gate base cand radius budget cost).verdict = Verdict.ok) :
    0 < cost ∧ cost ≤ budget ∧ 0 ≤ radius ∧ base.length = cand.length
      ∧ distSq base cand ≤ radius * radius
      ∧ (gate base cand radius budget cost).remaining = budget - cost := sorry

/-- Usefulness of the gate: a step that meets every condition is admitted.
    A gate that refuses everything passes the safety statements and fails
    this one. -/
theorem PlantGate.Spec.gate_complete (base cand : List Int) (radius budget cost : Int)
    (hc : 0 < cost) (hb : cost ≤ budget) (hn : base ≠ []) (hl : base.length = cand.length)
    (hr : 0 ≤ radius) (hd : distSq base cand ≤ radius * radius) :
    (gate base cand radius budget cost).verdict = Verdict.ok := sorry

/-- A refused step spends nothing. -/
theorem PlantGate.Spec.refusal_spends_nothing (base cand : List Int) (radius budget cost : Int)
    (h : (gate base cand radius budget cost).verdict ≠ Verdict.ok) :
    (gate base cand radius budget cost).remaining = budget := sorry

/-- The budget never grows, and a budget that is not negative never becomes
    negative. No step can mint budget or overdraw it. -/
theorem PlantGate.Spec.budget_never_grows (base cand : List Int) (radius budget cost : Int) :
    (gate base cand radius budget cost).remaining ≤ budget
      ∧ (0 ≤ budget → 0 ≤ (gate base cand radius budget cost).remaining) := sorry

/-- Within the radius, no coordinate rises by more than the radius. -/
theorem PlantGate.Spec.no_margin_rises_past_radius (base cand : List Int) (radius : Int)
    (hr : 0 ≤ radius) (hd : distSq base cand ≤ radius * radius) :
    ∀ p ∈ List.zip base cand, p.2 - p.1 ≤ radius := sorry

/-- The envelope: when the radius is the headroom of the baseline, an
    admitted candidate has every margin at or below the limit. Nothing is
    assumed about the baseline: a baseline past the limit has negative
    headroom and admits nothing. -/
theorem PlantGate.Spec.accepted_stays_within (limit : Int) (base cand : List Int) (budget cost : Int)
    (h : (gate base cand (headroom limit base) budget cost).verdict = Verdict.ok) :
    ∀ x ∈ cand, x ≤ limit := sorry

/-- The loop is safe against any proposer. Start within the limit with a
    budget that is not negative. After any list of proposals whatever, every
    margin is still at or below the limit, the budget is still not negative,
    and it has not grown. -/
theorem PlantGate.Spec.run_safe (limit : Int) (steps : List (List Int × Int)) (s : List Int × Int)
    (hw : ∀ x ∈ s.1, x ≤ limit) (hb : 0 ≤ s.2) :
    (∀ x ∈ (run limit s steps).1, x ≤ limit) ∧ 0 ≤ (run limit s steps).2
      ∧ (run limit s steps).2 ≤ s.2 := sorry

/-- The loop is bounded by its budget. Every admitted change costs at least
    one unit, so the number of admitted changes plus the budget left never
    exceeds the budget at the start. Whoever sets the budget sets the most
    changes the system can ever make to itself. -/
theorem PlantGate.Spec.run_bounded (limit : Int) (steps : List (List Int × Int)) (s : List Int × Int) :
    (acceptedCount limit s steps : Int) + (run limit s steps).2 ≤ s.2 := sorry

/-- Usefulness of the loop over designs: a different design within the
    bounds that stays within the headroom and either strictly raises the
    objective or keeps it equal while strictly widening headroom is taken up,
    for one unit of budget. A loop that takes nothing up passes the safety
    statements below and fails this one. -/
theorem PlantGate.Spec.step_complete (p : Plant) (sc : Scenario) (limit : Int)
    (s : Genome × Int) (cand : Genome)
    (hne : cand ≠ s.1)
    (hb : 0 < s.2) (hin : inBounds p.lo p.hi cand = true)
    (hw : ∀ x ∈ margins p sc s.1, x ≤ limit)
    (hd : distSq (margins p sc s.1) (margins p sc cand)
      ≤ headroom limit (margins p sc s.1) * headroom limit (margins p sc s.1))
    (ho : objective p sc s.1 < objective p sc cand
      ∨ (objective p sc s.1 = objective p sc cand
          ∧ headroom limit (margins p sc s.1) < headroom limit (margins p sc cand))) :
    step p sc limit s cand = (cand, s.2 - 1) := sorry

/-- A proposal identical to the design held is never taken up, so it
    cannot be charged to the budget. -/
theorem PlantGate.Spec.same_design_not_taken_up (p : Plant) (sc : Scenario) (limit : Int)
    (s : Genome × Int) :
    accepts p sc limit s s.1 = false := sorry

/-- An equal-objective proposal that does not strictly widen headroom is
    refused, so no proposer can erode headroom or burn budget on neutral
    sideways moves at a tied objective. -/
theorem PlantGate.Spec.tie_headroom_decay_refused (p : Plant) (sc : Scenario) (limit : Int)
    (s : Genome × Int) (cand : Genome)
    (heq : objective p sc cand = objective p sc s.1)
    (hdec : headroom limit (margins p sc cand) ≤ headroom limit (margins p sc s.1)) :
    accepts p sc limit s cand = false := sorry

/-- A proposed design that is not taken up changes nothing: the design
    held and the budget are as they were. -/
theorem PlantGate.Spec.step_refusal_changes_nothing (p : Plant) (sc : Scenario) (limit : Int)
    (s : Genome × Int) (cand : Genome)
    (h : accepts p sc limit s cand = false) :
    step p sc limit s cand = s := sorry

/-- The loop over designs is safe against any proposer. Start from a
    design whose margins are within the limit, with a budget that is not
    negative. After any list of proposed designs whatever, the margins of
    the design held, as this model computes them, are still within the
    limit, the budget is not negative and it has not grown. -/
theorem PlantGate.Spec.loop_safe (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int)
    (hw : ∀ x ∈ margins p sc s.1, x ≤ limit) (hb : 0 ≤ s.2) :
    (∀ x ∈ margins p sc (loop p sc limit s cands).1, x ≤ limit)
      ∧ 0 ≤ (loop p sc limit s cands).2 ∧ (loop p sc limit s cands).2 ≤ s.2 := sorry

/-- The design held never leaves the bounds it started in. -/
theorem PlantGate.Spec.loop_in_bounds (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int)
    (h : inBounds p.lo p.hi s.1 = true) :
    inBounds p.lo p.hi (loop p sc limit s cands).1 = true := sorry

/-- The loop never gets worse. Whatever is proposed, the objective of the
    design held at the end is at least the objective at the start. -/
theorem PlantGate.Spec.loop_never_worse (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int) :
    objective p sc s.1 ≤ objective p sc (loop p sc limit s cands).1 := sorry

/-- Lexicographic Pareto monotonicity: after any list of proposed designs,
    either the objective strictly rose, or it stayed equal and the headroom
    did not fall. -/
theorem PlantGate.Spec.loop_lex_monotone (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int) :
    objective p sc s.1 < objective p sc (loop p sc limit s cands).1
      ∨ (objective p sc s.1 = objective p sc (loop p sc limit s cands).1
          ∧ headroom limit (margins p sc s.1)
              ≤ headroom limit (margins p sc (loop p sc limit s cands).1)) := sorry

/-- The number of designs taken up plus the budget left never exceeds the
    budget at the start. -/
theorem PlantGate.Spec.loop_bounded (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int) :
    (changes p sc limit s cands : Int) + (loop p sc limit s cands).2 ≤ s.2 := sorry

/-- What the limit means. With the limit at 1,000,000 parts per million,
    start from a design whose margins are within it. After any list of
    proposed designs, the design held still has enough captured heat to
    drive its chiller, still cools itself at the scheduler's load floor,
    and still holds one outage in its store. These are exact
    inequalities: the rounding of the margins plays no part. -/
theorem PlantGate.Spec.loop_keeps_physics (p : Plant) (sc : Scenario)
    (cands : List Genome) (s : Genome × Int)
    (hw : ∀ x ∈ margins p sc s.1, x ≤ 1000000) :
    DriveHeatSuffices p (loop p sc 1000000 s cands).1
      ∧ SelfCoolsAtFloor p (loop p sc 1000000 s cands).1
      ∧ RidesThrough p sc (loop p sc 1000000 s cands).1 := sorry

/-- Well-formedness rules out vacuous negative demands and zero capacities:
    fixed heat load, drive demand, and outage heat are all non-negative, the
    thermal store capacity is strictly positive, and the scheduler floor is
    strictly positive. -/
theorem PlantGate.Spec.wellformed_nonneg_demands (p : Plant) (sc : Scenario) (g : Genome)
    (hwf : WellFormed p sc g) :
    0 ≤ qFix p g ∧ 0 ≤ driveNum p g ∧ 0 ≤ outageNum p sc g
      ∧ 0 < outageDen g ∧ 0 < g.floor := sorry

/-- Non-vacuous physics invariant: on a well-formed plant and scenario, start
    within bounds and within the 1,000,000 ppm limit. After any list of
    proposals, the held design remains well-formed (strictly positive store
    and floor, capture and shed within `[0, 1,000,000]`), satisfies all three
    exact physical inequalities, and has non-negative drive and outage
    demands. -/
theorem PlantGate.Spec.loop_keeps_wellformed_physics (p : Plant) (sc : Scenario)
    (cands : List Genome) (s : Genome × Int)
    (hwp : WellFormedPlant p sc)
    (hin : inBounds p.lo p.hi s.1 = true)
    (hw : ∀ x ∈ margins p sc s.1, x ≤ 1000000) :
    WellFormed p sc (loop p sc 1000000 s cands).1
      ∧ DriveHeatSuffices p (loop p sc 1000000 s cands).1
      ∧ SelfCoolsAtFloor p (loop p sc 1000000 s cands).1
      ∧ RidesThrough p sc (loop p sc 1000000 s cands).1
      ∧ 0 ≤ driveNum p (loop p sc 1000000 s cands).1
      ∧ 0 ≤ outageNum p sc (loop p sc 1000000 s cands).1 := sorry

/-- Safety of the asymmetric gate in normal mode: an admitted `.ok` candidate
    has every margin at or below the limit, positive cost within budget, and
    spends exactly its cost. -/
theorem PlantGate.Spec.asym_gate_ok_stays_within (limit : Int) (base cand : List Int)
    (budget cost : Int)
    (h : (gateAsymmetric limit base cand budget cost).verdict = AsymVerdict.ok) :
    (∀ x ∈ cand, x ≤ limit) ∧ 0 < cost ∧ cost ≤ budget
      ∧ (gateAsymmetric limit base cand budget cost).remaining = budget - cost := sorry

/-- Completeness of the asymmetric gate for pure safety moves: starting
    within the limit with positive cost within budget, any non-empty
    same-length move that raises no margin is admitted as `.ok`, regardless
    of how far margins drop toward safety. -/
theorem PlantGate.Spec.asym_gate_pure_safety_admitted (limit : Int) (base cand : List Int)
    (budget cost : Int)
    (hc : 0 < cost) (hb : cost ≤ budget) (hn : base ≠ []) (hl : base.length = cand.length)
    (hw : ∀ x ∈ base, x ≤ limit)
    (hdown : ∀ p ∈ List.zip base cand, p.2 ≤ p.1) :
    (gateAsymmetric limit base cand budget cost).verdict = AsymVerdict.ok := sorry

/-- Strict Lyapunov recovery for out-of-limit baselines: an `.okRecovery` step
    starts from negative headroom, strictly increases headroom (strictly
    lowers the worst excess above `limit`), never pushes a safe coordinate
    above `limit` or worsens an already-violating coordinate, and spends
    exactly its positive cost. -/
theorem PlantGate.Spec.asym_gate_recovery_lyapunov_descent (limit : Int) (base cand : List Int)
    (budget cost : Int)
    (h : (gateAsymmetric limit base cand budget cost).verdict = AsymVerdict.okRecovery) :
    headroom limit base < 0
      ∧ headroom limit base < headroom limit cand
      ∧ max 0 (-headroom limit cand) < max 0 (-headroom limit base)
      ∧ (∀ p ∈ List.zip base cand, p.2 ≤ max p.1 limit)
      ∧ 0 < cost ∧ cost ≤ budget
      ∧ (gateAsymmetric limit base cand budget cost).remaining = budget - cost := sorry

/-- Safety and budget bound of the asymmetric loop: starting within the
    limit with non-negative budget, any sequence of proposals stays within
    the limit, keeps the budget non-negative and non-increasing, and admits
    at most the starting budget of changes. -/
theorem PlantGate.Spec.asym_run_safe_and_bounded (limit : Int) (steps : List (List Int × Int))
    (s : List Int × Int)
    (hw : ∀ x ∈ s.1, x ≤ limit) (hb : 0 ≤ s.2) :
    (∀ x ∈ (runAsymmetric limit s steps).1, x ≤ limit)
      ∧ 0 ≤ (runAsymmetric limit s steps).2
      ∧ (runAsymmetric limit s steps).2 ≤ s.2
      ∧ (asymAcceptedCount limit s steps : Int) + (runAsymmetric limit s steps).2 ≤ s.2 := sorry
