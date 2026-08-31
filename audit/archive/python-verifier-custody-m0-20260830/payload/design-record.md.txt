# Design record: bounded Python verifier custody inventory M0

## Decision

Use an exact selected-tree, AST-assisted, fail-closed static registry as milestone M0. Keep source
objects separate from launch edges. Keep execution custody and both named closure projections open.
Do not implement an M1 launcher in this milestone.

The selected review object is commit
`eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9`, tree
`d3d247270822fe477862c80ba8b6a9041ac8f6bc`.

## First-principles decomposition

The desired long-term statement is about a process. A process statement has several distinct
objects:

1. stored source bytes;
2. a textual or programmatic launch request;
3. the interpreter executable;
4. final `argv`, standard input, current directory, environment, and platform;
5. imported and dynamically generated source;
6. child processes and native dependencies;
7. the produced result; and
8. the meaning assigned to the result.

None of these equalities follows from the others. M0 can soundly inventory items 1 and selected
static candidates for item 2. It cannot soundly close items 3 through 8. The data model therefore
uses references between objects and explicit blockers instead of one global “verified” flag.

## Twelve routes considered

### Route 1: list only `scripts/*.py`

Advantage: small and easy to read.

Failure: it omits audit tools, test generators, Python binding tests, and historical recovery code.
Disposition: rejected as an incomplete selected-tree source seed.

### Route 2: list all tracked `.py` paths

Advantage: exact, deterministic, and independent of naming conventions.

Failure: paths alone do not show imports, dynamic source construction, or launch routes.
Disposition: selected as the source seed, but not as the complete registry.

### Route 3: search only GitHub workflow YAML

Advantage: focuses on hosted operational commands.

Failure: local release recipes, shell wrappers, and documented commands remain invisible.
Disposition: included as one root class, not the only root class.

### Route 4: scan the complete tracked repository as untyped text

Advantage: high lexical recall.

Failure: large numbers of prose and fixture false positives; no language-specific meaning; costly
registry churn. Disposition: rejected for M0. The named repository-wide projection remains open.

### Route 5: use regex only for Python files

Advantage: one mechanism for all sources.

Failure: comments and strings are conflated with executable syntax; aliases and AST locations are
weak. Disposition: rejected. Use AST for Python and lexical rules only for operational text roots.

### Route 6: use AST and treat selected names as resolved calls

Advantage: concise dynamic-call result.

Failure: Python names and attributes are rebindable. `obj.spec_from_file_location` need not be
`importlib`. Disposition: reject resolution; retain the selected spelling as an open edge.

### Route 7: use runtime imports to discover the module graph

Advantage: observes one concrete import execution.

Failure: it executes inventoried code, can cause side effects, depends on the current environment,
and misses alternate branches. Disposition: rejected for M0. Runtime custody belongs to a later
milestone with process controls.

### Route 8: infer local imports by matching filenames

Advantage: exposes plausible repository-owned dependencies.

Failure: `sys.path`, packages, namespace packages, hooks, and shadowing control actual resolution.
Disposition: retain as `local_candidate`; never mark resolved.

### Route 9: classify imports with the scanner host's `sys.stdlib_module_names`

Advantage: broad and automatic.

Failure: output depends on the scanner interpreter version and build. Disposition: reject. Use an
explicit checked profile limited to roots observed in the selected files.

### Route 10: parse shell, YAML, Just, and Actions completely

Advantage: could reduce false positives and recover control flow.

Failure: four languages, expansions, reusable actions, external includes, and platform semantics
make this a much larger claim. Disposition: reject for M0. Use a small declared lexical grammar and
keep all matches open.

### Route 11: bind current worktree files

Advantage: simple file reads.

Failure: a dirty worktree can differ from the reviewed object, and a later edit can silently change
the scan. Disposition: reject. Read exact Git blobs from the pinned tree.

### Route 12: claim execution custody after registry equality

Advantage: attractive summary.

Failure: registry equality does not establish which bytes an interpreter opened or executed.
Disposition: prohibited. M0 claims inventory coherence only.

