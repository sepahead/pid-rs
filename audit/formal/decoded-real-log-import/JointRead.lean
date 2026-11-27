prelude
import JoinProof
import Mathlib.Analysis.SpecialFunctions.Log.Basic

#check (fun (rs : D1Whole.Table) (l : A2.Layer) (c : A1.Part) (i : A2.Node) =>
  Real.log (((A2.make rs l c i).2.2.2 : Rat) : ℝ))
#check @A2.Decoded.positive_value
#check @A2.Decoded.true_lower_interval
#check @A2.Decoded.signed_from_counts
#check @Real.log_mul
#check @Real.log_div
#print axioms A2.Decoded.positive_value
#print axioms A2.Decoded.true_lower_interval
#print axioms A2.Decoded.signed_from_counts
#print axioms Real.log_mul
#print axioms Real.log_div
