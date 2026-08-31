# Bounded Python verifier custody inventory (M0)

## Result in one sentence

Revision 1 gives a reproducible, typed inventory of Python source blobs and static launch candidates
in one exact `pid-rs` Git tree. It does **not** establish that any Python program ran from the
inventoried bytes.

The machine authority is [`registry-v1.json`](registry-v1.json). The strict schema is
[`../schemas/python-verifier-custody-registry-v1.schema.json`](../schemas/python-verifier-custody-registry-v1.schema.json).
The checker and hostile suite are:

```text
scripts/check-python-verifier-custody-inventory.py
scripts/check-python-verifier-custody-inventory-self-test.py
```

This packet is a directly consumed audit unit. That is why this directory has a `README.md` under
the repository's README-if-and-only-if rule.

## The exact claim

Assume all of the following conditions:

1. The local Git repository contains commit
   `eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9` and its objects.
2. That commit names tree `d3d247270822fe477862c80ba8b6a9041ac8f6bc`.
3. The selected Git implementation returns the exact blobs named by that tree.
4. CPython 3.11 or newer parses the source with the checked scanner rules.
5. The checked-in scanner, schema, subset validator, and registry have the reviewed meanings.

Under those assumptions, the checker establishes this bounded equality:

```text
checked-in registry bytes = canonical JSON(recompute(exact selected-tree blobs, M0 rules))
```

It also checks internal references, counts, digest projections, ordering, and the rule that every
source, import resolution, dynamic edge, launch edge, profile, bootstrap state, and named closure
projection stays open when M0 does not resolve it.

The claim is **inventory coherence**. It is not execution custody, process closure, correctness of a
verifier, correctness of Python, or correctness of mathematics.

## Why this work is necessary

Many mathematical checks in this repository are Python programs. A green command can be
misleading if the command loads different source bytes, imports an unexpected local module, uses a
different third-party package, compiles generated text, or starts a child interpreter with a
different environment. Before a later milestone can bind an execution, it needs a precise list of
the objects and unresolved edges that require binding.

M0 supplies that list. It does not use the list as a substitute for execution evidence. This
separation prevents a common error:

```text
source was found in Git  !=  source was loaded  !=  source ran  !=  result is correct
```

The inventory is also useful when a checker changes. A reviewer can see whether a change adds an
import, adds an `exec`, changes a launch route, or creates a new unresolved source kind. The
inventory makes that change visible. It does not decide whether the change is good.

## Terms

| Term | Exact meaning in revision 1 | It does not mean |
|---|---|---|
| selected review tree | The exact Git tree named above | current `HEAD`, every branch, or an external archive |
| Python file source | A tracked path ending in `.py` in the selected tree | an imported module or executed program |
| operational root | A selected workflow YAML, shell script, root `justfile`, or root `AGENTS.md` blob scanned for command tokens | a proven entry point |
| source | A file or a static candidate for interpreter input | bytes actually read by a process |
| launch edge | A lexical or AST candidate that can describe a Python launch | an observed process event |
| import edge | One imported-name binding in an AST import statement | successful import resolution |
| import statement | One `import` or `from ... import ...` AST node | one imported name; a statement can bind several names |
| dynamic edge | One selected direct call spelling | proof that the call target is the Python built-in or `importlib` function with that name |
| local module candidate | A tracked `.py` path whose name can match an imported root | the module selected by `sys.path` |
| third-party declared | An imported root in the explicit five-name profile | an authenticated package, version, wheel, or native library |
| profile | A typed placeholder for an interpreter, environment, or external tool | a resolved runtime identity |
| projection | A named subset of launch candidates | a closed call graph |
| `open_blocking` | Required evidence is absent, so a stronger claim must stop | a warning that can be ignored |
| `unsupported_blocking` | The data model recognizes the kind but this milestone does not support resolution | proof that the route cannot be supported later |
| `historical_nonoperational` | Reserved status for a separately justified historical source | a status inferred from a filename |
| `library_helper` | Reserved status for a separately justified helper | proof that direct execution is impossible |
| `closed` | Reserved for a later milestone with sufficient evidence | a status used by M0; M0 forbids it |

## Selected-tree census

The counts below come from the registry. The scanner recomputes them. No count is inserted only to
make a test pass.

### Seed

