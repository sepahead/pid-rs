# Exact retained context for Fable 5 Max KSG revision-4 review

HEAD and origin/main at launch: `118e1de6a2d6d2ae33fe7bdc224736257e42a83f`.

The listed artifacts are exact UTF-8 bytes. Unlisted repository state is outside this review.

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json`

SHA-256: `29fc9f78122d85e2852890bbfba1849729c1d1016c074ed7071a4f3dd52dc8a3`

```text
{
  "active_revision": 4,
  "claim_id": "KSG-INTEGER-HARMONIC-001",
  "facts": {
    "arithmetic": {
      "coefficient_vector": [
        1,
        1,
        -1,
        -1
      ],
      "exact_bound": "-D <= T <= D",
      "exact_term": "T = H_(k-1) + H_(n-1) - H_(x-1) - H_(y-1)",
      "information_unit": "nats",
      "negative_values_permitted": true,
      "silent_clamping_forbidden": true,
      "typed_analytic_premise": "psi(m) = H_(m-1) - gamma for used positive integers"
    },
    "binary64_corpus": {
      "allowed_absolute_error_epsilon_multiples": 32,
      "canonical_endpoint_negative_zero_count": 0,
      "canonical_endpoint_positive_zero_count": 354,
      "case_count": 8198,
      "exhaustive_case_count": 6920,
      "first_maximum_tuple_n_k_nx_ny": [
        4096,
        1,
        2048,
        2048
      ],
      "maximum_absolute_error_epsilon_multiples": 8,
      "maximum_error_is_ulp_claim": false,
      "maximum_error_measure": "absolute_error_nats_scaled_by_f64_epsilon",
      "maximum_error_tie_count": 40,
      "naive_prefix_ordinary_left_nonzero_count": 121,
      "selected_neumaier_prefix_ordinary_left_negative_zero_count": 0,
      "selected_neumaier_prefix_ordinary_left_nonzero_count": 150,
      "source_swap_bit_asymmetry_count": 0,
      "stress_case_count": 1278,
      "structural_endpoint_count": 354,
      "structural_endpoint_exhaustive_count": 240,
      "structural_endpoint_stress_count": 114,
      "structural_rule_is_frozen_corpus_iff": true,
      "structural_rule_is_universal_iff": false
    },
    "domains": {
      "exclusive_map": "k-1 <= nx,ny < n; x=nx+1; y=ny+1",
      "inclusive_map": "k <= x,y <= n; pass anchor-inclusive counts directly",
      "pure_arithmetic_lean_domain": "n >= 1; 1 <= k <= n; k <= x,y <= n",
      "runtime_estimator_domain": "n >= 2; 1 <= k < n; k <= x,y <= n"
    },
    "formal": {
      "formal_assurance_v4_sha256": "45813b90cc15c6880ca9df83419851a7bb80adb4100963ff4c2322493d4eb905",
      "lean_active_source_sha256": "32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4",
      "lean_mutation_count": 14,
      "lean_theorem_count": 19,
      "revision2_lean_source_sha256": "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943",
      "shared_cuts": [
        "analytic_digamma_premise",
        "human_coefficient_signs",
        "human_exclusive_inclusive_index_map",
        "chosen_domain_and_theorem_statements"
      ],
      "z3_local_bound_sha256": "33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31",
      "z3_mutation_count": 12,
      "z3_negated_unsat_count": 4,
      "z3_positive_sat_preflight_count": 4,
      "z3_self_test_sha256": "241a23c903c5087dadc91b31d6fd332fc57f9d94ad46b62709290f25082cb07e",
      "z3_uses_uninterpreted_harmonic": true
    },
    "modular_certificate": {
      "certificate_sha256": "ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102",
      "maximum_denominator": 999999,
      "mutation_count": 26,
      "nonendpoint_count": 7844,
      "pre_artifact_observation_is_final_custody": false,
      "pre_artifact_observation_sha256": "1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc",
      "rejected_prime": 1000003,
      "rejected_prime_collision_indices_zero_based": [
        8045,
        8049,
        8069,
        8093
      ],
      "rejected_prime_residue_digest": "d90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111",
      "residue_implication_direction": "nonzero residue implies exact rational nonzero",
      "selected_prime_role": "redundant fault diversity only, not CRT",
      "selected_primes": [
        1000033,
        1000037,
        1000081
      ],
      "selected_residue_digests": [
        "931c30fab8560d5692121f3c16be42afa4e9d0b73e640ca4285f5352f4cfff9b",
        "09b6d9e5a4f9f5ee4346dbfc869ba254710f6198cba97f2ac3449db8adb16479",
        "20b2596be7ed67e9fb07039465196da9c289f87d0e13b87d85e8bcf964b18de0"
      ],
      "zero_residue_implies_exact_zero": false
    },
    "object_firewall": [
      "ksg_local_integer_arithmetic_only",
      "no_transfer_to_complete_ksg_estimator",
      "no_transfer_to_continuous_ehrlich_isx",
      "no_transfer_to_continuous_pid2",
      "no_transfer_to_categorical_mgw_sxpid",
      "no_transfer_to_williams_beer_imin",
      "no_transfer_to_fitted_quantized_sxpid",
      "no_transfer_to_project_heuristics",
      "no_transfer_to_incomplete_or_mixed_dimension_pid3",
      "no_transfer_to_wrappers_identity_consumers_or_applications"
    ],
    "witnesses": {
      "w0_smallest_bound": "n=2,k=1 realizes +D,-D,0",
      "w1": {
        "exact_target": "107/210",
        "helper_arguments": [
          2,
          8,
          5,
          2
        ],
        "ordered_counts": [
          4,
          1
        ],
        "radius": 79,
        "selected_bits": "0x3fe04e04e04e04e0"
      },
      "w2": {
        "exact_mean": "71/840",
        "helper_arguments": [
          2,
          8,
          5,
          2
        ],
        "inclusive_counts": [
          5,
          2
        ],
        "ordered_binary64_position_difference": 8,
        "ulp_claim": false
      }
    }
  },
  "historical_hashes": {
    "audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean": "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943",
    "audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean": "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v2.md": "e8e3d936d94bc25ed1eaa49e22d3cbdee0e65a649192f613e76dce8c22a99151",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v3.md": "d17e8eed0f3944d2d4a8dd0e67cf44ffc7ddfb1a5d2194269d17a4003a9f6fa0",
    "claims/KSG-INTEGER-HARMONIC-001/call-site-map.md": "048aaa4209f5c42616f18339775c463f1ac45fe7d25581c7b9d37d571d79c5a6",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v1.md": "726907d19af21db00f3b4245722ac7a0d83b7e6df814aa3e589db47624344c44",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v2.md": "2a114fca75c52d65410bc2b80bd561c7a1858035d5643a2d660044a53823f7f3",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v3.md": "457f55ef444b931cefa05d0dcb06d084cd51f510810080a80a30f0b9f5d59071",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v2.md": "0c65acef2b96bcac208be78a1d781bccb6c079b249076544d2227b3634e5b61b",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v3.md": "8d4f289d5b1ee9a10995bd8ae1bc086ae276812d1e09005c9006a730adab0949",
    "claims/KSG-INTEGER-HARMONIC-001/decision-v2.md": "540d7f468bbcbc8771adeae8ce3ee103dad5d98d7bc5298a8c1e91a67a19fd26",
    "claims/KSG-INTEGER-HARMONIC-001/decision.md": "0dabc4d4a0247cf55aa03f433bc47eab6f8b2f245824d27da0c7927ce30b79fe",
    "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v2.md": "6b750c010a00debde29ec2b3959e1bd55751f7ebe9c136beac202503b1b6196c",
    "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix.md": "f9de6f6ebdd6fe30887c34e3abedef504ffbd2bba5e113a70f22a8f0b004b4fc",
    "claims/KSG-INTEGER-HARMONIC-001/failures/decimal-endpoint-cancellation-residuals-v3.md": "eeb7b369792ebc882428829ccc62cb472ab5e3b137f1231cbc7f722de759321b",
    "claims/KSG-INTEGER-HARMONIC-001/failures/evidence-gate-gaps.md": "ff4ea026728be041c01b97b91ddadfabc8e619f1ce292ccf131637c15e2dcfdb",
    "claims/KSG-INTEGER-HARMONIC-001/failures/formal-seams-and-negative-controls-v2.md": "d5e2f5bf6fc4f05a298d388ebecbf0bfcbb256c0b1e1e26de8a27d8f059782cb",
    "claims/KSG-INTEGER-HARMONIC-001/failures/mutation-count-drift-v3.md": "b6d886b5dc75c2dd1ae0e12ef4a3a9c842b68093fb541abe45dab19111970c53",
    "claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md": "565e18922514123942dd4d241c2d677be27101c3402f6fb594dc699641eae071",
    "claims/KSG-INTEGER-HARMONIC-001/failures/release-phase-conflation-v3.md": "2665ff3e7ddd0c4b845882267a6c6c2d2b9e96c3840f01a10e403300b5dc640c",
    "claims/KSG-INTEGER-HARMONIC-001/failures/route-label-and-tie-multiplicity.md": "0853760aa6e7e0952a5f4f1f945e05c9328863ef544a576bada44da033f94e5f",
    "claims/KSG-INTEGER-HARMONIC-001/failures/stale-parallel-bit-oracles.md": "87ea622cf0cea2827cc7637315c4f76e29d53b82a5479c37afd9d20841fc6343",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v2.md": "1068d90dcfe7a20b5237305c0468a6a74eedeb5b91196ff6bfe9969dec300c10",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md": "062d51b03cbcfbfee9a16cba1e29ba3cb83480e6e48e603788828f917b08db25",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v1.md": "83ee2a03b55ebc2161c3fec6dfe9a40680e8fae0b0bcebb01d5a1533f6872440",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v2.md": "e0f7badb2a5f929c3d91fd7193d2ab3fe4e9cf7a2ae83995b7465c2bae2a7724",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v2.md": "2c108aef29e833a6bf9f41968f917ad05b645606b377fc55ff3b0f9bccc1d389",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v3.md": "a2d29661b07a4b855c97ec6fb2e371bb4f422a1bdb3e24f5291a3022b49e889d",
    "claims/KSG-INTEGER-HARMONIC-001/obligations.md": "b22e061070d16e69a39ede6f367a01c600b9c917ab199debc5ebca267b3b502e",
    "claims/KSG-INTEGER-HARMONIC-001/revision-index-pre-v4.md": "b3c5c83cdb883acbc7cfc750cd97bab1d6e3d3bd3eb70ec8aabd840897cc4c15",
    "claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-2026-07-25.md": "1487761f2da443771854a1ad61b25042bb18267d68a67452e43d3c3a89d7cc7e",
    "claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-erratum-v2.md": "c8100a713bb5f557396398972346d081fe1f1ac3bfc67b749257a88b3f82c855",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v2.md": "5cfe75c9572ee7742a2428dcd119018a6ae1bd92c7cfb1ed0bce5257f7691ab5",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v3.md": "ed1f9324eb537eb4e752d7b147942562290ab9f6aeeab453fa91f7d73c80d9bc",
    "claims/KSG-INTEGER-HARMONIC-001/routes.md": "23b521232290b30c5d346b42f8cc55ecb1c5f639607a4fa03496cbdd3d1fe256"
  },
  "open_integration_gates": [
    "claim_custody_final_replay",
    "git_phase_isolation",
    "compiled_debug_release_witnesses",
    "serial_parallel_recapture",
    "catalog_reverse_closure",
    "release_family_closure",
    "audience_artifact_regeneration",
    "software_identity_rebind",
    "settled_full_ci",
    "final_hostile_review",
    "immutable_evidence_matrix_v4",
    "immutable_decision_v4",
    "unsigned_main_commit_and_receipt"
  ],
  "packet_files": {
    "audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean": "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943",
    "audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean": "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943",
    "audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean": "32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4",
    "audit/formal/lean/lake-manifest.json": "e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd",
    "audit/formal/lean/lakefile.toml": "1c3f1818c4a62ab48f4ae05de573f6d884aaf7f7397a21646df162151cfccdf1",
    "audit/formal/lean/lean-toolchain": "2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e",
    "audit/formal/z3-ksg-harmonic/ksg-digamma-cancellation.smt2": "8ae66c11fb66541bc47766b2682cf1e53d9b656aa0fa12e6945ac22057816ed4",
    "audit/formal/z3-ksg-harmonic/ksg-index-maps.smt2": "71ea8db97df43f51da89496a5e799bedc6216f9ede40368207d2ffed8df40fe1",
    "audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2": "33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31",
    "audit/formal/z3-ksg-harmonic/ksg-symmetric-range.smt2": "add0fc3a371c65433fdfd8b1e51d3182c6ef78db0cfd1d372f461f1d030e19a9",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v2.md": "e8e3d936d94bc25ed1eaa49e22d3cbdee0e65a649192f613e76dce8c22a99151",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v3.md": "d17e8eed0f3944d2d4a8dd0e67cf44ffc7ddfb1a5d2194269d17a4003a9f6fa0",
    "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md": "e14654f5b27273fefc0f9395f105c2e549ee4a281122579e722b47dc96e6d97d",
    "claims/KSG-INTEGER-HARMONIC-001/call-site-map.md": "048aaa4209f5c42616f18339775c463f1ac45fe7d25581c7b9d37d571d79c5a6",
    "claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json": "ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102",
    "claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json.sha256": "017a5ee3bd19ad1765b3f9499a65a95602af64577f5120b7af8e4ac1d6f1b7d9",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v1.md": "726907d19af21db00f3b4245722ac7a0d83b7e6df814aa3e589db47624344c44",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v2.md": "2a114fca75c52d65410bc2b80bd561c7a1858035d5643a2d660044a53823f7f3",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v3.md": "457f55ef444b931cefa05d0dcb06d084cd51f510810080a80a30f0b9f5d59071",
    "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md": "f3438abbb5fa97df4f27940358b2b8e2244a7ac94ca9b03bb82c5772142e048b",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v2.md": "0c65acef2b96bcac208be78a1d781bccb6c079b249076544d2227b3634e5b61b",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v3.md": "8d4f289d5b1ee9a10995bd8ae1bc086ae276812d1e09005c9006a730adab0949",
    "claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md": "61e81c0812978ad8d806a7ab836a103d26b52061094bbb38d8ca3c3460834b11",
    "claims/KSG-INTEGER-HARMONIC-001/decision-v2.md": "540d7f468bbcbc8771adeae8ce3ee103dad5d98d7bc5298a8c1e91a67a19fd26",
    "claims/KSG-INTEGER-HARMONIC-001/decision.md": "0dabc4d4a0247cf55aa03f433bc47eab6f8b2f245824d27da0c7927ce30b79fe",
    "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v2.md": "6b750c010a00debde29ec2b3959e1bd55751f7ebe9c136beac202503b1b6196c",
    "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix.md": "f9de6f6ebdd6fe30887c34e3abedef504ffbd2bba5e113a70f22a8f0b004b4fc",
    "claims/KSG-INTEGER-HARMONIC-001/failures/decimal-endpoint-cancellation-residuals-v3.md": "eeb7b369792ebc882428829ccc62cb472ab5e3b137f1231cbc7f722de759321b",
    "claims/KSG-INTEGER-HARMONIC-001/failures/evidence-gate-gaps.md": "ff4ea026728be041c01b97b91ddadfabc8e619f1ce292ccf131637c15e2dcfdb",
    "claims/KSG-INTEGER-HARMONIC-001/failures/formal-seams-and-negative-controls-v2.md": "d5e2f5bf6fc4f05a298d388ebecbf0bfcbb256c0b1e1e26de8a27d8f059782cb",
    "claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md": "04335c39cdbd409bd987805b3dc0d540bb5514d19d807a08940286d43770ca3c",
    "claims/KSG-INTEGER-HARMONIC-001/failures/mutation-count-drift-v3.md": "b6d886b5dc75c2dd1ae0e12ef4a3a9c842b68093fb541abe45dab19111970c53",
    "claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md": "565e18922514123942dd4d241c2d677be27101c3402f6fb594dc699641eae071",
    "claims/KSG-INTEGER-HARMONIC-001/failures/release-phase-conflation-v3.md": "2665ff3e7ddd0c4b845882267a6c6c2d2b9e96c3840f01a10e403300b5dc640c",
    "claims/KSG-INTEGER-HARMONIC-001/failures/route-label-and-tie-multiplicity.md": "0853760aa6e7e0952a5f4f1f945e05c9328863ef544a576bada44da033f94e5f",
    "claims/KSG-INTEGER-HARMONIC-001/failures/stale-parallel-bit-oracles.md": "87ea622cf0cea2827cc7637315c4f76e29d53b82a5479c37afd9d20841fc6343",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v2.md": "1068d90dcfe7a20b5237305c0468a6a74eedeb5b91196ff6bfe9969dec300c10",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md": "062d51b03cbcfbfee9a16cba1e29ba3cb83480e6e48e603788828f917b08db25",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md": "45813b90cc15c6880ca9df83419851a7bb80adb4100963ff4c2322493d4eb905",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v1.md": "83ee2a03b55ebc2161c3fec6dfe9a40680e8fae0b0bcebb01d5a1533f6872440",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v2.md": "e0f7badb2a5f929c3d91fd7193d2ab3fe4e9cf7a2ae83995b7465c2bae2a7724",
    "claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md": "d7c87b91e8bd4b43d86d08361f0b73df48f4d6ecb97d459f48ecb506f7f3d3e5",
    "claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md": "0e9a04456a6d60ed151e5bd764e5a08060c83024c1731311234907a1db2e805d",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v2.md": "2c108aef29e833a6bf9f41968f917ad05b645606b377fc55ff3b0f9bccc1d389",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v3.md": "a2d29661b07a4b855c97ec6fb2e371bb4f422a1bdb3e24f5291a3022b49e889d",
    "claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md": "28a4a5b885799a95f4450c241797886fd6a607abbbbb59bafd15db3195afd521",
    "claims/KSG-INTEGER-HARMONIC-001/obligations.md": "b22e061070d16e69a39ede6f367a01c600b9c917ab199debc5ebca267b3b502e",
    "claims/KSG-INTEGER-HARMONIC-001/revision-index-pre-v4.md": "b3c5c83cdb883acbc7cfc750cd97bab1d6e3d3bd3eb70ec8aabd840897cc4c15",
    "claims/KSG-INTEGER-HARMONIC-001/revision-index.md": "c50a66a8fd521b42f352055e7af21fdab00779a35cf4256c78d719737c6c1f23",
    "claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-2026-07-25.md": "1487761f2da443771854a1ad61b25042bb18267d68a67452e43d3c3a89d7cc7e",
    "claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-erratum-v2.md": "c8100a713bb5f557396398972346d081fe1f1ac3bfc67b749257a88b3f82c855",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v2.md": "5cfe75c9572ee7742a2428dcd119018a6ae1bd92c7cfb1ed0bce5257f7691ab5",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v3.md": "ed1f9324eb537eb4e752d7b147942562290ab9f6aeeab453fa91f7d73c80d9bc",
    "claims/KSG-INTEGER-HARMONIC-001/routes-v4.md": "e14c3a54c81f84208f42b241b04d0feda3f32d0b1e62a32396c9e161ef5aa951",
    "claims/KSG-INTEGER-HARMONIC-001/routes.md": "23b521232290b30c5d346b42f8cc55ecb1c5f639607a4fa03496cbdd3d1fe256",
    "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json": "560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c",
    "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256": "fb91172bdb767b3e11e15ef4e89bb0482b932c5c2450f87d566245eda87a8ec7",
    "scripts/check-ksg-harmonic-modular-certificate-self-test.py": "c6376ab07d714a7d732568d589e73e01377cffdbcf163340e9866dfadda7eac4",
    "scripts/check-ksg-harmonic-modular-certificate.py": "561f6c2fe25b5b54fd87f1c5b210b5cca55afda75b3b139ba5078269166aa755",
    "scripts/check-lean-ksg-integer-harmonic-self-test.py": "80e37d202acdc7fe9a5118601c693131e74bd8384c3e3ac712c8f0e617b92f3e",
    "scripts/check-lean-ksg-integer-harmonic.py": "eb57ba3632ba3d2a811c971b20ab5bda2d3b3e0cd26fe69662cc39dbf25504d4",
    "scripts/check-z3-ksg-integer-harmonic-self-test.py": "241a23c903c5087dadc91b31d6fd332fc57f9d94ad46b62709290f25082cb07e",
    "scripts/check-z3-ksg-integer-harmonic.py": "c52618848f3331892bcb34b151a1e51674e7f493fbad71c48b160ff40fbf2d19",
    "scripts/generate-ksg-harmonic-modular-certificate.py": "48bff86ad0a89f80dce0452fe032c91edea7f07b7979ec07aabe5ecf2c6a574b",
    "scripts/generate-ksg-local-arithmetic-oracle.py": "a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b"
  },
  "packet_stage": "preclosure_core_manifest_must_be_regenerated_at_m1c",
  "revision_history": [
    {
      "active": false,
      "revision": 1,
      "status": "retained_superseded"
    },
    {
      "active": false,
      "revision": 2,
      "status": "retained_superseded"
    },
    {
      "active": false,
      "revision": 3,
      "status": "frozen_preclosure_no_go"
    },
    {
      "active": true,
      "revision": 4,
      "status": "integration_no_go"
    }
  ],
  "schema": "pid-rs/ksg-harmonic-active-packet",
  "schema_revision": 1,
  "status": "integration_no_go"
}
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/claim-v4.md`

SHA-256: `f3438abbb5fa97df4f27940358b2b8e2244a7ac94ca9b03bb82c5772142e048b`

```text
# Claim `KSG-INTEGER-HARMONIC-001`, revision 4

## Status, chronology, and evidence class

Revision 4 is the active **post-result integration** revision. It was written after the exact
identity, schema-2 corpus, formal extensions, and modular residues were observed; it is not a
preregistration. It preserves revisions 1--3 byte-for-byte. Revision 3 remains a frozen
pre-closure **NO-GO** because its custody and completion statements were not simultaneously true.

The exact positive-integer arithmetic core, the scoped Lean/Z3 obligations, and the bounded
8,198-row modular classification are **GO on their stated domains**. Repository/publication
integration is **NO-GO** until the open gates in `integration-disposition-v4.md` close on one
isolated settled tree. No final revision-4 evidence matrix or decision is asserted yet.

## Exact object, domain, range, and units

Let

```text
H_0 = 0
H_j = sum_(r=1)^j 1/r
T = psi(k) + psi(n) - psi(x) - psi(y)
D = H_(n-1) - H_(k-1).
```

Information quantities are in **nats**. The estimator-facing common domain is

```text
n >= 2
1 <= k < n
k <= x <= n
k <= y <= n.
```

Exclusive KSG counts satisfy `k-1 <= nx,ny < n` and map to `x=nx+1,y=ny+1`. Inventoried
anchor-inclusive Ehrlich ISX/PID3 counts satisfy `k <= x,y <= n` after their declared shell checks
and are passed directly. Only the coefficient vector `(+1,+1,-1,-1)` is eligible.

Under the typed analytic premise

```text
psi(m) = H_(m-1) - gamma
```

at the four positive integer arguments, exact cancellation gives

```text
T = H_(k-1) + H_(n-1) - H_(x-1) - H_(y-1)
  = (H_(n-1) - H_(max(x,y)-1))
    - (H_(min(x,y)-1) - H_(k-1)).
```

Harmonic monotonicity yields the sharp two-sided local bound

```text
-D <= T <= D.
```

The pure Lean arithmetic theorem admits the slightly larger domain `1 <= k <= n`; this does not
authorize a runtime estimator to accept `k=n`. The bound permits negative terms. It is forbidden
to clamp them, and it is not a bound on MI, redundancy, any PID atom, estimator bias, calibration,
or application error. At the smallest boundary `n=2,k=1`, helper endpoints realize `+D`, `-D`,
and zero, so neither nonnegativity nor a tighter universal symmetric bound is available.

## Frozen schema-2 and binary64 result

The reviewed generator/fixture/sidecar digests are:

```text
a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b  generator
560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c  fixture
fb91172bdb767b3e11e15ef4e89bb0482b932c5c2450f87d566245eda87a8ec7  sidecar file
```

The fixture contains 8,198 unique ordered rows: 6,920 exhaustive rows through `n=16` and 1,278
declared stress rows. The sufficient structural endpoint predicate is

```text
(nx == k-1 and ny == n-1) or (nx == n-1 and ny == k-1).
```

It identifies 354 rows, split into 240 exhaustive and 114 stress rows. On this frozen corpus only,
the modular certificate proves that exact rational `T=0` **iff** this predicate holds. The
structural predicate is only asserted sufficient outside this corpus; no universal
harmonic-zero-classification theorem is claimed.

The selected binary64 route uses a Neumaier-compensated harmonic prefix and sorted symmetric range
association. On exactly these 8,198 rows it has:

```text
maximum absolute error             = 8 * f64::EPSILON nats
allowed finite-corpus ceiling      = 32 * f64::EPSILON nats
first maximum tuple                = (4096,1,2048,2048)
maximum-error tie count            = 40
source-swap bit asymmetries         = 0
selected endpoint outputs          = 354 positive zeros
selected endpoint negative zeros   = 0
```

The `8*EPSILON` quantity is an absolute error in nats, not eight ULPs and not an
ordered-binary64-position distance. Over the same selected Neumaier prefix, ordinary four-term
left association is nonzero at 150/354 endpoints and produces zero negative zeros. The naive
prefix has a different 121/354 result and is not the stated discriminator.

## Behavioral bridges

W1 reaches production-private ordered KSG diagnostics at zero-based row 5:

```text
radius = 79
exclusive counts = (nx,ny) = (4,1)
helper arguments = (k,n,x,y) = (2,8,5,2)
exact-real T = 107/210
selected bits = 0x3fe04e04e04e04e0.
```

W2 uses the inclusive Ehrlich map `(5,2)` and reaches the same local target. Its public
compensated mean differs from the correctly rounded exact `71/840` by eight
**ordered-binary64 positions**. That is a fixture/path observation, not an ULP-error theorem and
not a validation of an Ehrlich estimator.

## Formal and modular results

The revision-4 Lean source has SHA-256
`32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4`.
It checks 19 theorem declarations and kills 14/14 baseline-first semantic mutations. The Z3 route
has four satisfiable positive preflights, four unsatisfiable negated obligations, and 12/12
satisfiable semantic countermodels; the local-bound source digest is
`33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31`.

Both routes share the analytic digamma premise, human signs, index maps, and selected theorem
statements. Z3's harmonic function is uninterpreted and its bound uses explicit local order
premises. Neither route proves Rust refinement, binary64 behavior, neighbor geometry, KSG/Ehrlich
validity, support, MGW PID, or application validity.

The final canonical modular certificate has SHA-256
`ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102`.
For each selected prime `1000033`, `1000037`, and `1000081` independently, all 354 endpoints have
zero residue and all 7,844 nonendpoints have nonzero residue. Since every selected prime exceeds
the maximum denominator `999999`, a nonzero residue implies the exact rational is nonzero. The
three primes provide redundant fault diversity, not CRT reconstruction and not three independent
proofs.

Rejected prime `1000003` has four exact-nonzero/nonendpoint zero-residue collisions. It
demonstrates that a zero residue does not imply an exact rational zero in general. The earlier
digest `1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc`
is only a historical pre-artifact observation; it is not final certificate custody. The modular
self-test kills 26/26 registered mutations in normal and optimized Python.

## Ten-object firewall

This claim is confined to KSG local integer arithmetic. It does not transfer a theorem to:

1. the complete KSG MI estimator;
2. continuous Ehrlich shared-exclusions redundancy;
3. continuous PID2 compositions;
4. categorical Makkeh--Gutknecht--Wibral shared-exclusions PID;
5. Williams--Beer `I_min`;
6. fitted quantized SxPID;
7. project-defined ISX heuristics;
8. incomplete or research mixed-dimensional PID3;
9. resampling/report/Python wrappers; or
10. software identity, release, consumer, or application validity.

Such a transfer requires its own premises and an explicit mapping/refinement theorem. No such
theorem is supplied here.

## Falsifiers and completion boundary

The scoped core is reopened by an exact counterexample, an index/sign/domain error, a changed
schema-2 row/order/digest, a selected-prime nonendpoint collision, a structural endpoint nonzero,
a changed W1/W2 count map, a changed binary64 signature, or a surviving registered formal,
modular, custody, or semantic mutation.

Repository integration remains NO-GO until claim custody, phase isolation, source/compiled replay,
catalog/release closure, generated audience artifacts, software identity, final hostile review,
and settled-tree CI all pass. Only then may immutable `evidence-matrix-v4.md` and `decision-v4.md`
be created.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md`

SHA-256: `28a4a5b885799a95f4450c241797886fd6a607abbbbb59bafd15db3195afd521`

```text
# Obligations for `KSG-INTEGER-HARMONIC-001`, revision 4

## Conjunctive obligation graph

```text
typed digamma premise + signs + exclusive/inclusive index maps
  + exact harmonic monotonicity
  -> E exact identity and sharp signed local bound

schema-2 bytes + generator replay + fixture sidecar
  + 354 row-derived endpoints (240/114)
  -> O bounded oracle custody

endpoint cancellation
  + each selected-field nonendpoint separator
  + rejected-prime collision control
  -> M corpus-only exact-zero iff certificate

E + O + M + selected binary64 association
  + W1 ordered production counts + W2 inclusive propagation
  -> X bounded runtime correspondence

Lean(19 theorems, 14 mutants)
  + Z3(4 conditional obligations, 12 mutants)
  + explicit shared-cut accounting
  -> F scoped formal assurance

claim custody + phase isolation + source/compiled replay
  + catalog/release/audience/identity closure + settled CI
  -> I repository integration

I + immutable evidence matrix + immutable decision + pushed receipt
  -> revision-4 completion
```

Every arrow is conjunctive. A green exact/formal/modular branch cannot close repository
integration while another branch is open.

## Obligation table

| ID | Obligation | Current state | Exit evidence / boundary |
|---|---|---|---|
| E1 | Derive the positive-integer four-sign digamma reduction. | GO, typed premise | exact algebra; `psi(m)=H_(m-1)-gamma` remains an analytic premise |
| E2 | Bind exclusive successor and inclusive identity maps. | scoped formal GO; runtime replay pending final tree | Lean/Z3 maps plus W1/W2; neighbor shell construction is separate |
| E3 | Prove harmonic monotonicity and `-D<=T<=D`. | GO for exact object | Lean rational theorem and real bridge; signed values allowed |
| E4 | Preserve `(+1,+1,-1,-1)` eligibility and exclude the heuristic. | source candidate present; integration open | source and mutation replay; heuristic remains general digamma |
| O1 | Bind exact schema-2 generator, fixture, sidecar, row order, and segment counts. | bounded core GO | digests and no-write generator replay; integrity is not authenticity |
| O2 | Derive 354 endpoints and the 240/114 split from rows. | bounded core GO | Python/Rust replay; metadata alone is insufficient |
| N1 | Reproduce `8*EPSILON`, 40 ties, first maximum, zero swap asymmetries. | bounded core GO; final compiled replay open | absolute nats over 8,198 rows; no universal/ULP claim |
| N2 | Reproduce `354 +0`, `0 -0`, and 150 selected-prefix ordinary-left nonzeros. | bounded core GO; final compiled replay open | selected Neumaier prefix only; naive-prefix 121 retained as contrast |
| W1 | Bridge ordered KSG counts `(4,1)` and radius `79` to `107/210`. | candidate source/test present; final replay open | one finite geometry witness |
| W2 | Bridge inclusive Ehrlich counts `(5,2)` to the same local target. | candidate source/test present; final replay open | public mean is eight ordered-binary64 positions from exact rounding |
| F1 | Check 19 Lean theorems and kill 14 semantic mutants. | GO on settled formal bytes | conditional exact arithmetic; no runtime proof |
| F2 | Check four Z3 obligations and expose 12 mutant countermodels. | GO on settled formal bytes | explicit premises; harmonic function uninterpreted |
| F3 | Account for formal shared cuts. | GO in formal note and claim | analytic premise, signs, maps, statements, human transcription |
| M1 | Replay selected fields at primes `1000033/1000037/1000081`. | GO on 8,198 rows | each field separately separates all 7,844 nonendpoints |
| M2 | Retain rejected-prime collision as a negative control. | GO | four exact-nonzero collisions at prime `1000003` |
| M3 | Kill 26 modular certificate mutations. | GO in normal and optimized Python | bounded certificate/custody adequacy only |
| C1 | Preserve every revision-1/2/3 packet byte and stale observations. | GO in candidate claim lane | active manifest and frozen hash replay |
| C2 | Require canonical active-packet custody and semantic validation. | active | `--claim-only` plus hash-first and resealed semantic mutations |
| P1 | Prove exact KSG-only Git phase isolation from the declared parent. | NO-GO | separate phase checker, protected projections, forbidden-wave mutations |
| R1 | Bind exactly 15 affected and 20 protected release objects. | NO-GO pending later integration lane | complete object projections, no combined PID2 strings |
| C3 | Bind the 21-node reverse closure minus one shared-config exclusion. | NO-GO pending catalog lane | exactly 20 affected and 49 protected method objects |
| A1 | Regenerate audience views and review registries from settled JSON. | NO-GO | moving-tree output is not credited |
| I1 | Rebind software identity to final package/catalog/source bytes. | NO-GO | identity is provenance, not scientific validity |
| Q1 | Run focused and complete repository gates on final staged bytes. | NO-GO | debug/release, serial/parallel, docs, lint, Python, CI/release audit |
| H1 | Adjudicate final source-blind and proof-blind hostile reviews. | NO-GO | review is advisory attack input, never authority |
| D1 | Create immutable evidence matrix and decision only after I1/Q1/H1. | deliberately absent | prevents a preclosure decision from masquerading as final evidence |
| G1 | Commit unsigned, push `main`, and bind the implementation commit by receipt. | NO-GO | Git anchors checker plus manifest without a digest cycle |

## Verification lenses

The packet binds at least nine lenses: object/domain; exact algebra and boundaries; formal proof;
modular certificate and countermodel; binary64/signed-zero/association; compiled dataflow and
serial/parallel; statistical/support non-implication; custody/catalog/release/identity; and
citation/object-firewall/downstream scope. These lenses share cuts explicitly; their count is not
treated as an independence count.

## Stop conditions

Do not convert an open integration row to GO from an ambient dirty-tree run, a model review, a
moving-file run, a hash without semantic replay, or a downstream assertion. Do not create final
revision-4 decision/evidence artifacts until all writers stop and every required route is replayed
on the exact isolated candidate.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/routes-v4.md`

SHA-256: `e14c3a54c81f84208f42b241b04d0feda3f32d0b1e62a32396c9e161ef5aa951`

```text
# Route registry for `KSG-INTEGER-HARMONIC-001`, revision 4

| Route | Mechanism | Strongest current result | Shared cut / limitation | State |
|---|---|---|---|---|
| R-DERIVE | first-principles exact algebra | typed four-sign cancellation, range identity, sharp signed bound | analytic digamma premise and index map | GO |
| R-FRACTION | Python exact rationals | all 6,920 exhaustive rows plus signed boundaries | human formula/domain | GO, bounded enumeration |
| R-LEAN-V4 | Lean/Mathlib kernel | 19 exact theorems; 14/14 semantic mutants killed | typed digamma premise, human signs/maps/statements | GO, scoped |
| R-Z3-V4 | QF_UFLIRA solver | four sat preflights/four unsat negations; 12/12 mutants expose sat countermodels | harmonics uninterpreted; local order premises explicit | GO, scoped |
| R-DECIMAL | standard-library Decimal generator | 8,198 schema-2 reference rows | endpoint branch shares exact cancellation | GO, bounded corpus |
| R-CUSTODY | no-write regeneration plus SHA-256 | generator/fixture/sidecar byte correspondence | integrity, not authenticity or mathematical proof | GO on settled core bytes |
| R-PY-B64 | independent Python binary64 replay | 8 eps absolute nats, 40 ties, no swap asymmetry, signed-zero/association counts | same fixture and host binary64 | GO, bounded corpus |
| R-RUST-CORPUS | compiled production helper | production conformance over corpus and endpoints | same fixture/helper/compiler lineage | candidate present; final replay open |
| R-W1 | finite production-private KSG diagnostic | radius 79, ordered counts `(4,1)`, exact target `107/210` | one fixed geometry | candidate present; final replay open |
| R-W2 | finite Ehrlich disjunction diagnostic | inclusive `(5,2)`, same local target, public propagation | one construction; no estimator theorem | candidate present; final replay open |
| R-MOD-SELECTED | three prime-field residue vectors | each field separately separates 7,844 nonendpoints; corpus-only iff | all share corpus/formula; triple is not CRT | GO, bounded certificate |
| R-MOD-REJECTED | rejected field and exact tail witnesses | four nonendpoint exact-nonzero zero-residue collisions | counterexample to residue-zero converse | GO, negative control |
| R-SOURCE | masked textual/dataflow checks | selected helper/call maps/heuristic exclusion | not AST/def-use/compiler refinement | candidate present; final replay open |
| R-SERIAL | fixed compiled output capture | 13 KSG-only regression constants | fixed inputs/toolchain | open |
| R-PARALLEL | parallel/thread-budget replay | bit equality with settled serial capture | scheduling diversity, not theorem independence | open |
| R-CLAIM-CUSTODY | canonical manifest plus semantic checker | immutable historical/active packet bytes and reviewed facts | Git must anchor checker plus manifest | active |
| R-PHASE | staged-tree parent/allowlist/projection checker | exclusion of PID2/I_min/frontier/PDF contamination | provenance only | open |
| R-CATALOG | reverse-dependency closure and protected projections | 20 affected / 49 protected when settled | metadata, not arithmetic proof | open |
| R-RELEASE | affected/protected family objects | 15 affected / 20 protected when settled | release identity, not validity | open |
| R-HOSTILE | native/Fable/Opus attacks | searches for falsifiers and scope defects | advisory; agreement closes nothing | final pass open |

## Independence accounting

Lean and Z3 have different execution engines but share the analytic premise, signs, index map, and
chosen statements. Decimal, Python binary64, Rust corpus, and modular routes share the frozen row
specification. The three selected primes share the same formula, corpus, and generator class;
their role is redundant fault diversity, not three independent proofs and not CRT. Debug/release,
serial/parallel, and normal/optimized Python are execution-profile diversity. External model names
do not supply evidence without a replayable derivation, counterexample, or test.

## Negative and rejected routes retained

- schema-1 Decimal endpoint residuals and noncanonical zero spellings;
- the revision-1 association-label and 40-tie correction;
- stale serial/parallel regression values;
- live source shadow/overwrite counterexamples;
- KSG/PID2/I_min release-phase conflation;
- revision-3 custody/formal-bound/inventory preclosure failures;
- selected-Neumaier-prefix 150 versus naive-prefix 121 discriminator;
- rejected prime `1000003` with four exact-nonzero zero-residue collisions; and
- the forbidden inferences from exact arithmetic to KSG/Ehrlich/MGW/PID validity.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md`

SHA-256: `e14654f5b27273fefc0f9395f105c2e549ee4a281122579e722b47dc96e6d97d`

```text
# Behavioral witnesses for `KSG-INTEGER-HARMONIC-001`, revision 4

## W0 — smallest signed-boundary witness

In the pure helper domain take `n=2,k=1`, so `D=H_1-H_0=1`. Then:

```text
(x,y)=(1,1) -> +1 = +D
(x,y)=(2,2) -> -1 = -D
(x,y)=(1,2) or (2,1) -> 0.
```

This proves the two-sided bound is attained at the smallest domain boundary and refutes
nonnegativity or silent clamping. It is exact arithmetic, not a claim that all four count
configurations arise from every neighbor geometry.

## W1 — ordered exclusive KSG bridge

Use `n=8`, `k=2` and the fixed one-dimensional source/target rows retained in revisions 2 and 3.
The production-private diagnostic at zero-based row 5 must report:

```text
joint radius = 79
exclusive marginal counts = (nx,ny) = (4,1)
helper arguments = (2,8,5,2)
exact-real local term = H_7-H_4 = 107/210
selected bits = 0x3fe04e04e04e04e0.
```

The ordered count assertion matters because the public scalar and helper are source symmetric; a
swapped implementation could otherwise preserve that scalar. Brute-force and kd-tree backends
must produce the same ordered diagnostic. This finite bridge does not prove neighbor correctness
outside the fixture.

## W2 — anchor-inclusive Ehrlich bridge

Reuse W1 as source 1 and target, and set `s2[i]=1000*s1[i]+i`. The source disjunction distance
reduces to source 1's distance on every pair. At the same zero-based row 5 the anchor-inclusive
counts are:

```text
n_alpha = 5
n_t = 2
helper arguments = (2,8,5,2)
exact-real local term = 107/210
selected local bits = 0x3fe04e04e04e04e0.
```

The public compensated mean has bits `0x3fb5a35a35a35a3e`; the correctly rounded exact `71/840`
has bits `0x3fb5a35a35a35a36`. Their unsigned encodings differ by eight
ordered-binary64 positions. This wording does not assert eight ULPs or an estimator-error bound.

## W3 — 354 structural endpoint cancellations

For a fixture row satisfying

```text
{nx,ny} = {k-1,n-1},
```

the exact four-harmonic multiset cancels pairwise. Schema 2 contains 354 such rows: 240 exhaustive
and 114 stress. Every reference is canonical string `"0"`; the selected range route produces
354 `+0` outputs and zero `-0` outputs.

The selected Neumaier-prefix ordinary-left route is nonzero on 150/354 endpoints and has zero
negative-zero outputs. A naive-prefix route gives 121/354. Therefore an association count must
name its prefix; neither observation is a universal signed-zero theorem.

## W4 — selected modular separation

For each prime below, u32 big-endian residues are stored in fixture order:

| Prime | Endpoint zeros | Nonendpoint nonzeros | Residue-vector SHA-256 |
|---:|---:|---:|---|
| `1000033` | `354` | `7844` | `931c30fab8560d5692121f3c16be42afa4e9d0b73e640ca4285f5352f4cfff9b` |
| `1000037` | `354` | `7844` | `09b6d9e5a4f9f5ee4346dbfc869ba254710f6198cba97f2ac3449db8adb16479` |
| `1000081` | `354` | `7844` | `20b2596be7ed67e9fb07039465196da9c289f87d0e13b87d85e8bcf964b18de0` |

Every prime exceeds the maximum harmonic denominator `999999`, so denominators are invertible and
a nonzero residue proves exact rational nonzero. The corpus-only iff combines that one-way
implication for nonendpoints with structural pair cancellation for endpoints.

## W5 — rejected-prime counterexamples

Prime `1000003` has residue-vector digest
`d90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111`
and four nonendpoint zero-residue collisions:

| Zero-based index | `(n,k,nx,ny)` | Exact sign |
|---:|---|---|
| `8045` | `(1000000,3,2,3)` | positive |
| `8049` | `(1000000,3,3,2)` | positive |
| `8069` | `(1000000,4,3,3)` | positive |
| `8093` | `(1000000,4,999999,999999)` | negative |

The first three reduce to a strictly positive reciprocal tail and the fourth to its negative.
Thus zero modular residue does not imply exact zero. The selected triple is redundant fault
diversity, not CRT.

## Common firewall

W0--W5 concern exact/local arithmetic and finite implementation bridges. They do not prove KSG MI
consistency, continuous Ehrlich shared-exclusions calibration, continuous PID2 atoms, categorical
MGW SxPID, `I_min`, fitted quantized SxPID, heuristic correctness, PID3 validity, support,
application suitability, or consumer readiness.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md`

SHA-256: `d7c87b91e8bd4b43d86d08361f0b73df48f4d6ecb97d459f48ecb506f7f3d3e5`

```text
# Implementation and correspondence map for `KSG-INTEGER-HARMONIC-001`, revision 4

## Production arithmetic candidate

`crates/pid-core/src/stats.rs` constructs `table[m]=H_(m-1)` using a deterministic
Neumaier-compensated positive prefix and evaluates:

```text
(table[n] - table[max(x,y)]) - (table[min(x,y)] - table[k]).
```

Eligible exclusive KSG callers pass `nx+1,ny+1`. Eligible anchor-inclusive Ehrlich ISX/PID3
callers pass their counts directly. The non-cancelling heuristic retains general digamma
arithmetic. No public signature, shell rule, support contract, estimator definition, or
information unit changes.

This map is a candidate correspondence until final source, compiled, serial/parallel, and staged
tree gates pass. Text markers are bounded guards, not compiler def-use proofs.

## Exact/formal files

| Layer | Active artifact | Scoped result |
|---|---|---|
| historical Lean | `audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean` | exact retained revision-2 bytes |
| active Lean | `audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean` | 19 theorem declarations |
| Lean checker | `scripts/check-lean-ksg-integer-harmonic.py` | pinned environment/source/axiom inventory |
| Lean mutations | `scripts/check-lean-ksg-integer-harmonic-self-test.py` | 14/14 semantic kills |
| Z3 obligations | `audit/formal/z3-ksg-harmonic/*.smt2` | four conditional exact obligations |
| Z3 checker | `scripts/check-z3-ksg-integer-harmonic.py` | sat-preflight then unsat-negation |
| Z3 mutations | `scripts/check-z3-ksg-integer-harmonic-self-test.py` | 12/12 satisfiable countermodels |

The formal layer does not represent Rust, binary64, neighbor geometry, estimator statistics, or
PID objects.

## Bounded oracle and modular files

| Artifact | SHA-256 |
|---|---|
| `scripts/generate-ksg-local-arithmetic-oracle.py` | `a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b` |
| schema-2 fixture | `560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c` |
| fixture sidecar file | `fb91172bdb767b3e11e15ef4e89bb0482b932c5c2450f87d566245eda87a8ec7` |
| modular generator | `48bff86ad0a89f80dce0452fe032c91edea7f07b7979ec07aabe5ecf2c6a574b` |
| modular certificate | `ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102` |
| modular sidecar file | `017a5ee3bd19ad1765b3f9499a65a95602af64577f5120b7af8e4ac1d6f1b7d9` |
| modular checker | `561f6c2fe25b5b54fd87f1c5b210b5cca55afda75b3b139ba5078269166aa755` |
| modular self-test | `c6376ab07d714a7d732568d589e73e01377cffdbcf163340e9866dfadda7eac4` |

The modular checker independently recomputes prime admissibility, inverse residues, segment
counts, residue digests, collision witnesses, canonical bytes, and implication direction. Its
26-mutant suite covers prime/domain, residue/encoding, endpoint/split, prime inventory, custody,
schema/canonicality, and claim-boundary/collision faults.

## Claim custody

The current preclosure `active-packet-v4.json` is canonical UTF-8 JSON with a sorted
path-to-SHA-256 map, exactly one
active revision, scalar facts, historical hashes, open gates, and the object firewall. It excludes
itself and the claim checker/self-test to avoid a digest cycle. The checker pins the manifest
digest; the eventual Git commit anchors both sides.

This is not the immutable final M1c packet. After final `evidence-matrix-v4.md` and
`decision-v4.md` are truthfully created, the manifest and its checker pin must be regenerated on
settled bytes to include them.

Claim-only semantic mutations first demonstrate failure against the unchanged envelope, then
update the changed leaf hash and the unavoidable manifest digest in the checker. A second semantic
failure is required. This is one resealed envelope operation, not falsely advertised as one
independent hash.

## Integration phase boundary

The KSG-only release must be synthesized from the declared pushed parent. Shared files are rebuilt
from that parent plus reviewed KSG hunks. Later PID2 represented-sum, I_min, categorical frontier,
unrelated formal/PDF, and combined identity bytes are excluded.

Exactly 15 release families may advance to KSG-only revisions; 20 remain protected. Catalog
closure is the 21-node reverse dependency closure from two KSG roots minus the single
non-numerical shared-config object, yielding 20 affected and 49 protected methods. These rows are
requirements, not completed evidence in this preclosure document.

## Required replay before final decision

Run normal and optimized claim, formal, modular, generator, exact, binary64, source, catalog, and
release checkers; debug/release focused Rust tests; brute/kd-tree W1; serial/parallel/thread
identity; format, clippy, rustdoc, stable/no-default/all-feature debug/release; Python bindings;
review/ecosystem/identity/release audits; and phase-isolation mutations. Rerun after the last byte
change. Runs made while any input moved are not evidence.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md`

SHA-256: `61e81c0812978ad8d806a7ab836a103d26b52061094bbb38d8ca3c3460834b11`

```text
# Correction ledger for `KSG-INTEGER-HARMONIC-001`, revision 4

Revision 4 is post-result integration. These entries do not rewrite revisions 1--3.

## C10 — revision-3 packet was not in checker custody

- **Detector:** deletion/edit thought experiments and hostile preclosure audit.
- **Failure:** arithmetic/catalog routes could remain green after changing claim prose.
- **Correction:** canonical active manifest, exact file set/digests, regular non-symlink paths,
  exactly one active revision, semantic invariants, and hash-rebased semantic mutations.
- **Residual:** SHA-256/Git provide custody, not authenticity or scientific truth.

## C11 — revision index described revision 2 as active

- **Detector:** direct index inspection.
- **Failure:** live chronology disagreed with frozen revision-3 files.
- **Correction:** preserve the stale bytes as `revision-index-pre-v4.md`; make the live index name
  revisions 3 and 4 truthfully.
- **Residual:** historical revision-3 completion remained NO-GO and is not backfilled.

## C12 — formal bound exceeded the frozen revision-3 encoding

- **Detector:** theorem/source inventory comparison.
- **Failure:** revision-3 prose attributed `-D<=T<=D` to formal files that lacked monotonicity and
  bound theorems.
- **Correction:** retain revision-3 bytes; add a revision-scoped Lean v4 source with the rational
  monotonicity, rational bound, rational-to-real bridge, and combined real theorem; add a fourth
  premise-explicit Z3 obligation.
- **Residual:** digamma truth is typed; Z3 order facts are premises; no runtime proof follows.

## C13 — formal mutation inventory advanced

- **Observed:** Lean closes at 19 theorems/14 mutants; Z3 closes at four obligations/12 mutants,
  including reversal of the middle order premise.
- **Correction:** revision-4 documents bind these settled counts and source/checker hashes.
- **Residual:** mutation kills establish load-bearing checks, not theorem-to-program refinement.

## C14 — endpoint association wording omitted the prefix

- **Detector:** selected Neumaier prefix and naive prefix yield 150 and 121 ordinary-left nonzeros.
- **Correction:** every revision-4 statement says “selected-Neumaier-prefix ordinary-left” for
  150/354 and binds zero negative zeros.
- **Residual:** neither count is a universal signed-zero theorem.

## C15 — structural endpoint sufficiency was not a corpus-wide iff

- **Detector:** exact residue exploration.
- **Result:** each of three selected prime fields separates every one of the 7,844 frozen
  nonendpoints, while structural cancellation covers all 354 endpoints.
- **Correction:** promote only the **frozen-corpus** iff via the canonical modular certificate.
- **Residual:** no universal harmonic-zero classification is asserted.

## C16 — an earlier modular digest had no retained schema

- **Observed:** `1d5f61b...` described a pre-artifact computation but had no canonical retained
  byte schema.
- **Correction:** classify it as historical observation only. The final certificate digest is
  `ae4645c3...`.
- **Residual:** internal generator/checker diversity is not external custody.

## C17 — zero-residue converse is false

- **Detector:** rejected prime `1000003`.
- **Smallest retained corpus witnesses:** zero-based indices 8045, 8049, 8069, and 8093 are exact
  nonzero but have zero residue.
- **Correction:** only nonzero residue implies exact nonzero; retain exact reciprocal-tail signs.
- **Residual:** selected primes are separators for this corpus, not CRT or a universal theorem.

## C18 — “eight” had two incompatible numerical meanings

- **Failure:** `8*EPSILON` absolute nats and W2's eight integer-encoding steps could be conflated
  with ULP claims.
- **Correction:** call the former absolute error in nats and the latter ordered-binary64 positions.
- **Residual:** neither is a universal binary64 or estimator error theorem.

## C19 — bounded core GO could be mistaken for release GO

- **Detector:** two-parent/dirty-tree phase audit.
- **Correction:** status is `integration_no_go`; catalog, release, audience, identity, phase,
  compiled/full CI, hostile review, final evidence matrix, decision, commit, and receipt remain
  open.
- **Residual:** no ambient-tree green run can close an isolated-candidate obligation.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md`

SHA-256: `0e9a04456a6d60ed151e5bd764e5a08060c83024c1731311234907a1db2e805d`

```text
# Preclosure integration disposition for `KSG-INTEGER-HARMONIC-001`, revision 4

## Current decision boundary

```text
exact positive-integer arithmetic core                    GO
scoped Lean 19-theorem / 14-mutation route                GO
scoped Z3 4-obligation / 12-mutation route                GO
bounded 8,198-row modular / 26-mutation certificate       GO
repository and publication integration                    NO-GO
```

This is a preclosure disposition, not `decision-v4.md`. Revision 4 is post-result integration and
is not preregistered. Immutable final `evidence-matrix-v4.md` and `decision-v4.md` are deliberately
absent until all integration evidence is settled.

The current `active-packet-v4.json` is therefore a preclosure-core manifest. It must be regenerated
at M1c to include the final evidence matrix and decision after those artifacts exist; today's
manifest is not represented as the immutable final packet.

## Why integration remains NO-GO

The following are open and conjunctive:

1. claim-only custody and its normal/optimized mutation suite must pass on final packet bytes;
2. exact Git phase isolation must prove the candidate is based on the declared pushed parent and
   excludes PID2 represented-sum, I_min, frontier, PDF, and combined identity contamination;
3. source and fixture work must survive focused compiled debug/release tests;
4. W1 ordered brute/kd-tree counts and W2 inclusive propagation must replay;
5. 13 KSG-only serial constants must be freshly captured and parallel/thread replay must match;
6. catalog closure must bind exactly 20 affected methods while protecting 49 methods, all
   references, and top metadata;
7. release closure must bind exactly 15 affected and 20 protected full family objects, with no
   later combined PID2 strings;
8. generated methods/release Markdown, review evidence, dispositions, assurance registry,
   ecosystem capabilities, and software identity must be regenerated from settled source/JSON;
9. full format, lint, docs, Rust feature/debug/release, Python, identity, review, release, and CI
   gates must pass after every writer stops;
10. final source-blind and proof-blind hostile reviews must be independently adjudicated; and
11. an unsigned no-attribution commit must be pushed to `main`, followed by a receipt when needed
    to bind the implementation commit without self-reference.

## Nine-lens adjudication

| Lens | Current evidence | Open boundary |
|---|---|---|
| object/domain | exact KSG local arithmetic, domains/maps/units frozen | no transfer to estimators/PID |
| exact algebra | identity, signed sharp bound, W0 boundary | analytic digamma source authority remains a premise |
| formal | Lean/Z3 scoped routes and shared cuts | no program refinement |
| certificate | corpus-only modular iff and rejected collision | no universal zero theorem |
| binary64 | 8 eps absolute nats, 40 ties, signed-zero and association facts | no universal/platform theorem |
| compiled/dataflow | candidate helper, W1/W2/source checks | settled debug/release/serial/parallel replay |
| statistical/support | explicit non-implications | no calibration/consistency/support promotion |
| provenance/release | historical bytes and manifest design | phase/catalog/release/audience/identity closure |
| object firewall/downstream | KSG/Ehrlich/MGW/Imin/quantized/heuristic/PID3/wrapper separation | no consumer qualification |

The lenses are complementary but correlated. Their number is not an independence claim.

## Promotion rule

Do not rename this disposition or create a final decision merely because the bounded core is
green. Repository integration becomes eligible for GO only when every open item above has exact
settled-tree receipts and no unresolved hostile-review finding. A failure is retained and routed
to the smallest obligation; gates are not weakened to obtain a green result.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md`

SHA-256: `45813b90cc15c6880ca9df83419851a7bb80adb4100963ff4c2322493d4eb905`

```text
# Formal assurance for `KSG-INTEGER-HARMONIC-001` revision 4

## Disposition

Evidence label: **theorem proved under stated assumptions** for 19 exact Lean theorems, with four
independently encoded conditional QF_UFLIRA obligations checked by Z3. This is not end-to-end
formal verification. The analytic positive-integer digamma identity is still a typed premise, and
the implementation/refinement, neighbor-geometry, binary64, estimator, support, PID, and
application layers remain outside both formal systems.

## Revision-preserving source custody

The first revision-2 Lean result is retained byte-for-byte at
`../../audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean`:

```text
812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943
```

Revision 4 does not rewrite that source. Its canonical extended source is
`../../audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean`, with SHA-256:

```text
32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4
```

The pre-existing unversioned path
`../../audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean` retains the exact revision-2
bytes. The checker requires both historical revision-2 paths to have the displayed hash and
identical bytes; the active revision-4 extension exists only at its revision-scoped path.

## Lean route

Pinned environment:

| Artifact | Identity |
|---|---|
| Lean toolchain | `leanprover/lean4:v4.32.0` |
| Lean source commit | `8c9756b28d64dab099da31a4c09229a9e6a2ef35` |
| `audit/formal/lean/lean-toolchain` | `2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e` |
| `audit/formal/lean/lakefile.toml` | `1c3f1818c4a62ab48f4ae05de573f6d884aaf7f7397a21646df162151cfccdf1` |
| `audit/formal/lean/lake-manifest.json` | `e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd` |
| Mathlib source revision | `81a5d257c8e410db227a6665ed08f64fea08e997` |
| revision-4 proof source | digest pinned by the revision-4 checker |

The checker validates every manifest package checkout's root, exact revision, recorded origin, and
clean status under isolated Git configuration. It checks the exact Lean version and source commit,
the source/import inventory, proof-escape exclusions, scope sentinels, theorem declarations, and
the complete `#print axioms` result. Only `propext`, `Classical.choice`, and `Quot.sound` are
permitted.

The 14 retained revision-2 conclusions cover the rational finite-sum definition and recurrence,
four-sign cancellation conditional on `PositiveIntegerDigammaPremise`, direct/range equality,
source symmetry, exclusive successor, inclusive identity, argument bounds, and both count-index
maps. Revision 4 adds five kernel-checked conclusions:

1. universal monotonicity of the exact rational harmonic finite sum;
2. preservation of the range expression under the rational-to-real order embedding;
3. nonnegativity and full-tail upper bounds for both selected harmonic ranges;
4. the two-sided rational bound
   `-(H_(n-1)-H_(k-1)) <= T <= H_(n-1)-H_(k-1)`; and
5. one combined real theorem that explicitly composes the typed digamma premise, four-sign
   cancellation, direct-to-range identity, rational-to-real coercion, and both real inequalities.

The combined theorem assumes natural indices satisfying

```text
1 <= k <= n
k <= x <= n
k <= y <= n.
```

The estimator-facing claim remains on the stricter common domain `1 <= k < n`. Proving a theorem
on the slightly larger `k=n` arithmetic domain does not assert that a runtime estimator accepts
that endpoint.

The baseline-first Lean self-test compiles the unmodified source and kills 14 semantic mutations.
The five new kills reverse harmonic monotonicity, corrupt the rational-to-real bridge, strengthen a
zero tail to one, reverse the rational lower bound, and offset the combined real conclusion. The
nine retained kills cover the denominator, min/max, coefficient signs, source swap, exclusive and
inclusive maps, bounds, and the direct exclusive index.

## Z3 route

The checker requires exact `Z3 version 4.16.0 - 64 bit`. CI obtains the official
`z3-4.16.0-x64-glibc-2.39.zip` archive and verifies SHA-256
`7288c49a5bd6dbafd7b0b0d1f65956b91672da24b08f09242919af159be3418e`
before placing its executable on `PATH`.

| Script | Conditional obligation | SHA-256 |
|---|---|---|
| `ksg-digamma-cancellation.smt2` | four-sign cancellation under four explicit digamma instances | `8ae66c11fb66541bc47766b2682cf1e53d9b656aa0fa12e6945ac22057816ed4` |
| `ksg-index-maps.smt2` | exclusive successor, inclusive identity, bounds, and harmonic indices | `71ea8db97df43f51da89496a5e799bedc6216f9ede40368207d2ffed8df40fe1` |
| `ksg-symmetric-range.smt2` | direct/range equality and source exchange for arbitrary harmonic values | `add0fc3a371c65433fdfd8b1e51d3182c6ef78db0cfd1d372f461f1d030e19a9` |
| `ksg-local-bound-v4.smt2` | direct/range equality and the full-tail bound under explicit local harmonic-order premises | `33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31` |

For each script, the checker requires the positive formulation to be exactly `sat` before requiring
the negated obligation to be exactly `unsat`. This excludes vacuity from an inconsistent premise
set. The revision-4 bound script explicitly assumes only the three local instances

```text
H_(k-1) <= H_(min(x,y)-1) <= H_(max(x,y)-1) <= H_(n-1).
```

Z3 does not prove those harmonic-order premises. Lean independently proves universal monotonicity
for the exact rational harmonic definition. This division is deliberate and must not be described
as two independent proofs of harmonic monotonicity.

The Z3 self-test retains eight cancellation/range/index mutants and adds four bound mutants: a
strictly tightened lower conclusion and reversals of the lower, middle, and upper harmonic-order
premises. All 12 must expose a satisfiable countermodel. Z3 emits solver results, not proof
certificates checked by a smaller independent kernel.

## Shared cuts and prohibited promotions

Lean and Z3 share the chosen theorem statements, the human `(+1,+1,-1,-1)` sign transcription, the
exclusive successor/inclusive identity map, and the analytic positive-integer digamma premise.
Their engine diversity cannot close an error in one of those shared inputs. In particular:

- neither route constructs the analytic digamma function or proves
  `psi(m)=H_(m-1)-gamma`;
- neither proves that neighbor code produced counts in the formal domains;
- neither represents the selected Rust prefix/reassociation or any binary64 error;
- neither proves KSG/Ehrlich consistency, calibration, or support validity; and
- neither proves a Makkeh--Gutknecht--Wibral shared-exclusions functional or any PID atom.

The exact bound permits negative local terms. It is an arithmetic bound in nats after the typed
digamma bridge, not a bound on mutual information, redundancy, a PID atom, estimator bias, or
application error.

## Required replay

```text
python3 scripts/check-lean-ksg-integer-harmonic.py
python3 -O scripts/check-lean-ksg-integer-harmonic.py
python3 scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 -O scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 scripts/check-z3-ksg-integer-harmonic.py
python3 -O scripts/check-z3-ksg-integer-harmonic.py
python3 scripts/check-z3-ksg-integer-harmonic-self-test.py
python3 -O scripts/check-z3-ksg-integer-harmonic-self-test.py
```

Closure requires 19 Lean theorem inventories, 14/14 killed Lean semantic mutations, four exact Z3
positive `sat` preflights, four exact negated `unsat` results, and 12/12 Z3 mutants returning exact
`sat` under both normal and optimized Python execution.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md`

SHA-256: `04335c39cdbd409bd987805b3dc0d540bb5514d19d807a08940286d43770ca3c`

```text
# Retained negative control: modular zero-residue collisions

## Refuted inference

The inference

```text
T mod p = 0  =>  exact rational T = 0
```

is false even when prime `p` exceeds every harmonic denominator in the frozen row.

## Counterexamples

For rejected prime `p=1000003`, the ordered u32 big-endian residue-vector digest is

```text
d90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111.
```

Four nonendpoint rows have zero residue:

```text
index 8045: (1000000,3,2,3),         T =  H_999999 - H_3 > 0
index 8049: (1000000,3,3,2),         T =  H_999999 - H_3 > 0
index 8069: (1000000,4,3,3),         T =  H_999999 - H_3 > 0
index 8093: (1000000,4,999999,999999), T = H_3 - H_999999 < 0.
```

The strict signs follow because `sum_(j=4)^999999 1/j` is a nonempty sum of positive rationals.
These are exact counterexamples, not binary64 observations.

## Accepted implication

If `p` exceeds every denominator then all denominators are invertible in the field. Exact rational
zero must reduce to residue zero. Therefore the contrapositive is sound:

```text
nonzero residue => exact rational nonzero.
```

The converse is not sound. Selected primes `1000033`, `1000037`, and `1000081` happen to have
nonzero residue at all 7,844 frozen nonendpoints. Combining that bounded separation with pairwise
structural cancellation proves an iff only for the exact ordered 8,198-row corpus.

## Independence and non-implications

The selected triple provides redundant fault diversity. It is not CRT reconstruction and the
three fields are not three independent mathematical proofs: they share the row corpus, exact
formula, human index map, and generator class. The result classifies no harmonic zeros outside the
corpus and proves nothing about KSG neighbor geometry, MI estimation, Ehrlich shared exclusions,
MGW SxPID, any PID atom, support, calibration, or applications.

The pre-artifact digest
`1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc`
is retained only as a first observation. Canonical final custody is
`ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102`.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md`

SHA-256: `565e18922514123942dd4d241c2d677be27101c3402f6fb594dc699641eae071`

```text
# Revision-3 pre-closure audit findings

## Classification

**Result: NO-GO for revision-3 completion; retained negative assurance result.**

Revision 3 was frozen before its evidence matrix or decision existed. Hostile review then found
that its arithmetic core was supported but several completion and custody statements were not yet
true. The frozen revision-3 files are not edited to conceal that chronology. Revision 4 must close
or explicitly weaken every item below.

## Findings

1. **No claim-packet custody route.** The KSG checker recognized evidence-path strings but did not
   hash or semantically validate the revision-3 claim, obligations, routes, formal boundary,
   implementation note, correction ledger, or failures. Deleting or changing those files could
   leave the arithmetic, catalog, and release routes green.
2. **Stale revision index.** `revision-index.md` named revision 2 as active and contained no
   revision-3 hashes. Git retention alone did not satisfy revision 3's stronger D1 wording.
3. **Formal bound overstatement.** The revision-3 prose attributed the exact `-D <= T <= D` bound
   to formal routes, while the frozen Lean source proved algebra/index consequences but no
   harmonic monotonicity or bound theorem, and the three Z3 files had no premises sufficient to
   derive harmonic-value bounds.
4. **Historical Lean custody gap.** The only live untracked Lean path was edited after a
   revision-2 document had pinned its earlier SHA-256. Until identical revision-2 bytes were
   retained separately, Git history did not preserve the pinned source.
5. **Mutation inventory drift.** The retained first result was 85 mutations, followed by observed
   91, 99, 129, and 133-state runs while routes were still moving. None was a final revision-3
   inventory, and no final result may be selected retrospectively from those runs.
6. **Ambiguous W3 wording.** The 150/354 ordinary-left nonzero observation uses the selected
   Neumaier prefix table. With a naive prefix the corresponding count is 121/354. An unqualified
   “ordinary left association” therefore failed to identify the prefix path.
7. **Endpoint split was trusted by consumers.** The generator recomputed the 240 exhaustive and
   114 stress endpoint rows, but the Python checker and Rust corpus test initially asserted split
   metadata rather than deriving both counts from fixture rows.
8. **Ordered W1 production gap.** The external integration test independently derived row 5's
   ordered counts `(4,1)`, but the public local scalar is source-symmetric. No production-private
   diagnostic assertion initially proved that the implementation itself produced that order.
9. **Release/catalog projections were incomplete.** Revision fields were checked, but unrelated
   fields in affected release objects, top-level release metadata, protected catalog methods,
   catalog references, and catalog metadata were not all exact negative controls. The 20 catalog
   bindings were also hard-coded without deriving the 21-node reverse dependency closure and its
   single non-numerical shared-config exclusion.
10. **Evidence-path existence was not enforced.** Catalog validation required path strings but did
    not require their targets to be regular repository files.
11. **KSG-only phase isolation was not machine enforced.** The ambient worktree also contained
    later PID2 exact-sum and I_min work. A green KSG source route did not prove that a proposed Git
    tree excluded those changes, including unrelated hunks in shared `stats.rs` and parallel-oracle
    files.
12. **Audience evidence remained stale.** Generated `METHODS.md`, release-scope Markdown,
    review-evidence records, dispositions, assurance registry, and software-identity hashes still
    referred to earlier KSG evidence or pre-migration bytes.

## Required revision-4 response

Revision 4 must preserve this failure, retain the exact historical Lean bytes, prove only the
formal statements actually encoded (including any rational-to-real bridge it claims), add
hash-first and semantic claim custody with hash-rebased semantic mutants, recompute endpoint split
counts in both consumers, bind ordered W1 diagnostics in production, freeze the selected-prefix
150/354 result in executable routes, use full-object release/catalog projections and derived
dependency closure, require evidence targets to exist, and validate an isolated Git candidate
derived from the declared parent. Generated audience and identity artifacts must be rebuilt only
after every writer has settled.

No item here changes the KSG estimator definition or the Makkeh--Gutknecht--Wibral PID functional.
This is a correction to pid-rs evidence and release claims.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md`

SHA-256: `062d51b03cbcfbfee9a16cba1e29ba3cb83480e6e48e603788828f917b08db25`

```text
# Formal assurance for `KSG-INTEGER-HARMONIC-001` revision 3

## Lean route

The pinned Lean package proves 14 narrow exact theorems covering finite harmonic sums, recurrence,
the four-term/range identity, source symmetry, exact-real bounds, and exclusive/inclusive index
consequences. The integer-digamma theorem is a typed premise. The route contains no Rust semantics,
floating-point model, neighbor geometry, support model, estimator, PID lattice, or MGW functional.

The Lean mutation suite must reject nine named changes to the denominator, min/max ranges, signs,
successor/identity maps, and bounds. Mutation kills establish load-bearing use of those statements;
they do not prove the analytic premise.

## Z3 route

The pinned Z3 package checks three QF_UFLIRA obligations by showing the positive formulation
satisfiable and its negation unsatisfiable under explicit premises. Harmonic values are supplied by
an uninterpreted function. The route proves linear/range consequences of premises, not harmonic
analysis. The mutation suite must reject eight named premise/conclusion changes.

Z3 output is a solver result, not a proof certificate checked by a smaller independent kernel.

## Shared-cut accounting

Lean and Z3 share:

- the analytic positive-integer digamma premise;
- the human `(+1,+1,-1,-1)` sign transcription;
- the exclusive successor and inclusive identity correspondence; and
- the chosen theorem/domain statements.

They are different execution engines, but agreement cannot close a defect in a shared premise or
mapping. Exact `Fraction`, behavioral W1/W2, source checks, and compiled corpus tests attack other
parts of the chain without proving the analytic premise from first principles.

## Formal non-claims

Revision 3 does not call this end-to-end formal verification. It does not prove Rust refinement,
binary64 error, generator correctness, neighbor search, estimator consistency, shared-exclusions
validity, PID atoms, or application conclusions.
```

## Artifact: `claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json`

SHA-256: `ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102`

```text
{
  "certificate_revision": 1,
  "claim_id": "KSG-INTEGER-HARMONIC-001",
  "corpus": {
    "fixture": {
      "path": "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json",
      "schema": "pid-rs/ksg-local-arithmetic-oracle",
      "schema_revision": 2,
      "sha256": "560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c"
    },
    "maximum_harmonic_denominator": 999999,
    "ordered_row_count": 8198,
    "segments": [
      {
        "end_index_exclusive": 6920,
        "endpoint_count": 240,
        "name": "exhaustive",
        "nonendpoint_count": 6680,
        "row_count": 6920,
        "start_index_inclusive": 0
      },
      {
        "end_index_exclusive": 8198,
        "endpoint_count": 114,
        "name": "stress",
        "nonendpoint_count": 1164,
        "row_count": 1278,
        "start_index_inclusive": 6920
      }
    ]
  },
  "generator": {
    "algorithm": "linear modular-inverse recurrence followed by harmonic prefix accumulation",
    "imports_pid_rs": false,
    "path": "scripts/generate-ksg-harmonic-modular-certificate.py",
    "sha256": "48bff86ad0a89f80dce0452fe032c91edea7f07b7979ec07aabe5ecf2c6a574b",
    "third_party_dependencies": []
  },
  "limitations": [
    "the iff classification is limited to the exact ordered 8,198-row frozen corpus",
    "the selected triple is redundant fault diversity, not a CRT or universal-zero theorem",
    "a zero residue alone does not prove that an exact rational is zero",
    "the route proves no estimator consistency, support, bias, PID-atom, or application claim",
    "generator/checker diversity is internal evidence, not independent external review"
  ],
  "pre_artifact_observation": {
    "sha256": "1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc",
    "status": "historical_first_result_only_not_final_artifact_custody"
  },
  "rejected_prime_negative_control": {
    "classification": "rejected_nonendpoint_collision_negative_control",
    "collisions": [
      {
        "exact_reduction": "H_999999 - H_3",
        "fixture_index_zero_based": 8045,
        "fixture_ordinal_one_based": 8046,
        "harmonic_difference": {
          "negative_coefficient_index": 3,
          "positive_coefficient_index": 999999
        },
        "row": {
          "k": 3,
          "sample_count": 1000000,
          "x_count": 2,
          "y_count": 3
        },
        "sign": "positive",
        "strict_nonzero_witness": {
          "exact_form": "1 * sum_(j=4..999999) 1/j",
          "first_denominator": 4,
          "last_denominator": 999999,
          "tail_coefficient": 1,
          "term_sign_reason": "every reciprocal in the nonempty tail is strictly positive"
        }
      },
      {
        "exact_reduction": "H_999999 - H_3",
        "fixture_index_zero_based": 8049,
        "fixture_ordinal_one_based": 8050,
        "harmonic_difference": {
          "negative_coefficient_index": 3,
          "positive_coefficient_index": 999999
        },
        "row": {
          "k": 3,
          "sample_count": 1000000,
          "x_count": 3,
          "y_count": 2
        },
        "sign": "positive",
        "strict_nonzero_witness": {
          "exact_form": "1 * sum_(j=4..999999) 1/j",
          "first_denominator": 4,
          "last_denominator": 999999,
          "tail_coefficient": 1,
          "term_sign_reason": "every reciprocal in the nonempty tail is strictly positive"
        }
      },
      {
        "exact_reduction": "H_999999 - H_3",
        "fixture_index_zero_based": 8069,
        "fixture_ordinal_one_based": 8070,
        "harmonic_difference": {
          "negative_coefficient_index": 3,
          "positive_coefficient_index": 999999
        },
        "row": {
          "k": 4,
          "sample_count": 1000000,
          "x_count": 3,
          "y_count": 3
        },
        "sign": "positive",
        "strict_nonzero_witness": {
          "exact_form": "1 * sum_(j=4..999999) 1/j",
          "first_denominator": 4,
          "last_denominator": 999999,
          "tail_coefficient": 1,
          "term_sign_reason": "every reciprocal in the nonempty tail is strictly positive"
        }
      },
      {
        "exact_reduction": "H_3 - H_999999",
        "fixture_index_zero_based": 8093,
        "fixture_ordinal_one_based": 8094,
        "harmonic_difference": {
          "negative_coefficient_index": 999999,
          "positive_coefficient_index": 3
        },
        "row": {
          "k": 4,
          "sample_count": 1000000,
          "x_count": 999999,
          "y_count": 999999
        },
        "sign": "negative",
        "strict_nonzero_witness": {
          "exact_form": "-1 * sum_(j=4..999999) 1/j",
          "first_denominator": 4,
          "last_denominator": 999999,
          "tail_coefficient": -1,
          "term_sign_reason": "every reciprocal in the nonempty tail is strictly positive"
        }
      }
    ],
    "counts": {
      "exhaustive": {
        "endpoint_count": 240,
        "endpoint_nonzero_count": 0,
        "endpoint_zero_count": 240,
        "nonendpoint_count": 6680,
        "nonendpoint_nonzero_count": 6680,
        "nonendpoint_zero_count": 0,
        "row_count": 6920
      },
      "stress": {
        "endpoint_count": 114,
        "endpoint_nonzero_count": 0,
        "endpoint_zero_count": 114,
        "nonendpoint_count": 1164,
        "nonendpoint_nonzero_count": 1160,
        "nonendpoint_zero_count": 4,
        "row_count": 1278
      },
      "total": {
        "endpoint_count": 354,
        "endpoint_nonzero_count": 0,
        "endpoint_zero_count": 354,
        "nonendpoint_count": 7844,
        "nonendpoint_nonzero_count": 7840,
        "nonendpoint_zero_count": 4,
        "row_count": 8198
      }
    },
    "greater_than_every_harmonic_denominator": true,
    "prime": 1000003,
    "residue_u32be_sha256": "d90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111"
  },
  "residue_encoding": {
    "byte_order": "big_endian",
    "digest_algorithm": "sha256",
    "include_zero_residues": true,
    "row_order": "exact_fixture_array_order",
    "signed": false,
    "word_bits": 32
  },
  "schema": "pid-rs/ksg-harmonic-modular-certificate",
  "schema_revision": 1,
  "selected_prime_certificates": [
    {
      "classification": "selected_independent_separator",
      "counts": {
        "exhaustive": {
          "endpoint_count": 240,
          "endpoint_nonzero_count": 0,
          "endpoint_zero_count": 240,
          "nonendpoint_count": 6680,
          "nonendpoint_nonzero_count": 6680,
          "nonendpoint_zero_count": 0,
          "row_count": 6920
        },
        "stress": {
          "endpoint_count": 114,
          "endpoint_nonzero_count": 0,
          "endpoint_zero_count": 114,
          "nonendpoint_count": 1164,
          "nonendpoint_nonzero_count": 1164,
          "nonendpoint_zero_count": 0,
          "row_count": 1278
        },
        "total": {
          "endpoint_count": 354,
          "endpoint_nonzero_count": 0,
          "endpoint_zero_count": 354,
          "nonendpoint_count": 7844,
          "nonendpoint_nonzero_count": 7844,
          "nonendpoint_zero_count": 0,
          "row_count": 8198
        }
      },
      "greater_than_every_harmonic_denominator": true,
      "prime": 1000033,
      "residue_u32be_sha256": "931c30fab8560d5692121f3c16be42afa4e9d0b73e640ca4285f5352f4cfff9b"
    },
    {
      "classification": "selected_independent_separator",
      "counts": {
        "exhaustive": {
          "endpoint_count": 240,
          "endpoint_nonzero_count": 0,
          "endpoint_zero_count": 240,
          "nonendpoint_count": 6680,
          "nonendpoint_nonzero_count": 6680,
          "nonendpoint_zero_count": 0,
          "row_count": 6920
        },
        "stress": {
          "endpoint_count": 114,
          "endpoint_nonzero_count": 0,
          "endpoint_zero_count": 114,
          "nonendpoint_count": 1164,
          "nonendpoint_nonzero_count": 1164,
          "nonendpoint_zero_count": 0,
          "row_count": 1278
        },
        "total": {
          "endpoint_count": 354,
          "endpoint_nonzero_count": 0,
          "endpoint_zero_count": 354,
          "nonendpoint_count": 7844,
          "nonendpoint_nonzero_count": 7844,
          "nonendpoint_zero_count": 0,
          "row_count": 8198
        }
      },
      "greater_than_every_harmonic_denominator": true,
      "prime": 1000037,
      "residue_u32be_sha256": "09b6d9e5a4f9f5ee4346dbfc869ba254710f6198cba97f2ac3449db8adb16479"
    },
    {
      "classification": "selected_independent_separator",
      "counts": {
        "exhaustive": {
          "endpoint_count": 240,
          "endpoint_nonzero_count": 0,
          "endpoint_zero_count": 240,
          "nonendpoint_count": 6680,
          "nonendpoint_nonzero_count": 6680,
          "nonendpoint_zero_count": 0,
          "row_count": 6920
        },
        "stress": {
          "endpoint_count": 114,
          "endpoint_nonzero_count": 0,
          "endpoint_zero_count": 114,
          "nonendpoint_count": 1164,
          "nonendpoint_nonzero_count": 1164,
          "nonendpoint_zero_count": 0,
          "row_count": 1278
        },
        "total": {
          "endpoint_count": 354,
          "endpoint_nonzero_count": 0,
          "endpoint_zero_count": 354,
          "nonendpoint_count": 7844,
          "nonendpoint_nonzero_count": 7844,
          "nonendpoint_zero_count": 0,
          "row_count": 8198
        }
      },
      "greater_than_every_harmonic_denominator": true,
      "prime": 1000081,
      "residue_u32be_sha256": "20b2596be7ed67e9fb07039465196da9c289f87d0e13b87d85e8bcf964b18de0"
    }
  ],
  "statement": {
    "classification": "for every frozen corpus row, the exact rational T is zero if and only if the row is a structural endpoint",
    "exact_term": "T = H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
    "nonendpoint_route": "for each selected prime separately, a nonzero residue and invertible denominators imply the exact rational is nonzero",
    "residue_implication_direction": "nonzero_modular_residue_implies_exact_rational_nonzero",
    "selected_prime_set_role": "redundant_fault_diversity_only_not_crt",
    "structural_endpoint_predicate": "(nx == k-1 and ny == n-1) or (nx == n-1 and ny == k-1)",
    "structural_endpoint_route": "the four exact harmonic terms cancel pairwise before field reduction",
    "zero_residue_nonimplication": "zero_modular_residue_does_not_imply_exact_rational_zero"
  }
}
```

## Artifact: `audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean`

SHA-256: `32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4`

```text
import Mathlib.Data.Rat.BigOperators
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring

set_option autoImplicit false
set_option warningAsError true

/-!
# Exact positive-integer arithmetic behind the KSG harmonic rewrite

This file extends the retained revision-2 finite-sum, cancellation, index, range, and
source-symmetry obligations for `KSG-INTEGER-HARMONIC-001` revision 4. It additionally proves
harmonic monotonicity, sharp full-tail bounds for the source-symmetric term, and the explicit
ordered-field bridge from the rational harmonic expression to the exact-real digamma combination.

The special-function bridge is deliberately a typed premise:
`PositiveIntegerDigammaPremise ψ eulerConstant` states the positive-integer identity needed at
each argument. The file does not construct the analytic digamma function and does not establish
that premise. It also does not formalize neighbor geometry, count production, binary64 evaluation,
KSG consistency, continuous-support assumptions, shared-exclusions event semantics, any PID atom,
or Rust refinement.
-/

namespace PidKsgIntegerHarmonic

open scoped BigOperators

noncomputable section

/-- The exact rational harmonic number `H_m = ∑_{i=0}^{m-1} 1/(i+1)`. -/
def harmonic (m : ℕ) : ℚ :=
  ∑ i ∈ Finset.range m, (((i + 1 : ℕ) : ℚ)⁻¹)

@[simp]
theorem harmonic_zero : harmonic 0 = 0 := by
  simp [harmonic]

theorem harmonic_succ (m : ℕ) :
    harmonic (m + 1) = harmonic m + (((m + 1 : ℕ) : ℚ)⁻¹) := by
  simp [harmonic, Finset.sum_range_succ]

theorem harmonic_monotone : Monotone harmonic := by
  intro a b hab
  induction b, hab using Nat.le_induction with
  | base => rfl
  | succ b _ ih =>
      rw [harmonic_succ]
      have hnonneg : (0 : ℚ) ≤ (((b + 1 : ℕ) : ℚ)⁻¹) := by positivity
      exact ih.trans (le_add_of_nonneg_right hnonneg)

/-- Exact-real embedding of the rational finite sum. -/
def harmonicReal (m : ℕ) : ℝ :=
  harmonic m

/-- The direct four-harmonic combination after positive-integer digamma cancellation. -/
def directHarmonicTerm (k n x y : ℕ) : ℚ :=
  harmonic (k - 1) + harmonic (n - 1) - harmonic (x - 1) - harmonic (y - 1)

/-- The source-symmetric, two-nonnegative-range association used by the selected implementation. -/
def symmetricRangeTerm (k n x y : ℕ) : ℚ :=
  (harmonic (n - 1) - harmonic (max x y - 1)) -
    (harmonic (min x y - 1) - harmonic (k - 1))

/-- Exact-real embedding of the source-symmetric rational harmonic term. -/
def symmetricRangeTermReal (k n x y : ℕ) : ℝ :=
  (harmonicReal (n - 1) - harmonicReal (max x y - 1)) -
    (harmonicReal (min x y - 1) - harmonicReal (k - 1))

/--
The exact range identity is algebraic and holds for any natural indices. The hypotheses below bind
the theorem to the positive-integer estimator domain rather than supplying hidden proof power.
-/
theorem direct_eq_symmetric_range
    (k n x y : ℕ)
    (_hk : 1 ≤ k)
    (_hkn : k ≤ n)
    (_hkx : k ≤ x)
    (_hky : k ≤ y)
    (_hxn : x ≤ n)
    (_hyn : y ≤ n) :
    directHarmonicTerm k n x y = symmetricRangeTerm k n x y := by
  rcases le_total x y with hxy | hyx
  · simp [directHarmonicTerm, symmetricRangeTerm, Nat.max_eq_right hxy,
      Nat.min_eq_left hxy]
    ring
  · simp [directHarmonicTerm, symmetricRangeTerm, Nat.max_eq_left hyx,
      Nat.min_eq_right hyx]
    ring

theorem direct_source_swap (k n x y : ℕ) :
    directHarmonicTerm k n x y = directHarmonicTerm k n y x := by
  simp [directHarmonicTerm]
  ring

theorem symmetric_range_source_swap (k n x y : ℕ) :
    symmetricRangeTerm k n x y = symmetricRangeTerm k n y x := by
  simp [symmetricRangeTerm, Nat.max_comm, Nat.min_comm]

/-- Coercion from the rational range term preserves the selected exact-real expression. -/
theorem symmetric_range_term_cast (k n x y : ℕ) :
    ((symmetricRangeTerm k n x y : ℚ) : ℝ) = symmetricRangeTermReal k n x y := by
  simp [symmetricRangeTerm, symmetricRangeTermReal, harmonicReal]

/-- Each selected harmonic tail is between zero and the full `k..n-1` tail. -/
theorem symmetric_range_components_bounded
    (k n x y : ℕ)
    (hkx : k ≤ x)
    (hky : k ≤ y)
    (hxn : x ≤ n)
    (hyn : y ≤ n) :
    let upperTail := harmonic (n - 1) - harmonic (max x y - 1)
    let lowerTail := harmonic (min x y - 1) - harmonic (k - 1)
    let fullTail := harmonic (n - 1) - harmonic (k - 1)
    0 ≤ upperTail ∧ upperTail ≤ fullTail ∧
      0 ≤ lowerTail ∧ lowerTail ≤ fullTail := by
  have hkmax : k ≤ max x y := le_trans hkx (Nat.le_max_left x y)
  have hmaxn : max x y ≤ n := max_le hxn hyn
  have hkmin : k ≤ min x y := le_min hkx hky
  have hminn : min x y ≤ n := le_trans (Nat.min_le_left x y) hxn
  have hkmaxSub : k - 1 ≤ max x y - 1 := Nat.sub_le_sub_right hkmax 1
  have hmaxnSub : max x y - 1 ≤ n - 1 := Nat.sub_le_sub_right hmaxn 1
  have hkminSub : k - 1 ≤ min x y - 1 := Nat.sub_le_sub_right hkmin 1
  have hminnSub : min x y - 1 ≤ n - 1 := Nat.sub_le_sub_right hminn 1
  have hHkMax := harmonic_monotone hkmaxSub
  have hHMaxN := harmonic_monotone hmaxnSub
  have hHkMin := harmonic_monotone hkminSub
  have hHMinN := harmonic_monotone hminnSub
  dsimp
  constructor
  · exact sub_nonneg.mpr hHMaxN
  constructor
  · linarith
  constructor
  · exact sub_nonneg.mpr hHkMin
  · linarith

/-- Exact-real value bound for the selected source-symmetric local term. -/
theorem symmetric_range_term_bounded
    (k n x y : ℕ)
    (hkx : k ≤ x)
    (hky : k ≤ y)
    (hxn : x ≤ n)
    (hyn : y ≤ n) :
    let fullTail := harmonic (n - 1) - harmonic (k - 1)
    (-fullTail ≤ symmetricRangeTerm k n x y ∧
      symmetricRangeTerm k n x y ≤ fullTail) := by
  have hcomponents := symmetric_range_components_bounded k n x y hkx hky hxn hyn
  dsimp at hcomponents ⊢
  rcases hcomponents with ⟨hUpperNonnegative, hUpperBound, hLowerNonnegative, hLowerBound⟩
  simp only [symmetricRangeTerm]
  constructor <;> linarith

/--
Typed analytic seam. This is a premise about a supplied function on positive integers, not a
construction or verification of the analytic digamma function.
-/
def PositiveIntegerDigammaPremise (psi : ℕ → ℝ) (eulerConstant : ℝ) : Prop :=
  ∀ m : ℕ, 1 ≤ m → psi m = harmonicReal (m - 1) - eulerConstant

/-- The four copies of the typed constant cancel with coefficients `(+1,+1,-1,-1)`. -/
theorem digamma_four_term_cancellation
    (psi : ℕ → ℝ)
    (eulerConstant : ℝ)
    (hpsi : PositiveIntegerDigammaPremise psi eulerConstant)
    (k n x y : ℕ)
    (hk : 1 ≤ k)
    (hn : 1 ≤ n)
    (hx : 1 ≤ x)
    (hy : 1 ≤ y) :
    psi k + psi n - psi x - psi y =
      harmonicReal (k - 1) + harmonicReal (n - 1) -
        harmonicReal (x - 1) - harmonicReal (y - 1) := by
  rw [hpsi k hk, hpsi n hn, hpsi x hx, hpsi y hy]
  ring

/--
The typed exact-real digamma combination equals the selected range form and lies in the full
harmonic-tail interval. This theorem composes the analytic premise, four-sign cancellation,
rational range identity, order-preserving rational-to-real coercion, and the rational tail bound.
-/
theorem digamma_four_term_symmetric_range_bounded
    (psi : ℕ → ℝ)
    (eulerConstant : ℝ)
    (hpsi : PositiveIntegerDigammaPremise psi eulerConstant)
    (k n x y : ℕ)
    (hk : 1 ≤ k)
    (hkn : k ≤ n)
    (hkx : k ≤ x)
    (hky : k ≤ y)
    (hxn : x ≤ n)
    (hyn : y ≤ n) :
    let fullTail := harmonicReal (n - 1) - harmonicReal (k - 1)
    let value := symmetricRangeTermReal k n x y
    psi k + psi n - psi x - psi y = value ∧
      -fullTail ≤ value ∧ value ≤ fullTail := by
  have hCancellation :=
    digamma_four_term_cancellation psi eulerConstant hpsi k n x y
      hk (le_trans hk hkn) (le_trans hk hkx) (le_trans hk hky)
  have hRange :=
    direct_eq_symmetric_range k n x y hk hkn hkx hky hxn hyn
  have hRangeCast :=
    congrArg (fun value : ℚ => (value : ℝ)) hRange
  have hValue :
      psi k + psi n - psi x - psi y = symmetricRangeTermReal k n x y := by
    calc
      psi k + psi n - psi x - psi y =
          harmonicReal (k - 1) + harmonicReal (n - 1) -
            harmonicReal (x - 1) - harmonicReal (y - 1) := hCancellation
      _ = ((directHarmonicTerm k n x y : ℚ) : ℝ) := by
        simp [directHarmonicTerm, harmonicReal]
      _ = ((symmetricRangeTerm k n x y : ℚ) : ℝ) := hRangeCast
      _ = symmetricRangeTermReal k n x y := symmetric_range_term_cast k n x y
  have hBound :=
    symmetric_range_term_bounded k n x y hkx hky hxn hyn
  dsimp at hBound ⊢
  have hLowerCast :
      (-(harmonicReal (n - 1) - harmonicReal (k - 1))) ≤
        symmetricRangeTermReal k n x y := by
    rw [← symmetric_range_term_cast]
    simpa [harmonicReal] using (Rat.cast_le (K := ℝ)).2 hBound.1
  have hUpperCast :
      symmetricRangeTermReal k n x y ≤
        harmonicReal (n - 1) - harmonicReal (k - 1) := by
    rw [← symmetric_range_term_cast]
    simpa [harmonicReal] using (Rat.cast_le (K := ℝ)).2 hBound.2
  exact ⟨hValue, hLowerCast, hUpperCast⟩

/-- KSG exclusive marginal counts are shifted once before entering the positive-integer formula. -/
def exclusiveArgument (count : ℕ) : ℕ :=
  count + 1

/-- Ehrlich anchor-inclusive counts already are positive-integer formula arguments. -/
def inclusiveArgument (count : ℕ) : ℕ :=
  count

theorem exclusive_argument_predecessor (count : ℕ) :
    exclusiveArgument count - 1 = count := by
  simp [exclusiveArgument]

theorem exclusive_argument_bounds
    (n k count : ℕ)
    (hk : 1 ≤ k)
    (_hkn : k < n)
    (hlower : k - 1 ≤ count)
    (hupper : count < n) :
    k ≤ exclusiveArgument count ∧ exclusiveArgument count ≤ n := by
  simp only [exclusiveArgument]
  constructor <;> omega

theorem inclusive_argument_identity (count : ℕ) :
    inclusiveArgument count = count := by
  rfl

theorem inclusive_argument_bounds
    (n k count : ℕ)
    (_hk : 1 ≤ k)
    (_hkn : k < n)
    (hlower : k ≤ count)
    (hupper : count ≤ n) :
    k ≤ inclusiveArgument count ∧ inclusiveArgument count ≤ n := by
  simpa [inclusiveArgument] using And.intro hlower hupper

/-- Exact KSG exclusive-count index map, before the symmetric range reassociation. -/
theorem exclusive_direct_index_map (k n nx ny : ℕ) :
    directHarmonicTerm k n (exclusiveArgument nx) (exclusiveArgument ny) =
      harmonic (k - 1) + harmonic (n - 1) - harmonic nx - harmonic ny := by
  simp [directHarmonicTerm, exclusiveArgument]

/-- Exact KSG exclusive-count formula in source-symmetric range form. -/
theorem exclusive_symmetric_range
    (n k nx ny : ℕ)
    (hk : 1 ≤ k)
    (hkn : k < n)
    (hnxLower : k - 1 ≤ nx)
    (hnyLower : k - 1 ≤ ny)
    (hnxUpper : nx < n)
    (hnyUpper : ny < n) :
    harmonic (k - 1) + harmonic (n - 1) - harmonic nx - harmonic ny =
      (harmonic (n - 1) - harmonic (max nx ny)) -
        (harmonic (min nx ny) - harmonic (k - 1)) := by
  have hx := exclusive_argument_bounds n k nx hk hkn hnxLower hnxUpper
  have hy := exclusive_argument_bounds n k ny hk hkn hnyLower hnyUpper
  rw [← exclusive_direct_index_map k n nx ny]
  rw [direct_eq_symmetric_range k n (exclusiveArgument nx) (exclusiveArgument ny)
    hk (Nat.le_of_lt hkn) hx.1 hy.1 hx.2 hy.2]
  rcases le_total nx ny with hnxy | hnyx
  · simp [symmetricRangeTerm, exclusiveArgument, Nat.max_eq_right hnxy,
      Nat.min_eq_left hnxy]
  · simp [symmetricRangeTerm, exclusiveArgument, Nat.max_eq_left hnyx,
      Nat.min_eq_right hnyx]

/-- Exact anchor-inclusive index map; no additional successor is introduced. -/
theorem inclusive_direct_index_map (k n x y : ℕ) :
    directHarmonicTerm k n (inclusiveArgument x) (inclusiveArgument y) =
      harmonic (k - 1) + harmonic (n - 1) - harmonic (x - 1) - harmonic (y - 1) := by
  rfl

/-- Exact anchor-inclusive formula in source-symmetric range form. -/
theorem inclusive_symmetric_range
    (n k x y : ℕ)
    (hk : 1 ≤ k)
    (hkn : k < n)
    (hxLower : k ≤ x)
    (hyLower : k ≤ y)
    (hxUpper : x ≤ n)
    (hyUpper : y ≤ n) :
    directHarmonicTerm k n (inclusiveArgument x) (inclusiveArgument y) =
      symmetricRangeTerm k n x y := by
  simpa [inclusiveArgument] using
    direct_eq_symmetric_range k n x y hk (Nat.le_of_lt hkn)
      hxLower hyLower hxUpper hyUpper

end

end PidKsgIntegerHarmonic
```

## Artifact: `audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2`

SHA-256: `33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31`

```text
; Claim: KSG-INTEGER-HARMONIC-001 revision 4, exact local full-tail bound.
; Scope: exact integer indices and exact real algebra for harmonic values under three explicit
; monotonic-order instances. Lean separately proves universal monotonicity of the rational finite
; harmonic sum. This SMT route does not prove those order premises, the analytic digamma premise,
; neighbor geometry, floating-point behavior, an estimator, support, PID, or Rust refinement.
(set-info :smt-lib-version 2.6)
(set-info :category "crafted")
(set-logic QF_UFLIRA)

(declare-const n Int)
(declare-const k Int)
(declare-const x Int)
(declare-const y Int)
(assert (>= n 2))
(assert (>= k 1))
(assert (< k n))
(assert (>= x k))
(assert (<= x n))
(assert (>= y k))
(assert (<= y n))

(declare-fun harmonic (Int) Real)

(define-fun min_xy () Int (ite (<= x y) x y))
(define-fun max_xy () Int (ite (<= x y) y x))
(define-fun h_k () Real (harmonic (- k 1)))
(define-fun h_n () Real (harmonic (- n 1)))
(define-fun h_min () Real (harmonic (- min_xy 1)))
(define-fun h_max () Real (harmonic (- max_xy 1)))

; These are the only harmonic-order premises used by this independent linear route.
(assert (<= h_k h_min))
(assert (<= h_min h_max))
(assert (<= h_max h_n))

(define-fun direct_value () Real
  (- (+ h_k h_n)
     (harmonic (- x 1))
     (harmonic (- y 1))))
(define-fun range_value () Real
  (- (- h_n h_max)
     (- h_min h_k)))
(define-fun full_tail () Real (- h_n h_k))

; Fixed at zero in the checked theorem. The self-test tightens the lower bound.
(define-fun mutation_offset () Real 0.0)

(define-fun theorem_holds () Bool
  (and (= direct_value range_value)
       (<= (+ (- full_tail) mutation_offset) range_value)
       (<= range_value full_tail)))

; No exact-real counterexample exists under the stated index and order premises.
(assert (not theorem_holds))
(check-sat)
(exit)
```

## Artifact: `scripts/check-lean-ksg-integer-harmonic.py`

SHA-256: `eb57ba3632ba3d2a811c971b20ab5bda2d3b3e0cd26fe69662cc39dbf25504d4`

```text
#!/usr/bin/env python3
"""Kernel-check the scoped KSG positive-integer harmonic obligations in pinned Lean.

The revision-4 extension defines exact rational harmonic finite sums and proves recurrence,
monotonicity, four-term cancellation under an explicit positive-integer digamma premise, the
min/max range identity, exact rational and real full-tail bounds, source symmetry, and the
exclusive/inclusive count-index consequences. The checker separately preserves the exact
revision-2 source bytes at both historical paths; the unversioned path is not a revision-4 mirror.
It does not prove the digamma premise, neighbor-count geometry, estimator properties, support
assumptions, PID semantics, floating-point behavior, or Rust refinement.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "audit/formal/lean"
SOURCE = ROOT / "audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean"
UNVERSIONED_RETAINED_V2_SOURCE = (
    ROOT / "audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean"
)
RETAINED_V2_SOURCE = (
    ROOT / "audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean"
)
EXPECTED_SOURCE_SHA256 = (
    "32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4"
)
EXPECTED_V2_SOURCE_SHA256 = (
    "812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943"
)
EXPECTED_MANIFEST_SHA256 = (
    "e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd"
)
EXPECTED_TOOLCHAIN_SHA256 = (
    "2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e"
)
EXPECTED_LAKEFILE_SHA256 = (
    "1c3f1818c4a62ab48f4ae05de573f6d884aaf7f7397a21646df162151cfccdf1"
)
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.32.0"
EXPECTED_LEAN_COMMIT = "8c9756b28d64dab099da31a4c09229a9e6a2ef35"
EXPECTED_IMPORTS = (
    "import Mathlib.Data.Rat.BigOperators",
    "import Mathlib.Data.Real.Basic",
    "import Mathlib.Algebra.BigOperators.Group.Finset.Basic",
    "import Mathlib.Tactic.Linarith",
    "import Mathlib.Tactic.Positivity",
    "import Mathlib.Tactic.Ring",
)
THEOREMS = (
    "PidKsgIntegerHarmonic.harmonic_zero",
    "PidKsgIntegerHarmonic.harmonic_succ",
    "PidKsgIntegerHarmonic.harmonic_monotone",
    "PidKsgIntegerHarmonic.direct_eq_symmetric_range",
    "PidKsgIntegerHarmonic.direct_source_swap",
    "PidKsgIntegerHarmonic.symmetric_range_source_swap",
    "PidKsgIntegerHarmonic.symmetric_range_term_cast",
    "PidKsgIntegerHarmonic.symmetric_range_components_bounded",
    "PidKsgIntegerHarmonic.symmetric_range_term_bounded",
    "PidKsgIntegerHarmonic.digamma_four_term_cancellation",
    "PidKsgIntegerHarmonic.digamma_four_term_symmetric_range_bounded",
    "PidKsgIntegerHarmonic.exclusive_argument_predecessor",
    "PidKsgIntegerHarmonic.exclusive_argument_bounds",
    "PidKsgIntegerHarmonic.inclusive_argument_identity",
    "PidKsgIntegerHarmonic.inclusive_argument_bounds",
    "PidKsgIntegerHarmonic.exclusive_direct_index_map",
    "PidKsgIntegerHarmonic.exclusive_symmetric_range",
    "PidKsgIntegerHarmonic.inclusive_direct_index_map",
    "PidKsgIntegerHarmonic.inclusive_symmetric_range",
)
PERMITTED_AXIOMS = frozenset(("propext", "Classical.choice", "Quot.sound"))
PROHIBITED_SOURCE = re.compile(
    r"\b(sorry|sorryAx|admit|axiom|constant|native_decide|unsafe)\b"
)
REQUIRED_SCOPE_SENTINELS = (
    "special-function bridge is deliberately a typed premise",
    "does not construct the analytic digamma function",
    "does not formalize neighbor geometry",
    "shared-exclusions event semantics",
    "Rust refinement",
)
TIMEOUT_SECONDS = 240


class LeanKsgHarmonicError(RuntimeError):
    """The source, environment, compilation, or axiom audit failed."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LeanKsgHarmonicError(message)


def mask_lean_comments_and_strings(text: str) -> str:
    masked = list(text)
    index = 0
    block_depth = 0
    in_string = False
    while index < len(text):
        if block_depth:
            if text.startswith("/-", index):
                masked[index : index + 2] = (" ", " ")
                block_depth += 1
                index += 2
            elif text.startswith("-/", index):
                masked[index : index + 2] = (" ", " ")
                block_depth -= 1
                index += 2
            else:
                if text[index] != "\n":
                    masked[index] = " "
                index += 1
        elif in_string:
            if text[index] == "\\":
                masked[index] = " "
                index += 1
                if index < len(text):
                    if text[index] != "\n":
                        masked[index] = " "
                    index += 1
            elif text[index] == '"':
                masked[index] = " "
                in_string = False
                index += 1
            else:
                if text[index] != "\n":
                    masked[index] = " "
                index += 1
        elif text.startswith("/-", index):
            masked[index : index + 2] = (" ", " ")
            block_depth = 1
            index += 2
        elif text.startswith("--", index):
            while index < len(text) and text[index] != "\n":
                masked[index] = " "
                index += 1
        elif text[index] == '"':
            masked[index] = " "
            in_string = True
            index += 1
        else:
            index += 1
    require(block_depth == 0, "Lean source contains an unterminated block comment")
    require(not in_string, "Lean source contains an unterminated string")
    return "".join(masked)


def parse_axiom_inventory(output: str) -> dict[str, frozenset[str]]:
    pattern = re.compile(
        r"'([^']+)' (?:depends on axioms: \[(.*?)\]|does not depend on any axioms)",
        re.DOTALL,
    )
    inventory: dict[str, frozenset[str]] = {}
    for match in pattern.finditer(output):
        payload = match.group(2)
        axioms = (
            frozenset()
            if payload is None
            else frozenset(part.strip() for part in payload.split(",") if part.strip())
        )
        inventory[match.group(1)] = axioms
    return inventory


def run_lean(lake: str, source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [lake, "env", "lean", str(source)],
        cwd=PROJECT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=TIMEOUT_SECONDS,
    )


def verify_dependency_checkouts() -> None:
    manifest = json.loads((PROJECT / "lake-manifest.json").read_text(encoding="utf-8"))
    packages = manifest.get("packages")
    require(
        isinstance(packages, list)
        and packages
        and all(isinstance(package, dict) for package in packages),
        "pinned Lake package manifest is malformed",
    )
    git = shutil.which("git")
    require(git is not None, "git is not available for Lean dependency custody")
    isolated_environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    isolated_environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
    )
    for package in packages:
        name = package.get("name")
        revision = package.get("rev")
        origin = package.get("url")
        require(
            isinstance(name, str)
            and name
            and isinstance(revision, str)
            and revision
            and isinstance(origin, str)
            and origin,
            "Lake package pin is incomplete",
        )
        checkout = PROJECT / ".lake/packages" / name
        require(
            checkout.is_dir() and not checkout.is_symlink(),
            f"Lean dependency checkout is absent or symlinked: {name}",
        )

        def git_output(arguments: list[str], label: str) -> str:
            process = subprocess.run(
                [git, "-C", str(checkout), *arguments],
                env=isolated_environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=60,
            )
            require(
                process.returncode == 0 and process.stderr == "",
                f"{name} {label} failed: {process.stderr}",
            )
            return process.stdout.strip()

        root = Path(
            git_output(["rev-parse", "--show-toplevel"], "root check")
        ).resolve()
        require(root == checkout.resolve(), f"Lean dependency root mismatch: {name}")
        actual_revision = git_output(
            ["rev-parse", "--verify", "HEAD"], "revision check"
        )
        require(
            actual_revision == revision,
            f"Lean dependency revision mismatch for {name}: {actual_revision}",
        )
        actual_origin = git_output(
            ["config", "--local", "--get", "remote.origin.url"], "origin check"
        )
        require(
            actual_origin.rstrip("/") == origin.rstrip("/"),
            f"Lean dependency origin mismatch for {name}: {actual_origin}",
        )
        require(
            git_output(["status", "--porcelain=v1", "--untracked-files=all"], "clean check")
            == "",
            f"Lean dependency checkout is dirty: {name}",
        )


def verify_environment_and_source() -> tuple[str, str]:
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256, "Lean source digest drifted")
    require(
        sha256(UNVERSIONED_RETAINED_V2_SOURCE) == EXPECTED_V2_SOURCE_SHA256,
        "unversioned historical Lean source digest drifted",
    )
    require(
        sha256(RETAINED_V2_SOURCE) == EXPECTED_V2_SOURCE_SHA256,
        "retained revision-2 Lean source digest drifted",
    )
    require(
        UNVERSIONED_RETAINED_V2_SOURCE.read_bytes()
        == RETAINED_V2_SOURCE.read_bytes(),
        "unversioned historical Lean source is not the exact retained revision-2 source",
    )
    require(
        sha256(PROJECT / "lake-manifest.json") == EXPECTED_MANIFEST_SHA256,
        "pinned Lake manifest digest drifted",
    )
    require(
        sha256(PROJECT / "lean-toolchain") == EXPECTED_TOOLCHAIN_SHA256,
        "Lean toolchain file digest drifted",
    )
    require(
        sha256(PROJECT / "lakefile.toml") == EXPECTED_LAKEFILE_SHA256,
        "Lake configuration digest drifted",
    )
    require(
        (PROJECT / "lean-toolchain").read_text(encoding="utf-8").strip()
        == EXPECTED_TOOLCHAIN,
        "Lean toolchain identifier drifted",
    )
    verify_dependency_checkouts()

    source_text = SOURCE.read_text(encoding="utf-8")
    imports = tuple(
        line for line in source_text.splitlines() if line.startswith("import ")
    )
    require(imports == EXPECTED_IMPORTS, f"Lean import inventory drifted: {imports}")
    source_code = mask_lean_comments_and_strings(source_text)
    require(
        PROHIBITED_SOURCE.search(source_code) is None,
        "Lean source contains a prohibited proof escape",
    )
    for sentinel in REQUIRED_SCOPE_SENTINELS:
        require(sentinel in source_text, f"Lean scope sentinel is absent: {sentinel}")
    for theorem in THEOREMS:
        short_name = theorem.rsplit(".", maxsplit=1)[1]
        require(
            len(re.findall(rf"\btheorem\s+{re.escape(short_name)}\b", source_code))
            == 1,
            f"Lean theorem declaration is absent or ambiguous: {theorem}",
        )

    lake = shutil.which("lake")
    require(lake is not None, "lake is not available")
    version = subprocess.run(
        [lake, "env", "lean", "--version"],
        cwd=PROJECT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=60,
    )
    require(version.returncode == 0, f"Lean version probe failed: {version.stderr}")
    require(not version.stderr, f"Lean version probe emitted stderr: {version.stderr}")
    require("Lean (version 4.32.0" in version.stdout, "unexpected Lean version")
    require(
        f"commit {EXPECTED_LEAN_COMMIT}" in version.stdout,
        "unexpected Lean source commit",
    )
    return lake, version.stdout.strip()


def main() -> int:
    try:
        lake, version = verify_environment_and_source()
        source_text = SOURCE.read_text(encoding="utf-8")
        query = (
            source_text
            + "\n"
            + "\n".join(f"#print axioms {theorem}" for theorem in THEOREMS)
            + "\n"
        )
        with tempfile.TemporaryDirectory(prefix="pid-ksg-harmonic-lean-") as directory:
            query_path = Path(directory) / "PidKsgIntegerHarmonicCheck.lean"
            query_path.write_text(query, encoding="utf-8")
            checked = run_lean(lake, query_path)
        require(checked.returncode == 0, f"Lean kernel check failed: {checked.stderr}")
        require(
            not checked.stderr.strip(),
            f"Lean emitted unexpected stderr: {checked.stderr}",
        )

        inventory = parse_axiom_inventory(checked.stdout)
        require(set(inventory) == set(THEOREMS), "Lean theorem axiom inventory changed")
        for theorem, axioms in inventory.items():
            require(
                axioms <= PERMITTED_AXIOMS,
                f"theorem {theorem} uses unapproved axioms: {sorted(axioms)}",
            )

        result = {
            "schema": "pid-rs/lean-ksg-integer-harmonic-check/v2",
            "status": "passed",
            "source_revision": 4,
            "source_sha256": EXPECTED_SOURCE_SHA256,
            "unversioned_historical_source_sha256": EXPECTED_V2_SOURCE_SHA256,
            "retained_v2_source_sha256": EXPECTED_V2_SOURCE_SHA256,
            "unversioned_historical_equals_retained_v2": True,
            "checker_source_sha256": sha256(Path(__file__).resolve()),
            "lake_manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "lean_toolchain": EXPECTED_TOOLCHAIN,
            "lean_version": version,
            "theorems_kernel_checked": len(THEOREMS),
            "permitted_axioms": sorted(PERMITTED_AXIOMS),
            "axiom_inventory": {
                theorem: sorted(inventory[theorem]) for theorem in THEOREMS
            },
            "typed_unproved_premise": (
                "PositiveIntegerDigammaPremise: for each positive integer m used, "
                "psi(m)=H_(m-1)-eulerConstant"
            ),
            "boundary": (
                "Exact finite-sum/monotonicity/cancellation/index/range/symmetry, rational-tail "
                "bounds, and the explicit rational-to-real bounded-combination theorem only. "
                "The analytic digamma premise, count geometry, binary64, estimators, support, "
                "PID semantics, Rust refinement, calibration, and consumers remain outside scope."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        LeanKsgHarmonicError,
    ) as error:
        print(f"Lean KSG integer-harmonic check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

## Artifact: `scripts/check-lean-ksg-integer-harmonic-self-test.py`

SHA-256: `80e37d202acdc7fe9a5118601c693131e74bd8384c3e3ac712c8f0e617b92f3e`

```text
#!/usr/bin/env python3
"""Baseline-first mutation test for the scoped revision-4 Lean KSG harmonic proof."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-lean-ksg-integer-harmonic.py"
spec = importlib.util.spec_from_file_location("check_lean_ksg_harmonic", CHECKER)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load Lean KSG harmonic checker")
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


MUTATIONS = (
    (
        "shift_harmonic_denominator",
        "  ∑ i ∈ Finset.range m, (((i + 1 : ℕ) : ℚ)⁻¹)",
        "  ∑ i ∈ Finset.range m, (((i + 2 : ℕ) : ℚ)⁻¹)",
    ),
    (
        "reverse_harmonic_monotonicity",
        "theorem harmonic_monotone : Monotone harmonic := by",
        "theorem harmonic_monotone : Antitone harmonic := by",
    ),
    (
        "break_range_maximum",
        "harmonic (max x y - 1)) -",
        "harmonic (max x x - 1)) -",
    ),
    (
        "break_range_minimum",
        "(harmonic (min x y - 1) - harmonic (k - 1))",
        "(harmonic (min x x - 1) - harmonic (k - 1))",
    ),
    (
        "break_four_term_coefficient",
        "    psi k + psi n - psi x - psi y =\n"
        "      harmonicReal (k - 1) + harmonicReal (n - 1) -",
        "    psi k + psi n - psi x + psi y =\n"
        "      harmonicReal (k - 1) + harmonicReal (n - 1) -",
    ),
    (
        "shift_exclusive_argument_twice",
        "def exclusiveArgument (count : ℕ) : ℕ :=\n  count + 1",
        "def exclusiveArgument (count : ℕ) : ℕ :=\n  count + 2",
    ),
    (
        "shift_anchor_inclusive_argument",
        "def inclusiveArgument (count : ℕ) : ℕ :=\n  count",
        "def inclusiveArgument (count : ℕ) : ℕ :=\n  count + 1",
    ),
    (
        "make_exclusive_upper_bound_strict",
        "    k ≤ exclusiveArgument count ∧ exclusiveArgument count ≤ n := by",
        "    k ≤ exclusiveArgument count ∧ exclusiveArgument count < n := by",
    ),
    (
        "corrupt_exclusive_count_formula",
        "harmonic (k - 1) + harmonic (n - 1) - harmonic nx - harmonic ny := by",
        "harmonic (k - 1) + harmonic (n - 1) - harmonic (nx + 1) - harmonic ny := by",
    ),
    (
        "corrupt_source_swap_target",
        "    symmetricRangeTerm k n x y = symmetricRangeTerm k n y x := by",
        "    symmetricRangeTerm k n x y = symmetricRangeTerm k n y x + 1 := by",
    ),
    (
        "break_rational_to_real_range_cast",
        "    ((symmetricRangeTerm k n x y : ℚ) : ℝ) = symmetricRangeTermReal k n x y := by",
        "    ((symmetricRangeTerm k n x y : ℚ) : ℝ) = symmetricRangeTermReal k n x y + 1 := by",
    ),
    (
        "strengthen_zero_tail_to_one",
        "      0 ≤ lowerTail ∧ lowerTail ≤ fullTail := by",
        "      1 ≤ lowerTail ∧ lowerTail ≤ fullTail := by",
    ),
    (
        "reverse_rational_lower_bound",
        "    (-fullTail ≤ symmetricRangeTerm k n x y ∧",
        "    (fullTail ≤ symmetricRangeTerm k n x y ∧",
    ),
    (
        "offset_combined_real_value",
        "    psi k + psi n - psi x - psi y = value ∧",
        "    psi k + psi n - psi x - psi y = value + 1 ∧",
    ),
)


class MutationError(RuntimeError):
    """The baseline failed or a scientifically meaningful Lean mutation survived."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MutationError(message)


def main() -> int:
    try:
        lake, _version = checker.verify_environment_and_source()
        baseline = checker.run_lean(lake, checker.SOURCE)
        require(
            baseline.returncode == 0,
            f"baseline Lean source failed before mutation: {baseline.stderr}",
        )
        require(
            not baseline.stderr.strip(),
            f"baseline Lean source emitted stderr before mutation: {baseline.stderr}",
        )

        source_text = checker.SOURCE.read_text(encoding="utf-8")
        results: list[dict[str, object]] = []
        with tempfile.TemporaryDirectory(
            prefix="pid-ksg-harmonic-lean-mutations-"
        ) as directory:
            root = Path(directory)
            for index, (name, before, after) in enumerate(MUTATIONS):
                require(
                    source_text.count(before) == 1,
                    f"mutation anchor is absent or ambiguous: {name}",
                )
                mutant_text = source_text.replace(before, after, 1)
                mutant = root / f"Mutation{index}.lean"
                mutant.write_text(mutant_text, encoding="utf-8")
                checked = checker.run_lean(lake, mutant)
                require(
                    checked.returncode != 0,
                    f"scientifically meaningful Lean mutation survived: {name}",
                )
                results.append(
                    {
                        "name": name,
                        "killed": True,
                        "mutant_sha256": hashlib.sha256(
                            mutant_text.encode("utf-8")
                        ).hexdigest(),
                    }
                )

        evidence = {
            "schema": "pid-rs/lean-ksg-integer-harmonic-mutations/v1",
            "status": "passed",
            "source_sha256": checker.EXPECTED_SOURCE_SHA256,
            "checker_source_sha256": checker.sha256(Path(__file__).resolve()),
            "mutations_killed": len(results),
            "mutations": results,
            "boundary": (
                "These mutations show load-bearing use of the finite-sum denominator, harmonic "
                "monotonicity, min/max range, four signs, source symmetry, rational-to-real "
                "coercion, full-tail bounds, combined exact-real conclusion, exclusive successor, "
                "inclusive identity, and index bounds. They do not validate the typed digamma "
                "premise or any estimator, support, floating-point, PID, or Rust claim."
            ),
        }
        print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        MutationError,
        checker.LeanKsgHarmonicError,
    ) as error:
        print(f"Lean KSG harmonic self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

## Artifact: `scripts/check-z3-ksg-integer-harmonic.py`

SHA-256: `c52618848f3331892bcb34b151a1e51674e7f493fbad71c48b160ff40fbf2d19`

```text
#!/usr/bin/env python3
"""Check independently encoded exact KSG harmonic/index obligations with pinned Z3.

The SMT route proves four-term cancellation under explicit positive-integer digamma instances,
the min/max range identity and source symmetry for an arbitrary harmonic-value function, the
exclusive/inclusive index maps, and the local full-tail bound under explicit harmonic-order
instances. It does not prove the digamma premise, define or prove monotonicity of harmonic finite
sums, or establish neighbor geometry, estimator behavior, support, floating point, PID semantics,
or Rust refinement. The finite-sum definition, recurrence, monotonicity, and unconditional
rational harmonic bound are checked separately by Lean.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "audit/formal/z3-ksg-harmonic"
EXPECTED_Z3_VERSION = "Z3 version 4.16.0 - 64 bit"
TIMEOUT_SECONDS = 30
COUNTEREXAMPLE_ASSERTION = b"(assert (not theorem_holds))"
POSITIVE_ASSERTION = b"(assert theorem_holds)"


class Z3KsgHarmonicError(RuntimeError):
    """A source, pin, satisfiability preflight, or exact UNSAT check failed."""


@dataclass(frozen=True)
class ProofSpec:
    filename: str
    sha256: str
    obligation: str
    typed_premise: str


PROOFS = (
    ProofSpec(
        filename="ksg-digamma-cancellation.smt2",
        sha256="8ae66c11fb66541bc47766b2682cf1e53d9b656aa0fa12e6945ac22057816ed4",
        obligation="four-term exact-real cancellation at four positive integer arguments",
        typed_premise=(
            "four asserted instances psi(m)=harmonic(m-1)-euler_constant; analytic truth open"
        ),
    ),
    ProofSpec(
        filename="ksg-index-maps.smt2",
        sha256="71ea8db97df43f51da89496a5e799bedc6216f9ede40368207d2ffed8df40fe1",
        obligation="exclusive count+1 and anchor-inclusive identity maps with exact domains",
        typed_premise="declared integer count bounds; neighbor production and geometry open",
    ),
    ProofSpec(
        filename="ksg-local-bound-v4.smt2",
        sha256="33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31",
        obligation=(
            "direct/range equality and full-tail bound under explicit local harmonic-order premises"
        ),
        typed_premise=(
            "H(k-1)<=H(min-1)<=H(max-1)<=H(n-1); universal harmonic monotonicity is proved in Lean"
        ),
    ),
    ProofSpec(
        filename="ksg-symmetric-range.smt2",
        sha256="add0fc3a371c65433fdfd8b1e51d3182c6ef78db0cfd1d372f461f1d030e19a9",
        obligation="min/max range reassociation and source exchange for arbitrary harmonic values",
        typed_premise="positive integer index order only; harmonic values are uninterpreted",
    ),
)


def file_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Z3KsgHarmonicError(message)


def find_z3(explicit: str | None = None) -> Path:
    candidate = explicit if explicit is not None else shutil.which("z3")
    require(candidate is not None, "z3 executable was not found on PATH")
    path = Path(candidate).expanduser().resolve()
    require(
        path.is_file() and os.access(path, os.X_OK), f"z3 is not executable: {path}"
    )
    return path


def z3_version(z3: Path) -> str:
    process = subprocess.run(
        [str(z3), "--version"],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    require(
        process.returncode == 0
        and process.stdout == EXPECTED_Z3_VERSION + "\n"
        and process.stderr == "",
        "unexpected z3 version result: "
        f"exit={process.returncode}, stdout={process.stdout!r}, stderr={process.stderr!r}",
    )
    return process.stdout.strip()


def require_exact_proof_set() -> None:
    require(
        PROOF_DIR.is_dir() and not PROOF_DIR.is_symlink(),
        f"proof directory is missing or symlinked: {PROOF_DIR}",
    )
    expected = {spec.filename for spec in PROOFS}
    actual = {entry.name for entry in PROOF_DIR.iterdir()}
    require(
        actual == expected,
        f"proof manifest mismatch: missing={sorted(expected - actual)}, "
        f"unexpected={sorted(actual - expected)}",
    )


def validate_proof_source(path: Path, expected_sha256: str) -> bytes:
    require(
        path.is_file() and not path.is_symlink(), f"proof is not a regular file: {path}"
    )
    raw = path.read_bytes()
    require(
        file_sha256(raw) == expected_sha256,
        f"proof digest mismatch for {path.name}: got {file_sha256(raw)}",
    )
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise Z3KsgHarmonicError(f"proof is not UTF-8: {path}") from error
    required_counts = {
        "(set-logic QF_UFLIRA)": 1,
        "(define-fun theorem_holds () Bool": 1,
        COUNTEREXAMPLE_ASSERTION.decode("ascii"): 1,
        "(check-sat)": 1,
        "(exit)": 1,
    }
    for marker, expected_count in required_counts.items():
        require(
            source.count(marker) == expected_count,
            f"{path.name}: expected {expected_count} occurrence of {marker!r}, "
            f"got {source.count(marker)}",
        )
    forbidden = (
        "(forall",
        "(exists",
        "(check-sat-assuming",
        "(get-model",
        "(get-proof",
        "(include",
        "(push",
        "(pop",
        "(reset",
    )
    present = [marker for marker in forbidden if marker in source]
    require(not present, f"{path.name} contains forbidden solver commands: {present}")
    require("(assert" in source, f"{path.name} contains no assertion")
    return raw


def run_z3(z3: Path, proof: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(z3), "-smt2", str(proof)],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )


def require_exact_result(
    process: subprocess.CompletedProcess[str],
    expected: str,
    label: str,
) -> None:
    require(
        process.returncode == 0
        and process.stdout == expected + "\n"
        and process.stderr == "",
        f"{label} did not return exact {expected.upper()}: "
        f"exit={process.returncode}, stdout={process.stdout!r}, stderr={process.stderr!r}",
    )


def require_unsat(z3: Path, proof: Path) -> None:
    require_exact_result(run_z3(z3, proof), "unsat", proof.name)


def require_satisfiable_positive_preflight(z3: Path, path: Path, raw: bytes) -> None:
    require(
        raw.count(COUNTEREXAMPLE_ASSERTION) == 1,
        f"{path.name}: counterexample assertion is absent or ambiguous",
    )
    positive = raw.replace(COUNTEREXAMPLE_ASSERTION, POSITIVE_ASSERTION, 1)
    with tempfile.TemporaryDirectory(prefix="pid-ksg-z3-positive-") as directory:
        candidate = Path(directory) / path.name
        candidate.write_bytes(positive)
        require_exact_result(
            run_z3(z3, candidate), "sat", f"{path.name} positive preflight"
        )


def verify_all(z3: Path) -> str:
    version = z3_version(z3)
    require_exact_proof_set()
    for spec in PROOFS:
        path = PROOF_DIR / spec.filename
        raw = validate_proof_source(path, spec.sha256)
        require_satisfiable_positive_preflight(z3, path, raw)
        require_unsat(z3, path)
    return version


def main() -> int:
    try:
        z3 = find_z3()
        version = verify_all(z3)
        result = {
            "schema": "pid-rs/z3-ksg-integer-harmonic-check/v2",
            "status": "passed",
            "z3_version": version,
            "checker_source_sha256": file_sha256(Path(__file__).resolve().read_bytes()),
            "proofs": [
                {
                    "filename": spec.filename,
                    "sha256": spec.sha256,
                    "obligation": spec.obligation,
                    "typed_premise": spec.typed_premise,
                    "positive_preflight": "sat",
                    "negated_obligation": "unsat",
                }
                for spec in PROOFS
            ],
            "boundary": (
                "Quantifier-free exact Int/Real/uninterpreted-function obligations only. The "
                "local bound uses explicit harmonic-order premises; finite-sum recurrence and "
                "universal rational harmonic monotonicity are independently checked in Lean. "
                "Digamma truth, count geometry, binary64, estimators, support, PID semantics, "
                "Rust refinement, calibration, and consumers remain outside scope."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        Z3KsgHarmonicError,
    ) as error:
        print(f"Z3 KSG integer-harmonic check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

## Artifact: `scripts/check-z3-ksg-integer-harmonic-self-test.py`

SHA-256: `241a23c903c5087dadc91b31d6fd332fc57f9d94ad46b62709290f25082cb07e`

```text
#!/usr/bin/env python3
"""Baseline-first semantic mutation suite for the independently encoded KSG SMT route."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-z3-ksg-integer-harmonic.py"
spec = importlib.util.spec_from_file_location("check_z3_ksg_harmonic", CHECKER)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load Z3 KSG harmonic checker")
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


MUTATIONS = (
    (
        "ksg-digamma-cancellation.smt2",
        "nonzero_cancellation_offset",
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 1.0)",
    ),
    (
        "ksg-digamma-cancellation.smt2",
        "misbind_y_digamma_premise",
        b"(assert (= (psi y) (- (harmonic (- y 1)) euler_constant)))",
        b"(assert (= (psi y) (- (harmonic (- x 1)) euler_constant)))",
    ),
    (
        "ksg-symmetric-range.smt2",
        "nonzero_range_offset",
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 1.0)",
    ),
    (
        "ksg-symmetric-range.smt2",
        "replace_min_with_left_argument",
        b"(define-fun min_xy () Int (ite (<= x y) x y))",
        b"(define-fun min_xy () Int x)",
    ),
    (
        "ksg-symmetric-range.smt2",
        "replace_max_with_left_argument",
        b"(define-fun max_xy () Int (ite (<= x y) y x))",
        b"(define-fun max_xy () Int x)",
    ),
    (
        "ksg-index-maps.smt2",
        "nonzero_exclusive_predecessor_offset",
        b"(define-fun mutation_offset () Int 0)",
        b"(define-fun mutation_offset () Int 1)",
    ),
    (
        "ksg-index-maps.smt2",
        "shift_exclusive_x_twice",
        b"(define-fun exclusive_x () Int (+ nx 1))",
        b"(define-fun exclusive_x () Int (+ nx 2))",
    ),
    (
        "ksg-index-maps.smt2",
        "shift_anchor_inclusive_x",
        b"(define-fun inclusive_argument_x () Int inclusive_x)",
        b"(define-fun inclusive_argument_x () Int (+ inclusive_x 1))",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "tighten_local_lower_bound",
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 1.0)",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "reverse_lower_harmonic_order_premise",
        b"(assert (<= h_k h_min))",
        b"(assert (<= h_min h_k))",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "reverse_middle_harmonic_order_premise",
        b"(assert (<= h_min h_max))",
        b"(assert (<= h_max h_min))",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "reverse_upper_harmonic_order_premise",
        b"(assert (<= h_max h_n))",
        b"(assert (<= h_n h_max))",
    ),
)


class MutationError(RuntimeError):
    """The baseline failed or a meaningful SMT mutation was not exposed as SAT."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MutationError(message)


def main() -> int:
    try:
        z3 = checker.find_z3()
        version = checker.verify_all(z3)
        results: list[dict[str, object]] = []
        for index, (filename, name, before, after) in enumerate(MUTATIONS):
            original = checker.PROOF_DIR / filename
            raw = original.read_bytes()
            require(
                raw.count(before) == 1,
                f"mutation anchor is absent or ambiguous: {name}",
            )
            mutated = raw.replace(before, after, 1)
            with tempfile.TemporaryDirectory(
                prefix="pid-ksg-z3-mutation-"
            ) as directory:
                path = Path(directory) / f"Mutation{index}-{filename}"
                path.write_bytes(mutated)
                process = checker.run_z3(z3, path)
                checker.require_exact_result(process, "sat", name)
                try:
                    checker.require_unsat(z3, path)
                except checker.Z3KsgHarmonicError:
                    pass
                else:
                    raise MutationError(f"SAT mutation unexpectedly passed: {name}")
            results.append(
                {
                    "proof": filename,
                    "name": name,
                    "killed": True,
                    "mutant_sha256": hashlib.sha256(mutated).hexdigest(),
                }
            )

        result = {
            "schema": "pid-rs/z3-ksg-integer-harmonic-mutations/v2",
            "status": "passed",
            "z3_version": version,
            "checker_source_sha256": checker.file_sha256(
                Path(__file__).resolve().read_bytes()
            ),
            "mutations_killed": len(results),
            "mutations": results,
            "boundary": (
                "Mutations expose changed cancellation, premise binding, min/max, exclusive "
                "successor, inclusive identity, predecessor consequences, explicit harmonic "
                "order premises, and the local bound as SAT. They do not validate the analytic "
                "digamma premise, harmonic finite-sum recurrence or monotonicity, count geometry, "
                "estimator, support, floating-point, PID, or Rust claims."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        MutationError,
        checker.Z3KsgHarmonicError,
    ) as error:
        print(f"Z3 KSG harmonic self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

## Artifact: `scripts/check-ksg-harmonic-modular-certificate.py`

SHA-256: `561f6c2fe25b5b54fd87f1c5b210b5cca55afda75b3b139ba5078269166aa755`

```text
#!/usr/bin/env python3
"""Independently replay the bounded KSG integer-harmonic modular certificate.

The checker does not import the generator.  It reconstructs the fixture row
sequence, uses deterministic Miller--Rabin primality checks, obtains modular
inverses through a batch-product/extended-Euclid route, and rebuilds every
u32-big-endian residue digest.

Success establishes an exact zero/nonzero classification only for the frozen
8,198 rows.  The three selected fields are redundant checks; they are not used
as a CRT theorem and do not classify harmonic zeros outside the corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = (
    ROOT / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
)
DEFAULT_GENERATOR = (
    ROOT / "scripts/generate-ksg-harmonic-modular-certificate.py"
)
DEFAULT_CERTIFICATE = (
    ROOT
    / "claims/KSG-INTEGER-HARMONIC-001/certificates/"
    / "ksg-harmonic-modular-certificate-v1.json"
)
DEFAULT_SIDECAR = DEFAULT_CERTIFICATE.with_suffix(
    DEFAULT_CERTIFICATE.suffix + ".sha256"
)

SCHEMA = "pid-rs/ksg-harmonic-modular-certificate"
SCHEMA_REVISION = 1
CLAIM_ID = "KSG-INTEGER-HARMONIC-001"
CERTIFICATE_REVISION = 1
FIXTURE_PATH = "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
FIXTURE_SCHEMA = "pid-rs/ksg-local-arithmetic-oracle"
FIXTURE_SCHEMA_REVISION = 2
GENERATOR_PATH = "scripts/generate-ksg-harmonic-modular-certificate.py"

EXPECTED_FIXTURE_SHA256 = (
    "560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c"
)
EXPECTED_GENERATOR_SHA256 = (
    "48bff86ad0a89f80dce0452fe032c91edea7f07b7979ec07aabe5ecf2c6a574b"
)
EXPECTED_CERTIFICATE_SHA256 = (
    "ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102"
)
PRE_ARTIFACT_OBSERVATION_SHA256 = (
    "1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc"
)

EXHAUSTIVE_ROW_COUNT = 6_920
STRESS_ROW_COUNT = 1_278
ROW_COUNT = 8_198
EXHAUSTIVE_ENDPOINT_COUNT = 240
STRESS_ENDPOINT_COUNT = 114
ENDPOINT_COUNT = 354
NONENDPOINT_COUNT = 7_844
MAXIMUM_HARMONIC_DENOMINATOR = 999_999
SELECTED_PRIMES = (1_000_033, 1_000_037, 1_000_081)
REJECTED_PRIME = 1_000_003
EXPECTED_RESIDUE_DIGESTS = {
    1_000_033: "931c30fab8560d5692121f3c16be42afa4e9d0b73e640ca4285f5352f4cfff9b",
    1_000_037: "09b6d9e5a4f9f5ee4346dbfc869ba254710f6198cba97f2ac3449db8adb16479",
    1_000_081: "20b2596be7ed67e9fb07039465196da9c289f87d0e13b87d85e8bcf964b18de0",
    1_000_003: "d90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111",
}
EXPECTED_REJECTED_COLLISION_INDICES = (8_045, 8_049, 8_069, 8_093)
STRESS_SAMPLE_SIZES = (17, 32, 64, 256, 4_096, 65_536, 1_000_000)


class CheckError(RuntimeError):
    """The certificate, its custody, or its independently replayed result failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CheckError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def parse_canonical_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
        canonical = canonical_json_bytes(value)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise CheckError(
            f"{label} is not finite canonical UTF-8 JSON: {error}"
        ) from error
    require(isinstance(value, dict), f"{label} top level is not an object")
    require(raw == canonical, f"{label} is not canonical JSON")
    return value


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def is_prime_miller_rabin(value: int) -> bool:
    """Deterministic for the u32 moduli admitted by this certificate."""

    if value < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for prime in small_primes:
        if value % prime == 0:
            return value == prime

    odd_part = value - 1
    power_of_two = 0
    while odd_part % 2 == 0:
        odd_part //= 2
        power_of_two += 1
    for base in (2, 3, 5, 7, 11):
        if base >= value:
            continue
        witness = pow(base, odd_part, value)
        if witness in (1, value - 1):
            continue
        for _ in range(power_of_two - 1):
            witness = witness * witness % value
            if witness == value - 1:
                break
        else:
            return False
    return True


def inverse_extended_euclid(value: int, modulus: int) -> int:
    old_remainder, remainder = modulus, value
    old_coefficient, coefficient = 0, 1
    while remainder:
        quotient = old_remainder // remainder
        old_remainder, remainder = (
            remainder,
            old_remainder - quotient * remainder,
        )
        old_coefficient, coefficient = (
            coefficient,
            old_coefficient - quotient * coefficient,
        )
    require(old_remainder == 1, f"{value} is not invertible modulo {modulus}")
    return old_coefficient % modulus


def harmonic_prefix_batch(prime: int, maximum: int) -> list[int]:
    """Use one Euclidean inverse plus a product sweep, unlike the generator."""

    require(0 < prime < 2**32, f"modulus {prime} is outside the u32 range")
    require(is_prime_miller_rabin(prime), f"modulus {prime} is composite")
    require(
        maximum < prime,
        f"modulus {prime} is not above every denominator through {maximum}",
    )

    products = [1] * (maximum + 1)
    for denominator in range(1, maximum + 1):
        products[denominator] = (
            products[denominator - 1] * denominator
        ) % prime
    inverse_product = inverse_extended_euclid(products[maximum], prime)
    for denominator in range(maximum, 0, -1):
        inverse_denominator = (
            products[denominator - 1] * inverse_product
        ) % prime
        inverse_product = inverse_product * denominator % prime
        products[denominator] = inverse_denominator
    products[0] = 0

    total = 0
    for denominator in range(1, maximum + 1):
        total = (total + products[denominator]) % prime
        products[denominator] = total
    return products


def reconstruct_rows_independently() -> list[tuple[int, int, int, int]]:
    rows: list[tuple[int, int, int, int]] = []
    sample_count = 2
    while sample_count <= 16:
        k = 1
        while k < sample_count:
            x_count = k - 1
            while x_count < sample_count:
                y_count = k - 1
                while y_count < sample_count:
                    rows.append((sample_count, k, x_count, y_count))
                    y_count += 1
                x_count += 1
            k += 1
        sample_count += 1
    require(
        len(rows) == EXHAUSTIVE_ROW_COUNT,
        "independent exhaustive reconstruction count drifted",
    )

    for sample_count in STRESS_SAMPLE_SIZES:
        candidates = (
            1,
            2,
            3,
            4,
            8,
            16,
            64,
            sample_count // 2,
            sample_count - 1,
        )
        k_values = list(dict.fromkeys(sorted(candidates)))
        k_values = [value for value in k_values if 1 <= value < sample_count]
        for k in k_values:
            candidates_for_count = (
                k - 1,
                k if k < sample_count else sample_count - 1,
                (k + sample_count - 1) // 2,
                sample_count - 2,
                sample_count - 1,
            )
            count_values = list(dict.fromkeys(sorted(candidates_for_count)))
            rows.extend(
                (sample_count, k, x_count, y_count)
                for x_count in count_values
                for y_count in count_values
            )
    require(len(rows) == ROW_COUNT, "independent total row reconstruction drifted")
    require(len(set(rows)) == ROW_COUNT, "independent row reconstruction has duplicates")
    return rows


def endpoint_from_multiset(row: tuple[int, int, int, int]) -> bool:
    sample_count, k, x_count, y_count = row
    return sorted((x_count, y_count)) == [k - 1, sample_count - 1]


def read_fixture_rows(raw: bytes) -> tuple[dict[str, Any], list[tuple[int, int, int, int]]]:
    fixture = parse_canonical_json(raw, "fixture")
    require(fixture.get("schema") == FIXTURE_SCHEMA, "fixture schema drifted")
    require(
        fixture.get("schema_revision") == FIXTURE_SCHEMA_REVISION,
        "fixture schema revision drifted",
    )
    require(
        fixture.get("arithmetic", {}).get("exact_identity")
        == "H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
        "fixture exact identity drifted",
    )
    cases = fixture.get("cases")
    require(isinstance(cases, list), "fixture cases are not an array")
    require(len(cases) == ROW_COUNT, "fixture row count drifted")

    rows: list[tuple[int, int, int, int]] = []
    for index, case in enumerate(cases):
        require(isinstance(case, dict), f"fixture row {index} is not an object")
        require(
            set(case)
            == {"expected_nats", "k", "sample_count", "x_count", "y_count"},
            f"fixture row {index} fields drifted",
        )
        row = (
            case["sample_count"],
            case["k"],
            case["x_count"],
            case["y_count"],
        )
        require(
            all(type(component) is int for component in row),
            f"fixture row {index} contains a non-integer argument",
        )
        sample_count, k, x_count, y_count = row
        require(
            2 <= sample_count
            and 1 <= k < sample_count
            and k - 1 <= x_count < sample_count
            and k - 1 <= y_count < sample_count,
            f"fixture row {index} violates the count domain",
        )
        require(
            isinstance(case["expected_nats"], str),
            f"fixture row {index} expected_nats is not text",
        )
        if endpoint_from_multiset(row):
            require(
                case["expected_nats"] == "0",
                f"fixture endpoint row {index} is not canonical exact zero",
            )
        rows.append(row)

    require(
        rows == reconstruct_rows_independently(),
        "fixture row order or argument set differs from independent reconstruction",
    )
    endpoint_split = (
        sum(endpoint_from_multiset(row) for row in rows[:EXHAUSTIVE_ROW_COUNT]),
        sum(endpoint_from_multiset(row) for row in rows[EXHAUSTIVE_ROW_COUNT:]),
    )
    require(
        endpoint_split == (EXHAUSTIVE_ENDPOINT_COUNT, STRESS_ENDPOINT_COUNT),
        f"fixture endpoint split drifted: {endpoint_split!r}",
    )
    maximum = max(
        max(k - 1, sample_count - 1, x_count, y_count)
        for sample_count, k, x_count, y_count in rows
    )
    require(
        maximum == MAXIMUM_HARMONIC_DENOMINATOR,
        "fixture maximum harmonic denominator drifted",
    )
    return fixture, rows


def residue_vector(
    rows: list[tuple[int, int, int, int]], prime: int
) -> list[int]:
    harmonics = harmonic_prefix_batch(prime, MAXIMUM_HARMONIC_DENOMINATOR)
    residues: list[int] = []
    for sample_count, k, x_count, y_count in rows:
        residues.append(
            (
                harmonics[k - 1]
                + harmonics[sample_count - 1]
                - harmonics[x_count]
                - harmonics[y_count]
            )
            % prime
        )
    return residues


def u32be_digest(residues: list[int]) -> str:
    encoded = bytearray(4 * len(residues))
    cursor = 0
    for residue in residues:
        require(0 <= residue < 2**32, "residue is not an unsigned 32-bit value")
        encoded[cursor : cursor + 4] = residue.to_bytes(
            4, byteorder="big", signed=False
        )
        cursor += 4
    return sha256(bytes(encoded))


def classification_counts(
    rows: list[tuple[int, int, int, int]],
    residues: list[int],
    start: int,
    stop: int,
) -> dict[str, int]:
    require(len(rows) == len(residues), "row/residue vector length mismatch")
    buckets = {
        (True, True): 0,
        (True, False): 0,
        (False, True): 0,
        (False, False): 0,
    }
    for index in range(start, stop):
        endpoint = endpoint_from_multiset(rows[index])
        zero = residues[index] == 0
        buckets[(endpoint, zero)] += 1
    return {
        "endpoint_count": buckets[(True, True)] + buckets[(True, False)],
        "endpoint_nonzero_count": buckets[(True, False)],
        "endpoint_zero_count": buckets[(True, True)],
        "nonendpoint_count": buckets[(False, True)] + buckets[(False, False)],
        "nonendpoint_nonzero_count": buckets[(False, False)],
        "nonendpoint_zero_count": buckets[(False, True)],
        "row_count": stop - start,
    }


def all_counts(
    rows: list[tuple[int, int, int, int]], residues: list[int]
) -> dict[str, dict[str, int]]:
    return {
        "exhaustive": classification_counts(
            rows, residues, 0, EXHAUSTIVE_ROW_COUNT
        ),
        "stress": classification_counts(
            rows, residues, EXHAUSTIVE_ROW_COUNT, ROW_COUNT
        ),
        "total": classification_counts(rows, residues, 0, ROW_COUNT),
    }


def exact_collision_witness(
    index: int, row: tuple[int, int, int, int]
) -> dict[str, Any]:
    sample_count, k, x_count, y_count = row
    coefficients: dict[int, int] = {}
    for harmonic_index, coefficient in (
        (k - 1, 1),
        (sample_count - 1, 1),
        (x_count, -1),
        (y_count, -1),
    ):
        coefficients[harmonic_index] = (
            coefficients.get(harmonic_index, 0) + coefficient
        )
    coefficients = {
        harmonic_index: coefficient
        for harmonic_index, coefficient in coefficients.items()
        if coefficient != 0
    }
    require(
        sorted(coefficients.values()) == [-1, 1],
        f"collision row {index} does not reduce to one harmonic difference",
    )
    positive_index = next(
        harmonic_index
        for harmonic_index, coefficient in coefficients.items()
        if coefficient == 1
    )
    negative_index = next(
        harmonic_index
        for harmonic_index, coefficient in coefficients.items()
        if coefficient == -1
    )
    require(
        positive_index != negative_index,
        f"collision row {index} is structurally exact zero",
    )
    sign = "positive" if positive_index > negative_index else "negative"
    lower = min(positive_index, negative_index)
    upper = max(positive_index, negative_index)
    tail_coefficient = 1 if sign == "positive" else -1
    return {
        "exact_reduction": f"H_{positive_index} - H_{negative_index}",
        "fixture_index_zero_based": index,
        "fixture_ordinal_one_based": index + 1,
        "harmonic_difference": {
            "negative_coefficient_index": negative_index,
            "positive_coefficient_index": positive_index,
        },
        "row": {
            "k": k,
            "sample_count": sample_count,
            "x_count": x_count,
            "y_count": y_count,
        },
        "sign": sign,
        "strict_nonzero_witness": {
            "exact_form": (
                f"{tail_coefficient} * sum_(j={lower + 1}..{upper}) 1/j"
            ),
            "first_denominator": lower + 1,
            "last_denominator": upper,
            "tail_coefficient": tail_coefficient,
            "term_sign_reason": "every reciprocal in the nonempty tail is strictly positive",
        },
    }


def expected_prime_record(
    rows: list[tuple[int, int, int, int]],
    prime: int,
    selected: bool,
) -> dict[str, Any]:
    residues = residue_vector(rows, prime)
    digest = u32be_digest(residues)
    require(
        digest == EXPECTED_RESIDUE_DIGESTS[prime],
        f"replayed residue digest drifted for prime {prime}: {digest}",
    )
    counts = all_counts(rows, residues)
    collision_indices = tuple(
        index
        for index, (row, residue) in enumerate(zip(rows, residues, strict=True))
        if residue == 0 and not endpoint_from_multiset(row)
    )

    if selected:
        require(
            not collision_indices,
            f"selected prime {prime} has nonendpoint collisions",
        )
        require(
            counts["total"]["endpoint_zero_count"] == ENDPOINT_COUNT
            and counts["total"]["endpoint_nonzero_count"] == 0
            and counts["total"]["nonendpoint_zero_count"] == 0
            and counts["total"]["nonendpoint_nonzero_count"] == NONENDPOINT_COUNT,
            f"selected prime {prime} does not independently classify every row",
        )
        return {
            "classification": "selected_independent_separator",
            "counts": counts,
            "greater_than_every_harmonic_denominator": True,
            "prime": prime,
            "residue_u32be_sha256": digest,
        }

    require(
        collision_indices == EXPECTED_REJECTED_COLLISION_INDICES,
        f"rejected-prime collision indices drifted: {collision_indices!r}",
    )
    require(
        counts["total"]["endpoint_zero_count"] == ENDPOINT_COUNT
        and counts["total"]["endpoint_nonzero_count"] == 0
        and counts["total"]["nonendpoint_zero_count"]
        == len(EXPECTED_REJECTED_COLLISION_INDICES)
        and counts["total"]["nonendpoint_nonzero_count"]
        == NONENDPOINT_COUNT - len(EXPECTED_REJECTED_COLLISION_INDICES),
        "rejected-prime classification counts drifted",
    )
    return {
        "classification": "rejected_nonendpoint_collision_negative_control",
        "collisions": [
            exact_collision_witness(index, rows[index])
            for index in collision_indices
        ],
        "counts": counts,
        "greater_than_every_harmonic_denominator": True,
        "prime": prime,
        "residue_u32be_sha256": digest,
    }


def expected_static_certificate_parts(generator_digest: str) -> dict[str, Any]:
    return {
        "certificate_revision": CERTIFICATE_REVISION,
        "claim_id": CLAIM_ID,
        "corpus": {
            "fixture": {
                "path": FIXTURE_PATH,
                "schema": FIXTURE_SCHEMA,
                "schema_revision": FIXTURE_SCHEMA_REVISION,
                "sha256": EXPECTED_FIXTURE_SHA256,
            },
            "maximum_harmonic_denominator": MAXIMUM_HARMONIC_DENOMINATOR,
            "ordered_row_count": ROW_COUNT,
            "segments": [
                {
                    "end_index_exclusive": EXHAUSTIVE_ROW_COUNT,
                    "endpoint_count": EXHAUSTIVE_ENDPOINT_COUNT,
                    "name": "exhaustive",
                    "nonendpoint_count": EXHAUSTIVE_ROW_COUNT
                    - EXHAUSTIVE_ENDPOINT_COUNT,
                    "row_count": EXHAUSTIVE_ROW_COUNT,
                    "start_index_inclusive": 0,
                },
                {
                    "end_index_exclusive": ROW_COUNT,
                    "endpoint_count": STRESS_ENDPOINT_COUNT,
                    "name": "stress",
                    "nonendpoint_count": STRESS_ROW_COUNT - STRESS_ENDPOINT_COUNT,
                    "row_count": STRESS_ROW_COUNT,
                    "start_index_inclusive": EXHAUSTIVE_ROW_COUNT,
                },
            ],
        },
        "generator": {
            "algorithm": "linear modular-inverse recurrence followed by harmonic prefix accumulation",
            "imports_pid_rs": False,
            "path": GENERATOR_PATH,
            "sha256": generator_digest,
            "third_party_dependencies": [],
        },
        "limitations": [
            "the iff classification is limited to the exact ordered 8,198-row frozen corpus",
            "the selected triple is redundant fault diversity, not a CRT or universal-zero theorem",
            "a zero residue alone does not prove that an exact rational is zero",
            "the route proves no estimator consistency, support, bias, PID-atom, or application claim",
            "generator/checker diversity is internal evidence, not independent external review",
        ],
        "pre_artifact_observation": {
            "sha256": PRE_ARTIFACT_OBSERVATION_SHA256,
            "status": "historical_first_result_only_not_final_artifact_custody",
        },
        "residue_encoding": {
            "byte_order": "big_endian",
            "digest_algorithm": "sha256",
            "include_zero_residues": True,
            "row_order": "exact_fixture_array_order",
            "signed": False,
            "word_bits": 32,
        },
        "schema": SCHEMA,
        "schema_revision": SCHEMA_REVISION,
        "statement": {
            "classification": (
                "for every frozen corpus row, the exact rational T is zero "
                "if and only if the row is a structural endpoint"
            ),
            "exact_term": "T = H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
            "nonendpoint_route": (
                "for each selected prime separately, a nonzero residue and invertible "
                "denominators imply the exact rational is nonzero"
            ),
            "residue_implication_direction": (
                "nonzero_modular_residue_implies_exact_rational_nonzero"
            ),
            "selected_prime_set_role": "redundant_fault_diversity_only_not_crt",
            "structural_endpoint_predicate": (
                "(nx == k-1 and ny == n-1) or (nx == n-1 and ny == k-1)"
            ),
            "structural_endpoint_route": (
                "the four exact harmonic terms cancel pairwise before field reduction"
            ),
            "zero_residue_nonimplication": (
                "zero_modular_residue_does_not_imply_exact_rational_zero"
            ),
        },
    }


def check(
    fixture_path: Path,
    generator_path: Path,
    certificate_path: Path,
    sidecar_path: Path,
) -> dict[str, Any]:
    fixture_raw = fixture_path.read_bytes()
    generator_raw = generator_path.read_bytes()
    certificate_raw = certificate_path.read_bytes()
    sidecar_text = sidecar_path.read_text(encoding="utf-8")

    fixture_digest = sha256(fixture_raw)
    generator_digest = sha256(generator_raw)
    certificate_digest = sha256(certificate_raw)
    require(
        fixture_digest == EXPECTED_FIXTURE_SHA256,
        f"fixture SHA-256 custody mismatch: {fixture_digest}",
    )
    require(
        generator_digest == EXPECTED_GENERATOR_SHA256,
        f"generator SHA-256 custody mismatch: {generator_digest}",
    )
    require(
        certificate_digest == EXPECTED_CERTIFICATE_SHA256,
        f"certificate SHA-256 custody mismatch: {certificate_digest}",
    )
    expected_sidecar = f"{certificate_digest}  {certificate_path.name}\n"
    require(sidecar_text == expected_sidecar, "certificate sidecar is stale or malformed")

    certificate = parse_canonical_json(certificate_raw, "certificate")
    _fixture, rows = read_fixture_rows(fixture_raw)

    static_parts = expected_static_certificate_parts(generator_digest)
    require(
        set(certificate)
        == set(static_parts)
        | {"selected_prime_certificates", "rejected_prime_negative_control"},
        "certificate top-level fields drifted",
    )
    for field, expected in static_parts.items():
        require(certificate.get(field) == expected, f"certificate {field!r} drifted")

    selected_records = certificate.get("selected_prime_certificates")
    require(isinstance(selected_records, list), "selected-prime records are not an array")
    require(
        len(selected_records) == len(SELECTED_PRIMES),
        "selected-prime record count drifted",
    )
    observed_selected_primes = tuple(
        record.get("prime") if isinstance(record, dict) else None
        for record in selected_records
    )
    require(
        observed_selected_primes == SELECTED_PRIMES,
        f"selected-prime order or membership drifted: {observed_selected_primes!r}",
    )
    require(
        len(set(observed_selected_primes)) == len(SELECTED_PRIMES),
        "selected-prime records contain a duplicate",
    )

    expected_selected = [
        expected_prime_record(rows, prime, selected=True)
        for prime in SELECTED_PRIMES
    ]
    require(
        selected_records == expected_selected,
        "selected-prime certificate records differ from independent replay",
    )

    rejected_record = certificate.get("rejected_prime_negative_control")
    require(
        isinstance(rejected_record, dict),
        "rejected-prime negative control is not an object",
    )
    require(
        rejected_record.get("prime") == REJECTED_PRIME,
        "rejected-prime identity drifted",
    )
    require(
        REJECTED_PRIME not in observed_selected_primes,
        "rejected prime was promoted into the selected set",
    )
    expected_rejected = expected_prime_record(rows, REJECTED_PRIME, selected=False)
    require(
        rejected_record == expected_rejected,
        "rejected-prime negative control differs from independent replay",
    )

    # The exact implication is one-way at the field boundary.  Endpoints are
    # zero by symbolic cancellation.  Nonendpoints are exact-nonzero because
    # each selected lane has a nonzero residue while all denominators are
    # invertible.  The rejected zero collisions demonstrate why the converse
    # "zero residue => exact zero" must not be used.
    for record in expected_selected:
        total = record["counts"]["total"]
        require(
            total["endpoint_zero_count"] == ENDPOINT_COUNT
            and total["nonendpoint_nonzero_count"] == NONENDPOINT_COUNT,
            "corpus-scoped iff implication did not close",
        )
    require(
        len(expected_rejected["collisions"])
        == len(EXPECTED_REJECTED_COLLISION_INDICES),
        "rejected-prime zero-residue counterexample disappeared",
    )

    return {
        "certificate_sha256": certificate_digest,
        "endpoint_split": {
            "exhaustive": EXHAUSTIVE_ENDPOINT_COUNT,
            "stress": STRESS_ENDPOINT_COUNT,
            "total": ENDPOINT_COUNT,
        },
        "nonendpoint_count": NONENDPOINT_COUNT,
        "rejected_prime_collision_count": len(EXPECTED_REJECTED_COLLISION_INDICES),
        "row_count": ROW_COUNT,
        "selected_prime_count": len(SELECTED_PRIMES),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--certificate", type=Path, default=DEFAULT_CERTIFICATE)
    parser.add_argument("--sidecar", type=Path, default=DEFAULT_SIDECAR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = check(
            args.fixture,
            args.generator,
            args.certificate,
            args.sidecar,
        )
    except (OSError, UnicodeError, CheckError) as error:
        print(f"KSG modular certificate check error: {error}", file=sys.stderr)
        return 1
    print(
        "OK: bounded modular certificate replayed "
        f"{result['row_count']} rows; endpoints "
        f"{result['endpoint_split']['total']} "
        f"({result['endpoint_split']['exhaustive']}/"
        f"{result['endpoint_split']['stress']}), nonendpoints "
        f"{result['nonendpoint_count']} nonzero in each of "
        f"{result['selected_prime_count']} selected fields; rejected collisions "
        f"{result['rejected_prime_collision_count']}; certificate SHA-256 "
        f"{result['certificate_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Artifact: `scripts/check-ksg-harmonic-modular-certificate-self-test.py`

SHA-256: `c6376ab07d714a7d732568d589e73e01377cffdbcf163340e9866dfadda7eac4`

```text
#!/usr/bin/env python3
"""Baseline-first mutation suite for the bounded KSG modular certificate."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts/generate-ksg-harmonic-modular-certificate.py"
CHECKER = ROOT / "scripts/check-ksg-harmonic-modular-certificate.py"
FIXTURE = ROOT / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
CERTIFICATE = (
    ROOT
    / "claims/KSG-INTEGER-HARMONIC-001/certificates/"
    / "ksg-harmonic-modular-certificate-v1.json"
)
SIDECAR = CERTIFICATE.with_suffix(CERTIFICATE.suffix + ".sha256")

EXPECTED_FIXTURE_SHA256 = (
    "560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c"
)
EXPECTED_CERTIFICATE_SHA256 = (
    "ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102"
)


class SelfTestError(RuntimeError):
    """The baseline failed or a load-bearing mutation survived."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(
        count == 1,
        f"{label}: expected exactly one source replacement target, found {count}",
    )
    return text.replace(old, new, 1)


def run_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def child_optimization_arguments() -> list[str]:
    require(
        sys.flags.optimize in (0, 1, 2),
        f"unsupported parent optimization level: {sys.flags.optimize}",
    )
    if sys.flags.optimize == 0:
        return []
    return ["-" + "O" * sys.flags.optimize]


def child_python_command(script: Path, *arguments: str) -> list[str]:
    return [
        sys.executable,
        *child_optimization_arguments(),
        str(script),
        *arguments,
    ]


def child_optimization_preflight() -> None:
    probe = run_command(
        [
            sys.executable,
            *child_optimization_arguments(),
            "-c",
            "import sys; print(sys.flags.optimize)",
        ]
    )
    require(
        probe.returncode == 0,
        "child-optimization preflight process failed:\n"
        + probe.stdout
        + probe.stderr,
    )
    require(
        probe.stdout == f"{sys.flags.optimize}\n",
        "child-optimization preflight did not preserve the parent level: "
        f"parent={sys.flags.optimize}, child={probe.stdout!r}",
    )


def baseline_first(fixture: Path) -> None:
    child_optimization_preflight()
    generator = run_command(
        child_python_command(
            GENERATOR,
            "--fixture",
            str(fixture),
        )
    )
    require(
        generator.returncode == 0,
        "generator baseline failed before mutation testing:\n"
        + generator.stdout
        + generator.stderr,
    )
    checker = run_command(
        child_python_command(
            CHECKER,
            "--fixture",
            str(fixture),
        )
    )
    require(
        checker.returncode == 0,
        "checker baseline failed before mutation testing:\n"
        + checker.stdout
        + checker.stderr,
    )
    require(
        "8198 rows" in checker.stdout
        and "endpoints 354 (240/114)" in checker.stdout
        and "nonendpoints 7844 nonzero in each of 3 selected fields"
        in checker.stdout
        and "rejected collisions 4" in checker.stdout,
        "baseline checker summary drifted",
    )


class CaseFiles:
    def __init__(self, root: Path, fixture_source: Path) -> None:
        self.root = root
        self.scripts = root / "scripts"
        self.certificates = root / "certificates"
        self.scripts.mkdir(parents=True)
        self.certificates.mkdir(parents=True)
        self.fixture = root / "ksg_local_arithmetic_oracle.json"
        self.generator = self.scripts / GENERATOR.name
        self.checker = self.scripts / CHECKER.name
        self.certificate = self.certificates / CERTIFICATE.name
        self.sidecar = self.certificates / SIDECAR.name
        shutil.copyfile(fixture_source, self.fixture)
        shutil.copyfile(GENERATOR, self.generator)
        shutil.copyfile(CHECKER, self.checker)
        shutil.copyfile(CERTIFICATE, self.certificate)
        shutil.copyfile(SIDECAR, self.sidecar)

    def run_checker(self) -> subprocess.CompletedProcess[str]:
        return run_command(
            child_python_command(
                self.checker,
                "--fixture",
                str(self.fixture),
                "--generator",
                str(self.generator),
                "--certificate",
                str(self.certificate),
                "--sidecar",
                str(self.sidecar),
            )
        )

    def patch_checker(self, old: str, new: str, label: str) -> None:
        source = self.checker.read_text(encoding="utf-8")
        self.checker.write_text(
            replace_once(source, old, new, label),
            encoding="utf-8",
            newline="",
        )

    def write_certificate_raw(
        self, raw: bytes, *, rebase_checker_digest: bool
    ) -> str:
        digest = hashlib.sha256(raw).hexdigest()
        self.certificate.write_bytes(raw)
        self.sidecar.write_text(
            f"{digest}  {self.certificate.name}\n",
            encoding="utf-8",
            newline="",
        )
        if rebase_checker_digest:
            self.patch_checker(
                EXPECTED_CERTIFICATE_SHA256,
                digest,
                "certificate digest rebase",
            )
        return digest

    def write_certificate_value(
        self, value: dict[str, Any], *, rebase_checker_digest: bool = True
    ) -> str:
        return self.write_certificate_raw(
            canonical_json_bytes(value),
            rebase_checker_digest=rebase_checker_digest,
        )


def expect_rejection(
    root: Path,
    fixture_source: Path,
    label: str,
    mutate: Callable[[CaseFiles], None],
    *,
    diagnostic: str | None = None,
) -> None:
    case = CaseFiles(root / label, fixture_source)
    mutate(case)
    result = case.run_checker()
    require(
        result.returncode != 0,
        f"mutation survived: {label}\n{result.stdout}{result.stderr}",
    )
    if diagnostic is not None:
        require(
            diagnostic in result.stdout + result.stderr,
            f"mutation {label} failed for an unexpected reason; wanted "
            f"{diagnostic!r}\n{result.stdout}{result.stderr}",
        )


def certificate_mutation(
    baseline: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
) -> Callable[[CaseFiles], None]:
    def apply(case: CaseFiles) -> None:
        value = copy.deepcopy(baseline)
        mutate(value)
        case.write_certificate_value(value)

    return apply


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=FIXTURE,
        help="frozen schema-2 fixture; override is useful only for isolated-tree assembly",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_first(args.fixture)

    baseline_raw = CERTIFICATE.read_bytes()
    require(
        hashlib.sha256(baseline_raw).hexdigest() == EXPECTED_CERTIFICATE_SHA256,
        "self-test certificate custody constant drifted",
    )
    baseline = json.loads(baseline_raw)
    checker_source = CHECKER.read_text(encoding="utf-8")

    mutations: list[
        tuple[
            str,
            Callable[[CaseFiles], None],
            str | None,
        ]
    ] = []

    def selected_prime_mutation(
        replacement: int,
        replacement_source: str,
    ) -> Callable[[CaseFiles], None]:
        def apply(case: CaseFiles) -> None:
            value = copy.deepcopy(baseline)
            value["selected_prime_certificates"][0]["prime"] = replacement
            case.write_certificate_value(value)
            case.patch_checker(
                "SELECTED_PRIMES = (1_000_033, 1_000_037, 1_000_081)",
                replacement_source,
                "selected-prime tuple mutation",
            )

        return apply

    mutations.extend(
        [
            (
                "prime-too-small-noninvertible",
                selected_prime_mutation(
                    999_983,
                    "SELECTED_PRIMES = (999_983, 1_000_037, 1_000_081)",
                ),
                "not above every denominator",
            ),
            (
                "composite-selected-modulus",
                selected_prime_mutation(
                    1_000_035,
                    "SELECTED_PRIMES = (1_000_035, 1_000_037, 1_000_081)",
                ),
                "is composite",
            ),
        ]
    )

    def promote_rejected_prime(case: CaseFiles) -> None:
        value = copy.deepcopy(baseline)
        value["selected_prime_certificates"][0] = copy.deepcopy(
            value["rejected_prime_negative_control"]
        )
        case.write_certificate_value(value)
        case.patch_checker(
            "SELECTED_PRIMES = (1_000_033, 1_000_037, 1_000_081)",
            "SELECTED_PRIMES = (1_000_003, 1_000_037, 1_000_081)",
            "rejected-prime promotion",
        )

    mutations.append(
        (
            "selected-to-rejected-prime",
            promote_rejected_prime,
            "has nonendpoint collisions",
        )
    )

    def mutate_residue(value: dict[str, Any]) -> None:
        value["selected_prime_certificates"][0]["residue_u32be_sha256"] = "0" * 64

    mutations.append(
        (
            "selected-residue-digest",
            certificate_mutation(baseline, mutate_residue),
            "differ from independent replay",
        )
    )

    def reverse_row_replay(case: CaseFiles) -> None:
        case.patch_checker(
            "for sample_count, k, x_count, y_count in rows:",
            "for sample_count, k, x_count, y_count in reversed(rows):",
            "residue row-order mutation",
        )

    mutations.append(
        (
            "residue-row-order",
            reverse_row_replay,
            "replayed residue digest drifted",
        )
    )

    def little_endian_replay(case: CaseFiles) -> None:
        case.patch_checker(
            '4, byteorder="big", signed=False',
            '4, byteorder="little", signed=False',
            "residue endianness mutation",
        )

    mutations.append(
        (
            "residue-endianness",
            little_endian_replay,
            "replayed residue digest drifted",
        )
    )

    def asymmetric_endpoint(case: CaseFiles) -> None:
        case.patch_checker(
            "return sorted((x_count, y_count)) == [k - 1, sample_count - 1]",
            "return (x_count, y_count) == (k - 1, sample_count - 1)",
            "endpoint predicate mutation",
        )

    mutations.append(
        (
            "endpoint-predicate-source",
            asymmetric_endpoint,
            "fixture endpoint split drifted",
        )
    )

    def segment_count(value: dict[str, Any]) -> None:
        value["corpus"]["segments"][0]["endpoint_count"] = 239

    mutations.append(
        (
            "segment-split-count",
            certificate_mutation(baseline, segment_count),
            "certificate 'corpus' drifted",
        )
    )

    def split_boundary_source(case: CaseFiles) -> None:
        case.patch_checker(
            "EXHAUSTIVE_ROW_COUNT = 6_920",
            "EXHAUSTIVE_ROW_COUNT = 6_919",
            "exhaustive split-boundary mutation",
        )

    mutations.append(
        (
            "split-boundary-source",
            split_boundary_source,
            "independent exhaustive reconstruction count drifted",
        )
    )

    def duplicate_selected(value: dict[str, Any]) -> None:
        value["selected_prime_certificates"][1] = copy.deepcopy(
            value["selected_prime_certificates"][0]
        )

    mutations.append(
        (
            "duplicate-selected-prime",
            certificate_mutation(baseline, duplicate_selected),
            "selected-prime order or membership drifted",
        )
    )

    def drop_selected(value: dict[str, Any]) -> None:
        value["selected_prime_certificates"].pop()

    mutations.append(
        (
            "drop-selected-prime",
            certificate_mutation(baseline, drop_selected),
            "selected-prime record count drifted",
        )
    )

    def fixture_byte_custody(case: CaseFiles) -> None:
        case.fixture.write_bytes(case.fixture.read_bytes() + b"\n")

    mutations.append(
        (
            "fixture-byte-custody",
            fixture_byte_custody,
            "fixture SHA-256 custody mismatch",
        )
    )

    def fixture_row_order_resealed(case: CaseFiles) -> None:
        fixture = json.loads(case.fixture.read_bytes())
        fixture["cases"][0], fixture["cases"][1] = (
            fixture["cases"][1],
            fixture["cases"][0],
        )
        fixture_raw = canonical_json_bytes(fixture)
        fixture_digest = hashlib.sha256(fixture_raw).hexdigest()
        case.fixture.write_bytes(fixture_raw)

        value = copy.deepcopy(baseline)
        value["corpus"]["fixture"]["sha256"] = fixture_digest
        case.write_certificate_value(value)
        case.patch_checker(
            EXPECTED_FIXTURE_SHA256,
            fixture_digest,
            "resealed fixture digest",
        )

    mutations.append(
        (
            "fixture-row-order-resealed",
            fixture_row_order_resealed,
            "fixture row order or argument set differs",
        )
    )

    def generator_byte_custody(case: CaseFiles) -> None:
        case.generator.write_bytes(
            case.generator.read_bytes() + b"\n# custody mutation\n"
        )

    mutations.append(
        (
            "generator-byte-custody",
            generator_byte_custody,
            "generator SHA-256 custody mismatch",
        )
    )

    def certificate_byte_custody(case: CaseFiles) -> None:
        case.certificate.write_bytes(case.certificate.read_bytes() + b"\n")

    mutations.append(
        (
            "certificate-byte-custody",
            certificate_byte_custody,
            "certificate SHA-256 custody mismatch",
        )
    )

    def stale_sidecar(case: CaseFiles) -> None:
        case.sidecar.write_text(
            "0" * 64 + f"  {case.certificate.name}\n",
            encoding="utf-8",
            newline="",
        )

    mutations.append(
        (
            "certificate-sidecar-custody",
            stale_sidecar,
            "certificate sidecar is stale or malformed",
        )
    )

    def schema_identifier(value: dict[str, Any]) -> None:
        value["schema"] = "pid-rs/ksg-harmonic-modular-certificate-mutated"

    mutations.append(
        (
            "schema-identifier",
            certificate_mutation(baseline, schema_identifier),
            "certificate 'schema' drifted",
        )
    )

    def schema_revision(value: dict[str, Any]) -> None:
        value["schema_revision"] = 2

    mutations.append(
        (
            "schema-revision",
            certificate_mutation(baseline, schema_revision),
            "certificate 'schema_revision' drifted",
        )
    )

    def noncanonical_certificate(case: CaseFiles) -> None:
        case.write_certificate_raw(
            baseline_raw + b"\n",
            rebase_checker_digest=True,
        )

    mutations.append(
        (
            "certificate-canonicality",
            noncanonical_certificate,
            "certificate is not canonical JSON",
        )
    )

    def nonfinite_certificate(case: CaseFiles) -> None:
        raw = baseline_raw.replace(
            b'  "schema_revision": 1,\n',
            b'  "schema_revision": NaN,\n',
            1,
        )
        require(raw != baseline_raw, "nonfinite JSON mutation target was absent")
        case.write_certificate_raw(raw, rebase_checker_digest=True)

    mutations.append(
        (
            "certificate-nonfinite-json",
            nonfinite_certificate,
            "certificate is not finite canonical UTF-8 JSON",
        )
    )

    def duplicate_json_key(case: CaseFiles) -> None:
        raw = baseline_raw.replace(
            b'  "schema": "pid-rs/ksg-harmonic-modular-certificate",\n',
            (
                b'  "schema": "pid-rs/ksg-harmonic-modular-certificate",\n'
                b'  "schema": "pid-rs/ksg-harmonic-modular-certificate",\n'
            ),
            1,
        )
        require(raw != baseline_raw, "duplicate-key mutation target was absent")
        case.write_certificate_raw(raw, rebase_checker_digest=True)

    mutations.append(
        (
            "certificate-duplicate-key",
            duplicate_json_key,
            "duplicate JSON key",
        )
    )

    def implication_direction(value: dict[str, Any]) -> None:
        value["statement"]["residue_implication_direction"] = (
            "zero_modular_residue_implies_exact_rational_zero"
        )
        value["statement"]["zero_residue_nonimplication"] = (
            "nonzero_modular_residue_does_not_imply_exact_rational_nonzero"
        )

    mutations.append(
        (
            "implication-direction",
            certificate_mutation(baseline, implication_direction),
            "certificate 'statement' drifted",
        )
    )

    def crt_escalation(value: dict[str, Any]) -> None:
        value["statement"]["selected_prime_set_role"] = (
            "crt_reconstruction_universal_zero_theorem"
        )

    mutations.append(
        (
            "crt-universal-escalation",
            certificate_mutation(baseline, crt_escalation),
            "certificate 'statement' drifted",
        )
    )

    def collision_sign(value: dict[str, Any]) -> None:
        collision = value["rejected_prime_negative_control"]["collisions"][0]
        collision["sign"] = "negative"
        collision["strict_nonzero_witness"]["tail_coefficient"] = -1

    mutations.append(
        (
            "rejected-collision-sign",
            certificate_mutation(baseline, collision_sign),
            "rejected-prime negative control differs",
        )
    )

    def collision_index(value: dict[str, Any]) -> None:
        collision = value["rejected_prime_negative_control"]["collisions"][0]
        collision["fixture_index_zero_based"] += 1
        collision["fixture_ordinal_one_based"] += 1

    mutations.append(
        (
            "rejected-collision-index",
            certificate_mutation(baseline, collision_index),
            "rejected-prime negative control differs",
        )
    )

    def rejected_residue(value: dict[str, Any]) -> None:
        value["rejected_prime_negative_control"]["residue_u32be_sha256"] = "f" * 64

    mutations.append(
        (
            "rejected-residue-digest",
            certificate_mutation(baseline, rejected_residue),
            "rejected-prime negative control differs",
        )
    )

    require(
        EXPECTED_CERTIFICATE_SHA256 in checker_source,
        "checker no longer contains the certificate custody pin",
    )
    killed: list[str] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-modular-self-test-"
    ) as temporary:
        temporary_root = Path(temporary)
        for label, mutate, diagnostic in mutations:
            expect_rejection(
                temporary_root,
                args.fixture,
                label,
                mutate,
                diagnostic=diagnostic,
            )
            killed.append(label)

    require(len(killed) == 26, f"mutation inventory drifted: {len(killed)}")
    print(
        "OK: KSG modular certificate baseline passed before "
        f"{len(killed)}/{len(killed)} mutations were rejected "
        f"with child optimization level {sys.flags.optimize} "
        "(prime/domain 3, residue/encoding 3, endpoint/split 3, "
        "prime inventory 2, custody 5, schema/canonicality 5, "
        "claim-boundary/collision 5)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, ValueError, SelfTestError) as error:
        print(f"KSG modular certificate self-test error: {error}", file=sys.stderr)
        raise SystemExit(1)
```

## Artifact: `scripts/check-ksg-harmonic-revision.py`

SHA-256: `286388468a3866f2a447ba6e01a62d0d34c0e0a5efe6dad3172977726d39ea46`

```text
#!/usr/bin/env python3
"""Check the exact and bounded executable evidence for KSG-INTEGER-HARMONIC-001.

The exact Fraction route covers every feasible tuple through n=16. The binary64 route covers the
committed 8,198-cell Decimal corpus and inherits IEEE-754 arithmetic; it is not a universal error
bound, neighbor-search proof, estimator-consistency result, or application-validity claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

EXPECTED_CASES = 8_198
EXPECTED_EXHAUSTIVE_CASES = 6_920
EXPECTED_STRESS_CASES = 1_278
EXPECTED_STRESS_SAMPLE_SIZES = (17, 32, 64, 256, 4_096, 65_536, 1_000_000)
EXPECTED_MAX_ERROR = 8.0 * sys.float_info.epsilon
EXPECTED_MAX_ERROR_TIES = 40
ALLOWED_MAX_ERROR = 32.0 * sys.float_info.epsilon
EXPECTED_FIRST_MAXIMUM = (4_096, 1, 2_048, 2_048)
EXPECTED_FIXTURE_SCHEMA = "pid-rs/ksg-local-arithmetic-oracle"
EXPECTED_FIXTURE_SCHEMA_REVISION = 2
EXPECTED_GENERATOR_PATH = "scripts/generate-ksg-local-arithmetic-oracle.py"
EXPECTED_GENERATOR_SHA256 = "a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b"
EXPECTED_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS = 240
EXPECTED_ENDPOINT_CANCELLATION_STRESS_ZEROS = 114
EXPECTED_ENDPOINT_CANCELLATION_ZEROS = 354
EXPECTED_ENDPOINT_DIRECT_LEFT_NONZEROS = 150
EXPECTED_ENDPOINT_DIRECT_LEFT_NEGATIVE_ZEROS = 0
EXPECTED_ENDPOINT_CANCELLATION_RULE = (
    "{nx,ny}={k-1,n-1}; cancel equal symbolic harmonic terms before Decimal evaluation"
)

# (unchanged definition revision, superseded estimator revision, active estimator revision).
# Every family here can directly or transitively emit a scalar changed by the integer-harmonic
# KSG arithmetic. Keeping the prior revision in the table gives the mutation suite a precise stale
# state to replay rather than accepting an unconstrained "not old" check.
KSG_RELEASE_REVISIONS = {
    "pid-core.stable.continuous": (
        "ksg1-product-small-ball-v1",
        "strict-unique-shell-report-v3",
        "strict-unique-shell-integer-harmonic-report-v4",
    ),
    "pid-core.experimental.continuous.co-information": (
        "co-information-algebra-v1",
        "ksg-derived-co-information-v1",
        "ksg-derived-co-information-integer-harmonic-v2",
    ),
    "pid-core.experimental.continuous.isx": (
        "common-coordinate-radius-v1",
        "strict-unique-shell-isx-v3",
        "strict-unique-shell-integer-harmonic-isx-v4",
    ),
    "pid-core.experimental.continuous.pid2": (
        "continuous-isx-pid2-algebra-v1",
        "separate-biased-term-pid2-v1",
        "separate-biased-term-pid2-integer-harmonic-v2",
    ),
    "pid-core.experimental.continuous.incomplete-pid3": (
        "incomplete-pid3-availability-v1",
        "equal-ambient-branch-screen-v1",
        "equal-ambient-branch-screen-integer-harmonic-v2",
    ),
    "pid-core.research.raw-ksg": (
        "kraskov-stoegbauer-grassberger-2004-v1",
        "ksg-chebyshev-raw-v1",
        "ksg-chebyshev-integer-harmonic-raw-v2",
    ),
    "pid-core.research.raw-isx": (
        "ehrlich-et-al-2024-isx-intersection-v1",
        "ehrlich-local-knn-raw-v1",
        "ehrlich-local-knn-integer-harmonic-raw-v2",
    ),
    "pid-core.research.raw-co-information": (
        "shannon-co-information-inclusion-exclusion-v1",
        "ksg-co-information-raw-v1",
        "ksg-co-information-integer-harmonic-raw-v2",
    ),
    # The family owns Python migration `compute_pid2`, which combines a heuristic redundancy term
    # with KSG MI inputs changed by this milestone. Standalone Rust heuristic redundancy scalars
    # remain on the excluded non-cancelling general-digamma path and are numerically unchanged.
    "pid-core.research.isx-heuristics": (
        "heuristic-baselines-v1",
        "heuristic-baselines-v1",
        "heuristic-baselines-with-integer-harmonic-ksg-v2",
    ),
    "pid-core.research.mixed-dimension-pid3": (
        "mixed-dimensional-pid3-reference-v1",
        "mixed-dimensional-pid3-reference-v1",
        "mixed-dimensional-pid3-integer-harmonic-reference-v2",
    ),
    "pid-core.research.hyperbolic": (
        "hyperbolic-geometry-v1",
        "lorentz-geometry-safe-rust-v1",
        "lorentz-geometry-and-integer-harmonic-ksg-safe-rust-v2",
    ),
    "pid-core.experimental.hierarchy": (
        "hierarchy-screening-v1",
        "hierarchy-screening-v1",
        "hierarchy-screening-with-integer-harmonic-ksg-v2",
    ),
    "pid-core.experimental.pipelines.pid3-permutation": (
        "pid3-permutation-null-v1",
        "explicit-seed-pid3-permutation-v1",
        "explicit-seed-pid3-permutation-with-integer-harmonic-ksg-v2",
    ),
    "pid-core.experimental.pipelines.pls-selection-and-composition": (
        "pls-selection-composition-v1",
        "deterministic-pls-cv-v1",
        "deterministic-pls-cv-and-integer-harmonic-pid-composition-v2",
    ),
    "pid-core.experimental.pipelines.pid2-screening": (
        "pid2-pair-screen-v1",
        "deterministic-pair-enumeration-v1",
        "deterministic-pair-enumeration-with-integer-harmonic-pid2-v2",
    ),
}

# Every family outside the KSG migration is a negative control. Exact definition and estimator
# strings make an accidental transitive over-bump fail closed. In particular, the two I_min
# families remain at their pre-migration revisions: their independent numerical-boundary work is
# not authorized collateral in a KSG-only release milestone.
KSG_PROTECTED_RELEASE_REVISIONS = {
    "pid-core.infrastructure": ("pid-core-infrastructure-v2", "pid-core-infrastructure-v2"),
    "pid-core.stable.categorical": (
        "makkeh-gutknecht-wibral-2021-empirical-v1",
        "direct-empirical-pmf-mobius-v1",
    ),
    "pid-core.stable.quantized": (
        "fitted-quantized-categorical-sxpid-v1",
        "equal-width-fit-transform-plus-empirical-pmf-v1",
    ),
    "pid-core.stable.imin": (
        "williams-beer-2010-imin-plus-fixed-quantizer-composition-v1",
        "empirical-specific-information-minimum-with-quantized-provenance-v1",
    ),
    "pid-core.stable.preprocessing": (
        "preprocessing-utilities-v1",
        "preprocessing-safe-rust-v1",
    ),
    "pid-core.diagnostics.distance-matrix": (
        "metric-distance-matrix-v1",
        "upper-triangle-exact-v1",
    ),
    "pid-core.diagnostics.geometry": (
        "diagnostic-formulas-v1",
        "diagnostic-safe-rust-v1",
    ),
    "pid-core.diagnostics.invariants": (
        "empirical-shannon-invariants-v1",
        "empirical-count-map-v1",
    ),
    "pid-core.diagnostics.support": (
        "continuous-sample-diagnostics-v1",
        "exact-observation-diagnostics-v1",
    ),
    "pid-core.experimental.continuous.shared-ksg-config": (
        "kraskov-stoegbauer-grassberger-2004-config-v1",
        "ksg-chebyshev-config-v1",
    ),
    "pid-core.experimental.pipelines.block-resampling": (
        "moving-block-bootstrap-v2",
        "explicit-seed-block-bootstrap-v1",
    ),
    "pid-core.experimental.pipelines.logistic-regression": (
        "penalized-logistic-regression-v1",
        "newton-irls-v1",
    ),
    "pid-core.experimental.pipelines.fdr-adjustment": (
        "bh-by-fdr-v1",
        "deterministic-sorted-pvalues-v1",
    ),
    "pid-core.experimental.pipelines.quantized-sxpid-bootstrap": (
        "quantized-sxpid2-block-bootstrap-v2",
        "explicit-seed-quantized-bootstrap-v2",
    ),
    "pid-core.experimental.pipelines.row-bootstrap": (
        "callback-row-bootstrap-v2",
        "separated-schedule-perturbation-streams-v2",
    ),
    "pid-core.experimental.pipelines.permutation-contracts": (
        "permutation-contracts-v1",
        "explicit-seed-permutation-v1",
    ),
    "pid-core.experimental.pipelines.row-permutation": (
        "callback-row-permutation-v1",
        "explicit-seed-row-permutation-v1",
    ),
    "pid-core.experimental.pipelines.gaussian-noise-provenance": (
        "typed-added-gaussian-noise-v1",
        "content-bound-row-major-gaussian-application-v1",
    ),
    "pid-core.experimental.pipelines.jitter-preprocessing": (
        "legacy-seeded-jitter-v1",
        "seeded-jitter-v1",
    ),
    "pid-core.experimental.pipelines.same-sample-quantization": (
        "same-sample-quantized-exploration-v1",
        "equal-width-same-sample-v1",
    ),
}
KSG_AFFECTED_RELEASE_FAMILIES_SHA256 = (
    "a0c7f7f625e787a86d08435d8eb1fbcea0c045813efd774215b58c59a73271f2"
)
KSG_PROTECTED_RELEASE_FAMILIES_SHA256 = (
    "3596fc9899e8f632f5165fe0138958919f41204d671b70484a5142bb1e72decb"
)
KSG_PROTECTED_RELEASE_METADATA_SHA256 = (
    "24e2f99f8e11d2e2270c77e92f9aa8b4bddecea24574fa39d8980e8616141d19"
)

KSG_CATALOG_METHOD_IDS = (
    "co-information.continuous-raw",
    "co-information.continuous-report",
    "mutual-information.hyperbolic-ksg",
    "mutual-information.ksg1-raw",
    "mutual-information.ksg1-report",
    "mutual-information.ksg1-sensitivity-trajectories",
    "pid.continuous-pid2",
    "pid.incomplete-continuous-pid3",
    "pid.mixed-dimension-pid3",
    "pipelines.hierarchy-screening",
    "pipelines.pid2-screening",
    "pipelines.pid3-permutation",
    "pipelines.pls-pid-composition",
    "shannon-invariants.continuous-ksg-composition",
    "shared-exclusions.continuous-heuristics",
    "shared-exclusions.continuous-raw",
    "shared-exclusions.continuous-report",
    "software.python-experimental-migration-bindings",
    "software.python-v1-bindings",
    "validation.exp0",
)
KSG_CATALOG_ROOT_METHOD_IDS = (
    "mutual-information.ksg1-raw",
    "mutual-information.ksg1-report",
)
KSG_CATALOG_REVERSE_CLOSURE_EXCLUSIONS = (
    "mutual-information.ksg1-shared-config",
)
KSG_FORMAL_CATALOG_METHOD_IDS = (
    "mutual-information.ksg1-raw",
    "mutual-information.ksg1-report",
    "pid.incomplete-continuous-pid3",
    "pid.mixed-dimension-pid3",
    "shared-exclusions.continuous-raw",
    "shared-exclusions.continuous-report",
)
KSG_REQUIRED_CATALOG_EVIDENCE = (
    "claims/KSG-INTEGER-HARMONIC-001/claim-v3.md",
    "scripts/check-ksg-harmonic-revision-self-test.py",
    "scripts/check-ksg-harmonic-revision.py",
)
KSG_REQUIRED_FORMAL_CATALOG_EVIDENCE = (
    "audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean",
    "audit/formal/z3-ksg-harmonic/ksg-digamma-cancellation.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-index-maps.smt2",
    "audit/formal/z3-ksg-harmonic/ksg-symmetric-range.smt2",
    "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md",
    "scripts/check-lean-ksg-integer-harmonic-self-test.py",
    "scripts/check-lean-ksg-integer-harmonic.py",
    "scripts/check-z3-ksg-integer-harmonic-self-test.py",
    "scripts/check-z3-ksg-integer-harmonic.py",
)
KSG_PROTECTED_CATALOG_METHODS_SHA256 = (
    "7dcad03d4b018243c020765a61d7ac2d5a7117d0b3b098ce650fd4c6251fb48d"
)
KSG_PROTECTED_CATALOG_REFERENCES_SHA256 = (
    "dfa02422f456880a5c03830ed730db835d45211cd07558738f02afce7f81f654"
)
KSG_PROTECTED_CATALOG_METADATA_SHA256 = (
    "14cc8ececb23de3367f0629e85cb105c3a674f7499fdc09946bdcae9932ad6fb"
)
KSG_FORBIDDEN_CATALOG_TOKENS = (
    "PID2-REPRESENTED-SUM-001",
    "IMIN-TIE-SWAP-001",
    "exact_binary64_sum",
    "represented-input-exact",
)

ACTIVE_PACKET_RELATIVE_PATH = 'claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json'

EXPECTED_ACTIVE_PACKET_SHA256 = '29fc9f78122d85e2852890bbfba1849729c1d1016c074ed7071a4f3dd52dc8a3'

EXPECTED_PACKET_STAGE = 'preclosure_core_manifest_must_be_regenerated_at_m1c'

EXPECTED_PACKET_PATHS = ('audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean',
 'audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean',
 'audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean',
 'audit/formal/lean/lake-manifest.json',
 'audit/formal/lean/lakefile.toml',
 'audit/formal/lean/lean-toolchain',
 'audit/formal/z3-ksg-harmonic/ksg-digamma-cancellation.smt2',
 'audit/formal/z3-ksg-harmonic/ksg-index-maps.smt2',
 'audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2',
 'audit/formal/z3-ksg-harmonic/ksg-symmetric-range.smt2',
 'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/call-site-map.md',
 'claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json',
 'claims/KSG-INTEGER-HARMONIC-001/certificates/ksg-harmonic-modular-certificate-v1.json.sha256',
 'claims/KSG-INTEGER-HARMONIC-001/claim-v1.md',
 'claims/KSG-INTEGER-HARMONIC-001/claim-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/claim-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/claim-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/decision-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/decision.md',
 'claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/evidence-matrix.md',
 'claims/KSG-INTEGER-HARMONIC-001/failures/decimal-endpoint-cancellation-residuals-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/failures/evidence-gate-gaps.md',
 'claims/KSG-INTEGER-HARMONIC-001/failures/formal-seams-and-negative-controls-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/failures/mutation-count-drift-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/failures/release-phase-conflation-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/failures/route-label-and-tie-multiplicity.md',
 'claims/KSG-INTEGER-HARMONIC-001/failures/stale-parallel-bit-oracles.md',
 'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/implementation-v1.md',
 'claims/KSG-INTEGER-HARMONIC-001/implementation-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/implementation-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/obligations-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/obligations-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/obligations.md',
 'claims/KSG-INTEGER-HARMONIC-001/revision-index-pre-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/revision-index.md',
 'claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-2026-07-25.md',
 'claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-erratum-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/routes-v2.md',
 'claims/KSG-INTEGER-HARMONIC-001/routes-v3.md',
 'claims/KSG-INTEGER-HARMONIC-001/routes-v4.md',
 'claims/KSG-INTEGER-HARMONIC-001/routes.md',
 'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json',
 'crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256',
 'scripts/check-ksg-harmonic-modular-certificate-self-test.py',
 'scripts/check-ksg-harmonic-modular-certificate.py',
 'scripts/check-lean-ksg-integer-harmonic-self-test.py',
 'scripts/check-lean-ksg-integer-harmonic.py',
 'scripts/check-z3-ksg-integer-harmonic-self-test.py',
 'scripts/check-z3-ksg-integer-harmonic.py',
 'scripts/generate-ksg-harmonic-modular-certificate.py',
 'scripts/generate-ksg-local-arithmetic-oracle.py')

EXPECTED_HISTORICAL_HASHES = {'audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean': '812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943',
 'audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean': '812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943',
 'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v2.md': 'e8e3d936d94bc25ed1eaa49e22d3cbdee0e65a649192f613e76dce8c22a99151',
 'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v3.md': 'd17e8eed0f3944d2d4a8dd0e67cf44ffc7ddfb1a5d2194269d17a4003a9f6fa0',
 'claims/KSG-INTEGER-HARMONIC-001/call-site-map.md': '048aaa4209f5c42616f18339775c463f1ac45fe7d25581c7b9d37d571d79c5a6',
 'claims/KSG-INTEGER-HARMONIC-001/claim-v1.md': '726907d19af21db00f3b4245722ac7a0d83b7e6df814aa3e589db47624344c44',
 'claims/KSG-INTEGER-HARMONIC-001/claim-v2.md': '2a114fca75c52d65410bc2b80bd561c7a1858035d5643a2d660044a53823f7f3',
 'claims/KSG-INTEGER-HARMONIC-001/claim-v3.md': '457f55ef444b931cefa05d0dcb06d084cd51f510810080a80a30f0b9f5d59071',
 'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v2.md': '0c65acef2b96bcac208be78a1d781bccb6c079b249076544d2227b3634e5b61b',
 'claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v3.md': '8d4f289d5b1ee9a10995bd8ae1bc086ae276812d1e09005c9006a730adab0949',
 'claims/KSG-INTEGER-HARMONIC-001/decision-v2.md': '540d7f468bbcbc8771adeae8ce3ee103dad5d98d7bc5298a8c1e91a67a19fd26',
 'claims/KSG-INTEGER-HARMONIC-001/decision.md': '0dabc4d4a0247cf55aa03f433bc47eab6f8b2f245824d27da0c7927ce30b79fe',
 'claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v2.md': '6b750c010a00debde29ec2b3959e1bd55751f7ebe9c136beac202503b1b6196c',
 'claims/KSG-INTEGER-HARMONIC-001/evidence-matrix.md': 'f9de6f6ebdd6fe30887c34e3abedef504ffbd2bba5e113a70f22a8f0b004b4fc',
 'claims/KSG-INTEGER-HARMONIC-001/failures/decimal-endpoint-cancellation-residuals-v3.md': 'eeb7b369792ebc882428829ccc62cb472ab5e3b137f1231cbc7f722de759321b',
 'claims/KSG-INTEGER-HARMONIC-001/failures/evidence-gate-gaps.md': 'ff4ea026728be041c01b97b91ddadfabc8e619f1ce292ccf131637c15e2dcfdb',
 'claims/KSG-INTEGER-HARMONIC-001/failures/formal-seams-and-negative-controls-v2.md': 'd5e2f5bf6fc4f05a298d388ebecbf0bfcbb256c0b1e1e26de8a27d8f059782cb',
 'claims/KSG-INTEGER-HARMONIC-001/failures/mutation-count-drift-v3.md': 'b6d886b5dc75c2dd1ae0e12ef4a3a9c842b68093fb541abe45dab19111970c53',
 'claims/KSG-INTEGER-HARMONIC-001/failures/preclosure-audit-findings-v3.md': '565e18922514123942dd4d241c2d677be27101c3402f6fb594dc699641eae071',
 'claims/KSG-INTEGER-HARMONIC-001/failures/release-phase-conflation-v3.md': '2665ff3e7ddd0c4b845882267a6c6c2d2b9e96c3840f01a10e403300b5dc640c',
 'claims/KSG-INTEGER-HARMONIC-001/failures/route-label-and-tie-multiplicity.md': '0853760aa6e7e0952a5f4f1f945e05c9328863ef544a576bada44da033f94e5f',
 'claims/KSG-INTEGER-HARMONIC-001/failures/stale-parallel-bit-oracles.md': '87ea622cf0cea2827cc7637315c4f76e29d53b82a5479c37afd9d20841fc6343',
 'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v2.md': '1068d90dcfe7a20b5237305c0468a6a74eedeb5b91196ff6bfe9969dec300c10',
 'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md': '062d51b03cbcfbfee9a16cba1e29ba3cb83480e6e48e603788828f917b08db25',
 'claims/KSG-INTEGER-HARMONIC-001/implementation-v1.md': '83ee2a03b55ebc2161c3fec6dfe9a40680e8fae0b0bcebb01d5a1533f6872440',
 'claims/KSG-INTEGER-HARMONIC-001/implementation-v2.md': 'e0f7badb2a5f929c3d91fd7193d2ab3fe4e9cf7a2ae83995b7465c2bae2a7724',
 'claims/KSG-INTEGER-HARMONIC-001/obligations-v2.md': '2c108aef29e833a6bf9f41968f917ad05b645606b377fc55ff3b0f9bccc1d389',
 'claims/KSG-INTEGER-HARMONIC-001/obligations-v3.md': 'a2d29661b07a4b855c97ec6fb2e371bb4f422a1bdb3e24f5291a3022b49e889d',
 'claims/KSG-INTEGER-HARMONIC-001/obligations.md': 'b22e061070d16e69a39ede6f367a01c600b9c917ab199debc5ebca267b3b502e',
 'claims/KSG-INTEGER-HARMONIC-001/revision-index-pre-v4.md': 'b3c5c83cdb883acbc7cfc750cd97bab1d6e3d3bd3eb70ec8aabd840897cc4c15',
 'claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-2026-07-25.md': '1487761f2da443771854a1ad61b25042bb18267d68a67452e43d3c3a89d7cc7e',
 'claims/KSG-INTEGER-HARMONIC-001/route-memo-exact-numerics-erratum-v2.md': 'c8100a713bb5f557396398972346d081fe1f1ac3bfc67b749257a88b3f82c855',
 'claims/KSG-INTEGER-HARMONIC-001/routes-v2.md': '5cfe75c9572ee7742a2428dcd119018a6ae1bd92c7cfb1ed0bce5257f7691ab5',
 'claims/KSG-INTEGER-HARMONIC-001/routes-v3.md': 'ed1f9324eb537eb4e752d7b147942562290ab9f6aeeab453fa91f7d73c80d9bc',
 'claims/KSG-INTEGER-HARMONIC-001/routes.md': '23b521232290b30c5d346b42f8cc55ecb1c5f639607a4fa03496cbdd3d1fe256'}

EXPECTED_CLAIM_FACTS = {'arithmetic': {'coefficient_vector': [1, 1, -1, -1],
                'exact_bound': '-D <= T <= D',
                'exact_term': 'T = H_(k-1) + H_(n-1) - H_(x-1) - H_(y-1)',
                'information_unit': 'nats',
                'negative_values_permitted': True,
                'silent_clamping_forbidden': True,
                'typed_analytic_premise': 'psi(m) = H_(m-1) - gamma for used positive '
                                          'integers'},
 'binary64_corpus': {'allowed_absolute_error_epsilon_multiples': 32,
                     'canonical_endpoint_negative_zero_count': 0,
                     'canonical_endpoint_positive_zero_count': 354,
                     'case_count': 8198,
                     'exhaustive_case_count': 6920,
                     'first_maximum_tuple_n_k_nx_ny': [4096, 1, 2048, 2048],
                     'maximum_absolute_error_epsilon_multiples': 8,
                     'maximum_error_is_ulp_claim': False,
                     'maximum_error_measure': 'absolute_error_nats_scaled_by_f64_epsilon',
                     'maximum_error_tie_count': 40,
                     'naive_prefix_ordinary_left_nonzero_count': 121,
                     'selected_neumaier_prefix_ordinary_left_negative_zero_count': 0,
                     'selected_neumaier_prefix_ordinary_left_nonzero_count': 150,
                     'source_swap_bit_asymmetry_count': 0,
                     'stress_case_count': 1278,
                     'structural_endpoint_count': 354,
                     'structural_endpoint_exhaustive_count': 240,
                     'structural_endpoint_stress_count': 114,
                     'structural_rule_is_frozen_corpus_iff': True,
                     'structural_rule_is_universal_iff': False},
 'domains': {'exclusive_map': 'k-1 <= nx,ny < n; x=nx+1; y=ny+1',
             'inclusive_map': 'k <= x,y <= n; pass anchor-inclusive counts directly',
             'pure_arithmetic_lean_domain': 'n >= 1; 1 <= k <= n; k <= x,y <= n',
             'runtime_estimator_domain': 'n >= 2; 1 <= k < n; k <= x,y <= n'},
 'formal': {'formal_assurance_v4_sha256': '45813b90cc15c6880ca9df83419851a7bb80adb4100963ff4c2322493d4eb905',
            'lean_active_source_sha256': '32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4',
            'lean_mutation_count': 14,
            'lean_theorem_count': 19,
            'revision2_lean_source_sha256': '812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943',
            'shared_cuts': ['analytic_digamma_premise',
                            'human_coefficient_signs',
                            'human_exclusive_inclusive_index_map',
                            'chosen_domain_and_theorem_statements'],
            'z3_local_bound_sha256': '33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31',
            'z3_mutation_count': 12,
            'z3_negated_unsat_count': 4,
            'z3_positive_sat_preflight_count': 4,
            'z3_self_test_sha256': '241a23c903c5087dadc91b31d6fd332fc57f9d94ad46b62709290f25082cb07e',
            'z3_uses_uninterpreted_harmonic': True},
 'modular_certificate': {'certificate_sha256': 'ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102',
                         'maximum_denominator': 999999,
                         'mutation_count': 26,
                         'nonendpoint_count': 7844,
                         'pre_artifact_observation_is_final_custody': False,
                         'pre_artifact_observation_sha256': '1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc',
                         'rejected_prime': 1000003,
                         'rejected_prime_collision_indices_zero_based': [8045,
                                                                          8049,
                                                                          8069,
                                                                          8093],
                         'rejected_prime_residue_digest': 'd90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111',
                         'residue_implication_direction': 'nonzero residue implies exact '
                                                          'rational nonzero',
                         'selected_prime_role': 'redundant fault diversity only, not CRT',
                         'selected_primes': [1000033, 1000037, 1000081],
                         'selected_residue_digests': ['931c30fab8560d5692121f3c16be42afa4e9d0b73e640ca4285f5352f4cfff9b',
                                                      '09b6d9e5a4f9f5ee4346dbfc869ba254710f6198cba97f2ac3449db8adb16479',
                                                      '20b2596be7ed67e9fb07039465196da9c289f87d0e13b87d85e8bcf964b18de0'],
                         'zero_residue_implies_exact_zero': False},
 'object_firewall': ['ksg_local_integer_arithmetic_only',
                     'no_transfer_to_complete_ksg_estimator',
                     'no_transfer_to_continuous_ehrlich_isx',
                     'no_transfer_to_continuous_pid2',
                     'no_transfer_to_categorical_mgw_sxpid',
                     'no_transfer_to_williams_beer_imin',
                     'no_transfer_to_fitted_quantized_sxpid',
                     'no_transfer_to_project_heuristics',
                     'no_transfer_to_incomplete_or_mixed_dimension_pid3',
                     'no_transfer_to_wrappers_identity_consumers_or_applications'],
 'witnesses': {'w0_smallest_bound': 'n=2,k=1 realizes +D,-D,0',
               'w1': {'exact_target': '107/210',
                      'helper_arguments': [2, 8, 5, 2],
                      'ordered_counts': [4, 1],
                      'radius': 79,
                      'selected_bits': '0x3fe04e04e04e04e0'},
               'w2': {'exact_mean': '71/840',
                      'helper_arguments': [2, 8, 5, 2],
                      'inclusive_counts': [5, 2],
                      'ordered_binary64_position_difference': 8,
                      'ulp_claim': False}}}

EXPECTED_OPEN_INTEGRATION_GATES = ('claim_custody_final_replay',
 'git_phase_isolation',
 'compiled_debug_release_witnesses',
 'serial_parallel_recapture',
 'catalog_reverse_closure',
 'release_family_closure',
 'audience_artifact_regeneration',
 'software_identity_rebind',
 'settled_full_ci',
 'final_hostile_review',
 'immutable_evidence_matrix_v4',
 'immutable_decision_v4',
 'unsigned_main_commit_and_receipt')

EXPECTED_REVISION_HISTORY = [{'active': False, 'revision': 1, 'status': 'retained_superseded'},
 {'active': False, 'revision': 2, 'status': 'retained_superseded'},
 {'active': False, 'revision': 3, 'status': 'frozen_preclosure_no_go'},
 {'active': True, 'revision': 4, 'status': 'integration_no_go'}]

REQUIRED_V4_PROSE_MARKERS = {'claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md': ('ordered-binary64 positions. '
                                                                'This wording does not assert '
                                                                'eight ULPs',
                                                                'The selected Neumaier-prefix '
                                                                'ordinary-left route is '
                                                                'nonzero on 150/354 endpoints'),
 'claims/KSG-INTEGER-HARMONIC-001/claim-v4.md': ('n >= 2\n'
                                                 '1 <= k < n\n'
                                                 'k <= x <= n\n'
                                                 'k <= y <= n.',
                                                 'The fixture contains 8,198 unique ordered '
                                                 'rows',
                                                 '354 rows, split into 240 exhaustive and 114 '
                                                 'stress rows.',
                                                 'selected endpoint negative zeros   = 0',
                                                 'The `8*EPSILON` quantity is an absolute '
                                                 'error in nats, not eight ULPs',
                                                 'ordinary four-term\n'
                                                 'left association is nonzero at 150/354 '
                                                 'endpoints',
                                                 'The naive\n'
                                                 'prefix has a different 121/354 result',
                                                 'It checks 19 theorem declarations and kills '
                                                 '14/14 baseline-first semantic mutations.',
                                                 'four satisfiable positive preflights, four '
                                                 'unsatisfiable negated obligations, and 12/12',
                                                 'three primes provide redundant fault '
                                                 'diversity, not CRT reconstruction',
                                                 'only a historical pre-artifact observation; '
                                                 'it is not final certificate custody.',
                                                 'categorical Makkeh--Gutknecht--Wibral '
                                                 'shared-exclusions PID;'),
 'claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md': ('nonzero '
                                                                                    'residue '
                                                                                    '=> exact '
                                                                                    'rational '
                                                                                    'nonzero.',
                                                                                    'The '
                                                                                    'selected '
                                                                                    'triple '
                                                                                    'provides '
                                                                                    'redundant '
                                                                                    'fault '
                                                                                    'diversity. '
                                                                                    'It is not '
                                                                                    'CRT '
                                                                                    'reconstruction',
                                                                                    'Canonical '
                                                                                    'final '
                                                                                    'custody '
                                                                                    'is\n'
                                                                                    '`ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102`.'),
 'claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md': ('19 exact Lean theorems',
                                                            '12/12 Z3 mutants returning exact'),
 'claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md': ('repository and publication '
                                                                   'integration                    '
                                                                   'NO-GO',
                                                                   'Immutable final '
                                                                   '`evidence-matrix-v4.md` '
                                                                   'and `decision-v4.md` are '
                                                                   'deliberately'),
 'claims/KSG-INTEGER-HARMONIC-001/revision-index.md': ('The only active revision is 4.',)}


def fail(message: str) -> None:
    raise RuntimeError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def projection_sha256(value: object) -> str:
    projected = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(projected).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def parse_canonical_json(raw: bytes, label: str) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, f"{label} contains a duplicate object key: {key}")
            value[key] = item
        return value

    def reject_nonfinite(token: str) -> None:
        fail(f"{label} contains a non-finite JSON number: {token}")

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_nonfinite,
        )
        canonical = canonical_json_bytes(value)
    except (UnicodeError, json.JSONDecodeError) as error:
        fail(f"{label} is not canonical finite UTF-8 JSON: {error}")
    require(isinstance(value, dict), f"{label} root is not an object")
    require(raw == canonical, f"{label} is not canonical JSON")
    return value


def require_regular_packet_file(repo_root: Path, relative: str) -> Path:
    relative_path = Path(relative)
    require(relative != "", "packet contains an empty path")
    require(
        relative == relative_path.as_posix(),
        f"packet path is not canonical POSIX text: {relative}",
    )
    require(
        not relative_path.is_absolute()
        and all(part not in ("", ".", "..") for part in relative_path.parts),
        f"packet path escapes the repository: {relative}",
    )

    target = repo_root
    for part in relative_path.parts:
        target = target / part
        require(not target.is_symlink(), f"packet path traverses a symlink: {relative}")
    try:
        mode = target.lstat().st_mode
    except OSError as error:
        fail(f"packet target is absent or unreadable: {relative}: {error}")
    require(stat.S_ISREG(mode), f"packet target is not a regular file: {relative}")
    try:
        target.resolve(strict=True).relative_to(repo_root)
    except (OSError, ValueError) as error:
        fail(f"packet target resolves outside the repository: {relative}: {error}")
    return target


def check_claim_route(repo_root: Path) -> None:
    manifest_path = require_regular_packet_file(repo_root, ACTIVE_PACKET_RELATIVE_PATH)
    manifest_raw = manifest_path.read_bytes()
    require(
        hashlib.sha256(manifest_raw).hexdigest() == EXPECTED_ACTIVE_PACKET_SHA256,
        "active revision-4 packet digest changed",
    )
    manifest = parse_canonical_json(manifest_raw, "active revision-4 packet")
    require(
        set(manifest)
        == {
            "active_revision",
            "claim_id",
            "facts",
            "historical_hashes",
            "open_integration_gates",
            "packet_files",
            "packet_stage",
            "revision_history",
            "schema",
            "schema_revision",
            "status",
        },
        "active revision-4 packet top-level fields changed",
    )
    require(
        manifest.get("schema") == "pid-rs/ksg-harmonic-active-packet",
        "active packet schema changed",
    )
    require(manifest.get("schema_revision") == 1, "active packet schema revision changed")
    require(
        manifest.get("claim_id") == "KSG-INTEGER-HARMONIC-001",
        "active packet claim id changed",
    )
    require(manifest.get("active_revision") == 4, "active packet revision changed")
    require(manifest.get("status") == "integration_no_go", "active packet status changed")
    require(manifest.get("packet_stage") == EXPECTED_PACKET_STAGE, "packet stage changed")

    revision_history = manifest.get("revision_history")
    require(
        revision_history == EXPECTED_REVISION_HISTORY,
        "active packet revision history changed",
    )
    active_rows = [
        row
        for row in revision_history
        if isinstance(row, dict) and row.get("active") is True
    ]
    require(len(active_rows) == 1, "active packet does not contain exactly one active revision")
    require(
        active_rows[0] == {"active": True, "revision": 4, "status": "integration_no_go"},
        "active packet selects a revision other than integration-NO-GO revision 4",
    )

    packet_files = manifest.get("packet_files")
    require(isinstance(packet_files, dict), "active packet file map is not an object")
    require(
        list(packet_files) == sorted(packet_files),
        "active packet file map is not ordered",
    )
    for relative, expected_digest in packet_files.items():
        require(isinstance(relative, str), "active packet contains a non-string path")
        require(
            isinstance(expected_digest, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected_digest) is not None,
            f"active packet contains an invalid SHA-256 for {relative}",
        )
        require_regular_packet_file(repo_root, relative)
    require(
        tuple(packet_files) == EXPECTED_PACKET_PATHS,
        "active packet exact path set changed",
    )
    require(
        ACTIVE_PACKET_RELATIVE_PATH not in packet_files,
        "active packet includes itself and creates a digest cycle",
    )
    require(
        "scripts/check-ksg-harmonic-revision.py" not in packet_files
        and "scripts/check-ksg-harmonic-revision-self-test.py" not in packet_files,
        "active packet includes its checker or self-test and creates a digest cycle",
    )
    for relative, expected_digest in packet_files.items():
        target = require_regular_packet_file(repo_root, relative)
        require(
            hashlib.sha256(target.read_bytes()).hexdigest() == expected_digest,
            f"active packet file digest mismatch: {relative}",
        )

    historical_hashes = manifest.get("historical_hashes")
    require(
        historical_hashes == EXPECTED_HISTORICAL_HASHES,
        "frozen revision-1/2/3 historical hashes changed",
    )
    require(
        list(historical_hashes) == sorted(historical_hashes),
        "historical hash map is not ordered",
    )
    for relative, expected_digest in EXPECTED_HISTORICAL_HASHES.items():
        require(
            packet_files.get(relative) == expected_digest,
            f"historical hash is not bound into the packet file map: {relative}",
        )

    facts = manifest.get("facts")
    require(facts == EXPECTED_CLAIM_FACTS, "reviewed revision-4 scalar facts changed")
    require(
        manifest.get("open_integration_gates") == list(EXPECTED_OPEN_INTEGRATION_GATES),
        "revision-4 open integration gates changed",
    )

    linked_digests = {
        "audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean": facts["formal"][
            "revision2_lean_source_sha256"
        ],
        "audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean": facts["formal"][
            "revision2_lean_source_sha256"
        ],
        "audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean": facts["formal"][
            "lean_active_source_sha256"
        ],
        "audit/formal/z3-ksg-harmonic/ksg-local-bound-v4.smt2": facts["formal"][
            "z3_local_bound_sha256"
        ],
        "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md": facts["formal"][
            "formal_assurance_v4_sha256"
        ],
        "claims/KSG-INTEGER-HARMONIC-001/certificates/"
        "ksg-harmonic-modular-certificate-v1.json": facts["modular_certificate"][
            "certificate_sha256"
        ],
        "scripts/check-z3-ksg-integer-harmonic-self-test.py": facts["formal"][
            "z3_self_test_sha256"
        ],
    }
    for relative, expected_digest in linked_digests.items():
        require(
            packet_files.get(relative) == expected_digest,
            f"reviewed fact is not linked to its packet digest: {relative}",
        )

    formal_v3 = (
        repo_root / "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md"
    ).read_bytes()
    require(len(formal_v3) == 1_985, "formal-assurance-v3 byte length changed")
    require(len(formal_v3.splitlines()) == 40, "formal-assurance-v3 line count changed")

    for relative, markers in REQUIRED_V4_PROSE_MARKERS.items():
        source = require_regular_packet_file(repo_root, relative).read_text(encoding="utf-8")
        for marker in markers:
            require(
                marker in source,
                f"revision-4 semantic prose marker absent: {relative}: {marker!r}",
            )

    certificate_relative = (
        "claims/KSG-INTEGER-HARMONIC-001/certificates/"
        "ksg-harmonic-modular-certificate-v1.json"
    )
    certificate = parse_canonical_json(
        require_regular_packet_file(repo_root, certificate_relative).read_bytes(),
        "bounded modular certificate",
    )
    selected = certificate.get("selected_prime_certificates")
    require(isinstance(selected, list), "selected modular records are not an array")
    require(
        all(isinstance(record, dict) for record in selected),
        "selected modular array contains a non-object record",
    )
    modular = facts["modular_certificate"]
    require(
        [record.get("prime") for record in selected] == modular["selected_primes"],
        "selected modular prime inventory changed",
    )
    require(
        [record.get("residue_u32be_sha256") for record in selected]
        == modular["selected_residue_digests"],
        "selected modular residue digests changed",
    )
    for record in selected:
        total = record.get("counts", {}).get("total", {})
        require(
            total.get("endpoint_zero_count") == 354
            and total.get("nonendpoint_nonzero_count") == 7_844,
            "selected modular endpoint/nonendpoint classification changed",
        )
    rejected = certificate.get("rejected_prime_negative_control")
    require(isinstance(rejected, dict), "rejected modular negative control is absent")
    require(rejected.get("prime") == modular["rejected_prime"], "rejected prime changed")
    require(
        rejected.get("residue_u32be_sha256") == modular["rejected_prime_residue_digest"],
        "rejected-prime residue digest changed",
    )
    collisions = rejected.get("collisions")
    require(isinstance(collisions, list), "rejected-prime collisions are not an array")
    require(
        all(isinstance(collision, dict) for collision in collisions),
        "rejected-prime collision array contains a non-object record",
    )
    require(
        [collision.get("fixture_index_zero_based") for collision in collisions]
        == modular["rejected_prime_collision_indices_zero_based"],
        "rejected-prime zero-based collision indices changed",
    )
    statement = certificate.get("statement")
    require(isinstance(statement, dict), "modular certificate statement is absent")
    require(
        statement.get("residue_implication_direction")
        == "nonzero_modular_residue_implies_exact_rational_nonzero",
        "modular residue implication direction changed",
    )
    require(
        statement.get("selected_prime_set_role") == "redundant_fault_diversity_only_not_crt",
        "selected modular primes were promoted to CRT",
    )
    require(
        statement.get("zero_residue_nonimplication")
        == "zero_modular_residue_does_not_imply_exact_rational_zero",
        "rejected-prime zero-residue non-implication changed",
    )

    for relative in (
        "claims/KSG-INTEGER-HARMONIC-001/evidence-matrix-v4.md",
        "claims/KSG-INTEGER-HARMONIC-001/decision-v4.md",
    ):
        final_path = repo_root / relative
        require(
            not final_path.exists() and not final_path.is_symlink(),
            f"preclosure packet unexpectedly contains final artifact: {relative}",
        )


def mask_rust(source: str, *, mask_strings: bool) -> str:
    """Mask Rust comments and optionally strings while preserving positions and newlines."""

    masked = list(source)
    index = 0
    while index < len(source):
        if source.startswith("//", index):
            end = source.find("\n", index + 2)
            if end < 0:
                end = len(source)
            for position in range(index, end):
                masked[position] = " "
            index = end
            continue
        if source.startswith("/*", index):
            depth = 1
            end = index + 2
            while end < len(source) and depth:
                if source.startswith("/*", end):
                    depth += 1
                    end += 2
                elif source.startswith("*/", end):
                    depth -= 1
                    end += 2
                else:
                    end += 1
            require(depth == 0, "unterminated Rust block comment")
            for position in range(index, end):
                if masked[position] != "\n":
                    masked[position] = " "
            index = end
            continue

        raw_match = re.match(r"(?:br|r)(?P<hashes>#{0,255})\"", source[index:])
        if raw_match:
            hashes = raw_match.group("hashes")
            terminator = '"' + hashes
            content_start = index + raw_match.end()
            end_start = source.find(terminator, content_start)
            require(end_start >= 0, "unterminated Rust raw string")
            end = end_start + len(terminator)
            if mask_strings:
                for position in range(index, end):
                    if masked[position] != "\n":
                        masked[position] = " "
            index = end
            continue

        quote_index = index
        if source.startswith('b"', index):
            quote_index += 1
        if source[quote_index : quote_index + 1] == '"':
            end = quote_index + 1
            escaped = False
            while end < len(source):
                character = source[end]
                if character == '"' and not escaped:
                    end += 1
                    break
                if character == "\\" and not escaped:
                    escaped = True
                else:
                    escaped = False
                end += 1
            require(end <= len(source) and source[end - 1] == '"', "unterminated Rust string")
            if mask_strings:
                for position in range(index, end):
                    if masked[position] != "\n":
                        masked[position] = " "
            index = end
            continue
        index += 1
    return "".join(masked)


def mask_rust_noncode(source: str) -> str:
    """Mask Rust comments and strings for live-code structural checks."""

    return mask_rust(source, mask_strings=True)


def mask_rust_comments(source: str) -> str:
    """Mask Rust comments while retaining live string-literal values."""

    return mask_rust(source, mask_strings=False)


def rust_function_span(masked_source: str, name: str) -> tuple[int, int]:
    marker = f"fn {name}("
    start = masked_source.find(marker)
    require(start >= 0, f"Rust function is absent: {name}")
    require(masked_source.find(marker, start + 1) < 0, f"Rust function is duplicated: {name}")
    opening = masked_source.find("{", start)
    require(opening >= 0, f"Rust function body is absent: {name}")
    depth = 0
    for index in range(opening, len(masked_source)):
        if masked_source[index] == "{":
            depth += 1
        elif masked_source[index] == "}":
            depth -= 1
            if depth == 0:
                return opening + 1, index
    fail(f"Rust function body is unterminated: {name}")


def rust_function_body(masked_source: str, name: str) -> str:
    start, end = rust_function_span(masked_source, name)
    return masked_source[start:end]


def require_runtime_estimator_revision(
    comments_masked_source: str,
    structure_masked_source: str,
    function_name: str,
    expected_revision: str,
) -> None:
    start, end = rust_function_span(structure_masked_source, function_name)
    body = comments_masked_source[start:end]
    field = "estimator_revision:"
    marker = f'{field} "{expected_revision}",'
    require(body.count(field) == 1, f"runtime estimator field changed in {function_name}")
    require(
        body.count(marker) == 1,
        f"runtime estimator revision changed in {function_name}: expected {expected_revision}",
    )


def shifted_harmonic_table(max_argument: int) -> list[float]:
    """Return table[m] = H_(m-1) using the production compensation policy."""

    table = [0.0] * (max_argument + 1)
    total = 0.0
    correction = 0.0
    for argument in range(2, max_argument + 1):
        value = 1.0 / float(argument - 1)
        next_total = total + value
        if abs(total) >= abs(value):
            correction += (total - next_total) + value
        else:
            correction += (value - next_total) + total
        total = next_total
        table[argument] = total + correction
    return table


def harmonic_term(table: list[float], k: int, n: int, x: int, y: int) -> float:
    require(0 < k <= x <= n and k <= y <= n, "invalid positive-integer count domain")
    lower = min(x, y)
    upper = max(x, y)
    return (table[n] - table[upper]) - (table[lower] - table[k])


def exact_harmonic(index: int) -> Fraction:
    return sum((Fraction(1, denominator) for denominator in range(1, index + 1)), Fraction())


def is_endpoint_cancellation_case(case: dict[str, Any]) -> bool:
    low = case["k"] - 1
    high = case["sample_count"] - 1
    return (case["x_count"], case["y_count"]) in ((low, high), (high, low))


def check_exact_route() -> None:
    cases = 0
    for n in range(2, 17):
        harmonics = [exact_harmonic(index) for index in range(n)]
        for k in range(1, n):
            for nx in range(k - 1, n):
                for ny in range(k - 1, n):
                    direct = harmonics[k - 1] + harmonics[n - 1] - harmonics[nx] - harmonics[ny]
                    lower = min(nx + 1, ny + 1)
                    upper = max(nx + 1, ny + 1)
                    ranged = (harmonics[n - 1] - harmonics[upper - 1]) - (
                        harmonics[lower - 1] - harmonics[k - 1]
                    )
                    require(direct == ranged, f"exact range identity failed at {(n, k, nx, ny)}")
                    cases += 1
    require(cases == EXPECTED_EXHAUSTIVE_CASES, f"exact case count changed: {cases}")
    require(
        exact_harmonic(3) - 2 * exact_harmonic(0) == Fraction(11, 6),
        "n=4,k=1 sparse boundary changed",
    )
    require(
        exact_harmonic(1) + exact_harmonic(3) - 2 * exact_harmonic(1) == Fraction(5, 6),
        "n=4,k=2 boundary changed",
    )
    require(
        exact_harmonic(2) + exact_harmonic(3) - 2 * exact_harmonic(3) == Fraction(-1, 3),
        "n=4,k=3 dense boundary changed",
    )


def load_fixture(repo_root: Path) -> dict[str, Any]:
    fixture_path = repo_root / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
    sidecar_path = fixture_path.with_suffix(fixture_path.suffix + ".sha256")
    raw = fixture_path.read_bytes()
    sidecar_fields = sidecar_path.read_text(encoding="utf-8").split()
    require(len(sidecar_fields) == 2, "fixture SHA-256 sidecar shape changed")
    expected_digest, sidecar_name = sidecar_fields
    require(sidecar_name == fixture_path.name, "fixture SHA-256 sidecar filename changed")
    require(hashlib.sha256(raw).hexdigest() == expected_digest, "fixture SHA-256 mismatch")
    fixture = json.loads(raw)
    require(fixture.get("schema") == EXPECTED_FIXTURE_SCHEMA, "fixture schema changed")
    require(
        fixture.get("schema_revision") == EXPECTED_FIXTURE_SCHEMA_REVISION,
        "fixture schema revision changed",
    )
    arithmetic = fixture.get("arithmetic")
    require(isinstance(arithmetic, dict), "fixture arithmetic metadata is absent")
    require(arithmetic.get("decimal_precision_digits") == 80, "fixture precision changed")
    require(
        arithmetic.get("endpoint_cancellation_exact_zero_case_count")
        == EXPECTED_ENDPOINT_CANCELLATION_ZEROS,
        "fixture endpoint-cancellation exact-zero count changed",
    )
    require(
        arithmetic.get("endpoint_cancellation_exact_zero_exhaustive_case_count")
        == EXPECTED_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS,
        "fixture exhaustive endpoint-cancellation exact-zero count changed",
    )
    require(
        arithmetic.get("endpoint_cancellation_exact_zero_rule")
        == EXPECTED_ENDPOINT_CANCELLATION_RULE,
        "fixture endpoint-cancellation exact-zero rule changed",
    )
    require(
        arithmetic.get("endpoint_cancellation_exact_zero_stress_case_count")
        == EXPECTED_ENDPOINT_CANCELLATION_STRESS_ZEROS,
        "fixture stress endpoint-cancellation exact-zero count changed",
    )
    require(
        arithmetic.get("exact_identity") == "H_(k-1) + H_(n-1) - H_(nx) - H_(ny)",
        "fixture exact identity changed",
    )
    require(arithmetic.get("logarithm_unit") == "nats", "fixture information unit changed")
    require(len(fixture["cases"]) == EXPECTED_CASES, "fixture case count changed")
    endpoint_cases = [case for case in fixture["cases"] if is_endpoint_cancellation_case(case)]
    require(
        len(endpoint_cases) == EXPECTED_ENDPOINT_CANCELLATION_ZEROS,
        "fixture structural endpoint-cancellation case count changed",
    )
    require(
        all(case.get("expected_nats") == "0" for case in endpoint_cases),
        "fixture endpoint-cancellation references are not canonical exact positive zero",
    )
    canonical_zero_cases = [
        case for case in fixture["cases"] if case.get("expected_nats") == "0"
    ]
    require(
        len(canonical_zero_cases) == EXPECTED_ENDPOINT_CANCELLATION_ZEROS,
        "fixture canonical exact-zero reference count changed",
    )
    require(
        all(is_endpoint_cancellation_case(case) for case in canonical_zero_cases),
        "fixture contains a canonical exact-zero reference outside the endpoint rule",
    )
    endpoint_exhaustive_cases = [
        case for case in endpoint_cases if case["sample_count"] <= 16
    ]
    endpoint_stress_cases = [
        case for case in endpoint_cases if case["sample_count"] > 16
    ]
    require(
        len(endpoint_exhaustive_cases)
        == EXPECTED_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS,
        "fixture row-derived exhaustive endpoint-cancellation count changed",
    )
    require(
        len(endpoint_stress_cases) == EXPECTED_ENDPOINT_CANCELLATION_STRESS_ZEROS,
        "fixture row-derived stress endpoint-cancellation count changed",
    )
    require(
        fixture["bounds"]["exhaustive_case_count"] == EXPECTED_EXHAUSTIVE_CASES,
        "fixture exhaustive count changed",
    )
    require(
        fixture["bounds"]["exhaustive_max_samples"] == 16,
        "fixture exhaustive bound changed",
    )
    require(
        fixture["bounds"]["exhaustive_rule"]
        == "2 <= n <= bound; 1 <= k < n; k-1 <= nx,ny < n",
        "fixture exhaustive domain changed",
    )
    require(
        fixture["bounds"]["stress_case_count"] == EXPECTED_STRESS_CASES,
        "fixture stress count changed",
    )
    require(
        tuple(fixture["bounds"]["stress_sample_sizes"]) == EXPECTED_STRESS_SAMPLE_SIZES,
        "fixture stress sample sizes changed",
    )
    generator = fixture.get("generator")
    require(isinstance(generator, dict), "fixture generator metadata is absent")
    require(generator.get("path") == EXPECTED_GENERATOR_PATH, "fixture generator path changed")
    require(generator.get("imports_pid_rs") is False, "fixture generator imports pid-rs")
    require(
        generator.get("third_party_dependencies") == [],
        "fixture generator dependency declaration changed",
    )
    live_generator = (repo_root / EXPECTED_GENERATOR_PATH).read_bytes()
    live_generator_sha256 = hashlib.sha256(live_generator).hexdigest()
    require(
        live_generator_sha256 == EXPECTED_GENERATOR_SHA256,
        "live generator bytes changed from the reviewed revision-3 digest",
    )
    require(
        generator.get("sha256") == EXPECTED_GENERATOR_SHA256,
        "fixture is not bound to the reviewed live generator digest",
    )
    return fixture


def check_binary64_route(fixture: dict[str, Any]) -> None:
    max_argument = max(case["sample_count"] for case in fixture["cases"])
    table = shifted_harmonic_table(max_argument)
    maximum_error = 0.0
    first_maximum: tuple[int, int, int, int] | None = None
    maximum_error_ties = 0
    swap_bit_asymmetries = 0
    endpoint_direct_left_nonzeros = 0
    endpoint_direct_left_negative_zeros = 0
    for case in fixture["cases"]:
        n = case["sample_count"]
        k = case["k"]
        x = case["x_count"] + 1
        y = case["y_count"] + 1
        actual = harmonic_term(table, k, n, x, y)
        swapped = harmonic_term(table, k, n, y, x)
        swap_bit_asymmetries += actual.hex() != swapped.hex()
        expected = float(case["expected_nats"])
        if is_endpoint_cancellation_case(case):
            direct_left = ((table[k] + table[n]) - table[x]) - table[y]
            endpoint_direct_left_nonzeros += direct_left != 0.0
            endpoint_direct_left_negative_zeros += direct_left.hex() == "-0x0.0p+0"
        error = abs(actual - expected)
        if error > maximum_error:
            maximum_error = error
            first_maximum = (n, k, case["x_count"], case["y_count"])
            maximum_error_ties = 1
        elif error == maximum_error:
            maximum_error_ties += 1

    require(swap_bit_asymmetries == 0, f"found {swap_bit_asymmetries} source-swap asymmetries")
    require(
        endpoint_direct_left_nonzeros == EXPECTED_ENDPOINT_DIRECT_LEFT_NONZEROS,
        "selected-prefix ordinary-left endpoint nonzero count changed: "
        f"{endpoint_direct_left_nonzeros}",
    )
    require(
        endpoint_direct_left_negative_zeros
        == EXPECTED_ENDPOINT_DIRECT_LEFT_NEGATIVE_ZEROS,
        "selected-prefix ordinary-left endpoint negative-zero count changed: "
        f"{endpoint_direct_left_negative_zeros}",
    )
    require(maximum_error == EXPECTED_MAX_ERROR, f"observed maximum changed: {maximum_error}")
    require(
        first_maximum == EXPECTED_FIRST_MAXIMUM,
        f"first maximum-attaining tuple changed: {first_maximum}",
    )
    require(
        maximum_error_ties == EXPECTED_MAX_ERROR_TIES,
        f"maximum-error tie multiplicity changed: {maximum_error_ties}",
    )
    require(maximum_error <= ALLOWED_MAX_ERROR, "finite-corpus ceiling exceeded")


def load_release_families(repo_root: Path) -> dict[str, dict[str, Any]]:
    release_path = repo_root / "release-scope-1.0.json"
    release = json.loads(release_path.read_bytes())
    require(isinstance(release, dict), "release scope root is not an object")
    require(release.get("schema") == "pid-rs/release-scope", "release scope schema changed")
    require(release.get("schema_revision") == 1, "release scope schema revision changed")
    raw_families = release.get("families")
    require(isinstance(raw_families, list), "release scope families are not a list")
    families: dict[str, dict[str, Any]] = {}
    for index, family in enumerate(raw_families):
        require(isinstance(family, dict), f"release family {index} is not an object")
        family_id = family.get("id")
        require(
            isinstance(family_id, str) and family_id,
            f"release family {index} has no string id",
        )
        require(family_id not in families, f"duplicate release family id: {family_id}")
        families[family_id] = family
    return families


def require_release_revision(
    families: dict[str, dict[str, Any]],
    family_id: str,
    expected_definition: str,
    expected_estimator: str,
) -> None:
    require(family_id in families, f"release family is absent: {family_id}")
    family = families[family_id]
    require(
        family.get("definition_revision") == expected_definition,
        f"release definition revision changed for {family_id}: "
        f"expected {expected_definition}",
    )
    require(
        family.get("estimator_revision") == expected_estimator,
        f"release estimator revision changed for {family_id}: "
        f"expected {expected_estimator}",
    )


def check_release_route(repo_root: Path) -> None:
    release_path = repo_root / "release-scope-1.0.json"
    raw = release_path.read_bytes()
    release = json.loads(raw)
    canonical = (
        json.dumps(
            release,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    require(raw == canonical, "release scope is not canonical JSON")
    families = load_release_families(repo_root)
    require(
        len(KSG_RELEASE_REVISIONS) == 15,
        "KSG affected release-family inventory no longer contains exactly 15 rows",
    )
    require(
        len(KSG_PROTECTED_RELEASE_REVISIONS) == 20,
        "KSG protected release-family inventory no longer contains exactly 20 rows",
    )
    expected_ids = (
        set(KSG_RELEASE_REVISIONS)
        | set(KSG_PROTECTED_RELEASE_REVISIONS)
    )
    require(
        set(families) == expected_ids,
        "release family inventory changed: "
        f"missing={sorted(expected_ids - set(families))}, "
        f"unexpected={sorted(set(families) - expected_ids)}",
    )
    affected_rows = [
        family for family in release["families"] if family["id"] in KSG_RELEASE_REVISIONS
    ]
    protected_rows = [
        family
        for family in release["families"]
        if family["id"] in KSG_PROTECTED_RELEASE_REVISIONS
    ]
    metadata = {key: value for key, value in release.items() if key != "families"}
    require(
        projection_sha256(affected_rows) == KSG_AFFECTED_RELEASE_FAMILIES_SHA256,
        "a KSG-affected release family changed outside the reviewed full-object projection",
    )
    require(
        projection_sha256(protected_rows) == KSG_PROTECTED_RELEASE_FAMILIES_SHA256,
        "a protected release family changed during the KSG-only milestone",
    )
    require(
        projection_sha256(metadata) == KSG_PROTECTED_RELEASE_METADATA_SHA256,
        "release top-level metadata changed during the KSG-only milestone",
    )

    for family_id, (definition, previous_estimator, estimator) in sorted(
        KSG_RELEASE_REVISIONS.items()
    ):
        require(
            previous_estimator != estimator,
            f"{family_id}: estimator revision did not move",
        )
        require_release_revision(families, family_id, definition, estimator)
    for family_id, (definition, estimator) in sorted(
        KSG_PROTECTED_RELEASE_REVISIONS.items()
    ):
        require_release_revision(families, family_id, definition, estimator)


def check_catalog_route(repo_root: Path) -> None:
    catalog_path = repo_root / "method-catalog.json"
    raw = catalog_path.read_bytes()
    catalog = json.loads(raw)
    require(isinstance(catalog, dict), "method catalog root is not an object")
    require(catalog.get("schema") == "pid-rs/method-catalog", "method catalog schema changed")
    require(catalog.get("schema_revision") == 1, "method catalog schema revision changed")
    canonical = (
        json.dumps(
            catalog,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    require(raw == canonical, "method catalog is not canonical JSON")

    methods = catalog.get("methods")
    references = catalog.get("references")
    require(isinstance(methods, list), "method catalog methods are not a list")
    require(isinstance(references, list), "method catalog references are not a list")
    require(len(methods) == 69, "method catalog no longer contains exactly 69 methods")
    require(len(references) == 45, "method catalog no longer contains exactly 45 references")

    by_id: dict[str, dict[str, Any]] = {}
    for index, method in enumerate(methods):
        require(isinstance(method, dict), f"catalog method {index} is not an object")
        method_id = method.get("id")
        require(isinstance(method_id, str) and method_id, f"catalog method {index} has no id")
        require(method_id not in by_id, f"duplicate catalog method id: {method_id}")
        by_id[method_id] = method
    require(list(by_id) == sorted(by_id), "method catalog ids are not sorted")
    require(
        set(KSG_CATALOG_METHOD_IDS) <= set(by_id),
        "one or more KSG-affected catalog methods are absent",
    )
    reverse_dependencies: dict[str, set[str]] = {method_id: set() for method_id in by_id}
    for method_id, method in by_id.items():
        dependencies = method.get("depends_on")
        require(isinstance(dependencies, list), f"{method_id}: depends_on is not a list")
        require(
            dependencies == sorted(set(dependencies)),
            f"{method_id}: dependencies are not sorted and unique",
        )
        for dependency in dependencies:
            require(
                isinstance(dependency, str) and dependency in by_id,
                f"{method_id}: dependency target is absent: {dependency}",
            )
            reverse_dependencies[dependency].add(method_id)
    reverse_closure = set(KSG_CATALOG_ROOT_METHOD_IDS)
    frontier = list(KSG_CATALOG_ROOT_METHOD_IDS)
    while frontier:
        dependency = frontier.pop()
        for consumer in reverse_dependencies[dependency]:
            if consumer not in reverse_closure:
                reverse_closure.add(consumer)
                frontier.append(consumer)
    expected_reverse_closure = set(KSG_CATALOG_METHOD_IDS) | set(
        KSG_CATALOG_REVERSE_CLOSURE_EXCLUSIONS
    )
    require(
        reverse_closure == expected_reverse_closure,
        "KSG reverse-dependency closure changed: "
        f"missing={sorted(expected_reverse_closure - reverse_closure)}, "
        f"unexpected={sorted(reverse_closure - expected_reverse_closure)}",
    )
    require(
        reverse_closure - set(KSG_CATALOG_REVERSE_CLOSURE_EXCLUSIONS)
        == set(KSG_CATALOG_METHOD_IDS),
        "KSG affected catalog inventory is not the declared reverse closure minus the "
        "non-numerical shared-config exclusion",
    )

    protected_methods = [
        method for method in methods if method["id"] not in KSG_CATALOG_METHOD_IDS
    ]
    require(len(protected_methods) == 49, "protected catalog method count changed")
    require(
        projection_sha256(protected_methods) == KSG_PROTECTED_CATALOG_METHODS_SHA256,
        "a non-KSG catalog method changed from the KSG milestone parent",
    )
    require(
        projection_sha256(references) == KSG_PROTECTED_CATALOG_REFERENCES_SHA256,
        "catalog references changed during the KSG-only milestone",
    )
    metadata = {key: value for key, value in catalog.items() if key not in ("methods", "references")}
    require(
        projection_sha256(metadata) == KSG_PROTECTED_CATALOG_METADATA_SHA256,
        "catalog top-level metadata changed during the KSG-only milestone",
    )
    catalog_text = raw.decode("utf-8")
    for token in KSG_FORBIDDEN_CATALOG_TOKENS:
        require(token not in catalog_text, f"KSG-only catalog contains later-wave token: {token}")

    claim_bound: set[str] = set()
    formal_bound: set[str] = set()
    for method_id, method in by_id.items():
        validation = method.get("validation")
        require(isinstance(validation, dict), f"{method_id}: validation block is absent")
        evidence_paths = validation.get("evidence_paths")
        require(isinstance(evidence_paths, list), f"{method_id}: evidence_paths is not a list")
        require(
            all(isinstance(path, str) and path for path in evidence_paths),
            f"{method_id}: evidence_paths contains a non-string or empty path",
        )
        if method_id in KSG_CATALOG_METHOD_IDS:
            require(
                evidence_paths == sorted(set(evidence_paths)),
                f"{method_id}: KSG evidence_paths are not sorted and unique",
            )
        evidence = set(evidence_paths)
        if method_id in KSG_CATALOG_METHOD_IDS:
            for relative in evidence_paths:
                evidence_path = Path(relative)
                require(
                    not evidence_path.is_absolute() and ".." not in evidence_path.parts,
                    f"{method_id}: evidence path escapes the repository: {relative}",
                )
                require(
                    (repo_root / evidence_path).is_file(),
                    f"{method_id}: bound evidence target is absent: {relative}",
                )
        if "claims/KSG-INTEGER-HARMONIC-001/claim-v3.md" in evidence:
            claim_bound.add(method_id)
        if evidence & set(KSG_REQUIRED_FORMAL_CATALOG_EVIDENCE):
            formal_bound.add(method_id)
        require(
            "claims/KSG-INTEGER-HARMONIC-001/claim-v1.md" not in evidence
            and "claims/KSG-INTEGER-HARMONIC-001/claim-v2.md" not in evidence,
            f"{method_id}: active catalog evidence cites a stale KSG claim revision",
        )

    require(
        claim_bound == set(KSG_CATALOG_METHOD_IDS),
        "KSG claim-bound method inventory changed: "
        f"missing={sorted(set(KSG_CATALOG_METHOD_IDS) - claim_bound)}, "
        f"unexpected={sorted(claim_bound - set(KSG_CATALOG_METHOD_IDS))}",
    )
    require(
        formal_bound == set(KSG_FORMAL_CATALOG_METHOD_IDS),
        "KSG formal-evidence method inventory changed: "
        f"missing={sorted(set(KSG_FORMAL_CATALOG_METHOD_IDS) - formal_bound)}, "
        f"unexpected={sorted(formal_bound - set(KSG_FORMAL_CATALOG_METHOD_IDS))}",
    )
    for method_id in KSG_CATALOG_METHOD_IDS:
        method = by_id[method_id]
        validation = method["validation"]
        evidence = set(validation["evidence_paths"])
        for path in KSG_REQUIRED_CATALOG_EVIDENCE:
            require(path in evidence, f"{method_id}: required KSG evidence path absent: {path}")
        validation_text = json.dumps(validation, ensure_ascii=True).lower()
        require(
            "integer-harmonic" in validation_text or "integer harmonic" in validation_text,
            f"{method_id}: integer-harmonic validation boundary is absent",
        )
    for method_id in KSG_FORMAL_CATALOG_METHOD_IDS:
        evidence = set(by_id[method_id]["validation"]["evidence_paths"])
        for path in KSG_REQUIRED_FORMAL_CATALOG_EVIDENCE:
            require(path in evidence, f"{method_id}: formal KSG evidence path absent: {path}")

    shared_config_evidence = set(
        by_id["mutual-information.ksg1-shared-config"]["validation"]["evidence_paths"]
    )
    require(
        not any("KSG-INTEGER-HARMONIC-001" in path for path in shared_config_evidence),
        "unchanged shared KSG config is incorrectly bound to the arithmetic claim",
    )


def check_source_route(repo_root: Path) -> None:
    # These guards deliberately remain bounded textual evidence. They reject the named live-code
    # shadow/overwrite attacks after masking comments and strings, but they are not a compiler
    # def-use proof; compiled corpus and tiny count witnesses are the semantic backstop.
    stats_source = (repo_root / "crates/pid-core/src/stats.rs").read_text(encoding="utf-8")
    ksg_source = (repo_root / "crates/pid-core/src/ksg.rs").read_text(encoding="utf-8")
    isx_source = (repo_root / "crates/pid-core/src/isx.rs").read_text(encoding="utf-8")
    pid3_source = (repo_root / "crates/pid-core/src/pid3.rs").read_text(encoding="utf-8")
    stats = mask_rust_noncode(stats_source)
    ksg = mask_rust_noncode(ksg_source)
    isx = mask_rust_noncode(isx_source)
    pid3 = mask_rust_noncode(pid3_source)

    prefix_body = rust_function_body(stats, "shifted_harmonic_table")
    term_body = rust_function_body(stats, "ksg_local_harmonic_term")
    heuristic_body = rust_function_body(isx, "isx_redundancy_heuristic_sketch")
    w1_body = rust_function_body(
        ksg, "ksg_ordered_count_witness_reaches_production_diagnostics"
    )

    for marker in (
        "pub(crate) fn shifted_harmonic_table(n: usize)",
        "pub(crate) fn ksg_local_harmonic_term(",
        "const KSG_LOCAL_ARITHMETIC_OBSERVED_MAX_ERROR_NATS: f64 = 8.0 * f64::EPSILON;",
        "const KSG_LOCAL_ARITHMETIC_MAX_ERROR_NATS: f64 = 32.0 * f64::EPSILON;",
    ):
        require(marker in stats, f"shifted-harmonic source marker absent: {marker}")
    for marker in (
        "let len = n.checked_add(1)",
        "for argument in 2..=n",
        "let value = 1.0 / (argument - 1) as f64;",
        "if sum.abs() >= value.abs()",
        "correction += (sum - next) + value;",
        "correction += (value - next) + sum;",
        "out[argument] = sum + correction;",
    ):
        require(
            prefix_body.count(marker) == 1,
            f"shifted-harmonic prefix marker count changed: {marker}",
        )
    require(
        prefix_body.count("out[argument]") == 1,
        "shifted-harmonic prefix output has multiple live reads or writes",
    )
    for marker in (
        "let lower = x.min(y);",
        "let upper = x.max(y);",
        "(shifted_harmonics[n] - shifted_harmonics[upper])",
        "(shifted_harmonics[lower] - shifted_harmonics[k])",
    ):
        require(
            term_body.count(marker) == 1,
            f"source-symmetric range marker count changed: {marker}",
        )
    require(term_body.count("let lower =") == 1, "lower range binding is shadowed or duplicated")
    require(term_body.count("let upper =") == 1, "upper range binding is shadowed or duplicated")

    require(ksg.count("ksg_local_harmonic_term(") == 4, "KSG direct call-site count changed")
    require(
        len(re.findall(r"nx \+ 1,\s*ny \+ 1", ksg)) == 4,
        "KSG exclusive-count off-by-one map changed",
    )
    require("digamma(" not in ksg and "digamma_int_table" not in ksg, "KSG retained digamma")
    require_runtime_estimator_revision(
        mask_rust_comments(ksg_source),
        ksg,
        "ksg_mi_report_with_kernel_and_cancellation",
        "strict-unique-shell-integer-harmonic-report-v4",
    )
    for marker in (
        "let row = diagnostics[5];",
        "assert_eq!(row.joint_radius.to_bits(), 79.0_f64.to_bits());",
        "assert_eq!((row.x_count, row.y_count), (4, 1));",
        "assert_eq!(row.term_nats.to_bits(), 0x3fe0_4e04_e04e_04e0);",
    ):
        require(marker in w1_body, f"W1 production-diagnostic marker absent: {marker}")

    require(isx.count("ksg_local_harmonic_term(") == 1, "ISX eligible call-site count changed")
    require("&shifted_harmonics, k, n, n_alpha, n_t" in isx, "ISX inclusive index map changed")
    for marker in (
        "let psi_k = digamma(k as f64);",
        "let psi_n = digamma(n as f64);",
        "let psi_int = digamma_int_table(n)?;",
        "let psi_shared = psi_int[n_t_shared[i] + 1];",
        "let psi_s1 = psi_int[n_t_s1[i] + 1];",
        "let psi_s2 = psi_int[n_t_s2[i] + 1];",
        "psi_shared - 0.5 * (psi_s1 + psi_s2)",
        "let redundancy = psi_k + psi_n + avg_term;",
    ):
        require(marker in heuristic_body, f"non-cancelling heuristic marker absent: {marker}")
    require_runtime_estimator_revision(
        mask_rust_comments(isx_source),
        isx,
        "isx_redundancy_report_with_local_terms",
        "strict-unique-shell-integer-harmonic-isx-v4",
    )

    require(pid3.count("ksg_local_harmonic_term(") == 1, "PID3 eligible call-site count changed")
    require("n_alpha,\n            n_t," in pid3, "PID3 inclusive index map changed")
    require("digamma(" not in pid3 and "digamma_int_table" not in pid3, "PID3 retained digamma")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="pid-rs checkout to inspect (defaults to this script's repository)",
    )
    route = parser.add_mutually_exclusive_group()
    route.add_argument(
        "--claim-only",
        action="store_true",
        help=(
            "check only canonical revision-4 claim custody and semantics; this preclosure route "
            "does not imply repository integration GO"
        ),
    )
    route.add_argument(
        "--release-only",
        action="store_true",
        help=(
            "check only the release-family migration; intended for isolated mutation replay, "
            "not as a substitute for the default complete claim checker"
        ),
    )
    route.add_argument(
        "--source-only",
        action="store_true",
        help="check only Rust source correspondence for isolated mutation replay",
    )
    route.add_argument(
        "--exact-only",
        action="store_true",
        help="check only the exact rational identity for isolated mutation replay",
    )
    route.add_argument(
        "--binary64-only",
        action="store_true",
        help="check only the committed binary64 corpus for isolated mutation replay",
    )
    route.add_argument(
        "--catalog-only",
        action="store_true",
        help="check only the exact KSG method-catalog binding for isolated mutation replay",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = args.repo_root.resolve()
        if args.claim_only:
            check_claim_route(repo_root)
            print(
                "KSG harmonic-revision claim check passed: active revision 4 "
                "integration_no_go; 65 mapped files; 35 historical hashes"
            )
            return 0
        if args.release_only:
            check_release_route(repo_root)
            print(
                "KSG harmonic-revision release check passed: 15 affected and "
                "20 protected families"
            )
            return 0
        if args.source_only:
            check_source_route(repo_root)
            print("KSG harmonic-revision source check passed")
            return 0
        if args.exact_only:
            check_exact_route()
            print("KSG harmonic-revision exact check passed: 6,920 tuples")
            return 0
        if args.binary64_only:
            check_binary64_route(load_fixture(repo_root))
            print(
                "KSG harmonic-revision binary64 check passed: 8,198 Decimal cells; "
                "observed max 8 eps with 40 ties, allowed 32 eps, zero source-swap asymmetries"
            )
            return 0
        if args.catalog_only:
            check_catalog_route(repo_root)
            print("KSG harmonic-revision catalog check passed: 20 affected and 6 formal-bound methods")
            return 0
        check_claim_route(repo_root)
        check_release_route(repo_root)
        check_exact_route()
        fixture = load_fixture(repo_root)
        check_binary64_route(fixture)
        check_source_route(repo_root)
        check_catalog_route(repo_root)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"KSG harmonic-revision check failed: {error}", file=sys.stderr)
        return 1
    print(
        "KSG harmonic-revision check passed: 6,920 exact tuples and 8,198 Decimal cells; "
        "observed max 8 eps with 40 ties, allowed 32 eps, zero source-swap asymmetries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Artifact: `scripts/check-ksg-harmonic-revision-self-test.py`

SHA-256: `cc048f2bd7518ff6309a416af1952a8be77ff8c0e31a030e2e4db4e09e874943`

```text
#!/usr/bin/env python3
"""Mutation adequacy checks for check-ksg-harmonic-revision.py."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-ksg-harmonic-revision.py"
ACTIVE_PACKET = ROOT / "claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json"
EXECUTION_MODES = (("normal", False), ("optimized", True))
SUCCESS_LINES = {
    None: (
        "KSG harmonic-revision check passed: 6,920 exact tuples and 8,198 Decimal cells; "
        "observed max 8 eps with 40 ties, allowed 32 eps, zero source-swap asymmetries"
    ),
    "--release-only": (
        "KSG harmonic-revision release check passed: 15 affected and 20 protected families"
    ),
    "--source-only": "KSG harmonic-revision source check passed",
    "--exact-only": "KSG harmonic-revision exact check passed: 6,920 tuples",
    "--binary64-only": (
        "KSG harmonic-revision binary64 check passed: 8,198 Decimal cells; "
        "observed max 8 eps with 40 ties, allowed 32 eps, zero source-swap asymmetries"
    ),
    "--catalog-only": (
        "KSG harmonic-revision catalog check passed: 20 affected and 6 formal-bound methods"
    ),
    "--claim-only": (
        "KSG harmonic-revision claim check passed: active revision 4 integration_no_go; "
        "65 mapped files; 35 historical hashes"
    ),
}
EXPECTED_MUTATIONS = {
    "checker-model": 8,
    "fixture-custody": 2,
    "fixture-semantics": 3,
    "textual-source": 20,
    "release": 73,
    "catalog": 36,
}
EXPECTED_SCOPE_ISOLATION_PREFLIGHTS = 2
EXPECTED_CLAIM_MUTATIONS = {
    "custody": 3,
    "manifest-structure": 9,
    "resealed-semantics": 15,
}

KSG_STALE_RELEASE_REVISIONS = (
    (
        "pid-core.stable.continuous",
        "strict-unique-shell-report-v3",
    ),
    (
        "pid-core.experimental.continuous.co-information",
        "ksg-derived-co-information-v1",
    ),
    ("pid-core.experimental.continuous.isx", "strict-unique-shell-isx-v3"),
    (
        "pid-core.experimental.continuous.pid2",
        "separate-biased-term-pid2-v1",
    ),
    (
        "pid-core.experimental.continuous.incomplete-pid3",
        "equal-ambient-branch-screen-v1",
    ),
    ("pid-core.research.raw-ksg", "ksg-chebyshev-raw-v1"),
    ("pid-core.research.raw-isx", "ehrlich-local-knn-raw-v1"),
    ("pid-core.research.raw-co-information", "ksg-co-information-raw-v1"),
    (
        "pid-core.research.isx-heuristics",
        "heuristic-baselines-v1",
    ),
    (
        "pid-core.research.mixed-dimension-pid3",
        "mixed-dimensional-pid3-reference-v1",
    ),
    ("pid-core.research.hyperbolic", "lorentz-geometry-safe-rust-v1"),
    (
        "pid-core.experimental.hierarchy",
        "hierarchy-screening-v1",
    ),
    (
        "pid-core.experimental.pipelines.pid3-permutation",
        "explicit-seed-pid3-permutation-v1",
    ),
    (
        "pid-core.experimental.pipelines.pls-selection-and-composition",
        "deterministic-pls-cv-v1",
    ),
    (
        "pid-core.experimental.pipelines.pid2-screening",
        "deterministic-pair-enumeration-v1",
    ),
)

KSG_PROTECTED_RELEASE_FAMILIES = (
    "pid-core.infrastructure",
    "pid-core.stable.categorical",
    "pid-core.stable.quantized",
    "pid-core.stable.imin",
    "pid-core.stable.preprocessing",
    "pid-core.diagnostics.distance-matrix",
    "pid-core.diagnostics.geometry",
    "pid-core.diagnostics.invariants",
    "pid-core.diagnostics.support",
    "pid-core.experimental.continuous.shared-ksg-config",
    "pid-core.experimental.pipelines.block-resampling",
    "pid-core.experimental.pipelines.logistic-regression",
    "pid-core.experimental.pipelines.fdr-adjustment",
    "pid-core.experimental.pipelines.quantized-sxpid-bootstrap",
    "pid-core.experimental.pipelines.row-bootstrap",
    "pid-core.experimental.pipelines.permutation-contracts",
    "pid-core.experimental.pipelines.row-permutation",
    "pid-core.experimental.pipelines.gaussian-noise-provenance",
    "pid-core.experimental.pipelines.jitter-preprocessing",
    "pid-core.experimental.pipelines.same-sample-quantization",
)
KSG_CATALOG_METHOD_IDS = (
    "co-information.continuous-raw",
    "co-information.continuous-report",
    "mutual-information.hyperbolic-ksg",
    "mutual-information.ksg1-raw",
    "mutual-information.ksg1-report",
    "mutual-information.ksg1-sensitivity-trajectories",
    "pid.continuous-pid2",
    "pid.incomplete-continuous-pid3",
    "pid.mixed-dimension-pid3",
    "pipelines.hierarchy-screening",
    "pipelines.pid2-screening",
    "pipelines.pid3-permutation",
    "pipelines.pls-pid-composition",
    "shannon-invariants.continuous-ksg-composition",
    "shared-exclusions.continuous-heuristics",
    "shared-exclusions.continuous-raw",
    "shared-exclusions.continuous-report",
    "software.python-experimental-migration-bindings",
    "software.python-v1-bindings",
    "validation.exp0",
)
KSG_FORMAL_CATALOG_METHOD_IDS = (
    "mutual-information.ksg1-raw",
    "mutual-information.ksg1-report",
    "pid.incomplete-continuous-pid3",
    "pid.mixed-dimension-pid3",
    "shared-exclusions.continuous-raw",
    "shared-exclusions.continuous-report",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, mutation: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{mutation}: replacement anchor occurs {count} times instead of once")
    return text.replace(old, new, 1)


def run_checker(
    checker: Path,
    repo_root: Path,
    *,
    optimized: bool,
    route: str | None = None,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend([str(checker), "--repo-root", str(repo_root)])
    if route is not None:
        command.append(route)
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def require_exact_acceptance_in_all_modes(
    checker: Path,
    repo_root: Path,
    *,
    route: str | None = None,
    cwd: Path = ROOT,
) -> None:
    expected_stdout = SUCCESS_LINES[route] + "\n"
    for mode, optimized in EXECUTION_MODES:
        result = run_checker(
            checker,
            repo_root,
            optimized=optimized,
            route=route,
            cwd=cwd,
        )
        if (
            result.returncode != 0
            or result.stdout != expected_stdout
            or result.stderr != ""
        ):
            fail(
                f"unmodified checker failed its exact {route or 'all'} contract in {mode} mode\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


def require_rejection_in_all_modes(
    checker: Path,
    repo_root: Path,
    mutation: str,
    *,
    route: str | None = None,
    cwd: Path = ROOT,
) -> None:
    for mode, optimized in EXECUTION_MODES:
        result = run_checker(
            checker,
            repo_root,
            optimized=optimized,
            route=route,
            cwd=cwd,
        )
        diagnostics = result.stderr.splitlines()
        if (
            result.returncode != 1
            or result.stdout != ""
            or len(diagnostics) != 1
            or not diagnostics[0].startswith("KSG harmonic-revision check failed: ")
        ):
            fail(
                f"{mutation}: checker did not fail through one clean diagnostic in {mode} mode\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )


def copy_route(destination: Path) -> None:
    for relative in (
        Path("crates/pid-core/src/stats.rs"),
        Path("crates/pid-core/src/ksg.rs"),
        Path("crates/pid-core/src/isx.rs"),
        Path("crates/pid-core/src/pid3.rs"),
        Path("crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"),
        Path("crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256"),
        Path("scripts/generate-ksg-local-arithmetic-oracle.py"),
        Path("release-scope-1.0.json"),
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def copy_catalog_route(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "method-catalog.json", destination / "method-catalog.json")
    catalog = json.loads((ROOT / "method-catalog.json").read_bytes())
    affected = {
        method["id"]: method
        for method in catalog["methods"]
        if method["id"] in KSG_CATALOG_METHOD_IDS
    }
    if set(affected) != set(KSG_CATALOG_METHOD_IDS):
        fail("catalog copy route cannot resolve the exact KSG-affected method inventory")
    for method in affected.values():
        for relative_text in method["validation"]["evidence_paths"]:
            relative = Path(relative_text)
            if relative.is_absolute() or ".." in relative.parts:
                fail(f"catalog copy route found escaping evidence path: {relative_text}")
            source = ROOT / relative
            if not source.is_file():
                fail(f"catalog copy route found absent evidence target: {relative_text}")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def copy_claim_route(destination: Path) -> None:
    manifest = json.loads(ACTIVE_PACKET.read_bytes())
    packet_files = manifest.get("packet_files")
    if not isinstance(packet_files, dict):
        fail("claim copy route cannot resolve the active packet file map")
    relatives = [Path(relative) for relative in packet_files]
    relatives.append(ACTIVE_PACKET.relative_to(ROOT))
    for relative in relatives:
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            fail(f"claim copy route found a non-regular source: {relative}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def checker_rebound_to_manifest(
    checker_text: str,
    manifest_raw: bytes,
    mutation: str,
) -> str:
    baseline_digest = hashlib.sha256(ACTIVE_PACKET.read_bytes()).hexdigest()
    replacement_digest = hashlib.sha256(manifest_raw).hexdigest()
    old = f"EXPECTED_ACTIVE_PACKET_SHA256 = '{baseline_digest}'"
    new = f"EXPECTED_ACTIVE_PACKET_SHA256 = '{replacement_digest}'"
    return replace_once(checker_text, old, new, f"{mutation}-manifest-envelope")


def write_rebound_manifest_case(
    checker_text: str,
    case_root: Path,
    temporary: Path,
    manifest_raw: bytes,
    mutation: str,
) -> Path:
    manifest_path = case_root / ACTIVE_PACKET.relative_to(ROOT)
    manifest_path.write_bytes(manifest_raw)
    checker = temporary / f"{mutation}-checker.py"
    checker.write_text(
        checker_rebound_to_manifest(checker_text, manifest_raw, mutation),
        encoding="utf-8",
    )
    return checker


def mutate_release_field(
    path: Path, family_id: str, field: str, value: str, mutation: str
) -> None:
    release = json.loads(path.read_text(encoding="utf-8"))
    matches = [family for family in release["families"] if family.get("id") == family_id]
    if len(matches) != 1:
        fail(f"{mutation}: release family match count is {len(matches)}")
    matches[0][field] = value
    path.write_text(
        json.dumps(release, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def check_checker_mutations(checker_text: str, temporary: Path) -> list[str]:
    mutations = (
        (
            "corrupt-exact-k-index",
            "harmonics[k - 1] + harmonics[n - 1]",
            "harmonics[k] + harmonics[n - 1]",
            "--exact-only",
        ),
        (
            "accept-seven-eps",
            "EXPECTED_MAX_ERROR = 8.0",
            "EXPECTED_MAX_ERROR = 7.0",
            "--binary64-only",
        ),
        (
            "accept-wrong-case-count",
            "EXPECTED_CASES = 8_198",
            "EXPECTED_CASES = 8_197",
            "--binary64-only",
        ),
        (
            "accept-wrong-maximum-tie-count",
            "EXPECTED_MAX_ERROR_TIES = 40",
            "EXPECTED_MAX_ERROR_TIES = 39",
            "--binary64-only",
        ),
        (
            "accept-wrong-endpoint-cancellation-count",
            "EXPECTED_ENDPOINT_CANCELLATION_ZEROS = 354",
            "EXPECTED_ENDPOINT_CANCELLATION_ZEROS = 353",
            "--binary64-only",
        ),
        (
            "shift-endpoint-cancellation-predicate",
            'low = case["k"] - 1',
            'low = case["k"]',
            "--binary64-only",
        ),
        (
            "accept-wrong-selected-prefix-direct-left-nonzero-count",
            "EXPECTED_ENDPOINT_DIRECT_LEFT_NONZEROS = 150",
            "EXPECTED_ENDPOINT_DIRECT_LEFT_NONZEROS = 149",
            "--binary64-only",
        ),
        (
            "accept-wrong-selected-prefix-direct-left-negative-zero-count",
            "EXPECTED_ENDPOINT_DIRECT_LEFT_NEGATIVE_ZEROS = 0",
            "EXPECTED_ENDPOINT_DIRECT_LEFT_NEGATIVE_ZEROS = 1",
            "--binary64-only",
        ),
    )
    killed: list[str] = []
    for mutation, old, new, route in mutations:
        mutated = replace_once(checker_text, old, new, mutation)
        checker = temporary / f"{mutation}.py"
        checker.write_text(mutated, encoding="utf-8")
        require_rejection_in_all_modes(checker, ROOT, mutation, route=route)
        killed.append(mutation)
    return killed


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def check_claim_custody_mutations(checker_text: str, temporary: Path) -> list[str]:
    killed: list[str] = []

    deletion = "claim-packet-mapped-file-deletion"
    deletion_root = temporary / deletion
    copy_claim_route(deletion_root)
    (
        deletion_root
        / "claims/KSG-INTEGER-HARMONIC-001/routes-v4.md"
    ).unlink()
    require_rejection_in_all_modes(
        CHECKER,
        deletion_root,
        deletion,
        route="--claim-only",
    )
    killed.append(deletion)

    unresealed = "claim-packet-unresealed-leaf-edit"
    unresealed_root = temporary / unresealed
    copy_claim_route(unresealed_root)
    unresealed_path = (
        unresealed_root
        / "claims/KSG-INTEGER-HARMONIC-001/obligations-v4.md"
    )
    unresealed_path.write_bytes(
        unresealed_path.read_bytes() + b"\nmutation: unresealed claim edit\n"
    )
    require_rejection_in_all_modes(
        CHECKER,
        unresealed_root,
        unresealed,
        route="--claim-only",
    )
    killed.append(unresealed)

    pin = "claim-checker-manifest-digest-pin"
    baseline_digest = hashlib.sha256(ACTIVE_PACKET.read_bytes()).hexdigest()
    mutated_checker = replace_once(
        checker_text,
        f"EXPECTED_ACTIVE_PACKET_SHA256 = '{baseline_digest}'",
        f"EXPECTED_ACTIVE_PACKET_SHA256 = '{'0' * 64}'",
        pin,
    )
    checker = temporary / f"{pin}.py"
    checker.write_text(mutated_checker, encoding="utf-8")
    require_rejection_in_all_modes(
        checker,
        ROOT,
        pin,
        route="--claim-only",
    )
    killed.append(pin)
    return killed


def check_claim_manifest_mutations(checker_text: str, temporary: Path) -> list[str]:
    baseline_raw = ACTIVE_PACKET.read_bytes()
    baseline = json.loads(baseline_raw)
    killed: list[str] = []

    symlink = "claim-packet-symlink-leaf"
    symlink_root = temporary / symlink
    copy_claim_route(symlink_root)
    symlink_path = symlink_root / "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"
    symlink_path.unlink()
    symlink_path.symlink_to("claim-v3.md")
    require_rejection_in_all_modes(
        CHECKER,
        symlink_root,
        symlink,
        route="--claim-only",
    )
    killed.append(symlink)

    def canonical_case(
        mutation: str,
        transform: Callable[[dict[str, Any]], None],
    ) -> None:
        case_root = temporary / mutation
        copy_claim_route(case_root)
        value = json.loads(json.dumps(baseline))
        transform(value)
        raw = canonical_json_bytes(value)
        checker = write_rebound_manifest_case(
            checker_text,
            case_root,
            temporary,
            raw,
            mutation,
        )
        require_rejection_in_all_modes(
            checker,
            case_root,
            mutation,
            route="--claim-only",
        )
        killed.append(mutation)

    def path_escape(value: dict[str, Any]) -> None:
        value["packet_files"]["../outside-claim-artifact"] = "0" * 64

    canonical_case("claim-packet-path-escape", path_escape)

    def mapped_digest_mutation(value: dict[str, Any]) -> None:
        value["packet_files"][
            "claims/KSG-INTEGER-HARMONIC-001/routes-v4.md"
        ] = "0" * 64

    canonical_case("claim-packet-mapped-digest-mutation", mapped_digest_mutation)

    duplicate = "claim-packet-duplicate-json-key"
    duplicate_root = temporary / duplicate
    copy_claim_route(duplicate_root)
    duplicate_raw = baseline_raw.replace(
        b'{\n  "active_revision": 4,',
        b'{\n  "active_revision": 4,\n  "active_revision": 4,',
        1,
    )
    checker = write_rebound_manifest_case(
        checker_text,
        duplicate_root,
        temporary,
        duplicate_raw,
        duplicate,
    )
    require_rejection_in_all_modes(
        checker,
        duplicate_root,
        duplicate,
        route="--claim-only",
    )
    killed.append(duplicate)

    noncanonical = "claim-packet-noncanonical-json"
    noncanonical_root = temporary / noncanonical
    copy_claim_route(noncanonical_root)
    noncanonical_raw = baseline_raw + b"\n"
    checker = write_rebound_manifest_case(
        checker_text,
        noncanonical_root,
        temporary,
        noncanonical_raw,
        noncanonical,
    )
    require_rejection_in_all_modes(
        checker,
        noncanonical_root,
        noncanonical,
        route="--claim-only",
    )
    killed.append(noncanonical)

    canonical_case(
        "claim-packet-active-revision-change",
        lambda value: value.__setitem__("active_revision", 3),
    )

    def multiple_active(value: dict[str, Any]) -> None:
        value["revision_history"][2]["active"] = True

    canonical_case("claim-packet-multiple-active-revisions", multiple_active)
    canonical_case(
        "claim-packet-status-promotion",
        lambda value: value.__setitem__("status", "integration_go"),
    )
    canonical_case(
        "claim-packet-premature-final-stage",
        lambda value: value.__setitem__("packet_stage", "immutable_final_m1c"),
    )
    return killed


def check_claim_resealed_semantic_mutations(
    checker_text: str,
    temporary: Path,
) -> list[str]:
    semantic_mutations = (
        (
            "claim-domain-runtime-k-le-n",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "n >= 2\n1 <= k < n\nk <= x <= n\nk <= y <= n.",
            "n >= 2\n1 <= k <= n\nk <= x <= n\nk <= y <= n.",
        ),
        (
            "claim-corpus-row-count",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "The fixture contains 8,198 unique ordered rows",
            "The fixture contains 8,197 unique ordered rows",
        ),
        (
            "claim-endpoint-segment-split",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "354 rows, split into 240 exhaustive and 114 stress rows.",
            "354 rows, split into 239 exhaustive and 115 stress rows.",
        ),
        (
            "claim-selected-signed-zero",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "selected endpoint negative zeros   = 0",
            "selected endpoint negative zeros   = 1",
        ),
        (
            "claim-selected-prefix-association-count",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "ordinary four-term\nleft association is nonzero at 150/354 endpoints",
            "ordinary four-term\nleft association is nonzero at 149/354 endpoints",
        ),
        (
            "claim-absolute-error-measure-not-ulp",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "The `8*EPSILON` quantity is an absolute error in nats, not eight ULPs",
            "The `8*EPSILON` quantity is eight ULPs",
        ),
        (
            "claim-selected-versus-naive-prefix-distinction",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "The naive\nprefix has a different 121/354 result",
            "The naive\nprefix has the same 150/354 result",
        ),
        (
            "claim-lean-inventory",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "It checks 19 theorem declarations and kills 14/14 baseline-first semantic mutations.",
            "It checks 18 theorem declarations and kills 13/13 baseline-first semantic mutations.",
        ),
        (
            "claim-z3-inventory",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "four satisfiable positive preflights, four unsatisfiable negated obligations, and 12/12",
            "three satisfiable positive preflights, three unsatisfiable negated obligations, and 11/11",
        ),
        (
            "claim-modular-implication-direction",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "modular-zero-residue-collisions-v4.md"
            ),
            "nonzero residue => exact rational nonzero.",
            "zero residue => exact rational zero.",
        ),
        (
            "claim-modular-crt-role",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "modular-zero-residue-collisions-v4.md"
            ),
            "The selected triple provides redundant fault diversity. It is not CRT reconstruction",
            "The selected triple provides independent proof by CRT reconstruction",
        ),
        (
            "claim-historical-final-certificate-distinction",
            Path(
                "claims/KSG-INTEGER-HARMONIC-001/failures/"
                "modular-zero-residue-collisions-v4.md"
            ),
            "Canonical final custody is\n"
            "`ae4645c3c9db7e8ad39d74edb1093114aeefc99d9ca9f41285ffffaeab277102`.",
            "Canonical final custody is\n"
            "`1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc`.",
        ),
        (
            "claim-mgw-nontransfer-firewall",
            Path("claims/KSG-INTEGER-HARMONIC-001/claim-v4.md"),
            "categorical Makkeh--Gutknecht--Wibral shared-exclusions PID;",
            "categorical Makkeh--Gutknecht--Wibral shared-exclusions PID is proved;",
        ),
        (
            "claim-ordered-position-not-ulp",
            Path("claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v4.md"),
            "ordered-binary64 positions. This wording does not assert eight ULPs",
            "ULPs. This wording asserts eight ULPs",
        ),
        (
            "claim-preclosure-manifest-not-final",
            Path("claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md"),
            "Immutable final `evidence-matrix-v4.md` and `decision-v4.md` are deliberately",
            "Immutable final `evidence-matrix-v4.md` and `decision-v4.md` are already",
        ),
    )
    baseline_manifest = json.loads(ACTIVE_PACKET.read_bytes())
    killed: list[str] = []
    for mutation, relative, old, new in semantic_mutations:
        case_root = temporary / mutation
        copy_claim_route(case_root)
        leaf = case_root / relative
        original = leaf.read_text(encoding="utf-8")
        leaf.write_text(
            replace_once(original, old, new, mutation),
            encoding="utf-8",
        )

        # Hash-first custody must reject the edit before any resealing.  This first rejection and
        # the semantic rejection below are two stages of one mutation, not two independent hashes.
        require_rejection_in_all_modes(
            CHECKER,
            case_root,
            f"{mutation}-unresealed-custody",
            route="--claim-only",
        )

        manifest = json.loads(json.dumps(baseline_manifest))
        relative_text = relative.as_posix()
        manifest["packet_files"][relative_text] = hashlib.sha256(
            leaf.read_bytes()
        ).hexdigest()
        manifest_raw = canonical_json_bytes(manifest)
        checker = write_rebound_manifest_case(
            checker_text,
            case_root,
            temporary,
            manifest_raw,
            mutation,
        )
        require_rejection_in_all_modes(
            checker,
            case_root,
            f"{mutation}-resealed-semantic",
            route="--claim-only",
        )
        killed.append(mutation)
    return killed


def check_fixture_custody_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-custody-repo"
    copy_route(copied_root)
    checker = temporary / "custody-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--binary64-only",
    )
    generator_path = copied_root / "scripts/generate-ksg-local-arithmetic-oracle.py"
    fixture_path = (
        copied_root / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
    )
    sidecar_path = fixture_path.with_suffix(fixture_path.suffix + ".sha256")
    original_generator = generator_path.read_bytes()
    mutated_generator = original_generator + b"\n# mutation: reviewed generator bytes changed\n"

    generator_path.write_bytes(mutated_generator)
    require_rejection_in_all_modes(
        checker,
        copied_root,
        "live-generator-drift",
        route="--binary64-only",
    )

    original_fixture = json.loads(fixture_path.read_bytes())
    fixture = json.loads(json.dumps(original_fixture))
    fixture["generator"]["sha256"] = hashlib.sha256(mutated_generator).hexdigest()
    resealed = canonical_json_bytes(fixture)
    fixture_path.write_bytes(resealed)
    resealed_digest = hashlib.sha256(resealed).hexdigest()
    sidecar_path.write_text(
        f"{resealed_digest}  {fixture_path.name}\n",
        encoding="utf-8",
        newline="",
    )
    require_rejection_in_all_modes(
        checker,
        copied_root,
        "resealed-generator-and-fixture-metadata",
        route="--binary64-only",
    )
    return ["live-generator-drift", "resealed-generator-and-fixture-metadata"]


def check_fixture_semantic_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-fixture-semantic-repo"
    copy_route(copied_root)
    checker = temporary / "fixture-semantic-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--binary64-only",
    )

    fixture_path = (
        copied_root / "crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json"
    )
    sidecar_path = fixture_path.with_suffix(fixture_path.suffix + ".sha256")
    original_fixture = json.loads(fixture_path.read_bytes())
    fixture = json.loads(json.dumps(original_fixture))
    matches = [
        case
        for case in fixture["cases"]
        if (
            case["sample_count"],
            case["k"],
            case["x_count"],
            case["y_count"],
        )
        == (256, 64, 63, 255)
    ]
    if len(matches) != 1:
        fail(f"fixture endpoint semantic mutation match count changed: {len(matches)}")
    matches[0]["expected_nats"] = "1E-79"
    resealed = canonical_json_bytes(fixture)
    fixture_path.write_bytes(resealed)
    sidecar_path.write_text(
        f"{hashlib.sha256(resealed).hexdigest()}  {fixture_path.name}\n",
        encoding="utf-8",
        newline="",
    )
    mutation = "resealed-endpoint-cancellation-nonzero-reference"
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--binary64-only",
    )
    mutations = [mutation]

    fixture = json.loads(json.dumps(original_fixture))
    matches = [
        case
        for case in fixture["cases"]
        if (
            case["sample_count"],
            case["k"],
            case["x_count"],
            case["y_count"],
        )
        == (4, 1, 0, 0)
    ]
    if len(matches) != 1:
        fail(f"fixture non-endpoint semantic mutation match count changed: {len(matches)}")
    matches[0]["expected_nats"] = "0"
    resealed = canonical_json_bytes(fixture)
    fixture_path.write_bytes(resealed)
    sidecar_path.write_text(
        f"{hashlib.sha256(resealed).hexdigest()}  {fixture_path.name}\n",
        encoding="utf-8",
        newline="",
    )
    mutation = "resealed-nonendpoint-canonical-zero-reference"
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--binary64-only",
    )
    mutations.append(mutation)

    fixture = json.loads(json.dumps(original_fixture))
    matches = [
        case
        for case in fixture["cases"]
        if (
            case["sample_count"],
            case["k"],
            case["x_count"],
            case["y_count"],
        )
        == (16, 5, 4, 15)
    ]
    if len(matches) != 1:
        fail(f"fixture split semantic mutation match count changed: {len(matches)}")
    matches[0]["sample_count"] = 17
    matches[0]["y_count"] = 16
    resealed = canonical_json_bytes(fixture)
    fixture_path.write_bytes(resealed)
    sidecar_path.write_text(
        f"{hashlib.sha256(resealed).hexdigest()}  {fixture_path.name}\n",
        encoding="utf-8",
        newline="",
    )
    mutation = "resealed-endpoint-moved-from-exhaustive-to-stress"
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--binary64-only",
    )
    mutations.append(mutation)
    return mutations


def check_source_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-repo"
    copy_route(copied_root)
    checker = temporary / "unmodified-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--source-only",
    )
    mutations = (
        (
            "naive-prefix-discards-compensation",
            Path("crates/pid-core/src/stats.rs"),
            "out[argument] = sum + correction;",
            "out[argument] = sum;",
        ),
        (
            "drop-neumaier-correction-branch",
            Path("crates/pid-core/src/stats.rs"),
            "} else {\n"
            "            correction += (value - next) + sum;\n"
            "        }\n"
            "        sum = next;\n"
            "        out[argument] = sum + correction;",
            "} else {\n"
            "            correction += 0.0;\n"
            "        }\n"
            "        sum = next;\n"
            "        out[argument] = sum + correction;",
        ),
        (
            "remove-source-symmetric-upper",
            Path("crates/pid-core/src/stats.rs"),
            "let upper = x.max(y);",
            "let upper = x;",
        ),
        (
            "shadow-source-symmetric-lower",
            Path("crates/pid-core/src/stats.rs"),
            "let lower = x.min(y);",
            "let lower = x.min(y);\n    let _ = lower;\n    let lower = x;",
        ),
        (
            "shadow-source-symmetric-upper",
            Path("crates/pid-core/src/stats.rs"),
            "let upper = x.max(y);",
            "let upper = x.max(y);\n    let _ = upper;\n    let upper = x;",
        ),
        (
            "overwrite-compensated-prefix-output",
            Path("crates/pid-core/src/stats.rs"),
            "out[argument] = sum + correction;",
            "out[argument] = sum + correction;\n"
            "        let _ = out[argument];\n"
            "        out[argument] = sum;",
        ),
        (
            "comment-decoy-cannot-hide-missing-lower",
            Path("crates/pid-core/src/stats.rs"),
            "let lower = x.min(y);",
            "// let lower = x.min(y);\n    let lower = x;",
        ),
        (
            "string-decoy-cannot-hide-missing-upper",
            Path("crates/pid-core/src/stats.rs"),
            "let upper = x.max(y);",
            "let _range_marker_decoy = \"let upper = x.max(y);\";\n    let upper = x;",
        ),
        (
            "loosen-finite-ceiling",
            Path("crates/pid-core/src/stats.rs"),
            "const KSG_LOCAL_ARITHMETIC_MAX_ERROR_NATS: f64 = 32.0 * f64::EPSILON;",
            "const KSG_LOCAL_ARITHMETIC_MAX_ERROR_NATS: f64 = 256.0 * f64::EPSILON;",
        ),
        (
            "drop-one-ksg-count-shift",
            Path("crates/pid-core/src/ksg.rs"),
            "let ny = ty.count_within(y.row(i), eps, i as u32);\n"
            "            Ok(ksg_local_harmonic_term(\n"
            "                &shifted_harmonics,\n"
            "                k,\n"
            "                n,\n"
            "                nx + 1,\n"
            "                ny + 1,",
            "let ny = ty.count_within(y.row(i), eps, i as u32);\n"
            "            Ok(ksg_local_harmonic_term(\n"
            "                &shifted_harmonics,\n"
            "                k,\n"
            "                n,\n"
            "                nx,\n"
            "                ny + 1,",
        ),
        (
            "shift-inclusive-isx-count",
            Path("crates/pid-core/src/isx.rs"),
            "&shifted_harmonics, k, n, n_alpha, n_t",
            "&shifted_harmonics, k, n, n_alpha + 1, n_t",
        ),
        (
            "remove-heuristic-digamma-path",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_k = digamma(k as f64);",
            "let psi_k = 0.0;",
        ),
        (
            "remove-heuristic-psi-n",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_n = digamma(n as f64);",
            "let psi_n = 0.0;",
        ),
        (
            "shift-heuristic-shared-index",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_shared = psi_int[n_t_shared[i] + 1];",
            "let psi_shared = psi_int[n_t_shared[i] + 2];",
        ),
        (
            "shift-heuristic-s1-index",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_s1 = psi_int[n_t_s1[i] + 1];",
            "let psi_s1 = psi_int[n_t_s1[i] + 2];",
        ),
        (
            "shift-heuristic-s2-index",
            Path("crates/pid-core/src/isx.rs"),
            "let psi_s2 = psi_int[n_t_s2[i] + 1];",
            "let psi_s2 = psi_int[n_t_s2[i] + 2];",
        ),
        (
            "stale-ksg-runtime-identity",
            Path("crates/pid-core/src/ksg.rs"),
            "strict-unique-shell-integer-harmonic-report-v4",
            "strict-unique-shell-report-v3",
        ),
        (
            "swap-w1-ordered-production-counts",
            Path("crates/pid-core/src/ksg.rs"),
            "assert_eq!((row.x_count, row.y_count), (4, 1));",
            "assert_eq!((row.x_count, row.y_count), (1, 4));",
        ),
        (
            "stale-isx-runtime-identity",
            Path("crates/pid-core/src/isx.rs"),
            "strict-unique-shell-integer-harmonic-isx-v4",
            "strict-unique-shell-isx-v3",
        ),
        (
            "shift-inclusive-pid3-count",
            Path("crates/pid-core/src/pid3.rs"),
            "n_alpha,\n            n_t,",
            "n_alpha + 1,\n            n_t,",
        ),
    )
    killed: list[str] = []
    originals: dict[Path, str] = {}
    for mutation, relative, old, new in mutations:
        path = copied_root / relative
        original = originals.setdefault(path, path.read_text(encoding="utf-8"))
        path.write_text(replace_once(original, old, new, mutation), encoding="utf-8")
        require_rejection_in_all_modes(
            checker,
            copied_root,
            mutation,
            route="--source-only",
        )
        path.write_text(original, encoding="utf-8")
        killed.append(mutation)
    return killed


def check_release_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-release-repo"
    copy_route(copied_root)
    checker = temporary / "release-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--release-only",
    )
    release_path = copied_root / "release-scope-1.0.json"
    original = release_path.read_text(encoding="utf-8")
    original_release = json.loads(original)
    original_by_id = {
        family["id"]: family for family in original_release["families"]
    }

    killed: list[str] = []
    for family_id, stale_estimator in KSG_STALE_RELEASE_REVISIONS:
        mutation = f"stale-release-estimator-{family_id}"
        release_path.write_text(original, encoding="utf-8")
        mutate_release_field(
            release_path,
            family_id,
            "estimator_revision",
            stale_estimator,
            mutation,
        )
        require_rejection_in_all_modes(
            checker,
            copied_root,
            mutation,
            route="--release-only",
        )
        killed.append(mutation)

        mutation = f"changed-release-definition-{family_id}"
        release_path.write_text(original, encoding="utf-8")
        definition = original_by_id[family_id]["definition_revision"]
        mutate_release_field(
            release_path,
            family_id,
            "definition_revision",
            f"{definition}-unauthorized",
            mutation,
        )
        require_rejection_in_all_modes(
            checker,
            copied_root,
            mutation,
            route="--release-only",
        )
        killed.append(mutation)

    for family_id in KSG_PROTECTED_RELEASE_FAMILIES:
        for field in ("estimator_revision", "definition_revision"):
            mutation = f"over-bump-protected-{field}-{family_id}"
            release_path.write_text(original, encoding="utf-8")
            current = original_by_id[family_id][field]
            mutate_release_field(
                release_path,
                family_id,
                field,
                f"{current}-unauthorized",
                mutation,
            )
            require_rejection_in_all_modes(
                checker,
                copied_root,
                mutation,
                route="--release-only",
            )
            killed.append(mutation)

    mutation = "change-nonrevision-field-in-affected-release-family"
    release_path.write_text(original, encoding="utf-8")
    mutate_release_field(
        release_path,
        "pid-core.stable.continuous",
        "mathematical_family",
        "unauthorized affected-family semantic change",
        mutation,
    )
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--release-only",
    )
    killed.append(mutation)

    mutation = "change-nonrevision-field-in-protected-release-family"
    release_path.write_text(original, encoding="utf-8")
    mutate_release_field(
        release_path,
        "pid-core.stable.categorical",
        "mathematical_family",
        "unauthorized protected-family semantic change",
        mutation,
    )
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--release-only",
    )
    killed.append(mutation)

    mutation = "change-release-top-level-metadata"
    release = json.loads(original)
    release["scope_state"] = "unauthorized"
    release_path.write_bytes(canonical_json_bytes(release))
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--release-only",
    )
    killed.append(mutation)
    return killed


def check_catalog_mutations(checker_text: str, temporary: Path) -> list[str]:
    copied_root = temporary / "copied-catalog-repo"
    copy_catalog_route(copied_root)
    checker = temporary / "catalog-checker.py"
    checker.write_text(checker_text, encoding="utf-8")
    require_exact_acceptance_in_all_modes(
        checker,
        copied_root,
        route="--catalog-only",
    )
    catalog_path = copied_root / "method-catalog.json"
    original = json.loads(catalog_path.read_bytes())

    def method(catalog: dict[str, object], method_id: str) -> dict[str, object]:
        matches = [item for item in catalog["methods"] if item.get("id") == method_id]
        if len(matches) != 1:
            fail(f"catalog mutation method match count changed for {method_id}: {len(matches)}")
        return matches[0]

    def write_and_reject(catalog: dict[str, object], mutation: str) -> None:
        catalog_path.write_bytes(canonical_json_bytes(catalog))
        require_rejection_in_all_modes(
            checker,
            copied_root,
            mutation,
            route="--catalog-only",
        )

    killed: list[str] = []
    claim_path = "claims/KSG-INTEGER-HARMONIC-001/claim-v3.md"
    for method_id in KSG_CATALOG_METHOD_IDS:
        mutation = f"remove-ksg-claim-binding-{method_id}"
        catalog = json.loads(json.dumps(original))
        evidence = method(catalog, method_id)["validation"]["evidence_paths"]
        if evidence.count(claim_path) != 1:
            fail(f"{mutation}: claim path count changed")
        evidence.remove(claim_path)
        write_and_reject(catalog, mutation)
        killed.append(mutation)

    formal_path = "claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v3.md"
    for method_id in KSG_FORMAL_CATALOG_METHOD_IDS:
        mutation = f"remove-ksg-formal-binding-{method_id}"
        catalog = json.loads(json.dumps(original))
        evidence = method(catalog, method_id)["validation"]["evidence_paths"]
        if evidence.count(formal_path) != 1:
            fail(f"{mutation}: formal path count changed")
        evidence.remove(formal_path)
        write_and_reject(catalog, mutation)
        killed.append(mutation)

    mutation = "bind-unchanged-shared-config-to-ksg-claim"
    catalog = json.loads(json.dumps(original))
    evidence = method(catalog, "mutual-information.ksg1-shared-config")["validation"][
        "evidence_paths"
    ]
    evidence.append(claim_path)
    evidence.sort()
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "replace-active-ksg-claim-with-stale-v2"
    catalog = json.loads(json.dumps(original))
    evidence = method(catalog, "mutual-information.ksg1-report")["validation"][
        "evidence_paths"
    ]
    evidence[evidence.index(claim_path)] = "claims/KSG-INTEGER-HARMONIC-001/claim-v2.md"
    evidence.sort()
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "remove-required-ksg-checker-binding"
    catalog = json.loads(json.dumps(original))
    evidence = method(catalog, "validation.exp0")["validation"]["evidence_paths"]
    evidence.remove("scripts/check-ksg-harmonic-revision.py")
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "unsort-ksg-evidence-paths"
    catalog = json.loads(json.dumps(original))
    evidence = method(catalog, "mutual-information.ksg1-raw")["validation"]["evidence_paths"]
    evidence[0], evidence[-1] = evidence[-1], evidence[0]
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "change-protected-catalog-method-object"
    catalog = json.loads(json.dumps(original))
    protected = next(
        item for item in catalog["methods"] if item["id"] not in KSG_CATALOG_METHOD_IDS
    )
    protected["summary"] += " unauthorized KSG-phase change"
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "change-protected-catalog-reference"
    catalog = json.loads(json.dumps(original))
    catalog["references"][0]["title"] += " unauthorized KSG-phase change"
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "change-protected-catalog-metadata"
    catalog = json.loads(json.dumps(original))
    catalog["catalog_scope"] += " unauthorized KSG-phase change"
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "insert-forbidden-later-wave-catalog-token"
    catalog = json.loads(json.dumps(original))
    method(catalog, "mutual-information.ksg1-raw")["summary"] += (
        " PID2-REPRESENTED-SUM-001"
    )
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "break-ksg-reverse-dependency-closure"
    catalog = json.loads(json.dumps(original))
    method(catalog, "co-information.continuous-raw")["depends_on"] = []
    write_and_reject(catalog, mutation)
    killed.append(mutation)

    mutation = "delete-bound-catalog-evidence-target"
    catalog_path.write_bytes(canonical_json_bytes(original))
    bound_target = (
        copied_root
        / "claims/KSG-INTEGER-HARMONIC-001/behavioral-witnesses-v3.md"
    )
    bound_target.unlink()
    require_rejection_in_all_modes(
        checker,
        copied_root,
        mutation,
        route="--catalog-only",
    )
    killed.append(mutation)
    return killed


def check_scope_isolation_preflights(checker_text: str, temporary: Path) -> int:
    arithmetic_poisoned = replace_once(
        checker_text,
        "def check_exact_route() -> None:\n",
        "def check_exact_route() -> None:\n"
        "    raise RuntimeError('scope-isolation arithmetic poison: exact')\n",
        "scope-isolation-poison-exact",
    )
    arithmetic_poisoned = replace_once(
        arithmetic_poisoned,
        "def check_binary64_route(fixture: dict[str, Any]) -> None:\n",
        "def check_binary64_route(fixture: dict[str, Any]) -> None:\n"
        "    raise RuntimeError('scope-isolation arithmetic poison: binary64')\n",
        "scope-isolation-poison-binary64",
    )
    arithmetic_poisoned_checker = temporary / "arithmetic-poisoned-checker.py"
    arithmetic_poisoned_checker.write_text(arithmetic_poisoned, encoding="utf-8")
    for route in ("--source-only", "--release-only", "--catalog-only"):
        require_exact_acceptance_in_all_modes(
            arithmetic_poisoned_checker,
            ROOT,
            route=route,
        )

    repository_poisoned = replace_once(
        checker_text,
        "def check_release_route(repo_root: Path) -> None:\n",
        "def check_release_route(repo_root: Path) -> None:\n"
        "    raise RuntimeError('scope-isolation repository poison: release')\n",
        "scope-isolation-poison-release",
    )
    repository_poisoned = replace_once(
        repository_poisoned,
        "def check_source_route(repo_root: Path) -> None:\n",
        "def check_source_route(repo_root: Path) -> None:\n"
        "    raise RuntimeError('scope-isolation repository poison: source')\n",
        "scope-isolation-poison-source",
    )
    repository_poisoned = replace_once(
        repository_poisoned,
        "def check_catalog_route(repo_root: Path) -> None:\n",
        "def check_catalog_route(repo_root: Path) -> None:\n"
        "    raise RuntimeError('scope-isolation repository poison: catalog')\n",
        "scope-isolation-poison-catalog",
    )
    repository_poisoned_checker = temporary / "repository-poisoned-checker.py"
    repository_poisoned_checker.write_text(repository_poisoned, encoding="utf-8")
    outside_checkout = temporary / "outside-checkout"
    outside_checkout.mkdir()
    require_exact_acceptance_in_all_modes(
        repository_poisoned_checker,
        temporary / "absent-repository-root",
        route="--exact-only",
        cwd=outside_checkout,
    )
    return EXPECTED_SCOPE_ISOLATION_PREFLIGHTS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--claim-only",
        action="store_true",
        help=(
            "run only the preclosure revision-4 claim custody and semantic mutation suite; "
            "open catalog/release/source integration routes are not weakened or promoted"
        ),
    )
    return parser.parse_args()


def run_claim_only_self_test() -> int:
    try:
        checker_text = CHECKER.read_text(encoding="utf-8")
        require_exact_acceptance_in_all_modes(
            CHECKER,
            ROOT,
            route="--claim-only",
        )
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-ksg-claim-mutations-"
        ) as directory:
            temporary = Path(directory)
            partitions = {
                "custody": check_claim_custody_mutations(checker_text, temporary),
                "manifest-structure": check_claim_manifest_mutations(
                    checker_text, temporary
                ),
                "resealed-semantics": check_claim_resealed_semantic_mutations(
                    checker_text, temporary
                ),
            }
            counts = {name: len(mutations) for name, mutations in partitions.items()}
            if counts != EXPECTED_CLAIM_MUTATIONS:
                fail(f"claim mutation partition changed: {counts}")
            mutation_names = [
                mutation
                for mutations in partitions.values()
                for mutation in mutations
            ]
            if len(mutation_names) != len(set(mutation_names)):
                fail("claim mutation names are not globally unique")
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"KSG harmonic-revision claim self-test failed: {error}", file=sys.stderr)
        return 1
    total = sum(counts.values())
    print(
        f"KSG harmonic-revision claim self-test passed: {total} mutations rejected "
        f"(custody={counts['custody']}, "
        f"manifest-structure={counts['manifest-structure']}, "
        f"resealed-semantics={counts['resealed-semantics']}); "
        "each resealed semantic mutation was rejected first by hash custody and then after "
        "the leaf hash plus unavoidable manifest-envelope digest were rebound"
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.claim_only:
        return run_claim_only_self_test()
    try:
        checker_text = CHECKER.read_text(encoding="utf-8")
        for route in SUCCESS_LINES:
            require_exact_acceptance_in_all_modes(CHECKER, ROOT, route=route)
        with tempfile.TemporaryDirectory(prefix="pid-rs-ksg-harmonic-mutations-") as directory:
            temporary = Path(directory)
            partitions = {
                "checker-model": check_checker_mutations(checker_text, temporary),
                "fixture-custody": check_fixture_custody_mutations(checker_text, temporary),
                "fixture-semantics": check_fixture_semantic_mutations(
                    checker_text, temporary
                ),
                "textual-source": check_source_mutations(checker_text, temporary),
                "release": check_release_mutations(checker_text, temporary),
                "catalog": check_catalog_mutations(checker_text, temporary),
            }
            counts = {name: len(mutations) for name, mutations in partitions.items()}
            if counts != EXPECTED_MUTATIONS:
                fail(f"mutation partition changed: {counts}")
            mutation_names = [
                mutation
                for mutations in partitions.values()
                for mutation in mutations
            ]
            if len(mutation_names) != len(set(mutation_names)):
                fail("mutation names are not globally unique")
            scope_preflights = check_scope_isolation_preflights(checker_text, temporary)
            if scope_preflights != EXPECTED_SCOPE_ISOLATION_PREFLIGHTS:
                fail(f"scope-isolation preflight count changed: {scope_preflights}")
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"KSG harmonic-revision self-test failed: {error}", file=sys.stderr)
        return 1
    total = sum(counts.values())
    print(
        f"KSG harmonic-revision self-test passed: {total} mutations rejected "
        f"(checker-model={counts['checker-model']}, "
        f"fixture-custody={counts['fixture-custody']}, "
        f"fixture-semantics={counts['fixture-semantics']}, "
        f"textual-source={counts['textual-source']}, release={counts['release']}, "
        f"catalog={counts['catalog']}); "
        f"scope-isolation-preflights={scope_preflights}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Artifact: `crates/pid-core/src/stats.rs`

SHA-256: `a8fc8a6792c1f1406caf45301b2d8eb47dadbe9058673535c249646df475acb2`

```text
use crate::error::{PidError, PidResult};
use crate::resource::{try_vec_filled, ResourceBudget};

/// Mean of finite values, scaled before summation so avoidable intermediate overflow does not
/// reject a representable result.
pub(crate) fn finite_mean(values: &[f64], context: &'static str) -> PidResult<f64> {
    let (scale, mean_scaled) = scaled_mean_parts(values, context)?;
    let mean = scale * mean_scaled;
    if mean.is_finite() {
        Ok(mean)
    } else {
        Err(PidError::NumericalInstability { context })
    }
}

/// Population mean and standard deviation of finite values.
///
/// Both passes operate after division by `max(abs(x))`. This matters for data such as
/// `[0, f64::MAX]`: its mean and standard deviation are both finite, even though forming either
/// the raw sum or the raw variance overflows.
pub(crate) fn finite_mean_std_population(
    values: &[f64],
    context: &'static str,
) -> PidResult<(f64, f64)> {
    finite_mean_std(values, 0, context)
}

/// Sample mean and standard deviation (Bessel-corrected, denominator `n-1`).
#[cfg(feature = "experimental-pipelines")]
pub(crate) fn finite_mean_std_sample(
    values: &[f64],
    context: &'static str,
) -> PidResult<(f64, f64)> {
    finite_mean_std(values, 1, context)
}

fn finite_mean_std(values: &[f64], ddof: usize, context: &'static str) -> PidResult<(f64, f64)> {
    if values.len() <= ddof {
        return Err(PidError::InvalidConfig {
            context,
            message: "not enough values for the requested variance degrees of freedom",
        });
    }
    let (scale, mean_scaled) = scaled_mean_parts(values, context)?;
    if scale == 0.0 {
        return Ok((0.0, 0.0));
    }

    let sum_squared_scaled = compensated_sum(values.iter().map(|value| {
        let deviation = value / scale - mean_scaled;
        deviation * deviation
    }));
    let variance_scaled = sum_squared_scaled / (values.len() - ddof) as f64;
    // For |x| <= scale, the exact population variance is <= scale^2. Permit a small floating
    // tolerance, then restore that mathematical bound so `scale * sqrt(var)` cannot spuriously
    // overflow at `f64::MAX`.
    let variance_bound = values.len() as f64 / (values.len() - ddof) as f64;
    let tolerance = 64.0 * f64::EPSILON * variance_bound;
    if !variance_scaled.is_finite()
        || variance_scaled < -tolerance
        || variance_scaled > variance_bound + tolerance
    {
        return Err(PidError::NumericalInstability { context });
    }
    let std = scale * variance_scaled.clamp(0.0, variance_bound).sqrt();
    let mean = scale * mean_scaled;
    if mean.is_finite() && std.is_finite() {
        Ok((mean, std))
    } else {
        Err(PidError::NumericalInstability { context })
    }
}

fn scaled_mean_parts(values: &[f64], context: &'static str) -> PidResult<(f64, f64)> {
    if values.is_empty() {
        return Err(PidError::InvalidConfig {
            context,
            message: "need at least one value",
        });
    }
    if values.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NonFiniteInput { context });
    }
    let scale = values
        .iter()
        .fold(0.0_f64, |current, value| current.max(value.abs()));
    if scale == 0.0 {
        return Ok((0.0, 0.0));
    }

    let raw_mean_scaled =
        compensated_sum(values.iter().map(|value| value / scale)) / values.len() as f64;
    let tolerance = 64.0 * f64::EPSILON;
    if !raw_mean_scaled.is_finite() || raw_mean_scaled.abs() > 1.0 + tolerance {
        return Err(PidError::NumericalInstability { context });
    }
    Ok((scale, raw_mean_scaled.clamp(-1.0, 1.0)))
}

/// Deterministic Neumaier compensated summation in iterator order.
///
/// Callers remain responsible for ensuring that the mathematical sum is representable. Keeping
/// this helper crate-visible lets estimators share one stable accumulation policy without exposing
/// it as part of the public API.
pub(crate) fn compensated_sum(values: impl IntoIterator<Item = f64>) -> f64 {
    let mut sum = 0.0;
    let mut correction = 0.0;
    for value in values {
        let next = sum + value;
        if sum.abs() >= value.abs() {
            correction += (sum - next) + value;
        } else {
            correction += (value - next) + sum;
        }
        sum = next;
    }
    sum + correction
}

/// Digamma / psi function ψ(x).
///
/// Implementation: recurrence to shift into a "large x" regime + asymptotic expansion.
///
/// Units: natural logarithm (nats).
#[cfg(any(feature = "experimental-heuristics", test))]
pub(crate) fn digamma(x: f64) -> f64 {
    debug_assert!(x.is_finite());
    debug_assert!(x > 0.0);

    let mut x = x;
    let mut acc = 0.0;

    // Recurrence for small x: ψ(x) = ψ(x+1) - 1/x
    // Shifting to 8 keeps the truncated Bernoulli expansion comfortably below 1e-13 error at
    // the small integer arguments used by KSG. Stopping at 6 leaves a ~9.3e-13 bias in psi(1).
    while x < 8.0 {
        acc -= 1.0 / x;
        x += 1.0;
    }

    // Asymptotic series (Stirling-like).
    // ψ(x) ≈ ln(x) - 1/(2x) - 1/(12x²) + 1/(120x⁴) - 1/(252x⁶) + 1/(240x⁸) - 1/(132x¹⁰) + 691/(32760x¹²) - ...
    let inv = 1.0 / x;
    let inv2 = inv * inv;
    let inv4 = inv2 * inv2;
    let inv6 = inv4 * inv2;
    let inv8 = inv4 * inv4;
    let inv10 = inv8 * inv2;
    let inv12 = inv6 * inv6;

    acc + x.ln() - 0.5 * inv - (1.0 / 12.0) * inv2 + (1.0 / 120.0) * inv4 - (1.0 / 252.0) * inv6
        + (1.0 / 240.0) * inv8
        - (1.0 / 132.0) * inv10
        + (691.0 / 32760.0) * inv12
}

/// Precompute ψ(i) for integer `i` in `0..=n` (with index 0 unused).
///
/// The non-cancelling research heuristic calls `digamma` repeatedly at small positive integer
/// count arguments. This helper preserves that general special-function path; coefficient-
/// cancelling KSG and shared-exclusions paths use [`shifted_harmonic_table`] instead.
#[cfg(feature = "experimental-heuristics")]
pub(crate) fn digamma_int_table(n: usize) -> PidResult<Vec<f64>> {
    let len = n.checked_add(1).ok_or(PidError::SizeOverflow {
        operation: "digamma_int_table",
    })?;
    let mut out = try_vec_filled("digamma_int_table", len, 0.0f64, ResourceBudget::default())?;
    for (i, v) in out.iter_mut().enumerate().skip(1) {
        *v = digamma(i as f64);
    }
    Ok(out)
}

/// Precompute the positive-integer part of digamma without Euler's constant.
///
/// The returned table is indexed by the positive digamma argument and stores
/// `table[m] = H_(m-1)`, with index zero unused. Prefixes use deterministic Neumaier
/// compensation. This has the same `n + 1` binary64 allocation shape as `digamma_int_table`,
/// but it is only definition-preserving where all Euler-constant coefficients cancel.
pub(crate) fn shifted_harmonic_table(n: usize) -> PidResult<Vec<f64>> {
    let len = n.checked_add(1).ok_or(PidError::SizeOverflow {
        operation: "shifted_harmonic_table",
    })?;
    let mut out = try_vec_filled(
        "shifted_harmonic_table",
        len,
        0.0_f64,
        ResourceBudget::default(),
    )?;
    let mut sum = 0.0_f64;
    let mut correction = 0.0_f64;
    // `argument` is the mathematical digamma argument and the table index; retaining that exact
    // correspondence makes the audited off-by-one contract visible at the write site.
    #[expect(
        clippy::needless_range_loop,
        reason = "the loop index is the audited digamma argument and harmonic denominator"
    )]
    for argument in 2..=n {
        let value = 1.0 / (argument - 1) as f64;
        let next = sum + value;
        if sum.abs() >= value.abs() {
            correction += (sum - next) + value;
        } else {
            correction += (value - next) + sum;
        }
        sum = next;
        out[argument] = sum + correction;
    }
    Ok(out)
}

/// Evaluate a cancelling four-integer-digamma KSG term from shifted harmonic prefixes.
///
/// For positive arguments satisfying `k <= x,y <= n`, this evaluates
/// `psi(k) + psi(n) - psi(x) - psi(y)` as the source-symmetric range expression
/// `(H_(n-1) - H_(max(x,y)-1)) - (H_(min(x,y)-1) - H_(k-1))`.
/// KSG's exclusive counts therefore pass `x = nx + 1`, while inclusive shared-exclusions counts
/// pass their count directly. The exact-real identity is universal on that integer domain; the
/// binary64 prefix evaluation is not a universal correct-rounding guarantee.
#[inline]
pub(crate) fn ksg_local_harmonic_term(
    shifted_harmonics: &[f64],
    k: usize,
    n: usize,
    x: usize,
    y: usize,
) -> f64 {
    debug_assert!(k > 0);
    debug_assert!(k <= x && x <= n);
    debug_assert!(k <= y && y <= n);
    debug_assert!(n < shifted_harmonics.len());
    let lower = x.min(y);
    let upper = x.max(y);
    (shifted_harmonics[n] - shifted_harmonics[upper])
        - (shifted_harmonics[lower] - shifted_harmonics[k])
}

#[cfg(test)]
mod tests {
    #[cfg(feature = "experimental-pipelines")]
    use super::finite_mean_std_sample;
    use super::{
        digamma, finite_mean, finite_mean_std_population, ksg_local_harmonic_term,
        shifted_harmonic_table,
    };
    use serde::Deserialize;

    const EULER_GAMMA: f64 = 0.577_215_664_901_532_9_f64;
    const KSG_ARITHMETIC_FIXTURE: &[u8] =
        include_bytes!("../tests/fixtures/ksg_local_arithmetic_oracle.json");
    const KSG_ARITHMETIC_CHECKSUM: &str =
        include_str!("../tests/fixtures/ksg_local_arithmetic_oracle.json.sha256");
    const KSG_ARITHMETIC_GENERATOR: &[u8] =
        include_bytes!("../../../scripts/generate-ksg-local-arithmetic-oracle.py");
    const KSG_ARITHMETIC_GENERATOR_SHA256: &str =
        "a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b";
    const KSG_EXHAUSTIVE_CASES: usize = 6_920;
    const KSG_STRESS_CASES: usize = 1_278;
    const KSG_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS: usize = 240;
    const KSG_ENDPOINT_CANCELLATION_STRESS_ZEROS: usize = 114;
    const KSG_ENDPOINT_CANCELLATION_ZEROS: usize = 354;
    const KSG_ENDPOINT_DIRECT_LEFT_NONZEROS: usize = 150;
    // The final helper observes 8 binary64 epsilons over the exact committed corpus. The 32-epsilon
    // gate is a four-times finite-corpus margin, not a universal error theorem.
    const KSG_LOCAL_ARITHMETIC_OBSERVED_MAX_ERROR_NATS: f64 = 8.0 * f64::EPSILON;
    const KSG_LOCAL_ARITHMETIC_MAX_ERROR_TIES: usize = 40;
    const KSG_LOCAL_ARITHMETIC_MAX_ERROR_NATS: f64 = 32.0 * f64::EPSILON;

    #[derive(Deserialize)]
    struct KsgArithmeticFixture {
        arithmetic: KsgArithmeticMetadata,
        bounds: KsgArithmeticBounds,
        cases: Vec<KsgArithmeticCase>,
        generator: KsgArithmeticGenerator,
        schema: String,
        schema_revision: usize,
    }

    #[derive(Deserialize)]
    struct KsgArithmeticMetadata {
        decimal_precision_digits: usize,
        endpoint_cancellation_exact_zero_case_count: usize,
        endpoint_cancellation_exact_zero_exhaustive_case_count: usize,
        endpoint_cancellation_exact_zero_rule: String,
        endpoint_cancellation_exact_zero_stress_case_count: usize,
        exact_identity: String,
        logarithm_unit: String,
    }

    #[derive(Deserialize)]
    struct KsgArithmeticBounds {
        exhaustive_case_count: usize,
        exhaustive_max_samples: usize,
        exhaustive_rule: String,
        stress_case_count: usize,
        stress_sample_sizes: Vec<usize>,
    }

    #[derive(Deserialize)]
    struct KsgArithmeticGenerator {
        imports_pid_rs: bool,
        path: String,
        sha256: String,
        third_party_dependencies: Vec<String>,
    }

    #[derive(Deserialize)]
    struct KsgArithmeticCase {
        expected_nats: String,
        k: usize,
        sample_count: usize,
        x_count: usize,
        y_count: usize,
    }

    fn harmonic(n: usize) -> f64 {
        // H_n = sum_{k=1..n} 1/k, with H_0 = 0.
        (1..=n).map(|k| 1.0 / (k as f64)).sum()
    }

    #[test]
    fn digamma_matches_known_integer_values() {
        // ψ(1) = -γ
        let psi1 = digamma(1.0);
        assert!((psi1 + EULER_GAMMA).abs() < 1e-12, "psi(1)={psi1}");

        // ψ(n) = H_{n-1} - γ for integer n>=2
        for n in 2..=25usize {
            let psi_n = digamma(n as f64);
            let expected = harmonic(n - 1) - EULER_GAMMA;
            assert!(
                (psi_n - expected).abs() < 5e-14,
                "psi({n})={psi_n} expected={expected}"
            );
        }
    }

    #[test]
    fn digamma_recurrence_holds() {
        // ψ(x+1) = ψ(x) + 1/x
        let x = 3.7;
        let lhs = digamma(x + 1.0);
        let rhs = digamma(x) + 1.0 / x;
        assert!((lhs - rhs).abs() < 5e-13, "lhs={lhs} rhs={rhs}");
    }

    #[test]
    fn ksg_integer_harmonic_range_matches_decimal_oracle() {
        let mut checksum_fields = KSG_ARITHMETIC_CHECKSUM.split_whitespace();
        let expected_hash = checksum_fields
            .next()
            .expect("KSG arithmetic checksum must contain a SHA-256 digest");
        assert_eq!(
            checksum_fields.next(),
            Some("ksg_local_arithmetic_oracle.json"),
            "KSG arithmetic checksum filename changed"
        );
        assert_eq!(
            checksum_fields.next(),
            None,
            "KSG arithmetic checksum has trailing fields"
        );
        assert_eq!(
            pid_runlog::sha256_hex(KSG_ARITHMETIC_FIXTURE),
            expected_hash,
            "KSG arithmetic fixture does not match its committed SHA-256 digest"
        );

        let fixture: KsgArithmeticFixture = serde_json::from_slice(KSG_ARITHMETIC_FIXTURE)
            .expect("KSG arithmetic fixture must contain valid JSON");
        assert_eq!(fixture.schema, "pid-rs/ksg-local-arithmetic-oracle");
        assert_eq!(fixture.schema_revision, 2);
        assert_eq!(fixture.arithmetic.decimal_precision_digits, 80);
        assert_eq!(
            fixture
                .arithmetic
                .endpoint_cancellation_exact_zero_case_count,
            KSG_ENDPOINT_CANCELLATION_ZEROS
        );
        assert_eq!(
            fixture
                .arithmetic
                .endpoint_cancellation_exact_zero_exhaustive_case_count,
            KSG_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS
        );
        assert_eq!(
            fixture.arithmetic.endpoint_cancellation_exact_zero_rule,
            "{nx,ny}={k-1,n-1}; cancel equal symbolic harmonic terms before Decimal evaluation"
        );
        assert_eq!(
            fixture
                .arithmetic
                .endpoint_cancellation_exact_zero_stress_case_count,
            KSG_ENDPOINT_CANCELLATION_STRESS_ZEROS
        );
        assert_eq!(
            fixture.arithmetic.exact_identity,
            "H_(k-1) + H_(n-1) - H_(nx) - H_(ny)"
        );
        assert_eq!(fixture.arithmetic.logarithm_unit, "nats");
        assert_eq!(fixture.bounds.exhaustive_case_count, KSG_EXHAUSTIVE_CASES);
        assert_eq!(fixture.bounds.exhaustive_max_samples, 16);
        assert_eq!(
            fixture.bounds.exhaustive_rule,
            "2 <= n <= bound; 1 <= k < n; k-1 <= nx,ny < n"
        );
        assert_eq!(fixture.bounds.stress_case_count, KSG_STRESS_CASES);
        assert_eq!(
            fixture.bounds.stress_sample_sizes,
            [17, 32, 64, 256, 4_096, 65_536, 1_000_000]
        );
        assert_eq!(fixture.cases.len(), KSG_EXHAUSTIVE_CASES + KSG_STRESS_CASES);
        let endpoint_cancellation_cases = fixture
            .cases
            .iter()
            .filter(|case| {
                let low = case.k - 1;
                let high = case.sample_count - 1;
                matches!(
                    (case.x_count, case.y_count),
                    (x, y) if (x, y) == (low, high) || (x, y) == (high, low)
                )
            })
            .collect::<Vec<_>>();
        assert_eq!(
            endpoint_cancellation_cases.len(),
            KSG_ENDPOINT_CANCELLATION_ZEROS
        );
        assert!(endpoint_cancellation_cases
            .iter()
            .all(|case| case.expected_nats == "0"));
        let endpoint_cancellation_exhaustive_cases = endpoint_cancellation_cases
            .iter()
            .filter(|case| case.sample_count <= 16)
            .count();
        let endpoint_cancellation_stress_cases = endpoint_cancellation_cases
            .iter()
            .filter(|case| case.sample_count > 16)
            .count();
        assert_eq!(
            endpoint_cancellation_exhaustive_cases, KSG_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS,
            "row-derived exhaustive endpoint-cancellation count changed"
        );
        assert_eq!(
            endpoint_cancellation_stress_cases, KSG_ENDPOINT_CANCELLATION_STRESS_ZEROS,
            "row-derived stress endpoint-cancellation count changed"
        );
        let canonical_zero_cases = fixture
            .cases
            .iter()
            .filter(|case| case.expected_nats == "0")
            .collect::<Vec<_>>();
        assert_eq!(canonical_zero_cases.len(), KSG_ENDPOINT_CANCELLATION_ZEROS);
        assert!(canonical_zero_cases.iter().all(|case| {
            let low = case.k - 1;
            let high = case.sample_count - 1;
            (case.x_count, case.y_count) == (low, high)
                || (case.x_count, case.y_count) == (high, low)
        }));
        assert_eq!(
            fixture.generator.path,
            "scripts/generate-ksg-local-arithmetic-oracle.py"
        );
        assert!(!fixture.generator.imports_pid_rs);
        assert!(fixture.generator.third_party_dependencies.is_empty());
        assert_eq!(
            pid_runlog::sha256_hex(KSG_ARITHMETIC_GENERATOR),
            KSG_ARITHMETIC_GENERATOR_SHA256,
            "live KSG fixture generator changed from the reviewed schema-2 KSG revision-4 digest"
        );
        assert_eq!(
            fixture.generator.sha256, KSG_ARITHMETIC_GENERATOR_SHA256,
            "KSG arithmetic fixture is not bound to the reviewed live generator digest"
        );

        let max_argument = fixture
            .cases
            .iter()
            .map(|case| case.sample_count)
            .max()
            .expect("KSG arithmetic fixture must be nonempty");
        let shifted_harmonics = shifted_harmonic_table(max_argument)
            .expect("bounded shifted harmonic table must fit the default resource budget");
        let mut maximum_error = 0.0_f64;
        let mut first_maximum = None;
        let mut maximum_error_ties = 0_usize;
        let mut swap_bit_asymmetries = 0_usize;
        let mut endpoint_positive_zero_outputs = 0_usize;
        let mut endpoint_direct_left_nonzeros = 0_usize;
        let mut endpoint_direct_left_negative_zeros = 0_usize;
        for case in &fixture.cases {
            assert!(case.sample_count >= 2);
            assert!((1..case.sample_count).contains(&case.k));
            assert!((case.k - 1..case.sample_count).contains(&case.x_count));
            assert!((case.k - 1..case.sample_count).contains(&case.y_count));
            let expected = case
                .expected_nats
                .parse::<f64>()
                .expect("Decimal oracle value must be representable as finite f64");
            let actual = ksg_local_harmonic_term(
                &shifted_harmonics,
                case.k,
                case.sample_count,
                case.x_count + 1,
                case.y_count + 1,
            );
            let source_swapped = ksg_local_harmonic_term(
                &shifted_harmonics,
                case.k,
                case.sample_count,
                case.y_count + 1,
                case.x_count + 1,
            );
            let low = case.k - 1;
            let high = case.sample_count - 1;
            if (case.x_count, case.y_count) == (low, high)
                || (case.x_count, case.y_count) == (high, low)
            {
                assert_eq!(
                    actual.to_bits(),
                    0.0_f64.to_bits(),
                    "endpoint cancellation must follow the selected positive-zero path"
                );
                endpoint_positive_zero_outputs += 1;
                let direct_left = ((shifted_harmonics[case.k]
                    + shifted_harmonics[case.sample_count])
                    - shifted_harmonics[case.x_count + 1])
                    - shifted_harmonics[case.y_count + 1];
                endpoint_direct_left_nonzeros += usize::from(direct_left != 0.0);
                endpoint_direct_left_negative_zeros +=
                    usize::from(direct_left.to_bits() == (-0.0_f64).to_bits());
            }
            swap_bit_asymmetries += usize::from(actual.to_bits() != source_swapped.to_bits());
            let error = if actual.is_finite() && expected.is_finite() {
                (actual - expected).abs()
            } else {
                f64::INFINITY
            };
            if error > maximum_error {
                maximum_error = error;
                first_maximum = Some((
                    case.sample_count,
                    case.k,
                    case.x_count,
                    case.y_count,
                    actual,
                    expected,
                ));
                maximum_error_ties = 1;
            } else if error == maximum_error {
                maximum_error_ties += 1;
            }
        }

        assert_eq!(swap_bit_asymmetries, 0);
        assert_eq!(
            endpoint_positive_zero_outputs,
            KSG_ENDPOINT_CANCELLATION_ZEROS
        );
        assert_eq!(
            endpoint_direct_left_nonzeros, KSG_ENDPOINT_DIRECT_LEFT_NONZEROS,
            "ordinary left association over the selected Neumaier prefix changed"
        );
        assert_eq!(
            endpoint_direct_left_negative_zeros, 0,
            "ordinary left association produced a negative zero on an endpoint"
        );
        assert_eq!(
            maximum_error, KSG_LOCAL_ARITHMETIC_OBSERVED_MAX_ERROR_NATS,
            "the frozen finite-corpus maximum changed: {first_maximum:?}"
        );
        assert!(
            matches!(first_maximum, Some((4_096, 1, 2_048, 2_048, _, _))),
            "the first maximum-attaining tuple changed: {first_maximum:?}"
        );
        assert_eq!(
            maximum_error_ties, KSG_LOCAL_ARITHMETIC_MAX_ERROR_TIES,
            "the frozen maximum-error tie multiplicity changed"
        );
        assert!(
            maximum_error <= KSG_LOCAL_ARITHMETIC_MAX_ERROR_NATS,
            "maximum absolute error {maximum_error:.17e} nats exceeds the declared bound \
             {KSG_LOCAL_ARITHMETIC_MAX_ERROR_NATS:.17e}; first maximum: {first_maximum:?}"
        );
    }

    #[test]
    fn ksg_shifted_harmonic_indices_cover_off_by_one_boundaries() {
        let shifted = shifted_harmonic_table(4).unwrap();
        assert_eq!(shifted[1].to_bits(), 0.0_f64.to_bits());
        assert_eq!(ksg_local_harmonic_term(&shifted, 1, 2, 1, 1), 1.0);
        for (k, x, y, expected) in [
            (1, 1, 1, 11.0 / 6.0),
            (2, 2, 2, 5.0 / 6.0),
            (3, 4, 4, -1.0 / 3.0),
        ] {
            let actual = ksg_local_harmonic_term(&shifted, k, 4, x, y);
            assert!((actual - expected).abs() <= 2.0 * f64::EPSILON);
            assert_eq!(
                actual.to_bits(),
                ksg_local_harmonic_term(&shifted, k, 4, y, x).to_bits()
            );
        }
    }

    #[test]
    fn scaled_moments_keep_representable_extreme_results_finite() {
        let (mean, std) = finite_mean_std_population(&[0.0, f64::MAX], "extreme moments").unwrap();
        assert_eq!(mean, f64::MAX * 0.5);
        assert_eq!(std, f64::MAX * 0.5);

        let (mean, std) =
            finite_mean_std_population(&[-f64::MAX, f64::MAX], "extreme moments").unwrap();
        assert_eq!(mean, 0.0);
        assert_eq!(std, f64::MAX);

        assert_eq!(
            finite_mean(&[f64::MAX; 4], "extreme mean").unwrap(),
            f64::MAX
        );
    }

    #[test]
    fn scaled_moments_reject_empty_or_nonfinite_input() {
        assert!(finite_mean(&[], "empty mean").is_err());
        assert!(finite_mean_std_population(&[f64::NAN], "nan moments").is_err());
        #[cfg(feature = "experimental-pipelines")]
        assert!(finite_mean_std_sample(&[1.0], "singleton sample").is_err());
    }
}
```

## Artifact: `crates/pid-core/src/ksg.rs`

SHA-256: `0f5109dda054a0222ed796209b10d22196348eddac76d8d53dd78b4e03a95250`

```text
//! Kraskov–Stögbauer–Grassberger algorithm-1 mutual-information estimation.
//!
//! # Method provenance and availability
//!
//! **PAPER-DEFINED CORE / PROJECT-DEFINED REPORT CONTRACT.** The neighbor-count estimator is
//! KSG1 (Kraskov, Stögbauer, and Grassberger, 2004). The default stable surface is report-first and
//! adds pid-rs support declarations, observed-sample diagnostics, provenance, resource limits, and
//! cancellation. Those contracts do not broaden the estimator's published domain.
//!
//! Method catalog: mutual-information.ksg1-report
//!
//! **PROJECT-DEFINED SENSITIVITY DIAGNOSTICS.** The k and sample-size trajectories repeatedly
//! evaluate the report-first estimator under explicit resource bounds. They expose finite-sample
//! sensitivity and are not convergence proofs.
//!
//! Method catalog: mutual-information.ksg1-sensitivity-trajectories
//!
//! **PROJECT-DEFINED CONFIGURATION CONTRACT.** The `experimental-continuous` namespace
//! re-exports the same typed KSG settings for composed estimators. The paper supplies `k` and the
//! KSG1 neighborhood/count convention. `tie_epsilon`, signed-estimate presentation,
//! `support_contract`, the shared Rust type, and its namespace placement are pid-rs API contracts
//! rather than a second estimator or a separately published method.
//!
//! Method catalog: mutual-information.ksg1-shared-config
//!
//! **PAPER-DEFINED CORE / RESEARCH API.** Raw scalar and local-term functions use the same KSG
//! numerical
//! core but omit the stable report contract. They require `experimental-continuous`; local terms
//! are dependent, per-observation contributions and are not independent observations.
//!
//! Method catalog: mutual-information.ksg1-raw
//!
//! **PAPER-DERIVED RESEARCH ADAPTATION.** Hyperbolic report and trajectory entry points substitute
//! Lorentz-geodesic neighborhoods into the KSG construction. They remain research-only because no
//! general consistency result is claimed for that substitution.
//!
//! Method catalog: mutual-information.hyperbolic-ksg

use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::error::{PidError, PidResult};
#[cfg(feature = "experimental-hyperbolic")]
use crate::hyperbolic::{HyperbolicCurvature, HyperbolicMetric};
use crate::kdtree::{concat_row_into, kdtree_applicable, KdTree};
use crate::matrix::MatRef;
use crate::metric::{KernelMetric, Metric};
use crate::nn::{kth_neighbor_shell_counts, strict_radius, validate_kth_neighbor_shell};
#[cfg(feature = "parallel")]
use crate::par::WORKER_STACK_BYTES;
use crate::par::{map_index_ordered, with_thread_budget};
use crate::report::{
    Assumption, AssumptionLedgerEntry, AssumptionState, EstimandIdentity, InformationUnit,
    ProvenanceHashes, ScientificStatus, WarningCode,
};
use crate::resource::{
    sort_unstable_by_with_cancellation, try_vec_with_capacity, CancellationProgress,
    CancellationToken, ResourceBudget, ResourceEstimate,
};
use crate::stats::{compensated_sum, ksg_local_harmonic_term, shifted_harmonic_table};
#[cfg(any(feature = "experimental-continuous", test))]
use crate::support::validate_observed_sample_conditions_with_budget;
#[cfg(feature = "experimental-hyperbolic")]
use crate::support::validate_smooth_manifold_sample_conditions_with_budget_and_cancellation;
use crate::support::{
    continuous_input_diagnostics_with_kernel_and_cancellation,
    continuous_joint_shell_diagnostics_with_kernel_and_cancellation,
    validate_observed_sample_conditions_with_budget_and_cancellation, validate_support_contract,
    BoundaryModel, ContinuousInputDiagnostics, CoordinateCardinalityDiagnostics,
    NeighborShellDiagnostics, SupportContract,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum NegativeHandling {
    /// Return the signed finite-sample estimate without a presentation transform.
    Allow,
    /// Floor the final standalone estimate at zero as an explicit presentation transform.
    ///
    /// Do not use this for MI terms that enter algebraic identities or inference procedures.
    ClampToZero,
}

#[derive(Clone, Copy)]
struct DistPair {
    joint: f64,
    dx: f64,
    dy: f64,
}

#[derive(Clone, Copy)]
struct KsgLocalDiagnostic {
    term_nats: f64,
    joint_radius: f64,
    x_count: usize,
    y_count: usize,
}

/// Neighbor-search backend selection. `Auto` engages the exact Chebyshev
/// kd-tree (see `kdtree.rs`) when it is applicable and profitable; the other
/// variants exist so tests can force each path and assert bit-identical
/// results.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(not(test), allow(dead_code))] // Brute/KdTree are test-only forcing knobs
pub(crate) enum NnBackend {
    Auto,
    Brute,
    KdTree,
}

impl NnBackend {
    #[inline]
    fn use_tree(self, metric: KernelMetric, n: usize, joint_dims: usize) -> bool {
        match self {
            NnBackend::Brute => false,
            NnBackend::KdTree => metric.is_chebyshev() && joint_dims > 0,
            NnBackend::Auto => {
                metric.is_chebyshev() && kdtree_applicable(Metric::Chebyshev, n, joint_dims)
            }
        }
    }
}

pub(crate) fn effective_thread_count(requested: usize, n_tasks: usize) -> usize {
    #[cfg(feature = "parallel")]
    let available = std::thread::available_parallelism().map_or(1, std::num::NonZero::get);
    #[cfg(not(feature = "parallel"))]
    let available = 1;
    requested.min(n_tasks).min(available).max(1)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum KernelSupportMode {
    Stable,
    #[cfg(feature = "experimental-hyperbolic")]
    SmoothManifold,
}

#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct KsgConfig {
    /// Number of nearest neighbors (excluding self).
    ///
    /// KSG requires `n > k >= 1`.
    pub k: usize,
    /// Distance metric. For KSG, the standard choice is Chebyshev / L∞.
    pub metric: Metric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    ///
    /// Exact floating-point strict inequality is implemented with the predecessor of the raw kNN
    /// radius. Subtracting a material epsilon would exclude legitimate distances and estimate a
    /// different, eroded-neighborhood functional, so nonzero values are rejected.
    pub tie_epsilon: f64,
    /// Handling of small negative MI estimates due to finite-sample noise. The default is
    /// [`NegativeHandling::Allow`]; clamping is an explicit presentation-only opt-in.
    pub negative_handling: NegativeHandling,
    /// Population-support assertion for this call.
    ///
    /// The default is [`SupportContract::Unspecified`] and deliberately fails closed. For ordinary
    /// Euclidean KSG, the caller must assert [`SupportContract::AssumeRegularFullDimensional`] for
    /// every marginal and joint law used by the call. This assertion is not inferred or proved
    /// from the sample. The default-off `experimental-hyperbolic` feature adds a separate smooth
    /// manifold assertion for research-only pairwise reporting.
    pub support_contract: SupportContract,
}

impl Default for KsgConfig {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            negative_handling: NegativeHandling::Allow,
            support_contract: SupportContract::Unspecified,
        }
    }
}

impl KsgConfig {
    /// Set the nearest-neighbor count.
    pub const fn with_k(mut self, k: usize) -> Self {
        self.k = k;
        self
    }

    /// Set the distance metric.
    pub const fn with_metric(mut self, metric: Metric) -> Self {
        self.metric = metric;
        self
    }

    /// Set the reserved strict-radius compatibility value.
    ///
    /// Only exactly zero is accepted by estimator validation; this setter exists so malformed
    /// values can still be tested without relying on a semver-fragile struct literal.
    pub const fn with_tie_epsilon(mut self, tie_epsilon: f64) -> Self {
        self.tie_epsilon = tie_epsilon;
        self
    }

    /// Set the presentation policy for negative standalone estimates.
    pub const fn with_negative_handling(mut self, negative_handling: NegativeHandling) -> Self {
        self.negative_handling = negative_handling;
        self
    }

    /// Set the caller-declared population-support contract.
    pub const fn with_support_contract(mut self, support_contract: SupportContract) -> Self {
        self.support_contract = support_contract;
        self
    }

    /// Construct the ordinary Chebyshev configuration with an explicit caller assertion that all
    /// required marginal and joint laws are full-dimensional and absolutely continuous.
    pub fn assume_regular_full_dimensional() -> Self {
        Self {
            support_contract: SupportContract::assume_regular_full_dimensional(),
            ..Self::default()
        }
    }
}

#[derive(Debug, Clone)]
struct KernelKsgConfig {
    config: KsgConfig,
    kernel_metric: KernelMetric,
    kernel_support_mode: KernelSupportMode,
}

impl KernelKsgConfig {
    fn stable(config: &KsgConfig) -> Self {
        Self {
            config: config.clone(),
            kernel_metric: config.metric.into(),
            kernel_support_mode: KernelSupportMode::Stable,
        }
    }
}

impl std::ops::Deref for KernelKsgConfig {
    type Target = KsgConfig;

    fn deref(&self) -> &Self::Target {
        &self.config
    }
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct HyperbolicKsgConfig {
    /// Number of nearest neighbors (excluding self).
    pub k: usize,
    /// Lorentz-model metric and its explicit curvature.
    pub metric: HyperbolicMetric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    pub tie_epsilon: f64,
    /// Presentation handling for a negative finite-sample estimate.
    pub negative_handling: NegativeHandling,
}

#[cfg(feature = "experimental-hyperbolic")]
impl HyperbolicKsgConfig {
    /// Assert smooth densities relative to the relevant manifold volume measures and finite
    /// mutual information for every marginal and joint law required by the research estimator.
    pub const fn assume_smooth_manifold(curvature: HyperbolicCurvature) -> Self {
        Self {
            k: 3,
            metric: HyperbolicMetric::lorentz(curvature),
            tie_epsilon: 0.0,
            negative_handling: NegativeHandling::Allow,
        }
    }

    /// Set the nearest-neighbor count.
    pub const fn with_k(mut self, k: usize) -> Self {
        self.k = k;
        self
    }

    /// Set the reserved strict-radius compatibility value.
    pub const fn with_tie_epsilon(mut self, tie_epsilon: f64) -> Self {
        self.tie_epsilon = tie_epsilon;
        self
    }

    /// Set the presentation policy for negative standalone estimates.
    pub const fn with_negative_handling(mut self, negative_handling: NegativeHandling) -> Self {
        self.negative_handling = negative_handling;
        self
    }

    fn kernel_config(&self) -> KernelKsgConfig {
        KernelKsgConfig {
            config: KsgConfig {
                k: self.k,
                metric: Metric::Chebyshev,
                tie_epsilon: self.tie_epsilon,
                negative_handling: self.negative_handling,
                support_contract: SupportContract::Unspecified,
            },
            kernel_metric: self.metric.kernel(),
            kernel_support_mode: KernelSupportMode::SmoothManifold,
        }
    }
}

/// Owned, structurally checked caller-declared provenance attached to a [`KsgMiReport`].
///
/// Provenance describes operations and assumptions that cannot be reconstructed from the numeric
/// sample. Both required descriptions must contain at least one non-whitespace character. An
/// embedding-training description is optional for ordinary Chebyshev KSG, but is required by
/// `hyperbolic_ksg_mi_report` for the experimental Lorentz-hyperbolic path.
#[derive(Debug, PartialEq, Eq, Serialize)]
pub struct KsgProvenance {
    preprocessing_description: String,
    observation_model_description: String,
    embedding_training_provenance: Option<String>,
    sampling_model_description: Option<String>,
    training_split_id: Option<String>,
    evaluation_split_id: Option<String>,
}

impl KsgProvenance {
    /// Construct owned caller-declared provenance, checking only that required text is nonempty.
    pub fn new(
        preprocessing_description: impl AsRef<str>,
        observation_model_description: impl AsRef<str>,
        embedding_training_provenance: Option<&str>,
    ) -> PidResult<Self> {
        let preprocessing_description = preprocessing_description.as_ref();
        if preprocessing_description.trim().is_empty() {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::new",
                message: "preprocessing_description must be nonempty",
            });
        }
        let observation_model_description = observation_model_description.as_ref();
        if observation_model_description.trim().is_empty() {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::new",
                message: "observation_model_description must be nonempty",
            });
        }
        for value in [preprocessing_description, observation_model_description] {
            validate_optional_provenance_text(
                "KsgProvenance::new",
                "provenance field is too long",
                Some(value),
            )?;
        }
        if embedding_training_provenance.is_some_and(|description| description.trim().is_empty()) {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::new",
                message: "embedding_training_provenance must be nonempty when provided",
            });
        }
        validate_optional_provenance_text(
            "KsgProvenance::new",
            "embedding_training_provenance is too long",
            embedding_training_provenance,
        )?;
        let preprocessing_description =
            try_provenance_string("KsgProvenance::new", preprocessing_description)?;
        let observation_model_description =
            try_provenance_string("KsgProvenance::new", observation_model_description)?;
        let embedding_training_provenance = embedding_training_provenance
            .map(|value| try_provenance_string("KsgProvenance::new", value))
            .transpose()?;
        Ok(Self {
            preprocessing_description,
            observation_model_description,
            embedding_training_provenance,
            sampling_model_description: None,
            training_split_id: None,
            evaluation_split_id: None,
        })
    }

    /// Attach the declared sampling/dependence model and train/evaluation split identities.
    pub fn with_sampling_model_and_splits(
        mut self,
        sampling_model_description: impl AsRef<str>,
        training_split_id: Option<&str>,
        evaluation_split_id: Option<&str>,
    ) -> PidResult<Self> {
        let sampling_model_description = sampling_model_description.as_ref();
        if sampling_model_description.trim().is_empty() {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::with_sampling_model_and_splits",
                message: "sampling_model_description must be nonempty",
            });
        }
        for value in [
            Some(sampling_model_description),
            training_split_id,
            evaluation_split_id,
        ] {
            validate_optional_provenance_text(
                "KsgProvenance::with_sampling_model_and_splits",
                "provenance field is too long",
                value,
            )?;
        }
        self.sampling_model_description = Some(try_provenance_string(
            "KsgProvenance::with_sampling_model_and_splits",
            sampling_model_description,
        )?);
        self.training_split_id = training_split_id
            .map(|value| {
                try_provenance_string("KsgProvenance::with_sampling_model_and_splits", value)
            })
            .transpose()?;
        self.evaluation_split_id = evaluation_split_id
            .map(|value| {
                try_provenance_string("KsgProvenance::with_sampling_model_and_splits", value)
            })
            .transpose()?;
        Ok(self)
    }

    pub fn preprocessing_description(&self) -> &str {
        &self.preprocessing_description
    }

    pub fn observation_model_description(&self) -> &str {
        &self.observation_model_description
    }

    pub fn embedding_training_provenance(&self) -> Option<&str> {
        self.embedding_training_provenance.as_deref()
    }

    pub fn sampling_model_description(&self) -> Option<&str> {
        self.sampling_model_description.as_deref()
    }

    pub fn training_split_id(&self) -> Option<&str> {
        self.training_split_id.as_deref()
    }

    pub fn evaluation_split_id(&self) -> Option<&str> {
        self.evaluation_split_id.as_deref()
    }

    fn heap_bytes(&self) -> PidResult<u128> {
        [
            Some(self.preprocessing_description.as_str()),
            Some(self.observation_model_description.as_str()),
            self.embedding_training_provenance.as_deref(),
            self.sampling_model_description.as_deref(),
            self.training_split_id.as_deref(),
            self.evaluation_split_id.as_deref(),
        ]
        .into_iter()
        .flatten()
        .try_fold(0u128, |total, value| {
            total
                .checked_add(value.len() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "KsgProvenance",
                })
        })
    }

    /// Fallibly copy all owned provenance text under an aggregate resource budget.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        budget.check(
            "KsgProvenance report copy",
            ResourceEstimate {
                estimated_bytes: self.heap_bytes()?,
                pairwise_distances: 0,
                operations_hint: 6,
            },
        )?;
        Ok(Self {
            preprocessing_description: try_provenance_string(
                "KsgProvenance report copy",
                &self.preprocessing_description,
            )?,
            observation_model_description: try_provenance_string(
                "KsgProvenance report copy",
                &self.observation_model_description,
            )?,
            embedding_training_provenance: self
                .embedding_training_provenance
                .as_deref()
                .map(|value| try_provenance_string("KsgProvenance report copy", value))
                .transpose()?,
            sampling_model_description: self
                .sampling_model_description
                .as_deref()
                .map(|value| try_provenance_string("KsgProvenance report copy", value))
                .transpose()?,
            training_split_id: self
                .training_split_id
                .as_deref()
                .map(|value| try_provenance_string("KsgProvenance report copy", value))
                .transpose()?,
            evaluation_split_id: self
                .evaluation_split_id
                .as_deref()
                .map(|value| try_provenance_string("KsgProvenance report copy", value))
                .transpose()?,
        })
    }
}

fn validate_optional_provenance_text(
    context: &'static str,
    message: &'static str,
    value: Option<&str>,
) -> PidResult<()> {
    const MAX_PROVENANCE_BYTES: usize = 16 * 1024;
    if value.is_some_and(|value| value.len() > MAX_PROVENANCE_BYTES) {
        return Err(PidError::InvalidConfig { context, message });
    }
    Ok(())
}

fn try_provenance_string(context: &'static str, value: &str) -> PidResult<String> {
    let mut owned = String::new();
    owned
        .try_reserve_exact(value.len())
        .map_err(|_| PidError::AllocationFailed {
            operation: context,
            requested_bytes: value.len() as u128,
        })?;
    owned.push_str(value);
    Ok(owned)
}

/// Scientific maturity of the estimator represented by a [`KsgMiReport`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum KsgMethodStatus {
    /// Ordinary Chebyshev KSG under the explicitly declared, restricted support contract.
    RestrictedDomain,
    /// A research path without the same estimator-level validation claim.
    Experimental,
}

/// Geometry model recorded by a [`KsgMiReport`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum KsgGeometryModel {
    /// Ambient-coordinate product neighborhoods using the Chebyshev (L-infinity) metric.
    AmbientChebyshev,
}

/// A deterministic, machine-readable warning attached to a [`KsgMiReport`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum KsgReportWarning {
    /// Sample diagnostics are one-way checks, not proofs of population support.
    SampleDiagnosticsCannotProveSupport,
    /// At least one independently selected marginal k-th-neighbor shell is degenerate or
    /// ambiguous, even though the joint shells used by the returned estimate passed validation.
    MarginalNeighborShellPathology,
}

impl KsgReportWarning {
    /// Stable explanatory text for this warning.
    pub const fn message(self) -> &'static str {
        match self {
            Self::SampleDiagnosticsCannotProveSupport => {
                "sample diagnostics can identify observations incompatible with ideal estimator conditions, but cannot determine the cause or prove population continuity, a common reference measure, or finite mutual information"
            }
            Self::MarginalNeighborShellPathology => {
                "an independently selected marginal k-th-neighbor shell has zero radius or an ambiguous positive boundary"
            }
        }
    }
}

/// Empirical nearest-rank quantiles of finite local floating-point diagnostics.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct KsgValueQuantiles {
    pub min: f64,
    pub p10: f64,
    pub median: f64,
    pub p90: f64,
    pub p99: f64,
    pub max: f64,
}

/// Empirical nearest-rank quantiles of marginal neighbor counts.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct KsgCountQuantiles {
    pub min: usize,
    pub p10: usize,
    pub median: usize,
    pub p90: usize,
    pub p99: usize,
    pub max: usize,
}

/// Local-radius, count, and pointwise-term distributions used by the returned KSG estimate.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct KsgLocalDiagnosticsSummary {
    pub joint_radius: KsgValueQuantiles,
    pub x_marginal_count: KsgCountQuantiles,
    pub y_marginal_count: KsgCountQuantiles,
    pub local_mi_nats: KsgValueQuantiles,
}

/// Neighbor-search implementation selected before estimation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum KsgNeighborBackend {
    BruteForce,
    ExactChebyshevKdTree,
}

/// KSG estimate with scoped support, geometry, sample diagnostics, and caller provenance.
///
/// All information values are in nats. The sample diagnostics can identify observations
/// incompatible with ideal estimator conditions, but cannot determine their cause or prove
/// absolute continuity, a common reference measure, or finite population mutual information. This
/// stable report is restricted to ambient Chebyshev geometry; the feature-gated manifold path has
/// a separate typed report.
///
/// The diagnostic set is intentionally non-exhaustive: it does not estimate intrinsic dimension,
/// distance concentration, temporal dependence, k/n sensitivity, or finite-sample bias. Use the
/// crate's geometry diagnostics and an explicitly reported k/sample-size sensitivity analysis as
/// separate checks.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct KsgMiReport {
    /// Estimate after the requested presentation policy.
    pub estimate_nats: f64,
    /// Unclamped signed estimate. This is always retained so presentation clamping is reversible.
    pub signed_estimate_nats: f64,
    pub n_samples: usize,
    pub k: usize,
    pub metric: Metric,
    pub negative_handling: NegativeHandling,
    pub support_contract: SupportContract,
    pub method_status: KsgMethodStatus,
    pub scientific_status: ScientificStatus,
    pub estimand: EstimandIdentity,
    pub assumption_ledger: Vec<AssumptionLedgerEntry>,
    pub provenance: KsgProvenance,
    pub provenance_hashes: ProvenanceHashes,
    pub x_diagnostics: ContinuousInputDiagnostics,
    pub y_diagnostics: ContinuousInputDiagnostics,
    pub joint_shells: NeighborShellDiagnostics,
    pub local_diagnostics: KsgLocalDiagnosticsSummary,
    pub neighbor_backend: KsgNeighborBackend,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
    pub geometry_model: KsgGeometryModel,
    /// Reserved 0.9 compatibility field; ambient Chebyshev reports always contain `None`.
    pub curvature: Option<()>,
    /// Reserved 0.9 compatibility field; ambient Chebyshev reports always contain `None`.
    pub x_hyperbolic_dimension: Option<usize>,
    /// Reserved 0.9 compatibility field; ambient Chebyshev reports always contain `None`.
    pub y_hyperbolic_dimension: Option<usize>,
    /// Warnings in a stable order: support limitation, then observed marginal pathology.
    pub warnings: Vec<KsgReportWarning>,
    pub report_warnings: Vec<WarningCode>,
}

pub(crate) struct KsgReportComputation {
    pub(crate) report: KsgMiReport,
    #[cfg(feature = "experimental-continuous")]
    pub(crate) local_terms_nats: Vec<f64>,
}

/// Complete report sequence for a declared sensitivity trajectory.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct KsgTrajectoryReport {
    pub varied_parameter: &'static str,
    pub reports: Vec<KsgMiReport>,
    pub aggregate_resource_estimate: ResourceEstimate,
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum HyperbolicSupportContract {
    /// Caller asserts smooth densities relative to the relevant manifold volume measures and
    /// finite mutual information for every marginal and joint law required by the estimate.
    AssumeSmoothManifold,
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum HyperbolicKsgGeometryModel {
    /// Lorentz hyperboloid with the curvature recorded by the report metric.
    LorentzHyperboloid,
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum HyperbolicKsgReportWarning {
    /// Sample diagnostics are one-way checks, not population-support proofs.
    SampleDiagnosticsCannotProveSupport,
    /// A marginal neighbor shell is degenerate or ambiguous.
    MarginalNeighborShellPathology,
    /// This crate has no consistency theorem for its manifold KSG path.
    ConsistencyNotEstablished,
}

#[cfg(feature = "experimental-hyperbolic")]
const HYPERBOLIC_KSG_WARNING_CAPACITY: usize = 3;

#[cfg(feature = "experimental-hyperbolic")]
impl HyperbolicKsgReportWarning {
    /// Explanatory text for this warning.
    pub const fn message(self) -> &'static str {
        match self {
            Self::SampleDiagnosticsCannotProveSupport => {
                KsgReportWarning::SampleDiagnosticsCannotProveSupport.message()
            }
            Self::MarginalNeighborShellPathology => {
                KsgReportWarning::MarginalNeighborShellPathology.message()
            }
            Self::ConsistencyNotEstablished => {
                "hyperbolic/manifold KSG is experimental and this implementation lacks a statistical consistency theorem"
            }
        }
    }
}

/// Feature-gated Lorentz KSG estimate with typed geometry and research status.
#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct HyperbolicKsgMiReport {
    pub estimate_nats: f64,
    pub signed_estimate_nats: f64,
    pub n_samples: usize,
    pub k: usize,
    pub metric: HyperbolicMetric,
    pub negative_handling: NegativeHandling,
    pub support_contract: HyperbolicSupportContract,
    pub method_status: KsgMethodStatus,
    pub scientific_status: ScientificStatus,
    pub estimand: EstimandIdentity,
    pub assumption_ledger: Vec<AssumptionLedgerEntry>,
    pub provenance: KsgProvenance,
    pub provenance_hashes: ProvenanceHashes,
    pub x_diagnostics: ContinuousInputDiagnostics,
    pub y_diagnostics: ContinuousInputDiagnostics,
    pub joint_shells: NeighborShellDiagnostics,
    pub local_diagnostics: KsgLocalDiagnosticsSummary,
    pub neighbor_backend: KsgNeighborBackend,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
    pub geometry_model: HyperbolicKsgGeometryModel,
    pub curvature: HyperbolicCurvature,
    /// `d` inferred from a Lorentz row of width `d + 1`.
    pub x_hyperbolic_dimension: usize,
    /// `d` inferred from a Lorentz row of width `d + 1`.
    pub y_hyperbolic_dimension: usize,
    pub warnings: Vec<HyperbolicKsgReportWarning>,
    pub report_warnings: Vec<WarningCode>,
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct HyperbolicKsgTrajectoryReport {
    pub varied_parameter: &'static str,
    pub reports: Vec<HyperbolicKsgMiReport>,
    pub aggregate_resource_estimate: ResourceEstimate,
}

/// Estimate KSG mutual information and return scoped interpretation metadata and diagnostics.
///
/// This is the canonical stable entry point. Scalar and local-term paths are available only in
/// the default-off experimental namespace because a publication-facing number must remain coupled
/// to its assumptions, provenance, diagnostics, revision identity, and resource preflight.
pub fn ksg_mi_report(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
) -> PidResult<KsgMiReport> {
    ksg_mi_report_with_budget(x, y, cfg, provenance, ResourceBudget::default())
}

/// Report-first KSG with an explicit memory/work/thread budget.
pub fn ksg_mi_report_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
) -> PidResult<KsgMiReport> {
    let cancellation = CancellationToken::new();
    ksg_mi_report_with_budget_and_cancellation(
        x,
        y,
        cfg,
        provenance,
        resource_budget,
        &cancellation,
    )
}

/// Report-first KSG with explicit resource and cooperative-cancellation controls.
pub fn ksg_mi_report_with_budget_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<KsgMiReport> {
    Ok(ksg_mi_report_with_local_terms_and_cancellation(
        x,
        y,
        cfg,
        provenance,
        resource_budget,
        cancellation,
    )?
    .report)
}

#[cfg(feature = "experimental-continuous")]
pub(crate) fn ksg_mi_report_with_local_terms(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
) -> PidResult<KsgReportComputation> {
    let cancellation = CancellationToken::new();
    ksg_mi_report_with_local_terms_and_cancellation(
        x,
        y,
        cfg,
        provenance,
        resource_budget,
        &cancellation,
    )
}

pub(crate) fn ksg_mi_report_with_local_terms_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<KsgReportComputation> {
    let kernel_config = KernelKsgConfig::stable(cfg);
    ksg_mi_report_with_kernel_and_cancellation(
        x,
        y,
        &kernel_config,
        provenance,
        resource_budget,
        cancellation,
    )
}

fn ksg_mi_report_with_kernel_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KernelKsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<KsgReportComputation> {
    // Preserve shape/config/support error precedence before the report-only provenance gate.
    validate_ksg_pair_structure_with_kernel("ksg_mi_report", x, y, cfg)?;
    #[cfg(feature = "experimental-hyperbolic")]
    if matches!(cfg.kernel_metric, KernelMetric::HyperbolicLorentz { .. })
        && provenance.embedding_training_provenance().is_none()
    {
        return Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperbolic reports require embedding_training_provenance",
        });
    }

    let effective_threads = effective_thread_count(resource_budget.max_threads, x.nrows());
    let resource_estimate = ksg_report_resource_estimate(x, y, provenance, effective_threads)?;
    resource_budget.check("ksg_mi_report", resource_estimate)?;
    cancellation.check("ksg_mi_report", 0, x.nrows())?;
    let use_tree = NnBackend::Auto.use_tree(cfg.kernel_metric, x.nrows(), x.ncols() + y.ncols());
    let local = with_thread_budget(effective_threads, || {
        ksg_local_diagnostics_backend_with_kernel_and_cancellation(
            x,
            y,
            cfg,
            NnBackend::Auto,
            resource_budget,
            cancellation,
        )
    })?;
    let signed_estimate =
        compensated_sum(local.iter().map(|value| value.term_nats)) / local.len() as f64;
    let estimate_nats = match cfg.negative_handling {
        NegativeHandling::Allow => signed_estimate,
        NegativeHandling::ClampToZero => signed_estimate.max(0.0),
    };
    #[cfg(feature = "experimental-continuous")]
    let local_terms_nats = {
        let mut terms =
            try_vec_with_capacity("ksg retained local terms", local.len(), resource_budget)?;
        terms.extend(local.iter().map(|value| value.term_nats));
        terms
    };
    let local_diagnostics =
        summarize_local_diagnostics_with_cancellation(&local, resource_budget, cancellation)?;
    let x_diagnostics = continuous_input_diagnostics_with_kernel_and_cancellation(
        x,
        cfg.k,
        cfg.kernel_metric,
        resource_budget,
        cancellation,
    )?;
    let y_diagnostics = continuous_input_diagnostics_with_kernel_and_cancellation(
        y,
        cfg.k,
        cfg.kernel_metric,
        resource_budget,
        cancellation,
    )?;
    let joint_shells = continuous_joint_shell_diagnostics_with_kernel_and_cancellation(
        &[x, y],
        cfg.k,
        cfg.kernel_metric,
        resource_budget,
        cancellation,
    )?;

    let mut warnings = try_vec_with_capacity("ksg warnings", 3, resource_budget)?;
    warnings.push(KsgReportWarning::SampleDiagnosticsCannotProveSupport);
    if has_shell_pathology(x_diagnostics.marginal_shells)
        || has_shell_pathology(y_diagnostics.marginal_shells)
    {
        warnings.push(KsgReportWarning::MarginalNeighborShellPathology);
    }

    let (method_status, x_hyperbolic_dimension, y_hyperbolic_dimension) = match cfg.kernel_metric {
        KernelMetric::Chebyshev => (KsgMethodStatus::RestrictedDomain, None, None),
        #[cfg(feature = "experimental-hyperbolic")]
        KernelMetric::HyperbolicLorentz { .. } => (
            KsgMethodStatus::Experimental,
            Some(x.ncols() - 1),
            Some(y.ncols() - 1),
        ),
    };

    let scientific_status = match method_status {
        KsgMethodStatus::RestrictedDomain => ScientificStatus::ConditionalContinuous,
        KsgMethodStatus::Experimental => ScientificStatus::ResearchOnly,
    };
    let metric_identity = match cfg.kernel_metric {
        KernelMetric::Chebyshev => "chebyshev-max-product",
        #[cfg(feature = "experimental-hyperbolic")]
        KernelMetric::HyperbolicLorentz { .. } => "lorentz-hyperboloid-curvature-minus-one",
    };
    let estimand = EstimandIdentity {
        family: "kraskov-stoegbauer-grassberger-mutual-information",
        definition_revision: "ksg1-product-small-ball-v1",
        estimator_revision: "strict-unique-shell-integer-harmonic-report-v4",
        units: InformationUnit::Nats,
        metric: metric_identity,
        source_gauge: None,
    };
    let assumption_ledger = ksg_assumption_ledger(provenance, joint_shells, resource_budget)?;
    let mut input_hashes_sha256 =
        try_vec_with_capacity("ksg report input hashes", 2, resource_budget)?;
    input_hashes_sha256.extend([
        hash_matrix_with_cancellation(x, cancellation)?,
        hash_matrix_with_cancellation(y, cancellation)?,
    ]);
    let provenance_hashes = ProvenanceHashes {
        input_hashes_sha256,
        preprocessing_hash_sha256: hash_text(provenance.preprocessing_description()),
        observation_model_hash_sha256: hash_text(provenance.observation_model_description()),
        training_split_id: provenance
            .training_split_id()
            .map(|value| try_provenance_string("ksg report split identity", value))
            .transpose()?,
        evaluation_split_id: provenance
            .evaluation_split_id()
            .map(|value| try_provenance_string("ksg report split identity", value))
            .transpose()?,
    };
    let mut report_warnings = try_vec_with_capacity("ksg report warnings", 8, resource_budget)?;
    report_warnings.push(WarningCode::DiagnosticsDoNotProvePopulationAssumptions);
    if matches!(
        cfg.support_contract,
        SupportContract::AssumeRegularFullDimensional {
            boundary: BoundaryModel::Unknown,
            ..
        }
    ) {
        report_warnings.push(WarningCode::BoundaryModelUnknown);
    }
    if provenance.sampling_model_description.is_none() {
        report_warnings.push(WarningCode::DependenceDiagnosticsNotEvaluated);
    }
    report_warnings.extend([
        WarningCode::KTrajectoryNotEvaluated,
        WarningCode::SampleSizeTrajectoryNotEvaluated,
        WarningCode::TransformationSensitivityNotEvaluated,
        WarningCode::ObservationNoiseSensitivityNotEvaluated,
    ]);
    if scientific_status == ScientificStatus::ResearchOnly {
        report_warnings.push(WarningCode::ExperimentalEstimator);
    }

    let report = KsgMiReport {
        estimate_nats,
        signed_estimate_nats: signed_estimate,
        n_samples: x.nrows(),
        k: cfg.k,
        metric: cfg.metric,
        negative_handling: cfg.negative_handling,
        support_contract: cfg.support_contract,
        method_status,
        scientific_status,
        estimand,
        assumption_ledger,
        provenance: provenance.try_clone_with_budget(resource_budget)?,
        provenance_hashes,
        x_diagnostics,
        y_diagnostics,
        joint_shells,
        local_diagnostics,
        neighbor_backend: if use_tree {
            KsgNeighborBackend::ExactChebyshevKdTree
        } else {
            KsgNeighborBackend::BruteForce
        },
        resource_estimate,
        resource_budget,
        geometry_model: KsgGeometryModel::AmbientChebyshev,
        curvature: None,
        x_hyperbolic_dimension,
        y_hyperbolic_dimension,
        warnings,
        report_warnings,
    };
    cancellation.check("ksg_mi_report", x.nrows(), x.nrows())?;
    Ok(KsgReportComputation {
        report,
        #[cfg(feature = "experimental-continuous")]
        local_terms_nats,
    })
}

/// Compute a feature-gated Lorentz-model KSG report.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_mi_report(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
) -> PidResult<HyperbolicKsgMiReport> {
    hyperbolic_ksg_mi_report_with_budget(x, y, cfg, provenance, ResourceBudget::default())
}

/// Compute a Lorentz-model KSG report under an explicit resource budget.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_mi_report_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
) -> PidResult<HyperbolicKsgMiReport> {
    let cancellation = CancellationToken::new();
    hyperbolic_ksg_mi_report_with_budget_and_cancellation(
        x,
        y,
        cfg,
        provenance,
        resource_budget,
        &cancellation,
    )
}

/// Compute a Lorentz-model KSG report with resource and cancellation controls.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_mi_report_with_budget_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<HyperbolicKsgMiReport> {
    let kernel_config = cfg.kernel_config();
    // Preserve structural/support and provenance error precedence before resource preflight.
    validate_ksg_pair_structure_with_kernel("ksg_mi_report", x, y, &kernel_config)?;
    validate_hyperbolic_ksg_provenance(provenance)?;
    let resource_estimate = hyperbolic_ksg_report_resource_estimate(
        x,
        y,
        provenance,
        effective_thread_count(resource_budget.max_threads, x.nrows()),
    )?;
    resource_budget.check("hyperbolic_ksg_mi_report", resource_estimate)?;
    let report = ksg_mi_report_with_kernel_and_cancellation(
        x,
        y,
        &kernel_config,
        provenance,
        resource_budget,
        cancellation,
    )?
    .report;

    let warning_count = report
        .warnings
        .len()
        .checked_add(1)
        .ok_or(PidError::SizeOverflow {
            operation: "hyperbolic_ksg_mi_report",
        })?;
    if warning_count > HYPERBOLIC_KSG_WARNING_CAPACITY {
        return Err(PidError::SizeOverflow {
            operation: "hyperbolic_ksg_mi_report",
        });
    }
    let mut warnings = try_vec_with_capacity(
        "hyperbolic KSG warnings",
        HYPERBOLIC_KSG_WARNING_CAPACITY,
        resource_budget,
    )?;
    for warning in report.warnings {
        warnings.push(match warning {
            KsgReportWarning::SampleDiagnosticsCannotProveSupport => {
                HyperbolicKsgReportWarning::SampleDiagnosticsCannotProveSupport
            }
            KsgReportWarning::MarginalNeighborShellPathology => {
                HyperbolicKsgReportWarning::MarginalNeighborShellPathology
            }
        });
    }
    warnings.push(HyperbolicKsgReportWarning::ConsistencyNotEstablished);

    Ok(HyperbolicKsgMiReport {
        estimate_nats: report.estimate_nats,
        signed_estimate_nats: report.signed_estimate_nats,
        n_samples: report.n_samples,
        k: report.k,
        metric: cfg.metric,
        negative_handling: report.negative_handling,
        support_contract: HyperbolicSupportContract::AssumeSmoothManifold,
        method_status: report.method_status,
        scientific_status: report.scientific_status,
        estimand: report.estimand,
        assumption_ledger: report.assumption_ledger,
        provenance: report.provenance,
        provenance_hashes: report.provenance_hashes,
        x_diagnostics: report.x_diagnostics,
        y_diagnostics: report.y_diagnostics,
        joint_shells: report.joint_shells,
        local_diagnostics: report.local_diagnostics,
        neighbor_backend: report.neighbor_backend,
        resource_estimate,
        resource_budget: report.resource_budget,
        geometry_model: HyperbolicKsgGeometryModel::LorentzHyperboloid,
        curvature: cfg.metric.curvature,
        x_hyperbolic_dimension: x.ncols() - 1,
        y_hyperbolic_dimension: y.ncols() - 1,
        warnings,
        report_warnings: report.report_warnings,
    })
}

#[cfg(feature = "experimental-hyperbolic")]
fn validate_hyperbolic_ksg_provenance(provenance: &KsgProvenance) -> PidResult<()> {
    if provenance.embedding_training_provenance().is_none() {
        return Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperbolic reports require embedding_training_provenance",
        });
    }
    Ok(())
}

/// Evaluate Lorentz-model reports over a declared `k` grid.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_k_trajectory(
    x: MatRef<'_>,
    y: MatRef<'_>,
    k_values: &[usize],
    base_config: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<HyperbolicKsgTrajectoryReport> {
    if k_values.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "ksg_k_trajectory",
            message: "k_values must be nonempty",
        });
    }
    for &k in k_values {
        let config = base_config.clone().with_k(k);
        let kernel_config = config.kernel_config();
        validate_ksg_pair_structure_with_kernel("ksg_mi_report", x, y, &kernel_config)?;
    }
    validate_hyperbolic_ksg_provenance(provenance)?;
    let one = hyperbolic_ksg_report_resource_estimate(
        x,
        y,
        provenance,
        effective_thread_count(budget.max_threads, x.nrows()),
    )?;
    let aggregate = repeat_resource_estimate("ksg_k_trajectory", one, k_values.len())?;
    budget.check("ksg_k_trajectory", aggregate)?;
    let mut reports = try_vec_with_capacity("ksg_k_trajectory", k_values.len(), budget)?;
    for &k in k_values {
        let config = base_config.clone().with_k(k);
        reports.push(hyperbolic_ksg_mi_report_with_budget(
            x, y, &config, provenance, budget,
        )?);
    }
    Ok(HyperbolicKsgTrajectoryReport {
        varied_parameter: "k",
        reports,
        aggregate_resource_estimate: aggregate,
    })
}

/// Evaluate Lorentz-model reports on increasing row prefixes.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_sample_size_trajectory(
    x: MatRef<'_>,
    y: MatRef<'_>,
    sample_sizes: &[usize],
    config: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<HyperbolicKsgTrajectoryReport> {
    if x.nrows() != y.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "ksg_sample_size_trajectory",
            left_rows: x.nrows(),
            right_rows: y.nrows(),
        });
    }
    if sample_sizes.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "ksg_sample_size_trajectory",
            message: "sample_sizes must be nonempty",
        });
    }
    let kernel_config = config.kernel_config();
    validate_ksg_pair_structure_with_kernel("ksg_mi_report", x, y, &kernel_config)?;
    for &n in sample_sizes {
        if n > x.nrows() || n <= config.k {
            return Err(PidError::InvalidK {
                k: config.k,
                n_samples: n,
            });
        }
    }
    validate_hyperbolic_ksg_provenance(provenance)?;
    let mut aggregate = ResourceEstimate::ZERO;
    for &n in sample_sizes {
        let x_len = n.checked_mul(x.ncols()).ok_or(PidError::SizeOverflow {
            operation: "ksg_sample_size_trajectory",
        })?;
        let y_len = n.checked_mul(y.ncols()).ok_or(PidError::SizeOverflow {
            operation: "ksg_sample_size_trajectory",
        })?;
        let x_prefix = MatRef::new(&x.as_slice()[..x_len], n, x.ncols())?;
        let y_prefix = MatRef::new(&y.as_slice()[..y_len], n, y.ncols())?;
        aggregate = add_resource_estimates(
            "ksg_sample_size_trajectory",
            aggregate,
            hyperbolic_ksg_report_resource_estimate(
                x_prefix,
                y_prefix,
                provenance,
                effective_thread_count(budget.max_threads, n),
            )?,
        )?;
    }
    budget.check("ksg_sample_size_trajectory", aggregate)?;
    let mut reports =
        try_vec_with_capacity("ksg_sample_size_trajectory", sample_sizes.len(), budget)?;
    for &n in sample_sizes {
        let x_len = n * x.ncols();
        let y_len = n * y.ncols();
        let x_prefix = MatRef::new(&x.as_slice()[..x_len], n, x.ncols())?;
        let y_prefix = MatRef::new(&y.as_slice()[..y_len], n, y.ncols())?;
        reports.push(hyperbolic_ksg_mi_report_with_budget(
            x_prefix, y_prefix, config, provenance, budget,
        )?);
    }
    Ok(HyperbolicKsgTrajectoryReport {
        varied_parameter: "sample_size",
        reports,
        aggregate_resource_estimate: aggregate,
    })
}

/// Evaluate complete reports over a declared `k` grid without discarding diagnostics.
pub fn ksg_k_trajectory(
    x: MatRef<'_>,
    y: MatRef<'_>,
    k_values: &[usize],
    base_config: &KsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<KsgTrajectoryReport> {
    if k_values.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "ksg_k_trajectory",
            message: "k_values must be nonempty",
        });
    }
    let one = ksg_report_resource_estimate(
        x,
        y,
        provenance,
        effective_thread_count(budget.max_threads, x.nrows()),
    )?;
    let aggregate = repeat_resource_estimate("ksg_k_trajectory", one, k_values.len())?;
    budget.check("ksg_k_trajectory", aggregate)?;
    let mut reports = try_vec_with_capacity("ksg_k_trajectory", k_values.len(), budget)?;
    for &k in k_values {
        let mut config = base_config.clone();
        config.k = k;
        reports.push(ksg_mi_report_with_budget(
            x, y, &config, provenance, budget,
        )?);
    }
    Ok(KsgTrajectoryReport {
        varied_parameter: "k",
        reports,
        aggregate_resource_estimate: aggregate,
    })
}

/// Evaluate complete reports on increasing row prefixes.
///
/// Prefix trajectories are scientifically meaningful only when row ordering is independent of
/// the process being estimated (for example a fixed seeded random ordering). The ordering policy
/// belongs in provenance.
pub fn ksg_sample_size_trajectory(
    x: MatRef<'_>,
    y: MatRef<'_>,
    sample_sizes: &[usize],
    config: &KsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<KsgTrajectoryReport> {
    if x.nrows() != y.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "ksg_sample_size_trajectory",
            left_rows: x.nrows(),
            right_rows: y.nrows(),
        });
    }
    if sample_sizes.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "ksg_sample_size_trajectory",
            message: "sample_sizes must be nonempty",
        });
    }
    let mut aggregate = ResourceEstimate::ZERO;
    for &n in sample_sizes {
        if n > x.nrows() || n <= config.k {
            return Err(PidError::InvalidK {
                k: config.k,
                n_samples: n,
            });
        }
        let x_len = n.checked_mul(x.ncols()).ok_or(PidError::SizeOverflow {
            operation: "ksg_sample_size_trajectory",
        })?;
        let y_len = n.checked_mul(y.ncols()).ok_or(PidError::SizeOverflow {
            operation: "ksg_sample_size_trajectory",
        })?;
        let x_prefix = MatRef::new(&x.as_slice()[..x_len], n, x.ncols())?;
        let y_prefix = MatRef::new(&y.as_slice()[..y_len], n, y.ncols())?;
        aggregate = add_resource_estimates(
            "ksg_sample_size_trajectory",
            aggregate,
            ksg_report_resource_estimate(
                x_prefix,
                y_prefix,
                provenance,
                effective_thread_count(budget.max_threads, n),
            )?,
        )?;
    }
    budget.check("ksg_sample_size_trajectory", aggregate)?;
    let mut reports =
        try_vec_with_capacity("ksg_sample_size_trajectory", sample_sizes.len(), budget)?;
    for &n in sample_sizes {
        let x_len = n * x.ncols();
        let y_len = n * y.ncols();
        let x_prefix = MatRef::new(&x.as_slice()[..x_len], n, x.ncols())?;
        let y_prefix = MatRef::new(&y.as_slice()[..y_len], n, y.ncols())?;
        reports.push(ksg_mi_report_with_budget(
            x_prefix, y_prefix, config, provenance, budget,
        )?);
    }
    Ok(KsgTrajectoryReport {
        varied_parameter: "sample_size",
        reports,
        aggregate_resource_estimate: aggregate,
    })
}

fn repeat_resource_estimate(
    operation: &'static str,
    estimate: ResourceEstimate,
    count: usize,
) -> PidResult<ResourceEstimate> {
    let count = count as u128;
    Ok(ResourceEstimate {
        // Reports run sequentially, but their owned diagnostics/provenance remain in the
        // trajectory. Multiplying the full per-report estimate is conservative and guarantees
        // retained output cannot bypass the caller's ceiling.
        estimated_bytes: estimate
            .estimated_bytes
            .checked_mul(count)
            .ok_or(PidError::SizeOverflow { operation })?,
        pairwise_distances: estimate
            .pairwise_distances
            .checked_mul(count)
            .ok_or(PidError::SizeOverflow { operation })?,
        operations_hint: estimate
            .operations_hint
            .checked_mul(count)
            .ok_or(PidError::SizeOverflow { operation })?,
    })
}

fn add_resource_estimates(
    operation: &'static str,
    left: ResourceEstimate,
    right: ResourceEstimate,
) -> PidResult<ResourceEstimate> {
    Ok(ResourceEstimate {
        // Retained reports accumulate in the trajectory. Summing the complete per-report peaks
        // is conservative but prevents output heaps from escaping the aggregate ceiling.
        estimated_bytes: left
            .estimated_bytes
            .checked_add(right.estimated_bytes)
            .ok_or(PidError::SizeOverflow { operation })?,
        pairwise_distances: left
            .pairwise_distances
            .checked_add(right.pairwise_distances)
            .ok_or(PidError::SizeOverflow { operation })?,
        operations_hint: left
            .operations_hint
            .checked_add(right.operations_hint)
            .ok_or(PidError::SizeOverflow { operation })?,
    })
}

fn has_shell_pathology(diagnostics: NeighborShellDiagnostics) -> bool {
    diagnostics.zero_radius_queries > 0 || diagnostics.ambiguous_positive_shell_queries > 0
}

/// Worst-case pairwise-work and scratch/tree-memory estimate for report-first KSG.
pub fn ksg_resource_estimate(x: MatRef<'_>, y: MatRef<'_>) -> PidResult<ResourceEstimate> {
    ksg_resource_estimate_with_coordinate_work_factor(x, y, 1)
}

fn ksg_resource_estimate_with_coordinate_work_factor(
    x: MatRef<'_>,
    y: MatRef<'_>,
    coordinate_work_factor: u128,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "ksg_mi_report";
    let n = x.nrows() as u128;
    let dimensions = x
        .ncols()
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })? as u128;
    let pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let tree_build_operations = n
        .checked_mul(dimensions.max(1))
        .and_then(|value| {
            value.checked_mul(if x.nrows() <= 1 {
                1
            } else {
                (usize::BITS - (x.nrows() - 1).leading_zeros()) as u128
            })
        })
        .and_then(|value| value.checked_mul(3))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let estimator_operations = pairs
        .checked_mul(dimensions.max(1))
        .and_then(|value| value.checked_mul(coordinate_work_factor))
        .and_then(|value| value.checked_mul(6))
        .and_then(|value| value.checked_add(tree_build_operations))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    // Conservative simultaneous tree/scratch/local-diagnostic storage. The estimator does not
    // materialize an n-by-n distance matrix.
    let estimator_bytes = dimensions
        .checked_mul(4)
        .and_then(|value| value.checked_add(64))
        .and_then(|value| value.checked_mul(n))
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let x_support = crate::support::continuous_diagnostics_resource_estimate(
        &[x],
        true,
        coordinate_work_factor,
    )?;
    let y_support = crate::support::continuous_diagnostics_resource_estimate(
        &[y],
        true,
        coordinate_work_factor,
    )?;
    let joint_support = crate::support::continuous_diagnostics_resource_estimate(
        &[x, y],
        false,
        coordinate_work_factor,
    )?;
    let support_peak_bytes = x_support
        .estimated_bytes
        .max(y_support.estimated_bytes)
        .max(joint_support.estimated_bytes);
    let estimated_bytes =
        estimator_bytes
            .checked_add(support_peak_bytes)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    let pairwise_distances = pairs
        .checked_add(x_support.pairwise_distances)
        .and_then(|value| value.checked_add(y_support.pairwise_distances))
        .and_then(|value| value.checked_add(joint_support.pairwise_distances))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let operations_hint =
        estimator_operations
            .checked_add(x_support.operations_hint.checked_mul(2).ok_or(
                PidError::SizeOverflow {
                    operation: OPERATION,
                },
            )?)
            .and_then(|value| value.checked_add(y_support.operations_hint.checked_mul(2)?))
            .and_then(|value| value.checked_add(joint_support.operations_hint))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    Ok(ResourceEstimate {
        estimated_bytes,
        pairwise_distances,
        operations_hint,
    })
}

/// Conservative KSG preflight including one brute-force scratch buffer per worker.
pub fn ksg_resource_estimate_for_threads(
    x: MatRef<'_>,
    y: MatRef<'_>,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    ksg_resource_estimate_for_threads_with_coordinate_work_factor(x, y, max_threads, 1)
}

fn ksg_resource_estimate_for_threads_with_coordinate_work_factor(
    x: MatRef<'_>,
    y: MatRef<'_>,
    max_threads: usize,
    coordinate_work_factor: u128,
) -> PidResult<ResourceEstimate> {
    if max_threads == 0 {
        return Err(PidError::ResourceLimitExceeded {
            operation: "ksg_mi_report",
            resource: "threads",
            requested: 1,
            limit: 0,
        });
    }
    let mut estimate =
        ksg_resource_estimate_with_coordinate_work_factor(x, y, coordinate_work_factor)?;
    #[cfg(feature = "parallel")]
    let additional_scratch = {
        let active_threads = max_threads.min(x.nrows()).max(1) as u128;
        let scratch = active_threads
            .saturating_sub(1)
            .checked_mul(x.nrows() as u128)
            .and_then(|value| value.checked_mul(std::mem::size_of::<DistPair>() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_mi_report",
            })?;
        let stacks = active_threads
            .checked_mul(WORKER_STACK_BYTES as u128)
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_mi_report",
            })?;
        scratch.checked_add(stacks).ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?
    };
    #[cfg(not(feature = "parallel"))]
    let additional_scratch = 0;
    estimate.estimated_bytes = estimate
        .estimated_bytes
        .checked_add(additional_scratch)
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?;
    Ok(estimate)
}

/// Full report preflight, including worker scratch and retained provenance/diagnostic output.
pub fn ksg_report_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    ksg_report_resource_estimate_with_coordinate_work_factor(x, y, provenance, max_threads, 1)
}

fn ksg_report_resource_estimate_with_coordinate_work_factor(
    x: MatRef<'_>,
    y: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
    coordinate_work_factor: u128,
) -> PidResult<ResourceEstimate> {
    let split_identity_bytes = provenance
        .training_split_id()
        .into_iter()
        .chain(provenance.evaluation_split_id())
        .try_fold(0u128, |total, value| {
            total
                .checked_add(value.len() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "ksg_mi_report",
                })
        })?;
    ksg_report_resource_estimate_for_provenance_bytes_with_coordinate_work_factor(
        x,
        y,
        provenance.heap_bytes()?,
        split_identity_bytes,
        max_threads,
        coordinate_work_factor,
    )
}

/// Full Lorentz-report preflight, including the typed wrapper and warning conversion.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_report_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    let mut estimate = ksg_report_resource_estimate_with_coordinate_work_factor(
        x,
        y,
        provenance,
        max_threads,
        crate::hyperbolic::LORENTZ_DISTANCE_COORDINATE_WORK_FACTOR,
    )?;
    let warning_capacity = HYPERBOLIC_KSG_WARNING_CAPACITY as u128;
    let wrapper_bytes = (std::mem::size_of::<HyperbolicKsgMiReport>() as u128)
        .checked_add(
            warning_capacity
                .checked_mul(std::mem::size_of::<HyperbolicKsgReportWarning>() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "hyperbolic_ksg_mi_report",
                })?,
        )
        .ok_or(PidError::SizeOverflow {
            operation: "hyperbolic_ksg_mi_report",
        })?;
    estimate.estimated_bytes =
        estimate
            .estimated_bytes
            .checked_add(wrapper_bytes)
            .ok_or(PidError::SizeOverflow {
                operation: "hyperbolic_ksg_mi_report",
            })?;
    estimate.operations_hint = estimate
        .operations_hint
        .checked_add(warning_capacity)
        .ok_or(PidError::SizeOverflow {
            operation: "hyperbolic_ksg_mi_report",
        })?;
    Ok(estimate)
}

fn ksg_report_resource_estimate_for_provenance_bytes_with_coordinate_work_factor(
    x: MatRef<'_>,
    y: MatRef<'_>,
    provenance_heap_bytes: u128,
    split_identity_bytes: u128,
    max_threads: usize,
    coordinate_work_factor: u128,
) -> PidResult<ResourceEstimate> {
    let estimate = ksg_resource_estimate_for_threads_with_coordinate_work_factor(
        x,
        y,
        max_threads,
        coordinate_work_factor,
    )?;
    let dimensions = x
        .ncols()
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?;
    add_ksg_report_retained(
        estimate,
        x.nrows(),
        dimensions,
        provenance_heap_bytes,
        split_identity_bytes,
    )
}

/// Report preflight for a source represented as several Chebyshev-concatenated blocks.
///
/// This is used by higher-level report assemblers so they can preflight a joint-variable report
/// without first allocating the explicit row-major concatenation used for the retained report.
#[cfg(feature = "experimental-continuous")]
pub(crate) fn ksg_xblocks_report_resource_estimate(
    x_blocks: &[MatRef<'_>],
    y: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "ksg_mi_xblocks_report";
    if x_blocks.is_empty() {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "x_blocks must be nonempty",
        });
    }
    let dimensions = x_blocks.iter().try_fold(y.ncols(), |total, block| {
        total
            .checked_add(block.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })
    })?;
    let split_identity_bytes = provenance
        .training_split_id()
        .into_iter()
        .chain(provenance.evaluation_split_id())
        .try_fold(0u128, |total, value| {
            total
                .checked_add(value.len() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })
        })?;
    add_ksg_report_retained(
        ksg_xblocks_resource_estimate(x_blocks, y, max_threads)?,
        y.nrows(),
        dimensions,
        provenance.heap_bytes()?,
        split_identity_bytes,
    )
}

fn add_ksg_report_retained(
    mut estimate: ResourceEstimate,
    n_samples: usize,
    dimensions: usize,
    provenance_heap_bytes: u128,
    split_identity_bytes: u128,
) -> PidResult<ResourceEstimate> {
    let retained_local_terms = (n_samples as u128)
        .checked_mul(std::mem::size_of::<f64>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?;
    let retained_bytes = provenance_heap_bytes
        .checked_add(split_identity_bytes)
        .and_then(|value| value.checked_add(retained_local_terms))
        .and_then(|value| value.checked_add(std::mem::size_of::<KsgMiReport>() as u128))
        .and_then(|value| {
            value.checked_add(
                12u128.checked_mul(std::mem::size_of::<AssumptionLedgerEntry>() as u128)?,
            )
        })
        .and_then(|value| value.checked_add(2 * 32))
        .and_then(|value| {
            value.checked_add(
                (dimensions as u128)
                    .checked_mul(std::mem::size_of::<CoordinateCardinalityDiagnostics>() as u128)?,
            )
        })
        .and_then(|value| {
            value.checked_add(3u128.checked_mul(std::mem::size_of::<KsgReportWarning>() as u128)?)
        })
        .and_then(|value| {
            value.checked_add(8u128.checked_mul(std::mem::size_of::<WarningCode>() as u128)?)
        })
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?;
    estimate.estimated_bytes =
        estimate
            .estimated_bytes
            .checked_add(retained_bytes)
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_mi_report",
            })?;
    Ok(estimate)
}

fn summarize_local_diagnostics_with_cancellation(
    local: &[KsgLocalDiagnostic],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<KsgLocalDiagnosticsSummary> {
    let mut radii = try_vec_with_capacity("ksg local radius summary", local.len(), budget)?;
    let mut x_counts = try_vec_with_capacity("ksg x-count summary", local.len(), budget)?;
    let mut y_counts = try_vec_with_capacity("ksg y-count summary", local.len(), budget)?;
    let mut terms = try_vec_with_capacity("ksg local-term summary", local.len(), budget)?;
    for (index, diagnostic) in local.iter().enumerate() {
        if index.is_multiple_of(1024) {
            cancellation.check("ksg local diagnostic summary", index, local.len())?;
        }
        radii.push(diagnostic.joint_radius);
        x_counts.push(diagnostic.x_count);
        y_counts.push(diagnostic.y_count);
        terms.push(diagnostic.term_nats);
    }
    sort_unstable_by_with_cancellation(
        "ksg local radius summary",
        &mut radii,
        cancellation,
        f64::total_cmp,
    )?;
    sort_unstable_by_with_cancellation(
        "ksg x-count summary",
        &mut x_counts,
        cancellation,
        Ord::cmp,
    )?;
    sort_unstable_by_with_cancellation(
        "ksg y-count summary",
        &mut y_counts,
        cancellation,
        Ord::cmp,
    )?;
    sort_unstable_by_with_cancellation(
        "ksg local-term summary",
        &mut terms,
        cancellation,
        f64::total_cmp,
    )?;
    Ok(KsgLocalDiagnosticsSummary {
        joint_radius: value_quantiles(&radii)?,
        x_marginal_count: count_quantiles(&x_counts)?,
        y_marginal_count: count_quantiles(&y_counts)?,
        local_mi_nats: value_quantiles(&terms)?,
    })
}

fn nearest_rank_index(len: usize, percentile: u128) -> PidResult<usize> {
    if len == 0 || percentile > 100 {
        return Err(PidError::InvalidConfig {
            context: "ksg diagnostic quantiles",
            message: "quantiles require nonempty data and a percentile in 0..=100",
        });
    }
    let numerator = (len.saturating_sub(1) as u128)
        .checked_mul(percentile)
        .and_then(|value| value.checked_add(50))
        .ok_or(PidError::SizeOverflow {
            operation: "ksg diagnostic quantiles",
        })?;
    usize::try_from(numerator / 100).map_err(|_| PidError::SizeOverflow {
        operation: "ksg diagnostic quantiles",
    })
}

pub(crate) fn value_quantiles(sorted: &[f64]) -> PidResult<KsgValueQuantiles> {
    if sorted.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "ksg local diagnostic contains a non-finite value",
        });
    }
    Ok(KsgValueQuantiles {
        min: sorted[nearest_rank_index(sorted.len(), 0)?],
        p10: sorted[nearest_rank_index(sorted.len(), 10)?],
        median: sorted[nearest_rank_index(sorted.len(), 50)?],
        p90: sorted[nearest_rank_index(sorted.len(), 90)?],
        p99: sorted[nearest_rank_index(sorted.len(), 99)?],
        max: sorted[nearest_rank_index(sorted.len(), 100)?],
    })
}

pub(crate) fn count_quantiles(sorted: &[usize]) -> PidResult<KsgCountQuantiles> {
    Ok(KsgCountQuantiles {
        min: sorted[nearest_rank_index(sorted.len(), 0)?],
        p10: sorted[nearest_rank_index(sorted.len(), 10)?],
        median: sorted[nearest_rank_index(sorted.len(), 50)?],
        p90: sorted[nearest_rank_index(sorted.len(), 90)?],
        p99: sorted[nearest_rank_index(sorted.len(), 99)?],
        max: sorted[nearest_rank_index(sorted.len(), 100)?],
    })
}

fn ksg_assumption_ledger(
    provenance: &KsgProvenance,
    joint_shells: NeighborShellDiagnostics,
    budget: ResourceBudget,
) -> PidResult<Vec<AssumptionLedgerEntry>> {
    let mut ledger = try_vec_with_capacity("ksg assumption ledger", 12, budget)?;
    let shell_state = if joint_shells.zero_radius_queries == 0
        && joint_shells.ambiguous_positive_shell_queries == 0
    {
        AssumptionState::FiniteSampleChecksPassed
    } else {
        AssumptionState::UnsupportedObservedCondition
    };
    ledger.extend([
        AssumptionLedgerEntry {
            assumption: Assumption::RegularContinuousOrManifoldLaw,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; finite samples cannot prove the population support model",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FixedLocalDimension,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller asserts each required marginal and joint law is locally fixed-dimensional in its own ambient space",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::RegularFiniteDensity,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; radius trajectories are still required",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FiniteMutualInformation,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; a finite estimate does not prove finite population MI",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::DeclaredSamplingDependence,
            state: if provenance.sampling_model_description.is_some() {
                AssumptionState::AssumptionsDeclared
            } else {
                AssumptionState::WarningPresent
            },
            note: "dependence diagnostics are workflow-specific and not inferred here",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::UniqueKthNeighborShell,
            state: shell_state,
            note: "every joint shell used by the estimate is checked exactly",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::LocalNeighborhoods,
            state: AssumptionState::NotEvaluated,
            note: "interpret the reported radius quantiles against domain scales",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::CommonBranchLeadingScale,
            state: AssumptionState::NotEvaluated,
            note: "not used by pairwise MI; required by continuous shared exclusions",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::LowerOrderBranchIntersections,
            state: AssumptionState::NotEvaluated,
            note: "not used by pairwise MI; required by continuous shared exclusions",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FixedPreprocessingAndMetric,
            state: AssumptionState::AssumptionsDeclared,
            note: "the preprocessing description and metric are hashed in the report",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::AdequateSampleSize,
            state: AssumptionState::NotEvaluated,
            note: "run declared k and increasing-sample-size trajectories",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::AdaptiveTransformsFitOutsideEvaluationData,
            state: if provenance.training_split_id.is_some()
                && provenance.evaluation_split_id.is_some()
                && provenance.training_split_id != provenance.evaluation_split_id
            {
                AssumptionState::AssumptionsDeclared
            } else {
                AssumptionState::WarningPresent
            },
            note: "distinct training and evaluation split identifiers are required for adaptive transforms",
        },
    ]);
    Ok(ledger)
}

#[cfg(feature = "experimental-continuous")]
pub(crate) fn hash_matrix(matrix: MatRef<'_>) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update((matrix.nrows() as u128).to_le_bytes());
    digest.update((matrix.ncols() as u128).to_le_bytes());
    for row in 0..matrix.nrows() {
        for value in matrix.row(row) {
            digest.update(value.to_bits().to_le_bytes());
        }
    }
    digest.finalize().into()
}

fn hash_matrix_with_cancellation(
    matrix: MatRef<'_>,
    cancellation: &CancellationToken,
) -> PidResult<[u8; 32]> {
    let total_values =
        matrix
            .nrows()
            .checked_mul(matrix.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: "ksg report input hash",
            })?;
    let mut digest = Sha256::new();
    digest.update((matrix.nrows() as u128).to_le_bytes());
    digest.update((matrix.ncols() as u128).to_le_bytes());
    let mut completed_values = 0usize;
    cancellation.check("ksg report input hash", completed_values, total_values)?;
    for row in 0..matrix.nrows() {
        for value in matrix.row(row) {
            digest.update(value.to_bits().to_le_bytes());
            completed_values += 1;
            if completed_values.is_multiple_of(1024) {
                cancellation.check("ksg report input hash", completed_values, total_values)?;
            }
        }
    }
    cancellation.check("ksg report input hash", completed_values, total_values)?;
    Ok(digest.finalize().into())
}

pub(crate) fn hash_text(value: &str) -> [u8; 32] {
    Sha256::digest(value.as_bytes()).into()
}

/// KSG mutual information estimator (Algorithm 1 style).
///
/// - Uses a kNN search in joint space (X,Y). This scalar API accepts ordinary Chebyshev/L∞
///   geometry; experimental Lorentz geometry is provenance-gated through
///   `hyperbolic_ksg_mi_report`.
/// - Uses strict-inequality semantics for marginal counts (`< eps_raw`) via `strict_radius` + `<=`.
/// - Returns MI in nats (natural log).
///
/// Eligible low-dimensional Chebyshev inputs use an exact kd-tree with typically
/// sublinear pruned queries; other inputs use the brute-force scan. A kd-tree query
/// is still O(n) in the worst case, so the estimator remains O(n²) worst-case.
///
/// # Assumptions / failure modes
/// - **Declared support:** the default support contract is unspecified and fails closed. Ordinary
///   Chebyshev KSG requires a caller assertion that every marginal and joint law used here is
///   full-dimensional and absolutely continuous. Exact coordinate ties are incompatible with the
///   estimator's ideal i.i.d., unrounded continuous-sample conditions, but neither identify their
///   cause nor classify population support; all-unique finite observations do not prove the model.
/// - **i.i.d. samples:** KSG assumes independent samples from a fixed distribution. For time-series
///   data (VLA trajectories), autocorrelation can seriously bias estimates unless you subsample or
///   otherwise account for dependence.
/// - **Observed ties and geometry:** exact coordinate ties are rejected by the continuous-sample
///   preflight. Separately, an otherwise accepted sample can still produce a non-positive kNN
///   radius or multiple observations on a positive boundary; those cases trigger
///   `PidError::NumericalInstability` or `PidError::AmbiguousKthNeighborShell`, respectively.
///   Adding jitter changes the estimated distribution; use it only under an explicit
///   observation-noise model or as a seeded, reported noise-scale sensitivity analysis. Otherwise
///   use an estimator whose discrete, quantized, or mixed-support contract matches the data.
/// - **High dimension:** kNN distances concentrate with large ambient/intrinsic dimension; the
///   estimator can become unstable or dominated by finite-sample noise.
/// - **Strong dependence:** even at low dimension, near-deterministic relationships (very large
///   true MI) can require prohibitive sample sizes for kNN MI (see Gao, Ver Steeg, Galstyan 2015).
///   An exact deterministic map between continuous variables has infinite MI and is outside this
///   estimator's domain. An explicit observation-noise model defines a different noisy population
///   law. Finite MI remains a separate population assumption. Otherwise, use a suitable discrete
///   or mixed method.
/// - **Clamping:** `KsgConfig` returns signed estimates by default. Opting into
///   `NegativeHandling::ClampToZero` is a presentation transform, not a mathematical property of
///   the estimator, and must not be applied before algebraic identities or inference.
///
/// # Example
/// ```rust,ignore
/// use pid_core::{experimental::continuous::ksg_mi, stable::continuous::KsgConfig, MatRef};
/// // Columns are dimensions, rows are samples: scalar X and a dependent Y.
/// let x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0];
/// let y = [0.1, 0.9, 2.1, 2.8, 4.2, 4.9, 6.1, 7.0];
/// let x = MatRef::new(&x, 8, 1)?;
/// let y = MatRef::new(&y, 8, 1)?;
/// let mi = ksg_mi(x, y, &KsgConfig::assume_regular_full_dimensional())?; // nats
/// assert!(mi.is_finite());
/// # Ok::<(), pid_core::PidError>(())
/// ```
#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi(x: MatRef<'_>, y: MatRef<'_>, cfg: &KsgConfig) -> PidResult<f64> {
    ksg_mi_with_budget(x, y, cfg, ResourceBudget::default())
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    validate_ksg_pair_structure("ksg_mi", x, y, cfg)?;
    let local = ksg_local_mi_terms_with_budget(x, y, cfg, budget)?;
    let mi = compensated_sum(local.iter().copied()) / (local.len() as f64);
    Ok(match cfg.negative_handling {
        NegativeHandling::Allow => mi,
        NegativeHandling::ClampToZero => mi.max(0.0),
    })
}

/// Returns the per-sample local MI contributions whose average is the **unclamped** KSG MI
/// estimate (i.e. [`ksg_mi`] configured with [`NegativeHandling::Allow`]).
///
/// local_i = ψ(k) + ψ(n) - ψ(n_x(i)+1) - ψ(n_y(i)+1)
///
/// If [`ksg_mi`] is explicitly configured with [`NegativeHandling::ClampToZero`], low-MI data can
/// have a local-term mean slightly below the floored value that [`ksg_mi`] reports. The default
/// [`NegativeHandling::Allow`] returns this signed mean unchanged.
///
/// This is useful for building shared-exclusions estimators based on pointwise terms.
#[cfg(feature = "experimental-continuous")]
pub(crate) fn ksg_local_mi_terms(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<Vec<f64>> {
    ksg_local_mi_terms_with_budget(x, y, cfg, ResourceBudget::default())
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_local_mi_terms_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    validate_ksg_pair_structure("ksg_local_mi_terms", x, y, cfg)?;
    ksg_local_mi_terms_backend_with_budget(x, y, cfg, NnBackend::Auto, budget)
}

#[cfg(any(feature = "experimental-continuous", test))]
#[cfg(test)]
pub(crate) fn ksg_local_mi_terms_backend(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    backend: NnBackend,
) -> PidResult<Vec<f64>> {
    ksg_local_mi_terms_backend_with_budget(x, y, cfg, backend, ResourceBudget::default())
}

#[cfg(any(feature = "experimental-continuous", test))]
fn ksg_local_mi_terms_backend_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    backend: NnBackend,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    let threads = effective_thread_count(budget.max_threads, x.nrows());
    let diagnostics = with_thread_budget(threads, || {
        ksg_local_diagnostics_backend(x, y, cfg, backend, budget)
    })?;
    let mut terms = try_vec_with_capacity("ksg local MI terms", diagnostics.len(), budget)?;
    terms.extend(
        diagnostics
            .into_iter()
            .map(|diagnostic| diagnostic.term_nats),
    );
    Ok(terms)
}

#[cfg(any(feature = "experimental-continuous", test))]
fn ksg_local_diagnostics_backend(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    backend: NnBackend,
    resource_budget: ResourceBudget,
) -> PidResult<Vec<KsgLocalDiagnostic>> {
    let cancellation = CancellationToken::new();
    let kernel_config = KernelKsgConfig::stable(cfg);
    ksg_local_diagnostics_backend_with_kernel_and_cancellation(
        x,
        y,
        &kernel_config,
        backend,
        resource_budget,
        &cancellation,
    )
}

fn ksg_local_diagnostics_backend_with_kernel_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KernelKsgConfig,
    backend: NnBackend,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<KsgLocalDiagnostic>> {
    validate_ksg_pair_structure_with_kernel("ksg_local_mi_terms", x, y, cfg)?;
    let n = x.nrows();
    let k = cfg.k;
    let joint_dims = x
        .ncols()
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms",
        })?;
    let threads = effective_thread_count(resource_budget.max_threads, n);
    resource_budget.check(
        "ksg_local_mi_terms",
        ksg_resource_estimate_for_threads(x, y, threads)?,
    )?;
    match cfg.kernel_support_mode {
        KernelSupportMode::Stable => {
            validate_observed_sample_conditions_with_budget_and_cancellation(
                "ksg_local_mi_terms",
                cfg.support_contract,
                &[x, y],
                resource_budget,
                cancellation,
            )?;
        }
        #[cfg(feature = "experimental-hyperbolic")]
        KernelSupportMode::SmoothManifold => {
            validate_smooth_manifold_sample_conditions_with_budget_and_cancellation(
                "ksg_local_mi_terms",
                &[x, y],
                resource_budget,
                cancellation,
            )?;
        }
    }
    cancellation.check("ksg_local_mi_terms", 0, n)?;

    let shifted_harmonics = shifted_harmonic_table(n)?;

    // Typically faster exact Chebyshev kd-tree path (kdtree.rs) — identical
    // outputs to the brute scan (same distance fold, same total_cmp k-th
    // value, same inclusive counts on the strict radius). Queries remain
    // linear in the worst case. A selected tree backend never silently falls back to an
    // unbounded brute-force job: build failure is returned to the caller.
    if backend.use_tree(cfg.kernel_metric, n, joint_dims) {
        let joint =
            KdTree::build_with_budget_and_cancellation(&[x, y], resource_budget, cancellation)?;
        let tx = KdTree::build_with_budget_and_cancellation(&[x], resource_budget, cancellation)?;
        let ty = KdTree::build_with_budget_and_cancellation(&[y], resource_budget, cancellation)?;
        return map_index_ordered(n, |i| {
            cancellation.check("ksg_local_mi_terms", i, n)?;
            let mut q = try_vec_with_capacity(
                "ksg_local_mi_terms joint query",
                joint_dims,
                ResourceBudget::default(),
            )?;
            concat_row_into(&[x, y], i, &mut q);
            let eps_raw = joint.kth_distance_with_cancellation(&q, k, i as u32, cancellation)?;
            if eps_raw == 0.0 {
                return Err(PidError::NumericalInstability {
                    context: "ksg_local_mi_terms: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
                });
            }
            let (interior_count, boundary_count) = joint
                .kth_neighbor_shell_counts_with_cancellation(&q, eps_raw, i as u32, cancellation)?;
            validate_kth_neighbor_shell(
                "ksg_local_mi_terms",
                i,
                k,
                eps_raw,
                interior_count,
                boundary_count,
            )?;
            let eps = strict_radius(eps_raw);
            let nx = tx.count_within_with_cancellation(x.row(i), eps, i as u32, cancellation)?;
            let ny = ty.count_within_with_cancellation(y.row(i), eps, i as u32, cancellation)?;
            Ok(KsgLocalDiagnostic {
                term_nats: ksg_local_harmonic_term(&shifted_harmonics, k, n, nx + 1, ny + 1),
                joint_radius: eps_raw,
                x_count: nx,
                y_count: ny,
            })
        });
    }

    map_index_ordered(n, |i| {
        cancellation.check("ksg_local_mi_terms", i, n)?;
        let mut scratch = try_vec_with_capacity(
            "ksg_local_mi_terms distance scratch",
            n.saturating_sub(1),
            ResourceBudget::default(),
        )?;
        let xi = x.row(i);
        let yi = y.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            let dx = cfg.kernel_metric.checked_distance_with_cancellation(
                xi,
                x.row(j),
                "ksg_local_mi_terms: x distance",
                CancellationProgress::new("ksg_local_mi_terms", i, n),
                cancellation,
            )?;
            let dy = cfg.kernel_metric.checked_distance_with_cancellation(
                yi,
                y.row(j),
                "ksg_local_mi_terms: y distance",
                CancellationProgress::new("ksg_local_mi_terms", i, n),
                cancellation,
            )?;
            scratch.push(DistPair {
                joint: dx.max(dy),
                dx,
                dy,
            });
            if j.is_multiple_of(1024) {
                cancellation.check("ksg_local_mi_terms", i, n)?;
            }
        }

        let kth = k - 1;
        cancellation.check("ksg_local_mi_terms", i, n)?;
        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        cancellation.check("ksg_local_mi_terms", i, n)?;
        let eps_raw = scratch[kth].joint;
        // Strict inequality for marginal counts.
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "ksg_local_mi_terms: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(
            "ksg_local_mi_terms",
            i,
            k,
            eps_raw,
            interior_count,
            boundary_count,
        )?;
        let eps = strict_radius(eps_raw);

        let mut nx = 0usize;
        let mut ny = 0usize;
        for d in &scratch {
            if d.dx <= eps {
                nx += 1;
            }
            if d.dy <= eps {
                ny += 1;
            }
        }

        Ok(KsgLocalDiagnostic {
            term_nats: ksg_local_harmonic_term(&shifted_harmonics, k, n, nx + 1, ny + 1),
            joint_radius: eps_raw,
            x_count: nx,
            y_count: ny,
        })
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
fn validate_ksg_pair_structure(
    context: &'static str,
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<()> {
    let kernel_config = KernelKsgConfig::stable(cfg);
    validate_ksg_pair_structure_with_kernel(context, x, y, &kernel_config)
}

fn validate_ksg_pair_structure_with_kernel(
    context: &'static str,
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KernelKsgConfig,
) -> PidResult<()> {
    if x.nrows() != y.nrows() {
        return Err(PidError::RowCountMismatch {
            context,
            left_rows: x.nrows(),
            right_rows: y.nrows(),
        });
    }
    if x.ncols() == 0 || y.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "x and y must have at least 1 column",
        });
    }
    #[cfg(feature = "experimental-hyperbolic")]
    if cfg.kernel_metric.is_hyperbolic() && (x.ncols() < 2 || y.ncols() < 2) {
        return Err(PidError::InvalidConfig {
            context,
            message: "Lorentz-hyperboloid inputs must each have row width d+1 >= 2",
        });
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }
    let n = x.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }
    match cfg.kernel_support_mode {
        KernelSupportMode::Stable => {
            validate_support_contract(context, cfg.support_contract, cfg.metric)
        }
        #[cfg(feature = "experimental-hyperbolic")]
        KernelSupportMode::SmoothManifold => Ok(()),
    }
}

/// KSG local MI terms when the "X" variable is treated as a concatenation of multiple blocks.
///
/// With `Metric::Chebyshev`, treating the concatenation as a max-over-blocks distance is
/// equivalent to explicitly concatenating the vectors, but avoids allocating an `(n×(d1+d2+...))`
/// temporary matrix.
#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_xblocks_resource_estimate(
    x_blocks: &[MatRef<'_>],
    y: MatRef<'_>,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    let x_dims = x_blocks.iter().try_fold(0usize, |total, block| {
        total
            .checked_add(block.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_local_mi_terms_xblocks",
            })
    })?;
    let joint_dims = x_dims
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    let n = y.nrows();
    let pairs = (n as u128)
        .checked_mul(n.saturating_sub(1) as u128)
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    let base_bytes = (n as u128)
        .checked_mul(
            (joint_dims as u128)
                .checked_mul(4)
                .and_then(|value| value.checked_add(64))
                .ok_or(PidError::SizeOverflow {
                    operation: "ksg_local_mi_terms_xblocks",
                })?,
        )
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    let log_n = if n <= 1 {
        1u128
    } else {
        (usize::BITS - (n - 1).leading_zeros()) as u128
    };
    let support_peak_bytes = (n as u128)
        .checked_mul(joint_dims as u128)
        .and_then(|value| value.checked_mul(2 * std::mem::size_of::<u64>() as u128))
        .and_then(|value| {
            value.checked_add((n as u128).checked_mul(std::mem::size_of::<Vec<u64>>() as u128)?)
        })
        .and_then(|value| {
            value.checked_add(
                (joint_dims as u128)
                    .checked_mul(std::mem::size_of::<CoordinateCardinalityDiagnostics>() as u128)?,
            )
        })
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    #[cfg(feature = "parallel")]
    let parallel_bytes = {
        let threads = effective_thread_count(max_threads, n) as u128;
        threads
            .checked_mul(WORKER_STACK_BYTES as u128)
            .and_then(|value| {
                value.checked_add(
                    threads
                        .checked_mul(n as u128)?
                        .checked_mul(std::mem::size_of::<DistPair>() as u128)?,
                )
            })
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_local_mi_terms_xblocks",
            })?
    };
    #[cfg(not(feature = "parallel"))]
    let parallel_bytes = {
        // Thread requests are semantically inert in serial builds, but retaining the parameter
        // keeps the preflight API identical across feature sets.
        let _ = max_threads;
        0
    };
    let operations_hint = pairs
        .checked_mul(joint_dims as u128)
        .and_then(|value| value.checked_mul(6))
        .and_then(|value| {
            value.checked_add(
                (n as u128)
                    .checked_mul(joint_dims as u128)?
                    .checked_mul(log_n)?
                    .checked_mul(2)?,
            )
        })
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: base_bytes
            .checked_add(parallel_bytes)
            .map(|value| value.max(support_peak_bytes))
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_local_mi_terms_xblocks",
            })?,
        pairwise_distances: pairs,
        operations_hint,
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_local_mi_terms_xblocks_with_budget<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    let threads = effective_thread_count(budget.max_threads, y.nrows());
    with_thread_budget(threads, || {
        ksg_local_mi_terms_xblocks_backend_with_budget(x_blocks, y, cfg, NnBackend::Auto, budget)
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
#[cfg(test)]
pub(crate) fn ksg_local_mi_terms_xblocks_backend<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
    backend: NnBackend,
) -> PidResult<Vec<f64>> {
    ksg_local_mi_terms_xblocks_backend_with_budget(
        x_blocks,
        y,
        cfg,
        backend,
        ResourceBudget::default(),
    )
}

#[cfg(any(feature = "experimental-continuous", test))]
fn ksg_local_mi_terms_xblocks_backend_with_budget<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
    backend: NnBackend,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    if x_blocks.is_empty() {
        return Err(PidError::NotImplemented {
            feature: "ksg_local_mi_terms_xblocks with empty x_blocks",
        });
    }
    if y.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "y must have at least 1 column",
        });
    }
    let n = y.nrows();
    for b in x_blocks {
        if b.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: "ksg_local_mi_terms_xblocks",
                left_rows: n,
                right_rows: b.nrows(),
            });
        }
        if b.ncols() == 0 {
            return Err(PidError::InvalidConfig {
                context: "ksg_local_mi_terms_xblocks",
                message: "x blocks must have at least 1 column",
            });
        }
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }

    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }
    // The max-over-blocks distance equals true concatenation only under L∞/Chebyshev
    // (max(max_b d_b, d_y) == d over the concatenated vector). For any other metric it
    // silently computes a *different* quantity, so reject it rather than mislabel the
    // result — matching the gating in `isx_redundancy` and `pid3_isx`.
    if cfg.metric != Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "max-over-blocks concatenation distance is exact only for Metric::Chebyshev (L∞); other metrics are research-gated",
        });
    }
    let x_dims = x_blocks.iter().try_fold(0usize, |total, block| {
        total
            .checked_add(block.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_local_mi_terms_xblocks",
            })
    })?;
    let joint_dims = x_dims
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    budget.check(
        "ksg_local_mi_terms_xblocks",
        ksg_xblocks_resource_estimate(x_blocks, y, budget.max_threads)?,
    )?;
    validate_support_contract(
        "ksg_local_mi_terms_xblocks",
        cfg.support_contract,
        cfg.metric,
    )?;
    let block_count = x_blocks
        .len()
        .checked_add(1)
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    let mut support_inputs = try_vec_with_capacity(
        "ksg_local_mi_terms_xblocks support inputs",
        block_count,
        budget,
    )?;
    support_inputs.extend_from_slice(x_blocks);
    support_inputs.push(y);
    validate_observed_sample_conditions_with_budget(
        "ksg_local_mi_terms_xblocks",
        cfg.support_contract,
        &support_inputs,
        budget,
    )?;

    let shifted_harmonics = shifted_harmonic_table(n)?;

    // Typically faster exact tree path (see ksg_local_mi_terms_backend). The
    // metric is already gated to Chebyshev above, where max-over-blocks equals
    // the concatenated-space distance. Worst-case queries are still linear.
    if backend.use_tree(cfg.metric.into(), n, joint_dims) {
        let mut joint_blocks = try_vec_with_capacity(
            "ksg_local_mi_terms_xblocks tree blocks",
            block_count,
            budget,
        )?;
        joint_blocks.extend_from_slice(x_blocks);
        joint_blocks.push(y);
        let joint = KdTree::build_with_budget(&joint_blocks, budget)?;
        let tx = KdTree::build_with_budget(x_blocks, budget)?;
        let ty = KdTree::build_with_budget(&[y], budget)?;
        return map_index_ordered(n, |i| {
            let mut q = try_vec_with_capacity(
                "ksg_local_mi_terms_xblocks joint query",
                joint_dims,
                budget,
            )?;
            concat_row_into(&joint_blocks, i, &mut q);
            let eps_raw = joint.kth_distance(&q, k, i as u32)?;
            if eps_raw == 0.0 {
                return Err(PidError::NumericalInstability {
                        context: "ksg_local_mi_terms_xblocks: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
                    });
            }
            let (interior_count, boundary_count) =
                joint.kth_neighbor_shell_counts(&q, eps_raw, i as u32);
            validate_kth_neighbor_shell(
                "ksg_local_mi_terms_xblocks",
                i,
                k,
                eps_raw,
                interior_count,
                boundary_count,
            )?;
            let eps = strict_radius(eps_raw);
            let mut qx =
                try_vec_with_capacity("ksg_local_mi_terms_xblocks source query", x_dims, budget)?;
            concat_row_into(x_blocks, i, &mut qx);
            let nx = tx.count_within(&qx, eps, i as u32);
            let ny = ty.count_within(y.row(i), eps, i as u32);
            Ok(ksg_local_harmonic_term(
                &shifted_harmonics,
                k,
                n,
                nx + 1,
                ny + 1,
            ))
        });
    }

    map_index_ordered(n, |i| {
        let mut scratch = try_vec_with_capacity(
            "ksg_local_mi_terms_xblocks distance scratch",
            n.saturating_sub(1),
            budget,
        )?;
        let mut x_rows_i = try_vec_with_capacity(
            "ksg_local_mi_terms_xblocks source rows",
            x_blocks.len(),
            budget,
        )?;
        for b in x_blocks {
            x_rows_i.push(b.row(i));
        }
        let yi = y.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            let mut dx = 0.0f64;
            for (b_idx, b) in x_blocks.iter().enumerate() {
                dx = dx.max(cfg.metric.checked_distance(
                    x_rows_i[b_idx],
                    b.row(j),
                    "ksg_local_mi_terms_xblocks: x distance",
                )?);
            }
            let dy = cfg.metric.checked_distance(
                yi,
                y.row(j),
                "ksg_local_mi_terms_xblocks: y distance",
            )?;
            scratch.push(DistPair {
                joint: dx.max(dy),
                dx,
                dy,
            });
        }

        let kth = k - 1;
        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps_raw = scratch[kth].joint;
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "ksg_local_mi_terms_xblocks: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(
            "ksg_local_mi_terms_xblocks",
            i,
            k,
            eps_raw,
            interior_count,
            boundary_count,
        )?;
        let eps = strict_radius(eps_raw);

        let mut nx = 0usize;
        let mut ny = 0usize;
        for d in &scratch {
            if d.dx <= eps {
                nx += 1;
            }
            if d.dy <= eps {
                ny += 1;
            }
        }

        Ok(ksg_local_harmonic_term(
            &shifted_harmonics,
            k,
            n,
            nx + 1,
            ny + 1,
        ))
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi_xblocks_with_budget<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    let local = ksg_local_mi_terms_xblocks_with_budget(x_blocks, y, cfg, budget)?;
    let mi = compensated_sum(local.iter().copied()) / (local.len() as f64);
    Ok(match cfg.negative_handling {
        NegativeHandling::Allow => mi,
        NegativeHandling::ClampToZero => mi.max(0.0),
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi_concat_xy(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<f64> {
    ksg_mi_concat_xy_with_budget(x, y, t, cfg, ResourceBudget::default())
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi_concat_xy_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    ksg_mi_xblocks_with_budget(&[x, y], t, cfg, budget)
}

#[cfg(test)]
mod tests {
    use super::{ksg_local_diagnostics_backend, ksg_mi, ksg_mi_concat_xy, KsgConfig, NnBackend};
    use crate::matrix::{concat_horiz, MatRef};
    use crate::resource::ResourceBudget;

    #[test]
    fn ksg_ordered_count_witness_reaches_production_diagnostics() {
        let x = [7.0, 194.0, 144.0, 75.0, 61.0, 138.0, 38.0, 9.0];
        let y = [17.0, 48.0, 166.0, 120.0, 2.0, 199.0, 43.0, 93.0];
        let x = MatRef::new(&x, 8, 1).unwrap();
        let y = MatRef::new(&y, 8, 1).unwrap();
        let config = KsgConfig::assume_regular_full_dimensional().with_k(2);

        for backend in [NnBackend::Brute, NnBackend::KdTree] {
            let diagnostics =
                ksg_local_diagnostics_backend(x, y, &config, backend, ResourceBudget::default())
                    .unwrap();
            let row = diagnostics[5];
            assert_eq!(row.joint_radius.to_bits(), 79.0_f64.to_bits());
            assert_eq!((row.x_count, row.y_count), (4, 1));
            assert_eq!(row.term_nats.to_bits(), 0x3fe0_4e04_e04e_04e0);
        }
    }

    #[test]
    fn concat_xy_matches_explicit_concatenation_for_chebyshev() {
        // For Chebyshev/L∞, computing distance as max-over-blocks is equivalent to explicit
        // concatenation. This test guards the allocation-avoidance optimization.
        let n = 40;
        let d1 = 3;
        let d2 = 2;
        let dt = 1;

        let mut state = 0xC011_CAFE_D15C_A11Eu64;
        let mut next = || {
            state ^= state >> 12;
            state ^= state << 25;
            state ^= state >> 27;
            (state.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1u64 << 53) as f64
        };
        let mut x = Vec::with_capacity(n * d1);
        let mut y = Vec::with_capacity(n * d2);
        let mut t = Vec::with_capacity(n * dt);
        for _ in 0..n {
            for _ in 0..d1 {
                x.push(next());
            }
            for _ in 0..d2 {
                y.push(next());
            }
            t.push(next());
        }

        let x = MatRef::new(&x, n, d1).unwrap();
        let y = MatRef::new(&y, n, d2).unwrap();
        let t = MatRef::new(&t, n, dt).unwrap();
        let cfg = KsgConfig::assume_regular_full_dimensional();

        let mi_blocks = ksg_mi_concat_xy(x, y, t, &cfg).unwrap();
        let xy = concat_horiz(x, y).unwrap();
        let mi_explicit = ksg_mi(xy.as_ref(), t, &cfg).unwrap();

        assert!(
            (mi_blocks - mi_explicit).abs() < 1e-12,
            "mi_blocks={mi_blocks} mi_explicit={mi_explicit}"
        );
    }
}

#[cfg(test)]
mod kdtree_parity_tests {
    use super::*;
    use crate::error::PidError;
    use crate::matrix::MatOwned;

    struct Rng(u64);
    impl Rng {
        fn next_f64(&mut self) -> f64 {
            let mut x = self.0;
            x ^= x >> 12;
            x ^= x << 25;
            x ^= x >> 27;
            self.0 = x;
            (x.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1u64 << 53) as f64
        }
    }

    fn mat(rng: &mut Rng, n: usize, d: usize, quantize: bool) -> MatOwned {
        let mut data = Vec::with_capacity(n * d);
        for _ in 0..n * d {
            let v = rng.next_f64();
            data.push(if quantize {
                (v * 16.0).round() / 16.0
            } else {
                v
            });
        }
        MatOwned::new(data, n, d).unwrap()
    }

    fn cfg(k: usize) -> KsgConfig {
        KsgConfig {
            k,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            negative_handling: NegativeHandling::Allow,
            support_contract: crate::support::SupportContract::AssumeRegularFullDimensional {
                boundary: crate::support::BoundaryModel::Unknown,
                density_regular: true,
                finite_information: true,
            },
        }
    }

    fn shell_error_signature(
        result: PidResult<Vec<f64>>,
    ) -> (&'static str, usize, usize, u64, usize, usize) {
        match result.unwrap_err() {
            PidError::AmbiguousKthNeighborShell {
                context,
                query_index,
                k,
                radius,
                interior_count,
                boundary_count,
            } => (
                context,
                query_index,
                k,
                radius.to_bits(),
                interior_count,
                boundary_count,
            ),
            error => panic!("expected ambiguous k-th-neighbor shell, got {error:?}"),
        }
    }

    #[test]
    fn local_mi_terms_tree_is_bit_identical_to_brute() {
        // Below and above the Auto threshold; smooth and tie-heavy data.
        for (n, dx, dy, k, quantize) in [
            (64, 1, 1, 4, false),
            (300, 1, 1, 4, false),
            (300, 2, 1, 3, true),
            (200, 3, 2, 7, true),
        ] {
            let mut rng = Rng(0x5EED ^ ((n as u64) << 16) ^ ((dx as u64) << 8) ^ k as u64);
            let x = mat(&mut rng, n, dx, quantize);
            let y = mat(&mut rng, n, dy, quantize);
            let c = cfg(k);
            let brute = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute);
            let tree = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree);
            match (brute, tree) {
                (Ok(b), Ok(t)) => {
                    assert_eq!(b.len(), t.len());
                    for (i, (bb, tt)) in b.iter().zip(&t).enumerate() {
                        assert_eq!(
                            bb.to_bits(),
                            tt.to_bits(),
                            "term {i} differs (n={n} dx={dx} dy={dy} k={k} q={quantize})"
                        );
                    }
                }
                // Tie-heavy data may legitimately collapse the radius: both
                // paths must then fail identically.
                (Err(_), Err(_)) => {}
                (b, t) => panic!("backend disagreement: brute={b:?} tree={t:?}"),
            }
        }
    }

    #[test]
    fn xblocks_tree_is_bit_identical_to_brute() {
        let mut rng = Rng(0xB10C5);
        let n = 260;
        let x1 = mat(&mut rng, n, 2, false);
        let x2 = mat(&mut rng, n, 1, false);
        let y = mat(&mut rng, n, 1, false);
        let c = cfg(4);
        let blocks = [x1.as_ref(), x2.as_ref()];
        let brute =
            ksg_local_mi_terms_xblocks_backend(&blocks, y.as_ref(), &c, NnBackend::Brute).unwrap();
        let tree =
            ksg_local_mi_terms_xblocks_backend(&blocks, y.as_ref(), &c, NnBackend::KdTree).unwrap();
        for (i, (bb, tt)) in brute.iter().zip(&tree).enumerate() {
            assert_eq!(bb.to_bits(), tt.to_bits(), "xblocks term {i} differs");
        }
    }

    #[test]
    fn positive_outer_shell_tie_errors_identically_on_both_backends() {
        // Every joint row is distinct. At query 0 and k=2 the positive distances are
        // [0.5, 1, 1, 3], so the outer shell contains two points.
        let x = MatOwned::new(vec![0.0, 0.5, 1.0, 0.3, 3.0], 5, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 0.4, 0.2, 1.0, 3.0], 5, 1).unwrap();
        let c = cfg(2);
        let brute = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::Brute,
        ));
        let tree = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::KdTree,
        ));
        let expected = ("ksg_local_mi_terms", 0, 2, 1.0f64.to_bits(), 1, 2);

        assert_eq!([brute, tree], [expected, expected]);
    }

    #[test]
    fn positive_left_shell_tie_errors_identically_on_both_backends() {
        // Every joint row is distinct. At query 0 and k=2 the positive distances are
        // [1, 1, 2], so fewer than k-1 points lie strictly inside the selected radius.
        let x = MatOwned::new(vec![0.0, 1.0, 0.3, 2.0], 4, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 0.2, 1.0, 2.0], 4, 1).unwrap();
        let c = cfg(2);
        let brute = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::Brute,
        ));
        let tree = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::KdTree,
        ));
        let expected = ("ksg_local_mi_terms", 0, 2, 1.0f64.to_bits(), 0, 2);

        assert_eq!([brute, tree], [expected, expected]);
    }

    #[test]
    fn xblocks_positive_shell_tie_errors_identically_on_both_backends() {
        let x1 = MatOwned::new(vec![0.0, 0.5, 1.0, 0.3, 3.0], 5, 1).unwrap();
        let x2 = MatOwned::new(vec![0.0, 0.25, 0.75, 0.35, 2.5], 5, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 0.4, 0.2, 1.0, 3.0], 5, 1).unwrap();
        let blocks = [x1.as_ref(), x2.as_ref()];
        let c = cfg(2);
        let brute = shell_error_signature(ksg_local_mi_terms_xblocks_backend(
            &blocks,
            y.as_ref(),
            &c,
            NnBackend::Brute,
        ));
        let tree = shell_error_signature(ksg_local_mi_terms_xblocks_backend(
            &blocks,
            y.as_ref(),
            &c,
            NnBackend::KdTree,
        ));
        let expected = ("ksg_local_mi_terms_xblocks", 0, 2, 1.0f64.to_bits(), 1, 2);

        assert_eq!([brute, tree], [expected, expected]);
    }

    #[test]
    fn duplicate_rows_error_identically_on_both_backends() {
        // All-identical rows collapse every kNN radius; both backends must
        // fail (radius guard), not silently disagree.
        let n = 150;
        let x = MatOwned::new(vec![0.25; n], n, 1).unwrap();
        let y = MatOwned::new(vec![0.75; n], n, 1).unwrap();
        let c = cfg(3);
        assert!(ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute).is_err());
        assert!(ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree).is_err());
    }

    #[test]
    fn overflowing_coordinate_span_errors_identically_on_both_backends() {
        let x = MatOwned::new(vec![-f64::MAX, f64::MAX, 0.0, 1.0], 4, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let c = cfg(1);

        let brute = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute);
        let tree = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree);

        assert!(brute.is_err());
        assert!(tree.is_err());
    }

    #[test]
    #[ignore = "manual benchmark: cargo test -p pid-core --release kdtree_speedup -- --ignored --nocapture"]
    fn kdtree_speedup_smoke() {
        let mut rng = Rng(0xBEEF);
        let n = 4000;
        let x = mat(&mut rng, n, 1, false);
        let y = mat(&mut rng, n, 1, false);
        let c = cfg(4);
        let t0 = std::time::Instant::now();
        let brute =
            ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute).unwrap();
        let t_brute = t0.elapsed();
        let t1 = std::time::Instant::now();
        let tree =
            ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree).unwrap();
        let t_tree = t1.elapsed();
        assert_eq!(brute.len(), tree.len());
        println!(
            "n={n}: brute {t_brute:?} vs kd-tree {t_tree:?} ({:.1}x)",
            t_brute.as_secs_f64() / t_tree.as_secs_f64()
        );
    }
}
```

## Artifact: `crates/pid-core/src/isx.rs`

SHA-256: `ad2bf59da32433f866313d339889084050bff21e0b672589019260df8ff690d5`

```text
//! Continuous shared-exclusions redundancy estimators and explicitly labelled baselines.
//!
//! # Method provenance and availability
//!
//! **PAPER-DEFINED.** `IsxMethod::EhrlichKsg` implements the continuous two-source estimator of
//! Ehrlich et al. (2024) within its restricted equal-ambient-source-dimension,
//! source-gauge-sensitive, regular-support domain. The report-first API adds project-defined
//! provenance and diagnostic contracts. It is available under `experimental-continuous`.
//!
//! Method catalog: shared-exclusions.continuous-report
//!
//! **PAPER-DEFINED CORE, RESEARCH API.** Raw redundancy functions expose the same estimator without
//! the report contract under `experimental-continuous`; they are not a separate method.
//!
//! Method catalog: shared-exclusions.continuous-raw
//!
//! **PROJECT-DEFINED BASELINES.** The `experimental-heuristics` variants are formula-labelled
//! comparison sketches. They do not implement or estimate the Ehrlich et al. shared-exclusions
//! functional, and no paper-defined validity claim is attached to them.
//!
//! Method catalog: shared-exclusions.continuous-heuristics
//!
//! **EXTERNAL REFERENCE CODE.** A pinned BSD-3-Clause `csxpid` revision is used for bounded
//! reference-fixture comparisons. It is not embedded in the library, does not define the
//! estimator, and does not turn heuristic baselines into implementations of the cited estimator.
//!
//! Method catalog: validation.csxpid-reference-code

use serde::Serialize;

use crate::error::{PidError, PidResult};
use crate::ksg::{
    count_quantiles, effective_thread_count, hash_matrix, hash_text, value_quantiles,
    KsgCountQuantiles, KsgValueQuantiles,
};
#[cfg(feature = "experimental-heuristics")]
use crate::ksg::{
    ksg_local_mi_terms_with_budget, ksg_local_mi_terms_xblocks_with_budget, KsgConfig,
    NegativeHandling,
};
use crate::matrix::MatRef;
use crate::metric::Metric;
#[cfg(feature = "experimental-heuristics")]
use crate::nn::{count_neighbors_within, kth_neighbor_distance_joint_max_with_scratch};
use crate::nn::{kth_neighbor_shell_counts, strict_radius, validate_kth_neighbor_shell};
#[cfg(feature = "parallel")]
use crate::par::WORKER_STACK_BYTES;
use crate::report::{
    Assumption, AssumptionLedgerEntry, AssumptionState, EstimandIdentity, InformationUnit,
    ProvenanceHashes, ScientificStatus, WarningCode,
};
#[cfg(feature = "experimental-heuristics")]
use crate::resource::try_vec_filled;
use crate::resource::{try_vec_with_capacity, ResourceBudget, ResourceEstimate};
use crate::stats::{compensated_sum, ksg_local_harmonic_term, shifted_harmonic_table};
#[cfg(feature = "experimental-heuristics")]
use crate::stats::{digamma, digamma_int_table};
use crate::support::{
    validate_observed_sample_conditions_with_budget, validate_support_contract,
    CoordinateCardinalityDiagnostics, SupportContract,
};

#[derive(Clone, Copy)]
struct DistIsx2 {
    joint: f64,
    dt: f64,
    ds: f64,
    ds1: f64,
    ds2: f64,
}

#[derive(Clone, Copy)]
pub(crate) struct IsxLocalDiagnostic {
    pub(crate) term_nats: f64,
    joint_radius: f64,
    source_union_count: usize,
    target_count: usize,
    source1_count: usize,
    source2_count: usize,
    overlap_count: usize,
    source1_half_count: usize,
    source2_half_count: usize,
    overlap_half_count: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum IsxMethod {
    /// KSG-style kNN estimator for continuous shared-exclusions redundancy described by:
    /// Ehrlich et al. (2024), Phys. Rev. E 110, 014115 (arXiv:2311.06373v3).
    ///
    /// Implements the bivariate redundancy `I^sx_∩(S1,S2;T)` via the KSG-style estimator
    /// (Appendix H, Algorithms 3–6) under the L∞/Chebyshev metric:
    ///
    /// I^sx_∩ = ψ(k) + ψ(n) - ⟨ ψ(n_α(i)) + ψ(n_T(i)) ⟩_i
    ///
    /// where:
    /// - ε_i is the kNN radius in the joint (source-disjunction, target) space,
    /// - n_α(i) counts neighbors in the *source disjunction* within ε_i,
    /// - n_T(i) counts neighbors in target space within ε_i.
    ///
    /// Note: This is the default method for `IsxConfig`.
    EhrlichKsg,
    /// Experimental heuristic sketch estimator.
    ///
    /// Provided as an explicit, clearly-labelled research baseline only. Synthetic checks can
    /// characterize bounded cases but do not make it an estimator of the cited functional.
    #[cfg(feature = "experimental-heuristics")]
    HeuristicSketch,
    /// Approximate shared-exclusions redundancy by taking the samplewise minimum
    /// of KSG local MI terms for (S1,T) and (S2,T), then averaging.
    #[cfg(feature = "experimental-heuristics")]
    LocalMinKsg,
    /// Experimental **unweighted inclusion–exclusion heuristic** over pointwise KSG local-MI
    /// terms:
    ///
    /// r(s1,s2;t) = log( exp(i(s1;t)) + exp(i(s2;t)) - exp(i(s1,s2;t)) )
    ///
    /// **This is NOT the shared-exclusions disjunction identity.** The true forms are:
    /// - discrete (Makkeh–Gutknecht–Wibral 2021):
    ///   `i^sx = log[(p(s1)e^{i1} + p(s2)e^{i2} − p(s1,s2)e^{i12}) / (p(s1)+p(s2)−p(s1,s2))]`
    ///   (probability-weighted);
    /// - Ehrlich et al.'s continuous functional under its declared relative source gauge
    ///   (2024, Def. 2; evaluated for matched standard-normal marginals and a common partition in
    ///   `tests/sxpid_gaussian_oracle.rs`):
    ///   `i^sx = log[w1·e^{i1} + w2·e^{i2}]` with density weights
    ///   `w_a = f_{S_a}(s_a) / (f_{S1}(s1) + f_{S2}(s2))` and **no** joint term (the discrete
    ///   joint-term weight `p(s1,s2)` vanishes under that refining-partition construction).
    ///
    /// This variant sets all weights to 1 and retains a full-weight joint term, so it estimates
    /// a *different* functional and does not converge to `I^sx_∩` as estimation error → 0; its
    /// log argument can also be non-positive (surfacing as `NumericalInstability`), whereas the
    /// true `i^sx` argument `P(∪|t)/P(∪)` is always positive. Baseline/diagnostic use only.
    #[cfg(feature = "experimental-heuristics")]
    DisjunctionFromLocalMi,
}

#[derive(Debug, Clone, Serialize)]
pub struct IsxConfig {
    pub k: usize,
    pub metric: Metric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    ///
    /// Strict counts use the floating-point predecessor of the raw kNN radius. A material
    /// subtraction would erode the neighborhood and estimate a different functional.
    pub tie_epsilon: f64,
    pub method: IsxMethod,
    /// Population-support assertion for every marginal and joint law used by this call.
    ///
    /// The default is [`SupportContract::Unspecified`] and deliberately fails closed. The current
    /// continuous shared-exclusions estimators accept only
    /// [`SupportContract::AssumeRegularFullDimensional`].
    pub support_contract: SupportContract,
}

/// Caller-declared source gauges, preprocessing, sampling, and split provenance for ISX.
#[derive(Debug, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct IsxProvenance {
    source1_gauge_description: String,
    source2_gauge_description: String,
    target_preprocessing_description: String,
    observation_model_description: String,
    sampling_model_description: Option<String>,
    training_split_id: Option<String>,
    evaluation_split_id: Option<String>,
}

impl IsxProvenance {
    pub fn new(
        source1_gauge_description: impl AsRef<str>,
        source2_gauge_description: impl AsRef<str>,
        target_preprocessing_description: impl AsRef<str>,
        observation_model_description: impl AsRef<str>,
        sampling_model_description: impl AsRef<str>,
        training_split_id: Option<String>,
        evaluation_split_id: Option<String>,
    ) -> PidResult<Self> {
        let source1_gauge_description = source1_gauge_description.as_ref();
        let source2_gauge_description = source2_gauge_description.as_ref();
        let target_preprocessing_description = target_preprocessing_description.as_ref();
        let observation_model_description = observation_model_description.as_ref();
        let sampling_model_description = sampling_model_description.as_ref();
        for value in [
            source1_gauge_description,
            source2_gauge_description,
            target_preprocessing_description,
            observation_model_description,
            sampling_model_description,
        ] {
            if value.trim().is_empty() || value.len() > 16 * 1024 {
                return Err(PidError::InvalidConfig {
                    context: "IsxProvenance::new",
                    message: "provenance descriptions must be nonempty and at most 16 KiB",
                });
            }
        }
        for value in [training_split_id.as_deref(), evaluation_split_id.as_deref()]
            .into_iter()
            .flatten()
        {
            if value.is_empty() || value.len() > 16 * 1024 {
                return Err(PidError::InvalidConfig {
                    context: "IsxProvenance::new",
                    message: "split identifiers must be nonempty and at most 16 KiB",
                });
            }
        }
        Ok(Self {
            source1_gauge_description: try_owned_text(
                "IsxProvenance::new source1 gauge",
                source1_gauge_description,
            )?,
            source2_gauge_description: try_owned_text(
                "IsxProvenance::new source2 gauge",
                source2_gauge_description,
            )?,
            target_preprocessing_description: try_owned_text(
                "IsxProvenance::new target preprocessing",
                target_preprocessing_description,
            )?,
            observation_model_description: try_owned_text(
                "IsxProvenance::new observation model",
                observation_model_description,
            )?,
            sampling_model_description: Some(try_owned_text(
                "IsxProvenance::new sampling model",
                sampling_model_description,
            )?),
            training_split_id,
            evaluation_split_id,
        })
    }

    pub fn source1_gauge_description(&self) -> &str {
        &self.source1_gauge_description
    }

    pub fn source2_gauge_description(&self) -> &str {
        &self.source2_gauge_description
    }

    pub fn target_preprocessing_description(&self) -> &str {
        &self.target_preprocessing_description
    }

    pub fn observation_model_description(&self) -> &str {
        &self.observation_model_description
    }

    pub fn sampling_model_description(&self) -> Option<&str> {
        self.sampling_model_description.as_deref()
    }

    pub fn training_split_id(&self) -> Option<&str> {
        self.training_split_id.as_deref()
    }

    pub fn evaluation_split_id(&self) -> Option<&str> {
        self.evaluation_split_id.as_deref()
    }

    fn heap_bytes(&self) -> PidResult<u128> {
        [
            Some(self.source1_gauge_description.as_str()),
            Some(self.source2_gauge_description.as_str()),
            Some(self.target_preprocessing_description.as_str()),
            Some(self.observation_model_description.as_str()),
            self.sampling_model_description.as_deref(),
            self.training_split_id.as_deref(),
            self.evaluation_split_id.as_deref(),
        ]
        .into_iter()
        .flatten()
        .try_fold(0u128, |total, value| {
            total
                .checked_add(value.len() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "ISX provenance",
                })
        })
    }

    fn try_clone_for_report(&self) -> PidResult<Self> {
        Ok(Self {
            source1_gauge_description: try_owned_text(
                "ISX report provenance",
                &self.source1_gauge_description,
            )?,
            source2_gauge_description: try_owned_text(
                "ISX report provenance",
                &self.source2_gauge_description,
            )?,
            target_preprocessing_description: try_owned_text(
                "ISX report provenance",
                &self.target_preprocessing_description,
            )?,
            observation_model_description: try_owned_text(
                "ISX report provenance",
                &self.observation_model_description,
            )?,
            sampling_model_description: self
                .sampling_model_description
                .as_deref()
                .map(|value| try_owned_text("ISX report provenance", value))
                .transpose()?,
            training_split_id: self
                .training_split_id
                .as_deref()
                .map(|value| try_owned_text("ISX report provenance", value))
                .transpose()?,
            evaluation_split_id: self
                .evaluation_split_id
                .as_deref()
                .map(|value| try_owned_text("ISX report provenance", value))
                .transpose()?,
        })
    }

    pub(crate) fn new_with_optional_sampling(
        source1_gauge_description: &str,
        source2_gauge_description: &str,
        target_preprocessing_description: &str,
        observation_model_description: &str,
        sampling_model_description: Option<&str>,
        training_split_id: Option<&str>,
        evaluation_split_id: Option<&str>,
    ) -> PidResult<Self> {
        let explicit_sampling = sampling_model_description.unwrap_or("sampling model undeclared");
        let mut provenance = Self::new(
            source1_gauge_description,
            source2_gauge_description,
            target_preprocessing_description,
            observation_model_description,
            explicit_sampling,
            training_split_id
                .map(|value| try_owned_text("ISX training split", value))
                .transpose()?,
            evaluation_split_id
                .map(|value| try_owned_text("ISX evaluation split", value))
                .transpose()?,
        )?;
        if sampling_model_description.is_none() {
            provenance.sampling_model_description = None;
        }
        Ok(provenance)
    }
}

fn try_owned_text(operation: &'static str, value: &str) -> PidResult<String> {
    let mut owned = String::new();
    owned
        .try_reserve_exact(value.len())
        .map_err(|_| PidError::AllocationFailed {
            operation,
            requested_bytes: value.len() as u128,
        })?;
    owned.push_str(value);
    Ok(owned)
}

/// Multi-scale branch/overlap and local-term summary for the ISX neighborhoods actually used.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[non_exhaustive]
pub struct IsxLocalDiagnosticsSummary {
    pub joint_radius: KsgValueQuantiles,
    pub source_union_count: KsgCountQuantiles,
    pub target_count: KsgCountQuantiles,
    pub source1_count: KsgCountQuantiles,
    pub source2_count: KsgCountQuantiles,
    pub overlap_count: KsgCountQuantiles,
    pub overlap_half_radius_count: KsgCountQuantiles,
    pub overlap_ratio: KsgValueQuantiles,
    pub overlap_half_radius_ratio: KsgValueQuantiles,
    pub source1_scaling_slope: Option<KsgValueQuantiles>,
    pub source2_scaling_slope: Option<KsgValueQuantiles>,
    pub undefined_source1_slopes: usize,
    pub undefined_source2_slopes: usize,
    pub local_redundancy_nats: KsgValueQuantiles,
}

/// Restricted-domain experimental continuous shared-exclusions report.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct IsxReport {
    pub estimate_nats: f64,
    pub n_samples: usize,
    pub k: usize,
    pub source_dimensions: [usize; 2],
    pub target_dimension: usize,
    pub estimand: EstimandIdentity,
    pub scientific_status: ScientificStatus,
    pub support_contract: SupportContract,
    pub provenance: IsxProvenance,
    pub provenance_hashes: ProvenanceHashes,
    pub assumption_ledger: Vec<AssumptionLedgerEntry>,
    pub local_diagnostics: IsxLocalDiagnosticsSummary,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
    pub warnings: Vec<WarningCode>,
}

pub(crate) struct IsxReportComputation {
    pub(crate) report: IsxReport,
    pub(crate) local: Vec<IsxLocalDiagnostic>,
}

impl Default for IsxConfig {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            method: IsxMethod::EhrlichKsg,
            support_contract: SupportContract::Unspecified,
        }
    }
}

impl IsxConfig {
    /// Construct the cited Ehrlich-KSG Chebyshev configuration with an explicit caller assertion
    /// that every required marginal and joint law is full-dimensional and absolutely continuous.
    pub fn assume_regular_full_dimensional() -> Self {
        Self {
            support_contract: SupportContract::assume_regular_full_dimensional(),
            ..Self::default()
        }
    }
}

/// Continuous shared-exclusions redundancy I^sx_∩(S1,S2;T).
///
/// This is the core Wibral-group PID quantity (Makkeh et al. 2021; Ehrlich et al. 2024).
///
/// By default (`IsxMethod::EhrlichKsg`), this uses the KSG-style kNN construction described by
/// Ehrlich et al. (2024, Appendix H).
///
/// # Units
/// Returns redundancy in **nats** (natural log).
///
/// # Important: can be negative
/// `I^sx_∩` is a well-defined functional of the joint distribution, but it is **not guaranteed
/// to be non-negative** under all desiderata (see the PID inconsistency/impossibility results
/// discussed in Makkeh et al. 2021 and Matthias et al. 2025). Do not clamp this value to 0.
///
/// # Assumptions / failure modes (estimator-level)
/// The default estimator is kNN-based and inherits the usual kNN MI pathologies:
/// - The default support contract is unspecified and fails closed. Callers must explicitly assert
///   full-dimensional absolute continuity for every marginal and joint law used by the estimator.
///   Exact coordinate ties are incompatible with ideal i.i.d., unrounded continuous-sample
///   conditions but do not identify their cause or population support; all-unique finite
///   observations do not prove the model.
/// - Assumes i.i.d. samples from a continuous distribution; trajectory autocorrelation and
///   quantization/duplicates can collapse the kNN radius or create an ambiguous positive boundary.
///   Adding jitter changes the estimated distribution and is appropriate only under an explicit
///   observation-noise model or as a seeded, reported noise-scale sensitivity analysis; otherwise
///   use a discrete, quantized, or mixed-support estimator.
/// - Can fail in high ambient/intrinsic dimension due to distance concentration.
/// - Can require prohibitive samples under strong dependence (very large true MI).
/// - Exact deterministic continuous maps have infinite MI and fall outside the estimator's domain.
///   An explicit observation-noise model defines a different noisy population law. Finite MI
///   remains a separate population assumption. Otherwise, use a suitable discrete or mixed
///   estimator.
/// - The two source matrices must have the same ambient column count. The small-ball
///   disjunction compares their raw neighborhood radii, whose asymptotic scaling depends on
///   dimension; unequal-dimensional source balls therefore do not share the estimator's
///   required reference scaling. Equal ambient dimensions are only a necessary guard: they do
///   **not** prove equal intrinsic dimensions, compatible reference measures, or comparable
///   neighborhood geometry.
/// - Relative source units and preprocessing define the comparison between source neighborhoods
///   and are part of the continuous `I^sx_∩` estimand. Record the full scheme and do not compare
///   or pool results across different source scalings/projections.
///
/// Other `IsxMethod` variants are included only as explicit experimental baselines / cross-checks
/// against the default estimator, and should not be trusted without validation.
pub(crate) fn isx_redundancy(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
) -> PidResult<f64> {
    isx_redundancy_with_budget(s1, s2, t, cfg, ResourceBudget::default())
}

pub(crate) fn isx_redundancy_with_budget(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    const CONTEXT: &str = "isx_redundancy";
    validate_isx_structure(CONTEXT, s1, s2, t, cfg)?;
    validate_support_contract(CONTEXT, cfg.support_contract, cfg.metric)?;
    let threads = effective_thread_count(budget.max_threads, s1.nrows());
    let estimate = isx_resource_estimate_for_method(s1, s2, t, cfg.method, threads)?;
    budget.check(CONTEXT, estimate)?;
    validate_observed_sample_conditions_with_budget(
        CONTEXT,
        cfg.support_contract,
        &[s1, s2, t],
        budget,
    )?;
    match cfg.method {
        IsxMethod::EhrlichKsg => crate::par::with_thread_budget(threads, || {
            isx_redundancy_ehrlich_ksg(s1, s2, t, cfg, budget)
        }),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::HeuristicSketch => isx_redundancy_heuristic_sketch(s1, s2, t, cfg, budget),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::LocalMinKsg => isx_redundancy_local_min_ksg(s1, s2, t, cfg, budget),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::DisjunctionFromLocalMi => {
            isx_redundancy_disjunction_from_local_mi(s1, s2, t, cfg, budget)
        }
    }
}

fn validate_isx_structure(
    context: &'static str,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
) -> PidResult<()> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context,
            left_rows: s1.nrows(),
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    if s1.ncols() == 0 || s2.ncols() == 0 || t.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "inputs must have at least 1 column",
        });
    }
    if s1.ncols() != s2.ncols() {
        return Err(PidError::SourceDimensionMismatch {
            context,
            left_cols: s1.ncols(),
            right_cols: s2.ncols(),
        });
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }
    if cfg.k == 0 || s1.nrows() <= cfg.k {
        return Err(PidError::InvalidK {
            k: cfg.k,
            n_samples: s1.nrows(),
        });
    }
    // The cited continuous `I^sx_∩` construction is restricted to its documented L∞/Chebyshev
    // convention. This is metric-domain validation, not a general consistency claim.
    // Do not silently “swap the geometry” (e.g., hyperbolic distances) and still call it `I^sx_∩`.
    if cfg.method == IsxMethod::EhrlichKsg && cfg.metric != Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context,
            message:
                "IsxMethod::EhrlichKsg is restricted to the cited Metric::Chebyshev (L∞) convention; other metrics are research-gated",
        });
    }
    Ok(())
}

/// Compute the cited restricted-domain estimator with neighborhood, scaling, overlap, assumption,
/// provenance, and resource diagnostics attached.
pub fn isx_redundancy_report(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    config: &IsxConfig,
    provenance: &IsxProvenance,
    budget: ResourceBudget,
) -> PidResult<IsxReport> {
    Ok(isx_redundancy_report_with_local_terms(s1, s2, target, config, provenance, budget)?.report)
}

pub(crate) fn isx_redundancy_report_with_local_terms(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    config: &IsxConfig,
    provenance: &IsxProvenance,
    budget: ResourceBudget,
) -> PidResult<IsxReportComputation> {
    validate_isx_structure("isx_redundancy_report", s1, s2, target, config)?;
    if config.method != IsxMethod::EhrlichKsg {
        return Err(PidError::InvalidConfig {
            context: "isx_redundancy_report",
            message: "report-first ISX is defined only for the cited EhrlichKsg construction",
        });
    }
    validate_support_contract(
        "isx_redundancy_report",
        config.support_contract,
        config.metric,
    )?;
    let threads = effective_thread_count(budget.max_threads, s1.nrows());
    let resource_estimate = isx_report_resource_estimate(s1, s2, target, provenance, threads)?;
    budget.check("isx_redundancy_report", resource_estimate)?;
    validate_observed_sample_conditions_with_budget(
        "isx_redundancy_report",
        config.support_contract,
        &[s1, s2, target],
        budget,
    )?;
    let local = crate::par::with_thread_budget(threads, || {
        isx_local_diagnostics(s1, s2, target, config, budget)
    })?;
    let estimate_nats =
        compensated_sum(local.iter().map(|term| term.term_nats)) / local.len() as f64;
    let local_diagnostics = summarize_isx_local(&local, budget)?;
    let assumption_ledger = isx_assumption_ledger(provenance, budget)?;
    let combined_preprocessing = combined_preprocessing_description(provenance)?;
    let mut input_hashes_sha256 = try_vec_with_capacity("ISX report input hashes", 3, budget)?;
    input_hashes_sha256.extend([hash_matrix(s1), hash_matrix(s2), hash_matrix(target)]);
    let mut warnings = try_vec_with_capacity("ISX report warnings", 7, budget)?;
    warnings.extend([
        WarningCode::DiagnosticsDoNotProvePopulationAssumptions,
        WarningCode::ExperimentalEstimator,
        WarningCode::KTrajectoryNotEvaluated,
        WarningCode::SampleSizeTrajectoryNotEvaluated,
        WarningCode::TransformationSensitivityNotEvaluated,
        WarningCode::ObservationNoiseSensitivityNotEvaluated,
    ]);
    if provenance.sampling_model_description.is_none() {
        warnings.push(WarningCode::DependenceDiagnosticsNotEvaluated);
    }
    let report = IsxReport {
        estimate_nats,
        n_samples: s1.nrows(),
        k: config.k,
        source_dimensions: [s1.ncols(), s2.ncols()],
        target_dimension: target.ncols(),
        estimand: EstimandIdentity {
            family: "ehrlich-wibral-continuous-isx",
            definition_revision: "common-coordinate-radius-v1",
            estimator_revision: "strict-unique-shell-integer-harmonic-isx-v4",
            units: InformationUnit::Nats,
            metric: "chebyshev-common-coordinate-radius",
            source_gauge: Some("caller-declared-source-gauges"),
        },
        scientific_status: ScientificStatus::ExperimentalRestrictedDomain,
        support_contract: config.support_contract,
        provenance: provenance.try_clone_for_report()?,
        provenance_hashes: ProvenanceHashes {
            input_hashes_sha256,
            preprocessing_hash_sha256: hash_text(&combined_preprocessing),
            observation_model_hash_sha256: hash_text(provenance.observation_model_description()),
            training_split_id: provenance
                .training_split_id
                .as_deref()
                .map(|value| try_owned_text("ISX report split identity", value))
                .transpose()?,
            evaluation_split_id: provenance
                .evaluation_split_id
                .as_deref()
                .map(|value| try_owned_text("ISX report split identity", value))
                .transpose()?,
        },
        assumption_ledger,
        local_diagnostics,
        resource_estimate,
        resource_budget: budget,
        warnings,
    };
    Ok(IsxReportComputation { report, local })
}

/// Conservative peak-memory and pairwise-work estimate for report-first two-source ISX.
pub fn isx_resource_estimate(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
) -> PidResult<ResourceEstimate> {
    isx_resource_estimate_for_threads(
        s1,
        s2,
        target,
        effective_thread_count(ResourceBudget::default().max_threads, s1.nrows()),
    )
}

/// ISX preflight including one scratch buffer and explicit stack reservation per active worker.
pub fn isx_resource_estimate_for_threads(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "isx_redundancy_report";
    if max_threads == 0 {
        return Err(PidError::ResourceLimitExceeded {
            operation: OPERATION,
            resource: "threads",
            requested: 1,
            limit: 0,
        });
    }
    if s1.nrows() != s2.nrows() || s1.nrows() != target.nrows() {
        return Err(PidError::RowCountMismatch {
            context: OPERATION,
            left_rows: s1.nrows(),
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                target.nrows()
            },
        });
    }
    let n_usize = s1.nrows();
    let n = n_usize as u128;
    let dimensions = s1
        .ncols()
        .checked_add(s2.ncols())
        .and_then(|value| value.checked_add(target.ncols()))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })? as u128;
    let pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    // The coefficient-cancelling Ehrlich path stores H_(m-1) at positive integer argument m.
    // Its table retains the previous n+1 binary64 allocation shape.
    let harmonic_bytes = n
        .checked_add(1)
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let local_bytes = n
        .checked_mul(std::mem::size_of::<IsxLocalDiagnostic>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let summary_bytes = n
        .checked_mul(
            6u128
                .checked_mul(std::mem::size_of::<f64>() as u128)
                .and_then(|value| {
                    value.checked_add(6u128.checked_mul(std::mem::size_of::<usize>() as u128)?)
                })
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?,
        )
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let active_threads = effective_thread_count(max_threads, n_usize) as u128;
    let worker_scratch = active_threads
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_mul(std::mem::size_of::<DistIsx2>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    #[cfg(feature = "parallel")]
    let worker_stacks = active_threads
        .checked_mul(WORKER_STACK_BYTES as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    #[cfg(not(feature = "parallel"))]
    let worker_stacks = 0;
    #[cfg(feature = "parallel")]
    let ordered_map_intermediate = n
        .checked_mul(std::mem::size_of::<PidResult<IsxLocalDiagnostic>>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    #[cfg(not(feature = "parallel"))]
    let ordered_map_intermediate = 0;
    let estimator_peak = harmonic_bytes
        .checked_add(local_bytes)
        .and_then(|value| value.checked_add(ordered_map_intermediate))
        .and_then(|value| value.checked_add(worker_scratch))
        .and_then(|value| value.checked_add(worker_stacks))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let summary_peak = local_bytes
        .checked_add(summary_bytes)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let support_peak = [s1, s2, target]
        .into_iter()
        .map(continuous_cardinality_estimate)
        .try_fold(ResourceEstimate::ZERO, |peak, estimate| {
            let estimate = estimate?;
            Ok::<_, PidError>(ResourceEstimate {
                estimated_bytes: peak.estimated_bytes.max(estimate.estimated_bytes),
                pairwise_distances: 0,
                operations_hint: peak
                    .operations_hint
                    .checked_add(estimate.operations_hint)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?,
            })
        })?;
    let operations_hint = pairs
        .checked_mul(2)
        .and_then(|value| value.checked_mul(dimensions.checked_add(16)?))
        .and_then(|value| value.checked_add(support_peak.operations_hint))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: estimator_peak
            .max(summary_peak)
            .max(support_peak.estimated_bytes),
        pairwise_distances: pairs,
        operations_hint,
    })
}

/// Complete ISX report preflight including retained provenance, hashes, and metadata.
pub fn isx_report_resource_estimate(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    provenance: &IsxProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "isx_redundancy_report";
    let mut estimate = isx_resource_estimate_for_threads(s1, s2, target, max_threads)?;
    let retained = provenance
        .heap_bytes()?
        .checked_mul(2)
        .and_then(|value| {
            value.checked_add(
                provenance.source1_gauge_description.len() as u128
                    + provenance.source2_gauge_description.len() as u128
                    + provenance.target_preprocessing_description.len() as u128
                    + 27,
            )
        })
        .and_then(|value| value.checked_add(std::mem::size_of::<IsxReport>() as u128))
        .and_then(|value| value.checked_add(5 * 64))
        .and_then(|value| {
            value.checked_add(
                12u128.checked_mul(std::mem::size_of::<AssumptionLedgerEntry>() as u128)?,
            )
        })
        .and_then(|value| {
            value.checked_add(7u128.checked_mul(std::mem::size_of::<WarningCode>() as u128)?)
        })
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    estimate.estimated_bytes =
        estimate
            .estimated_bytes
            .checked_add(retained)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    Ok(estimate)
}

fn continuous_cardinality_estimate(input: MatRef<'_>) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "ISX support cardinalities";
    let n = input.nrows() as u128;
    let dimensions = input.ncols() as u128;
    let coordinates = n.checked_mul(dimensions).ok_or(PidError::SizeOverflow {
        operation: OPERATION,
    })?;
    let log_n = if input.nrows() <= 1 {
        1u128
    } else {
        (usize::BITS - (input.nrows() - 1).leading_zeros()) as u128
    };
    Ok(ResourceEstimate {
        estimated_bytes: coordinates
            .checked_mul(2 * std::mem::size_of::<u64>() as u128)
            .and_then(|value| {
                value.checked_add(n.checked_mul(std::mem::size_of::<Vec<u64>>() as u128)?)
            })
            .and_then(|value| {
                value.checked_add(
                    dimensions.checked_mul(
                        std::mem::size_of::<CoordinateCardinalityDiagnostics>() as u128,
                    )?,
                )
            })
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?,
        pairwise_distances: 0,
        operations_hint: coordinates
            .checked_mul(log_n)
            .and_then(|value| value.checked_mul(2))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?,
    })
}

fn combined_preprocessing_description(provenance: &IsxProvenance) -> PidResult<String> {
    const PREFIX_BYTES: usize = "source1=; source2=; target=".len();
    let capacity = provenance
        .source1_gauge_description
        .len()
        .checked_add(provenance.source2_gauge_description.len())
        .and_then(|value| value.checked_add(provenance.target_preprocessing_description.len()))
        .and_then(|value| value.checked_add(PREFIX_BYTES))
        .ok_or(PidError::SizeOverflow {
            operation: "ISX preprocessing provenance",
        })?;
    let mut combined = String::new();
    combined
        .try_reserve_exact(capacity)
        .map_err(|_| PidError::AllocationFailed {
            operation: "ISX preprocessing provenance",
            requested_bytes: capacity as u128,
        })?;
    combined.push_str("source1=");
    combined.push_str(&provenance.source1_gauge_description);
    combined.push_str("; source2=");
    combined.push_str(&provenance.source2_gauge_description);
    combined.push_str("; target=");
    combined.push_str(&provenance.target_preprocessing_description);
    Ok(combined)
}

pub(crate) fn isx_resource_estimate_for_method(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    method: IsxMethod,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    let base = isx_resource_estimate_for_threads(s1, s2, target, max_threads)?;
    match method {
        IsxMethod::EhrlichKsg => Ok(base),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::HeuristicSketch => scale_isx_work(base, target.nrows(), 5, 5),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::LocalMinKsg => scale_isx_work(base, target.nrows(), 2, 2),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::DisjunctionFromLocalMi => scale_isx_work(base, target.nrows(), 3, 3),
    }
}

#[cfg(feature = "experimental-heuristics")]
fn scale_isx_work(
    base: ResourceEstimate,
    n: usize,
    passes: u128,
    retained_vectors: u128,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "experimental ISX heuristic";
    let retained_bytes = (n as u128)
        .checked_mul(retained_vectors)
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: base.estimated_bytes.checked_add(retained_bytes).ok_or(
            PidError::SizeOverflow {
                operation: OPERATION,
            },
        )?,
        pairwise_distances: base.pairwise_distances.checked_mul(passes).ok_or(
            PidError::SizeOverflow {
                operation: OPERATION,
            },
        )?,
        operations_hint: base.operations_hint.checked_mul(passes).ok_or(
            PidError::SizeOverflow {
                operation: OPERATION,
            },
        )?,
    })
}

fn isx_redundancy_ehrlich_ksg(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    let terms = isx_local_diagnostics(s1, s2, t, cfg, budget)?;
    let sum = compensated_sum(terms.iter().map(|term| term.term_nats));
    Ok(sum / terms.len() as f64)
}

fn isx_local_diagnostics(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<Vec<IsxLocalDiagnostic>> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_ehrlich_ksg",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    // This is the bivariate antichain α = {{1},{2}}; the disjunction distance in source space is:
    // d_S_disj(i,j) = min( d(S1_i,S1_j), d(S2_i,S2_j) ).
    //
    // With Chebyshev/L∞ and a shared target ball, the joint disjunction distance is:
    // d_ST_disj(i,j) = max( d(T_i,T_j), d_S_disj(i,j) ).
    let shifted_harmonics = shifted_harmonic_table(n)?;

    // Per-point local term. Each point is independent and allocates its own scratch, so the
    // closure is pure and can run data-parallel. Results are collected **in index order** and
    // reduced with the same deterministic compensated summation in both paths, so the `parallel`
    // path is bit-for-bit identical to the serial path (see `map_index_ordered`).
    let local = |i: usize| -> PidResult<IsxLocalDiagnostic> {
        let mut scratch = try_vec_with_capacity(
            "ISX per-query distance scratch",
            n.saturating_sub(1),
            budget,
        )?;
        let s1i = s1.row(i);
        let s2i = s2.row(i);
        let ti = t.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            let ds1 = cfg.metric.checked_distance(
                s1i,
                s1.row(j),
                "isx_redundancy_ehrlich_ksg: s1 distance",
            )?;
            let ds2 = cfg.metric.checked_distance(
                s2i,
                s2.row(j),
                "isx_redundancy_ehrlich_ksg: s2 distance",
            )?;
            let dt = cfg.metric.checked_distance(
                ti,
                t.row(j),
                "isx_redundancy_ehrlich_ksg: target distance",
            )?;
            let ds = ds1.min(ds2);
            scratch.push(DistIsx2 {
                joint: dt.max(ds),
                dt,
                ds,
                ds1,
                ds2,
            });
        }

        let kth = k - 1;
        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps_raw = scratch[kth].joint;
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "isx_redundancy_ehrlich_ksg: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(
            "isx_redundancy_ehrlich_ksg",
            i,
            k,
            eps_raw,
            interior_count,
            boundary_count,
        )?;
        let eps = strict_radius(eps_raw);

        // Counts exclude self; the estimator needs counts including self.
        let mut n_t = 1usize;
        let mut n_alpha = 1usize;
        let mut n_s1 = 0usize;
        let mut n_s2 = 0usize;
        let mut n_overlap = 0usize;
        let mut n_s1_half = 0usize;
        let mut n_s2_half = 0usize;
        let mut n_overlap_half = 0usize;
        let half_radius = eps_raw * 0.5;
        for d in &scratch {
            if d.dt <= eps {
                n_t += 1;
            }
            if d.ds <= eps {
                n_alpha += 1;
            }
            let in_s1 = d.ds1 <= eps;
            let in_s2 = d.ds2 <= eps;
            n_s1 += usize::from(in_s1);
            n_s2 += usize::from(in_s2);
            n_overlap += usize::from(in_s1 && in_s2);
            let in_s1_half = d.ds1 < half_radius;
            let in_s2_half = d.ds2 < half_radius;
            n_s1_half += usize::from(in_s1_half);
            n_s2_half += usize::from(in_s2_half);
            n_overlap_half += usize::from(in_s1_half && in_s2_half);
        }

        Ok(IsxLocalDiagnostic {
            term_nats: ksg_local_harmonic_term(&shifted_harmonics, k, n, n_alpha, n_t),
            joint_radius: eps_raw,
            source_union_count: n_alpha,
            target_count: n_t,
            source1_count: n_s1,
            source2_count: n_s2,
            overlap_count: n_overlap,
            source1_half_count: n_s1_half,
            source2_half_count: n_s2_half,
            overlap_half_count: n_overlap_half,
        })
    };

    crate::par::map_index_ordered(n, local)
}

fn summarize_isx_local(
    local: &[IsxLocalDiagnostic],
    budget: ResourceBudget,
) -> PidResult<IsxLocalDiagnosticsSummary> {
    let mut radii = try_vec_with_capacity("ISX radius summary", local.len(), budget)?;
    let mut source_union = try_vec_with_capacity("ISX union-count summary", local.len(), budget)?;
    let mut target = try_vec_with_capacity("ISX target-count summary", local.len(), budget)?;
    let mut source1 = try_vec_with_capacity("ISX source1-count summary", local.len(), budget)?;
    let mut source2 = try_vec_with_capacity("ISX source2-count summary", local.len(), budget)?;
    let mut overlap = try_vec_with_capacity("ISX overlap-count summary", local.len(), budget)?;
    let mut overlap_half =
        try_vec_with_capacity("ISX half-overlap-count summary", local.len(), budget)?;
    let mut overlap_ratio =
        try_vec_with_capacity("ISX overlap-ratio summary", local.len(), budget)?;
    let mut overlap_half_ratio =
        try_vec_with_capacity("ISX half-overlap-ratio summary", local.len(), budget)?;
    let mut source1_slopes =
        try_vec_with_capacity("ISX source1-slope summary", local.len(), budget)?;
    let mut source2_slopes =
        try_vec_with_capacity("ISX source2-slope summary", local.len(), budget)?;
    let mut terms = try_vec_with_capacity("ISX local-term summary", local.len(), budget)?;
    for value in local {
        radii.push(value.joint_radius);
        source_union.push(value.source_union_count);
        target.push(value.target_count);
        source1.push(value.source1_count);
        source2.push(value.source2_count);
        overlap.push(value.overlap_count);
        overlap_half.push(value.overlap_half_count);
        let union = value
            .source1_count
            .checked_add(value.source2_count)
            .and_then(|count| count.checked_sub(value.overlap_count))
            .ok_or(PidError::SizeOverflow {
                operation: "ISX overlap ratio",
            })?;
        let half_union = value
            .source1_half_count
            .checked_add(value.source2_half_count)
            .and_then(|count| count.checked_sub(value.overlap_half_count))
            .ok_or(PidError::SizeOverflow {
                operation: "ISX half-overlap ratio",
            })?;
        overlap_ratio.push(if union == 0 {
            0.0
        } else {
            value.overlap_count as f64 / union as f64
        });
        overlap_half_ratio.push(if half_union == 0 {
            0.0
        } else {
            value.overlap_half_count as f64 / half_union as f64
        });
        if let Some(slope) = scaling_slope(value.source1_count, value.source1_half_count) {
            source1_slopes.push(slope);
        }
        if let Some(slope) = scaling_slope(value.source2_count, value.source2_half_count) {
            source2_slopes.push(slope);
        }
        terms.push(value.term_nats);
    }
    for values in [
        &mut radii,
        &mut overlap_ratio,
        &mut overlap_half_ratio,
        &mut source1_slopes,
        &mut source2_slopes,
        &mut terms,
    ] {
        values.sort_unstable_by(f64::total_cmp);
    }
    for values in [
        &mut source_union,
        &mut target,
        &mut source1,
        &mut source2,
        &mut overlap,
        &mut overlap_half,
    ] {
        values.sort_unstable();
    }
    Ok(IsxLocalDiagnosticsSummary {
        joint_radius: value_quantiles(&radii)?,
        source_union_count: count_quantiles(&source_union)?,
        target_count: count_quantiles(&target)?,
        source1_count: count_quantiles(&source1)?,
        source2_count: count_quantiles(&source2)?,
        overlap_count: count_quantiles(&overlap)?,
        overlap_half_radius_count: count_quantiles(&overlap_half)?,
        overlap_ratio: value_quantiles(&overlap_ratio)?,
        overlap_half_radius_ratio: value_quantiles(&overlap_half_ratio)?,
        source1_scaling_slope: (!source1_slopes.is_empty())
            .then(|| value_quantiles(&source1_slopes))
            .transpose()?,
        source2_scaling_slope: (!source2_slopes.is_empty())
            .then(|| value_quantiles(&source2_slopes))
            .transpose()?,
        undefined_source1_slopes: local.len() - source1_slopes.len(),
        undefined_source2_slopes: local.len() - source2_slopes.len(),
        local_redundancy_nats: value_quantiles(&terms)?,
    })
}

fn scaling_slope(full_count: usize, half_count: usize) -> Option<f64> {
    (full_count > 0 && half_count > 0 && full_count >= half_count)
        .then(|| (full_count as f64 / half_count as f64).ln() / 2.0_f64.ln())
}

fn isx_assumption_ledger(
    provenance: &IsxProvenance,
    budget: ResourceBudget,
) -> PidResult<Vec<AssumptionLedgerEntry>> {
    let mut ledger = try_vec_with_capacity("ISX assumption ledger", 12, budget)?;
    let separated_splits = provenance.training_split_id.is_some()
        && provenance.evaluation_split_id.is_some()
        && provenance.training_split_id != provenance.evaluation_split_id;
    ledger.extend([
        AssumptionLedgerEntry {
            assumption: Assumption::RegularContinuousOrManifoldLaw,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; sample diagnostics cannot prove population support",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FixedLocalDimension,
            state: AssumptionState::WarningPresent,
            note: "equal ambient source columns do not prove equal intrinsic dimensions",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::RegularFiniteDensity,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; inspect the multi-scale branch slopes",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FiniteMutualInformation,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; finite output is not proof",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::DeclaredSamplingDependence,
            state: if provenance.sampling_model_description.is_some() {
                AssumptionState::AssumptionsDeclared
            } else {
                AssumptionState::WarningPresent
            },
            note: "sampling model is recorded but not verified",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::UniqueKthNeighborShell,
            state: AssumptionState::FiniteSampleChecksPassed,
            note: "every joint disjunction shell used by the estimate passed the exact check",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::LocalNeighborhoods,
            state: AssumptionState::NotEvaluated,
            note: "compare radius quantiles with density, noise, and domain scales",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::CommonBranchLeadingScale,
            state: AssumptionState::WarningPresent,
            note: "branch slopes are diagnostics, not a proof of common asymptotic scaling",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::LowerOrderBranchIntersections,
            state: AssumptionState::WarningPresent,
            note: "overlap ratios are reported at full and half radii",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FixedPreprocessingAndMetric,
            state: AssumptionState::AssumptionsDeclared,
            note: "source gauges and target preprocessing are hashed",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::AdequateSampleSize,
            state: AssumptionState::NotEvaluated,
            note: "run declared k and sample-size trajectories",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::AdaptiveTransformsFitOutsideEvaluationData,
            state: if separated_splits {
                AssumptionState::AssumptionsDeclared
            } else {
                AssumptionState::WarningPresent
            },
            note: "distinct training and evaluation split identifiers are required",
        },
    ]);
    Ok(ledger)
}

#[cfg(feature = "experimental-heuristics")]
fn isx_redundancy_disjunction_from_local_mi(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_disjunction_from_local_mi",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    let ksg_cfg = KsgConfig {
        k: cfg.k,
        metric: cfg.metric,
        tie_epsilon: cfg.tie_epsilon,
        negative_handling: NegativeHandling::Allow,
        support_contract: cfg.support_contract,
    };

    let mut i1 = ksg_local_mi_terms_with_budget(s1, t, &ksg_cfg, budget)?;
    let i2 = ksg_local_mi_terms_with_budget(s2, t, &ksg_cfg, budget)?;
    let i12 = ksg_local_mi_terms_xblocks_with_budget(&[s1, s2], t, &ksg_cfg, budget)?;

    for ((a, &b), &c) in i1.iter_mut().zip(i2.iter()).zip(i12.iter()) {
        // Compute: log(exp(a)+exp(b)-exp(c)) stably.
        let m = (*a).max(b).max(c);
        let sa = (*a - m).exp();
        let sb = (b - m).exp();
        let sc = (c - m).exp();
        let s = sa + sb - sc;
        if !s.is_finite() || s <= 0.0 {
            return Err(PidError::NumericalInstability {
                context:
                    "isx_redundancy_disjunction_from_local_mi: disjunction argument is non-positive",
            });
        }
        *a = m + s.ln();
    }

    Ok(compensated_sum(i1) / (n as f64))
}

#[cfg(feature = "experimental-heuristics")]
fn isx_redundancy_local_min_ksg(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_local_min_ksg",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    let ksg_cfg = KsgConfig {
        k: cfg.k,
        metric: cfg.metric,
        tie_epsilon: cfg.tie_epsilon,
        negative_handling: NegativeHandling::Allow,
        support_contract: cfg.support_contract,
    };

    let local_s1 = ksg_local_mi_terms_with_budget(s1, t, &ksg_cfg, budget)?;
    let local_s2 = ksg_local_mi_terms_with_budget(s2, t, &ksg_cfg, budget)?;

    let red = compensated_sum(
        local_s1
            .iter()
            .zip(local_s2.iter())
            .map(|(&a, &b)| a.min(b)),
    ) / (n as f64);

    Ok(red)
}

#[cfg(feature = "experimental-heuristics")]
fn isx_redundancy_heuristic_sketch(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_heuristic_sketch",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    // 1) Per-sample kNN radii in the (S1,T) and (S2,T) joint spaces. (Steps 2–3 use only
    //    these two and their samplewise min; no (S1,S2,T) joint radius enters the estimate.)
    let mut eps_s1_t = try_vec_filled("experimental ISX source1 radii", n, 0.0f64, budget)?;
    let mut eps_s2_t = try_vec_filled("experimental ISX source2 radii", n, 0.0f64, budget)?;

    let mut scratch = try_vec_with_capacity(
        "experimental ISX distance scratch",
        n.saturating_sub(1),
        budget,
    )?;
    for i in 0..n {
        let e1 =
            kth_neighbor_distance_joint_max_with_scratch(&[s1, t], i, k, cfg.metric, &mut scratch)?;
        if e1 == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "isx_redundancy_heuristic_sketch: kNN radius collapsed to 0; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().copied(), e1);
        validate_kth_neighbor_shell(
            "isx_redundancy_heuristic_sketch (s1,target)",
            i,
            k,
            e1,
            interior_count,
            boundary_count,
        )?;
        eps_s1_t[i] = e1;

        let e2 =
            kth_neighbor_distance_joint_max_with_scratch(&[s2, t], i, k, cfg.metric, &mut scratch)?;
        if e2 == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "isx_redundancy_heuristic_sketch: kNN radius collapsed to 0; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().copied(), e2);
        validate_kth_neighbor_shell(
            "isx_redundancy_heuristic_sketch (s2,target)",
            i,
            k,
            e2,
            interior_count,
            boundary_count,
        )?;
        eps_s2_t[i] = e2;
    }

    // 2) Count neighbors in target space within the respective radii.
    let mut n_t_s1 = try_vec_filled("experimental ISX source1 target counts", n, 0usize, budget)?;
    let mut n_t_s2 = try_vec_filled("experimental ISX source2 target counts", n, 0usize, budget)?;
    let mut n_t_shared =
        try_vec_filled("experimental ISX shared target counts", n, 0usize, budget)?;

    for i in 0..n {
        let e1_raw = eps_s1_t[i];
        let e2_raw = eps_s2_t[i];

        let e1 = strict_radius(e1_raw);
        let e2 = strict_radius(e2_raw);
        let es = strict_radius(e1_raw.min(e2_raw));

        n_t_s1[i] = count_neighbors_within(t, i, e1, cfg.metric)?;
        n_t_s2[i] = count_neighbors_within(t, i, e2, cfg.metric)?;
        n_t_shared[i] = count_neighbors_within(t, i, es, cfg.metric)?;
    }

    // 3) Experimental heuristic sketch estimator.
    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n)?;

    let avg_term = compensated_sum((0..n).map(|i| {
        let psi_shared = psi_int[n_t_shared[i] + 1];
        let psi_s1 = psi_int[n_t_s1[i] + 1];
        let psi_s2 = psi_int[n_t_s2[i] + 1];
        psi_shared - 0.5 * (psi_s1 + psi_s2)
    })) / (n as f64);

    let redundancy = psi_k + psi_n + avg_term;
    Ok(redundancy)
}

#[cfg(test)]
mod tests {
    use super::{isx_local_diagnostics, IsxConfig};
    use crate::{MatRef, ResourceBudget};

    #[test]
    fn ehrlich_inclusive_counts_reach_the_exact_integer_harmonic_local_term() {
        // This is a finite algorithmic witness only. The second source is constructed so every
        // pairwise S2 distance strictly dominates S1, reducing the source-disjunction distance
        // min(d_S1,d_S2) exactly to d_S1 without changing the continuous ISX definition.
        let s1: [f64; 8] = [7.0, 194.0, 144.0, 75.0, 61.0, 138.0, 38.0, 9.0];
        let target: [f64; 8] = [17.0, 48.0, 166.0, 120.0, 2.0, 199.0, 43.0, 93.0];
        let s2 = std::array::from_fn::<_, 8, _>(|index| 1_000.0 * s1[index] + index as f64);
        for left in 0..s1.len() {
            for right in left + 1..s1.len() {
                assert!(
                    (s2[left] - s2[right]).abs() > (s1[left] - s1[right]).abs(),
                    "S2 must be strictly dominated by S1 in the disjunction at ({left},{right})"
                );
            }
        }

        let s1 = MatRef::new(&s1, 8, 1).unwrap();
        let s2 = MatRef::new(&s2, 8, 1).unwrap();
        let target = MatRef::new(&target, 8, 1).unwrap();
        let config = IsxConfig {
            k: 2,
            ..IsxConfig::assume_regular_full_dimensional()
        };
        let local = isx_local_diagnostics(s1, s2, target, &config, ResourceBudget::default())
            .expect("the exact finite witness has unique positive k-th-neighbor shells");
        let expected = [
            (54.0, 3, 4),
            (119.0, 3, 7),
            (69.0, 3, 3),
            (69.0, 6, 3),
            (54.0, 4, 4),
            (79.0, 5, 2),
            (41.0, 5, 3),
            (66.0, 4, 4),
        ];

        assert_eq!(local.len(), expected.len());
        for (query, diagnostic) in local.iter().enumerate() {
            assert_eq!(
                (
                    diagnostic.joint_radius,
                    diagnostic.source_union_count,
                    diagnostic.target_count,
                ),
                expected[query],
                "query {query}"
            );
        }
        assert_eq!(
            local[5].term_nats.to_bits(),
            0x3fe0_4e04_e04e_04e0,
            "row 5 must use inclusive counts (n_alpha,n_t)=(5,2), giving 107/210"
        );
    }
}
```

## Artifact: `crates/pid-core/src/pid3.rs`

SHA-256: `f1f9d18b73312fb2e25e725382e65edf42bdaecd73d611d7dffc943221b2bfcd`

```text
//! Three-source continuous shared-exclusions availability diagnostics and research reproduction.
//!
//! # Method provenance and availability
//!
//! **PROJECT-DEFINED DIAGNOSTIC.** The `experimental-continuous` incomplete API computes only
//! ambient-dimension-compatible redundancy coordinates and exact atom combinations whose required
//! coordinates all exist. It deliberately does not impute a complete 18-atom PID and has no
//! dedicated paper method cited by pid-rs.
//!
//! Method catalog: pid.incomplete-continuous-pid3
//!
//! **PAPER-DEFINED RESEARCH REPRODUCTION.** The full lattice follows the shared-exclusions
//! construction but compares singleton and pair-source neighborhoods with different ambient
//! dimensions. It is available only with `research-mixed-dimension-pid3` plus a runtime opt-in.
//! A finite-union small-ball bound shows that, under positive regular branch expansions in one raw
//! radius, the union has the smallest branch exponent. Branches with larger exponents then have
//! vanishing relative mass. This standard consequence identifies raw-radius branch-weight
//! collapse. It does not prove that the published estimator is inconsistent. Such a claim would
//! also require an estimator-specific result for the random neighbor radius, local uniformity,
//! boundaries, count corrections, and bias. pid-rs supplies no such mixed-dimensional consistency
//! result. Dimension-normalized or probability-content gauges are not implemented because they
//! require a separate derivation and can define a different estimand.
//!
//! Method catalog: pid.mixed-dimension-pid3
//!
//! **NO GENERAL IMPLEMENTATION.** Schick-Poland et al. define a measure-theoretic
//! shared-exclusions PID functional for arbitrary variable types, but pid-rs implements no
//! practical general estimator for atomic, mixed, singular, stratified, or otherwise incompatible
//! support. Barà et al. (2025) provide a restricted nearest-neighbor PID for a discrete target and
//! continuous sources; that method is also not implemented here and does not close the general
//! arbitrary-support gap. Typed support contracts reject or flag incompatible inputs; callers must
//! route them to a matching estimand rather than treating the research PID3 path as a solution.
//!
//! Method catalog: unsupported.mixed-support-continuous-pid

use crate::distance_matrix::{symmetric_distances_with_budget, SymmetricDistanceMatrix};
use crate::error::{PidError, PidResult};
use crate::ksg::effective_thread_count;
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::nn::{kth_neighbor_shell_counts, strict_radius, validate_kth_neighbor_shell};
#[cfg(feature = "parallel")]
use crate::par::WORKER_STACK_BYTES;
use crate::resource::{try_vec_filled, try_vec_with_capacity, ResourceBudget, ResourceEstimate};
use crate::stats::{compensated_sum, ksg_local_harmonic_term, shifted_harmonic_table};
use crate::support::{
    validate_observed_sample_conditions_with_budget, validate_support_contract,
    CoordinateCardinalityDiagnostics, SupportContract,
};

#[derive(Clone, Copy)]
struct DistIsx3 {
    joint: f64,
    ds: f64,
    dt: f64,
}

#[derive(Debug, Clone)]
pub struct Pid3Config {
    pub k: usize,
    pub metric: Metric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    /// Strict counts use the predecessor of the raw kNN radius.
    pub tie_epsilon: f64,
    /// Caller-declared population support assumptions. The default is unspecified and fails
    /// closed; use [`Pid3Config::assume_regular_full_dimensional`] for an explicit assertion.
    pub support_contract: SupportContract,
    /// Explicit research opt-in for the full mixed-dimensional redundancy lattice.
    ///
    /// Every full three-source lattice contains antichains such as
    /// `{{S0}, {S1,S2}}`. The current kNN construction compares a singleton source ball with a
    /// concatenated pair-source ball without a dimension-derived normalization. Setting this to
    /// `true` preserves the implementation for reference reproduction and diagnostics; it does
    /// not validate a mixed-dimensional small-ball limit for scientific inference.
    #[cfg(feature = "research-mixed-dimension-pid3")]
    pub experimental_allow_mixed_dimension_lattice: bool,
}

impl Default for Pid3Config {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            support_contract: SupportContract::Unspecified,
            #[cfg(feature = "research-mixed-dimension-pid3")]
            experimental_allow_mixed_dimension_lattice: false,
        }
    }
}

impl Pid3Config {
    /// Construct a configuration that explicitly asserts full-dimensional absolute continuity.
    ///
    /// The full mixed-dimensional lattice remains compile-time research-gated. This constructor
    /// is intended first for [`incomplete_pid3_diagnostic`].
    pub fn assume_regular_full_dimensional() -> Self {
        Self {
            support_contract: SupportContract::assume_regular_full_dimensional(),
            ..Self::default()
        }
    }
}

/// A 3-source antichain on indices {0,1,2}, represented as up to 3 conjunction masks.
///
/// Each mask is a non-zero subset bitmask over {0,1,2}:
/// - bit 0 => source 0
/// - bit 1 => source 1
/// - bit 2 => source 2
///
/// Example: `{ {0}, {1,2} }` is encoded as `[0b001, 0b110]`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Antichain3 {
    sets: [u8; 3],
    len: u8,
}

impl Antichain3 {
    pub fn sets(&self) -> &[u8] {
        &self.sets[..(self.len as usize)]
    }

    pub fn len(&self) -> usize {
        self.len as usize
    }

    pub fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Create an antichain from a list of non-empty subset masks over {0,1,2}.
    ///
    /// The input is canonicalized (sorted ascending) and validated to satisfy the
    /// antichain property (no set is a subset of another).
    pub fn try_from_sets(sets: &[u8]) -> PidResult<Self> {
        if sets.is_empty() || sets.len() > 3 {
            return Err(PidError::InvalidConfig {
                context: "Antichain3::try_from_sets",
                message: "need 1..=3 sets",
            });
        }

        let mut out = [0u8; 3];
        for (idx, &m) in sets.iter().enumerate() {
            if m == 0 || m > 0b111 {
                return Err(PidError::InvalidConfig {
                    context: "Antichain3::try_from_sets",
                    message: "set masks must be in 1..=0b111",
                });
            }
            out[idx] = m;
        }

        let len = sets.len();
        out[..len].sort_unstable();

        for i in 0..len {
            for j in (i + 1)..len {
                let a = out[i];
                let b = out[j];
                if a == b {
                    return Err(PidError::InvalidConfig {
                        context: "Antichain3::try_from_sets",
                        message: "duplicate set mask",
                    });
                }
                if (a & b) == a || (a & b) == b {
                    return Err(PidError::InvalidConfig {
                        context: "Antichain3::try_from_sets",
                        message: "not an antichain (subset relation present)",
                    });
                }
            }
        }

        Ok(Self {
            sets: out,
            len: len as u8,
        })
    }
}

impl Ord for Antichain3 {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.len
            .cmp(&other.len)
            .then_with(|| self.sets().cmp(other.sets()))
    }
}

impl PartialOrd for Antichain3 {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Debug, Clone)]
#[cfg(feature = "research-mixed-dimension-pid3")]
pub struct Pid3Redundancy {
    pub antichain: Antichain3,
    pub value: f64,
}

#[derive(Debug, Clone)]
#[cfg(feature = "research-mixed-dimension-pid3")]
pub struct Pid3Atom {
    pub antichain: Antichain3,
    pub value: f64,
}

/// Scientific maturity of a full continuous PID3 result.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
#[cfg(feature = "research-mixed-dimension-pid3")]
pub enum Pid3MethodStatus {
    /// Reference-reproduction path containing mixed-dimensional lattice comparisons without an
    /// established small-ball limit.
    ExperimentalMixedDimension,
}

#[cfg(feature = "research-mixed-dimension-pid3")]
const FULL_PID3_WARNINGS: [&str; 3] = [
    "the full continuous PID3 lattice compares mixed-dimensional source neighborhoods and has no established small-ball consistency result",
    "the support contract is caller-declared; sample checks can identify incompatible observations but cannot determine their cause or verify population support",
    "relative source units and preprocessing are part of the shared-exclusions estimand and must be recorded alongside every reported result",
];

/// Full 18-coordinate continuous PID3 result with attached status and configuration metadata.
///
/// This type is produced only after the explicit mixed-dimensional research opt-in. Its metadata
/// and warnings are part of the result contract, not a validation claim. Use [`Pid3Report`] when
/// caller-declared preprocessing and observation-model descriptions must travel with it.
#[derive(Debug)]
#[non_exhaustive]
#[cfg(feature = "research-mixed-dimension-pid3")]
pub struct Pid3Result {
    pub n_samples: usize,
    pub k: usize,
    pub metric: Metric,
    pub support_contract: SupportContract,
    pub source_ambient_dimensions: [usize; 3],
    pub target_ambient_dimension: usize,
    pub method_status: Pid3MethodStatus,
    pub warnings: Vec<&'static str>,
    pub redundancies: Vec<Pid3Redundancy>,
    pub atoms: Vec<Pid3Atom>,
}

/// Structurally checked, caller-declared provenance for a full `Pid3Report`.
///
/// Separate source descriptions are required because relative source scaling changes the
/// shared-exclusions estimand. Construction checks only nonemptiness, not truth or adequacy.
#[derive(Debug, PartialEq, Eq)]
#[non_exhaustive]
pub struct Pid3Provenance {
    source1_preprocessing_description: String,
    source2_preprocessing_description: String,
    source3_preprocessing_description: String,
    target_preprocessing_description: String,
    observation_model_description: String,
}

impl Pid3Provenance {
    pub fn new(
        source1_preprocessing_description: impl AsRef<str>,
        source2_preprocessing_description: impl AsRef<str>,
        source3_preprocessing_description: impl AsRef<str>,
        target_preprocessing_description: impl AsRef<str>,
        observation_model_description: impl AsRef<str>,
    ) -> PidResult<Self> {
        let source1_preprocessing_description = source1_preprocessing_description.as_ref();
        let source2_preprocessing_description = source2_preprocessing_description.as_ref();
        let source3_preprocessing_description = source3_preprocessing_description.as_ref();
        let target_preprocessing_description = target_preprocessing_description.as_ref();
        let observation_model_description = observation_model_description.as_ref();
        for (description, message) in [
            (
                source1_preprocessing_description,
                "source1_preprocessing_description must be nonempty",
            ),
            (
                source2_preprocessing_description,
                "source2_preprocessing_description must be nonempty",
            ),
            (
                source3_preprocessing_description,
                "source3_preprocessing_description must be nonempty",
            ),
            (
                target_preprocessing_description,
                "target_preprocessing_description must be nonempty",
            ),
            (
                observation_model_description,
                "observation_model_description must be nonempty",
            ),
        ] {
            if description.trim().is_empty() || description.len() > 16 * 1024 {
                return Err(PidError::InvalidConfig {
                    context: "Pid3Provenance::new",
                    message: match message {
                        "source1_preprocessing_description must be nonempty" => {
                            "source1_preprocessing_description must be nonempty and at most 16 KiB"
                        }
                        "source2_preprocessing_description must be nonempty" => {
                            "source2_preprocessing_description must be nonempty and at most 16 KiB"
                        }
                        "source3_preprocessing_description must be nonempty" => {
                            "source3_preprocessing_description must be nonempty and at most 16 KiB"
                        }
                        "target_preprocessing_description must be nonempty" => {
                            "target_preprocessing_description must be nonempty and at most 16 KiB"
                        }
                        _ => "observation_model_description must be nonempty and at most 16 KiB",
                    },
                });
            }
        }
        Ok(Self {
            source1_preprocessing_description: try_owned_text(
                "PID3 provenance",
                source1_preprocessing_description,
            )?,
            source2_preprocessing_description: try_owned_text(
                "PID3 provenance",
                source2_preprocessing_description,
            )?,
            source3_preprocessing_description: try_owned_text(
                "PID3 provenance",
                source3_preprocessing_description,
            )?,
            target_preprocessing_description: try_owned_text(
                "PID3 provenance",
                target_preprocessing_description,
            )?,
            observation_model_description: try_owned_text(
                "PID3 provenance",
                observation_model_description,
            )?,
        })
    }

    pub fn source1_preprocessing_description(&self) -> &str {
        &self.source1_preprocessing_description
    }

    pub fn source2_preprocessing_description(&self) -> &str {
        &self.source2_preprocessing_description
    }

    pub fn source3_preprocessing_description(&self) -> &str {
        &self.source3_preprocessing_description
    }

    pub fn target_preprocessing_description(&self) -> &str {
        &self.target_preprocessing_description
    }

    pub fn observation_model_description(&self) -> &str {
        &self.observation_model_description
    }

    fn heap_bytes(&self) -> PidResult<u128> {
        [
            self.source1_preprocessing_description.as_str(),
            self.source2_preprocessing_description.as_str(),
            self.source3_preprocessing_description.as_str(),
            self.target_preprocessing_description.as_str(),
            self.observation_model_description.as_str(),
        ]
        .into_iter()
        .try_fold(0u128, |total, value| {
            total
                .checked_add(value.len() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "PID3 provenance",
                })
        })
    }

    fn try_clone_for_report(&self) -> PidResult<Self> {
        Ok(Self {
            source1_preprocessing_description: try_owned_text(
                "PID3 report provenance",
                &self.source1_preprocessing_description,
            )?,
            source2_preprocessing_description: try_owned_text(
                "PID3 report provenance",
                &self.source2_preprocessing_description,
            )?,
            source3_preprocessing_description: try_owned_text(
                "PID3 report provenance",
                &self.source3_preprocessing_description,
            )?,
            target_preprocessing_description: try_owned_text(
                "PID3 report provenance",
                &self.target_preprocessing_description,
            )?,
            observation_model_description: try_owned_text(
                "PID3 report provenance",
                &self.observation_model_description,
            )?,
        })
    }
}

fn try_owned_text(operation: &'static str, value: &str) -> PidResult<String> {
    let mut owned = String::new();
    owned
        .try_reserve_exact(value.len())
        .map_err(|_| PidError::AllocationFailed {
            operation,
            requested_bytes: value.len() as u128,
        })?;
    owned.push_str(value);
    Ok(owned)
}

/// Full experimental PID3 result with caller-declared preprocessing and observation provenance.
#[derive(Debug)]
#[non_exhaustive]
#[cfg(feature = "research-mixed-dimension-pid3")]
pub struct Pid3Report {
    pub result: Pid3Result,
    pub provenance: Pid3Provenance,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
}

/// One continuous PID3 redundancy coordinate with its branch ambient dimensions.
///
/// `value` is present only when every branch in the antichain has the same ambient dimension.
/// This dimension check is necessary but does not certify compatible intrinsic dimensions,
/// reference measures, or leading-order intersection behavior.
#[derive(Debug)]
#[non_exhaustive]
pub struct IncompletePid3Redundancy {
    pub antichain: Antichain3,
    pub branch_dimensions: Vec<usize>,
    pub value: Option<f64>,
}

/// One PID3 atom derived from the exactly available redundancy coordinates.
#[derive(Debug)]
#[non_exhaustive]
pub struct IncompletePid3Atom {
    pub antichain: Antichain3,
    pub value: Option<f64>,
    /// Every unavailable redundancy coordinate with a non-zero coefficient in this atom's exact
    /// Möbius expansion, in canonical antichain order.
    pub unavailable_redundancies: Vec<Antichain3>,
}

/// Ambient-dimension-compatible part of a continuous three-source PID lattice.
///
/// This result deliberately does not fill unavailable coordinates with zeros or inferred values.
/// Consequently the available atoms are valid exact linear combinations of the returned
/// redundancy estimates, but they do not by themselves form a complete 18-atom decomposition.
#[derive(Debug)]
#[non_exhaustive]
pub struct IncompletePid3Diagnostic {
    pub n_samples: usize,
    pub k: usize,
    pub metric: Metric,
    pub support_contract: SupportContract,
    pub source_ambient_dimensions: [usize; 3],
    pub target_ambient_dimension: usize,
    pub status: IncompletePid3Status,
    /// Deterministically ordered scientific limitations that must travel with the estimates.
    pub warnings: Vec<&'static str>,
    pub redundancies: Vec<IncompletePid3Redundancy>,
    pub atoms: Vec<IncompletePid3Atom>,
}

/// Scientific status of an incomplete three-source continuous diagnostic.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum IncompletePid3Status {
    /// Ambient branch dimensions match for returned coordinates, but intrinsic scaling,
    /// reference measures, and leading-order branch intersections remain unvalidated.
    AmbientDimensionCompatibleButUnvalidated,
}

const PARTIAL_PID3_WARNINGS: [&str; 4] = [
    "the support contract is caller-declared; sample checks can identify incompatible observations but cannot determine their cause or verify population support",
    "equal ambient branch dimensions do not establish equal intrinsic dimensions, compatible reference measures, or regular leading-order intersections",
    "relative source units and preprocessing are part of the shared-exclusions estimand and must be recorded alongside every reported result",
    "unavailable coordinates are not imputed; available atoms do not form a complete 18-atom decomposition",
];

/// Partial PID3 availability result with caller-declared preprocessing/observation provenance.
#[derive(Debug)]
#[non_exhaustive]
pub struct IncompletePid3Report {
    pub result: IncompletePid3Diagnostic,
    pub provenance: Pid3Provenance,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
}

impl IncompletePid3Diagnostic {
    pub fn redundancy(&self, antichain: Antichain3) -> Option<&IncompletePid3Redundancy> {
        self.redundancies
            .iter()
            .find(|redundancy| redundancy.antichain == antichain)
    }

    pub fn atom(&self, antichain: Antichain3) -> Option<&IncompletePid3Atom> {
        self.atoms.iter().find(|atom| atom.antichain == antichain)
    }
}

#[cfg(feature = "research-mixed-dimension-pid3")]
impl Pid3Result {
    pub fn redundancy(&self, antichain: Antichain3) -> Option<f64> {
        self.redundancies
            .iter()
            .find(|r| r.antichain == antichain)
            .map(|r| r.value)
    }

    pub fn atom(&self, antichain: Antichain3) -> Option<f64> {
        self.atoms
            .iter()
            .find(|a| a.antichain == antichain)
            .map(|a| a.value)
    }
}

/// Full 3-source continuous SxPID using shared exclusions (Ehrlich et al. 2024).
///
/// Computes all 18 PID atoms for three sources by:
/// 1) Estimating `I^sx_∩(T : α)` for every non-empty antichain α on {0,1,2} using the kNN estimator
///    (a KSG-style construction with disjunction neighborhoods).
/// 2) Applying Möbius inversion on the redundancy lattice to obtain the PID atoms Π^sx(α).
///
/// Units: nats (natural logarithm).
///
/// # Experimental mixed-dimensional lattice
///
/// A full three-source lattice necessarily includes singleton-vs-pair antichains such as
/// `{{S0}, {S1,S2}}`. Their source neighborhoods live in different ambient dimensions, so their
/// raw small-ball radii do not share a dimension-independent reference scaling. Consequently this
/// entry point rejects the default configuration. Set
/// [`Pid3Config::experimental_allow_mixed_dimension_lattice`] to `true` only to reproduce reference
/// fixtures or run explicitly labelled diagnostics. That opt-in does not make the resulting atoms
/// validated mixed-dimensional scientific estimates. Equal dimensions among the three singleton
/// source matrices would not remove the singleton-vs-pair mismatch, nor prove compatible intrinsic
/// dimensions or reference measures.
///
/// Relative source units/preprocessing are part of the continuous shared-exclusions estimand;
/// record them and do not compare atoms across schemes. Exact deterministic continuous maps have
/// infinite MI and require a justified noise model or a suitable discrete/mixed estimator.
/// Collapsed or ambiguous positive k-th-neighbor shells are rejected rather than assigned a silent
/// tie convention.
#[cfg(feature = "research-mixed-dimension-pid3")]
pub fn pid3_isx(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
) -> PidResult<Pid3Result> {
    pid3_isx_with_budget(s0, s1, s2, t, cfg, ResourceBudget::default())
}

/// Full research PID3 under an explicit aggregate memory, work, and thread budget.
#[cfg(feature = "research-mixed-dimension-pid3")]
pub fn pid3_isx_with_budget(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    budget: ResourceBudget,
) -> PidResult<Pid3Result> {
    validate_pid3_common("pid3_isx", s0, s1, s2, t, cfg)?;
    if !cfg.experimental_allow_mixed_dimension_lattice {
        return Err(PidError::InvalidConfig {
            context: "pid3_isx",
            message: "the full continuous PID3 lattice compares mixed-dimensional singleton and pair source neighborhoods; set experimental_allow_mixed_dimension_lattice=true only for reference reproduction or explicitly labelled diagnostics",
        });
    }
    let n = t.nrows();
    validate_support_contract("pid3_isx", cfg.support_contract, cfg.metric)?;
    let threads = effective_thread_count(budget.max_threads, n);
    let estimate = pid3_resource_estimate_for_threads(s0, s1, s2, t, cfg, threads)?;
    budget.check("pid3_isx", estimate)?;
    validate_observed_sample_conditions_with_budget(
        "pid3_isx",
        cfg.support_contract,
        &[s0, s1, s2, t],
        budget,
    )?;
    crate::par::with_thread_budget(threads, || {
        pid3_isx_prevalidated(s0, s1, s2, t, cfg, budget)
    })
}

#[cfg(feature = "research-mixed-dimension-pid3")]
fn pid3_isx_prevalidated(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    budget: ResourceBudget,
) -> PidResult<Pid3Result> {
    let n = t.nrows();
    let k = cfg.k;

    let sources = [
        symmetric_distances_with_budget(s0, cfg.metric, budget)?,
        symmetric_distances_with_budget(s1, cfg.metric, budget)?,
        symmetric_distances_with_budget(s2, cfg.metric, budget)?,
    ];
    let target = symmetric_distances_with_budget(t, cfg.metric, budget)?;

    let antichains = antichains_3();
    let mut redundancies = try_vec_with_capacity("PID3 redundancies", antichains.len(), budget)?;
    for &a in antichains {
        let val = redundancy_for_antichain("pid3_isx", &sources, &target, a, cfg, budget)?;
        redundancies.push(Pid3Redundancy {
            antichain: a,
            value: val,
        });
    }

    let atoms = mobius_inversion_atoms(antichains, &redundancies, budget)?;
    let mut warnings = try_vec_with_capacity("PID3 warnings", FULL_PID3_WARNINGS.len(), budget)?;
    warnings.extend(FULL_PID3_WARNINGS);
    Ok(Pid3Result {
        n_samples: n,
        k,
        metric: cfg.metric,
        support_contract: cfg.support_contract,
        source_ambient_dimensions: [s0.ncols(), s1.ncols(), s2.ncols()],
        target_ambient_dimension: t.ncols(),
        method_status: Pid3MethodStatus::ExperimentalMixedDimension,
        warnings,
        redundancies,
        atoms,
    })
}

/// Compute full experimental PID3 while preserving caller-declared provenance.
///
/// Provenance construction checks only for nonempty descriptions. Neither that structural check
/// nor this wrapper validates the mixed-dimensional estimator, population support, preprocessing
/// choice, or observation model.
#[cfg(feature = "research-mixed-dimension-pid3")]
pub fn pid3_isx_report(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    provenance: &Pid3Provenance,
) -> PidResult<Pid3Report> {
    pid3_isx_report_with_budget(s0, s1, s2, t, cfg, provenance, ResourceBudget::default())
}

/// Full research PID3 report under an explicit aggregate resource budget.
#[cfg(feature = "research-mixed-dimension-pid3")]
pub fn pid3_isx_report_with_budget(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    provenance: &Pid3Provenance,
    budget: ResourceBudget,
) -> PidResult<Pid3Report> {
    validate_pid3_common("pid3_isx", s0, s1, s2, t, cfg)?;
    let threads = effective_thread_count(budget.max_threads, t.nrows());
    let resource_estimate = pid3_report_resource_estimate(s0, s1, s2, t, cfg, provenance, threads)?;
    budget.check("pid3_isx_report", resource_estimate)?;
    Ok(Pid3Report {
        result: pid3_isx_with_budget(s0, s1, s2, t, cfg, budget)?,
        provenance: provenance.try_clone_for_report()?,
        resource_estimate,
        resource_budget: budget,
    })
}

/// Estimate only the ambient-dimension-compatible coordinates of continuous three-source PID.
///
/// For each redundancy antichain, the ambient dimension of a branch is the sum of the column
/// counts of the sources in that branch. A redundancy is estimated only when all of its branches
/// have the same dimension. Each atom is then expanded exactly as an integer linear combination
/// of redundancy coordinates by Möbius inversion. Its value is returned only when every
/// non-zero-coefficient dependency is available; otherwise `value` is `None` and
/// [`IncompletePid3Atom::unavailable_redundancies`] lists the exact missing coordinates.
///
/// This is a conservative availability API, not a proof of estimator consistency. Equal ambient
/// dimensions do not establish equal intrinsic dimensions, compatible reference measures, or
/// regular leading-order intersections. The declared support contract remains a caller assertion,
/// and observations with exact ties are conservatively rejected as incompatible with ideal
/// i.i.d., unrounded continuous-sample conditions, without inferring their cause or population
/// support.
///
/// # Errors
///
/// Returns an error for incompatible shapes or configuration, an unsupported or unspecified
/// support contract, observations incompatible with ideal continuous-sample conditions, invalid
/// `k`, or degenerate or ambiguous k-nearest-neighbor geometry in any redundancy that is actually
/// estimated.
pub fn incomplete_pid3_diagnostic(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
) -> PidResult<IncompletePid3Diagnostic> {
    incomplete_pid3_diagnostic_with_budget(s0, s1, s2, t, cfg, ResourceBudget::default())
}

/// Incomplete PID3 diagnostic under an explicit aggregate resource budget.
pub fn incomplete_pid3_diagnostic_with_budget(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    budget: ResourceBudget,
) -> PidResult<IncompletePid3Diagnostic> {
    const CONTEXT: &str = "incomplete_pid3_diagnostic";

    validate_pid3_common(CONTEXT, s0, s1, s2, t, cfg)?;
    let n = t.nrows();
    validate_support_contract(CONTEXT, cfg.support_contract, cfg.metric)?;
    let threads = effective_thread_count(budget.max_threads, n);
    let estimate = incomplete_pid3_resource_estimate_for_threads(s0, s1, s2, t, cfg, threads)?;
    budget.check(CONTEXT, estimate)?;
    validate_observed_sample_conditions_with_budget(
        CONTEXT,
        cfg.support_contract,
        &[s0, s1, s2, t],
        budget,
    )?;
    crate::par::with_thread_budget(threads, || {
        incomplete_pid3_prevalidated(s0, s1, s2, t, cfg, budget)
    })
}

fn incomplete_pid3_prevalidated(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    budget: ResourceBudget,
) -> PidResult<IncompletePid3Diagnostic> {
    const CONTEXT: &str = "incomplete_pid3_diagnostic";
    let n = t.nrows();
    let k = cfg.k;

    let sources = [
        symmetric_distances_with_budget(s0, cfg.metric, budget)?,
        symmetric_distances_with_budget(s1, cfg.metric, budget)?,
        symmetric_distances_with_budget(s2, cfg.metric, budget)?,
    ];
    let target = symmetric_distances_with_budget(t, cfg.metric, budget)?;
    let source_dimensions = [s0.ncols(), s1.ncols(), s2.ncols()];
    let antichains = antichains_3();

    let mut redundancies =
        try_vec_with_capacity("incomplete PID3 redundancies", antichains.len(), budget)?;
    for &antichain in antichains {
        let branch_dimensions = antichain_branch_dimensions(antichain, source_dimensions, budget)?;
        let compatible = branch_dimensions
            .windows(2)
            .all(|dimensions| dimensions[0] == dimensions[1]);
        let value = if compatible {
            Some(redundancy_for_antichain(
                CONTEXT, &sources, &target, antichain, cfg, budget,
            )?)
        } else {
            None
        };
        redundancies.push(IncompletePid3Redundancy {
            antichain,
            branch_dimensions,
            value,
        });
    }

    let atoms = partial_mobius_inversion_atoms(antichains, &redundancies, budget)?;
    let mut warnings = try_vec_with_capacity(
        "incomplete PID3 warnings",
        PARTIAL_PID3_WARNINGS.len(),
        budget,
    )?;
    warnings.extend(PARTIAL_PID3_WARNINGS);
    Ok(IncompletePid3Diagnostic {
        n_samples: n,
        k,
        metric: cfg.metric,
        support_contract: cfg.support_contract,
        source_ambient_dimensions: source_dimensions,
        target_ambient_dimension: t.ncols(),
        status: IncompletePid3Status::AmbientDimensionCompatibleButUnvalidated,
        warnings,
        redundancies,
        atoms,
    })
}

/// Compute the conservative partial PID3 surface while preserving caller-declared provenance.
///
/// Provenance is checked only for nonempty descriptions and does not establish estimator
/// consistency, support, preprocessing validity, or an observation model.
pub fn incomplete_pid3_report(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    provenance: &Pid3Provenance,
) -> PidResult<IncompletePid3Report> {
    incomplete_pid3_report_with_budget(s0, s1, s2, t, cfg, provenance, ResourceBudget::default())
}

/// Incomplete PID3 report under an explicit aggregate resource budget.
pub fn incomplete_pid3_report_with_budget(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    provenance: &Pid3Provenance,
    budget: ResourceBudget,
) -> PidResult<IncompletePid3Report> {
    validate_pid3_common("incomplete_pid3_diagnostic", s0, s1, s2, t, cfg)?;
    let threads = effective_thread_count(budget.max_threads, t.nrows());
    let resource_estimate =
        incomplete_pid3_report_resource_estimate(s0, s1, s2, t, cfg, provenance, threads)?;
    budget.check("incomplete_pid3_report", resource_estimate)?;
    Ok(IncompletePid3Report {
        result: incomplete_pid3_diagnostic_with_budget(s0, s1, s2, t, cfg, budget)?,
        provenance: provenance.try_clone_for_report()?,
        resource_estimate,
        resource_budget: budget,
    })
}

/// Conservative preflight for the complete four-matrix continuous PID3 working set.
#[cfg(feature = "research-mixed-dimension-pid3")]
pub fn pid3_resource_estimate(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
) -> PidResult<ResourceEstimate> {
    pid3_resource_estimate_for_threads(
        s0,
        s1,
        s2,
        t,
        cfg,
        effective_thread_count(ResourceBudget::default().max_threads, t.nrows()),
    )
}

/// PID3 preflight including simultaneous matrices and per-worker stack/scratch reservations.
#[cfg_attr(
    not(feature = "research-mixed-dimension-pid3"),
    expect(
        unreachable_pub,
        reason = "shared implementation is public only when the full research surface is enabled"
    )
)]
pub fn pid3_resource_estimate_for_threads(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    _cfg: &Pid3Config,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "continuous PID3";
    if max_threads == 0 {
        return Err(PidError::ResourceLimitExceeded {
            operation: OPERATION,
            resource: "threads",
            requested: 1,
            limit: 0,
        });
    }
    if s0.nrows() != s1.nrows() || s0.nrows() != s2.nrows() || s0.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: OPERATION,
            left_rows: s0.nrows(),
            right_rows: if s1.nrows() != s0.nrows() {
                s1.nrows()
            } else if s2.nrows() != s0.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n_usize = t.nrows();
    let n = n_usize as u128;
    let pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let dimensions = [s0, s1, s2, t]
        .into_iter()
        .try_fold(0u128, |total, input| {
            total
                .checked_add(input.ncols() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })
        })?;
    let matrix_bytes = pairs
        .checked_mul(4)
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    // Every continuous PID3 redundancy term uses the coefficient-cancelling integer KSG form;
    // shifted harmonic prefixes retain the previous n+1 binary64 allocation shape.
    let harmonic_bytes = n
        .checked_add(1)
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let active_threads = effective_thread_count(max_threads, n_usize) as u128;
    let worker_scratch = active_threads
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_mul(std::mem::size_of::<DistIsx3>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    #[cfg(feature = "parallel")]
    let worker_stacks = active_threads
        .checked_mul(WORKER_STACK_BYTES as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    #[cfg(not(feature = "parallel"))]
    let worker_stacks = 0;
    #[cfg(feature = "parallel")]
    let ordered_map_intermediate = n
        .checked_mul(std::mem::size_of::<PidResult<f64>>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    #[cfg(not(feature = "parallel"))]
    let ordered_map_intermediate = 0;
    let local_terms =
        n.checked_mul(std::mem::size_of::<f64>() as u128)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    let lattice_len = antichains_3().len() as u128;
    let lattice_workspace = lattice_len
        .checked_mul(lattice_len)
        .and_then(|value| value.checked_mul(std::mem::size_of::<i64>() as u128))
        .and_then(|value| {
            value.checked_add(lattice_len.checked_mul(std::mem::size_of::<Vec<i64>>() as u128)?)
        })
        .and_then(|value| {
            value.checked_add(
                lattice_len
                    .checked_mul(lattice_len)?
                    .checked_mul(std::mem::size_of::<Antichain3>() as u128)?,
            )
        })
        .and_then(|value| {
            value.checked_add(lattice_len.checked_mul(
                (std::mem::size_of::<IncompletePid3Redundancy>()
                    + std::mem::size_of::<IncompletePid3Atom>()) as u128,
            )?)
        })
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let estimator_peak = matrix_bytes
        .checked_add(harmonic_bytes)
        .and_then(|value| value.checked_add(worker_scratch))
        .and_then(|value| value.checked_add(worker_stacks))
        .and_then(|value| value.checked_add(ordered_map_intermediate))
        .and_then(|value| value.checked_add(local_terms))
        .and_then(|value| value.checked_add(lattice_workspace))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let support_peak = [s0, s1, s2, t]
        .into_iter()
        .map(pid3_cardinality_estimate)
        .try_fold(ResourceEstimate::ZERO, |peak, estimate| {
            let estimate = estimate?;
            Ok::<_, PidError>(ResourceEstimate {
                estimated_bytes: peak.estimated_bytes.max(estimate.estimated_bytes),
                pairwise_distances: 0,
                operations_hint: peak
                    .operations_hint
                    .checked_add(estimate.operations_hint)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?,
            })
        })?;
    let distance_operations = pairs
        .checked_mul(dimensions)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let redundancy_operations = pairs
        .checked_mul(2)
        .and_then(|value| value.checked_mul(lattice_len))
        .and_then(|value| value.checked_mul(18))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: estimator_peak.max(support_peak.estimated_bytes),
        pairwise_distances: pairs.checked_mul(4).ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?,
        operations_hint: distance_operations
            .checked_add(redundancy_operations)
            .and_then(|value| value.checked_add(support_peak.operations_hint))
            .and_then(|value| value.checked_add(lattice_len.pow(3)))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?,
    })
}

/// Conservative resource preflight for the incomplete diagnostic surface.
pub fn incomplete_pid3_resource_estimate(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
) -> PidResult<ResourceEstimate> {
    incomplete_pid3_resource_estimate_for_threads(
        s0,
        s1,
        s2,
        t,
        cfg,
        effective_thread_count(ResourceBudget::default().max_threads, t.nrows()),
    )
}

/// Incomplete PID3 preflight with explicit per-worker reservations.
pub fn incomplete_pid3_resource_estimate_for_threads(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    // The compatible subset depends on source dimensions. Bounding it by the complete 18-node
    // lattice keeps preflight valid even if future availability rules admit more coordinates.
    pid3_resource_estimate_for_threads(s0, s1, s2, t, cfg, max_threads)
}

#[cfg(feature = "research-mixed-dimension-pid3")]
fn pid3_report_resource_estimate(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    provenance: &Pid3Provenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    add_pid3_report_retained(
        "pid3_isx_report",
        pid3_resource_estimate_for_threads(s0, s1, s2, t, cfg, max_threads)?,
        provenance,
        std::mem::size_of::<Pid3Report>(),
    )
}

fn incomplete_pid3_report_resource_estimate(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
    provenance: &Pid3Provenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    add_pid3_report_retained(
        "incomplete_pid3_report",
        incomplete_pid3_resource_estimate_for_threads(s0, s1, s2, t, cfg, max_threads)?,
        provenance,
        std::mem::size_of::<IncompletePid3Report>(),
    )
}

fn add_pid3_report_retained(
    operation: &'static str,
    mut estimate: ResourceEstimate,
    provenance: &Pid3Provenance,
    report_size: usize,
) -> PidResult<ResourceEstimate> {
    estimate.estimated_bytes = estimate
        .estimated_bytes
        .checked_add(provenance.heap_bytes()?)
        .and_then(|value| value.checked_add(report_size as u128))
        .ok_or(PidError::SizeOverflow { operation })?;
    Ok(estimate)
}

fn pid3_cardinality_estimate(input: MatRef<'_>) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "PID3 support cardinalities";
    let n = input.nrows() as u128;
    let dimensions = input.ncols() as u128;
    let coordinates = n.checked_mul(dimensions).ok_or(PidError::SizeOverflow {
        operation: OPERATION,
    })?;
    let log_n = if input.nrows() <= 1 {
        1u128
    } else {
        (usize::BITS - (input.nrows() - 1).leading_zeros()) as u128
    };
    Ok(ResourceEstimate {
        estimated_bytes: coordinates
            .checked_mul(2 * std::mem::size_of::<u64>() as u128)
            .and_then(|value| {
                value.checked_add(n.checked_mul(std::mem::size_of::<Vec<u64>>() as u128)?)
            })
            .and_then(|value| {
                value.checked_add(
                    dimensions.checked_mul(
                        std::mem::size_of::<CoordinateCardinalityDiagnostics>() as u128,
                    )?,
                )
            })
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?,
        pairwise_distances: 0,
        operations_hint: coordinates
            .checked_mul(log_n)
            .and_then(|value| value.checked_mul(2))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?,
    })
}

fn validate_pid3_common(
    context: &'static str,
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid3Config,
) -> PidResult<()> {
    if s0.nrows() != s1.nrows() || s0.nrows() != s2.nrows() || s0.nrows() != t.nrows() {
        let n = s0.nrows();
        let right_rows = if s1.nrows() != n {
            s1.nrows()
        } else if s2.nrows() != n {
            s2.nrows()
        } else {
            t.nrows()
        };
        return Err(PidError::RowCountMismatch {
            context,
            left_rows: n,
            right_rows,
        });
    }
    if s0.ncols() == 0 || s1.ncols() == 0 || s2.ncols() == 0 || t.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "inputs must have at least 1 column",
        });
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }
    if cfg.k == 0 || s0.nrows() <= cfg.k {
        return Err(PidError::InvalidK {
            k: cfg.k,
            n_samples: s0.nrows(),
        });
    }
    if cfg.metric != Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context,
            message: "PID3 ISX is restricted to the cited Metric::Chebyshev (L∞) convention; other metrics are research-gated",
        });
    }
    Ok(())
}

fn antichain_branch_dimensions(
    antichain: Antichain3,
    source_dimensions: [usize; 3],
    budget: ResourceBudget,
) -> PidResult<Vec<usize>> {
    let mut dimensions = try_vec_with_capacity("PID3 branch dimensions", antichain.len(), budget)?;
    for &source_set in antichain.sets() {
        let mut dimension = 0usize;
        for (source, &source_dimension) in source_dimensions.iter().enumerate() {
            if source_set & (1u8 << source) != 0 {
                dimension =
                    dimension
                        .checked_add(source_dimension)
                        .ok_or(PidError::InvalidConfig {
                            context: "incomplete_pid3_diagnostic",
                            message: "source branch dimension overflow",
                        })?;
            }
        }
        dimensions.push(dimension);
    }
    Ok(dimensions)
}

fn redundancy_for_antichain(
    context: &'static str,
    sources: &[SymmetricDistanceMatrix; 3],
    target: &SymmetricDistanceMatrix,
    antichain: Antichain3,
    cfg: &Pid3Config,
    budget: ResourceBudget,
) -> PidResult<f64> {
    let n = target.n();
    let k = cfg.k;
    let kth = k - 1;

    let shifted_harmonics = shifted_harmonic_table(n)?;

    // Per-point local term. Each point reads the shared (immutable) distance matrices and
    // allocates its own scratch, so the closure is pure and order-independent. Terms are
    // collected **in index order** and summed left-to-right exactly as the serial loop did,
    // so the `parallel` path is bit-for-bit identical to serial (see `par::map_index_ordered`).
    let local = |i: usize| -> PidResult<f64> {
        let mut scratch = try_vec_with_capacity(
            "PID3 per-query distance scratch",
            n.saturating_sub(1),
            budget,
        )?;
        for j in 0..n {
            if i == j {
                continue;
            }
            let d0 = sources[0].get(i, j);
            let d1 = sources[1].get(i, j);
            let d2 = sources[2].get(i, j);
            let ds_disj = source_disjunction_distance(antichain, d0, d1, d2);
            let dt_ij = target.get(i, j);
            scratch.push(DistIsx3 {
                joint: dt_ij.max(ds_disj),
                ds: ds_disj,
                dt: dt_ij,
            });
        }

        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps_raw = scratch[kth].joint;
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: pid3_non_positive_radius_context(context),
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(context, i, k, eps_raw, interior_count, boundary_count)?;
        let eps = strict_radius(eps_raw);

        // Counts exclude self; estimator uses inclusive counts.
        let mut n_alpha = 1usize;
        let mut n_t = 1usize;
        for d in &scratch {
            if d.ds <= eps {
                n_alpha += 1;
            }
            if d.dt <= eps {
                n_t += 1;
            }
        }

        Ok(ksg_local_harmonic_term(
            &shifted_harmonics,
            k,
            n,
            n_alpha,
            n_t,
        ))
    };

    let terms = crate::par::map_index_ordered(n, local)?;
    let sum = compensated_sum(terms.iter().copied());
    Ok(sum / (n as f64))
}

fn pid3_non_positive_radius_context(context: &'static str) -> &'static str {
    match context {
        "incomplete_pid3_diagnostic" => "incomplete_pid3_diagnostic: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
        _ => "pid3_isx: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
    }
}

#[inline]
fn source_disjunction_distance(antichain: Antichain3, d0: f64, d1: f64, d2: f64) -> f64 {
    let mut best = f64::INFINITY;
    for &m in antichain.sets() {
        let mut v = 0.0f64;
        if (m & 0b001) != 0 {
            v = v.max(d0);
        }
        if (m & 0b010) != 0 {
            v = v.max(d1);
        }
        if (m & 0b100) != 0 {
            v = v.max(d2);
        }
        best = best.min(v);
    }
    best
}

#[cfg(feature = "research-mixed-dimension-pid3")]
fn mobius_inversion_atoms(
    antichains: &[Antichain3],
    redundancies: &[Pid3Redundancy],
    budget: ResourceBudget,
) -> PidResult<Vec<Pid3Atom>> {
    if antichains.len() != redundancies.len() {
        return Err(PidError::InvalidConfig {
            context: "mobius_inversion_atoms",
            message: "antichains/redundancies length mismatch",
        });
    }
    let coefficients = mobius_redundancy_coefficients(antichains, budget)?;
    let mut atoms = try_vec_with_capacity("PID3 atoms", antichains.len(), budget)?;
    for (idx, &a) in antichains.iter().enumerate() {
        let value = compensated_sum(
            coefficients[idx]
                .iter()
                .zip(redundancies)
                .filter(|(coefficient, _)| **coefficient != 0)
                .map(|(&coefficient, redundancy)| coefficient as f64 * redundancy.value),
        );
        if !value.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "mobius_inversion_atoms",
            });
        }
        atoms.push(Pid3Atom {
            antichain: a,
            value,
        });
    }
    Ok(atoms)
}

fn partial_mobius_inversion_atoms(
    antichains: &[Antichain3],
    redundancies: &[IncompletePid3Redundancy],
    budget: ResourceBudget,
) -> PidResult<Vec<IncompletePid3Atom>> {
    if antichains.len() != redundancies.len() {
        return Err(PidError::InvalidConfig {
            context: "partial_mobius_inversion_atoms",
            message: "antichains/redundancies length mismatch",
        });
    }

    let coefficients = mobius_redundancy_coefficients(antichains, budget)?;
    let mut atoms = try_vec_with_capacity("incomplete PID3 atoms", antichains.len(), budget)?;
    for (atom_index, &antichain) in antichains.iter().enumerate() {
        let mut unavailable_redundancies = try_vec_with_capacity(
            "incomplete PID3 unavailable dependencies",
            antichains.len(),
            budget,
        )?;
        for (redundancy_index, &coefficient) in coefficients[atom_index].iter().enumerate() {
            if coefficient != 0 && redundancies[redundancy_index].value.is_none() {
                unavailable_redundancies.push(antichains[redundancy_index]);
            }
        }

        let value = if unavailable_redundancies.is_empty() {
            let mut terms =
                try_vec_with_capacity("incomplete PID3 Mobius terms", antichains.len(), budget)?;
            for (redundancy_index, &coefficient) in coefficients[atom_index].iter().enumerate() {
                if coefficient == 0 {
                    continue;
                }
                let value =
                    redundancies[redundancy_index]
                        .value
                        .ok_or(PidError::InvalidConfig {
                            context: "partial_mobius_inversion_atoms",
                            message: "available atom has an unavailable redundancy dependency",
                        })?;
                terms.push((coefficient as f64) * value);
            }
            Some(compensated_sum(terms))
        } else {
            None
        };

        atoms.push(IncompletePid3Atom {
            antichain,
            value,
            unavailable_redundancies,
        });
    }
    Ok(atoms)
}

fn mobius_redundancy_coefficients(
    antichains: &[Antichain3],
    budget: ResourceBudget,
) -> PidResult<Vec<Vec<i64>>> {
    let n = antichains.len();
    let topo = topo_order(antichains, budget)?;
    if topo.len() != n {
        return Err(PidError::InvalidConfig {
            context: "mobius_redundancy_coefficients",
            message: "topological sort failed",
        });
    }

    let mut coefficients = try_vec_with_capacity("PID3 Mobius coefficient rows", n, budget)?;
    for _ in 0..n {
        coefficients.push(try_vec_filled(
            "PID3 Mobius coefficient row",
            n,
            0i64,
            budget,
        )?);
    }
    for (position, &atom_index) in topo.iter().enumerate() {
        coefficients[atom_index][atom_index] = 1;
        for &lower_atom_index in &topo[..position] {
            if !leq(antichains[lower_atom_index], antichains[atom_index]) {
                continue;
            }
            let (atom_coefficients, lower_atom_coefficients) = if atom_index < lower_atom_index {
                let (before_lower, from_lower) = coefficients.split_at_mut(lower_atom_index);
                (&mut before_lower[atom_index], &from_lower[0])
            } else {
                let (before_atom, from_atom) = coefficients.split_at_mut(atom_index);
                (&mut from_atom[0], &before_atom[lower_atom_index])
            };
            for (atom_coefficient, &lower_atom_coefficient) in atom_coefficients
                .iter_mut()
                .zip(lower_atom_coefficients.iter())
            {
                *atom_coefficient = atom_coefficient.checked_sub(lower_atom_coefficient).ok_or(
                    PidError::InvalidConfig {
                        context: "mobius_redundancy_coefficients",
                        message: "integer coefficient overflow",
                    },
                )?;
            }
        }
    }
    Ok(coefficients)
}

fn topo_order(antichains: &[Antichain3], budget: ResourceBudget) -> PidResult<Vec<usize>> {
    let mut remaining =
        try_vec_with_capacity("PID3 topological remaining set", antichains.len(), budget)?;
    remaining.extend(0..antichains.len());
    let mut out = try_vec_with_capacity("PID3 topological order", remaining.len(), budget)?;
    while !remaining.is_empty() {
        let mut mins = try_vec_with_capacity("PID3 topological minima", remaining.len(), budget)?;
        'outer: for &i in &remaining {
            for &j in &remaining {
                if i == j {
                    continue;
                }
                if leq(antichains[j], antichains[i]) {
                    continue 'outer;
                }
            }
            mins.push(i);
        }
        mins.sort_unstable_by(|&a, &b| antichains[a].cmp(&antichains[b]));
        let chosen = *mins.first().ok_or(PidError::InvalidConfig {
            context: "mobius_redundancy_coefficients",
            message: "topological sort found no minimal antichain",
        })?;
        out.push(chosen);
        remaining.retain(|&x| x != chosen);
    }
    Ok(out)
}

#[inline]
fn leq(a: Antichain3, b: Antichain3) -> bool {
    // a ⪯ b iff for every set B in b, there exists A in a with A ⊆ B.
    for &b_set in b.sets() {
        let mut found = false;
        for &a_set in a.sets() {
            if (a_set & b_set) == a_set {
                found = true;
                break;
            }
        }
        if !found {
            return false;
        }
    }
    true
}

fn antichains_3() -> &'static [Antichain3] {
    // Canonical order: increasing number of sets, then lexicographic by mask.
    const ANTICHAINS: [Antichain3; 18] = [
        Antichain3 {
            sets: [0b001, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b010, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b100, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b011, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b101, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b110, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b111, 0, 0],
            len: 1,
        },
        Antichain3 {
            sets: [0b001, 0b010, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b001, 0b100, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b001, 0b110, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b010, 0b100, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b010, 0b101, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b011, 0b100, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b011, 0b101, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b011, 0b110, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b101, 0b110, 0],
            len: 2,
        },
        Antichain3 {
            sets: [0b001, 0b010, 0b100],
            len: 3,
        },
        Antichain3 {
            sets: [0b011, 0b101, 0b110],
            len: 3,
        },
    ];
    &ANTICHAINS
}
```

## Artifact: `crates/pid-core/tests/ksg.rs`

SHA-256: `544192cac6c00957e1e05a4cc320c069453060eb1fe676131f83b155c1ee6daa`

```text
#![cfg(feature = "experimental-continuous")]

use pid_core::experimental::continuous::raw_scalars::{
    co_information_pairwise, ksg_local_mi_terms, ksg_mi, ksg_mi_concat_xy,
};
use pid_core::stable::continuous::{KsgConfig, NegativeHandling, SupportContract};
use pid_core::stable::preprocessing::{ConstantColumnPolicy, Standardizer};
use pid_core::{MatRef, PidError};

mod common;

use common::Rng64;

fn gaussian_mi_from_corr(rho: f64) -> f64 {
    let r2 = rho * rho;
    debug_assert!(r2 < 1.0);
    -0.5 * (1.0 - r2).ln()
}

fn gaussian_channel_mi(sigma: f64) -> f64 {
    debug_assert!(sigma.is_finite());
    debug_assert!(sigma > 0.0);
    0.5 * (1.0 + 1.0 / (sigma * sigma)).ln()
}

#[test]
fn ksg_default_preserves_signed_finite_sample_estimates() {
    assert_eq!(
        KsgConfig::default().negative_handling,
        NegativeHandling::Allow
    );
}

#[test]
fn ksg_default_fails_closed_without_a_support_assertion() {
    let x = MatRef::new(&[0.0, 0.2, 0.5, 0.9], 4, 1).unwrap();
    let y = MatRef::new(&[0.1, 0.35, 0.6, 1.1], 4, 1).unwrap();

    assert!(matches!(
        ksg_mi(x, y, &KsgConfig::default()),
        Err(PidError::SupportContractRequired { .. })
    ));
}

#[test]
fn ksg_exclusive_counts_reach_the_exact_integer_harmonic_local_term() {
    // This fixed sample is a count/arithmetic conformance witness, not evidence for a population
    // support model or estimator calibration. Every coordinate and joint row is unique, and each
    // k=2 joint shell has exactly one strict-interior and one boundary neighbor.
    let x: [f64; 8] = [7.0, 194.0, 144.0, 75.0, 61.0, 138.0, 38.0, 9.0];
    let y: [f64; 8] = [17.0, 48.0, 166.0, 120.0, 2.0, 199.0, 43.0, 93.0];
    let expected_counts = [
        (54.0, 2, 3),
        (119.0, 2, 6),
        (69.0, 2, 2),
        (69.0, 5, 2),
        (54.0, 3, 3),
        (79.0, 4, 1),
        (41.0, 4, 2),
        (66.0, 3, 3),
    ];

    for query in 0..x.len() {
        let mut joint_distances = Vec::with_capacity(x.len() - 1);
        for neighbor in 0..x.len() {
            if query != neighbor {
                let dx = (x[query] - x[neighbor]).abs();
                let dy = (y[query] - y[neighbor]).abs();
                joint_distances.push(dx.max(dy));
            }
        }
        joint_distances.sort_by(f64::total_cmp);
        let radius = joint_distances[1];
        let interior = joint_distances
            .iter()
            .filter(|&&distance| distance < radius)
            .count();
        let boundary = joint_distances
            .iter()
            .filter(|&&distance| distance == radius)
            .count();
        let nx = (0..x.len())
            .filter(|&neighbor| query != neighbor && (x[query] - x[neighbor]).abs() < radius)
            .count();
        let ny = (0..y.len())
            .filter(|&neighbor| query != neighbor && (y[query] - y[neighbor]).abs() < radius)
            .count();

        assert_eq!((interior, boundary), (1, 1), "query {query}");
        assert_eq!((radius, nx, ny), expected_counts[query], "query {query}");
    }

    let x = MatRef::new(&x, 8, 1).unwrap();
    let y = MatRef::new(&y, 8, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional()
        .with_k(2)
        .with_negative_handling(NegativeHandling::Allow);
    let terms = ksg_local_mi_terms(x, y, &config).unwrap();

    assert_eq!(terms.len(), 8);
    assert_eq!(
        terms[5].to_bits(),
        0x3fe0_4e04_e04e_04e0,
        "row 5 has exact-real target H_7 - H_4 = 107/210; pin the selected binary64 association"
    );
}

#[test]
fn ksg_rejects_every_declared_incompatible_support_type() {
    let x = MatRef::new(&[0.0, 0.2, 0.5, 0.9], 4, 1).unwrap();
    let y = MatRef::new(&[0.1, 0.35, 0.6, 1.1], 4, 1).unwrap();
    let incompatible_contracts = [
        SupportContract::KnownAtomicOrMixed,
        SupportContract::KnownQuantized,
        SupportContract::KnownSingularOrLowerDimensional,
    ];
    for support_contract in incompatible_contracts {
        let config = KsgConfig::default().with_support_contract(support_contract);
        assert!(matches!(
            ksg_mi(x, y, &config),
            Err(PidError::UnsupportedSupportContract { contract, .. })
                if contract == support_contract
        ));
    }
}

#[test]
fn ksg_mi_is_small_for_independent_uniforms() {
    let mut rng = Rng64::new(42);
    let n = 250;
    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    for _ in 0..n {
        x.push(rng.next_f64());
        y.push(rng.next_f64());
    }

    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let mi = ksg_mi(x, y, &cfg).unwrap();

    assert!(mi.is_finite());
    assert!(mi.abs() < 0.6, "expected near-0 MI, got {mi}");
}

#[test]
fn ksg_mi_is_larger_for_noisy_copy() {
    let mut rng = Rng64::new(123);
    let n = 300;
    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    for _ in 0..n {
        let xi = rng.next_f64();
        let yi = xi + 0.05 * rng.normal();
        x.push(xi);
        y.push(yi);
    }

    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let mi = ksg_mi(x, y, &cfg).unwrap();

    assert!(mi.is_finite());
    assert!(mi > 0.5, "expected MI > 0.5 nats, got {mi}");
}

#[test]
fn ksg_mi_matches_gaussian_correlation_approximately() {
    // Analytic MI for 1D jointly-Gaussian variables via correlation:
    // I(X;Y) = -0.5 ln(1 - rho^2)
    let mut rng = Rng64::new(2026);
    let n = 600;
    let sigma_x = 0.5;
    let sigma_y = 0.8;

    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.normal();
        x.push(base + sigma_x * rng.normal());
        y.push(base + sigma_y * rng.normal());
    }

    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let (x, _) = Standardizer::fit_transform(x, ConstantColumnPolicy::Error).unwrap();
    let (y, _) = Standardizer::fit_transform(y, ConstantColumnPolicy::Error).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let mi_hat = ksg_mi(x.as_ref(), y.as_ref(), &cfg).unwrap();

    let rho = 1.0 / ((1.0 + sigma_x * sigma_x) * (1.0 + sigma_y * sigma_y)).sqrt();
    let mi_true = gaussian_mi_from_corr(rho);

    assert!(mi_hat.is_finite());
    // The tolerance must stay BELOW the effect size (mi_true ≈ 0.33 nats) or the check is
    // vacuous — a dead-zero estimator, a 2× scale bug, and a bits-for-nats mixup would all
    // pass at 0.35. 0.12 nats is comfortably above the KSG finite-sample error here while
    // excluding all three failure modes; the second assertion pins the zero-collapse case.
    assert!(
        (mi_hat - mi_true).abs() < 0.12,
        "MI mismatch: estimated={mi_hat:.4} true={mi_true:.4} rho={rho:.4}"
    );
    assert!(
        mi_hat > 0.5 * mi_true,
        "MI collapsed toward zero: estimated={mi_hat:.4} true={mi_true:.4}"
    );
}

#[test]
fn exp0_strong_dependence_gaussian_channel_sweep_smoke() {
    // Strong dependence (very large true MI) can break kNN MI even at low dimension.
    // This test is not asserting "perfect accuracy"; it checks:
    // - finiteness (no NaNs/Infs)
    // - broadly increasing MI as sigma shrinks
    // - rough agreement with the analytic Gaussian-channel MI at moderate MI values
    //
    // Analytic: X ~ N(0,1), Y = X + σN, N~N(0,1): I(X;Y) = 0.5 ln(1 + 1/σ²).
    let mut rng = Rng64::new(0x51A7_2026);
    let n = 800;

    let mut x_raw = Vec::with_capacity(n);
    let mut noise = Vec::with_capacity(n);
    for _ in 0..n {
        x_raw.push(rng.normal());
        noise.push(rng.normal());
    }

    let x = MatRef::new(&x_raw, n, 1).unwrap();
    let (x, _) = Standardizer::fit_transform(x, ConstantColumnPolicy::Error).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);

    let sigmas = [1.0, 0.3, 0.1];
    let mut last = None;
    for &sigma in &sigmas {
        let y_raw: Vec<f64> = x_raw
            .iter()
            .zip(noise.iter())
            .map(|(&xi, &ni)| xi + sigma * ni)
            .collect();

        let y = MatRef::new(&y_raw, n, 1).unwrap();
        let (y, _) = Standardizer::fit_transform(y, ConstantColumnPolicy::Error).unwrap();

        let mi_hat = ksg_mi(x.as_ref(), y.as_ref(), &cfg).unwrap();
        let mi_true = gaussian_channel_mi(sigma);

        assert!(mi_hat.is_finite(), "sigma={sigma} mi_hat={mi_hat}");

        if let Some(prev) = last {
            assert!(
                mi_hat >= prev - 0.25,
                "expected MI to increase as sigma shrinks: sigma={sigma} mi_hat={mi_hat} prev={prev}"
            );
        }
        last = Some(mi_hat);

        assert!(
            (mi_hat - mi_true).abs() < 1.0,
            "MI mismatch: sigma={sigma} estimated={mi_hat:.4} true={mi_true:.4}"
        );
    }
}

#[test]
fn exp0_co_information_smoke() {
    // Minimal Experiment 0-ish smoke: CI is finite.
    let mut rng = Rng64::new(999);
    let n = 250;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        let noise = 0.01 * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional();
    let ci = co_information_pairwise(s1, s2, t, &cfg).unwrap();
    assert!(ci.is_finite());
}

#[test]
fn co_information_matches_gaussian_sum_channel_approximately() {
    // S1,S2 ~ N(0,1) independent. T = S1 + S2 + N, N~N(0, sigma^2).
    //
    // Analytic:
    // I(S1;T) = -0.5 ln((1+sigma^2)/(2+sigma^2))
    // I(S1,S2;T) = 0.5 ln((2+sigma^2)/sigma^2)
    // CI = I(S1;T)+I(S2;T)-I(S1,S2;T)
    let mut rng = Rng64::new(2027);
    let n = 700;
    let sigma = 0.6;
    let sigma2 = sigma * sigma;

    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        let noise = sigma * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();
    let (s1, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error).unwrap();
    let (s2, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error).unwrap();
    let (t, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let ci_hat = co_information_pairwise(s1.as_ref(), s2.as_ref(), t.as_ref(), &cfg).unwrap();

    let i_s1_t = -0.5 * ((1.0 + sigma2) / (2.0 + sigma2)).ln();
    let i_s1s2_t = 0.5 * ((2.0 + sigma2) / sigma2).ln();
    let ci_true = 2.0 * i_s1_t - i_s1s2_t;

    assert!(ci_hat.is_finite());
    // Same principle as the MI test above: tolerance below the effect size (|ci_true| ≈ 0.39
    // nats), plus an explicit bound that excludes a zero-collapsed estimator and pins the sign.
    assert!(
        (ci_hat - ci_true).abs() < 0.20,
        "CI mismatch: estimated={ci_hat:.4} true={ci_true:.4}"
    );
    assert!(
        ci_hat < 0.5 * ci_true,
        "CI collapsed toward zero (should be clearly negative): estimated={ci_hat:.4} true={ci_true:.4}"
    );
}

#[test]
fn ksg_rejects_zero_column_inputs() {
    let n = 10;
    let x: Vec<f64> = Vec::new();
    let y: Vec<f64> = Vec::new();
    let x = MatRef::new(&x, n, 0).unwrap();
    let y = MatRef::new(&y, n, 0).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let err = ksg_mi(x, y, &cfg).unwrap_err();
    assert!(
        matches!(err, PidError::InvalidConfig { .. }),
        "unexpected error: {err:?}"
    );
}

#[test]
fn ksg_rejects_every_nonzero_or_nonfinite_tie_epsilon() {
    let n = 20;
    let x: Vec<f64> = (0..n).map(|i| i as f64).collect();
    let y: Vec<f64> = (0..n).map(|i| (i as f64) * 0.5).collect();
    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    for tie_epsilon in [-1.0, 1.0e-12, f64::NAN, f64::INFINITY] {
        let cfg = KsgConfig::assume_regular_full_dimensional()
            .with_k(3)
            .with_tie_epsilon(tie_epsilon)
            .with_negative_handling(NegativeHandling::Allow);
        let err = ksg_mi(x, y, &cfg).unwrap_err();
        assert!(
            matches!(err, PidError::InvalidConfig { .. }),
            "tie_epsilon={tie_epsilon:?}: unexpected error: {err:?}"
        );
    }
}

#[test]
fn ksg_accepts_a_smallest_subnormal_positive_radius() {
    let smallest = f64::from_bits(1);
    let x = [0.0, smallest];
    let y = [0.0, smallest];
    let x = MatRef::new(&x, 2, 1).unwrap();
    let y = MatRef::new(&y, 2, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional()
        .with_k(1)
        .with_negative_handling(NegativeHandling::Allow);

    let estimate = ksg_mi(x, y, &config).unwrap();

    assert!(estimate.is_finite());
}

#[test]
fn ksg_rejects_a_positive_ambiguous_kth_neighbor_shell() {
    // All joint rows are distinct and every non-self distance is positive. At query 0 and k=2,
    // the joint distances are [0.5, 1, 1, 3], making the positive outer shell ambiguous.
    let x = [0.0, 0.5, 1.0, 0.3, 3.0];
    let y = [0.0, 0.4, 0.2, 1.0, 3.0];
    let x = MatRef::new(&x, 5, 1).unwrap();
    let y = MatRef::new(&y, 5, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional()
        .with_k(2)
        .with_negative_handling(NegativeHandling::Allow);

    let error = ksg_mi(x, y, &config).unwrap_err();

    assert!(matches!(
        error,
        PidError::AmbiguousKthNeighborShell {
            query_index: 0,
            k: 2,
            radius: 1.0,
            interior_count: 1,
            boundary_count: 2,
            ..
        }
    ));
}

#[test]
fn ksg_handles_heavily_quantized_data_cleanly() {
    // Stress test: feed heavily-quantized data so that many points coincide exactly
    // (the realistic failure mode when continuous signals are rounded to a coarse grid
    // or recorded by a low-resolution sensor). The contract is that the estimator must
    // EITHER reject a collapsed or ambiguous kNN shell with its structured error OR return a
    // finite, stable estimate — but never panic, never produce NaN/Inf, and never silently report
    // a value that pretends the data was continuous.
    //
    // We sweep quantization coarseness from very coarse (few levels → many exact ties)
    // to fairly fine (few ties). At every coarseness, both outcomes are acceptable; we
    // only forbid panics and non-finite "successes".
    let mut rng = Rng64::new(0xC0FFEE);
    let n = 200;

    let mut x_cont = Vec::with_capacity(n);
    let mut y_cont = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.normal();
        x_cont.push(base);
        y_cont.push(base + 0.3 * rng.normal());
    }

    let cfg = KsgConfig::default()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow)
        .with_support_contract(SupportContract::KnownQuantized);

    // levels=2 is extremely coarse (data collapses onto ~2 grid points per axis →
    // heavy duplication); levels=64 is fine enough that ties are rare.
    for &levels in &[2.0f64, 3.0, 5.0, 16.0, 64.0] {
        let quantize = |v: f64| -> f64 { (v * levels).round() / levels };
        let xq: Vec<f64> = x_cont.iter().map(|&v| quantize(v)).collect();
        let yq: Vec<f64> = y_cont.iter().map(|&v| quantize(v)).collect();

        let x = MatRef::new(&xq, n, 1).unwrap();
        let y = MatRef::new(&yq, n, 1).unwrap();

        assert!(matches!(
            ksg_mi(x, y, &cfg),
            Err(PidError::UnsupportedSupportContract {
                contract: SupportContract::KnownQuantized,
                ..
            })
        ));
    }
}

#[test]
fn ksg_errors_on_duplicate_points() {
    // Duplicate points make the kNN radius zero, which breaks strict-inequality counting.
    let n = 30;
    let x = vec![0.0f64; n];
    let y = vec![0.0f64; n];
    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let err = ksg_mi(x, y, &cfg).unwrap_err();
    assert!(
        matches!(
            err,
            PidError::ObservedContinuousSampleIncompatibility { .. }
        ),
        "unexpected error: {err:?}"
    );
}

#[test]
fn marginal_atoms_are_rejected_even_when_joint_rows_and_shells_are_unique() {
    // Bernoulli X plus a continuously perturbed Y has eight unique joint rows and unique positive
    // k=3 joint shells. The atomic X marginal still invalidates standard continuous KSG.
    let x = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0];
    let y = [0.01, 0.08, 0.19, 0.41, 1.03, 1.11, 1.29, 1.52];
    let x = MatRef::new(&x, 8, 1).unwrap();
    let y = MatRef::new(&y, 8, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(3);

    let error = ksg_mi(x, y, &cfg).unwrap_err();
    assert!(matches!(
        error,
        PidError::ObservedContinuousSampleIncompatibility {
            input_index: 0,
            coordinate: Some(0),
            unique_values: 2,
            max_multiplicity: 4,
            ..
        }
    ));
}

#[test]
fn public_local_and_concat_apis_cannot_bypass_support_preflight() {
    let x1_data = [0.03, 0.17, 0.31, 0.52, 0.76, 1.01, 1.29, 1.62];
    let x2_data = [1.73, 1.41, 1.16, 0.88, 0.63, 0.39, 0.21, 0.07];
    let y_data = [0.12, 0.29, 0.48, 0.71, 0.97, 1.22, 1.51, 1.85];
    let x1 = MatRef::new(&x1_data, 8, 1).unwrap();
    let x2 = MatRef::new(&x2_data, 8, 1).unwrap();
    let y = MatRef::new(&y_data, 8, 1).unwrap();

    assert!(matches!(
        ksg_local_mi_terms(x1, y, &KsgConfig::default()),
        Err(PidError::SupportContractRequired { .. })
    ));
    assert!(matches!(
        ksg_mi_concat_xy(x1, x2, y, &KsgConfig::default()),
        Err(PidError::SupportContractRequired { .. })
    ));

    let tied_data = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0];
    let tied = MatRef::new(&tied_data, 8, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional();
    assert!(matches!(
        ksg_local_mi_terms(tied, y, &cfg),
        Err(PidError::ObservedContinuousSampleIncompatibility { .. })
    ));
    assert!(matches!(
        ksg_mi_concat_xy(tied, x2, y, &cfg),
        Err(PidError::ObservedContinuousSampleIncompatibility { .. })
    ));

    let short_data = [1.73, 1.41, 1.16, 0.88, 0.63, 0.39, 0.21];
    let short = MatRef::new(&short_data, 7, 1).unwrap();
    let invalid_tie_cfg = KsgConfig::assume_regular_full_dimensional().with_tie_epsilon(1.0e-6);
    assert!(matches!(
        ksg_mi_concat_xy(x1, short, y, &invalid_tie_cfg),
        Err(PidError::RowCountMismatch { .. })
    ));
}
```

## Artifact: `crates/pid-core/tests/isx.rs`

SHA-256: `10b40cfc2b37243a28ae38d32917e803094d37e90549a993961a53eeeefd537d`

```text
#![cfg(feature = "experimental-continuous")]

use pid_core::experimental::continuous::raw_scalars::isx_redundancy;
#[cfg(feature = "experimental-heuristics")]
use pid_core::experimental::continuous::raw_scalars::ksg_local_mi_terms;
use pid_core::experimental::continuous::{
    isx_redundancy_report, pid2_isx, IsxConfig, IsxMethod, IsxProvenance, Pid2Config,
};
#[cfg(feature = "experimental-heuristics")]
use pid_core::stable::continuous::{KsgConfig, NegativeHandling};
use pid_core::{MatRef, PidError, ResourceBudget};

mod common;

use common::{csxpid_reference, Rng64};

#[test]
fn exp0_isx_redundancy_smoke() {
    let mut rng = Rng64::new(2026);
    let n = 200;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        let noise = 0.01 * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let red = isx_redundancy(s1, s2, t, &IsxConfig::assume_regular_full_dimensional()).unwrap();
    assert!(red.is_finite());
}

#[test]
fn ehrlich_public_redundancy_propagates_the_inclusive_count_witness() {
    // The private isx.rs regression pins every radius/count and the exact row-5 local term. This
    // integration assertion separately pins the public, index-ordered compensated reduction. It
    // is implementation conformance on fixed rows, not population-support or calibration evidence.
    let s1_data: [f64; 8] = [7.0, 194.0, 144.0, 75.0, 61.0, 138.0, 38.0, 9.0];
    let target_data: [f64; 8] = [17.0, 48.0, 166.0, 120.0, 2.0, 199.0, 43.0, 93.0];
    let s2_data: [f64; 8] = std::array::from_fn(|index| 1_000.0 * s1_data[index] + index as f64);
    let s1 = MatRef::new(&s1_data, 8, 1).unwrap();
    let s2 = MatRef::new(&s2_data, 8, 1).unwrap();
    let target = MatRef::new(&target_data, 8, 1).unwrap();
    let config = IsxConfig {
        k: 2,
        ..IsxConfig::assume_regular_full_dimensional()
    };

    let redundancy = isx_redundancy(s1, s2, target, &config).unwrap();

    assert_eq!(redundancy.to_bits(), 0x3fb5_a35a_35a3_5a3e);
    let correctly_rounded_exact_mean = 71.0_f64 / 840.0;
    assert_eq!(
        correctly_rounded_exact_mean.to_bits(),
        0x3fb5_a35a_35a3_5a36
    );
    assert_ne!(
        redundancy.to_bits(),
        correctly_rounded_exact_mean.to_bits(),
        "the public reduction is a frozen implementation value, not a correct-rounding claim"
    );
}

#[test]
fn isx_report_records_integer_harmonic_estimator_revision() {
    let mut rng = Rng64::new(2_032);
    let n = 64;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut target = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        s1.push(a);
        s2.push(b);
        target.push(0.7 * a - 0.2 * b + 0.01 * rng.normal());
    }
    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let target = MatRef::new(&target, n, 1).unwrap();
    let provenance = IsxProvenance::new(
        "identity source-1 gauge",
        "identity source-2 gauge",
        "identity target transform",
        "continuous observation model",
        "i.i.d. evaluation rows",
        None,
        None,
    )
    .unwrap();

    let report = isx_redundancy_report(
        s1,
        s2,
        target,
        &IsxConfig::assume_regular_full_dimensional(),
        &provenance,
        ResourceBudget::default(),
    )
    .unwrap();

    assert_eq!(
        report.estimand.estimator_revision,
        "strict-unique-shell-integer-harmonic-isx-v4"
    );
}

#[test]
fn public_isx_api_cannot_bypass_support_preflight() {
    let s1_data = [0.03, 0.17, 0.31, 0.52, 0.76, 1.01, 1.29, 1.62];
    let s2_data = [1.73, 1.41, 1.16, 0.88, 0.63, 0.39, 0.21, 0.07];
    let target_data = [0.12, 0.29, 0.48, 0.71, 0.97, 1.22, 1.51, 1.85];
    let s1 = MatRef::new(&s1_data, 8, 1).unwrap();
    let s2 = MatRef::new(&s2_data, 8, 1).unwrap();
    let target = MatRef::new(&target_data, 8, 1).unwrap();
    assert!(matches!(
        isx_redundancy(s1, s2, target, &IsxConfig::default()),
        Err(PidError::SupportContractRequired { .. })
    ));

    let tied_data = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0];
    let tied = MatRef::new(&tied_data, 8, 1).unwrap();
    assert!(matches!(
        isx_redundancy(
            tied,
            s2,
            target,
            &IsxConfig::assume_regular_full_dimensional()
        ),
        Err(PidError::ObservedContinuousSampleIncompatibility { .. })
    ));
}

#[test]
fn isx_rejects_every_nonzero_or_nonfinite_tie_epsilon() {
    let s1_data = [0.0, 0.2, 0.5, 0.9];
    let s2_data = [0.1, 0.3, 0.6, 1.0];
    let target_data = [0.05, 0.25, 0.55, 0.95];
    let s1 = MatRef::new(&s1_data, 4, 1).unwrap();
    let s2 = MatRef::new(&s2_data, 4, 1).unwrap();
    let target = MatRef::new(&target_data, 4, 1).unwrap();

    for tie_epsilon in [-1.0, 1.0e-12, f64::NAN, f64::INFINITY] {
        let config = IsxConfig {
            tie_epsilon,
            ..IsxConfig::default()
        };
        assert!(isx_redundancy(s1, s2, target, &config).is_err());
    }
}

#[test]
fn isx_rejects_unequal_ambient_source_dimensions() {
    let scalar_data = [0.0, 0.2, 0.5, 0.9];
    let vector_data = [0.0, 0.1, 0.2, 0.3, 0.5, 0.6, 0.9, 1.0];
    let target_data = [0.05, 0.25, 0.55, 0.95];
    let scalar = MatRef::new(&scalar_data, 4, 1).unwrap();
    let vector = MatRef::new(&vector_data, 4, 2).unwrap();
    let target = MatRef::new(&target_data, 4, 1).unwrap();

    let error = isx_redundancy(scalar, vector, target, &IsxConfig::default()).unwrap_err();

    assert!(matches!(
        error,
        PidError::SourceDimensionMismatch {
            context: "isx_redundancy",
            left_cols: 1,
            right_cols: 2,
        }
    ));
}

#[test]
fn every_continuous_isx_method_rejects_an_ambiguous_positive_shell() {
    let source_data = [0.0, 0.5, 1.0, 0.3, 3.0];
    let target_data = [0.0, 0.4, 0.2, 1.0, 3.0];
    let source = MatRef::new(&source_data, 5, 1).unwrap();
    let target = MatRef::new(&target_data, 5, 1).unwrap();

    #[cfg(not(feature = "experimental-heuristics"))]
    let methods = [IsxMethod::EhrlichKsg];
    #[cfg(feature = "experimental-heuristics")]
    let methods = [
        IsxMethod::EhrlichKsg,
        IsxMethod::HeuristicSketch,
        IsxMethod::LocalMinKsg,
        IsxMethod::DisjunctionFromLocalMi,
    ];
    for method in methods {
        let config = IsxConfig {
            k: 2,
            method,
            ..IsxConfig::assume_regular_full_dimensional()
        };
        assert!(matches!(
            isx_redundancy(source, source, target, &config),
            Err(PidError::AmbiguousKthNeighborShell { .. })
        ));
    }
}

#[cfg(feature = "experimental-heuristics")]
#[test]
fn exp0_isx_redundancy_heuristic_sketch_smoke() {
    let mut rng = Rng64::new(2028);
    let n = 200;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        let noise = 0.01 * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = IsxConfig {
        method: IsxMethod::HeuristicSketch,
        ..IsxConfig::assume_regular_full_dimensional()
    };
    let red = isx_redundancy(s1, s2, t, &cfg).unwrap();
    assert!(red.is_finite());
}

#[cfg(feature = "experimental-heuristics")]
#[test]
fn exp0_isx_redundancy_disjunction_smoke() {
    let mut rng = Rng64::new(2029);
    let n = 250;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.normal();
        let noise1 = 0.01 * rng.normal();
        let noise2 = 0.01 * rng.normal();
        t.push(base);
        s1.push(base + noise1);
        s2.push(base + noise2);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = IsxConfig {
        method: IsxMethod::DisjunctionFromLocalMi,
        ..IsxConfig::assume_regular_full_dimensional()
    };
    let red = isx_redundancy(s1, s2, t, &cfg).unwrap();
    assert!(red.is_finite());
}

#[cfg(feature = "experimental-heuristics")]
#[test]
fn local_min_heuristic_matches_its_named_formula_and_is_source_symmetric() {
    let mut rng = Rng64::new(2030);
    let n = 160;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        s1.push(a + 0.05 * rng.normal());
        s2.push(b + 0.05 * rng.normal());
        t.push(a + b + 0.1 * rng.normal());
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();
    let cfg = IsxConfig {
        method: IsxMethod::LocalMinKsg,
        ..IsxConfig::assume_regular_full_dimensional()
    };
    let ksg_cfg = KsgConfig::default()
        .with_k(cfg.k)
        .with_metric(cfg.metric)
        .with_tie_epsilon(cfg.tie_epsilon)
        .with_negative_handling(NegativeHandling::Allow)
        .with_support_contract(cfg.support_contract);
    let local_s1 = ksg_local_mi_terms(s1, t, &ksg_cfg).unwrap();
    let local_s2 = ksg_local_mi_terms(s2, t, &ksg_cfg).unwrap();
    let expected = local_s1
        .iter()
        .zip(&local_s2)
        .map(|(&left, &right)| left.min(right))
        .sum::<f64>()
        / n as f64;
    let observed = isx_redundancy(s1, s2, t, &cfg).unwrap();
    let swapped = isx_redundancy(s2, s1, t, &cfg).unwrap();

    assert!((observed - expected).abs() < 1e-12);
    assert!((observed - swapped).abs() < 1e-12);
}

#[cfg(feature = "experimental-heuristics")]
#[test]
fn every_heuristic_scalar_baseline_is_source_symmetric_on_a_regular_fixture() {
    let mut rng = Rng64::new(2031);
    let n = 250;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.normal();
        s1.push(base + 0.01 * rng.normal());
        s2.push(base + 0.01 * rng.normal());
        t.push(base);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();
    for method in [
        IsxMethod::HeuristicSketch,
        IsxMethod::LocalMinKsg,
        IsxMethod::DisjunctionFromLocalMi,
    ] {
        let cfg = IsxConfig {
            method,
            ..IsxConfig::assume_regular_full_dimensional()
        };
        let observed = isx_redundancy(s1, s2, t, &cfg).unwrap();
        let swapped = isx_redundancy(s2, s1, t, &cfg).unwrap();
        assert!(
            (observed - swapped).abs() < 1e-12,
            "{method:?}: observed={observed} swapped={swapped}"
        );
    }
}

#[test]
fn exp0_pid2_isx_smoke() {
    let mut rng = Rng64::new(2027);
    let n = 220;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        let noise = 0.01 * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = Pid2Config::assume_regular_full_dimensional();
    let out = pid2_isx(s1, s2, t, &cfg).unwrap();
    assert!(out.redundancy.is_finite());
    assert!(out.unique_s1.is_finite());
    assert!(out.unique_s2.is_finite());
    assert!(out.synergy.is_finite());
}

#[test]
fn ehrlich_ksg_matches_pinned_csxpid_on_committed_fixture() {
    // Generated by scripts/generate-csxpid-reference.py from the authors' public csxpid
    // implementation. The JSON records the upstream commit, exact scientific Python
    // environment, SciPy kd-tree backend, complete input rows, bit-to-nat conversion, and output
    // hash. It is therefore an external cross-check rather than a self-generated regression pin.
    let reference = csxpid_reference();
    assert_eq!(
        reference["provenance"]["upstream"]["commit"].as_str(),
        Some("7bb984611a422cf7944ece68993fe3a27e2eadec")
    );

    let case = &reference["cases"]["bivariate"];
    let rows = case["rows"].as_array().unwrap();
    let n = rows.len();
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for row in rows {
        let row = row.as_array().unwrap();
        assert_eq!(row.len(), 3);
        s1.push(row[0].as_f64().unwrap());
        s2.push(row[1].as_f64().unwrap());
        t.push(row[2].as_f64().unwrap());
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = IsxConfig {
        k: 3,
        method: IsxMethod::EhrlichKsg,
        ..IsxConfig::assume_regular_full_dimensional()
    };

    let red = isx_redundancy(s1, s2, t, &cfg).unwrap();
    let expected = case["redundancy_bits"].as_f64().unwrap() * std::f64::consts::LN_2;
    let stored_nats = case["redundancy_nats"].as_f64().unwrap();
    assert!(
        (stored_nats - expected).abs() < 1e-15,
        "invalid bit-to-nat conversion in pinned csxpid fixture: bits*ln(2)={expected:.15e} stored={stored_nats:.15e}"
    );

    assert!(red.is_finite());
    assert!(
        (red - expected).abs() < 1e-12,
        "I^sx mismatch against pinned csxpid: estimated={red:.15e} expected={expected:.15e}"
    );
}
```

## Artifact: `crates/pid-core/tests/ksg_report.rs`

SHA-256: `724c1fad3ce11ce14b789efda0edccfe96a6f3334d077cad075dd667683b0f44`

```text
#[cfg(feature = "experimental-hyperbolic")]
use pid_core::experimental::hyperbolic::{
    hyperbolic_ksg_k_trajectory, hyperbolic_ksg_mi_report, hyperbolic_ksg_mi_report_with_budget,
    hyperbolic_ksg_report_resource_estimate, hyperbolic_ksg_sample_size_trajectory,
    HyperbolicCurvature, HyperbolicKsgConfig, HyperbolicKsgGeometryModel,
    HyperbolicKsgReportWarning, HyperbolicMetric,
};
#[cfg(feature = "experimental-hyperbolic")]
use pid_core::stable::continuous::ksg_report_resource_estimate;
use pid_core::stable::continuous::{
    ksg_mi_report, ksg_mi_report_with_budget, ksg_mi_report_with_budget_and_cancellation,
    Assumption, AssumptionState, KsgConfig, KsgGeometryModel, KsgMethodStatus, KsgNeighborBackend,
    KsgProvenance, KsgReportWarning, NegativeHandling, SupportContract,
};
use pid_core::{CancellationToken, MatRef, Metric, PidError, ResourceBudget};

#[cfg(feature = "experimental-hyperbolic")]
const HYPERBOLIC_CURVATURE: HyperbolicCurvature = HyperbolicCurvature::NegativeOne;

struct Rng(u64);

impl Rng {
    fn next_f64(&mut self) -> f64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        (x.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1_u64 << 53) as f64
    }
}

fn euclidean_data(n: usize) -> (Vec<f64>, Vec<f64>) {
    let mut rng = Rng(0xC0DE_5EED_1234_5678);
    let mut x = Vec::with_capacity(2 * n);
    let mut y = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        x.extend_from_slice(&[a, b]);
        y.push(0.3 * a + 0.2 * b + rng.next_f64());
    }
    (x, y)
}

#[test]
fn report_cancellation_is_preemptive_and_preserves_uncancelled_bits() {
    let n = 64;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional().with_k(4);
    let provenance = KsgProvenance::new(
        "identity transform",
        "i.i.d. continuous regression fixture",
        None,
    )
    .unwrap();
    let budget = ResourceBudget::default();
    let baseline = ksg_mi_report_with_budget(x, y, &config, &provenance, budget).unwrap();
    let running = CancellationToken::new();
    let cancellable =
        ksg_mi_report_with_budget_and_cancellation(x, y, &config, &provenance, budget, &running)
            .unwrap();
    assert_eq!(baseline, cancellable);

    let cancelled = CancellationToken::new();
    cancelled.cancel();
    let error =
        ksg_mi_report_with_budget_and_cancellation(x, y, &config, &provenance, budget, &cancelled)
            .unwrap_err();
    assert!(matches!(error, PidError::Cancelled { .. }));
}

#[cfg(feature = "experimental-hyperbolic")]
fn hyperbolic_data(n: usize) -> (Vec<f64>, Vec<f64>) {
    let mut rng = Rng(0xA11C_E5E5_7788_9900);
    let mut x = Vec::with_capacity(2 * n);
    let mut y = Vec::with_capacity(3 * n);
    for _ in 0..n {
        let x1 = 1.4 * rng.next_f64() - 0.7;
        x.extend_from_slice(&[x1.hypot(1.0), x1]);

        let y1 = 1.2 * rng.next_f64() - 0.6;
        let y2 = 1.2 * rng.next_f64() - 0.6;
        y.extend_from_slice(&[y1.hypot(y2).hypot(1.0), y1, y2]);
    }
    (x, y)
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_report_preflight_accounts_for_the_typed_wrapper() {
    let n = 24;
    let (x, y) = hyperbolic_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_k(3);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();
    let estimate = hyperbolic_ksg_report_resource_estimate(x, y, &provenance, 1).unwrap();
    let chebyshev_estimate = ksg_report_resource_estimate(x, y, &provenance, 1).unwrap();
    assert!(estimate.operations_hint > chebyshev_estimate.operations_hint);
    let exact_budget = ResourceBudget::new(
        estimate.estimated_bytes.try_into().unwrap(),
        estimate.pairwise_distances.try_into().unwrap(),
        estimate.operations_hint,
        1,
    )
    .unwrap();

    let report =
        hyperbolic_ksg_mi_report_with_budget(x, y, &cfg, &provenance, exact_budget).unwrap();
    assert_eq!(report.resource_estimate, estimate);
    assert_eq!(report.resource_budget, exact_budget);

    let one_byte_short = ResourceBudget::new(
        exact_budget.max_bytes - 1,
        exact_budget.max_pairwise_distances,
        exact_budget.max_operations_hint,
        exact_budget.max_threads,
    )
    .unwrap();
    assert!(matches!(
        hyperbolic_ksg_mi_report_with_budget(x, y, &cfg, &provenance, one_byte_short),
        Err(PidError::ResourceLimitExceeded {
            operation: "hyperbolic_ksg_mi_report",
            resource: "bytes",
            requested,
            limit,
        }) if requested == estimate.estimated_bytes && limit == estimate.estimated_bytes - 1
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_trajectory_preflights_sum_typed_report_estimates() {
    let n = 24;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_k(3);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();

    let one = hyperbolic_ksg_report_resource_estimate(x, y, &provenance, 1).unwrap();
    let k_budget = ResourceBudget::new(
        (one.estimated_bytes * 2).try_into().unwrap(),
        (one.pairwise_distances * 2).try_into().unwrap(),
        one.operations_hint * 2,
        1,
    )
    .unwrap();
    let k_trajectory =
        hyperbolic_ksg_k_trajectory(x, y, &[2, 3], &cfg, &provenance, k_budget).unwrap();
    assert_eq!(
        k_trajectory.aggregate_resource_estimate.estimated_bytes,
        one.estimated_bytes * 2
    );

    let prefix_n = 12;
    let x_prefix = MatRef::new(&x_data[..prefix_n * 2], prefix_n, 2).unwrap();
    let y_prefix = MatRef::new(&y_data[..prefix_n * 3], prefix_n, 3).unwrap();
    let prefix =
        hyperbolic_ksg_report_resource_estimate(x_prefix, y_prefix, &provenance, 1).unwrap();
    let sample_budget = ResourceBudget::new(
        (prefix.estimated_bytes + one.estimated_bytes)
            .try_into()
            .unwrap(),
        (prefix.pairwise_distances + one.pairwise_distances)
            .try_into()
            .unwrap(),
        prefix.operations_hint + one.operations_hint,
        1,
    )
    .unwrap();
    let sample_trajectory = hyperbolic_ksg_sample_size_trajectory(
        x,
        y,
        &[prefix_n, n],
        &cfg,
        &provenance,
        sample_budget,
    )
    .unwrap();
    assert_eq!(
        sample_trajectory
            .aggregate_resource_estimate
            .estimated_bytes,
        prefix.estimated_bytes + one.estimated_bytes
    );
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_k_trajectory_validates_every_k_before_resource_preflight() {
    let n = 12;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();
    let tiny_budget = ResourceBudget::new(1, 1, 1, 1).unwrap();

    assert!(matches!(
        hyperbolic_ksg_k_trajectory(x, y, &[2, n], &cfg, &provenance, tiny_budget),
        Err(PidError::InvalidK {
            k,
            n_samples,
        }) if k == n && n_samples == n
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_k_trajectory_validates_provenance_before_resource_preflight() {
    let n = 12;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        None,
    )
    .unwrap();
    let tiny_budget = ResourceBudget::new(1, 1, 1, 1).unwrap();

    assert!(matches!(
        hyperbolic_ksg_k_trajectory(x, y, &[2, 3], &cfg, &provenance, tiny_budget),
        Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperbolic reports require embedding_training_provenance",
        })
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_sample_trajectory_validates_config_before_resource_preflight() {
    let n = 12;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg =
        HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_tie_epsilon(0.25);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();
    let tiny_budget = ResourceBudget::new(1, 1, 1, 1).unwrap();

    assert!(matches!(
        hyperbolic_ksg_sample_size_trajectory(x, y, &[8, n], &cfg, &provenance, tiny_budget,),
        Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        })
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_sample_trajectory_validates_provenance_before_resource_preflight() {
    let n = 12;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        None,
    )
    .unwrap();
    let tiny_budget = ResourceBudget::new(1, 1, 1, 1).unwrap();

    assert!(matches!(
        hyperbolic_ksg_sample_size_trajectory(x, y, &[8, n], &cfg, &provenance, tiny_budget,),
        Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperbolic reports require embedding_training_provenance",
        })
    ));
}

#[test]
fn provenance_rejects_empty_descriptions() {
    assert!(matches!(
        KsgProvenance::new("  ", "additive Gaussian sensor noise", None),
        Err(PidError::InvalidConfig { .. })
    ));
    assert!(matches!(
        KsgProvenance::new("z-score each column", "\n", None),
        Err(PidError::InvalidConfig { .. })
    ));
    assert!(matches!(
        KsgProvenance::new(
            "z-score each column",
            "additive Gaussian sensor noise",
            Some("\t"),
        ),
        Err(PidError::InvalidConfig { .. })
    ));
}

#[test]
fn euclidean_report_preserves_metadata_and_radius_diagnostics() {
    let n = 32;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(4);
    let provenance = KsgProvenance::new(
        "training-fold z-score parameters applied without refitting",
        "i.i.d. draws with an additive continuous sensor-noise model",
        None,
    )
    .unwrap();

    let report = ksg_mi_report(x, y, &cfg, &provenance).unwrap();

    assert!(report.estimate_nats.is_finite());
    assert_eq!(
        report.estimate_nats.to_bits(),
        report.signed_estimate_nats.to_bits()
    );
    assert_eq!(report.n_samples, n);
    assert_eq!(report.k, 4);
    assert_eq!(report.metric, Metric::Chebyshev);
    assert_eq!(report.negative_handling, NegativeHandling::Allow);
    assert!(matches!(
        report.support_contract,
        SupportContract::AssumeRegularFullDimensional { .. }
    ));
    assert_eq!(report.method_status, KsgMethodStatus::RestrictedDomain);
    assert_eq!(
        report.estimand.estimator_revision,
        "strict-unique-shell-integer-harmonic-report-v4"
    );
    assert_eq!(report.geometry_model, KsgGeometryModel::AmbientChebyshev);
    assert_eq!(report.curvature, None);
    assert_eq!(report.x_hyperbolic_dimension, None);
    assert_eq!(report.y_hyperbolic_dimension, None);
    assert_eq!(report.x_diagnostics.ambient_dimension, 2);
    assert_eq!(report.y_diagnostics.ambient_dimension, 1);
    assert_eq!(report.x_diagnostics.marginal_shells.query_count, n);
    assert_eq!(report.y_diagnostics.marginal_shells.query_count, n);
    assert_eq!(report.joint_shells.query_count, n);
    assert!(report.x_diagnostics.marginal_shells.kth_radius.min > 0.0);
    assert!(report.y_diagnostics.marginal_shells.kth_radius.min > 0.0);
    assert!(report.joint_shells.kth_radius.min > 0.0);
    assert!(report.joint_shells.kth_radius.max >= report.joint_shells.kth_radius.min);
    let dimension_assumption = report
        .assumption_ledger
        .iter()
        .find(|entry| entry.assumption == Assumption::FixedLocalDimension)
        .unwrap();
    assert_eq!(
        dimension_assumption.state,
        AssumptionState::AssumptionsDeclared
    );
    assert!(dimension_assumption
        .note
        .contains("each required marginal and joint law"));
    assert_eq!(
        report.provenance.preprocessing_description(),
        "training-fold z-score parameters applied without refitting"
    );
    assert_eq!(
        report.provenance.observation_model_description(),
        "i.i.d. draws with an additive continuous sensor-noise model"
    );
    assert!(report
        .warnings
        .contains(&KsgReportWarning::SampleDiagnosticsCannotProveSupport));
    assert!(KsgReportWarning::SampleDiagnosticsCannotProveSupport
        .message()
        .contains("cannot determine the cause or prove"));
}

#[test]
fn report_records_the_selected_backend_without_claiming_a_fallback() {
    let provenance = KsgProvenance::new(
        "identity transform",
        "i.i.d. continuous regression fixture",
        None,
    )
    .unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(4);

    let (small_x, small_y) = euclidean_data(32);
    let small = ksg_mi_report(
        MatRef::new(&small_x, 32, 2).unwrap(),
        MatRef::new(&small_y, 32, 1).unwrap(),
        &cfg,
        &provenance,
    )
    .unwrap();
    assert_eq!(small.neighbor_backend, KsgNeighborBackend::BruteForce);

    let (large_x, large_y) = euclidean_data(128);
    let large = ksg_mi_report(
        MatRef::new(&large_x, 128, 2).unwrap(),
        MatRef::new(&large_y, 128, 1).unwrap(),
        &cfg,
        &provenance,
    )
    .unwrap();
    assert_eq!(
        large.neighbor_backend,
        KsgNeighborBackend::ExactChebyshevKdTree
    );

    let json = serde_json::to_value(&large).unwrap();
    assert!(json.get("neighbor_backend").is_some());
    assert!(json.get("used_brute_force_fallback").is_none());
    assert!(json.get("backend_fallback_occurred").is_none());
}

#[test]
fn report_retains_signed_estimate_under_presentation_clamping() {
    let n = 32;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional()
        .with_k(4)
        .with_negative_handling(NegativeHandling::ClampToZero);
    let provenance = KsgProvenance::new(
        "identity transform",
        "i.i.d. continuous regression fixture",
        None,
    )
    .unwrap();

    let report = ksg_mi_report(x, y, &config, &provenance).unwrap();

    assert_eq!(
        report.estimate_nats.to_bits(),
        report.signed_estimate_nats.max(0.0).to_bits()
    );
    let json = serde_json::to_value(&report).unwrap();
    assert_eq!(
        json["signed_estimate_nats"].as_f64().unwrap().to_bits(),
        report.signed_estimate_nats.to_bits()
    );
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_report_requires_embedding_training_provenance() {
    let n = 16;
    let (x, y) = hyperbolic_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_k(3);
    let provenance = KsgProvenance::new(
        "no coordinate preprocessing",
        "smooth densities relative to declared manifold volume",
        None,
    )
    .unwrap();

    let error = hyperbolic_ksg_mi_report(x, y, &cfg, &provenance).unwrap_err();

    assert!(matches!(
        error,
        PidError::InvalidConfig {
            context: "ksg_mi_report",
            ..
        }
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn report_validates_shape_before_hyperbolic_provenance_gate() {
    let x_data = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0];
    let y_data = [1.0, 0.0, 1.0, 0.0];
    let x = MatRef::new(&x_data, 3, 2).unwrap();
    let y = MatRef::new(&y_data, 2, 2).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to hyperboloid coordinates",
        "smooth manifold observation model",
        None,
    )
    .unwrap();

    assert!(matches!(
        hyperbolic_ksg_mi_report(x, y, &cfg, &provenance),
        Err(PidError::RowCountMismatch {
            context: "ksg_mi_report",
            ..
        })
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_report_rejects_row_width_below_two_as_configuration() {
    let x_data = [1.0, 1.1, 1.2, 1.3];
    let y_data = [1.0, 1.1, 1.2, 1.3];
    let x = MatRef::new(&x_data, 4, 1).unwrap();
    let y = MatRef::new(&y_data, 4, 1).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to hyperboloid coordinates",
        "smooth manifold observation model",
        Some("frozen encoder checkpoint sha256:abc"),
    )
    .unwrap();

    let error = hyperbolic_ksg_mi_report(x, y, &cfg, &provenance).unwrap_err();
    assert!(matches!(
        error,
        PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperboloid inputs must each have row width d+1 >= 2",
        }
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_report_records_model_curvature_dimensions_and_status() {
    let n = 24;
    let (x, y) = hyperbolic_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_k(3);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("encoder checkpoint sha256:0123456789abcdef; frozen before evaluation"),
    )
    .unwrap();

    let report = hyperbolic_ksg_mi_report(x, y, &cfg, &provenance).unwrap();

    assert!(report.estimate_nats.is_finite());
    assert_eq!(
        report.metric,
        HyperbolicMetric::lorentz(HYPERBOLIC_CURVATURE)
    );
    assert_eq!(report.method_status, KsgMethodStatus::Experimental);
    assert_eq!(
        report.geometry_model,
        HyperbolicKsgGeometryModel::LorentzHyperboloid
    );
    assert_eq!(report.curvature, HYPERBOLIC_CURVATURE);
    assert_eq!(report.x_hyperbolic_dimension, 1);
    assert_eq!(report.y_hyperbolic_dimension, 2);
    assert_eq!(
        report.provenance.embedding_training_provenance(),
        Some("encoder checkpoint sha256:0123456789abcdef; frozen before evaluation")
    );
    assert!(report
        .warnings
        .contains(&HyperbolicKsgReportWarning::ConsistencyNotEstablished));
    assert!(HyperbolicKsgReportWarning::ConsistencyNotEstablished
        .message()
        .contains("lacks a statistical consistency theorem"));
}

#[test]
fn report_is_deterministic() {
    let n = 32;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(4);
    let provenance = KsgProvenance::new(
        "fixed preprocessing recipe v2",
        "i.i.d. absolutely-continuous observation model",
        None,
    )
    .unwrap();

    let first = ksg_mi_report(x, y, &cfg, &provenance).unwrap();
    let second = ksg_mi_report(x, y, &cfg, &provenance).unwrap();

    assert_eq!(first, second);
}

#[test]
fn giant_thread_ceiling_is_capped_to_available_query_work() {
    let n = 16;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(3);
    let provenance = KsgProvenance::new("identity", "i.i.d. continuous fixture", None).unwrap();
    let mut budget = ResourceBudget::default();
    budget.max_threads = usize::MAX;

    let report = ksg_mi_report_with_budget(x, y, &cfg, &provenance, budget).unwrap();
    assert!(report.estimate_nats.is_finite());
}
```

## Artifact: `crates/pid-core/tests/parallel_bit_identity.rs`

SHA-256: `611a31e1b76536b1b1b712cdbd7713dc5caad24f354b0c507e2779bbf8f3cb28`

```text
#![cfg(feature = "experimental-pipelines")]

//! Serial == parallel **bit-identity** guard.
//!
//! The `parallel` (rayon) feature is required to be bit-for-bit identical to the serial path
//! (`f64::to_bits` equality) — a non-negotiable project convention. This test pins that
//! contract for every estimator that the `parallel` feature touches:
//!
//! - `ksg_local_mi_terms` (the per-point KSG local MI contributions),
//! - the 2-source PID atoms (`pid2_isx`),
//! - the 3-source PID atoms / redundancies (`pid3_isx`, whose `redundancy_for_antichain` is
//!   the parallelized hot loop),
//! - the continuous `I^sx_∩` redundancy (`isx_redundancy`, `IsxMethod::EhrlichKsg`), and
//! - a block-bootstrap result (`block_bootstrap`).
//!
//! Strategy: the expected values below are **frozen `f64::to_bits` patterns captured from the
//! serial build**
//! (`cargo test -p pid-core --features experimental-pipelines --test parallel_bit_identity`).
//! The same test then runs under
//! `cargo test -p pid-core --features experimental-pipelines,parallel --test parallel_bit_identity`;
//! if any parallelized path changed a single bit, the corresponding `assert_eq!` on `to_bits()`
//! fails. Running it in *both* configurations is what makes it a serial==parallel guard: the
//! serial run proves the frozen constants are the serial truth, the parallel run proves the
//! parallel path reproduces them exactly.
//!
//! The constants are NOT scientific ground truth — they are whatever the (unchanged) serial
//! estimator produces on this fixed synthetic dataset; the test's only job is to detect any
//! serial/parallel divergence (or any accidental change to the serial numbers).
//!
//! The count-based tests use a deliberately non-uniform empirical distribution and compare
//! repeated calls with `f64::to_bits`. Those paths do not use Rayon; their guard catches
//! iteration-order nondeterminism in histogram accumulation across invocations.

use pid_core::diagnostics::{red_degree_discrete, vul_degree_discrete};
use pid_core::experimental::continuous::raw_scalars::{isx_redundancy, ksg_local_mi_terms};
use pid_core::experimental::continuous::{pid2_isx, IsxConfig, Pid2Config};
use pid_core::experimental::mixed_dimension_pid3::{pid3_isx, Antichain3, Pid3Config};
use pid_core::experimental::pipelines::{
    block_bootstrap, block_bootstrap_with_budget,
    exploratory_same_sample_quantized_imin_pid2 as discrete_pid2, BlockLengthSelection,
    BootstrapConfig, BootstrapReplicateStatus, ResamplingValidityDeclaration,
    StatisticCallbackDeclaration,
};
use pid_core::stable::continuous::{
    ksg_mi_report_with_budget, KsgConfig, KsgMiReport, KsgProvenance, NegativeHandling,
};
use pid_core::stable::imin::IminPid2Result;
use pid_core::{MatOwned, ResourceBudget, ResourceEstimate};

mod common;
use common::Rng64;

/// Deterministic synthetic system: V and L share a latent signal that drives the target A;
/// D is an independent noisy copy. Fixed seed, so the data is identical on every run and in
/// both feature configurations.
fn make_system(n: usize, seed: u64) -> (MatOwned, MatOwned, MatOwned, MatOwned) {
    let mut rng = Rng64::new(seed);
    let mut s1 = Vec::with_capacity(n * 2);
    let mut s2 = Vec::with_capacity(n * 2);
    let mut s3 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let signal = rng.normal();
        s1.push(signal + 0.2 * rng.normal());
        s1.push(0.5 * rng.normal());
        s2.push(signal + 0.3 * rng.normal());
        s2.push(0.5 * rng.normal());
        s3.push(0.7 * signal + 0.7 * rng.normal());
        t.push(signal + 0.1 * rng.normal());
    }
    (
        MatOwned::new(s1, n, 2).unwrap(),
        MatOwned::new(s2, n, 2).unwrap(),
        MatOwned::new(s3, n, 1).unwrap(),
        MatOwned::new(t, n, 1).unwrap(),
    )
}

const N: usize = 120;
const SEED: u64 = 20240917;
const THREAD_BUDGET_N: usize = 48;

fn ksg_cfg() -> KsgConfig {
    KsgConfig::assume_regular_full_dimensional()
        .with_k(4)
        .with_negative_handling(NegativeHandling::Allow)
}

/// An irregular empirical PMF with many distinct probabilities. Using uniform logic-gate data
/// here would let reordered floating-point accumulation accidentally produce the same bits.
fn nonuniform_discrete_labels() -> [Vec<u32>; 4] {
    let states = [
        (0, 4, 1, 9, 17),
        (0, 2, 1, 8, 5),
        (1, 4, 0, 8, 13),
        (1, 2, 2, 7, 7),
        (2, 3, 0, 7, 11),
        (2, 3, 2, 6, 3),
        (3, 1, 1, 6, 19),
        (3, 0, 2, 5, 2),
        (4, 1, 3, 5, 23),
        (4, 0, 3, 4, 6),
        (5, 2, 4, 4, 29),
        (5, 4, 0, 9, 4),
    ];
    let n = states.iter().map(|state| state.4).sum();
    let mut labels = std::array::from_fn(|_| Vec::with_capacity(n));
    for &(x, y, z, w, count) in &states {
        for _ in 0..count {
            labels[0].push(x);
            labels[1].push(y);
            labels[2].push(z);
            labels[3].push(w);
        }
    }
    labels
}

fn discrete_pid2_bits(result: &IminPid2Result) -> [u64; 7] {
    [
        result.redundancy.to_bits(),
        result.unique_s1.to_bits(),
        result.unique_s2.to_bits(),
        result.synergy.to_bits(),
        result.mi_s1_t.to_bits(),
        result.mi_s2_t.to_bits(),
        result.mi_s1s2_t.to_bits(),
    ]
}

fn thread_limits_through_available_maximum() -> Vec<usize> {
    let mut limits = vec![1, 2, 3, 4, ResourceBudget::default().max_threads];
    limits.sort_unstable();
    limits.dedup();
    limits
}

fn budget_with_threads(max_threads: usize) -> ResourceBudget {
    let mut budget = ResourceBudget::default();
    budget.max_threads = max_threads;
    budget
}

fn normalize_ksg_resource_accounting(report: &mut KsgMiReport) {
    report.resource_budget = budget_with_threads(1);
    report.resource_estimate = ResourceEstimate::ZERO;
}

fn pid3_bits(result: &pid_core::experimental::mixed_dimension_pid3::Pid3Result) -> Vec<u64> {
    result
        .redundancies
        .iter()
        .map(|entry| entry.value.to_bits())
        .chain(result.atoms.iter().map(|entry| entry.value.to_bits()))
        .collect()
}

fn bootstrap_result_bits(result: &pid_core::experimental::pipelines::BootstrapResult) -> Vec<u64> {
    let mut bits = vec![result.point_estimate.to_bits()];
    let summary = result
        .summary
        .as_ref()
        .expect("the deterministic statistic must complete for every replicate");
    bits.extend([
        summary.resample_mean.to_bits(),
        summary.resample_standard_deviation.to_bits(),
        summary.percentile_lower.to_bits(),
        summary.percentile_upper.to_bits(),
    ]);
    for outcome in &result.replicates {
        bits.push(outcome.replicate_index as u64);
        match &outcome.status {
            BootstrapReplicateStatus::Complete { value } => bits.push(value.to_bits()),
            BootstrapReplicateStatus::Failed { error } => {
                panic!("deterministic bootstrap replicate failed: {error}")
            }
            _ => panic!("unexpected future bootstrap replicate status"),
        }
    }
    bits
}

#[test]
fn ksg_report_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {
    let (s1, _s2, _s3, target) = make_system(THREAD_BUDGET_N, SEED ^ 0x4B53_4701);
    let provenance = KsgProvenance::new("identity", "seeded continuous fixture", None).unwrap();
    let mut expected = ksg_mi_report_with_budget(
        s1.as_ref(),
        target.as_ref(),
        &ksg_cfg(),
        &provenance,
        budget_with_threads(1),
    )
    .unwrap();
    normalize_ksg_resource_accounting(&mut expected);

    for max_threads in thread_limits_through_available_maximum() {
        let mut actual = ksg_mi_report_with_budget(
            s1.as_ref(),
            target.as_ref(),
            &ksg_cfg(),
            &provenance,
            budget_with_threads(max_threads),
        )
        .unwrap();
        normalize_ksg_resource_accounting(&mut actual);
        assert_eq!(
            actual, expected,
            "KSG report changed at max_threads={max_threads}"
        );
    }
}

#[test]
fn pid2_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {
    let (s1, s2, _s3, target) = make_system(THREAD_BUDGET_N, SEED ^ 0x5049_4432);
    let cfg = Pid2Config {
        ksg: ksg_cfg(),
        isx: IsxConfig {
            k: 4,
            ..IsxConfig::assume_regular_full_dimensional()
        },
    };
    let expected = pid_core::experimental::continuous::pid2_isx_with_budget(
        s1.as_ref(),
        s2.as_ref(),
        target.as_ref(),
        &cfg,
        budget_with_threads(1),
    )
    .unwrap();

    for max_threads in thread_limits_through_available_maximum() {
        let actual = pid_core::experimental::continuous::pid2_isx_with_budget(
            s1.as_ref(),
            s2.as_ref(),
            target.as_ref(),
            &cfg,
            budget_with_threads(max_threads),
        )
        .unwrap();
        assert_eq!(
            actual, expected,
            "PID2 atoms changed at max_threads={max_threads}"
        );
    }
}

#[test]
fn pid3_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {
    let (s0, s1, s2, target) = make_system(THREAD_BUDGET_N, SEED ^ 0x5049_4433);
    let cfg = Pid3Config {
        k: 4,
        experimental_allow_mixed_dimension_lattice: true,
        ..Pid3Config::assume_regular_full_dimensional()
    };
    let expected = pid3_bits(
        &pid_core::experimental::mixed_dimension_pid3::pid3_isx_with_budget(
            s0.as_ref(),
            s1.as_ref(),
            s2.as_ref(),
            target.as_ref(),
            &cfg,
            budget_with_threads(1),
        )
        .unwrap(),
    );

    for max_threads in thread_limits_through_available_maximum() {
        let actual = pid3_bits(
            &pid_core::experimental::mixed_dimension_pid3::pid3_isx_with_budget(
                s0.as_ref(),
                s1.as_ref(),
                s2.as_ref(),
                target.as_ref(),
                &cfg,
                budget_with_threads(max_threads),
            )
            .unwrap(),
        );
        assert_eq!(
            actual, expected,
            "PID3 coordinates changed at max_threads={max_threads}"
        );
    }
}

#[test]
fn bootstrap_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {
    let data: Vec<f64> = (0..THREAD_BUDGET_N)
        .map(|index| ((index % 19) as i32 - 9) as f64 / 8.0)
        .collect();
    let cfg = BootstrapConfig::new(
        32,
        6,
        0x4255_4447_4554,
        0.05,
        ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori),
    )
    .unwrap();
    let evaluate = |max_threads| {
        block_bootstrap_with_budget(
            &data,
            &cfg,
            budget_with_threads(max_threads),
            StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO),
            |samples| Ok(samples.iter().sum::<f64>() / samples.len() as f64),
        )
        .map(|result| bootstrap_result_bits(&result))
    };
    let expected = evaluate(1).unwrap();

    for max_threads in thread_limits_through_available_maximum() {
        let actual = evaluate(max_threads).unwrap();
        assert_eq!(
            actual, expected,
            "bootstrap distribution changed at max_threads={max_threads}"
        );
    }
}

#[test]
fn ksg_local_mi_terms_match_serial_reference() {
    let (s1, _s2, _s3, t) = make_system(N, SEED);
    let terms = ksg_local_mi_terms(s1.as_ref(), t.as_ref(), &ksg_cfg()).unwrap();
    assert_eq!(terms.len(), N);
    // Frozen reference: bit-pattern checksum + the first/last/mid term bits. We XOR-fold all
    // term bits into one u64 so a divergence at any index trips the checksum, then also pin a
    // few individual terms to localize a failure.
    let checksum = terms.iter().fold(0u64, |acc, &x| acc ^ x.to_bits());
    assert_eq!(
        [
            checksum,
            terms[0].to_bits(),
            terms[N / 2].to_bits(),
            terms[N - 1].to_bits(),
        ],
        [
            KSG_LOCAL_TERMS_CHECKSUM,
            KSG_LOCAL_TERM_0,
            KSG_LOCAL_TERM_MID,
            KSG_LOCAL_TERM_LAST,
        ],
        "KSG local-MI term bits diverged"
    );
}

#[test]
fn isx_redundancy_matches_serial_reference() {
    let (s1, s2, _s3, t) = make_system(N, SEED);
    let cfg = IsxConfig {
        k: 4,
        ..IsxConfig::assume_regular_full_dimensional()
    };
    let red = isx_redundancy(s1.as_ref(), s2.as_ref(), t.as_ref(), &cfg).unwrap();
    assert_eq!(red.to_bits(), ISX_REDUNDANCY_BITS, "I^sx_∩ bits diverged");
}

#[test]
fn pid2_atoms_match_serial_reference() {
    let (s1, s2, _s3, t) = make_system(N, SEED);
    let cfg = Pid2Config {
        ksg: ksg_cfg(),
        isx: IsxConfig {
            k: 4,
            ..IsxConfig::assume_regular_full_dimensional()
        },
    };
    let r = pid2_isx(s1.as_ref(), s2.as_ref(), t.as_ref(), &cfg).unwrap();
    assert_eq!(
        [
            r.redundancy.to_bits(),
            r.unique_s1.to_bits(),
            r.unique_s2.to_bits(),
            r.synergy.to_bits(),
        ],
        [PID2_RED_BITS, PID2_UNQ1_BITS, PID2_UNQ2_BITS, PID2_SYN_BITS],
        "pid2 atom bits diverged"
    );
}

#[test]
fn pid3_atoms_match_serial_reference() {
    let (s1, s2, s3, t) = make_system(N, SEED);
    let cfg = Pid3Config {
        k: 4,
        experimental_allow_mixed_dimension_lattice: true,
        ..Pid3Config::assume_regular_full_dimensional()
    };
    let r = pid3_isx(s1.as_ref(), s2.as_ref(), s3.as_ref(), t.as_ref(), &cfg).unwrap();
    assert_eq!(r.atoms.len(), 18);
    // XOR-fold every atom's bits (order is the canonical antichain order, fixed) and every
    // redundancy's bits — `redundancy_for_antichain` is the parallelized loop.
    let atom_checksum = r.atoms.iter().fold(0u64, |acc, a| acc ^ a.value.to_bits());
    let red_checksum = r
        .redundancies
        .iter()
        .fold(0u64, |acc, x| acc ^ x.value.to_bits());
    // Pin two individual atoms to localize a failure.
    let unq_s1 = r
        .atom(Antichain3::try_from_sets(&[0b001]).unwrap())
        .unwrap();
    let full_syn = r
        .atom(Antichain3::try_from_sets(&[0b111]).unwrap())
        .unwrap();
    assert_eq!(
        [
            atom_checksum,
            red_checksum,
            unq_s1.to_bits(),
            full_syn.to_bits(),
        ],
        [
            PID3_ATOM_CHECKSUM,
            PID3_RED_CHECKSUM,
            PID3_ATOM_001_BITS,
            PID3_ATOM_111_BITS,
        ],
        "pid3 bits diverged"
    );
}

#[test]
fn block_bootstrap_matches_serial_reference() {
    // A bootstrap over a floating-point mean exercises the resample loop (the path made parallel
    // in `block_bootstrap`) with a non-trivial, RNG-order-sensitive statistic. Unlike continuous
    // kNN estimators, the mean remains defined when with-replacement resampling duplicates rows.
    // Use exactly represented binary-rational inputs. The estimator fixtures above intentionally
    // exercise transcendental RNG output, but a frozen bootstrap *mean* must not depend on a
    // platform libm's last bits before the serial/parallel comparison even begins.
    let data: Vec<f64> = (0..N)
        .map(|i| ((i % 29) as i32 - 14) as f64 / 8.0)
        .collect();
    let cfg = BootstrapConfig::new(
        64,
        12,
        7,
        0.05,
        ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori),
    )
    .unwrap();
    let result = block_bootstrap(
        &data,
        &cfg,
        StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO),
        |samples| Ok(samples.iter().sum::<f64>() / samples.len() as f64),
    )
    .unwrap();
    let summary = result.summary.unwrap();
    assert_eq!(
        [
            result.point_estimate.to_bits(),
            summary.resample_mean.to_bits(),
            summary.resample_standard_deviation.to_bits(),
            summary.percentile_lower.to_bits(),
            summary.percentile_upper.to_bits(),
        ],
        [
            BOOT_POINT_BITS,
            BOOT_MEAN_BITS,
            BOOT_SE_BITS,
            BOOT_CI_LOW_BITS,
            BOOT_CI_HIGH_BITS,
        ],
        "bootstrap bits diverged"
    );
}

#[test]
fn discrete_pid2_is_bit_identical_across_repeated_calls() {
    let [x, y, z, w] = nonuniform_discrete_labels();
    let n = x.len();
    let mut s1_data = Vec::with_capacity(2 * n);
    for (&x_i, &w_i) in x.iter().zip(&w) {
        s1_data.extend([f64::from(x_i), f64::from(w_i)]);
    }
    let s1 = MatOwned::new(s1_data, n, 2).unwrap();
    let s2 = MatOwned::new(y.into_iter().map(f64::from).collect(), n, 1).unwrap();
    let target = MatOwned::new(z.into_iter().map(f64::from).collect(), n, 1).unwrap();
    let expected = discrete_pid2_bits(
        &discrete_pid2(s1.as_ref(), s2.as_ref(), target.as_ref(), 6)
            .unwrap()
            .into_categorical_result(),
    );

    for _ in 0..32 {
        let actual = discrete_pid2(s1.as_ref(), s2.as_ref(), target.as_ref(), 6)
            .unwrap()
            .into_categorical_result();
        assert_eq!(discrete_pid2_bits(&actual), expected);
    }
}

#[test]
fn red_degree_discrete_is_bit_identical_across_repeated_calls() {
    let labels = nonuniform_discrete_labels();
    let vars = labels.iter().map(Vec::as_slice).collect::<Vec<_>>();
    let expected = red_degree_discrete(&vars).unwrap().to_bits();

    for _ in 0..32 {
        assert_eq!(red_degree_discrete(&vars).unwrap().to_bits(), expected);
    }
}

#[test]
fn vul_degree_discrete_is_bit_identical_across_repeated_calls() {
    let labels = nonuniform_discrete_labels();
    let vars = labels.iter().map(Vec::as_slice).collect::<Vec<_>>();
    let expected = vul_degree_discrete(&vars).unwrap().to_bits();

    for _ in 0..32 {
        assert_eq!(vul_degree_discrete(&vars).unwrap().to_bits(), expected);
    }
}

// ── Frozen serial bit patterns (`experimental-pipelines`, without `parallel`) ──
//
// The KSG/ISX/PID2/PID3 values below reflect the integer-harmonic range evaluation used by the
// candidate KSG arithmetic. Estimator topology, neighbor selection, signed PID reconstruction,
// and the parent PID2 implementation are unchanged. These bits pin the resulting serial
// implementation; they are not an independent accuracy oracle.
const KSG_LOCAL_TERMS_CHECKSUM: u64 = 13714940533915299;
const KSG_LOCAL_TERM_0: u64 = 4611372573292626839;
const KSG_LOCAL_TERM_MID: u64 = 4608683422432580648;
const KSG_LOCAL_TERM_LAST: u64 = 4609053335123176929;
const ISX_REDUNDANCY_BITS: u64 = 4608069949341512143;
const PID2_RED_BITS: u64 = 4608069949341512143;
const PID2_UNQ1_BITS: u64 = 4590324628665003600;
const PID2_UNQ2_BITS: u64 = 13821388618758275492;
const PID2_SYN_BITS: u64 = 4591732782175321776;
const PID3_ATOM_CHECKSUM: u64 = 9260367673031411424;
const PID3_RED_CHECKSUM: u64 = 12358916445650220;
const PID3_ATOM_001_BITS: u64 = 13803885910316517056;
const PID3_ATOM_111_BITS: u64 = 4587721666143603408;
const BOOT_POINT_BITS: u64 = 13811038857269521067;
const BOOT_MEAN_BITS: u64 = 4578959861135162299;
const BOOT_SE_BITS: u64 = 4597572063773922634;
const BOOT_CI_LOW_BITS: u64 = 13825206431097290752;
const BOOT_CI_HIGH_BITS: u64 = 4603598304096568388;
```
