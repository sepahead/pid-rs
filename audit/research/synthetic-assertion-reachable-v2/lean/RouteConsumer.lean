import RouteResult

open SmtW02 ArchivedProjection RouteSpec
namespace RouteConsumer

theorem formation : wellFormed primary = true ∧ wellFormed readingTag = true ∧ wellFormed malformed = false := RouteHelpers.wellFormedInputs

theorem ordered : ∀ v : Valuation primary, evaluate primary v = observed (bit v) := RouteResult.ordered

theorem invariance : ∀ v w : Valuation primary, bit v = bit w → evaluate primary v = evaluate primary w := RouteResult.sameOutput

theorem difference : state sample0 ≠ state sample1 := RouteResult.environmentsDiffer

theorem counterexample : bit sample0 = bit sample1 ∧ state sample0 ≠ state sample1 ∧ evaluate primary sample0 = evaluate primary sample1 := RouteResult.counterexample

theorem successful : ∀ v : Valuation primary, RefutesTwo (evaluate primary v) := RouteResult.allRefute

theorem reachableTag : evaluate readingTag (tagSample true 0) = some [true, false] ∧ evaluate readingTag (tagSample true 1) = some [false, true] := RouteHelpers.changedUse

theorem typedFailure : evaluate malformed (zeroValuation malformed) = none := RouteHelpers.failedSource

end RouteConsumer
