# Finite-index proofs passed fresh checks before the term observer exceeded its memory limit

Sepehr Mahmoudian · 21 November 2026

Stock Lean compiled two proofs about an invented table with 83 positions. It also checked the compiled proofs again in fresh kernel environments. A separate command reported the axioms used by all 170 named theorems. The next command exceeded the registered memory limit before it returned a row. **The calibration failed.** Its selection rule stops the proposed follow-up on three original scripts. [Hosted job](https://github.com/sepahead/pid-rs/actions/runs/44862925463/job/136720115700) · [Registered question and selection rule](../../research/index-family-control-registration.json) · [Earlier original failures](../three-original-reachable-attempt-2026-11-21/README.md)

## What was checked

A *finite index* is a natural number smaller than a fixed bound. Here the index is $i$, from 0 through 82. The *argument* $x$ is any natural number, including zero. A *readiness flag* $r$ has two possible values. The *table entry* $a_i$ is a given nonnegative integer. A *leaf* is a proof for one index. A *consumer* is a separate declaration that requires a proof of an explicit statement. An *axiom* is an assumption that a proof may use. A *term* is Lean's stored expression for a definition or a proof. All quantities in this example are dimensionless integers. The inputs are invented. [Registered specification](../../research/index-family-control/lean/IndexSpec.lean) · [Consumer statements](../../research/index-family-control/lean/IndexConsumer.lean)

The left side is $3i+2+x$. The right side is $a_i+x$ when the flag is true and $a_i+x+1$ when it is false. The table starts at $a_0=37$. It has $a_i=3i+2$ at each positive index. Each proof must show equality **for every natural argument when the flag is true and the index is positive**. For example, index 1 with argument 7 gives 12 on both sides when ready and 13 on the right when unready. At index 0 with argument 7 and readiness true, the two sides are 9 and 44. These are calculations from the definitions. The native numerical trace was never reached. [Proof inputs](submitted.json) · [Trace source](../../research/index-family-control/lean/IndexTrace.lean)

One construction joins 83 named leaves by finite cases. Its zero branch has a contradictory positive-index premise. Its tail has index type `Fin 0`, which has no values. The other construction uses 83 case splits in a single 333-line proof. It has no reference to a named leaf or cover in the submitted text. The two consumer definitions specify the same quantified equality. They refer to `cover00` and `inlineComplete`, respectively. The full proof-term observer did not record their direct dependencies. [Named construction](../../research/index-family-control/lean/IndexProofs.lean.in) · [Single-slot construction](../../research/index-family-control/lean/IndexInline.lean.in)

| Required observation | Actual result |
|---|---|
| Official stock release and source checks | The archive checksum matched the registered value. Stock Lean 4.34.1 reported source revision `5045d0056413266e57c625dcd7c365b10e377c52`. |
| Four ordinary modules and four fresh checks | `IndexSpec`, `IndexProofs`, `IndexInline` and `IndexConsumer` each compiled without diagnostics. Every corresponding `leanchecker --fresh` exited 0. |
| Separate transitive axiom listing | Lean printed all 170 entries. The empty-tail theorem `IndexExample.cover83` used no axioms. The other 169 used propositional extensionality, `propext`, which identifies equivalent propositions. |
| Complete stored types, terms and their dependencies | Command 13 of 17, `inspect-IndexTerms`, exceeded the memory ceiling and exited with signal 9. Its two output streams were empty. It wrote no compiled object. It delivered 0 of 170 term records and 0 of 254 required direct dependency checks. |
| Numeric trace and false closings | The job stopped before the 332 trace rows and all three expected native refusals. The refusals concern an unready position, index zero and a false equality at the last index. |
| Scope | This run tested no original script. The preceding original attempts and the separately checked W02 result retain their respective outcomes. |

Stock `--fresh` first loads the module and its imports. It sends eligible stored declarations to a new kernel environment at trust level zero. It reintroduces axiom declarations as assumptions and skips unsafe and partial constants. The successful runs therefore give evidence for the two stated formal consumers under the named toolchain. They do not supply the missing output from the term observer or establish what happens for a different interpreter or table. [Stock checker](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/LeanChecker.lean#L36-L38) · [Stock replay](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Lean/Replay.lean#L167-L188) · [W02 result](../../research/three-source-w02/README.md)

## Rust implementation and computational cost

This experiment concerns proof checking. It uses stock Lean and a standard-library Python observer. It has no statistical estimand, sample, fitted model, information units or Rust estimator API. One hosted Linux job used one logical CPU under registered ceilings of 2,700 seconds in total, 900 seconds per native command, 4 GiB of direct or sampled process-group resident memory and 1 GiB of retained evidence. Resident memory counts physical pages reported as resident under the registered Linux measurement. The job had an outer limit of 55 minutes. Stock archive extraction had a separate destination.

The four fresh checks took 45.80–46.40 seconds each. The failed observer ran for 2.65 seconds. The sampled process-group peak and the direct process measurement each reached **4,438,499,328 bytes**. The ceiling was **4,294,967,296 bytes**. The runner recorded 31 memory samples for this command and found its process group gone after cleanup. The native campaign stopped after 212.17 seconds. The receipt identifies the observer and the memory stop. Its empty streams do not locate the expression or operation responsible for the peak. [Native resource monitor](../../research/three-source-original-reachable-v3/native_resources.py) · [Complete native archive](native-evidence.zip)

## Read the retained evidence

The public ZIP contains all 58 regular files from artifact 14690508470. It has 534,167 compressed bytes and 1,608,186 bytes of member data. SHA-256 is `85ccfa1c1e746b51df96a6529dea25137bb36c286fd1d03d0e45fb555ac342bc`. The files preserve all ten materialized sources, five compiled objects, 13 command records, 26 raw output streams, the exact import sequence, registration, launch and terminal records. The offline reader treats them as data. It does not load a compiled Lean object. The submitted payload, file inventory and selected hosted metadata are also available separately. [Native ZIP](native-evidence.zip) · [Portable record](record.json) · [Public submission](submitted.json) · [Original hosted artifact](https://github.com/sepahead/pid-rs/actions/runs/44862925463/artifacts/14690508470)

From a clean checkout, use Python 3.11 or later. Both commands must report the historical failure. The self-test rejects fifteen changed interpretations, including invented completed checks.

```sh
python3 -I -S -B audit/evidence/index-family-control-attempt-2026-11-21/check.py --self-test
python3 -I -S -B -O audit/evidence/index-family-control-attempt-2026-11-21/check.py --self-test
```

One fixed artificial input was selected before the first and only enrolled push. The judge, table and expected values were exposed before submission. The selected proof lines are retained here. The operator inspected the same retained outputs in two Python modes. These runs and the model-assisted review share the source, supplier and archived observations. They provide no separate human scientific disposition. Any proposed change to the observer needs its own prospective registration, full terms and types, axiom and dependency records, finite trace and false controls under the stated limits. The failed registration remains spent. [Registered method](../../research/index-family-control/README.md) · [One-shot input commit](https://github.com/sepahead/pid-rs/commit/39cecc889f81f62608cf4f836cfcef20b730a80c)

**Suggested citation.** Sepehr Mahmoudian (2026), *Finite-index proofs passed fresh checks before the term observer exceeded its memory limit*. Include the exact repository commit or release, run 44862925463 and the native archive digest. [Software citation](../../../CITATION.cff)