| Object | Exact count | Rule |
|---|---:|---|
| tracked tree entries | 1,040 | recursive entries in the selected tree |
| tracked Python files | 186 | every path that ends in `.py` |
| operational roots | 66 | the four root classes below |
| workflow YAML roots | 13 | tracked `.github/workflows/*.yml` or `*.yaml` |
| shell roots | 51 | every tracked path that ends in `.sh` |
| root `justfile` | 1 | exact root path |
| root `AGENTS.md` | 1 | exact root path |

All 186 tracked Python blobs decode and parse under the selected AST rule. This is a bounded parse
result. It is not a Python-version portability theorem.

The wider source-record census keeps parse failures visible:

| AST status over all 662 source records | Exact count | Meaning |
|---|---:|---|
| `parsed` | 332 | exact bytes were available and accepted by the selected parser rule |
| `not_available_open_blocking` | 312 | M0 has a name or launch candidate but not source bytes to parse |
| `syntax_error_open_blocking` | 18 | captured bytes did not parse under the selected rule; the candidate remains blocking |

All 186 exact tracked-file records are in the `parsed` row. The other 146 parsed records are
captured inline sources. A syntax error is not discarded and is not reinterpreted as proof that a
candidate cannot execute: quoting, shell expansion, or a different runtime could change the bytes.

### Sources and static launch candidates

| Record | Exact count | Interpretation |
|---|---:|---|
| all source records | 662 | 186 Git files plus 476 inline, module, unresolved-file, or dynamic candidates |
| file-kind records | 198 | 186 exact Git files plus 12 unresolved `.py` command tokens |
| inline `-c` records | 23 | static command-string candidates |
| inline standard-input records | 146 | heredoc candidates; exact bodies are retained when a simple terminator is found |
| `-m` module-tool records | 16 | module-name candidates, not resolved modules |
| dynamic-fixture records | 279 | unresolved command or child-launch fragments |
| launch edges | 1,057 | lexical and selected Python-child-process candidates |
| launch edges in the official-verifier-name projection | 507 | exact Git file sources with a `check-*` spelling |
| launch edges in the all-process projection | 1,057 | every launch candidate found by the M0 seed |

The value 1,057 is **not** a process count. A command can appear several times in documents,
recipes, tests, and workflows. A conditional command can never run. One runtime command can also
expand into several processes. M0 retains the static occurrences and does not collapse these
different meanings.

### Imports in the 186 tracked files

| Record | Exact count |
|---|---:|
| import statements | 2,110 |
| imported-name edges | 2,295 |
| standard-library-profile imported names | 2,214 |
| local-candidate imported names | 16 |
| declared-third-party imported names | 65 |
| third-party import statements | 26 |
| files with a declared-third-party import | 11 |

The local candidates are `_exact_product` and `json_schema_subset`:

| Imported root | Statements | Imported-name edges | Files |
|---|---:|---:|---:|
| `_exact_product` | 4 | 4 | 4 |
| `json_schema_subset` | 6 | 12 | 6 |

The declared third-party roots are:

| Imported root | Statements | Imported-name edges | Files |
|---|---:|---:|---:|
| `csxpid` | 3 | 4 | 1 |
| `numpy` | 3 | 3 | 3 |
| `pid_core_rs` | 2 | 2 | 2 |
| `pypdf` | 16 | 54 | 8 |
| `pytest` | 2 | 2 | 2 |

An imported-name edge counts each name in a statement. For example,
`from pypdf import PdfReader, PdfWriter` is one statement and two imported-name edges. This is why
the two totals differ.

### Selected dynamic calls in the 186 tracked files

| Direct AST spelling | Exact count |
|---|---:|
| `compile(...)` where the callee is an `ast.Name` | 50 |
| `exec(...)` where the callee is an `ast.Name` | 49 |
| `__import__(...)` where the callee is an `ast.Name` | 2 |
| `*.spec_from_file_location(...)` where the final attribute matches | 32 |
| `*.module_from_spec(...)` where the final attribute matches | 32 |
| total | 165 |
| files containing at least one selected call | 76 |

The attribute rule intentionally accepts a possible false positive. For example,
`unrelated.spec_from_file_location(...)` is recorded even if `unrelated` is not `importlib`. The
edge stays `open_blocking`. The scanner prefers an explicit extra candidate to an unjustified
closed claim.

An alias is a possible false negative. For example:

```python
make_code = compile
make_code(source, name, "exec")
```

