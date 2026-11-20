# Workflow filters for the normalized Shannon report checks

Sepehr Mahmoudian, 20 November 2026

The ordinary hosted run on commit `8709ee545c9cec9f29f66129bda48aef49adedcd` stopped in the action-reference check before it ran the KSG arithmetic tests. The checker interpreted a quoted branch-name entry in a YAML list as a possible mapping key. The same syntax occurred in two workflows. [Failed job](https://github.com/sepahead/pid-rs/actions/runs/44657429606/job/136027020101)

The repair writes the same branch names and path patterns as plain YAML strings. Eight entries changed spelling in the normalized-ratio workflow and fourteen in the PID2 source workflow. PyYAML 6.0.3 and Psych 3.1.0 each parsed both complete workflows identically before and after the edits. Their job, permissions and action-reference sections also matched byte for byte. [Normalized-ratio workflow](../../.github/workflows/normalized-shannon-ratio.yml) · [PID2 workflow](../../.github/workflows/pid2-shannon-source-profile.yml)

The original numerical comparison used the observer manifest with SHA-256 `35439baf58eef626f99a5e10ef2bc42356558c560a10aaab0c496136af084f5c`. Its six files and exact byte bindings are preserved at the original observer commit. The live manifest changes only the digest of the workflow file. The original and corrected Rust outputs, reference inputs and the numerical predicate retain their recorded identities. This change in workflow spelling adds no numerical observations. [Frozen observer manifest](https://github.com/sepahead/pid-rs/blob/a5fe92978a8671c2592191ab9c5b25b6ab46c02b/audit/research/normalized-shannon-ratios/manifest.json) · [Native observations](normalized-shannon-reports-2026-11-20/receipt.json)

Cite Sepehr Mahmoudian (2026), *Workflow filters for the normalized Shannon report checks*, with the exact repository commit or release. [Software citation](../../CITATION.cff)
