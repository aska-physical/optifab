/-
  Proofs of the statements in `PlantGate/Spec.lean`, under the same names.
-/

import PlantGate

open PlantGate

namespace PlantGate.Proofs

/-- If `d² ≤ r²` and `r` is not negative then `d ≤ r`. -/
theorem le_of_sq_le (d r : Int) (hr : 0 ≤ r) (h : d * d ≤ r * r) : d ≤ r := by
  by_cases hd : d ≤ r
  · exact hd
  · have h1 : r < d := by omega
    have h2 : r * r ≤ r * d := Int.mul_le_mul_of_nonneg_left (by omega) hr
    have h3 : r * d < d * d := Int.mul_lt_mul_of_pos_right h1 (by omega)
    omega

theorem sq_nonneg (d : Int) : 0 ≤ d * d := by
  by_cases h : 0 ≤ d
  · exact Int.mul_nonneg h h
  · have h' : 0 ≤ -d := by omega
    have := Int.mul_nonneg h' h'
    rwa [Int.neg_mul_neg] at this

theorem distSq_nonneg : ∀ (base cand : List Int), 0 ≤ distSq base cand
  | [], _ => by simp [distSq]
  | _ :: _, [] => by simp [distSq]
  | b :: bs, c :: cs => by
    have h1 : 0 ≤ (c - b) * (c - b) := sq_nonneg (c - b)
    have h2 := distSq_nonneg bs cs
    simp only [distSq]
    omega

theorem coord (r : Int) (hr : 0 ≤ r) :
    ∀ (base cand : List Int), distSq base cand ≤ r * r → ∀ p ∈ List.zip base cand, p.2 - p.1 ≤ r
  | [], _, _ => by simp
  | _ :: _, [], _ => by simp
  | b :: bs, c :: cs, hd => by
    intro p hp
    simp only [distSq] at hd
    have h1 : 0 ≤ (c - b) * (c - b) := sq_nonneg (c - b)
    have h2 := distSq_nonneg bs cs
    rw [List.zip_cons_cons] at hp
    rcases List.mem_cons.mp hp with rfl | hp'
    · show c - b ≤ r
      exact le_of_sq_le _ _ hr (by omega)
    · exact coord r hr bs cs (by omega) p hp'

theorem headroom_le (limit : Int) : ∀ (base : List Int), ∀ b ∈ base, headroom limit base ≤ limit - b
  | [], _, h => by simp at h
  | [b0], b, h => by
    have : b = b0 := by simpa using h
    subst this
    simp [headroom]
  | b0 :: b1 :: bs, b, h => by
    have ih := headroom_le limit (b1 :: bs)
    have e : headroom limit (b0 :: b1 :: bs) = min (limit - b0) (headroom limit (b1 :: bs)) := by
      simp [headroom]
    rw [e]
    rcases List.mem_cons.mp h with rfl | h'
    · exact Int.min_le_left _ _
    · exact Int.le_trans (Int.min_le_right _ _) (ih b h')

theorem within_of (limit r : Int) (hr : 0 ≤ r) :
    ∀ (base cand : List Int), base.length = cand.length → distSq base cand ≤ r * r →
      (∀ b ∈ base, r ≤ limit - b) → ∀ x ∈ cand, x ≤ limit
  | [], [], _, _, _ => by simp
  | [], _ :: _, hl, _, _ => by simp at hl
  | _ :: _, [], hl, _, _ => by simp at hl
  | b :: bs, c :: cs, hl, hd, hh => by
    intro x hx
    simp only [distSq] at hd
    have h1 : 0 ≤ (c - b) * (c - b) := sq_nonneg (c - b)
    have h2 := distSq_nonneg bs cs
    rcases List.mem_cons.mp hx with rfl | hx'
    · have h3 := le_of_sq_le (x - b) r hr (by omega)
      have h4 := hh b (by simp)
      omega
    · exact within_of limit r hr bs cs (by simpa using hl) (by omega)
        (fun b' hb' => hh b' (by simp [hb'])) x hx'

theorem headroom_nonneg (limit : Int) :
    ∀ (base : List Int), (∀ b ∈ base, b ≤ limit) → 0 ≤ headroom limit base
  | [], _ => by simp [headroom]
  | [b0], h => by
    have h0 := h b0 (by simp)
    simp only [headroom]
    omega
  | b0 :: b1 :: bs, h => by
    have ih := headroom_nonneg limit (b1 :: bs) (fun b hb => h b (by simp [hb]))
    have e : headroom limit (b0 :: b1 :: bs) = min (limit - b0) (headroom limit (b1 :: bs)) := by
      simp [headroom]
    rw [e]
    have h0 := h b0 (by simp)
    exact Int.le_min.mpr ⟨by omega, ih⟩