The selected dynamic scanner does not call this a `compile` edge. It counts the call in
`other_call_count`, and `other_call_resolution_status` remains `open_blocking`. Thus the registry
does not imply that 165 is the complete number of behaviorally dynamic calls.

## How the scanner works

### Step 1: fix the review object

The scanner resolves the exact commit with replacements disabled. It reads the raw commit object
and requires the pinned first `tree` header. It also requires Git to report the `sha1` object
format. It does not use the worktree copy of the 186 sources.

The scanner removes ambient Git directory, worktree, namespace, replacement, shallow-file,
alternate-object, and configuration routing variables from its Git child environment. It also
sets `GIT_NO_REPLACE_OBJECTS=1` and `core.useReplaceRefs=false`. This reduces accidental routing.
It does not authenticate the Git executable or object store.

### Step 2: read and verify the tree blobs

The scanner runs a NUL-delimited recursive tree listing. It rejects malformed records,
non-UTF-8 paths, duplicate paths, and noncanonical relative paths. It retrieves each seed blob by
object identifier. This repository uses SHA-1 Git objects, so it recomputes the framed blob object
identifier:

```text
SHA1("blob " || decimal_length || NUL || blob_bytes)
```

This is Git object correspondence inside the available repository. SHA-1 here is not an
authenticity, collision-resistance, or external-publication claim. The registry also stores a
SHA-256 digest of each selected blob for exact local comparison.

### Step 3: build the source universe

The file seed is every selected-tree path with suffix `.py`. The path list is sorted by its
canonical POSIX spelling. The registry stores the complete list and the SHA-256 digest of its
compact canonical JSON encoding.

The scanner then adds typed candidate sources found by the launch scan:

- `file`: an exact tracked file or an unresolved token ending in `.py`;
- `inline_stdin`: a heredoc candidate;
- `inline_argv`: an interpreter `-c` candidate;
- `module_tool`: an interpreter `-m` candidate; and
- `dynamic_fixture`: an unresolved command or child-process expression.

Exact Git files and exact static fragments carry byte lengths and SHA-256 digests. Unresolved
fragments carry `null` for unavailable bytes. A `null` is not silently converted into an empty
program.

### Step 4: parse Python files

The scanner uses `tokenize.detect_encoding`, decodes the exact blob, and calls `ast.parse` in
`exec` mode with type comments enabled. It records the encoding, parse status, AST node count,
selected imports, selected dynamic edges, and the number of all other calls.

If decoding or parsing fails, the source stays blocking. The scanner does not skip the source and
does not treat a failed parse as an empty AST.

### Step 5: classify imports

For each imported name, the scanner takes the first component as the import root. It assigns one
of four static classes:

1. `stdlib_profile` for a root in the explicit checked scanner tuple;
2. `local_candidate` for `_exact_product` or `json_schema_subset`;
3. `third_party_declared` for the five roots in the table above; or
4. `unresolved_open_blocking` for every other root.

All four classes retain `execution_resolution_status = open_blocking`. Even a standard-library
name can be affected by `sys.path`, import hooks, interpreter state, or shadowing. A class describes
the static spelling. It does not describe the runtime module object.

The `local_modules` array lists possible basename and qualified-name matches from the selected
paths. It also stays open because a path match does not determine `sys.path`.

### Step 6: detect selected dynamic edges

The scanner records direct `ast.Name` calls to `compile`, `exec`, and `__import__`. It also records
attribute calls whose final name is `spec_from_file_location` or `module_from_spec`. It records the
source anchor, first-argument AST shape, argument count, keyword names, and primitive spelling.

The scanner does not evaluate name bindings. Every dynamic edge remains open. Calls through aliases,
wrappers, decorators, descriptors, C extensions, monkey patches, or generated AST are not resolved.

### Step 7: scan operational roots

The root scanner uses a checked regular expression for lowercase `python`, `python3`, versioned
`python3.x`, `pypy`, and selected `$PYTHON` forms. Token boundaries avoid treating the package name
`pid-python` as a command. It then classifies a candidate in this order:

1. `-c` gives `inline_argv`;
2. `-m` gives `module_tool`;
3. `<<` gives `inline_stdin`;
4. a `.py` token gives `file`; or
5. the unresolved remainder gives `dynamic_fixture`.

For a simple heredoc delimiter, the scanner captures lines up to the matching terminator. Shell
expansion, nested heredocs, generated delimiters, command substitution, quoting semantics, and
control flow are not interpreted. Those gaps stay blocking.

### Step 8: scan selected Python child-process calls

