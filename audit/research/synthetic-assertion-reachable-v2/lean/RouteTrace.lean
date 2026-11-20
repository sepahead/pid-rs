import RouteConsumer
open SmtW02 RouteSpec

private def code : Option (List Bool) → Nat
  | some [false, true] => 1
  | some [true, false] => 2
  | none => 0
  | _ => 9

#eval [evaluate primary (sample false 0), evaluate primary (sample true 1),
       evaluate readingTag (tagSample true 0), evaluate readingTag (tagSample true 1),
       evaluate malformed (zeroValuation malformed)].map code
