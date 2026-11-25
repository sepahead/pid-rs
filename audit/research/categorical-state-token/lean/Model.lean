prelude
import Init.Tactics
import Init.ByCases
import Init.Data.List.Lemmas
import Init.Data.List.TakeDrop
import Init.Data.UInt.Basic

namespace D1Token

def tokenByte (b : UInt8) : Bool :=
  let n := b.toNat
  decide ((65 ≤ n ∧ n ≤ 90) ∨ (97 ≤ n ∧ n ≤ 122) ∨
    (48 ≤ n ∧ n ≤ 57) ∨ n = 46 ∨ n = 95 ∨ n = 58 ∨ n = 45)

def Admissible (t : List UInt8) : Prop :=
  0 < t.length ∧ t.length ≤ 128 ∧ t.all tokenByte = true

instance (t : List UInt8) : Decidable (Admissible t) :=
  inferInstanceAs (Decidable (0 < t.length ∧ t.length ≤ 128 ∧ t.all tokenByte = true))

def emit (t : List UInt8) : List UInt8 := 34 :: (t ++ [34])

def scan (body : List UInt8) : Option (List UInt8 × List UInt8) :=
  match body.dropWhile tokenByte with
  | [] => none
  | close :: suffix =>
    let t := body.takeWhile tokenByte
    if close = 34 ∧ Admissible t then some (t, suffix) else none

def read : List UInt8 → Option (List UInt8 × List UInt8)
  | [] => none
  | opener :: body => if opener = 34 then scan body else none

end D1Token