The AST scan considers calls whose final name is one of `Popen`, `run`, `call`, `check_call`,
`check_output`, `system`, `execv`, or `execve`. It records a candidate only when the expression also
contains `sys.executable` or a selected static Python token. It resolves a target only when an exact
literal `.py` string matches a selected file path. Variable targets remain dynamic fixtures.

This is a selected spelling scan. It does not resolve wrappers, aliases, native extensions,
function reassignment, or commands launched by Rust and other unscanned languages.

### Step 9: attach profiles and projections

Each launch edge records:

- caller blob and anchor;
- source identifier and source kind;
- observed normal or optimized mode;
- observed `-B`, `-I`, `-O`, and `-S` flags;
- unresolved `cwd`, standard input, environment, interpreter, external tool, and platform profiles;
- related import, dynamic, and declared-third-party edge identifiers;
- named projection membership;
- blockers and nonimplications.

The two named projections are deliberately open:

1. `repo-owned-official-verifier-source-entry/v1`; and
2. `all-repository-python-processes/v1`.

The first uses a resolved `check-*` path spelling. The spelling is a selection rule, not proof that
the file is official, complete, or invoked. The second contains all 1,057 M0 launch candidates but
cannot contain launchers outside the seed or grammar. Neither projection is a closure result.

### Step 10: validate schema, semantics, and exact equality

The checker requires canonical UTF-8 JSON with sorted object keys, two-space indentation, no
duplicate keys, and no non-finite numbers. The local schema subset validator rejects unsupported
schema assertions. Semantic checks then require unique source identifiers, contiguous launch
identifiers, valid references, exact path-list correspondence, and the M0 blocking boundary.

Finally, the checker compares the canonical checked-in registry bytes with the canonical
recomputed value. A stale digest, count, source, edge, profile, blocker, or nonimplication fails.

## Worked examples

The examples explain the data model. They do not add execution evidence.

### Example 1: exact file command

Input text in an operational root:

```text
python3 -I -S -B scripts/check-method-catalog.py
```

Static output:

```text
source kind: file
source id: file:scripts/check-method-catalog.py
observed flags: -B, -I, -S
mode: normal
execution custody: open_blocking
```

Why it remains open: the text does not bind the executable selected by `python3`, the current
directory, environment, source bytes opened by that process, imported modules, or process result.

Negative comparison:

```text
python3 "$CHECKER"
```

The variable target is a dynamic fixture. The scanner does not guess its value.

### Example 2: local import candidate

Input Python:

```python
from json_schema_subset import SchemaValidationError, validate
```

Static output: one import statement, two imported-name edges, root
`json_schema_subset`, class `local_candidate`, and an exact candidate path
`scripts/json_schema_subset.py`.

Why it remains open: if the caller directory, `sys.path`, package state, or import hooks differ,
Python can select another object or fail. The path match is useful evidence for a later launcher. It
is not runtime resolution.

Negative comparison:

```python
from package import json_schema_subset
```

The static root is `package`, not `json_schema_subset`. M0 does not relabel this as the known local
candidate merely because the final component has a familiar spelling.

### Example 3: direct and aliased dynamic calls

Input Python:

```python
compile(raw, name, "exec")
make_code = compile
make_code(raw, name, "exec")
```

Static output: the first call is a selected `compile` dynamic edge. The second is an unselected
call and contributes to `other_call_count`. Both resolution states remain open.

This asymmetry is deliberate. An AST name spelling is observable. Binding equivalence requires a
different analysis and runtime assumptions.

### Example 4: heredoc standard input

Input shell:

```text
python3 -I -S -B - <<'PY'
import json
print(json.dumps({"status": "example"}))
PY
```

Static output: `inline_stdin`, exact captured body bytes when the simple terminator is found, an AST
for the body, and a standard-library-profile import edge for `json`.

Why it remains open: a shell can expand or redirect content, choose another interpreter, or skip
the command. M0 does not observe the bytes read from file descriptor 0.

Negative comparison: a generated delimiter or nested shell construct can defeat the simple
delimiter grammar. The source then retains unavailable bytes and remains blocking.

### Example 5: command-string source

Input text:

```text
python3 -O -I -S -B -c 'import sys; raise SystemExit(0)'
```

Static output: `inline_argv`, optimized mode, the four observed flags, exact statically parsed
command text when shell tokenization succeeds, and a standard-library-profile `sys` import edge.

