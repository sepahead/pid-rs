# Lean theorem map for SX-COUNT-EVENT-BRIDGE-001 revision 2

Authority: `audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean`.

| Obligation | Checked declarations |
|---|---|
| S1 fixed nodes | `SxPid2Node`, `sxPid2Collections`, `sx_pid2_node_collection_semantics`, `sx_pid2_collections_nonempty` |
| C1 counts/law/support | `totalCount`, `positiveSupport`, `eventCount`, `empiricalLaw`, `empirical_law_nonnegative`, `sum_empirical_law_eq_one` |
| M1 event masses | `event_mass_empirical_law_eq_count_ratio`, `positive_mass_support_empirical_law` |
| M2 redundancy IE | `sx_pid2_redundancy_source_event_eq_union`, `source_singleton_branch_inter_eq_joint`, `redundancy_source_event_count_inclusion_exclusion`, `redundancy_source_event_count_eq_add_sub_joint` |
| M3 restricted IE | `sx_pid2_redundancy_target_restricted_event_eq_union`, `source_target_singleton_branch_inter_eq_joint`, `redundancy_target_restricted_event_count_inclusion_exclusion`, `redundancy_target_restricted_event_count_eq_add_sub_joint` |
| M4 joint keyed count | `joint_source_target_branch_eq_singleton`, `joint_source_target_restricted_event_count_eq_anchor` |
| P1 supported positivity | `event_count_positive_of_mem`, `sx_pid2_event_counts_positive_on_support`, `count_net_argument_positive_on_support`, `sx_pid2_empirical_event_masses_positive_on_support` |
| L1 local count identity | `probabilityNetArgument`, `countNetArgument`, `localCumulativeInformative`, `localCumulativeMisinformative`, `localCumulativeNet`, `local_cumulative_net_eq_log_probability_argument`, `probability_net_argument_empirical_eq_count_net_argument`, `local_cumulative_net_empirical_eq_log_count_net_argument` |
| A1 averaged expression | `averagedCumulativeNet`, `sxpid2_averaged_cumulative_net_count_expression` |

The module contains exactly 38 ordered source declarations, including 24 theorems. Together with
the existing six imported modules, the pinned finite-convergence package has 263 inventoried
declarations and 201 named source theorems. Every named source theorem is enumerated for
`collectAxioms`; the permitted basis is exactly `propext`, `Classical.choice`, and `Quot.sound`.
The complete bridge source is SHA-256 bound, so same-name theorem-body or theorem-type drift is a
gate failure.

`PidFiniteConvergenceSemanticContract.lean` separately pins the four-node map, asymmetric event
membership, exact source and restricted counts, four distinct rational arguments, supported
nonnegativity and positivity, and the main averaged theorem. Its 16 compiled examples are not
individually axiom-audited. Its exact bytes are SHA-256 bound by the checker.

The theorem map stops at a supplied exact count function. It contains no theorem for bytes or rows
to counts, Rust implementation refinement, floating-point execution, certificate parsing,
resource behavior, concrete Möbius atoms, sampling, population convergence, or calibration.
