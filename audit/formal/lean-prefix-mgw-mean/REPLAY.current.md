# Current replay, controls and publication build

The unchanged [adapter](replay-proposed.py), SHA-256 `121068917f2cdc0e3b3098c63869227be9511d7df5f9c011d3d68f980308220a`, and [48-member manifest](replay-proposed-v1.json) have actual local replay acceptance. Their historical filenames and docstrings remain exact. The [current results](../../evidence/prefix-mgw-mean-formal-verification-2026-09-08/RESULTS.md) distinguish four full positive proof replays, one causal wrong-final rejection, inert controls, and publication work.

Every new execution needs a new registration before it starts. Never reuse the closed September 8 clock, its STOP record, accepted receipt, or fixture result as a new run. The adapter requires a canonical repository root, the pinned Lean 4.33.0 toolchain and unchanged dependency checkout/source preflight. A clean source mirror without those exact dependency inputs is insufficient. See [dependencies](DEPENDENCIES.md) for inherited obligations.

For a new proof replay, use the exact [registration schema](REGISTRATION.template.json) with actual UTC start and exactly 120 minutes, observed current tool digests, the accepted manifest digest, and a concrete reviewed controls-adoption receipt. Materialize an execution plan using the schema of the [prior actual plan projection](../../evidence/prefix-mgw-mean-formal-verification-2026-09-08/portable-replay/SUPERVISOR_PLAN.json): replace its logical locators with canonical paths in the new checkout; bind the new registration's actual SHA; keep the unchanged supervisor digest `529245c5f842283132f8fe21a2555968a8f9c29950489f41c2639ace08f7f569`. The plan's ready status requires review of these concrete inputs. The production supervisor itself chooses the selected normal, selected optimized, cosmetic normal, cosmetic optimized and wrong-final sequence.

The command shape, after that registration and review, is:

```text
python3 -I -S -B audit/formal/lean-prefix-mgw-mean/portable-controls/proposed/stage-supervisor.py \
  --plan <fresh-ignored-plan.json> --plan-sha256 <actual-plan-sha256> \
  --output <fresh-ignored-supervisor-output>
```

The adapter stage must be a fresh direct child of the repository's `.local/prefix-mgw-mean-public-replay-v1/`. Its six-attempt/150 compiler-kernel-child/six-version-probe limits are ceilings, not replenishable budgets. The actual accepted sequence used five attempts, 123 compiler/kernel children and five version probes. The wrong-final control must follow an actual selected-source full pass within its own stage and preserve the first two exact records before the final raw/alias type rejection. Receipt parsing, process observation, source-byte checking and final human review have separate roles. The cooperative supervisor provides neither an atomic census/launch boundary nor a hard real-time deadline, sandbox or escaped-descendant guarantee.

For inert controls, the [distribution manifest](portable-controls/DISTRIBUTION.json) binds five unchanged source files and an inert archive of 73 pinned source inputs. The archive keeps exact original bytes and file/directory modes. Packing avoids treating deliberately relocated fixture Markdown as live publication navigation. The [materializer](portable-controls/materialize.py) passed 192 actual causal cases across normal and optimized invocations. The unchanged adapter and supervisor harnesses then passed their actual relocated suites from the exact materialized output. [The publication evidence](../../evidence/prefix-mgw-mean-formal-verification-2026-09-08/publication-current/STATUS.md) identifies those closed runs; a new run still needs its own registration and review.

```text
python3 -I -S -B audit/formal/lean-prefix-mgw-mean/portable-controls/materialize.py \
  --destination <fresh-canonical-directory-under-.local>
```

Register the adapter-control suite for at most 45 minutes with schema `portable-mean-adapter-controls-execution-v1`, status `root-reviewed-source-ready-for-controls`, exact `adapter_sha256`, integer `new_mean_theorems_proved: 0`, actual UTC bounds, and `source_sha256` entries for `adapter-controls.py` and `control-child.py`. Register supervisor controls separately for at most 15 minutes with schema `portable-mean-supervisor-controls-execution-v1`, the same reviewed-source status and integer zero, and exact hashes for `supervisor-controls.py`, `stage-supervisor.py` and `supervisor-child.py`. Use the [actual original schemas and results](../../evidence/prefix-mgw-mean-formal-verification-2026-09-08/controls/adapter-controls-current/EXECUTION_REGISTRATION.json) as retained evidence; their old clocks are closed.

```text
python3 -I -S -B <materialized>/proposed/adapter-controls.py \
  --registration <new-adapter-control-registration.json> \
  --registration-sha256 <actual-sha256> --output <fresh-ignored-results>
python3 -I -S -B <materialized>/proposed/supervisor-controls.py \
  --registration <new-supervisor-control-registration.json> \
  --registration-sha256 <actual-sha256> --output <different-fresh-ignored-results>
```

Each harness already runs its internal normal/optimized matrix. The 198 scored adapter rows involve 218 instrumented entrypoint invocations, and the supervisor suite contains 12 bounded inert cases. These counts were observed both before packaging and in the subsequent actual relocated distribution check. Repetition supplies operational evidence, not additional cases of mathematical proof. They produce no Lean or mathematical credit. Preserve the original zero-case copy-root failure and the one-line source correction; do not relabel that failure as a passing run.

For the publication builder, provide Pandoc 3.10.2, the reviewed LuaLaTeX/TeX Live environment and exact publication assets, then register a fresh externally supervised build stage. The builder retains its work directory and all command streams. Each command has a 300-second bound; an external stage owner must provide aggregate limits and cleanup review. Its resolved profile binds the reviewed HTTPS-link PDF successor. Actual normal and optimized checks each produced two matching PDFs. Exact mode admits only those reviewed bytes, with no source-to-installed-font authenticity claim.

```text
python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --exact --check \
  --work-dir <fresh-canonical-build-directory>
python3 -O -I -S -B scripts/build-prefix-mgw-mean-pdf.py --exact --check \
  --work-dir <different-fresh-canonical-build-directory>
```

These are command shapes for a new run; the linked current evidence contains the completed local runs. `--check` makes two new build directories. Optional `--output` must be a new file; an interrupted output write can leave a partial owned output for inspection. Existing paths are not overwritten. `--cross-toolchain` deliberately returns status 2 before building because no reviewed relation for this new mean PDF exists. A successful same-toolchain run establishes only the exact publication relation it checks. Builder controls passed 224 actual cases in normal and optimized invocations. The [portable control distribution](pdf-controls/CONTROLS.md) passed a separate actual normal/optimized relocation check with the same 224-case/532-start scope. Full integration inventories, hosted evidence and source-state generation remain separate obligations.