Why it remains open: shell quoting and variable expansion are not a proof of the final `argv`
element. `-O` can also change behavior by removing assertions and changing `__debug__`. This is why
the inventory and self-test run in normal and optimized scanner modes.

Negative comparison:

```text
python3 -c "$CODE"
```

M0 can retain the static `$CODE` token, but it does not know the expanded command string. A parse
failure for that token remains `syntax_error_open_blocking`; it is not proof that the runtime
command is invalid or empty.

### Example 6: module tool

Input text:

```text
python3 -m pytest -q
```

Static output: `module_tool` with static fragment `pytest` and an unresolved interpreter profile.

Why it remains open: `-m` asks Python's import system to locate a module. The spelling does not bind
the installed distribution, version, entry code, plugins, configuration, or test collection.

Negative comparison:

```text
python3 -m "$TOOL"
```

This is still a module-tool candidate, but the literal token does not identify the expanded module.
M0 records the unresolved fragment and does not infer `pytest` or any other tool.

### Example 7: declared third-party import

Input Python:

```python
from pypdf import PdfReader
```

Static output: class `third_party_declared`, one statement, one imported-name edge, and open runtime
resolution.

The class is useful because later custody must include package and native dependency identity. It
does not claim that `pypdf` is installed, authentic, safe, or semantically suitable.

Negative comparison:

```python
import importlib
importlib.import_module(package_name)
```

The ordinary `import importlib` statement is visible. The value of `package_name` is not a static
third-party import edge, and `import_module` is outside the five selected dynamic spellings. The
call remains in `other_call_count` with open resolution.

### Example 8: selected attribute false positive

Input Python:

```python
unrelated.spec_from_file_location("x", path)
```

Static output: one selected-attribute dynamic edge with `resolution_status = open_blocking`.

This can be a false positive because the receiver is not resolved. Retaining it is safe for an
inventory. Treating it as a confirmed importlib call would be wrong.

### Example 9: Python child process from Python

Input Python:

```python
subprocess.run([sys.executable, "scripts/check-method-catalog.py"])
```

Static output: a `python_subprocess_api` caller, file source when the literal matches the selected
tree, and an unresolved child-interpreter profile.

Negative comparison:

```python
runner([interpreter, checker_path])
```

The selected grammar cannot establish that `runner` creates a process or that either variable has
the expected value. It remains among unselected calls.

### Example 10: native launcher outside the seed

Input Rust, C, or another native language:

```text
Command::new("python3").arg("tool.py")
```

M0 output: no launch edge, because native-language files are not operational roots in revision 1.
The `all-repository-python-processes/v1` projection therefore stays open. A later milestone must
add a typed native-language grammar or runtime process evidence before it can claim repository-wide
closure.

There is no positive native-launch classification in M0. Inventing one from a textual example would
contradict the declared seed. The positive result is narrower: this counterexample is documented as
a blocker, so the all-process projection cannot silently close.

This is an important negative example. The name of the all-process projection states the desired
question. Its `open_blocking` status states that M0 has not answered it.

## Positive and negative results

### Positive results

- The exact selected tree contains 186 tracked Python files, and all 186 parse under the M0 rule.
- The scanner reproduces the complete selected path list and each exact Git blob identity.
- Import statements, imported names, selected dynamic spellings, and launch candidates have typed
  records and exact anchors.
- The selected dynamic census is stable in normal and optimized scanner modes.
- The registry keeps source records separate from launch edges. One source can have several launch
  candidates, and one unresolved launch can name no exact file.
- Hostile tests reject count, digest, path, edge, schema, bootstrap, and closure-status mutations.
- Worked fixtures cover file, local import, dynamic call, heredoc, `-c`, `-m`, third-party, and
  Python child-process routes.

### Negative results and retained gaps

- No source or launch edge is closed.
- No interpreter, environment, external tool, module import, or dynamic target is authenticated.
- The checker does not resolve aliases, wrappers, decorators, monkey patches, import hooks, native
  extensions, or runtime-generated names.
- The operational-root seed excludes Rust and other native-language launchers.
- The command grammar is lexical. It does not implement shell, YAML, Just, or GitHub Actions
  semantics.
- The AST parser is not a Python semantic model.
- The bootstrap is open because the scanner and schema are descendants of the reviewed tree.
- The registry has no independent external custody or transparency witness.
- The scan has finite selected inputs but no hard memory, CPU, or denial-of-service theorem.
- Neither named projection is closed.

