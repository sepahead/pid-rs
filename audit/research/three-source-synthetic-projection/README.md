# Testing a finite valuation reduction against four artificial scripts

**Sepehr Mahmoudian, 2026**

Can a small finite calculation reproduce the result of evaluating both assertions for every typed assignment to a script, including its other bit-vector and integer variables? This package tests that question on four artificial scripts. The last script has enough unused definitions to put substantial pressure on a proof checker. A successful finite count is only relevant after a theorem connects it to the exact interpreter output. The status of a particular run is recorded in its terminal receipt. [Package plan](plan.json) · [Mathematical model and public source readers](../three-source-w02/README.md)

## Terms and construction

| Term or symbol | Meaning in this study |
|---|---|
| Script, s | Ordered commands in the supported SMT-LIB fragment, with typed declarations and two assertions. |
| Valuation, v | A function assigning each declaration a value of its specified type. A bit vector of width w has 2 to the power w possible values. The integer type is unbounded. |
| Evaluation, E(s,v) | The project-defined interpreter either fails or returns the ordered list of assertion truth values. |
| Projection, p | A function from full valuations to a smaller set of possible inputs. |
| Extension, e | A function assigning a full valuation to each projected input. |
| Finite observation, o | A function from a projected input to the same optional ordered result type as the interpreter. |
| Fresh replay | The stock Lean checker reloads the named compiled module and replays its loaded constant map into an empty kernel environment. |

For every projected input a and every full valuation v, the proof requires

    p(e(a)) = a
    E(s,v)  = E(s,e(p(v)))
    E(s,e(a)) = o(a).

The last two equalities yield E(s,v) = o(p(v)). A successful refutation returns exactly two Boolean values, at least one false. If this holds for every projected input, no full valuation returns two true values. The source separately requires that a full typed valuation exists and that the static syntax check succeeds. All comparisons here are discrete. The data consist entirely of artificial command lists. [Proof interface](lean/ProjectionCore.lean) · [Symbolic term-fold equality](lean/ProjectionReification.lean) · [Frozen stock semantics](../three-source-w02/lean/W02Semantics.lean)

| Artificial input | Tested proposition |
|---|---|
| Unary | A selected seven-bit variable can change the first assertion. The second asserts its negation. For selected values 1 and 0 the output switches between true/false and false/true. The theorem includes every value of an unused integer and a same-width spare. |
| Pair | The first assertion compares bit 1 of two four-bit inputs. Changing either coordinate of (0,0) to 2 changes the result. The finite set contains 256 ordered pairs. |
| Sat | Both assertions test the same predicate. Setting the chosen coordinate to 1 gives a full satisfying witness. |
| Scale | The same selected bit controls both assertions as in Unary. The raw script is 44,089 bytes and has 89 commands, including 25 declarations and 57 definitions. Fifty-six definitions share a large body. |

The two public readers independently preserve the token spans and recover the same typed command tree from each exact byte stream. A third reader checks the generated Lean constructor syntax. The source-only procedure checks every emitted module against its published digest. It loads five source files from the adjacent W02 package. All mathematical inputs in the native manifest are artificial. [Fixture identities](fixtures.json) · [Generated module identities](generated.json)

## Qualification stages

The stock compiler first checks the unary and pair proofs, the satisfiable witness, their consumers and their supporting declarations. The plan requires two fresh replays before it asks the compiler to reject four incorrect declarations. Each rejection must have exit status 1, no object, an empty error stream, and exactly one ordinary compiler diagnostic in its JSON output. The source file, line, diagnostic class and mathematical tokens are bound separately for each case. They cover the wrong same-width coordinate, a fixed truth vector, a refutation transferred to a satisfiable input, and interpreting failure as a successful refutation. An independent source then observes the complete kernel type and proof expressions for 62 named results and compares their transitive axioms with the separate stock reports. The term observer and these typechecked consumers share the stock compiler and source semantics. [Native criteria](plan.json) · [Small theorem roster](small-targets.json) · [Explicit consumer types](lean/ConsumerSynthetic.lean)

The large test retains the **same byte stream and literal script** used in the earlier failed proof. Its four stages have separate receipts.

1. The prefix module proves that the exact interpreter selects the specified 85 active commands from the 89-command script. It shares one typed syntax tree between the 56 matching bodies. The equality with the expanded original literal is a native proof obligation.
2. Each of the 85 static commands has a named theorem relating its input state to its output state under the unchanged static step. Eleven ordinary compilation commands check groups of at most eight. A final theorem composes those equalities and checks the echo and assertion count. A failure records the exact group.
3. The dynamic proof first uses the established static result. It then requires that the original dynamic command fold agrees with the finite observation at *every* full valuation, including the unbounded integers. Both projection equalities are source-bound.
4. The finite proof reuses the 128-input computation on the same finite observation. A new full-valuation theorem transfers it to Scale, proves both possible assertion vectors on explicit inputs, and supplies four typed consumer declarations. Fresh replay and separate term and axiom observations complete the stage. The scale roster has 107 named theorems, including all 85 static transitions. [Dynamic proof](lean/ScaleDynamic.lean) · [Finite transfer](lean/ScaleFinite.lean) · [Large-case consumer](lean/ScaleConsumer.lean) · [Scale theorem roster](scale-targets.json)