## Why the selected design is the best bounded combination

Route 2 gives the complete selected-tree `.py` seed. Route 3 contributes one operational root
class. Route 6 contributes AST spelling evidence without its invalid resolution claim. Route 8
provides useful local candidates while preserving `sys.path` uncertainty. Route 11 supplies exact
review-object bytes. The fail-closed parts of routes 4, 7, 10, and 12 become explicit blockers and
future-work requirements.

This combination has a narrow theorem-like shape: for one exact tree and one exact algorithm, the
stored registry equals the recomputed static inventory. It does not stretch static evidence into a
runtime statement.

## Fifty-lens council review

The council is a structured internal critique. It is not independent review. Each lens asks a
different question and records the design response.

| # | Lens | Question | Finding and action |
|---:|---|---|---|
| 1 | object identity | Which repository object is scanned? | Pin exact commit and tree; do not scan moving `HEAD`. |
| 2 | path completeness | Can naming conventions omit Python? | Seed every tracked `.py` path. |
| 3 | worktree isolation | Can dirty files affect output? | Read Git blobs, not worktree source copies. |
| 4 | Git routing | Can ambient variables redirect objects? | Scrub common routing and replacement variables; state residual Git trust. |
| 5 | Git object semantics | Is a path digest enough? | Bind mode, blob OID, byte length, and SHA-256. |
| 6 | hash semantics | Does hashing authenticate source? | State that local digests give correspondence, not authenticity. |
| 7 | parser version | Can AST output vary? | Require Python 3.11+; avoid a portability claim. |
| 8 | encoding | Can decoding silently replace bytes? | Use `tokenize.detect_encoding`; fail closed on errors. |
| 9 | syntax failure | Is an unparsable file dropped? | Retain a blocking parse status; never substitute an empty AST. |
| 10 | import granularity | Is one statement one dependency? | Record imported-name edges and separate statement counts. |
| 11 | relative imports | Can an empty root be mistaken for stdlib? | Retain level and root; unresolved roots stay blocking. |
| 12 | local modules | Does a matching filename prove resolution? | Use `local_candidate`, never “resolved.” |
| 13 | standard library | Is a name proof of stdlib origin? | Use an explicit spelling profile and keep execution resolution open. |
| 14 | third-party code | Does a package name bind a wheel? | Record declared roots only; versions, wheels, and native libraries remain open. |
| 15 | dynamic built-ins | Does `compile` spelling prove built-in identity? | Record direct AST spelling; keep target resolution open. |
| 16 | attribute calls | Can selected attributes be false positives? | Retain possible false positives as open edges. |
| 17 | aliases | Can the selected grammar miss dynamic behavior? | Count every other call and mark its resolution open. |
| 18 | decorators | Can code run outside explicit calls? | State that decorator and metaclass effects are not resolved. |
| 19 | import hooks | Can import behavior be replaced? | Put import hooks in the environment blocker. |
| 20 | module cache | Can `sys.modules` change resolution? | Keep interpreter and environment profiles open. |
| 21 | launch/source separation | Can one source have many launches? | Store separate source and launch tables with references. |
| 22 | source kinds | Are file, `-c`, stdin, and `-m` conflated? | Give each a separate enum value. |
| 23 | missing bytes | Is unknown input treated as empty input? | Use `null` availability plus a blocking status. |
| 24 | shell quoting | Does `shlex` implement the shell? | Use it only as a bounded token aid; state non-equivalence. |
| 25 | heredocs | Can stdin source be inventoried? | Capture simple exact bodies; leave complex forms open. |
| 26 | command strings | Can `-c` change under expansion? | Record static content only; final `argv` stays open. |
| 27 | module tools | Does `-m pytest` bind pytest? | Record module spelling; dependency and plugin state stay open. |
| 28 | child Python | Can Python start another Python? | Scan selected subprocess spellings with `sys.executable` clues. |
| 29 | wrappers | Can a helper hide process creation? | Leave all unselected calls open; no wrapper closure claim. |
| 30 | native launchers | Can Rust or C start Python? | Explicitly exclude native files from the M0 root seed and block global closure. |
| 31 | workflow semantics | Does a YAML line necessarily execute? | Treat it as a static candidate, not an event. |
| 32 | documentation commands | Are commands in `AGENTS.md` operational? | Include them as declared guidance candidates, not process evidence. |
| 33 | historical sources | Can filenames justify “nonoperational”? | Reserve the status but do not infer it in M0. |
| 34 | helper sources | Can lack of `__main__` prove library-only use? | Reserve `library_helper`; do not infer it in M0. |
| 35 | optimization | Can `-O` alter scanner behavior? | Run checker and hostile suite in normal and optimized modes. |
| 36 | assertions | Can `assert` be used as a correctness gate? | Core semantic checks use explicit exceptions, not assertions. |
| 37 | schema weakening | Can an unknown keyword be ignored? | Use the fail-closed schema subset validator and test an unknown assertion. |
| 38 | duplicate JSON keys | Can later keys shadow earlier keys? | Reject duplicate object keys. |
| 39 | canonical encoding | Can semantically equal JSON hide byte drift? | Require one canonical UTF-8 rendering. |
| 40 | reference integrity | Can edges point to absent sources? | Validate every source, import, and dynamic reference. |
| 41 | projection semantics | Can “all” be mistaken for closure? | Name the desired projection but set status `open_blocking`. |
| 42 | bootstrap circularity | Can the scanner validate itself? | Keep checker and schema bootstrap explicitly open. |
| 43 | mutation adequacy | Do a few mutants prove completeness? | Report bounded hostile sensitivity only. |
| 44 | resource bounds | Can a hostile object store exhaust memory? | State the lack of hard pre-allocation and timeout bounds. |
| 45 | platform scope | Is a macOS result portable? | Platform profiles remain unresolved; no portability claim. |
| 46 | scientific transfer | Does inventory validate PID math? | Explicitly prohibit mathematical or statistical transfer. |
| 47 | security language | Is this a security attestation? | State no security-clean, sandbox, or authenticity claim. |
| 48 | maintenance | Can `--write` normalize away a real change? | Require adjudication before regeneration. |
| 49 | accessibility | Can a reader distinguish counts and objects? | Define every term and give input/output examples. |
| 50 | future compatibility | Can M0 be extended without relabeling it? | Keep versioned formats and place M1 in a separate milestone. |

