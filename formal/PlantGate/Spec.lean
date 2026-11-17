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
