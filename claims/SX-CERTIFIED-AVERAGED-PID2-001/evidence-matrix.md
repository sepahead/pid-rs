# Evidence matrix for SX-CERTIFIED-AVERAGED-PID2-001

## Evidence rule

Each evidence class supports only its stated layer:

- a primary source establishes method provenance;
- exact algebra supports the frozen mathematical specification;
- an independent executable route supports per-input reconstruction and containment;
- exhaustive finite tests support only their enumerated domain;
- mutation tests establish sensitivity only to registered faults;
- hashes detect drift from named bytes but do not establish authorship, authenticity, or custody.

## Claim-to-evidence matrix

| Statement | Origin | Retained evidence | Evidence status | Remaining boundary |
|---|---|---|---|---|
| The source-disjunction event and informative/misinformative SxPID construction are paper-defined. | Makkeh et al. | Primary-source pin in [bindings.md](bindings.md) | Provenance mapped | Independent bibliographic-to-code refinement |
| The exact table is one canonical empirical law with positive integer counts. | Project schema | `src/schema.rs`, verifier `validate_input`, strict parser tests | Executably checked for accepted bytes | Input authenticity and scientific meaning |
| Keyed event masses have positive denominators. | Exact finite-set argument | Keyed-row inclusion proof and exact runtime inequalities | Closed analytically and replayed | Implementation/runtime correctness |
| The four-node order and redundancy mask encode the intended two-source lattice. | Paper semantics plus project encoding | `src/lattice2.rs`, independent constants, XOR union-vs-joint counterexample | Analytically identified and mutation challenged | No machine-checked paper-to-code theorem |
| $M$ and $Z$ are inverse and reconstruct all component coordinates. | Exact integer algebra | Two independent matrix implementations and reconstruction checks | Exact arithmetic self-consistency replay | Correct semantic labels remain a premise; zeta reconstruction is a consequence of $ZM=I_4$ |
| All 24 exact expressions are reconstructed independently from input counts. | Project verifier | Python exact-integer/Fraction path; equality against certificate identities and terms | Per-input exact replay | Verifier source/runtime trusted |
| Each independently derived log interval contains the exact rational logarithm. | Exact analysis | Range reduction, positive atanh series, explicit tail bound, outward integer fixed point | Closed analytically, not kernel checked | Correct implementation and Python semantics |
| The fixed-point logarithm enclosure contains a separately evaluated exact-rational series-and-tail enclosure on the qualification grid. | Project qualification | 325 reduced rational arguments at 64, 128, and 256 bits; 975 containments | Qualified bounded | Arguments or precisions outside the grid and common proof mistakes |
| Every accepted producer interval contains the corresponding independently reconstructed value. | Project assurance theorem | Independent interval subset check for all 24 coordinates | Conditionally supported | Verifier implementation is not formally verified |
| Interval width is at most $2^{-160}$. | Project policy | Exact dyadic width recomputation | Per-input exact replay | Does not imply statistical precision |
| The verifier does not accept Python booleans as integers. | Project parser hardening | Numeric-evidence and lattice boolean substitutions | Registered mutations rejected | Other language coercions or parser faults |
| Incremental term growth respects the 1638 cumulative-term ceiling. | Project resource contract | Exact 410-row witness reconstructing 1640 terms | Negative control rejected | Other resource-amplification shapes |
| A low Python integer-text limit cannot silently truncate/reject producer-valid counts inconsistently. | Project environment guard | Limit set to 640 with a 1000-digit count; verifier requires unlimited or at least 4096 | Negative control rejected | Other runtime-policy changes |
| Malformed Unicode cannot enter a canonical token through JSON escaping. | Project schema guard | Lone-surrogate negative control | Rejected | Correctness of Python JSON implementation |
| Small binary empirical laws have exhaustive independently varied route agreement. | Project qualification | 494 tables; 11,856 coordinates; 1,482 direct-MI identities; 5,928 cumulative expressions checked by direct row scans | Complete only for binary $N\le4$ | Larger counts, alphabets, widths, and term patterns |
| Live producer certificates satisfy independent containment. | Project qualification | Singleton, XOR, asymmetric sparse table; 72 containments | Qualified bounded | Not a universal proof |
| Named certificate forgeries fail closed even after payload resealing. | Project mutation suite | 20 resealed field/semantic mutations plus one changed-input reuse | 21 named semantic mutations rejected | Unknown or equivalent faults |
| A one-sided fixed-point logarithm source regression fails closed. | Project source-mutation suite | Subtract 70 fixed-point units from the $\ln 2$ upper endpoint | One retained source mutation rejected by the exact-rational enclosure grid | Other source faults |
| Event-extraction source substitution fails closed. | Project source-mutation suite | Replace target-restricted inclusion--exclusion with a `max` shortcut | Direct row-scan qualification rejects the retained mutant | Other shared specification faults |
| Cross-artifact substitutions fail closed. | Project binding suite | Post-import verifier-source drift, rehashed Rug version change, Cargo `[patch]` substitution, and locked-checksum substitution | Four binding adversaries rejected for their intended reasons | Other loader, ambient Cargo configuration, build, and custody faults |
| Named Rust policy regressions fail closed. | Project static-policy suite | 34 representative source mutations | 34 named mutations rejected | Static policy is not semantic program verification |
| Source-manifest and lockfile bytes are bound. | Project evidence envelope | Length-delimited manifest, `Cargo.lock` digest, stable bounded reads | Drift detection for named local bytes | Executable/native archive identity and external custody |
| The producer's MPFR interval is correct without independent verification. | Conditional producer theorem | Directed-wrapper argument and Rust tests | Conditional only | Rug/MPFR/GMP/toolchain correctness |
| The independent verifier is formally correct. | No closed claim | No kernel-checked refinement proof | Open | F1 |
| The work was independently executed or reviewed. | No closed claim | None | External/open | H1 |
| `pid-core` binary64 output is enclosed. | Separate claim | None | Out of scope | Rust refinement and binary64 error |
| The interval is a statistical confidence interval. | No claim | None | Explicitly excluded | Statistical model and calibration |
| The result has downstream decision validity. | No claim | None | Explicitly excluded | Consumer-specific qualification |