These are not cosmetic disclaimers. They define the difference between M0 and a future execution
custody milestone.

## Trust and resource boundary

The bounded result trusts the local hardware and operating system, CPython parser and standard
library, Git executable and object store, SHA-1/SHA-256 implementations, the schema subset
validator, the scanner source, and the human interpretation of the seed and grammar. The checker
does not make these dependencies independent by hashing its own output.

The selected input is finite: 1,040 tree entries, 186 Python files, and 66 operational roots. The
implementation currently materializes the selected blobs, ASTs, and registry in memory. It has no
pre-allocation byte limit and no hard child-process deadline. Thus an available hostile object store
can consume resources before a clean failure. This milestone is a repository audit, not a
denial-of-service boundary.

## Run and interpret the checks

Run both modes:

```text
python3 -I -S -B scripts/check-python-verifier-custody-inventory.py
python3 -O -I -S -B scripts/check-python-verifier-custody-inventory.py
python3 -I -S -B scripts/check-python-verifier-custody-inventory-self-test.py
python3 -O -I -S -B scripts/check-python-verifier-custody-inventory-self-test.py
```

`-I` isolates Python from user site and `PYTHON*` settings. `-S` skips automatic `site` import.
`-B` suppresses bytecode-cache writes. `-O` exercises optimized Python. These flags reduce ambient
state for the scanner. They do not authenticate the interpreter or establish custody for the 186
inventoried programs.

The expected checker summary ends with:

```text
closure=0 (both projections open_blocking)
```

The summary's `imports` and `dynamic` fields cover all 662 source records, including captured
inline fragments. The selected-tree file census is the separately named
`tracked_file_import_*` and `tracked_file_dynamic_*` family in the registry: 2,295 imported-name
edges and 165 selected dynamic calls. Do not compare the two scopes as if they were the same
population.

That is a successful M0 result. Changing it to a nonzero closure count without new evidence would
be a claim escalation, not an improvement.

`--emit` writes the deterministic expected registry to standard output. `--write` is a maintenance
operation for an explicitly reviewed revision change. It is restricted to the canonical registry
path, requires a regular single-link destination, stages bytes in the same directory, and replaces
the file after schema and semantic validation. This is not a filesystem-durability or atomic-reader
theorem. Do not use `--write` to silence a mismatch. First determine why the selected source or
scanner rules changed, then update the design, documentation, tests, and review revision together.

## Maintenance rule

A new selected tree is a new adjudication. Do all of the following:

1. list every changed Python file and operational root;
2. explain every changed import, dynamic edge, and launch candidate;
3. decide whether the seed and grammar are still adequate;
4. keep unresolved cases blocking;
5. update exact counts from the scanner, not from memory;
6. run the normal and optimized checker and hostile suite;
7. inspect the canonical registry diff;
8. update the design record when a route or assumption changes; and
9. make no M1 execution-custody claim unless a separate M1 design and evidence justify it.

## Provenance and novelty boundary

The use of Python's AST, import syntax, command-line modes, and Git object access is established
technology. The typed registry, selected seed, fail-closed statuses, named open projections, and
composition of these parts are project-defined engineering in `pid-rs`. They are not a scientific
novelty claim and do not change any PID definition, estimator, theorem, or mathematical result.

Primary technical references:

- Python, [Abstract Syntax Trees](https://docs.python.org/3/library/ast.html).
- Python, [The import system](https://docs.python.org/3/reference/import.html).
- Python, [Command line and environment](https://docs.python.org/3/using/cmdline.html).
- Python, [`importlib` implementation utilities](https://docs.python.org/3/library/importlib.html).
- Git, [Git objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects).

The prose uses an ASD-STE100-inspired preference for short sentences, defined terms, and one
meaning per term. The repository does not claim ASD-STE100 certification or full conformance.

## Relationship to later work

M0 answers: “What exact static source and launch candidates did this bounded scan find?”

A later M1 can ask: “For one declared launcher, can a same-run mechanism bind the exact entry bytes
that the interpreter loaded?” That later result still would not automatically close transitive
imports, dynamic code, child processes, native libraries, or every repository launcher.

Repository-wide closure requires a separate design. It must cover the open projections, native
launchers, shell and workflow semantics, interpreter and dependency identities, dynamic sources,
process descendants, environment, resource control, and a noncircular bootstrap. M0 does not
pretend that this larger result already exists.
