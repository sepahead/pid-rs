# KSG revision-4 public-CI corrective phase

- Date: 2026-07-28
- Corrective anchor: `dc7b8de0a87443ef2bcde71b19938642f1af2197`
- Corrective-anchor tree: `88b24c0ba4fcad4bd749b9146486143397b6a6eb`
- Observed Actions run: `30305288762`

## Scope and authority

The public run exposed four distinct failures: one fail-closed CPython 3.11 verifier false
rejection, one checkout-metadata phase failure, one missing formal-PDF tool, and one
package-archive compilation failure. Final local replay exposed one additional same-phase
evidence-custody defect: ordinary exact-product boundary qualification overwrote its historical
execution receipt after a source-manifest-changing rebuild. This record authorizes only their
bounded corrections, the revision-3 verifier re-adjudication required by the first failure, and
the catalog, identity, publication, documentation, phase-policy, checker, and self-test
projections needed to make those corrections honest and reproducible.

The manually reviewed phase policy is anchored to the exact commit and tree above. It contains
45 sorted added/modified paths in eleven review classes, permits no deletion or mechanical
resealing, and excludes later PID2 represented-sum, PID3, I_min boundary, frontier, Python
binding, estimator, and release work. The complete anchor-relative delta is pinned as one
projection; review-selected full blobs are also pinned individually. The two phase-checker
scripts retain an explicit self-reference cut and require independently pre-pinned staged-tree
and checkpoint custody before credit.

This correction changes no KSG harmonic identity, local-term formula, summation order,
estimator result, unit, support contract, PID event/lattice/exact-product algorithm, or
producer certificate. It does change the independent verifier's project-defined
loaded-execution measurement and therefore receives a new verification schema and an immutable
revision-3 claim packet. It is not a new SxPID theorem or a stronger mathematical claim.

## Observed failures and exact corrections

### CPython 3.11 loaded-execution false rejection

Job `90107923447` used CPython 3.11.15 and stopped in the normal-mode independent-verifier
qualification with:

```text
pid_certified_sxpid_independent_verifier.VerificationError:
independent verifier loaded execution changed after module initialization
```

The guard failed closed before crediting an accepted certificate. The observed source hashes,
retrieved log digest, diagnosis, trust boundary, and public run/job links are retained in
[`certified-sxpid2-cpython311-loaded-execution-incident-20260728.md`](certified-sxpid2-cpython311-loaded-execution-incident-20260728.md).
The failure was a nonsemantic lazy string-intern cache transition in CPython's marshal
representation, not a counterexample to the paper-defined categorical SxPID functional or the
exact count/product mathematics.

The candidate recursively primes the qualified strings and nested code constants before the
loaded-execution serialization, retains both source-byte and post-execution integrity checks,
changes the loaded-execution domain from v1 to v3, and changes only the
independent-verification schema from v2 to v3. The final reviewed source hashes are:

| Artifact | SHA-256 |
|---|---|
| `audit/tools/certified-sxpid/scripts/verify_certificate.py` | `c90572571eac9b5cd5cd11d526a211dd0dfa7ab45274f6c038c0f8338cd2958e` |
| `audit/tools/certified-sxpid/scripts/check-independent-verifier.py` | `4327afdcce04421544481e0af9abf15dd3709ea75c5df994cb33b3ce3de91c17` |

Four local replays—CPython 3.11 and 3.14, each in normal and optimized mode—reported the
unchanged 11,856 coordinates, 1,482 direct-MI identities, 5,928 direct-event identities, 72 live
containments, 975 exact-Fraction logarithm enclosures, 23 semantic mutations, one fixed-point
source mutation, one event-extraction source mutation, four cross-artifact adversaries, six
structural adversaries, and two transport/invocation controls. Each also passed two distinct
loaded-execution cache/integrity controls and rejected post-import mutation of each of the exact
51 declared semantic/configuration globals. The affected CPython 3.11 route killed one isolated
normalization-removal source mutant; the explicitly version-conditioned lane reported zero on
3.14. A separate exhaustive typed-encoding audit replaced all 263 currently reachable nested
values and dictionary keys per interpreter; every replacement changed the digest and restoration
recovered.

