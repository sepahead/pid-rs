import W02Semantics

set_option maxRecDepth 8192
namespace SmtW02

def t01 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T01-equality-pair\""),
  (Cmd.constant "x" (Ty.int)),
  (Cmd.assertion (Term.app (Ty.bool) "=" [(Term.name (Ty.int) "x"), (Term.name (Ty.int) "x")])),
  (Cmd.assertion (Term.app (Ty.bool) "not" [(Term.app (Ty.bool) "=" [(Term.name (Ty.int) "x"), (Term.name (Ty.int) "x")])])),
  (Cmd.check),
  (Cmd.exit)
]

def t02 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T02-swapped-assertions\""),
  (Cmd.constant "x" (Ty.int)),
  (Cmd.assertion (Term.app (Ty.bool) "not" [(Term.app (Ty.bool) "=" [(Term.name (Ty.int) "x"), (Term.name (Ty.int) "x")])])),
  (Cmd.assertion (Term.app (Ty.bool) "=" [(Term.name (Ty.int) "x"), (Term.name (Ty.int) "x")])),
  (Cmd.check),
  (Cmd.exit)
]

def t03 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T03-arbitrary-negative-model\""),
  (Cmd.constant "x" (Ty.int)),
  (Cmd.assertion (Term.app (Ty.bool) "<" [(Term.name (Ty.int) "x"), (Term.app (Ty.int) "-" [(Term.numeral 10000000000000000000000)])])),
  (Cmd.assertion (Term.app (Ty.bool) "<=" [(Term.name (Ty.int) "x"), (Term.name (Ty.int) "x")])),
  (Cmd.check),
  (Cmd.exit)
]

def t04 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T04-three-way-distinct\""),
  (Cmd.assertion (Term.boolean true)),
  (Cmd.assertion (Term.app (Ty.bool) "distinct" [(Term.bits 3 0), (Term.bits 3 1), (Term.bits 3 0)])),
  (Cmd.check),
  (Cmd.exit)
]

def t05 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T05-distinct-positive\""),
  (Cmd.assertion (Term.boolean true)),
  (Cmd.assertion (Term.app (Ty.bool) "distinct" [(Term.bits 3 0), (Term.bits 3 1), (Term.bits 3 2)])),
  (Cmd.check),
  (Cmd.exit)
]

def t06 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T06-zero-extended-sub\""),
  (Cmd.assertion (Term.app (Ty.bool) "=" [(Term.indexed (Ty.bv 7) "zero_extend" [4] (Term.app (Ty.bv 3) "bvsub" [(Term.bits 3 0), (Term.bits 3 1)])), (Term.bits 7 7)])),
  (Cmd.assertion (Term.app (Ty.bool) "not" [(Term.app (Ty.bool) "=" [(Term.app (Ty.bv 7) "bvshl" [(Term.bits 7 1), (Term.bits 7 7)]), (Term.bits 7 0)])])),
  (Cmd.check),
  (Cmd.exit)
]

def t07 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T07-extract-and-or\""),
  (Cmd.assertion (Term.app (Ty.bool) "=" [(Term.indexed (Ty.bv 3) "extract" [3, 1] (Term.bits 4 10)), (Term.bits 3 5)])),
  (Cmd.assertion (Term.app (Ty.bool) "=" [(Term.app (Ty.bv 3) "bvor" [(Term.app (Ty.bv 3) "bvand" [(Term.bits 3 5), (Term.bits 3 3)]), (Term.bits 3 2)]), (Term.bits 3 3)])),
  (Cmd.check),
  (Cmd.exit)
]

