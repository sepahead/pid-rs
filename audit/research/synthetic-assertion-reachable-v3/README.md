# Synthetic check of equality between two assertion outputs

Sepehr Mahmoudian · 20 November 2026

The question is whether a small negative test can keep the full statement of a prior failed test and produce the required compiler diagnostic. Lean previously exhausted its internal work budget on the false statement. The program, both inputs and the nine previously submitted proof bodies have fixed identities. This version changes how the diagnostic reaches the final comparison. The first issued test retains its failure. [Earlier record](../../evidence/synthetic-assertion-route-attempt-2026-11-20/README.md) · [Qualification task](task.json)

## Terms and example

A **valuation** supplies each declared variable with one value of its type. An **assertion** is an expression with a true or false value when evaluation succeeds. The program supplies a Boolean named `keep` and an integer named `unused`. An **ordered output** records both assertion values from first to last. The interpreter uses a separate result, `none`, for failure. [Program](lean/RouteSpec.lean) · [Interpreter](../three-source-w02/lean/W02Semantics.lean)

The primary program reads the Boolean and its negation. Two valuations with the same Boolean can have different integers and different complete environments. They give the same primary output. A changed program tests whether the integer equals zero.

| Program | Boolean | Integer | First and second assertion values |
|---|---|---:|---|
| Primary | false | 0 | false, true |
| Primary | true | 1 | true, false |
| Tests the integer | true | 0 | true, false |
| Tests the integer | true | 1 | false, true |
| Uses a missing name | false | 0 | Evaluation fails |

The designated false statement asserts equality between the fourth and third outputs, in that order. These are two calls to the full interpreter on the same changed program. The complete statement still names both calls and their original valuations. [Typed consumers](lean/RouteConsumer.lean) · [False statement](negative/RefuseReachedInteger.lean)

## How the diagnostic works

Call the two evaluations `x` and `y`. Let `a` and `b` be their respective known outputs. The qualification uses the following rule for any one type. Given `x = a` and `y = b`, the statement `x = y` is equivalent to `a = b`. This use of equalities to move between propositions is called **transport**. Both directions follow by symmetry and transitivity of equality.

A fixed ordinary theorem applies the rule to the original two evaluations. A second check uses a true equality and a third establishes that the actual evaluations differ. The negative test applies one direction of the rule and asks the compiler to prove the remaining literal equality by reflexivity. The left output is `some [false, true]` and the right output is `some [true, false]`. The reader requires the exact diagnostic class, source line, order and values. An unrelated diagnostic fails the test. [Four protected transport declarations](lean/RouteTransport.lean) · [Expected diagnostics](negative.json)

## What the qualification requires

The historical 22 theorem names, eight typed consumers and five trace outputs retain their full predicates. Four additional theorem names describe the prescribed transport and its positive controls. Nine ordinary modules must compile and pass a fresh stock check. The ordinary compiled imports and the checker share one Lean release. The observer records their trust level and complete theorem terms. The only permitted transitive axioms are `Classical.choice`, `Quot.sound` and `propext`. [Named declarations and required uses](roster.json) · [Observer](lean/RouteInspect.lean)

All four false examples must produce their designated errors. The Linux monitor must also accept a small successful command and stop the registered memory and time controls. The final custody comparison covers the scientific source, all resulting objects, the stock files and the registered input. The earlier nine proof bodies are public. A successful future check would qualify the prescribed diagnostic for these invented programs. Each original formula still needs its own proof. [Registered decision](diagnostic-decision.json) · [Protected checker](check.py)

## Rust implementation and computational cost

This is an offline test of a project-defined interpreter model. It has no estimator, training samples or production Rust API. The primary theorem covers both Booleans and every integer input. The ordinary checks run one stock Lean 4.34.1 process at a time. The process-group memory limit is 4 GiB. The time limits are 900 seconds per command and 5,400 seconds in total. The retained evidence limit is 1 GiB. The proof and failure controls retain Lean’s stock heartbeat budget. A heartbeat is Lean’s internal unit of work. This registration contains no new runtime measurements. [Historical measurements](../../evidence/synthetic-assertion-route-attempt-2026-11-20/README.md)

**Citation.** Sepehr Mahmoudian, *Synthetic check of equality between two assertion outputs* (2026). Include the exact repository commit or release. [Software citation](../../../CITATION.cff)
