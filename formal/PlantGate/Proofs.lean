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
        ∧ (objective p sc s.1 < objective p sc cand
            ∨ (objective p sc s.1 = objective p sc cand
                ∧ headroom limit (margins p sc s.1) < headroom limit (margins p sc cand))))
      ∨ (accepts p sc limit s cand = false ∧ step p sc limit s cand = s) := by
  by_cases h : accepts p sc limit s cand = true
  · left
    have h' := h
    simp only [accepts, lexImproves, Bool.and_eq_true, Bool.or_eq_true, decide_eq_true_eq] at h'
    have j := judge_ok p sc limit s cand h'.1.2
    refine ⟨h, ?_, h'.1.1.2, j.1, j.2.2, h'.2⟩
    simp [step, h, j.2.1]
  · right
    have h2 : accepts p sc limit s cand = false := by simpa using h
    exact ⟨h2, by simp [step, h2]⟩

theorem posDiff_nonneg (b c : Int) : 0 ≤ posDiff b c := by
  unfold posDiff
  split <;> omega

theorem posDistSq_nonneg : ∀ (base cand : List Int), 0 ≤ posDistSq base cand
  | [], _ => by simp [posDistSq]
  | _ :: _, [] => by simp [posDistSq]
  | b :: bs, c :: cs => by
    have h1 : 0 ≤ posDiff b c * posDiff b c := sq_nonneg (posDiff b c)
    have h2 := posDistSq_nonneg bs cs
    simp only [posDistSq]
    omega

theorem posDistSq_zero_of_le :
    ∀ (base cand : List Int), (∀ p ∈ List.zip base cand, p.2 ≤ p.1) → posDistSq base cand = 0
  | [], _, _ => by simp [posDistSq]
  | _ :: _, [], _ => by simp [posDistSq]
  | b :: bs, c :: cs, h => by
    have h0 : c ≤ b := h (b, c) (by simp)
    have hp : posDiff b c = 0 := by
      unfold posDiff
      split <;> omega
    have ih := posDistSq_zero_of_le bs cs (fun p hp' => h p (by simp [hp']))
    simp [posDistSq, hp, ih]

theorem within_of_pos (limit r : Int) (hr : 0 ≤ r) :
    ∀ (base cand : List Int), base.length = cand.length → posDistSq base cand ≤ r * r →
      (∀ b ∈ base, r ≤ limit - b) → ∀ x ∈ cand, x ≤ limit
  | [], [], _, _, _ => by simp
  | [], _ :: _, hl, _, _ => by simp at hl
  | _ :: _, [], hl, _, _ => by simp at hl
  | b :: bs, c :: cs, hl, hd, hh => by
    intro x hx
    simp only [posDistSq] at hd
    have h1 : 0 ≤ posDiff b c * posDiff b c := sq_nonneg (posDiff b c)
    have h2 := posDistSq_nonneg bs cs
    rcases List.mem_cons.mp hx with rfl | hx'
    · have h3 := le_of_sq_le (posDiff b x) r hr (by omega)
      have h4 := hh b (by simp)
      unfold posDiff at h3
      split at h3 <;> omega
    · exact within_of_pos limit r hr bs cs (by simpa using hl) (by omega)
        (fun b' hb' => hh b' (by simp [hb'])) x hx'

theorem noNewExcess_sound (limit : Int) :
    ∀ (base cand : List Int), noNewExcess limit base cand = true →
      ∀ p ∈ List.zip base cand, p.2 ≤ max p.1 limit
  | [], _, _ => by simp
  | _ :: _, [], _ => by simp
  | b :: bs, c :: cs, h => by
    intro p hp
    simp only [noNewExcess, Bool.and_eq_true, decide_eq_true_eq] at h
    rw [List.zip_cons_cons] at hp
    rcases List.mem_cons.mp hp with rfl | hp'
    · exact h.1
    · exact noNewExcess_sound limit bs cs h.2 p hp'

