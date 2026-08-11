# Lean theorem map for SX-COUNT-ATOM-BRIDGE-001 revision 2

Bound authority:
`audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean`.

Status: accepted source-level crosswalk within revision 2. The pinned checker binds complete
source bytes and declaration bodies; this human map is orientation, not the enforcement route.

| Obligation | Bound declarations |
|---|---|
| Q1 component, atom, and coordinate types | `SxPid2Component`, `SxPid2Atom`, `SxPid2Coordinate` |
| Q1 fixed orders | `sxPid2NodeOrder`, `sxPid2AtomOrder`, `sxPid2ComponentOrder`, `sxPid2CoordinateOrder` |
| Q1 order/cardinality facts | `sx_pid2_node_order_length`, `sx_pid2_atom_order_length`, `sx_pid2_component_order_length`, `sx_pid2_coordinate_order_length`, `sx_pid2_coordinate_order_nodup`, `sx_pid2_coordinate_order_complete`, `sx_pid2_coordinate_card` |
| M1 coefficient tables | `sxPid2MobiusCoefficient`, `sxPid2ZetaCoefficient` |
| M1 concrete transforms | `sxPid2MobiusTransform`, `sxPid2ZetaTransform` |
| M1 coefficient interpretations | `sx_pid2_mobius_transform_eq_integer_row_sum`, `sx_pid2_zeta_transform_eq_integer_row_sum` |
| M1 inverse and reconstruction | `sx_pid2_zeta_after_mobius`, `sx_pid2_mobius_after_zeta`, `sx_pid2_joint_cumulative_eq_sum_atoms`, `sx_pid2_source_one_cumulative_eq_unique_one_add_redundancy`, `sx_pid2_source_two_cumulative_eq_unique_two_add_redundancy`, `sx_pid2_mobius_row_sum` |
| S1 coordinate exchange | `sxPid2SwapNode`, `sxPid2SwapAtom`, `sx_pid2_swap_node_involution`, `sx_pid2_swap_atom_involution`, `sx_pid2_mobius_coordinate_swap_equivariant` |
| L1 transform linearity | `sx_pid2_mobius_sub` |
| L1 component selection | `localCumulativeComponent`, `averagedCumulativeComponent`, `localAtomComponent`, `averagedPointwiseAtomComponent`, `averagedAtomComponent` |
| L1 net subtraction | `local_cumulative_net_component_eq_sub`, `averaged_cumulative_net_component_eq_sub`, `averaged_atom_net_component_eq_sub` |
| A1 average/transform commutation | `averaged_pointwise_atom_eq_mobius_of_averaged_cumulatives` |
| Q1 coordinate evaluator | `averagedSxPid2Coordinate` |
| L1 exact local arguments | `countInformativeArgument`, `countMisinformativeArgument`, `countComponentArgument` |
| L1 support positivity and component ratio | `count_component_argument_positive_on_support`, `count_net_argument_eq_informative_div_misinformative` |
| L1 empirical local-log bridges | `local_cumulative_informative_empirical_eq_log_count_argument`, `local_cumulative_misinformative_empirical_eq_log_count_argument`, `local_cumulative_component_empirical_eq_log_count_argument` |
| E1 averaged count expressions | `averagedCumulativeCountExpression`, `averagedAtomCountExpression`, `sxPid2CountCoordinateExpression` |
| E1 cumulative, atom, and all-coordinate equalities | `averaged_cumulative_component_empirical_eq_count_expression`, `averaged_atom_component_empirical_eq_count_expression`, `all_24_averaged_coordinates_empirical_eq_count_expression` |
| P1 cumulative products | `countCumulativeRealProduct`, `countCumulativeRationalProduct` |
| P1 atom products | `countAtomRealProduct`, `countAtomRationalProduct` |
| P1 coordinate products | `countCoordinateRealProduct`, `countCoordinateRationalProduct` |
| P1 product positivity | `count_cumulative_real_product_positive`, `count_atom_real_product_positive`, `count_coordinate_real_product_positive` |
| P1 exact rational casts | `count_cumulative_real_product_eq_rational_cast`, `count_atom_real_product_eq_rational_cast`, `count_coordinate_real_product_eq_rational_cast` |
| G1 logarithm of cumulative product | `log_count_cumulative_real_product` |
| G1 scaled-log normalization | `averaged_cumulative_count_expression_eq_scaled_log_product`, `averaged_atom_count_expression_eq_scaled_log_product`, `all_24_count_expressions_eq_scaled_log_product`, `all_24_averaged_coordinates_eq_scaled_log_product` |
| G1 sign and zero reductions | `all_24_averaged_coordinates_positive_iff_product_gt_one`, `all_24_averaged_coordinates_negative_iff_product_lt_one`, `all_24_averaged_coordinates_zero_iff_product_eq_one` |

## Imported dependency boundary

The module imports `TwoSourceCountEventBridge.lean`, which supplies `SxPid2Node`, the fixed source
collections and keyed events, exact count/event operations, empirical law and positive support,
local informative/misinformative/net cumulatives, event-count positivity, and the signed-net
cumulative count bridge. Its completed claim is documented separately under
`SX-COUNT-EVENT-BRIDGE-001` revision 2.

## Deliberately absent theorem classes

This map contains no theorem for:

- publication text to Lean definitions;
- component-atom nonnegativity;
- rows or serialized inputs to counts;
- Rust `NODES2`, `invert2`, binary64, or output fields;
- a standalone certifier, Python, compiler, or runtime;
- bounded resource execution;
- statistical or population behavior; or
- three-source and general higher-source Möbius lattices.

The checker binds complete declaration types and bodies, not merely the names listed in this human
crosswalk.