## Earlier measurements and open obligations

On stock 4.34.1 for macOS arm64 the first 12 ordinary compiler invocations produced 10 successful modules. An initial attempt to identify a simplified arithmetic expression with the interpreter failed at definitional equality. The successful Unary alternative used the original primitive operations. The successful Unary proof took 0.880 s, the Pair proof 3.992 s and the SAT witness 0.299 s. The large literal module compiled in 1.074 s. The monolithic Scale proof was killed after 632.134 s. Its sampled process group reached 4,294,983,680 bytes and its direct process reached 4,295,032,832 bytes. The observed budget was 4 GiB. A later proposed launch hit the 5,400 s campaign deadline before it started. That attempt produced no fresh replay, separate negative-test or full-term readback results. No original W01, W03 or W15 assertion was evaluated. All twelve process outcomes and the prelaunch stop retain their own identities. [Prior observations](prior-observations.json)

The four artificial scripts and the choice of proof interface were exposed during development. A hosted run adds a distinct execution host. Both implementations of the readers still share the inputs, generated formal object, execution platform and project definitions. No independent human scientific review is recorded. A result here earns only the finite artificial script and proof checks identified in its receipt. A scientific result on any original formula would require its own source mapping, full-valuation proof, isolated case environment and separately bound run.

## Reproduction and evidence

Use the standalone workflow on a standard x86-64 Linux host. It uses the official Lean 4.34.1 release at source revision `5045d0056413266e57c625dcd7c365b10e377c52`. The workflow pins the archive SHA-256 and action revisions. It issues one command at a time. The campaign begins before checkout, with 5,400 s total, 900 s per native command, a 4 GiB observed process-group RSS limit and a 1 GiB limit on retained sources, objects and logs. The large upstream archive and its freshly extracted stock distribution have separate storage. The enclosing job allows 100 minutes for the campaign and final evidence upload. The controller records group samples and a direct child peak, so the observed group measurement has the sampling interval's resolution. [Hosted entry point](../../../.github/workflows/three-source-synthetic-projection.yml)

From a checkout containing this package, the following source check uses small text inputs. The workflow publishes the expected manifest digest for its checkout. In the example, set `EXPECTED` to that value and choose a fresh evidence path.

```sh
PACKAGE=audit/research/three-source-synthetic-projection
python3 -I -S -B "$PACKAGE/run.py" --check-sources \
  --expected-manifest "$EXPECTED" --output "$NEW_SOURCE_REPORT"
```

For the native campaign use a standard hosted Linux runner with Python 3.11 or later, Git, GNU tar, zstd and the pinned official Lean release archive. Both named directories must be new. The driver extracts its own clean provider. The timestamp supplied by the GitHub workflow includes provisioning time. An invocation without that optional timestamp starts its own campaign clock.

```sh
python3 -I -S -B "$PACKAGE/run.py" --native \
  --expected-manifest "$EXPECTED" --commit "$(git rev-parse HEAD)" \
  --archive "$VERIFIED_LEAN_ARCHIVE" --stock-root "$NEW_STOCK_DIRECTORY" \
  --output "$NEW_NATIVE_REPORT"
```

Read `terminal.json` first. For a partial run, `progress.json`, per-command source and output identities, exit status and resource measurements identify what was reached. The full stdout and stderr streams are retained separately. A complete run also produces `four-refusals.json`, `small-observations.json`, `scale-observations.json` and the compiled-object identity roster. Ordinary compilation and full-term observation load compiled imports. Stock fresh replay uses its own saved declaration replay policy, which admits axiom declarations and skips unsafe and partial constants. Named mathematical results must be ordinary theorems. Their closed proof and type expressions and transitive dependencies are checked separately, allowing only `propext`, `Quot.sound` and `Classical.choice` where actually observed. The observer's own metaprogram checks for free variables, metavariables and loose bound variables. [Observer source](../three-source-w02/lean/W02Inspect.lean) · [Readback rules](readback.py)

## Rust implementation and computational cost

This is an offline exact statement about a typed finite-input projection. It has no empirical rows, fitted estimator, resampling step, public Rust API or runtime feature gate. The bounded mathematical enumerations have 128 and 256 inputs. Proving the connection to the full source and rechecking the resulting declarations is a separate compiler workload. The earlier measured times and memory are given above. Each hosted receipt records its own timings and resource limits. A constant truth vector or direct Boolean proof on the finite inputs would be simpler, but the witnessed premise changes and the obligatory equality on every full assignment determine which substitutions are valid.

Cite Sepehr Mahmoudian, *Testing a finite valuation reduction against four artificial scripts* (2026), with the exact repository commit or release and the hosted run identity used. [Software citation](../../../CITATION.cff)