/-- A margin at or below 1,000,000 means the demand is at most the capacity, exactly. -/
theorem ppm_le (num den : Int) (h : ppm num den ≤ 1000000) : 0 < den ∧ num ≤ den := by
  unfold ppm at h
  by_cases hd : den ≤ 0
  · simp only [hd, ↓reduceIte] at h
    omega
  · simp only [hd, ↓reduceIte] at h
    have hpos : 0 < den := by omega
    refine ⟨hpos, ?_⟩
    by_cases hn : num ≤ den
    · exact hn
    · have h1 : (1000001 : Int) * den ≤ 1000000 * num + den - 1 := by omega
      have h2 : (1000001 : Int) ≤ (1000000 * num + den - 1) / den := Int.le_ediv_of_mul_le hpos h1
      unfold ceilDiv at h
      rw [Int.min_def] at h
      split at h <;> omega

theorem margins_ne_nil (p : Plant) (sc : Scenario) (g : Genome) : margins p sc g ≠ [] := by
  simp [margins]

theorem margins_length (p : Plant) (sc : Scenario) (a b : Genome) :
    (margins p sc a).length = (margins p sc b).length := by
  simp [margins]

theorem moving_le (p : Plant) (sc : Scenario) (g : Genome) (limit : Int)
    (hw : ∀ x ∈ margins p sc g, x ≤ limit) :
    driveMargin p g ≤ limit ∧ floorMargin p g ≤ limit ∧ outageMargin p sc g ≤ limit := by
  refine ⟨hw _ ?_, hw _ ?_, hw _ ?_⟩ <;> simp [margins]

theorem physics_of (p : Plant) (sc : Scenario) (g : Genome)
    (hw : ∀ x ∈ margins p sc g, x ≤ 1000000) :
    DriveHeatSuffices p g ∧ SelfCoolsAtFloor p g ∧ RidesThrough p sc g := by
  have m := moving_le p sc g 1000000 hw
  refine ⟨ppm_le _ _ m.1, ?_, ppm_le _ _ m.2.2⟩
  have hf := m.2.1
  unfold floorMargin at hf
  by_cases hc : coolGain p g ≤ 0 ∨ g.floor ≤ 0
  · simp only [hc, ↓reduceIte] at hf
    omega
  · simp only [hc, ↓reduceIte] at hf
    have a := ppm_le _ _ hf
    have h1 : 0 < coolGain p g := by
      by_cases h : coolGain p g ≤ 0
      · exact absurd (Or.inl h) hc
      · omega
    have h2 : 0 < g.floor := by
      by_cases h : g.floor ≤ 0
      · exact absurd (Or.inr h) hc
      · omega
    exact ⟨h1, h2, a.2⟩

end PlantGate.Proofs

open PlantGate.Proofs

theorem PlantGate.Spec.gate_ok_sound (base cand : List Int) (radius budget cost : Int)
    (h : (gate base cand radius budget cost).verdict = Verdict.ok) :
    0 < cost ∧ cost ≤ budget ∧ 0 ≤ radius ∧ base.length = cand.length
      ∧ distSq base cand ≤ radius * radius
      ∧ (gate base cand radius budget cost).remaining = budget - cost := by
  by_cases h1 : cost ≤ 0
  · simp [gate, h1] at h
  by_cases h2 : budget < cost
  · simp [gate, h1, h2] at h
  by_cases h3 : base.length ≠ cand.length ∨ base = []
  · simp [gate, h1, h2, h3] at h
  by_cases h4 : radius < 0
  · simp [gate, h1, h2, h3, h4] at h
  by_cases h5 : radius * radius < distSq base cand
  · simp [gate, h1, h2, h3, h4, h5] at h
  · have hl : base.length = cand.length := by
      by_cases e : base.length = cand.length
      · exact e
      · exact absurd (Or.inl e) h3
    refine ⟨by omega, by omega, by omega, hl, by omega, ?_⟩
    simp [gate, h1, h2, h3, h4, h5]

