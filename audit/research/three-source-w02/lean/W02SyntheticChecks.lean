import W02SyntheticData

set_option maxRecDepth 8192
set_option maxHeartbeats 1500000
namespace SmtW02

theorem syntheticAllWellFormed : [t01, t02, t03, t04, t05, t06, t07, t08, t09, t10, t11, t12, t13].all wellFormed = true := by decide

theorem t01Result (ρ : Valuation t01) : evaluate t01 ρ = some [true,false] := by
  let x := Value.integer (ρ ⟨0, by decide⟩)
  change some [(x == x) && true, !((x == x) && true)] = _
  simp

theorem t02Result (ρ : Valuation t02) : evaluate t02 ρ = some [false,true] := by
  let x := Value.integer (ρ ⟨0, by decide⟩)
  change some [!((x == x) && true), (x == x) && true] = _
  simp

def t03witness : Valuation t03 :=
  fun i => match i with
    | ⟨0, _⟩ => (-10000000000000000000001 : Int)
    | ⟨n+1, h⟩ => False.elim (by have : n+1 < 1 := h; omega)

theorem t03Model : evaluate t03 t03witness = some [true,true] := by decide

theorem t04Result (ρ : Valuation t04) : evaluate t04 ρ = some [true,false] := by rfl
theorem t05Result (ρ : Valuation t05) : evaluate t05 ρ = some [true,true] := by rfl
theorem t06Result (ρ : Valuation t06) : evaluate t06 ρ = some [true,false] := by rfl
theorem t07Result (ρ : Valuation t07) : evaluate t07 ρ = some [true,true] := by rfl
theorem t08Result (ρ : Valuation t08) : evaluate t08 ρ = some [true,true] := by
  let xi : Int := ρ ⟨0, by decide⟩
  let x := Value.integer ((0 + xi) + 1)
  change some [true, (x == x) && true] = _
  simp
theorem t09Result (ρ : Valuation t09) : evaluate t09 ρ = some [true,false] := by rfl
theorem t10Result (ρ : Valuation t10) : evaluate t10 ρ = some [true,true] := by rfl
theorem t11Result (ρ : Valuation t11) : evaluate t11 ρ = some [true,true] := by rfl
theorem t12Result (ρ : Valuation t12) : evaluate t12 ρ = some [true,true] := by rfl
theorem t13Result (ρ : Valuation t13) : evaluate t13 ρ = some [true,true] := by rfl

end SmtW02

