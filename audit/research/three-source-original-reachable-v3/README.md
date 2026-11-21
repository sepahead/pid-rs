# Three original finite proof obligations

This package prepares a proof check for three archived input files. Each file has two assertions. The question is whether the specified interpreter can return true for both assertions for any assignment of the 25 input variables. A proof must show that evaluation succeeds for every assignment. It must give the two results in the order in the file.

A **valuation** assigns a value of the declared type to every input. Sixteen inputs can take any integer value. A **prefix** is an initial segment of the command list. When the interpreter reads a function definition, it stores a function that can use the earlier definitions. A **retained command** is an original constant declaration or function definition used by an assertion, directly or through another definition. The check compares call results under the full valuation with results from the retained commands. It checks installation for each of the 83 prefix lengths from 0 through 82. The source reader binds all 89 commands. [Original interpreter](../three-source-w02/lean/W02Semantics.lean) · [Original formulas and solver records](../../formal/finite-smt39-qualification-v1/README.md)

| Original | Projected values | Two assertion results that the check requires |
|---|---|---|
| W01 | All 128 seven-bit family masks | True, followed by the negation of equality between the validity test and membership in the fixed list of 18 family masks. The second result must be false. |
| W03 | All 128 seven-bit family masks | The validity test, followed by the negation of the source order applied to the mask twice. An invalid mask can give false for the first result. At least one result must be false. |
| W15 | All 256 ordered pairs of four-bit cell keys | True, followed by the negation of equality between the full-source event and agreement of the two keys on bits 3, 2 and 1. The second result must be false. |

For example, W15 compares two source patterns. A four-bit key assigns three bits to the sources and one bit to the target. The literal right operand tests the three source bits in order. It omits bit 0. A proof must also recover the left operand from the original function calls and show that the full interpreter returns the specified pair on every assignment of the other inputs.

The earlier attempt reached its memory limit in W01. W03 and W15 did not start. The artificial checks that later passed use an invented input. They give an example in which two valuations produce different environments and the same ordered results. These records have distinct scopes. [Earlier original attempt](../../evidence/three-source-original-proof-attempt-2026-11-20/README.md) · [Artificial check](../synthetic-assertion-reachable-v3/README.md) · [Registered mathematical requirements](task.json)

## Check the source

Use Python 3.11 or later in a checkout that includes the named historical Git objects. Supply the reviewed SHA-256 of this package's manifest. The output directory must be new and outside the checkout.

```sh
python3 -I -S -B audit/research/three-source-original-reachable-v3/run.py \
  --check-sources --expected-manifest "$REVIEWED_SHA256" --output "$NEW_OUTPUT"
```

The source operation records two parse results, the original Lean literal, the proof statements, owner names, call dependencies, individual lemma templates and interval limits. It performs zero original assertion evaluations. It supplies no native proof verdict.

The three inputs correspond to three parts of Program A. W01 tests the complete list of seven-bit antichain masks in L1. W03 tests reflexivity of the order in L2. W15 tests the full-family source event in D2. W03 gives no matrix inverse. W15 gives no general count or logarithm result. None of these three files addresses the complete output-certificate parser in D1 or closes Programs A through E. [Program definitions and remaining obligations](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md#program-and-obligation-credit)

## Rust implementation and computational cost

The hosted check uses one sequential Linux proof worker on one allowed logical CPU. The scientific clock starts before checkout. Common setup, stock retrieval and the artificial controls have 1,500 seconds. W01, W03 and W15 each have up to 5,400 seconds. The combined limit is 18,000 seconds, including a 300-second final custody reserve. The separate workflow timeout is 320 minutes. The native command limit stays at 900 seconds. The checker samples the command's process group and reads the direct child's peak memory. Both must stay within 4 GiB. All cases share a 1 GiB retained-evidence limit.

A case that breaches its memory or time limit fails. The next case can start only after the native group has ended and the case inputs, compiled objects and common stock supplier pass the transition check. Shared custody, shared storage, global time or lingering-process failures stop the run. Each case keeps its own terminal record. All three cases must pass for an all-three result. Artifact upload and independent archive readback have separate receipts.

Each case uses a fresh module directory. The judge compiles 32 scientific modules and requests a separate stock fresh replay for each. Three additional diagnostic modules print the finite outputs, the axiom list and the proof records. The judge also elaborates each proof in the call and interval groups separately. Those isolated runs produce no scientific import. It records the exact source and import bytes at each stage. The observer checks every named proof term, its type, its owner and its direct and transitive axioms. The separate output check reads both Booleans at every finite coordinate. A missing result stays open. This is an offline formal check. It supplies no estimator timing or Rust refinement.
