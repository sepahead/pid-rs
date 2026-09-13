# Current local bias-paper reproduction

On 12 September 2026, the current builder reproduced the [14-page bias paper](../../../../output/pdf/prefix-mgw-bias.pdf) and [one-page summary](../../../../output/pdf/prefix-mgw-bias-summary.pdf) with exact reference bytes. Each document had two fresh builds in normal Python and two in optimized Python. The [typed evidence record](CURRENT_REPRODUCTION.json) binds the sources, outputs and private receipts.

Before production, both runs of the 158-case reader controls passed: 14 positive and 144 negative cases per run. The added cases exercise the current parser profile, file inventory, source bytes, links and import guards. These controls use inert inputs. The subsequent production imported fresh copies of the actual 58-file pypdf 6.16.1 source package.

All four producer processes and 164 direct builder commands returned zero. Review covered 336 command streams, all eight output PDFs, 652 input records and 420 captured input blobs. The full-paper checks include thirty heading destinations, their visible locations and eight protected identifier types. Both original execution deadlines were met. Normal and optimized runs share the same interpreter and tools, so they are correlated checks.

The result makes the rendered [exposition](../../lean-prefix-mgw-bias/EXPOSITION.md) and [summary source](../../lean-prefix-mgw-bias/SUMMARY.md) reproducible under the declared local profile. It adds no mathematical result. The [theorem map](../../lean-prefix-mgw-bias/THEOREM_MAP.md) states the formal scope and assumptions. Mean-paper reproduction, the full repository aggregate and hosted acceptance have separate evidence requirements.

The profile binds the primary executables, five fonts, the selected LuaLaTeX format and parser sources. Complete dynamic-library and TeX-distribution identity are outside its scope. Process and memory checks are sampled observations. Raw receipts retain machine paths and stay in private custody; their exact hashes are in the typed record. The [negative history](NEGATIVE_HISTORY.md) retains the earlier production and navigation failures.