theorem asym_evolve_safe_step (limit : Int) (s : List Int × Int) (cand : List Int) (cost : Int)
    (hw : ∀ x ∈ s.1, x ≤ limit) (hb : 0 ≤ s.2) :
    (∀ x ∈ (evolveAsymmetric limit s cand cost).1, x ≤ limit)
      ∧ 0 ≤ (evolveAsymmetric limit s cand cost).2
      ∧ (evolveAsymmetric limit s cand cost).2 ≤ s.2
      ∧ ((if (gateAsymmetric limit s.1 cand s.2 cost).verdict.admitted = true then 1 else 0) : Int)
          + (evolveAsymmetric limit s cand cost).2 ≤ s.2 := by
  have hr : 0 ≤ headroom limit s.1 := headroom_nonneg limit s.1 hw
  by_cases h1 : cost ≤ 0
  · simp [evolveAsymmetric, gateAsymmetric, AsymVerdict.admitted, h1, hb]; exact hw
  by_cases h2 : s.2 < cost
  · simp [evolveAsymmetric, gateAsymmetric, AsymVerdict.admitted, h1, h2, hb]; exact hw
  by_cases h3 : s.1.length ≠ cand.length ∨ s.1 = []
  · simp [evolveAsymmetric, gateAsymmetric, AsymVerdict.admitted, h1, h2, h3, hb]; exact hw
  have h4 : ¬ headroom limit s.1 < 0 := by omega
  by_cases h5 : headroom limit s.1 * headroom limit s.1 < posDistSq s.1 cand
  · simp [evolveAsymmetric, gateAsymmetric, AsymVerdict.admitted, h1, h2, h3, h4, h5, hb]; exact hw
  · have hl : s.1.length = cand.length := by
      by_cases e : s.1.length = cand.length
      · exact e
      · exact absurd (Or.inl e) h3
    have hc : ∀ x ∈ cand, x ≤ limit :=
      within_of_pos limit (headroom limit s.1) hr s.1 cand hl (by omega)
        (fun b hb' => headroom_le limit s.1 b hb')
    simp only [evolveAsymmetric, gateAsymmetric, AsymVerdict.admitted, h1, h2, h3, h4, h5, ↓reduceIte]
    exact ⟨hc, by omega, by omega, by omega⟩

end PlantGate.Proofs

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
    step p sc limit s cand = (cand, s.2 - 1) := by
  have hv : (judge p sc limit s cand).verdict = Verdict.ok := by
    unfold judge
    exact PlantGate.Spec.gate_complete _ _ _ _ _ (by omega) (by omega) (margins_ne_nil p sc s.1)
      (margins_length p sc s.1 cand) (headroom_nonneg limit _ hw) hd
  have hlex : lexImproves p sc limit s.1 cand = true := by
    simp only [lexImproves, Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq]
    exact ho
  have ha : accepts p sc limit s cand = true := by
    simp [accepts, hin, hv, hlex, hne]
  rcases step_cases p sc limit s cand with ⟨_, e, _⟩ | ⟨hf, _⟩
  · exact e
  · rw [ha] at hf
    exact absurd hf (by simp)

theorem PlantGate.Spec.same_design_not_taken_up (p : Plant) (sc : Scenario) (limit : Int)
    (s : Genome × Int) :
    accepts p sc limit s s.1 = false := by
  simp [accepts]

theorem PlantGate.Spec.tie_headroom_decay_refused (p : Plant) (sc : Scenario) (limit : Int)
    (s : Genome × Int) (cand : Genome)
    (heq : objective p sc cand = objective p sc s.1)
    (hdec : headroom limit (margins p sc cand) ≤ headroom limit (margins p sc s.1)) :
    accepts p sc limit s cand = false := by
  have h1 : ¬ objective p sc s.1 < objective p sc cand := by omega
  have h2 : ¬ headroom limit (margins p sc s.1) < headroom limit (margins p sc cand) := by omega
  simp [accepts, lexImproves, h1, h2]

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
    rcases step_cases p sc limit s cand with ⟨_, e, _, _, _, hlex⟩ | ⟨_, e⟩
    · rw [e] at r ⊢
      have ho : objective p sc s.1 ≤ objective p sc cand := by
        rcases hlex with hlt | ⟨heq, _⟩ <;> omega
      exact Int.le_trans ho r
    · rw [e] at r ⊢
      exact r

