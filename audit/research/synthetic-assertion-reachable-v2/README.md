# Synthetic check of projection for two assertions

Sepehr Mahmoudian, 2026. A citation includes the exact repository commit or release. [Software citation](../../../CITATION.cff)

## Question and terms

Can separate small proofs recover the outcomes of both original assertions in an invented program? The project defines this qualification. It uses the fixed finite interpreter from the repository. A **valuation** assigns one value of the correct type to each declared variable. An **environment** stores the declared values and functions available at one step in the program. The **projection** keeps the Boolean variable named `keep` and omits the integer named `unused`. [Interpreter](../three-source-w02/lean/W02Semantics.lean) · [Qualification task](task.json)

The function `idb` returns its Boolean argument. The function `relay` calls `idb` on `keep`. The two assertions test `relay` and its logical negation. A **successful output** contains the Boolean result of each assertion in source order. Failure has a separate result, called `none`. [Source program](lean/RouteSpec.lean)

## Worked examples and false alternatives

| Invented program | Values supplied | Required ordered output |
|---|---|---|
| Primary | `keep=false, unused=0` | false, true |
| Primary | `keep=true, unused=1` | true, false |
| Integer comparison | `keep=true, unused=0` | true, false |
| Integer comparison | `keep=true, unused=1` | false, true |
| Missing name in an assertion | Zero valuation | Failure |

Now hold `keep` fixed at true in the primary program. Set `unused` to 0 in one valuation and 1 in another. A lookup of `unused` gives different results, so the complete environments differ. Both assertions read `relay`, so both valuations give the same ordered output. In the second program the first assertion reads the omitted integer. The same projection now loses information needed for the answer. [Definitions and typed conclusions](lean/RouteResult.lean)

The fixed qualification requires proofs for **all** full primary valuations, including every integer. It also checks the two possible retained Boolean values. The two finite examples alone cannot prove the full-valuation statement. Treating failure as a successful false assertion would also invalidate the result. [Protected statements](helpers.json) · [Typed consumers](lean/RouteConsumer.lean)

## Acceptance and trust

The candidate supplies proof bodies for nine fixed statements. Three separate modules contain the proof bodies. A fixed module combines them. Eight typed consumers refer directly to the required declarations. The observer checks 22 theorem names, owning modules, types, proof expressions, direct axiom use and transitive axiom use. Each transitive set may contain only `Classical.choice`, `Quot.sound` and `propext`. The stock tool also replays every ordinary module in a new process. [Expected declarations and edges](roster.json) · [Stock term observer](lean/RouteInspect.lean)

Four false claims must produce their registered type-checking failures. Two controls test the proof-input grammar. A separate reader control inserts a fabricated forbidden axiom into a copy of an actual axiom report. The reader must reject this altered report. A successful small command, a memory overrun and a time overrun test the Linux resource monitor. [Negative proof controls](negative.json) · [Qualification checker](check.py)

The output records retain source and object identities, term and axiom readbacks, process status, and the final resource result. The formal check concerns this invented program and its explicitly named results. The ordinary compiled imports and the stock checker share a release. This qualification leaves the retired original three-formula run at its own recorded outcome.

## Rust implementation and computational cost

This is an offline proof qualification. It has no estimator, sampled rows, alphabet estimation, training procedure, or production Rust API. The source domain has one Boolean and one unbounded integer. The proof checks a finite split of the Boolean domain. It must separately justify omission of every possible integer from the primary assertions. The exact finite readback has five rows.

The operator runs one stock Lean 4.34.1 worker at a time. Each command has a 900-second time limit. The campaign has 5,400 seconds, 4 GiB of observed process-group resident memory and 1 GiB of retained evidence. Direct-child peak memory is also checked. The operating system can stop the worker at the first recorded resource violation. The memory test uses 96 MiB and requests 144 MiB under that separate control. There is no production runtime measurement in this registration.

A source-only check can inspect the input definitions, templates and custody before the proof file exists. A separate earlier registration fixes the judge manifest, hosted workflow, stock release and allowed proof-file path. Only the uniquely named push associated with that registration may execute the native qualification. [Full predicate](task.json) · [Protected source inputs](external.json)
