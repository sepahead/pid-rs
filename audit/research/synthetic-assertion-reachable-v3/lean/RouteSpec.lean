import ProjectionCore

namespace RouteSpec
open SmtW02 ArchivedProjection

def prefixCommands : List Cmd :=
  [.constant "keep" .bool, .constant "unused" .int,
   .define "idb" [("x", .bool)] .bool (.name .bool "x"),
   .define "relay" [] .bool (.app .bool "idb" [.name .bool "keep"])]

def scriptWith (assertion : Term) : List Cmd :=
  [.logic "ALL", .option ":produce-models" "true"] ++ prefixCommands ++
    [.echo "\"qualification\"", .assertion assertion,
     .assertion (.app .bool "not" [assertion]), .check, .exit]

def primary := scriptWith (.name .bool "relay")
def readingTag := scriptWith (.app .bool "=" [.name .int "unused", .numeral 0])
def malformed := scriptWith (.name .bool "missing")
def bitIndex : Fin (declarations primary).length := ⟨0, by decide⟩
def tagIndex : Fin (declarations primary).length := ⟨1, by decide⟩
def bit (v : Valuation primary) : Bool := v bitIndex
def tag (v : Valuation primary) : Int := v tagIndex

def sample (b : Bool) (i : Int) : Valuation primary :=
  put primary bitIndex b (put primary tagIndex i (zeroValuation primary))
def sample0 := sample true 0
def sample1 := sample true 1

def tagSample (b : Bool) (i : Int) : Valuation readingTag :=
  put readingTag ⟨0, by decide⟩ b (put readingTag ⟨1, by decide⟩ i (zeroValuation readingTag))

def state (v : Valuation primary) : Option DynamicState :=
  prefixCommands.foldlM (dynamicStep (valuationLookup (declarations primary) v)) {}

def fetch (s : Option DynamicState) (name : String) : Option Value := do
  let finalState ← s
  let fn ← finalState.globals.lookup name
  fn []

def observed (b : Bool) : Option (List Bool) := some [b, !b]

def fromValue : Option Value → Option (List Bool)
  | some (.boolean b) => observed b
  | _ => none

end RouteSpec