theorem PlantGate.Spec.loop_lex_monotone (p : Plant) (sc : Scenario) (limit : Int)
    (cands : List Genome) (s : Genome × Int) :
    objective p sc s.1 < objective p sc (loop p sc limit s cands).1
      ∨ (objective p sc s.1 = objective p sc (loop p sc limit s cands).1
          ∧ headroom limit (margins p sc s.1)
              ≤ headroom limit (margins p sc (loop p sc limit s cands).1)) := by
  induction cands generalizing s with
  | nil => exact Or.inr ⟨rfl, Int.le_refl _⟩
  | cons cand rest ih =>
    simp only [loop]
    rcases step_cases p sc limit s cand with ⟨_, e, _, _, _, hlex⟩ | ⟨_, e⟩
    · have r := ih (cand, s.2 - 1)
      dsimp only at r
      rw [e]
      rcases hlex with hlt | ⟨heq, hht⟩
      · rcases r with rlt | ⟨req, _⟩
        · exact Or.inl (by omega)
        · exact Or.inl (by omega)
      · rcases r with rlt | ⟨req, rh⟩
        · exact Or.inl (by omega)
        · exact Or.inr ⟨by omega, by omega⟩
    · rw [e]
      exact ih s

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

theorem PlantGate.Spec.wellformed_nonneg_demands (p : Plant) (sc : Scenario) (g : Genome)
    (hwf : WellFormed p sc g) :
    0 ≤ qFix p g ∧ 0 ≤ driveNum p g ∧ 0 ≤ outageNum p sc g
      ∧ 0 < outageDen g ∧ 0 < g.floor := by
  rcases hwf with ⟨hp, hg⟩
  rcases hp with ⟨hpIt, hcop, hua, hwa, hdT, hother, hpas, haux, hlcop,
    hlopcm, hhipcm, hlocap, hhicap, hcapmax, hlowall, hhiwall, hlofl, hhifl,
    hloshed, hhished, hshedmax, houtMin, _⟩
  rcases hg with ⟨gpcm, gcap0, gcap1, gwall, gfloor, gshed0, gshed1⟩
  have hwa_nonneg : 0 ≤ g.wallU * p.wallArea := Int.mul_nonneg gwall hwa
  have hqf : 0 ≤ qFix p g := by
    unfold qFix
    have hmul : 0 ≤ (p.uaRoof + g.wallU * p.wallArea) * p.dT := Int.mul_nonneg (by omega) hdT
    omega
  have hdn : 0 ≤ driveNum p g := by
    unfold driveNum
    have hmul : 0 ≤ (1000000 - g.capture) * (p.pIt * 1000000) := Int.mul_nonneg (by omega) (by omega)
    omega
  have hon : 0 ≤ outageNum p sc g := by
    unfold outageNum
    have hmul : 0 ≤ p.pIt * (1000000 - g.shed) := Int.mul_nonneg (by omega) (by omega)
    exact Int.mul_nonneg (by omega) (by omega)
  have hod : 0 < outageDen g := by
    unfold outageDen
    omega
  exact ⟨hqf, hdn, hon, hod, gfloor⟩

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
      ∧ 0 ≤ outageNum p sc (loop p sc 1000000 s cands).1 := by
  have hphys := PlantGate.Spec.loop_keeps_physics p sc cands s hw
  have hbnd := PlantGate.Spec.loop_in_bounds p sc 1000000 cands s hin
  simp only [inBounds, between, Bool.and_eq_true, decide_eq_true_eq] at hbnd
  rcases hwp with ⟨hpIt, hcop, hua, hwa, hdT, hother, hpas, haux, hlcop,
    hlopcm, hhipcm, hlocap, hhicap, hcapmax, hlowall, hhiwall, hlofl, hhifl,
    hloshed, hhished, hshedmax, houtMin, hrest⟩
  have hwp' : WellFormedPlant p sc :=
    ⟨hpIt, hcop, hua, hwa, hdT, hother, hpas, haux, hlcop,
      hlopcm, hhipcm, hlocap, hhicap, hcapmax, hlowall, hhiwall, hlofl, hhifl,
      hloshed, hhished, hshedmax, houtMin, hrest⟩
  have hwg : WellFormedGenome (loop p sc 1000000 s cands).1 :=
    ⟨by omega, by omega, by omega, by omega, hphys.2.1.2.1, by omega, by omega⟩
  have hwf : WellFormed p sc (loop p sc 1000000 s cands).1 := ⟨hwp', hwg⟩
  have hdem := PlantGate.Spec.wellformed_nonneg_demands p sc _ hwf
  exact ⟨hwf, hphys.1, hphys.2.1, hphys.2.2, hdem.2.1, hdem.2.2.1⟩

