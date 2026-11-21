import IndexSpec
import Init.Data.List.FinRange

open IndexExample

#eval do
  for i in List.finRange 83 do
    for ready in [false, true] do
      for x in [0, 7] do
        IO.println s!"INDEX_ROW {i.val},{ready},{x},{calcLeft i x},{lookupRight ready i x}"
