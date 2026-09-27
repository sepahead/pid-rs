import PidStoppedPrefixStageA.Contract

/- Source-only F4 candidate. No native elaboration or kernel check has occurred. -/
set_option autoImplicit false
set_option warningAsError true
open PidMgwBridgeContract (Key Node mismatches)
open PidPrefixProbabilityContract
universe u v w
namespace PidStoppedPrefixF4Candidate

theorem native_return_kills
    (I : Type u) (X : I → Type v) (T : Type w)
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z : Key I X T) (alpha : Node I) (rows : List (Key I X T))
    (hz : z ∈ rows) :
    positiveOnPrefix z alpha rows = 0 ∧ negativeOnPrefix z alpha rows = 0 := by
  classical
  have self_mismatches : mismatches z z = (∅ : Finset I) := by
    simp [mismatches]
  have excludes : ∀ xs : List (Key I X T),
      z ∈ xs → ¬ prefixEvent z alpha xs := by
    intro xs hmem hevent
    have impossible : (mismatches z z).Nonempty := hevent.2.1 z hmem
    simp [self_mismatches] at impossible
  have retained_mem : z ∈ rows.filter (fun x => decide (x.2 = z.2)) := by
    exact List.mem_filter.mpr ⟨hz, by simp⟩
  have retained_excludes :
      ¬ prefixEvent z alpha (rows.filter (fun x => decide (x.2 = z.2))) :=
    excludes _ retained_mem
  constructor
  · simp [positiveOnPrefix, excludes rows hz]
  · cases hlast : rows.getLast? with
    | none => simp [negativeOnPrefix, hlast]
    | some current => simp [negativeOnPrefix, hlast, retained_excludes]

end PidStoppedPrefixF4Candidate
