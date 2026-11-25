namespace SmtW02

inductive Ty where
  | bool | int | bv (width : Nat)
deriving DecidableEq, Repr

inductive Term where
  | boolean (value : Bool)
  | numeral (value : Nat)
  | bits (width value : Nat)
  | name (ty : Ty) (identifier : String)
  | app (ty : Ty) (operator : String) (args : List Term)
  | indexed (ty : Ty) (operator : String) (indices : List Nat) (arg : Term)
deriving Repr

inductive Cmd where
  | logic (value : String)
  | option (name value : String)
  | constant (name : String) (ty : Ty)
  | define (name : String) (params : List (String × Ty)) (ret : Ty) (body : Term)
  | echo (token : String)
  | assertion (body : Term)
  | check | exit
deriving Repr

structure TermAlgebra (α : Type) where
  boolean : Bool → α
  numeral : Nat → α
  bits : Nat → Nat → α
  name : Ty → String → α
  app : Ty → String → List α → α
  indexed : Ty → String → List Nat → α → α

mutual
  def Term.fold (a : TermAlgebra α) (term : Term) : α := match term with
    | .boolean v => a.boolean v
    | .numeral n => a.numeral n
    | .bits w n => a.bits w n
    | .name t n => a.name t n
    | .app t op args => a.app t op (Term.foldArgs a args)
    | .indexed t op ix arg => a.indexed t op ix (Term.fold a arg)
  termination_by structural term

  def Term.foldArgs (a : TermAlgebra α) (terms : List Term) : List α := match terms with
    | [] => []
    | x::rest => Term.fold a x :: Term.foldArgs a rest
  termination_by structural terms
end


def Ty.valid : Ty → Bool
  | .bool | .int => true
  | .bv w => 0 < w && w <= 64

abbrev Binding := String × Ty
abbrev Ranks := List (String × (List Ty × Ty))

def allSame [BEq α] (xs : List α) : Bool :=
  match xs with
  | [] => true
  | x::more => more.all (· == x)

def allDistinct [BEq α] : List α → Bool
  | [] => true
  | x::xs => !(xs.contains x) && allDistinct xs

def indexedRank (op : String) (ix : List Nat) (input : Ty) : Option Ty := do
  let .bv w := input | none
  match op, ix with
  | "extract", [high, low] =>
    guard (low <= high && high < w)
    return .bv (high - low + 1)
  | "zero_extend", [amount] =>
    guard (w + amount <= 64)
    return .bv (w + amount)
  | _, _ => none

def builtinRank (op : String) (args : List Ty) : Option Ty := do
  let arity := args.length
  match op with
  | "and" | "or" | "=>" | "not" =>
    guard ((if op == "not" then arity == 1 else 2 <= arity) && args.all (· == .bool))
    return .bool
  | "=" | "distinct" =>
    guard (2 <= arity && allSame args)
    return .bool
  | "ite" =>
    let [.bool, t, u] := args | none
    guard (t == u)
    return t
  | "+" | "-" | "<=" | ">=" | "<" | ">" =>
    guard ((if op == "-" then 1 <= arity else 2 <= arity) && args.all (· == .int))
    return if op == "+" || op == "-" then .int else .bool
  | "bvand" | "bvor" | "bvsub" | "bvshl" =>
    let [.bv x, .bv y] := args | none
    guard (x == y)
    return .bv x
  | _ => none

def sameRank (annotated actual : Ty) : Option Ty :=
  if annotated == actual then some actual else none

def infer (term : Term) (global : Ranks) (localRanks : List Binding := []) : Option Ty :=
  term.fold {
    boolean := fun _ => some .bool
    numeral := fun _ => some .int
    bits := fun w n => do
      guard ((Ty.bv w).valid && n < 2^w)
      return .bv w
    name := fun t n => do
      match localRanks.lookup n with
      | some actual => sameRank t actual
      | none =>
        let (ins, out) ← global.lookup n
        guard ins.isEmpty
        sameRank t out
    app := fun t op nodes => do
      guard ((localRanks.lookup op).isNone)
      let args ← nodes.mapM id
      let actual ← match global.lookup op with
        | some (ins, out) => if args == ins then some out else none
        | none => builtinRank op args
      sameRank t actual
    indexed := fun t op ix node => do
      let child ← node
      let actual ← indexedRank op ix child
      sameRank t actual }

