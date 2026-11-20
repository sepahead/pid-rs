import RouteConsumer

open SmtW02 RouteSpec
namespace RouteTransport

theorem equalResults {α : Type} {x y left right : α}
    (hx : x = left) (hy : y = right) : (x = y) ↔ (left = right) :=
  ⟨fun h => hx.symm.trans (h.trans hy), fun h => hx.trans (h.trans hy.symm)⟩

theorem reached :
    (evaluate readingTag (tagSample true 1) = evaluate readingTag (tagSample true 0)) ↔
    (some [false, true] : Option (List Bool)) = some [true, false] :=
  equalResults RouteConsumer.reachableTag.2 RouteConsumer.reachableTag.1

theorem equalControl : evaluate readingTag (tagSample true 0) = evaluate readingTag (tagSample true 0) :=
  (equalResults RouteConsumer.reachableTag.1 RouteConsumer.reachableTag.1).mpr rfl

theorem unequalControl : evaluate readingTag (tagSample true 1) ≠ evaluate readingTag (tagSample true 0) := by
  intro same
  have distinct : (some [false, true] : Option (List Bool)) ≠ some [true, false] := by decide
  exact distinct (reached.mp same)

end RouteTransport
