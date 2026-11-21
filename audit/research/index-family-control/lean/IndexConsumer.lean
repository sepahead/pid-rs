import IndexProofs
import IndexInline

set_option maxRecDepth 65536
set_option maxHeartbeats 20000000

namespace IndexExample

theorem namedResult : ∀ (i : Fin 83) (ready : Bool) (x : Nat),
    ready = true → 0 < i.val → calcLeft i x = lookupRight ready i x :=
  cover00

theorem singleSlotResult : ∀ (i : Fin 83) (ready : Bool) (x : Nat),
    ready = true → 0 < i.val → calcLeft i x = lookupRight ready i x :=
  inlineComplete

end IndexExample
