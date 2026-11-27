# Four registered proof attempts for a real logarithm bound

**Sepehr Mahmoudian · 2026**. Cite this record with the exact repository commit or release. [Software citation](../../../CITATION.cff)

The claim concerns the error left after summing finitely many terms of a real logarithm series. The proposed bound adds a factor that depends on the number of retained terms. The separate Linux check of two existing Mathlib statements succeeded. That check used a different statement and a different judge. [Two original library bounds](../real-log-library-read/HOSTED-RESULTS.md) · [Exact scientific statement](Model.lean) · [Prospective contract](frozen.json)

The fixed four-attempt limit was reached. The first proof text failed its permitted-source check before any Lean command. The next three attempts compiled the model. In each case the proof compiler returned status 1 and produced no compiled proof object. The further checks of the declaration, the three fresh kernel reads and the intentionally false control did not run. No attempt passed the complete registered test.

| Attempt | Actual result | Original evidence |
|---|---|---|
| 1 | The proof text used a forbidden numeric projection. Its source check stopped before the Linux proof field. | [Accepted source language](allowed-identifiers.txt) · [Original rejection](history/attempt-01-TERMINAL.json) |
| 2 | The proof tried to use equality symmetry on a function from an equality to false. The compiler printed a partial term containing a placeholder axiom. | [Native records](history/attempt-02-native-evidence.json) · [Complete compiler print](history/attempt-02-proof.stdout.txt) · [Linux job](https://github.com/sepahead/pid-rs/actions/runs/45567721612/job/139046511327) |
| 3 | An unused ring tactic at line 42 failed the compiler policy that treats this warning as an error. | [Native records](history/attempt-03-native-evidence.json) · [Complete compiler print](history/attempt-03-proof.stdout.txt) · [Linux job](https://github.com/sepahead/pid-rs/actions/runs/45581754714/job/139093263561) |
| 4 | The same policy rejected three unnecessary tactic sequences, at line 42 column 49 and line 44 columns 21 and 44. The compiler printed a proposed term and axioms before exit. | [Native records](history/attempt-04-native-evidence.json) · [Complete compiler print](history/attempt-04-proof.stdout.txt) · [Linux job](https://github.com/sepahead/pid-rs/actions/runs/45638237493/job/139289397528) |

Each native record gives the exact scientific source digest, the original artifact digest, the digests of its 17 files and the two commands that ran. The compiler text is openly readable even after a hosted artifact expires. The original source workflow remains in the field directory for inspection. A mathematical proof on paper and the nine separately checked integer grid statements have their own premises and evidence. [Original workflow](workflow.source.yml) · [Written real bound and integer calculations](../../research/signed-log-certificate-enclosure/EXPOSITION.md)