def t08 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T08-param-scope\""),
  (Cmd.constant "x" (Ty.int)),
  (Cmd.constant "q" (Ty.bool)),
  (Cmd.define "xplus" [] (Ty.int) (Term.app (Ty.int) "+" [(Term.name (Ty.int) "x"), (Term.numeral 1)])),
  (Cmd.define "choose" [("q", (Ty.bool)), ("x", (Ty.int)), ("y", (Ty.int))] (Ty.int) (Term.app (Ty.int) "ite" [(Term.name (Ty.bool) "q"), (Term.name (Ty.int) "x"), (Term.name (Ty.int) "y")])),
  (Cmd.define "g" [("x", (Ty.int)), ("q", (Ty.bool))] (Ty.int) (Term.app (Ty.int) "choose" [(Term.name (Ty.bool) "q"), (Term.name (Ty.int) "x"), (Term.name (Ty.int) "xplus")])),
  (Cmd.assertion (Term.app (Ty.bool) "=" [(Term.app (Ty.int) "g" [(Term.numeral 8), (Term.boolean true)]), (Term.numeral 8)])),
  (Cmd.assertion (Term.app (Ty.bool) "=" [(Term.app (Ty.int) "g" [(Term.numeral 11), (Term.boolean false)]), (Term.app (Ty.int) "+" [(Term.name (Ty.int) "x"), (Term.numeral 1)])])),
  (Cmd.check),
  (Cmd.exit)
]

def t09 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T09-unused-int\""),
  (Cmd.constant "w" (Ty.int)),
  (Cmd.define "dead" [] (Ty.bool) (Term.app (Ty.bool) ">" [(Term.name (Ty.int) "w"), (Term.numeral 999999999999)])),
  (Cmd.assertion (Term.boolean true)),
  (Cmd.assertion (Term.boolean false)),
  (Cmd.check),
  (Cmd.exit)
]

def t10 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T10-comments-whitespace\""),
  (Cmd.assertion (Term.app (Ty.bool) "=>" [(Term.boolean true), (Term.boolean true)])),
  (Cmd.assertion (Term.app (Ty.bool) "=" [(Term.app (Ty.int) "ite" [(Term.boolean false), (Term.numeral 7), (Term.numeral 4)]), (Term.numeral 4)])),
  (Cmd.check),
  (Cmd.exit)
]

def t11 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T11-indicator-sum\""),
  (Cmd.define "pred" [("f", (Ty.bv 2))] (Ty.bool) (Term.app (Ty.bool) "=" [(Term.app (Ty.bv 2) "bvand" [(Term.name (Ty.bv 2) "f"), (Term.bits 2 1)]), (Term.bits 2 1)])),
  (Cmd.assertion (Term.app (Ty.bool) "=" [(Term.app (Ty.int) "+" [(Term.app (Ty.int) "ite" [(Term.app (Ty.bool) "pred" [(Term.bits 2 0)]), (Term.numeral 1), (Term.numeral 0)]), (Term.app (Ty.int) "ite" [(Term.app (Ty.bool) "pred" [(Term.bits 2 1)]), (Term.numeral 1), (Term.numeral 0)])]), (Term.numeral 1)])),
  (Cmd.assertion (Term.app (Ty.bool) "distinct" [(Term.bits 2 0), (Term.bits 2 1)])),
  (Cmd.check),
  (Cmd.exit)
]

def t12 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T12-different-count-conjunct\""),
  (Cmd.assertion (Term.boolean true)),
  (Cmd.assertion (Term.app (Ty.bool) "not" [(Term.app (Ty.bool) "and" [(Term.app (Ty.bool) "=" [(Term.app (Ty.int) "+" [(Term.numeral 1), (Term.numeral 1)]), (Term.numeral 3)]), (Term.app (Ty.bool) "distinct" [(Term.bits 2 0), (Term.bits 2 1)])])])),
  (Cmd.check),
  (Cmd.exit)
]

def t13 : List Cmd := [
  (Cmd.logic "ALL"),
  (Cmd.option ":produce-models" "true"),
  (Cmd.echo "\"T13-different-distinct-conjunct\""),
  (Cmd.assertion (Term.boolean true)),
  (Cmd.assertion (Term.app (Ty.bool) "not" [(Term.app (Ty.bool) "and" [(Term.app (Ty.bool) "=" [(Term.app (Ty.int) "+" [(Term.numeral 1), (Term.numeral 1)]), (Term.numeral 2)]), (Term.app (Ty.bool) "distinct" [(Term.bits 2 0), (Term.bits 2 0)])])])),
  (Cmd.check),
  (Cmd.exit)
]

end SmtW02