theorem PlantGate.Spec.gate_complete (base cand : List Int) (radius budget cost : Int)
    (hc : 0 < cost) (hb : cost ≤ budget) (hn : base ≠ []) (hl : base.length = cand.length)
    (hr : 0 ≤ radius) (hd : distSq base cand ≤ radius * radius) :
    (gate base cand radius budget cost).verdict = Verdict.ok := by
  have h1 : ¬ cost ≤ 0 := by omega
  have h2 : ¬ budget < cost := by omega
  have h3 : ¬ (base.length ≠ cand.length ∨ base = []) := by
    intro h
    rcases h with h | h
    · exact h hl
    · exact hn h
  have h4 : ¬ radius < 0 := by omega
  have h5 : ¬ radius * radius < distSq base cand := by omega
  simp [gate, h1, h2, h3, h4, h5]

theorem PlantGate.Spec.refusal_spends_nothing (base cand : List Int) (radius budget cost : Int)
    (h : (gate base cand radius budget cost).verdict ≠ Verdict.ok) :
    (gate base cand radius budget cost).remaining = budget := by
  by_cases h1 : cost ≤ 0
  · simp [gate, h1]
  by_cases h2 : budget < cost
  · simp [gate, h1, h2]
  by_cases h3 : base.length ≠ cand.length ∨ base = []
  · simp [gate, h1, h2, h3]
  by_cases h4 : radius < 0
  · simp [gate, h1, h2, h3, h4]
  by_cases h5 : radius * radius < distSq base cand
  · simp [gate, h1, h2, h3, h4, h5]
  · exact absurd (by simp [gate, h1, h2, h3, h4, h5]) h

theorem PlantGate.Spec.budget_never_grows (base cand : List Int) (radius budget cost : Int) :
    (gate base cand radius budget cost).remaining ≤ budget
      ∧ (0 ≤ budget → 0 ≤ (gate base cand radius budget cost).remaining) := by
  by_cases h : (gate base cand radius budget cost).verdict = Verdict.ok
  · have s := PlantGate.Spec.gate_ok_sound base cand radius budget cost h
    rw [s.2.2.2.2.2]
    exact ⟨by omega, fun _ => by omega⟩
  · rw [PlantGate.Spec.refusal_spends_nothing base cand radius budget cost h]
    exact ⟨by omega, fun hb => hb⟩

theorem PlantGate.Spec.no_margin_rises_past_radius (base cand : List Int) (radius : Int)
    (hr : 0 ≤ radius) (hd : distSq base cand ≤ radius * radius) :
    ∀ p ∈ List.zip base cand, p.2 - p.1 ≤ radius :=
  coord radius hr base cand hd

theorem PlantGate.Spec.accepted_stays_within (limit : Int) (base cand : List Int) (budget cost : Int)
    (h : (gate base cand (headroom limit base) budget cost).verdict = Verdict.ok) :
    ∀ x ∈ cand, x ≤ limit := by
  have s := PlantGate.Spec.gate_ok_sound base cand (headroom limit base) budget cost h
  exact within_of limit (headroom limit base) s.2.2.1 base cand s.2.2.2.1 s.2.2.2.2.1
    (fun b hb => headroom_le limit base b hb)

theorem PlantGate.Proofs.evolve_safe (limit : Int) (s : List Int × Int) (cand : List Int) (cost : Int)
    (hw : ∀ x ∈ s.1, x ≤ limit) (hb : 0 ≤ s.2) :
    (∀ x ∈ (evolve limit s cand cost).1, x ≤ limit) ∧ 0 ≤ (evolve limit s cand cost).2
      ∧ (evolve limit s cand cost).2 ≤ s.2 := by
  by_cases h : (gate s.1 cand (headroom limit s.1) s.2 cost).verdict = Verdict.ok
  · have a := PlantGate.Spec.accepted_stays_within limit s.1 cand s.2 cost h
    have g := PlantGate.Spec.budget_never_grows s.1 cand (headroom limit s.1) s.2 cost
    simp only [evolve, h, ite_true]
    exact ⟨a, g.2 hb, g.1⟩
  · simp only [evolve, h, ite_false]
    exact ⟨hw, hb, by omega⟩

theorem PlantGate.Spec.run_safe (limit : Int) (steps : List (List Int × Int)) (s : List Int × Int)
    (hw : ∀ x ∈ s.1, x ≤ limit) (hb : 0 ≤ s.2) :
    (∀ x ∈ (run limit s steps).1, x ≤ limit) ∧ 0 ≤ (run limit s steps).2
      ∧ (run limit s steps).2 ≤ s.2 := by
  induction steps generalizing s with
  | nil => exact ⟨hw, hb, by simp [run]⟩
  | cons step rest ih =>
    obtain ⟨cand, cost⟩ := step
    have e := PlantGate.Proofs.evolve_safe limit s cand cost hw hb
    have r := ih (evolve limit s cand cost) e.1 e.2.1
    simp only [run]
    exact ⟨r.1, r.2.1, by omega⟩