theorem PlantGate.Spec.asym_gate_ok_stays_within (limit : Int) (base cand : List Int)
    (budget cost : Int)
    (h : (gateAsymmetric limit base cand budget cost).verdict = AsymVerdict.ok) :
    (∀ x ∈ cand, x ≤ limit) ∧ 0 < cost ∧ cost ≤ budget
      ∧ (gateAsymmetric limit base cand budget cost).remaining = budget - cost := by
  by_cases h1 : cost ≤ 0
  · simp [gateAsymmetric, h1] at h
  by_cases h2 : budget < cost
  · simp [gateAsymmetric, h1, h2] at h
  by_cases h3 : base.length ≠ cand.length ∨ base = []
  · simp [gateAsymmetric, h1, h2, h3] at h
  by_cases h4 : headroom limit base < 0
  · by_cases hr : headroom limit base < headroom limit cand ∧ noNewExcess limit base cand = true
    · simp [gateAsymmetric, h1, h2, h3, h4, hr] at h
    · simp [gateAsymmetric, h1, h2, h3, h4, hr] at h
  by_cases h5 : headroom limit base * headroom limit base < posDistSq base cand
  · simp [gateAsymmetric, h1, h2, h3, h4, h5] at h
  · have hl : base.length = cand.length := by
      by_cases e : base.length = cand.length
      · exact e
      · exact absurd (Or.inl e) h3
    have hc : ∀ x ∈ cand, x ≤ limit :=
      within_of_pos limit (headroom limit base) (by omega) base cand hl (by omega)
        (fun b hb => headroom_le limit base b hb)
    refine ⟨hc, by omega, by omega, ?_⟩
    simp [gateAsymmetric, h1, h2, h3, h4, h5]

theorem PlantGate.Spec.asym_gate_pure_safety_admitted (limit : Int) (base cand : List Int)
    (budget cost : Int)
    (hc : 0 < cost) (hb : cost ≤ budget) (hn : base ≠ []) (hl : base.length = cand.length)
    (hw : ∀ x ∈ base, x ≤ limit)
    (hdown : ∀ p ∈ List.zip base cand, p.2 ≤ p.1) :
    (gateAsymmetric limit base cand budget cost).verdict = AsymVerdict.ok := by
  have h1 : ¬ cost ≤ 0 := by omega
  have h2 : ¬ budget < cost := by omega
  have h3 : ¬ (base.length ≠ cand.length ∨ base = []) := by
    intro h
    rcases h with h | h
    · exact h hl
    · exact hn h
  have hr : 0 ≤ headroom limit base := headroom_nonneg limit base hw
  have h4 : ¬ headroom limit base < 0 := by omega
  have hz : posDistSq base cand = 0 := posDistSq_zero_of_le base cand hdown
  have hsq : 0 ≤ headroom limit base * headroom limit base := sq_nonneg (headroom limit base)
  have h5 : ¬ headroom limit base * headroom limit base < posDistSq base cand := by omega
  simp [gateAsymmetric, h1, h2, h3, h4, h5]