The claim checker binds schema v3, source hashes, counts, immutable revision separation, the exact
reviewed certified-method and evidence projections, complete historical/v3 authority bytes,
workflow/Just containers, static-policy and PDF leaf gates, assurance sources/PDFs, and prohibited
claims. Its hostile suite has 111 registered mutations, including raw CRLF drift,
Markdown/HTML/entity equivalences, dead enclosing commands, historical rewrites, contradictory
machine evidence, and early-exit leaf gates. These are bounded same-worktree results, not Python
verification, a portable semantic hash, an independent execution, or a green public rerun.

### Actions checkout worktree residue

Job `90107923456` stopped before arithmetic replay because
`actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0` left
`.git/config.worktree`. The observed path was an 83-byte regular file with SHA-256
`443a5f645c23c3d0c0aa09f634b2ad111d46ef61946b598a2fb311678ab47454`
and these exact inert sparse-checkout bytes:

```text
[core]
	sparseCheckout = false
	sparseCheckoutCone = false
[index]
	sparse = false
```

Checkout had already removed its temporary credential configuration because
`persist-credentials` was false. The workflow now permits only two initial states: absence, or
one single-link regular non-symlink file with exactly that digest. In the latter state it unlinks
that one literal path and then verifies absence. Wrong bytes, a directory, symlink, hard link, or
surviving path fails closed. No general Git configuration key is unset or rewritten.

### Formal-PDF toolchain

Job `90107923578` built and structurally checked the first formal paper, then stopped with
`missing command: lacheck` while starting the dependency-colored SxPID paper. The workflow adds
only the Ubuntu `lacheck` package. It does not weaken a TeX/PDF checker, expected digest,
cross-toolchain comparison, warning policy, or visual-review obligation.

### cargo-deny 0.20.2 option position

The certified-SxPID job stopped before reaching cargo-deny, so this was a latent workflow defect
rather than an observed terminal failure. The workflow pins cargo-deny 0.20.2; its common
options belong before the subcommand. The exact corrected command is:

```text
cargo deny --manifest-path audit/tools/certified-sxpid/Cargo.toml --config audit/tools/certified-sxpid/deny.toml check
```

The manifest and deny-policy paths are unchanged. The phase checker reconstructs the candidate
workflow from the dc7 blob with exactly the checkout-residue, `lacheck`, and cargo-deny edits; a
fourth edit is rejected.

A retained local negative control used the pre-existing cargo-deny 0.19.9 executable. That version
rejected the corrected command because it still treats `--config` as a `check`-subcommand option.
An isolated installation of the workflow-pinned cargo-deny 0.20.2 accepted the exact corrected
command and reported all four policy families `ok`; the inverse 0.19.9 ordering was rejected by
0.20.2. This is version-specific CLI evidence, not a dependency-policy theorem. Local reproduction
must therefore use the pinned 0.20.2 executable rather than silently interpreting a failure from a
different cargo-deny grammar.

### Retained local toolchain-routing and publication negatives

Two local failures were executable-selection confounds rather than failed scientific gates. First,
`/opt/homebrew/bin/cargo` received `+1.89` literally and rejected it; putting the rustup shim
directory first in `PATH` selected the pinned Rust 1.89 toolchain and the same suite passed. Second,
an `elan` proxy attempted a first-time Lean 4.32 download during the nine-PDF replay and exceeded
the bounded wait. The partial download was interrupted without deleting it. Replaying with the
already present official Lean 4.32.0 runtime (commit
`8c9756b28d64dab099da31a4c09229a9e6a2ef35`, Lake 5.0.0) under the isolated
authority-review worktree removed the network
dependency. Neither event is evidence against Rust, Lean, a theorem, or a PDF; both show why
toolchain provenance and executable routing must be recorded separately from a gate result.

The version gate also rejected legacy `\(...\)` inline math and a blockquoted display delimiter in
the new revision-3 Markdown claim. The source was converted to GitHub-supported dollar delimiters,
then the Markdown-math checker and all 17 of its hostile mutations passed. This was a publication
rendering defect, not a change to the theorem or claim content.

### Historical SxPID2 boundary-receipt overwrite

A later local replay exposed a third custody defect. The former
`check-nonsyntactic-zero-boundary.py` always overwrote its tracked JSON receipt. The historical
certifier had digest
`0486ab6603b0906cc3022faebaa56ff5f69dbb2bbf7f3a406d628ceee828ab4a`
and emitted certificate
`a9aa6171a7516ac03f93f647b09471d987331da37859e8e6b6561ee0a27fd082`;
the current build had digest
`53f836053ec65549951dc67df0423b8802a67d5bff80247126fab7e28687ba71`
and emitted certificate
`5af24512fd5ae7573636f42ce57f5350aa0e874d76a84bec50b35d1b03a7548f`.
The ordinary command therefore changed tracked bytes and the exact claim projection failed even
though all 12,869 tables, 308,856 coordinates, 16 minimal boundary cases, and the retained witness
were unchanged.

