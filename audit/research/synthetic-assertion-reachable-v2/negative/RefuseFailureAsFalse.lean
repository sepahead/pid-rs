import RouteConsumer
open SmtW02 RouteSpec
set_option maxRecDepth 8192
example : evaluate malformed (zeroValuation malformed) = some [false, true] := by rfl