structure StaticState where
  globals : Ranks := []
  echoSeen : Bool := false
  nassert : Nat := 0

def staticStep (s : StaticState) : Cmd → Option StaticState
  | .constant n t => do
    guard (s.nassert == 0 && t.valid && (s.globals.lookup n).isNone)
    return {s with globals := (n, [], t) :: s.globals}
  | .define n args result body => do
    guard (s.nassert == 0 && (s.globals.lookup n).isNone && result.valid &&
           args.all (fun p => p.2.valid) && allDistinct (args.map Prod.fst))
    let bodyTy ← infer body s.globals args
    guard (bodyTy == result)
    return {s with globals := (n, args.map Prod.snd, result) :: s.globals}
  | .echo tok => do
    guard (!s.echoSeen && s.nassert == 0 &&
           tok.toList.head? == some '"' && tok.toList.getLast? == some '"')
    return {s with echoSeen := true}
  | .assertion expr => do
    guard (s.echoSeen && (infer expr s.globals) == some .bool)
    return {s with nassert := s.nassert + 1}
  | _ => none

def currentCommands : List Cmd → Option (List Cmd)
  | .logic "ALL" :: .option ":produce-models" "true" :: rest =>
    match rest.reverse with
    | .exit :: .check :: rev => some rev.reverse
    | _ => none
  | _ => none

def wellFormed (script : List Cmd) : Bool :=
  match (do let cmds ← currentCommands script; cmds.foldlM staticStep {}) with
  | some s => s.echoSeen && s.nassert == 2
  | none => false

inductive Value where
  | boolean (v : Bool)
  | integer (v : Int)
  | bits (width number : Nat)
deriving DecidableEq, Repr

def Value.getBool : Value → Option Bool | .boolean x => some x | _ => none
def Value.getInt : Value → Option Int | .integer x => some x | _ => none

def rightImplies : List Bool → Bool
  | [] => true
  | [x] => x
  | x::xs => !x || rightImplies xs

def intChain (p : Int → Int → Bool) : List Int → Bool
  | a::b::more => p a b && intChain p (b::more)
  | _ => true

def builtinValue (op : String) (vs : List Value) : Option Value := do
  match op with
  | "ite" =>
    let [.boolean k, x, y] := vs | none
    return if k then x else y
  | "=" => return .boolean (allSame vs)
  | "distinct" => return .boolean (allDistinct vs)
  | "and" | "or" | "=>" | "not" =>
    let bs ← vs.mapM Value.getBool
    let b ← match op with
      | "and" => some (bs.all id)
      | "or" => some (bs.any id)
      | "=>" => some (rightImplies bs)
      | _ => match bs with | [x] => some (!x) | _ => none
    return .boolean b
  | "+" | "-" | "<=" | ">=" | "<" | ">" =>
    let ns ← vs.mapM Value.getInt
    match op with
    | "+" => return .integer (ns.foldl (· + ·) 0)
    | "-" =>
      match ns with
      | [] => none
      | [n] => return .integer (-n)
      | n::more => return .integer (more.foldl (· - ·) n)
    | "<=" => return .boolean (intChain (fun x y => decide (x <= y)) ns)
    | ">=" => return .boolean (intChain (fun x y => decide (y <= x)) ns)
    | "<" => return .boolean (intChain (fun x y => decide (x < y)) ns)
    | _ => return .boolean (intChain (fun x y => decide (y < x)) ns)
  | "bvand" | "bvor" | "bvsub" | "bvshl" =>
    let [.bits w x, .bits v y] := vs | none
    guard (w == v)
    let modulus := 2 ^ w
    let z := match op with
      | "bvand" => Nat.land x y
      | "bvor" => Nat.lor x y
      | "bvsub" => (x + modulus - y) % modulus
      | _ => if w <= y then 0 else Nat.shiftLeft x y % modulus
    return .bits w z
  | _ => none