The old and current same-host certificates differed only at
`payload/tool_binding/runtime_source_manifest_sha256` and the resulting outer `payload_sha256`.
Ordinary replay is now read-only. It verifies the complete live certificate, compares the bounded
result under a declared projection, emits the full live receipt to standard output, and leaves the
historical receipt unchanged. The outer evidence projection excludes exactly the executable and
full-certificate digest bindings. A stable certificate replay digest first validates the complete
payload digest plus exact outer, tool-binding, and build-context inventories, then removes only:

1. runtime source-manifest digest;
2. Rust verbose version;
3. build host; and
4. build target.

Every other payload field remains bound, including lockfile, encoding, profile, native-cache
policy, distribution status, arithmetic, coordinates, and claim boundary. Fifty-one controls
independently bind the exact exclusion/inclusion inventories, vary every declared dynamic and
stable class, and reject malformed, missing, extra, and digest-inconsistent inputs. An explicit
`--update-evidence` flag is required for a reviewed custody transition. Both binaries yielded the
same narrowed replay digest,
`11641347ef83ef7262b54d8be4b112dfef38bd61af22dfa9f89e4930d2b9beba`.
Beyond those targeted controls, a complete recorded-schema sweep mutates all 1,236 scalar leaves
one at a time. The outer receipt partitions into 274 changed and exactly two declared invariant
leaves; the certificate payload partitions into 956 changed and exactly four declared invariant
leaves. This closes hidden scalar-leaf omissions for the recorded objects, not structural
transformations, future schemas, parser defects, or hash failure.

No second operating system or architecture was executed in this corrective replay. The design
uses an exact declared variable-field projection; that is not cross-build or cross-platform
validation. It is not source, executable, dependency, compiler, or portable-semantic identity.
The complete machine-readable process record is
`audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json`.

### Package-archive KSG generator witness

Job `90107923806` built `pid-core` in the workspace, then failed while compiling its unpacked
crate because `stats.rs` used `include_bytes!` on the repository-root generator, which is
intentionally absent from the published crate archive.

The correction adds
`crates/pid-core/tests/fixtures/generate-ksg-local-arithmetic-oracle.py.snapshot` as an exact
11,028-byte copy of the canonical generator. Both have SHA-256
`a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b`.
The test includes the packaged snapshot and retains the canonical repository path as data. In a
workspace checkout it requires exact live-source equality. If the live source is absent, that
state is accepted only when `.cargo_vcs_info.json` is a regular file containing parseable JSON
with one unambiguous `path_in_vcs` string exactly equal to `crates/pid-core`; a typed
deserialization control rejects duplicate bindings. This forgeable marker is package-layout
context, not evidence that Cargo produced the file and not archive authenticity or provenance.

The complete corrected `stats.rs` bytes are pinned at SHA-256
`204080f7a8854cc390754907e56aff31321853bf350542ea9c8b570038920a8e`.
The archive verifier is separately pinned at SHA-256
`13bf728a06c5a22289a5cdd0ba2a229440d584108918b256898a4fac4252f256`.
It first proves the repository generator path is absent from the extracted archive, compiles all
archived targets and features in an isolated target directory, and then executes only
`stats::tests::packaged_ksg_generator_snapshot_matches_workspace_source_when_available` with an
exact libtest filter and deterministic color setting. It requires one `running 1 test` line, the
named test's `ok` line, and one one-pass summary; a compile-only or zero-test result cannot satisfy
the receipt.
The canonical generator, arithmetic fixture, production summation path, KSG units, and numerical
constants are unchanged.

#### Retained package-harness negative result

A hostile local package experiment initially appeared to accept a mutated extracted crate when
the original and mutant had the same package name/version and shared one `CARGO_TARGET_DIR`.
Cargo reused the already compiled test artifact. This was a harness-cache confound, not evidence
that the mutation was semantically accepted. Repeating each candidate with an isolated target
directory killed the wrong-marker and snapshot mutations. Package mutation claims must therefore
use isolated target directories or an equivalently proved clean build boundary; a shared target
directory is not admissible evidence here.