## Replay evidence recorded on 2026-07-24

The following commands completed successfully in the local worktree:

```text
CARGO_TARGET_DIR=target/certified-sxpid cargo test --locked \
  --manifest-path audit/tools/certified-sxpid/Cargo.toml

python3 audit/tools/certified-sxpid/scripts/check-static-policy.py
python3 audit/tools/certified-sxpid/scripts/check-static-policy-self-test.py
python3 audit/tools/certified-sxpid/scripts/check-independent-verifier.py
python3 -O audit/tools/certified-sxpid/scripts/check-independent-verifier.py

python3 -m py_compile \
  audit/tools/certified-sxpid/scripts/verify_certificate.py \
  audit/tools/certified-sxpid/scripts/check-independent-verifier.py

just formal-certified-sxpid2-assurance-pdf
scripts/check-certified-sxpid2-assurance-pdf.sh --cross-toolchain
```

Observed results:

- 34 Rust tests passed: 28 library, 4 CLI contract, 1 exhaustive oracle, and 1 resource
  adversary; no test failed;
- the static policy passed;
- all 34 registered static-policy mutations were killed;
- the independent verifier reconstructed 11,856 coordinates, 1,482 direct-MI identities, and
  5,928 direct row-scan event-expression identities over 494 exhaustive tables;
- it proved 72 live-certificate containments; and
- it checked 975 exact-`Fraction` logarithm enclosures;
- it killed all 21 registered semantic mutations, the retained fixed-point source mutation, and
  the retained event-extraction source mutation;
- four cross-artifact binding adversaries failed for their intended reasons;
- six structural adversaries failed for their intended reasons;
- two transport/invocation controls passed; and
- verifier CLI output was byte-identical across the two retained `PYTHONHASHSEED` values.

These are local observations, not an independently signed evidence record.

## Evidence artifacts

- `audit/tools/certified-sxpid/README.md`
- `audit/tools/certified-sxpid/src/schema.rs`
- `audit/tools/certified-sxpid/src/extract.rs`
- `audit/tools/certified-sxpid/src/lattice2.rs`
- `audit/tools/certified-sxpid/src/exact.rs`
- `audit/tools/certified-sxpid/src/directed.rs`
- `audit/tools/certified-sxpid/src/report.rs`
- `audit/tools/certified-sxpid/src/digest.rs`
- `audit/tools/certified-sxpid/src/resource.rs`
- `audit/tools/certified-sxpid/tests/exhaustive_oracle.rs`
- `audit/tools/certified-sxpid/tests/resource_adversary.rs`
- `audit/tools/certified-sxpid/scripts/verify_certificate.py`
- `audit/tools/certified-sxpid/scripts/check-independent-verifier.py`
- `audit/tools/certified-sxpid/scripts/check-static-policy.py`
- `audit/tools/certified-sxpid/scripts/check-static-policy-self-test.py`
- `audit/formal/latex/certified-sxpid2-executable-assurance.tex`
- `output/pdf/certified-sxpid2-executable-assurance.pdf`