theorem PlantGate.Spec.asym_gate_recovery_lyapunov_descent (limit : Int) (base cand : List Int)
    (budget cost : Int)
    (h : (gateAsymmetric limit base cand budget cost).verdict = AsymVerdict.okRecovery) :
    headroom limit base < 0
      ∧ headroom limit base < headroom limit cand
      ∧ max 0 (-headroom limit cand) < max 0 (-headroom limit base)
      ∧ (∀ p ∈ List.zip base cand, p.2 ≤ max p.1 limit)
      ∧ 0 < cost ∧ cost ≤ budget
      ∧ (gateAsymmetric limit base cand budget cost).remaining = budget - cost := by
  by_cases h1 : cost ≤ 0
  · simp [gateAsymmetric, h1] at h
  by_cases h2 : budget < cost
  · simp [gateAsymmetric, h1, h2] at h
  by_cases h3 : base.length ≠ cand.length ∨ base = []
  · simp [gateAsymmetric, h1, h2, h3] at h
  by_cases h4 : headroom limit base < 0
  · by_cases hr : headroom limit base < headroom limit cand ∧ noNewExcess limit base cand = true
    · have hlyap : max 0 (-headroom limit cand) < max 0 (-headroom limit base) := by
        simp only [Int.max_def]
        split <;> split <;> omega
      refine ⟨h4, hr.1, hlyap, noNewExcess_sound limit base cand hr.2, by omega, by omega, ?_⟩
      simp [gateAsymmetric, h1, h2, h3, h4, hr]
    · simp [gateAsymmetric, h1, h2, h3, h4, hr] at h
  · by_cases h5 : headroom limit base * headroom limit base < posDistSq base cand
    · simp [gateAsymmetric, h1, h2, h3, h4, h5] at h
    · simp [gateAsymmetric, h1, h2, h3, h4, h5] at h

theorem PlantGate.Spec.asym_run_safe_and_bounded (limit : Int) (steps : List (List Int × Int))
    (s : List Int × Int)
    (hw : ∀ x ∈ s.1, x ≤ limit) (hb : 0 ≤ s.2) :
    (∀ x ∈ (runAsymmetric limit s steps).1, x ≤ limit)
      ∧ 0 ≤ (runAsymmetric limit s steps).2
      ∧ (runAsymmetric limit s steps).2 ≤ s.2
      ∧ (asymAcceptedCount limit s steps : Int) + (runAsymmetric limit s steps).2 ≤ s.2 := by
  induction steps generalizing s with
  | nil => exact ⟨hw, hb, by simp [runAsymmetric], by simp [asymAcceptedCount, runAsymmetric]⟩
  | cons st rest ih =>
    obtain ⟨cand, cost⟩ := st
    have e := asym_evolve_safe_step limit s cand cost hw hb
    have r := ih (evolveAsymmetric limit s cand cost) e.1 e.2.1
    simp only [runAsymmetric, asymAcceptedCount]
    have h4 : ((if (gateAsymmetric limit s.1 cand s.2 cost).verdict.admitted = true then 1 else 0) : Int)
        + (evolveAsymmetric limit s cand cost).2 ≤ s.2 := e.2.2.2
    have r4 : (asymAcceptedCount limit (evolveAsymmetric limit s cand cost) rest : Int)
        + (runAsymmetric limit (evolveAsymmetric limit s cand cost) rest).2
        ≤ (evolveAsymmetric limit s cand cost).2 := r.2.2.2
    refine ⟨r.1, r.2.1, by omega, ?_⟩
    by_cases hadm : (gateAsymmetric limit s.1 cand s.2 cost).verdict.admitted = true
    · simp only [hadm, ↓reduceIte] at h4 ⊢
      omega
    · simp only [hadm, Bool.false_eq_true, ↓reduceIte] at h4 ⊢
      omega
