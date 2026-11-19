import W02Candidate
set_option maxRecDepth 65536
set_option maxHeartbeats 20000000
open SmtW02
namespace W02Readback
theorem valid : SmtW02.wellFormed SmtW02.originalScript = Bool.true := W02.sourceWellFormed
theorem evaluated (v : SmtW02.Valuation SmtW02.originalScript) :
  SmtW02.evaluate SmtW02.originalScript v = Option.some (true :: false :: []) := W02.assertionsAtAllValuations v
theorem hasNoModel : ¬ (∃ v : SmtW02.Valuation SmtW02.originalScript, SmtW02.Satisfies SmtW02.originalScript v) := W02.noSatisfyingValuation
theorem hasAssignments : Nonempty (SmtW02.Valuation SmtW02.originalScript) := W02.sourceRanksHaveValuation
end W02Readback