The first exact clean-checkpoint archive run then exposed a different harness false negative:
the intended Rust test ran and passed exactly once, but the shell receipt parser rejected Cargo's
valid one-pass summary. In a single-quoted extended regular expression, the script had written
two backslashes before the literal period after `ok`; `grep -E` therefore required a backslash in
the Cargo output. The corrected parser uses exactly one backslash. The phase checker now binds
the complete summary-parser pattern, and a dedicated hostile mutation restores the invalid
two-backslash form after rebasing the package-script hash. This incident concerns receipt
parsing—not the passing Rust test, package contents, or KSG arithmetic—and is retained because a
static token inventory alone did not execute the parser semantics.

### Cross-gate catalog isolation

The first settled `just ksg-revision` replay passed both oracle generations, both exact-enclosure
routes and their 29-mutation suites, both modular-certificate routes, both 28-mutation modular
suites, and both scoped claim checks. It then stopped in the normal claim self-test because the
unscoped KSG checker reached this earlier diagnostic:

```text
KSG harmonic-revision check failed: a non-KSG catalog method changed from the KSG milestone parent
```

The self-test required the exact intentional preclosure diagnostic instead. The cause was not KSG
arithmetic drift: revision-3 verifier registration had necessarily changed the protected
`validation.certified-sxpid2-reference` catalog object. Treating the whole 49-method protected
projection as unchanged made the independently required SxPID2 correction and the KSG phase gate
incompatible.

The correction does not wholesale rebaseline protected methods. It partitions the 49 non-KSG
methods into the exact reviewed SxPID2 method and the other 48 methods, then independently binds
all three relevant projections:

| Projection | SHA-256 |
|---|---|
| dc7 full 49-method parent projection, retained as the comparison origin | `7dcad03d4b018243c020765a61d7ac2d5a7117d0b3b098ce650fd4c6251fb48d` |
| unchanged 48-method projection | `217e752f530ab1b2875b4ff95ee3e96f3424b0b3ed6a65f6983c7d8d7bca7c47` |
| exact current `validation.certified-sxpid2-reference` object | `e9c8af473fe7ed7d14e9621c1c88f5dd5012783db8d95a8ed5bd7a0d5207a229` |
| reviewed current 49-method composition | `174cfb1c351357f180837eefe4ae935172c769cd6ec18f5d5202786bf64efe55` |

The checker rejects a change in either partition with a distinct diagnostic and also rejects a
change in their full composition. The self-test now attacks an unaffected protected method and
the reviewed cross-lane method separately, requiring the exact intended diagnostic in normal and
optimized modes. Both full replays rejected 176 mutations
(`checker-model=16`, `fixture-custody=2`, `fixture-semantics=12`,
`textual-source=35`, `release=74`, `catalog=37`) and passed two scope-isolation preflights.
Both claim-only replays independently rejected 141 packet mutations. The unscoped checker again
stops only at the exact 13-open-gate `integration_no_go` lifecycle boundary. No KSG status,
formula, fixture, source, release, binary64, enclosure, modular, Lean, or Z3 constant changed.

### Cross-authority ecosystem binding

The first complete `just version-check` replay passed release-state, software-identity, and
method-catalog validation plus their mutation suites, then stopped at the ecosystem capability
checker:

```text
ecosystem capability check failed: method-catalog: stale SHA-256;
expected 154ce65f1b9da2d72dfcbdc3649281c2ad3cce719ba57dae281a29aff71da652,
observed 1d1f1765209062b8fdc31faed1870de960c53f50ac8d3925a8ac27198aeab313
```

That message is retained exactly as observed at that replay. At that point
`154ce65f1b9da2d72dfcbdc3649281c2ad3cce719ba57dae281a29aff71da652`
identified the then-current `method-catalog.json`; the older
`1d1f1765209062b8fdc31faed1870de960c53f50ac8d3925a8ac27198aeab313`
remained in both the ecosystem JSON binding and the checker's reviewed-current constant, and the
generated Markdown repeated it. Thus each local artifact was internally well formed, but their
cross-authority custody edge was stale.

Subsequent hostile verifier review changed only the bounded certified-SxPID2 method object and
settled the final catalog bytes at
`637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f`.