theorem PlantGate.Spec.run_bounded (limit : Int) (steps : List (List Int × Int)) (s : List Int × Int) :
    (acceptedCount limit s steps : Int) + (run limit s steps).2 ≤ s.2 := by
  induction steps generalizing s with
  | nil => simp [acceptedCount, run]
  | cons step rest ih =>
    obtain ⟨cand, cost⟩ := step
    have r := ih (evolve limit s cand cost)
    simp only [acceptedCount, run]
    by_cases h : (gate s.1 cand (headroom limit s.1) s.2 cost).verdict = Verdict.ok
    · have a := PlantGate.Spec.gate_ok_sound s.1 cand (headroom limit s.1) s.2 cost h
      have e : (evolve limit s cand cost).2 = s.2 - cost := by
        simp only [evolve, h, ite_true]
        exact a.2.2.2.2.2
      simp only [h, ite_true]
      omega
    · have e : evolve limit s cand cost = s := by
        simp only [evolve, h, ite_false]
      simp only [h, ite_false]
      rw [e] at r ⊢
      omega

namespace PlantGate.Proofs

/-- An admitted design has margins within the limit and cost exactly one unit. -/
theorem judge_ok (p : Plant) (sc : Scenario) (limit : Int) (s : Genome × Int) (cand : Genome)
    (h : (judge p sc limit s cand).verdict = Verdict.ok) :
    (∀ x ∈ margins p sc cand, x ≤ limit) ∧ (judge p sc limit s cand).remaining = s.2 - 1
      ∧ 1 ≤ s.2 := by
  unfold judge at h ⊢
  have a := PlantGate.Spec.accepted_stays_within limit _ _ _ _ h
  have g := PlantGate.Spec.gate_ok_sound _ _ _ _ _ h
  exact ⟨a, g.2.2.2.2.2, g.2.1⟩

/-- A step either takes the design up, with everything that implies, or changes nothing. -/
theorem step_cases (p : Plant) (sc : Scenario) (limit : Int) (s : Genome × Int) (cand : Genome) :
    (accepts p sc limit s cand = true
        ∧ step p sc limit s cand = (cand, s.2 - 1)
        ∧ inBounds p.lo p.hi cand = true
        ∧ (∀ x ∈ margins p sc cand, x ≤ limit)
        ∧ 1 ≤ s.2
        ∧ objective p sc s.1 ≤ objective p sc cand)
      ∨ (accepts p sc limit s cand = false ∧ step p sc limit s cand = s) := by
  by_cases h : accepts p sc limit s cand = true
  · left
    have h' := h
    simp only [accepts, Bool.and_eq_true, decide_eq_true_eq] at h'
    have j := judge_ok p sc limit s cand h'.1.2
    refine ⟨h, ?_, h'.1.1, j.1, j.2.2, h'.2⟩
    simp [step, h, j.2.1]
  · right
    have h2 : accepts p sc limit s cand = false := by simpa using h
    exact ⟨h2, by simp [step, h2]⟩

end PlantGate.Proofs

theorem PlantGate.Spec.step_complete (p : Plant) (sc : Scenario) (limit : Int)
    (s : Genome × Int) (cand : Genome)
    (hb : 0 < s.2) (hin : inBounds p.lo p.hi cand = true)
    (hw : ∀ x ∈ margins p sc s.1, x ≤ limit)
    (hd : distSq (margins p sc s.1) (margins p sc cand)
      ≤ headroom limit (margins p sc s.1) * headroom limit (margins p sc s.1))
    (ho : objective p sc s.1 ≤ objective p sc cand) :
    step p sc limit s cand = (cand, s.2 - 1) := by
  have hv : (judge p sc limit s cand).verdict = Verdict.ok := by
    unfold judge
    exact PlantGate.Spec.gate_complete _ _ _ _ _ (by omega) (by omega) (margins_ne_nil p sc s.1)
      (margins_length p sc s.1 cand) (headroom_nonneg limit _ hw) hd
  have ha : accepts p sc limit s cand = true := by
    simp [accepts, hin, hv, ho]
  rcases step_cases p sc limit s cand with ⟨_, e, _⟩ | ⟨hf, _⟩
  · exact e
  · rw [ha] at hf
    exact absurd hf (by simp)

