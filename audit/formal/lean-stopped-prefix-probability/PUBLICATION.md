# Finite first-hit laws and exact MGW prefix cancellation

Author: Sepehr Mahmoudian · 27 September 2026.

The [standalone exposition](EXPOSITION.md) and [PDF](../../../output/pdf/stopped-prefix-probability.pdf) derive two classical finite IID probability identities and an exact invariant of the project's categorical MGW prefix statistic. They explain the probability model, complete proof steps, endpoint cases, counterexamples and implementation boundary.

For a fixed finite law and event $A$ with mass $a$, a word containing $n$ misses followed by one hit has mass $(1-a)^n a$, including $n=0$, $a=0$ and $a=1$. Splitting its restricted law gives a product of unnormalized miss and hit measures. Separately, if a comparison list contains the complete source-plus-target anchor, both defined prefix contributions are zero. That condition is sufficient, not necessary or an earliest-stop characterization.

The [three-export theorem map](THEOREM_MAP.md) records local acceptance at 21:28:05 UTC on 26 September 2026: newly accepted F1/F2 and a fresh F4 recheck under the joint source closure. The [expanded source statements](THEOREM_STATEMENTS.md), [source map](SOURCE_MAP.json), [acceptance projection](LOCAL_FORMAL_ACCEPTANCE.json), [raw exported type records](evidence/EXPORTED_TYPES.json) and [command evidence](evidence/COMMANDS.json) distinguish statements from execution. The 41 theorem/control records include three theorem exports; they do not represent 41 theorems.

[REPLAY.md](REPLAY.md) states the open portable-launcher and hosted theorem-replay obligations. [HISTORY.md](HISTORY.md) retains the failed F1/F2 correspondence check, earlier exact F4 closure and pre-admission inventory refusal. Preparation-era comments in unchanged proof sources remain historical; the later acceptance record supplies their disposition.

The status fields in SOURCE_MAP.json and LOCAL_FORMAL_ACCEPTANCE.json still name the private publication candidate assembled on 26 September 2026. HISTORY.md's statement that a rendered figure or accepted PDF did not exist “yet” describes that same dated snapshot. Those retained fields are not updated to describe a later containing commit. They preserve the earlier publication state alongside the accepted local theorem result; they neither claim nor replace later PDF validation. Portable and hosted theorem replay remain open.

The proposed exact return guard would inspect a complete anchor and supplied categorical rows. Under constant-cost coordinate equality, scanning $n$ rows costs $O(n|I|)$ comparisons and stores $O(|I|)$ anchor values, excluding sampling and lattice state. No stopped-prefix Rust API, sampler, runtime measurement, expected-runtime or variance result is supplied. Zero prefix increments do not by themselves establish a stopped-gradient theorem or an application benefit.

The [metadata projection ledger](evidence/PUBLIC_METADATA_PROJECTIONS.json) records locator replacements and handle omissions while retaining original-byte commitments. Of 58 main streams, 56 preserve native bytes and two are declared boundary-output projections. The accepted source and all 41 record values are unchanged. These public projections are neither a new native run nor authenticated binaries or complete off-host raw custody.

F1/F2 are classical probability; F4 is a project invariant in the context of [Makkeh, Gutknecht and Wibral's categorical shared exclusions](https://doi.org/10.1103/PhysRevE.103.032149). No scientific-priority claim or transfer to continuous PID follows.

The [figure-font manifest](../latex/stopped-prefix-probability/figure-fonts.json) binds Source Sans Pro Regular, Semibold and Bold, plus Latin Modern Math. The builder checks the font bytes, confines SVG rendering to private Fontconfig directories and records the actual configuration and embedded figure fonts before temporary files are removed. The complete report also uses its declared TeX body fonts. See the [third-party notices](../../../THIRD_PARTY_NOTICES.md), [Source Sans Pro license](../latex/mathematical-results-guide/font-licenses/source-sans-pro-ofl-1.1-tex-live-2024.txt) and [Latin Modern Math license](../latex/mgw-fixed-world/font-licenses/latin-modern-math/GUST-FONT-LICENSE.txt). These input checks do not imply identical rendering across toolchain versions.

Cite: Sepehr Mahmoudian, *Finite first-hit laws and exact MGW prefix cancellation*, pid-rs, 2026, with the exact containing repository commit or release. Use [CITATION.cff](../../../CITATION.cff) for the software and cite the defining method paper separately.