The final correction changes only that current catalog binding in
`ecosystem-capabilities.json`, its exact human rendering in `ECOSYSTEM_CAPABILITIES.md`, and the
matching reviewed-current constant in `scripts/check-ecosystem-capabilities.py`. The historical
base semantic projection remains
`63a843b4fbd36c43534ab8fa6dd9da2174c673862b13368c3dd6eed4fc2c5280`,
the consumer-inventory projection remains
`ccc5ba5ad414a9c923f56619a3acb09ebc1f5e18ee014ce8f02e152ae24d3d40`,
and every consumer statement, evidence record, release claim, other source binding, method
entry, and assurance family is unchanged. The corrected checker validates four consumers and
its hostile suite rejects all 76 registered mutations. This repair refreshes provenance; it
does not establish downstream compatibility or integration.

## Settled non-phase bytes and replay ledger

The following receipts were regenerated after the scientific, verifier, documentation, and PDF
writers stopped. The phase checker and its self-test remain outside their own stored hash
projection and are closed separately by the staged-tree and checkpoint hooks.

| Artifact or projection | SHA-256 |
|---|---|
| boundary-replay process record, raw bytes | `f9f0156abd4370857099f215a313b95621510d591e5726d52c856670324eb8d3` |
| boundary-replay process record, canonical projection | `9887b0deff4deeec915e363c77741e12973af49473f8a74ae98fbdd1afe4731c` |
| exact-product mutation receipt, raw bytes | `031a449c4239d74d0584c5f244ca18c852555d442ae7a880c2d750a02d5bcb0a` |
| exact-product mutation receipt, canonical projection | `9922fb473f6bd52768e6f8120d0994e0903d7efe1e848c627650fd56a2c87de7` |
| retained boundary receipt, raw bytes | `c36da6d5c55d553a6a647818cf15e6143a7914409370b096e6f6492f5731131d` |
| retained boundary receipt, canonical projection | `dfa276a129d0d82b739e3037488468fa921d5981b18c503a9cddef2a19511fbc` |
| certified executable-assurance PDF | `2370637b750578fc1818279f6001f4143dd8e1e3d48136077a6953ceb2ee795c` |
| exact log-product assurance PDF | `aa3217998c442cfafa2dea16f9a31caa952cfe503c0d32e36e853b77a86953aa` |
| formal-tool adoption PDF | `e7d4fa04700b9cbe8d9a4701525341f1743a4a28e624c31a2e8726b69fc9147c` |
| certified-SxPID2 claim checker | `0496e497ff168dc293e8817f60c3fb690726e37ebc9dc1ac084431740d9694ad` |
| certified-SxPID2 claim self-test | `cac22cb1af20e8b020d67ec1124515179db4cc93ddc4885d43d83a49dd46a24f` |
| method catalog, exact canonical file bytes | `637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f` |
| 45-path phase policy, exact canonical file bytes | `297b4cb3fc60422796d64b2b5a23763d5c9d46f09ad3abe049e5a01c1330d5b2` |

The four-way final boundary replay used CPython 3.11.15 and 3.14.6 in normal and optimized
modes. Every run emitted identical full receipt bytes with SHA-256
`42b8d589c37d9b304fbeba4f6fe0a5f88812969aae9fa24ca958ff558ceed048`,
certifier executable
`a59ca9db150feb08c3d298561b35d90a6971d4d96bc6e48364801525a9b25bab`,
live certificate
`fa738993381e457946c23c267ecd93386cbd08ba136f5fa576503683f1db8a83`,
and replay projection
`11641347ef83ef7262b54d8be4b112dfef38bd61af22dfa9f89e4930d2b9beba`.
The tracked historical receipt remained exactly `c36da6d5…`. These are same-host replay facts,
not cross-platform or cross-build validation.

Both interpreter versions, in both modes, passed the claim checker and rejected exactly 111
claim-custody mutations. The lower exact-product suite produced byte-identical receipts across
the four interpreter/mode runs, rejecting 23 product adversaries and passing two preflight
sentinels, 51 targeted projection controls, and the exhaustive 1,236-leaf sensitivity
partition. The KSG checker passed every scoped route; its full and claim-only hostile suites
rejected 176 and 141 mutations, respectively, in normal and optimized modes. The unscoped route
failed only at its required `integration_no_go` state with 13 open integration gates.

All nine declared formal papers passed same-toolchain exact reproduction and cross-toolchain
structural equivalence. The three changed PDFs comprise 62 A4 pages; every page was rendered and
visually inspected. That inspection caused one substantive correction: unexecuted
“platform-tolerant” wording was replaced with the narrower declared variable-field projection
contract. The resulting exact-product PDF was rebuilt, re-pinned, and re-inspected.