## Hostile-test design

The hostile suite rejects changes to the format, review commit, review tree, bootstrap, tracked
count, path list, path-list digest, dynamic count, operational-root digest, source digest,
source status, unselected-call status, import resolution, dynamic resolution, launch custody,
launch kind, launch ordering, launch source reference, both projection statuses, projection order,
nonimplications, unknown top-level fields, and unsupported schema assertions.

Worked fixtures independently exercise four import classes, five dynamic spellings, file launch,
`-c`, `-m`, heredoc, unresolved command, Python child-process recognition, a hyphenated package-name
negative control, and a selected-attribute false-positive boundary.

These tests show sensitivity to the named faults. They do not prove that the fault inventory is
complete or that the scanner implementation is correct.

## Retained negative results

1. A complete shell/YAML/Just/Actions semantic parser was not implemented. The effort and trust
   boundary exceed M0.
2. Runtime imports were not used. They would execute code and provide only environment-specific
   evidence.
3. Native launchers were not scanned. The all-process projection therefore cannot close.
4. Dynamic aliases were not resolved. Every other call remains open.
5. The checker does not have an acyclic independent bootstrap.
6. No launch edge has execution custody.
7. No mathematical claim receives additional truth credit from this inventory.

## Publication and provenance note

The process contribution is the explicit separation of stored sources, launch candidates, import
classes, dynamic edges, profiles, projections, and nonimplications in this repository. Python AST
and Git objects are established tools. This design record does not claim a new scientific method,
new PID measure, new estimator, or formal verification result.
