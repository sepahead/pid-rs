import RouteTransport
open SmtW02 RouteSpec
set_option maxRecDepth 8192
example : evaluate readingTag (tagSample true 1) = evaluate readingTag (tagSample true 0) := by
  refine RouteTransport.reached.mpr ?_
  rfl