The 45 phase-policy paths partition as: three catalog/identity, fourteen claim-adjudication,
three corrective-evidence, five cross-gate isolation, three documentation/release, three
package-archive, one phase-authority, eight publication-evidence, two verification-tool, one
verification-wiring, and two verifier-runtime paths.

## Failure-diverse review

1. **Object, domain, range, and quantifier.** The KSG change is test/package provenance only. The
   verifier change concerns a project-defined CPython live-code digest only. Neither is promoted
   to a population PID, statistical, estimator, binary, or universal runtime statement.
2. **Exact derivation and counterexample.** The package snapshot equals the reviewed generator
   byte-for-byte. Checkout accepts only absence or one exact inert file. The original CPython
   transition is retained, a real post-import code mutation must still fail, and removing
   normalization on the affected runtime must reproduce the intended rejection.
3. **Formal and mutation adequacy.** The seven earlier Lean SxPID theorems and KSG formal packets
   are unchanged and explicitly do not verify CPython. The verifier, claim, phase, policy,
   workflow, package, Git-context, and source mutants provide failure-diverse negative controls
   without being mislabeled as complete program proofs.
4. **Runtime and compiled dataflow.** Normal and optimized CPython 3.11/3.14 routes are distinct;
   the package archive compiles without a repository-root include; workspace parity remains
   checked; release/debug, serial/parallel, and platform claims still require their own gates.
5. **Provenance, custody, and self-reference.** The dc7 commit/tree, exact 45-path policy, policy
   digest, complete-delta projection, selected full-blob hashes, staged tree, single-parent
   checkpoint, source hashes, public failure identifiers, and retained self-reference cut are
   separate evidence layers. None proves authenticity or independent authorship.
6. **Catalog, novelty, and downstream.** The machine catalog, generated human rendering,
   software-identity digest, revision-3 packet, papers, and PDFs describe the same narrow
   verifier correction. The cross-gate checker admits exactly that one protected catalog object
   and independently pins the other 48. The ecosystem contract binds the refreshed catalog bytes
   without changing its consumer semantics or promoting any integration claim. No continuous
   Ehrlich estimator, fitted quantized composition, I_min, PID2 represented-sum, PID3, or
   downstream consumer is covered.
7. **Publication and visual evidence.** Human and TeX sources identify the revised schema,
   controls, affected-runtime lane, and trust boundary. Deterministic structural checks,
   cross-toolchain checks, and page-by-page rendering remain separate from mathematical truth.

An earlier read-only policy-inventory attempt terminated at a service usage limit before producing
a report; no finding or review credit is assigned to it. Subsequent read-only agent audits did
complete. One independently re-derived the KSG harmonic and SxPID algebra. Over the finite integer
domain `2 <= n <= 100`, `1 <= k < n`, and `k <= x,y <= n`, it exhaustively compared 8,670,750
unique full-rectangle KSG tuples; 4,421,175 of those also satisfy the conditional-subdomain
constraint `x+y <= n+k`. It additionally checked 1,013 high-precision rational-log cases without
finding an arithmetic or claim-scope defect. A
second found and reproduced verifier-state omissions,
vacuous cache-control ordering, structured-authority parser bypasses, historical/canonical
projection gaps, and unbound child-command routes; every accepted bypass became a named negative
control. A release audit separately identified the archive-only execution and ecosystem-custody
requirements. These are failure-diverse agent reviews, not independent human source acquisition,
external execution, or custody.

## Disposition before the remote rerun

- Completed on the reviewed candidate bytes: the four bounded corrections; revision-3 source,
  packet, catalog, identity, paper, PDF, documentation, and phase-authority integration; and the
  retained negative/process controls described above.
- Required before this milestone is credited: final settled-byte replay after all writers stop,
  independent staged-tree custody, small unsigned single-parent commits, fast-forward push to
  `main`, and a fresh complete public CI result.
- External/open even after an ordinary green CI run: independent human source acquisition,
  review, execution, and custody; binary/native-archive attestation; transparency-log or
  authenticity proof; and stronger source-to-runtime formal refinement.
- Not implied: universal KSG or SxPID correctness, formal verification of Python/Rust/Cargo/Git,
  release completion, publication acceptance, downstream integration, or completion of the
  long-horizon PID program.
