# Three original proof inputs and the memory limit

Sepehr Mahmoudian · 20 November 2026

Of the 22 original formulas that solvers reported as unsatisfiable, W02 has a complete stock Lean proof for the formal reading of its input. An unsatisfiable formula has no assignment of values that makes all its assertions true. This later test selected three of the other 21 formulas. It obtained no additional complete proof. [W02 statement and proof](../../research/three-source-w02/README.md) · [Original formulas](../../formal/finite-smt39-qualification-v1/README.md)

## What the test required

Each input is a script with 89 commands. An assignment gives each of 25 variables a value of its declared type. For each assignment, the interpreter must successfully return the two assertion values. At least one must be false. The proof must also connect this result to a finite table computed from the specified input. A failed evaluation cannot serve as a false assertion. [Statements, acceptance rules and input identities](../../research/three-source-original-first-three-attempt.json)

The selection used the meaning of the formulas. W01 compares the validity of each family code with its membership in a specified list. W03 asks whether the stated order relates each valid family to itself. W15 tests an identity for a joint event. All three solver labels were known. The test used one submission, with a fixed order and limits. [Registered procedure](../../research/three-source-original-first-three/README.md) · [Submitted proof bodies](submitted/)

## What happened

| Input | Result |
|---|---|
| W01 | Nineteen modules each passed compilation and a fresh stock check. Compilation of the next module, `OriginalDynamic`, reached the memory limit. |
| W03 | The files for the test had been prepared. No command ran on this case. |
| W15 | The files for the test had been prepared. No command ran on this case. |

The host ran stock Lean 4.34.1. Across setup, artificial controls and W01, 58 commands succeeded. Four commands correctly rejected altered proofs. The 63rd command stopped after 428.17 seconds. The monitor recorded 4,296,556,544 bytes of memory in the process group. Its limit was 4,294,967,296 bytes, or four gibibytes. The campaign used 1,519.85 seconds of its 5,400-second budget. [Execution and job log](https://github.com/sepahead/pid-rs/actions/runs/44760935574)

The last command produced no text on either output stream. Its module contained six declarations. The available measurements do not identify the declaration that caused the peak. The run produced no complete W01 evaluation table or final proof for the original claim. All three cases remain open. A new attempt needs a separate registration. A possible change is to compile smaller lemmas separately and measure their use of memory before submitting an original formula.

## Inspect the records

The public result gives the registered limits, the tool and source identities, and all 63 command outcomes in order. The submitted files preserve the three proof proposals as data. The companion program reads the records without executing the proposals. The original archive has 345 files. Its SHA-256 digest is `ad493f45a89be70f62c9dc5c965f2dc3ffd8b0bc162f891cbe11df8e1c41c365`. [Result](result.json) · [Record reader](check.py) · [Original hosted archive](https://github.com/sepahead/pid-rs/actions/runs/44760935574/artifacts/14642817786)

From the root of a checkout, run the first command to compare the local sources, submissions and command summary. With the original ZIP file, run the second command to compare every command result and both of its output streams.

```sh
python3 -I -B audit/evidence/three-source-original-proof-attempt-2026-11-20/check.py
python3 -I -B audit/evidence/three-source-original-proof-attempt-2026-11-20/check.py /path/to/original-first-three.zip
```

**Citation.** Sepehr Mahmoudian, *Three original proof inputs and the memory limit* (2026). Include the exact repository commit or release. [Software citation](../../../CITATION.cff)