def indexedValue (op : String) (ix : List Nat) (v : Value) : Option Value := do
  let .bits w x := v | none
  let .bv out ← indexedRank op ix (.bv w) | none
  match op, ix with
  | "extract", [_, low] => return .bits out (Nat.shiftRight x low % (2^out))
  | "zero_extend", [_] => return .bits out x
  | _, _ => none

abbrev Functions := List (String × (List Value → Option Value))
abbrev Locals := List (String × Value)

def evaluateTerm (t : Term) (global : Functions) (locals : Locals := []) : Option Value :=
  t.fold {
    boolean := fun v => some (.boolean v)
    numeral := fun n => some (.integer (Int.ofNat n))
    bits := fun w n => some (.bits w n)
    name := fun _ n =>
      match locals.lookup n with
      | some v => some v
      | none => do let g ← global.lookup n; g []
    app := fun _ op children => do
      let args ← children.mapM id
      match global.lookup op with
      | some g => g args
      | none => builtinValue op args
    indexed := fun _ op ix child => do indexedValue op ix (← child) }

def Ty.carrier : Ty → Type
  | .bool => Bool
  | .int => Int
  | .bv w => BitVec w

def Ty.toValue : (s : Ty) → s.carrier → Value
  | .bool, b => .boolean b
  | .int, i => .integer i
  | .bv w, v => .bits w v.toNat

def declarations (script : List Cmd) : List Binding :=
  script.filterMap (fun c => match c with | .constant n t => some (n,t) | _ => none)

abbrev Valuation (script : List Cmd) :=
  (i : Fin (declarations script).length) → ((declarations script).get i).2.carrier

def valuationLookup (d : List Binding) (ρ : (i : Fin d.length) → (d.get i).2.carrier) (n : String) :
    Option Value :=
  let vals := List.ofFn (fun i : Fin d.length => ((d.get i).1, (d.get i).2.toValue (ρ i)))
  vals.lookup n

def Ty.zero : (s : Ty) → s.carrier
  | .bool => false
  | .int => (0 : Int)
  | .bv w => BitVec.zero w

def zeroValuation (script : List Cmd) : Valuation script :=
  fun i => ((declarations script).get i).2.zero

structure DynamicState where
  globals : Functions := []
  assertedRev : List Bool := []

def dynamicStep (value : String → Option Value) (s : DynamicState) : Cmd → Option DynamicState
  | .constant n _ => return {s with globals :=
      (n, fun xs => if xs.isEmpty then value n else none) :: s.globals}
  | .define n params _ body =>
    let g := fun xs => if xs.length == params.length then
                  evaluateTerm body s.globals ((params.map Prod.fst).zip xs)
                else none
    return {s with globals := (n, g) :: s.globals}
  | .assertion e => do
    let v ← evaluateTerm e s.globals
    let b ← v.getBool
    return {s with assertedRev := b :: s.assertedRev}
  | .echo _ => some s
  | _ => none

def evaluate (script : List Cmd) (ρ : Valuation script) : Option (List Bool) := do
  guard (wellFormed script)
  let cmds ← currentCommands script
  let s ← cmds.foldlM (dynamicStep (valuationLookup (declarations script) ρ)) {}
  return s.assertedRev.reverse

def Satisfies (script : List Cmd) (ρ : Valuation script) : Prop :=
  evaluate script ρ = some [true, true]

theorem valuationsInhabited (script : List Cmd) : Nonempty (Valuation script) :=
  ⟨zeroValuation script⟩

theorem noModelOfResults (script : List Cmd)
    (h : ∀ ρ : Valuation script, evaluate script ρ = some [true, false]) :
    ¬ ∃ ρ : Valuation script, Satisfies script ρ := by
  rintro ⟨ρ, hs⟩
  have bad : (some [true, false] : Option (List Bool)) = some [true, true] :=
    (h ρ).symm.trans hs
  contradiction

end SmtW02

