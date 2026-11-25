# Evidence and reproduction

**Sepehr Mahmoudian, 2026.** This record accompanies *Reading quoted categorical state tokens*. Cite the exact commit or release used. The scientific paper defines the categorical shared-exclusions functional. The project defines the labeled input and certificate bytes. [Paper](https://doi.org/10.1103/PhysRevE.103.032149) · [Input specification](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/bindings.md) · [Software citation](../../../CITATION.cff)

## Proof, source and trust

The stock proof objects make four declarations of kind theorem. The model uses finite lists of actual unsigned 8-bit values. It admits the 62 ASCII letters and digits and four punctuation bytes. The independently stated bounds are one and 128, inclusive, for the content between quotes. The parser tries the leading quote, reads the longest allowed prefix, checks its size and alphabet, consumes the exact closing quote, and returns the literal suffix. No bound is assumed for that suffix. The high-bit value 255 in the positive example belongs to the suffix. Decimal count fields, state arrays, whole-file order and resources have separate definitions. [Model](lean/Model.lean) · [Formal proof](lean/Proof.lean) · [Observer](lean/Observer.lean) · [False proposition](lean/Contradiction.lean)

| Actual declaration | Exact mathematical content | Transitive axioms reported by stock Lean |
|---|---|---|
| `D1Token.read_emit` | Every admissible token and every suffix return unchanged after writing and then reading. | `propext`, `Quot.sound` |
| `D1Token.read_sound` | Every successful read has an admissible token and reconstructs the complete word. | `propext` |
| `D1Token.read_iff` | Successful read is equivalent to the literal quoted-prefix decomposition with an admissible token. | `propext`, `Quot.sound` |
| `D1Token.unique` | For a fixed successful input, both the token and the suffix are unique. | `propext` |

Propositional extensionality, `propext`, identifies two propositions when each implies the other. Quotient soundness, `Quot.sound`, identifies the quotient images of related representatives. The raw value and full type of each named theorem were printed with proof display enabled. The observer separately applied each declaration to its exact stated inputs. All four transitive lists exclude `sorryAx` and classical choice. The candidate consisted of ordinary proof lines. The model, theorem statements, accepted tactic interface and adverse proposition were fixed outside those proof lines. [Exact stock proof output](proof-terms.txt) · [Source digests](proof-inputs.json)

The observed release was stock Lean 4.34.1 at revision `5045d0056413266e57c625dcd7c365b10e377c52` on Apple arm64. Compiler SHA-256 was `1b370cfcbf44e80d1b004ab1b1ab9a4c73951f9f7c242140bcff9bc577576554` and checker SHA-256 was `cfde41cb11dde58c84e9c60c551fd104bb2fc1104ad44dca932a923120272a35`. The original caller additionally bound 3,257 local stock runtime, object or source entries, including the available `Init` bytecode, its compiled object parts, runtime libraries, and the stock list/byte source. Only ordinary `Init` modules enter the model. No Mathlib, custom kernel, new axiom, foreign execution, native decision shortcut or new proof extension was supplied by this study.

The normal compiler imports stock compiled data. The separate `leanchecker --fresh` route loads the compiled environment using the stock import interface and replays eligible constants into a fresh kernel environment. The executable's default import trust argument and the fresh kernel environment argument are both zero in the bound source. Loading compiled modules still trusts the implementation and its input files. The replay re-adds theorem declarations with their values, and re-adds axioms as axioms. It excludes unsafe and partial constants. It compares constructors and recursors to those generated from checked inductives. Duplicate theorems and the stock software remain part of the trust boundary. The project asserted no new axioms in the four modules supplied here, including the intentionally false source. External human review and institutional or custody independence are unestablished. [Exact stock driver](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/LeanChecker.lean) · [Replay rules](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Lean/Replay.lean) · [Import defaults](https://github.com/leanprover/lean4/blob/5045d0056413266e57c625dcd7c365b10e377c52/src/Lean/Environment.lean)

## Actual selection and failed attempts

An earlier ordinary proof of the whole-input grammar already contained the token-prefix argument. An earlier implementation roadmap named the token as an available component. The first selection for this new work compared 12 routes and chose this exact component before any new proof. It did not register a new mathematical discovery. The concrete declarations, alphabet, length, controls and resource limits were fixed. Candidate and checker shared the stock toolchain, source grammar, model-based authorship and local custody. The finite witnesses were chosen to expose known semantic distinctions. No hidden validation dataset or unrehearsed human review is claimed. [Earlier grammar and its proof](../categorical-count-table-encoding/README.md)

The budget allowed at most eight development launches and stopped on the first complete pass. Five launches used three distinct proof payloads. First, a tactic-alphabet check refused a membership symbol. Second, the frozen model compiled, but the stock checker could not start its matching compiler with the supplied search path. The corrected launch preserved the same source and gave the stock binary directory precedence. Third, the compiler refused deprecated or unused proof constructs with warnings treated as errors. Fourth, the corrected proof and all fresh replays succeeded, and the stock compiler correctly rejected the false proposition. The wrapper expected different English wording and its overall predicate failed. Fifth, the same proof bytes passed a separate predicate that required the exact full stock diagnostic for the false proposition. It specified the file, line, proposition and judgment of falsity. The older failed wrapper outcomes keep their original status. The final pass verifies a visible deterministic predicate. Reuse gives no unexposed selection credit.

The candidate sources, finite facts and native software are not independent across reruns. Independent model readers can check different reasoning or arithmetic while sharing these dependencies. The published proposition and word examples are open to inspection; a source digest or model agreement cannot establish scientific priority. Public applications should use the exact claim boundaries given in the report. [Original open decision](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md)

## Reproduce the checks

From the repository root, run the finite reader. The two Python modes must return the same output. The checker uses the standard library and the existing small-panel exact arithmetic code. It works with the four native output words included here and the six earlier complete input and output pairs.

```text
python3 -I -S -B audit/research/categorical-state-token/finite.py --self-test
python3 -I -S -B -O audit/research/categorical-state-token/finite.py --self-test
```

Pass a genuine unpacked stock Lean 4.34.1 directory to the native proof replay. Use a new evidence directory if you retain the source, objects and separate standard-output and standard-error streams. The caller verifies the version, source revision, proof and observer source digests, actual printed terms, actual axiom sets, the negative control's exact stock diagnostic, and all 256 individual alphabet decisions. It invokes the stock compiler with one thread and strict warnings, then fresh-replays each successfully compiled module. A missing compiler, changed source, timeout or incomplete independent checker produces failure. Hardware-specific binary hashes are reported on each replay. Source checks on another distribution cannot certify its provenance.

```text
python3 -I -S -B audit/research/categorical-state-token/replay.py --self-test --toolchain lean-4.34.1 --evidence new-proof-run
```

For the standalone report, use Pandoc, LuaLaTeX and the repository-local styles and fonts. Source diagram and PDF use the same text and drawing coordinates. Regenerate in temporary output locations and compare SHA-256 with the publication you used.

```text
python3 -I -S -B audit/research/categorical-state-token/figures/diagram.py --output diagram.pdf
python3 -I -S -B audit/research/categorical-state-token/build.py --output report.pdf
```

## Complete-byte evidence

The full native producer SHA-256 was `0c7ed490c6478d671fb7ba1f65f59fa0b9edddee25ead4d9e71fd41402a427f3`. The historical 36-member source frame SHA-256 was `7ad9710e1dc3d308644365e742b34af1858eae82e903c279ad51903255083c85`. The original composed observer checked the source members, producer identity, canonical binding, resources, every exact product and every interval in ordinary and optimized Python. The six earlier positive inputs already had fixed records. For the four newly constructed witnesses, the input expectations were written and frozen locally before production. No external authority or independent source acquisition was supplied for them. Their positive observations exercise the established paired-format semantics. The complete original claim requires further evidence. [Original obligations](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/obligations.md) · [Exact observed input and output identities](observations.json)

The public finite reader reconstructs the original product correction from 4/1 to 3/1, exercises the exact numerical rejection, and recomputes the accepted wider interval for the same input. It checks the literal four input examples, all 108 products in each against the existing arithmetic reader, the named categorical relations, and the nine hostile B inputs in its own parser. Its error messages differ from the historical whole-format observer. The result record preserves the historical native and independent diagnoses. The ten tables are descriptive, deterministic tests. The code does not regenerate a native release, establish binary64 behavior, verify every admitted input or estimate a population distribution.
