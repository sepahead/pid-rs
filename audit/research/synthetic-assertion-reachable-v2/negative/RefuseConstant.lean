import RouteConsumer
open SmtW02 RouteSpec
set_option maxRecDepth 8192
example : evaluate primary (sample false 0) = observed true := by rfl