theorem PlantGate.Spec.step_refusal_changes_nothing (p : Plant) (sc : Scenario) (limit : Int)
    (s : Genome × Int) (cand : Genome)
    (h : accepts p sc limit s cand = false) :
    step p sc limit s cand = s := by
  simp [step, h]

theorem PlantGate.Proofs.loop_margins (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int)
    (hw : ∀ x ∈ margins p sc s.1, x ≤ limit) :
    ∀ x ∈ margins p sc (loop p sc limit s cands).1, x ≤ limit := by
  induction cands generalizing s with
  | nil => exact hw
  | cons cand rest ih =>
    simp only [loop]
    apply ih
    rcases step_cases p sc limit s cand with ⟨_, e, _, hm, _⟩ | ⟨_, e⟩
    · rw [e]
      exact hm
    · rw [e]
      exact hw

theorem PlantGate.Spec.loop_safe (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int)
    (hw : ∀ x ∈ margins p sc s.1, x ≤ limit) (hb : 0 ≤ s.2) :
    (∀ x ∈ margins p sc (loop p sc limit s cands).1, x ≤ limit)
      ∧ 0 ≤ (loop p sc limit s cands).2 ∧ (loop p sc limit s cands).2 ≤ s.2 := by
  refine ⟨PlantGate.Proofs.loop_margins p sc limit cands s hw, ?_⟩
  induction cands generalizing s with
  | nil => exact ⟨hb, by simp [loop]⟩
  | cons cand rest ih =>
    simp only [loop]
    rcases step_cases p sc limit s cand with ⟨_, e, _, hm, h1, _⟩ | ⟨_, e⟩
    · have r := ih (step p sc limit s cand) (by rw [e]; exact hm) (by rw [e]; show 0 ≤ s.2 - 1; omega)
      rw [e] at r ⊢
      have r2 : (loop p sc limit (cand, s.2 - 1) rest).2 ≤ s.2 - 1 := r.2
      exact ⟨r.1, by omega⟩
    · rw [e]
      exact ih s hw hb

theorem PlantGate.Spec.loop_in_bounds (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int)
    (h : inBounds p.lo p.hi s.1 = true) :
    inBounds p.lo p.hi (loop p sc limit s cands).1 = true := by
  induction cands generalizing s with
  | nil => exact h
  | cons cand rest ih =>
    simp only [loop]
    apply ih
    rcases step_cases p sc limit s cand with ⟨_, e, hin, _⟩ | ⟨_, e⟩
    · rw [e]
      exact hin
    · rw [e]
      exact h

theorem PlantGate.Spec.loop_never_worse (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int) :
    objective p sc s.1 ≤ objective p sc (loop p sc limit s cands).1 := by
  induction cands generalizing s with
  | nil => exact Int.le_refl _
  | cons cand rest ih =>
    simp only [loop]
    have r := ih (step p sc limit s cand)
    rcases step_cases p sc limit s cand with ⟨_, e, _, _, _, ho⟩ | ⟨_, e⟩
    · rw [e] at r ⊢
      exact Int.le_trans ho r
    · rw [e] at r ⊢
      exact r

theorem PlantGate.Spec.loop_bounded (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int) :
    (changes p sc limit s cands : Int) + (loop p sc limit s cands).2 ≤ s.2 := by
  induction cands generalizing s with
  | nil => simp [changes, loop]
  | cons cand rest ih =>
    have r := ih (step p sc limit s cand)
    simp only [changes, loop]
    rcases step_cases p sc limit s cand with ⟨ha, e, _⟩ | ⟨hf, e⟩
    · simp only [ha, ↓reduceIte]
      rw [e] at r ⊢
      have r2 : (changes p sc limit (cand, s.2 - 1) rest : Int)
          + (loop p sc limit (cand, s.2 - 1) rest).2 ≤ s.2 - 1 := r
      omega
    · simp only [hf, Bool.false_eq_true, ↓reduceIte]
      rw [e] at r ⊢
      omega

theorem PlantGate.Spec.loop_keeps_physics (p : Plant) (sc : Scenario)
    (cands : List Genome) (s : Genome × Int)
    (hw : ∀ x ∈ margins p sc s.1, x ≤ 1000000) :
    DriveHeatSuffices p (loop p sc 1000000 s cands).1
      ∧ SelfCoolsAtFloor p (loop p sc 1000000 s cands).1
      ∧ RidesThrough p sc (loop p sc 1000000 s cands).1 :=
  physics_of p sc _ (PlantGate.Proofs.loop_margins p sc 1000000 cands s hw)
