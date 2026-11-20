# What survived the failed synthetic assertion test

Sepehr Mahmoudian · 20 November 2026

The test asked whether small proofs can recover both assertions of an invented program when the program has an unused variable. All 22 named theorems passed their checks. The complete test **failed**. The compiler stopped its third deliberately false example for a different reason from the one required. This result concerns the invented programs. The earlier test of three original formulas has its own record. [Synthetic registration](../../research/synthetic-assertion-reachable-v2-registration.json) · [Three original formulas](../three-source-original-proof-attempt-2026-11-20/README.md)

## The programs and their outputs

An **assertion** is an expression that must give a true or false value when evaluation succeeds. A **valuation** supplies each input with a value of its declared type. An **environment** stores the values and functions available to the interpreter. The **projection** keeps one Boolean input and omits one integer input. The output lists both assertion values in their original order. Failure to evaluate has the separate result `none`. [Interpreter](../../research/three-source-w02/lean/W02Semantics.lean) · [Invented programs](../../research/synthetic-assertion-reachable-v2/lean/RouteSpec.lean)

| Invented program | Boolean | Integer | Ordered result |
|---|---:|---:|---|
| Primary | false | 0 | false, true |
| Primary | true | 1 | true, false |
| Reads the integer | true | 0 | true, false |
| Reads the integer | true | 1 | false, true |
| Refers to a missing name | false | 0 | Evaluation fails |

In the primary program, a function returns the Boolean input. The assertions read this function and its negation. Hold the Boolean fixed at true and change the integer from 0 to 1. A lookup of the integer distinguishes the two environments. Both valuations still give the same primary output. The primary theorem covers both Booleans and every integer. In the changed program, the first assertion tests whether the integer equals zero. The third and fourth table rows show why the same projection then loses information. [Checked statements](../../research/synthetic-assertion-reachable-v2/lean/RouteConsumer.lean)

## Why the complete test failed

A **heartbeat** is an internal unit that Lean uses to bound work. The third false example asserted that the two different outputs were equal. It proposed reflexivity as the reason. The registered control required a specific error explaining that the two expressions differ. The compiler instead reached its 200,000-heartbeat limit during reduction. It returned exactly one error, on line 4 of the expected file. The reader correctly rejected that error. The checked positive theorem had already established the two different outputs. [False statement](../../research/synthetic-assertion-reachable-v2/negative/RefuseReachedInteger.lean) · [Required diagnostic](../../research/synthetic-assertion-reachable-v2/negative.json) · [Raw result and diagnostic](result.json)

Eight ordinary modules compiled and passed separate stock Lean checks. A further three modules inspected the results. The term and axiom records agreed on the 22 theorem names. Two names used no transitive axioms, five used only `propext`, and 15 used `Classical.choice`, `Quot.sound` and `propext`. Eight typed consumers referred directly to the intended theorems. Two earlier false examples produced their required errors. The fourth false example, the three Linux monitor controls and final source and object checks were unreached. [Hosted job and full log](https://github.com/sepahead/pid-rs/actions/runs/44806160042/job/136530593268)

## Rust implementation and computational cost

This is an offline test of a project-defined interpreter model. Stock Lean 4.34.1 checked the proofs. The programs use one Boolean and one unbounded integer. They use no samples or estimator and have no production Rust API. Each of 25 native commands ran in sequence. The first 22 returned zero. The next three returned one. Only the first two of these three gave the required diagnostic.

The complete run used 393.92 seconds. Its largest sampled process-group memory was 788,189,184 bytes. The largest direct-child peak was 820,879,360 bytes. Both occurred during inspection of the theorem expressions. The third false example used 10.49 seconds and 592,027,648 bytes. The limits were 4 GiB for observed process-group memory, 900 seconds per command, 5,400 seconds in total and 1 GiB of retained evidence. These measurements apply to this workload. [Command records and limits](result.json)

The archive contains 108 files. Its compressed size is 705,318 bytes and its SHA-256 is `786cfda4673fd44de66e95df04afbc81b795a0982b4a50838d4dccbb15d995c1`. The submitted proof bodies are preserved as text data. The index gives the byte count and SHA-256 of each archive and job-log member. [Submitted proposal](submitted-proof-bodies.json.txt) · [File index](archive-members.json) · [Original hosted archive](https://github.com/sepahead/pid-rs/actions/runs/44806160042/artifacts/14663932446)

**Citation.** Sepehr Mahmoudian, *What survived the failed synthetic assertion test* (2026). Include the exact repository commit or release. [Software citation](../../../CITATION.cff)
