"""Contract tests for the pid_core_rs 0.9 review surface proposed for 1.0."""

from __future__ import annotations

import math
import importlib
import os
import signal
import subprocess
import sys
import textwrap
import threading
import time

import numpy as np
import pytest

import pid_core_rs as pid


SUPPORT = "regular_full_dimensional_absolutely_continuous"
PROVENANCE = {
    "support_assertion": SUPPORT,
    "preprocessing_description": "training-fold scaling reused without refitting",
    "observation_model_description": "continuous observations with additive sensor noise",
    "dependence_model_description": "rows treated as independent draws",
}
SX_UNSUPPORTED_INFERENCES = (
    "intentional_deception",
    "causal_effect",
    "fault_attribution",
    "per_source_responsibility",
    "measure_independent_decomposition",
    "unbiased_population_estimate",
)


def gate2(rows: list[tuple[int, int, int]], repetitions: int = 8):
    repeated = rows * repetitions
    return tuple(
        np.asarray([[row[index]] for row in repeated], dtype=np.int64)
        for index in range(3)
    )


def assert_empirical_pmf_averaged_atom(atom) -> None:
    assert isinstance(atom, pid.SxAveragedAtom)
    interpretation = atom.interpretation
    assert isinstance(interpretation, pid.SxAtomInterpretation)
    assert interpretation.contract_revision == 1
    assert interpretation.aggregation_scope == "empirical_pmf_average"
    assert (
        interpretation.context_requirement
        == "containing_result_for_coordinate_and_realization_context"
    )
    assert interpretation.decomposition_measure == "shared_exclusions_sxpid"
    assert (
        interpretation.coordinate_semantics
        == "source_collection_antichain_mobius_contribution"
    )
    assert (
        interpretation.evidential_scope
        == "statistical_information_under_supplied_distribution"
    )
    assert interpretation.guard_origin == "project_defined"
    assert interpretation.not_established_by_atom_alone == SX_UNSUPPORTED_INFERENCES


def test_default_module_is_stable_and_typed():
    expected = {
        "compute_mi_report",
        "software_identity",
        "compute_categorical_sxpid2",
        "compute_categorical_sxpid3",
        "compute_categorical_sxpid",
        "compute_categorical_imin_pid2",
        "compute_fitted_quantized_sxpid2",
        "EqualWidthQuantizer",
        "ResourceBudget",
        "SxAtomInterpretation",
        "SxAveragedAtom",
        "stable",
        "diagnostics",
    }
    assert expected <= set(dir(pid))
    expects_experimental = os.environ.get("PID_CORE_RS_EXPECT_EXPERIMENTAL") == "1"
    assert hasattr(pid, "experimental") is expects_experimental
    if not expects_experimental:
        assert not any(
            name == "pid_core_rs.experimental"
            or name.startswith("pid_core_rs.experimental.")
            for name in sys.modules
        )
    for removed in (
        "compute_mi",
        "compute_redundancy",
        "compute_pid2",
        "compute_pid3",
        "compute_pid3_partial",
        "compute_quantized_sxpid2",
        "pls_transform",
        "PlsProjector",
    ):
        assert not hasattr(pid, removed), removed
    assert pid.stable.compute_categorical_sxpid2 is not None
    assert pid.diagnostics.diagnose_continuous_input is not None
    assert importlib.import_module("pid_core_rs.stable") is pid.stable
    assert importlib.import_module("pid_core_rs.diagnostics") is pid.diagnostics
    assert pid.stable.__name__ == "pid_core_rs.stable"
    assert issubclass(pid.PidCancelledError, pid.PidRsError)
    assert not hasattr(pid, "SxAtom")
    assert not hasattr(pid.stable, "SxAtom")


def test_software_identity_matches_typed_rust_serialization_contract():
    identity = pid.software_identity()
    assert identity == pid.stable.software_identity()
    assert set(identity) == {
        "identity_format",
        "package_name",
        "package_version",
        "public_rust_api_signature_identity",
        "source",
        "build",
        "reference_artifacts",
        "attestation",
    }
    assert identity["identity_format"] == 1
    assert identity["package_name"] == "pid-core"
    assert isinstance(identity["package_version"], str)
    assert identity["package_version"].strip()
    assert identity["public_rust_api_signature_identity"] == {
        "epoch": 0,
        "revision": 4,
        "scope": "proposed_release_scope_profiles",
        "status": "pre_1_0_review",
    }
    assert identity["attestation"] == "none"

    source = identity["source"]
    assert source["kind"] in {"workspace_git", "cargo_package", "unavailable"}
    if source["kind"] == "unavailable":
        assert set(source) == {"kind", "reason"}
        assert source["reason"] in {
            "invalid_cargo_vcs_info",
            "unrecognized_workspace_layout",
            "git_unavailable",
            "invalid_git_commit",
        }
    else:
        assert set(source) == {
            "kind",
            "commit_sha1",
            "working_tree_scope",
            "working_tree",
        }
        assert len(source["commit_sha1"]) == 40
        assert set(source["commit_sha1"]) <= set("0123456789abcdef")
        assert source["working_tree"] in {"clean", "dirty", "unknown"}
        expected_scope = (
            "crates/pid-core"
            if source["kind"] == "workspace_git"
            else "cargo_vcs_info_dirty_flag"
        )
        assert source["working_tree_scope"] == expected_scope

    build = identity["build"]
    assert set(build) == {
        "rustc_version",
        "target_triple",
        "profile",
        "opt_level",
        "debug_information",
        "enabled_features",
    }
    assert build["rustc_version"] is None or build["rustc_version"].startswith("rustc ")
    assert build["target_triple"]
    assert build["profile"]
    assert build["opt_level"]
    assert isinstance(build["debug_information"], bool)
    assert build["enabled_features"] == sorted(set(build["enabled_features"]))

    artifacts = identity["reference_artifacts"]
    assert [artifact["kind"] for artifact in artifacts] == [
        "method_catalog",
        "proposed_release_scope",
    ]
    for artifact in artifacts:
        assert set(artifact) == {
            "kind",
            "repository_path",
            "schema",
            "schema_revision",
            "digest_scope",
            "canonical_json_sha256",
            "role",
        }
        assert artifact["schema_revision"] == 1
        assert artifact["digest_scope"] == "sha256_of_canonical_file_bytes"
        assert artifact["role"] == "forensic_reference_only"
        assert len(artifact["canonical_json_sha256"]) == 64
        assert set(artifact["canonical_json_sha256"]) <= set("0123456789abcdef")


def test_categorical_sxpid2_and_gate_matches_reference():
    s1, s2, target = gate2([(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)])
    result = pid.compute_categorical_sxpid2(s1, s2, target)
    assert isinstance(result, pid.SxPid2Result)
    with pytest.raises(AttributeError):
        result.status = "rewritten"
    expected_redundancy = 0.12255624891826572 * math.log(2.0)
    assert result.redundancy.net_nats == pytest.approx(expected_redundancy, abs=1e-12)
    atom_sum = sum(
        atom.net_nats
        for atom in (
            result.redundancy,
            result.unique_s1,
            result.unique_s2,
            result.synergy,
        )
    )
    assert atom_sum == pytest.approx(result.mi_s1s2_t_nats, abs=1e-12)
    assert result.pointwise_included is False
    assert result.empirical_pmf.sample_count == len(s1)
    assert result.empirical_pmf.observed_joint_states == 4
    for atom in (
        result.redundancy,
        result.unique_s1,
        result.unique_s2,
        result.synergy,
    ):
        assert_empirical_pmf_averaged_atom(atom)


def test_sx_averaged_atom_interpretation_is_frozen_and_repr_is_explicit():
    s1, s2, target = gate2([(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)])
    atom = pid.compute_categorical_sxpid2(s1, s2, target).synergy
    interpretation = atom.interpretation

    assert_empirical_pmf_averaged_atom(atom)
    with pytest.raises(TypeError):
        pid.SxAveragedAtom()
    with pytest.raises(TypeError):
        pid.SxAtomInterpretation()
    with pytest.raises(AttributeError):
        atom.net_nats = 0.0
    with pytest.raises(AttributeError):
        interpretation.aggregation_scope = "pointwise_distinct_joint_realization"
    assert not hasattr(type(atom), "__float__")
    rendered = repr(atom)
    assert rendered.startswith("SxAveragedAtom(")
    assert "net_nats=" in rendered
    assert "decomposition_measure='shared_exclusions_sxpid'" in rendered
    assert "aggregation_scope='empirical_pmf_average'" in rendered


def test_signed_labels_noncontiguous_and_read_only_are_safe():
    maximum = np.iinfo(np.int64).max
    minimum = np.iinfo(np.int64).min
    base = np.array(
        [[maximum, 9], [maximum, 8], [minimum, 7], [minimum, 6]], dtype=np.int64
    )
    source = base[::-1, :1]
    other = np.array([[11], [-13], [11], [-13]], dtype=np.int64)
    target = np.bitwise_xor(source == maximum, other == 11).astype(np.int64)
    assert not source.flags.c_contiguous
    source.flags.writeable = False
    other.flags.writeable = False
    target.flags.writeable = False
    result = pid.compute_categorical_sxpid2(source, other, target)
    assert math.isfinite(result.mi_s1s2_t_nats)


def test_categorical_encoding_is_invariant_to_label_order_and_magnitude():
    s1, s2, target = gate2([(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)])
    baseline = pid.compute_categorical_sxpid2(s1, s2, target)
    # `np.where` with Python int scalars yields the platform default integer dtype, which is
    # int32 on Windows under NumPy 1.x; the bindings take int64. Pin the dtype explicitly.
    relabeled = pid.compute_categorical_sxpid2(
        np.where(s1 == 0, 10_000, -3).astype(np.int64),
        np.where(s2 == 0, -9_000, 17).astype(np.int64),
        np.where(target == 0, 42, -1_000_000).astype(np.int64),
    )
    assert tuple(
        atom.net_nats
        for atom in (
            relabeled.redundancy,
            relabeled.unique_s1,
            relabeled.unique_s2,
            relabeled.synergy,
        )
    ) == pytest.approx(
        tuple(
            atom.net_nats
            for atom in (
                baseline.redundancy,
                baseline.unique_s1,
                baseline.unique_s2,
                baseline.synergy,
            )
        ),
        abs=1e-12,
    )


def test_canonical_lattice_entries_are_typed_tuples():
    states = np.array([[0], [0], [0], [0], [1], [1], [1], [1]], dtype=np.int64)
    s0 = states
    s1 = np.roll(states, 1, axis=0)
    s2 = np.roll(states, 2, axis=0)
    target = np.bitwise_xor(np.bitwise_xor(s0, s1), s2)
    result = pid.compute_categorical_sxpid3(s0, s1, s2, target)
    assert isinstance(result, pid.SxPidLatticeResult)
    assert len(result.entries) == 18
    assert result.pointwise_included is False
    assert result.empirical_pmf.sample_count == len(target)
    assert all(isinstance(entry.antichain.sets, tuple) for entry in result.entries)
    for entry in result.entries:
        assert_empirical_pmf_averaged_atom(entry.atom)
    selected_atom = result.atom(result.entries[0].antichain.sets)
    assert selected_atom is not None
    assert_empirical_pmf_averaged_atom(selected_atom)
    with pytest.raises(pid.PidInputError) as caught:
        result.atom(range(1_000_000))
    assert caught.value.code == "invalid_antichain"


def test_explicit_imin_comparator_remains_measure_separated():
    # Two-bit COPY: I_min assigns one bit redundancy; shared exclusions assigns log(4/3).
    s1, s2, target = gate2([(0, 0, 0), (0, 1, 1), (1, 0, 2), (1, 1, 3)])
    imin = pid.compute_categorical_imin_pid2(s1, s2, target)
    sx = pid.compute_categorical_sxpid2(s1, s2, target)
    assert isinstance(imin, pid.IminPid2Result)
    assert imin.redundancy_nats == pytest.approx(math.log(2.0), abs=1e-12)
    assert sx.redundancy.net_nats == pytest.approx(math.log(4.0 / 3.0), abs=1e-12)
    assert imin.input_encoding == "categorical"
    assert imin.empirical_pmf.sample_count == len(target)
    assert "different redundancy measure" in imin.warnings[0]


def test_categorical_imin_pid2_preserves_exact_source_swap_bits():
    # Pinned minimal count table [0, 0, 0, 1, 1, 0, 0, 2] in (S1, S2, T)
    # lexicographic bit order. Before the exact represented-operand sum, the two source
    # orders reconstructed synergy as 2^-56 and +0 respectively.
    source_one = np.array([[0], [1], [1], [1]], dtype=np.int64)
    source_two = np.array([[1], [0], [1], [1]], dtype=np.int64)
    target = np.array([[1], [0], [1], [1]], dtype=np.int64)

    original = pid.compute_categorical_imin_pid2(source_one, source_two, target)
    swapped = pid.compute_categorical_imin_pid2(source_two, source_one, target)

    def bits(value: float) -> int:
        return int(np.float64(value).view(np.uint64))

    mapped_original = (
        bits(original.redundancy_nats),
        bits(original.unique_s1_nats),
        bits(original.unique_s2_nats),
        bits(original.synergy_nats),
        bits(original.mi_s1_t_nats),
        bits(original.mi_s2_t_nats),
        bits(original.mi_s1s2_t_nats),
    )
    mapped_swapped = (
        bits(swapped.redundancy_nats),
        bits(swapped.unique_s2_nats),
        bits(swapped.unique_s1_nats),
        bits(swapped.synergy_nats),
        bits(swapped.mi_s2_t_nats),
        bits(swapped.mi_s1_t_nats),
        bits(swapped.mi_s1s2_t_nats),
    )
    assert mapped_original == mapped_swapped
    assert bits(original.synergy_nats) == 0
    assert bits(swapped.synergy_nats) == 0

    historical_original = (
        (original.mi_s1s2_t_nats - original.mi_s1_t_nats)
        - original.mi_s2_t_nats
    ) + original.redundancy_nats
    historical_swapped = (
        (swapped.mi_s1s2_t_nats - swapped.mi_s1_t_nats)
        - swapped.mi_s2_t_nats
    ) + swapped.redundancy_nats
    assert bits(historical_original) == 0x3C70000000000000
    assert bits(historical_swapped) == 0


def test_fitted_quantizer_reuses_edges_and_returns_shaped_numpy():
    training = np.array([[0.0], [10.0]], dtype=np.float64)
    held_out = np.array([[2.0], [8.0]], dtype=np.float64)
    quantizer = pid.EqualWidthQuantizer.fit(
        training,
        2,
        preprocessing_description="raw units",
    )
    assert quantizer.edges == ((0.0, 5.0, 10.0),)
    assert quantizer.resource_budget.max_bytes > 0
    output = quantizer.transform(held_out)
    assert output.values.shape == held_out.shape
    assert output.values.dtype == np.int64
    assert output.values.flags.c_contiguous
    assert not output.values.flags.writeable
    np.testing.assert_array_equal(output.values, np.array([[0], [1]], dtype=np.int64))
    assert output.report.bin_edges == quantizer.edges
    assert output.report.distinct_binary64_edge_value_counts == [3]
    assert output.report.positive_width_interval_counts == [2]
    assert output.report.reachable_binary64_label_counts == [2]
    assert output.report.observed_label_counts == [2]
    assert output.report.nominal_joint_cardinality == 2
    assert output.report.reachable_joint_cardinality == 2
    assert output.report.observed_joint_cardinality == 2
    assert output.report.structurally_unreachable_joint_cells == 0
    assert output.report.unobserved_reachable_joint_cells == 0
    assert output.report.empty_joint_cells == 0
    assert quantizer.training_input_hash_sha256 == (
        "9d1158bcc0470bf1212ba4db233cba701c34f67b6a13a375a1d2bba84a604f90"
    )
    assert (
        output.report.training_input_hash_sha256 == quantizer.training_input_hash_sha256
    )
    assert output.report.transform_input_hash_sha256 == (
        "7acddb067b72df6ae7b441ebd39923a9a7c9a5ae04f9aac79a613f9ba0fdc5cd"
    )
    assert output.report.categorical_output_hash_sha256 == (
        "b863c6850b73a86db3b07bf84c226f6222a2aae536fc79362d596bc15cb392f4"
    )
    same_labels = quantizer.transform(np.array([[1.0], [9.0]], dtype=np.float64))
    assert (
        same_labels.report.transform_input_hash_sha256
        != output.report.transform_input_hash_sha256
    )
    assert (
        same_labels.report.categorical_output_hash_sha256
        == output.report.categorical_output_hash_sha256
    )
    assert not hasattr(output.report, "training_data_hash_sha256")
    assert not hasattr(output.report, "transformed_data_hash_sha256")
    with pytest.raises(ValueError):
        output.values.setflags(write=True)
    with pytest.raises(ValueError):
        output.values[0, 0] = 1

    constant = pid.EqualWidthQuantizer.fit(
        np.array([[3.0], [3.0]], dtype=np.float64),
        4,
        preprocessing_description="declared constant feature",
    )
    constant_output = constant.transform(np.array([[3.0]], dtype=np.float64))
    np.testing.assert_array_equal(constant_output.values, np.array([[0]], dtype=np.int64))
    assert constant_output.report.distinct_binary64_edge_value_counts == [1]
    assert constant_output.report.positive_width_interval_counts == [0]
    assert constant_output.report.reachable_binary64_label_counts == [1]
    assert constant_output.report.observed_label_counts == [1]
    assert constant_output.report.nominal_joint_cardinality == 4
    assert constant_output.report.reachable_joint_cardinality == 1
    assert constant_output.report.structurally_unreachable_joint_cells == 3
    assert constant_output.report.unobserved_reachable_joint_cells == 0
    assert "labels were not compacted" in constant_output.report.warnings[-1]


def test_quantizer_binary64_reachability_handles_adjacent_signed_zero_and_overflow():
    adjacent = np.nextafter(np.float64(1.0), np.float64(np.inf))
    two_steps = np.nextafter(adjacent, np.float64(np.inf))
    quantizer = pid.EqualWidthQuantizer.fit(
        np.array([[1.0], [two_steps]], dtype=np.float64),
        4,
        preprocessing_description="adjacent binary64 reachability",
    )
    output = quantizer.transform(np.array([[1.0], [two_steps]], dtype=np.float64))
    assert output.report.distinct_binary64_edge_value_counts == [3]
    assert output.report.positive_width_interval_counts == [2]
    assert output.report.reachable_binary64_label_counts == [3]
    assert output.report.observed_label_counts == [2]
    assert output.report.reachable_joint_cardinality == 3
    assert output.report.structurally_unreachable_joint_cells == 1
    assert output.report.unobserved_reachable_joint_cells == 1
    assert output.report.empty_joint_cells == 2
    np.testing.assert_array_equal(output.values[:, 0], np.array([0, 3]))

    signed_zero = pid.EqualWidthQuantizer.fit(
        np.array([[-0.0], [0.0]], dtype=np.float64),
        4,
        preprocessing_description="signed-zero structural diagnostic",
    ).transform(np.array([[-0.0], [0.0]], dtype=np.float64))
    assert signed_zero.report.distinct_binary64_edge_value_counts == [2]
    assert signed_zero.report.positive_width_interval_counts == [0]
    assert signed_zero.report.reachable_binary64_label_counts == [1]
    assert signed_zero.report.observed_label_counts == [1]

    dimensions = 129
    constant_data = np.ones((1, dimensions), dtype=np.float64)
    overflow = pid.EqualWidthQuantizer.fit(
        constant_data,
        2,
        preprocessing_description="u128 nominal-cardinality overflow",
    ).transform(constant_data)
    assert overflow.report.nominal_joint_cardinality is None
    assert overflow.report.reachable_joint_cardinality == 1
    assert overflow.report.structurally_unreachable_joint_cells is None
    assert overflow.report.unobserved_reachable_joint_cells == 0


def test_quantizer_out_of_range_policy_is_structured():
    training = np.array([[0.0], [10.0]], dtype=np.float64)
    strict = pid.EqualWidthQuantizer.fit(
        training,
        2,
        preprocessing_description="raw units",
    )
    with pytest.raises(pid.PidInputError) as caught:
        strict.transform(np.array([[11.0]], dtype=np.float64))
    assert caught.value.code == "quantizer_out_of_range"
    assert caught.value.fields["column"] == "0"

    clamped = pid.EqualWidthQuantizer.fit(
        training,
        2,
        preprocessing_description="raw units",
        out_of_range_policy="clamp_to_boundary",
    )
    output = clamped.transform(np.array([[-1.0], [11.0]], dtype=np.float64))
    np.testing.assert_array_equal(output.values[:, 0], np.array([0, 1]))
    assert output.report.out_of_range_policy == "clamp_to_boundary"


def test_fitted_quantized_sxpid_attaches_all_reports():
    s1, s2, target = gate2([(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)])
    f1, f2, ft = (value.astype(np.float64) for value in (s1, s2, target))
    quantizers = [
        pid.EqualWidthQuantizer.fit(
            value,
            2,
            preprocessing_description="identity conversion from declared binary values",
        )
        for value in (f1, f2, ft)
    ]
    result = pid.compute_fitted_quantized_sxpid2(
        f1, f2, ft, quantizers[0], quantizers[1], quantizers[2]
    )
    assert isinstance(result, pid.QuantizedSxPid2Result)
    assert result.pid.status == "quantized_estimand"
    assert result.pid.synergy.net_nats == pytest.approx(math.log(4.0 / 3.0), abs=1e-12)
    assert result.source1_quantization.n_rows == len(s1)
    assert result.target_quantization.num_bins == 2
    for atom in (
        result.pid.redundancy,
        result.pid.unique_s1,
        result.pid.unique_s2,
        result.pid.synergy,
    ):
        assert_empirical_pmf_averaged_atom(atom)


def test_error_codes_for_empty_nonfinite_and_budget_preflight():
    empty = np.empty((0, 1), dtype=np.int64)
    with pytest.raises(pid.PidInputError) as caught:
        pid.compute_categorical_sxpid2(empty, empty, empty)
    assert caught.value.code == "empty_matrix"

    empty_columns = np.empty((4, 0), dtype=np.int64)
    with pytest.raises(pid.PidInputError) as caught:
        pid.compute_categorical_sxpid2(empty_columns, empty_columns, empty_columns)
    assert caught.value.code == "empty_matrix"

    with pytest.raises(pid.PidInputError) as caught:
        pid.EqualWidthQuantizer.fit(
            np.array([[0.0], [np.nan]], dtype=np.float64),
            2,
            preprocessing_description="raw units",
        )
    assert caught.value.code == "non_finite_input"

    tiny = pid.ResourceBudget(
        max_bytes=1024,
        max_pairwise_distances=1,
        max_operations_hint=10_000,
        max_threads=1,
    )
    with pytest.raises(pid.PidResourceError) as caught:
        pid.distance_concentration_report(
            np.array([[0.0], [1.0], [2.0]], dtype=np.float64), budget=tiny
        )
    assert caught.value.code == "resource_limit_exceeded"
    assert caught.value.fields["resource"] == "pairwise_distances"

    aggregate_tiny = pid.ResourceBudget(
        max_bytes=200,
        max_pairwise_distances=10_000,
        max_operations_hint=1_000_000,
        max_threads=1,
    )
    labels = np.arange(4, dtype=np.int64).reshape(4, 1)
    with pytest.raises(pid.PidResourceError) as caught:
        pid.compute_categorical_sxpid2(labels, labels, labels, budget=aggregate_tiny)
    assert caught.value.code == "resource_limit_exceeded"
    assert caught.value.fields["resource"] == "bytes"


def test_huge_broadcast_view_is_rejected_before_owned_copy():
    huge = np.broadcast_to(
        np.array([[1.0]], dtype=np.float64),
        (100_000_000, 1),
    )
    tiny = pid.ResourceBudget(
        max_bytes=1024,
        max_pairwise_distances=10_000,
        max_operations_hint=1_000_000,
        max_threads=1,
    )
    with pytest.raises(pid.PidResourceError) as caught:
        pid.diagnose_continuous_input(huge, k=3, budget=tiny)
    assert caught.value.code == "resource_limit_exceeded"
    assert caught.value.fields["resource"] == "bytes"


def test_huge_source_sequence_is_rejected_before_rust_sequence_copy():
    target = np.array([[0], [1]], dtype=np.int64)
    with pytest.raises(pid.PidInputError) as caught:
        pid.compute_categorical_sxpid(range(100_000_000), target)
    assert caught.value.code == "unsupported_source_count"
    assert caught.value.fields["source_count"] == "100000000"


def test_categorical_source_sequence_fetches_each_item_exactly_once():
    source1 = np.array([[0], [0], [1], [1]], dtype=np.int64)
    source2 = np.array([[0], [1], [0], [1]], dtype=np.int64)
    target = np.array([[0], [1], [1], [0]], dtype=np.int64)

    class SingleFetchSequence(list):
        def __init__(self, values):
            super().__init__(values)
            self.calls = [0] * len(values)

        def __getitem__(self, index):
            self.calls[index] += 1
            if self.calls[index] != 1:
                raise AssertionError(f"source {index} was fetched more than once")
            return super().__getitem__(index)

    sources = SingleFetchSequence([source1, source2])
    result = pid.compute_categorical_sxpid(sources, target)

    assert result.n_sources == 2
    assert sources.calls == [1, 1]


def test_categorical_source_sequence_cannot_inflate_after_preflight():
    source1 = np.array([[0], [0], [1], [1]], dtype=np.int64)
    source2 = np.array([[0], [1], [0], [1]], dtype=np.int64)
    target = np.array([[0], [1], [1], [0]], dtype=np.int64)
    inflated = np.broadcast_to(
        np.array([[1]], dtype=np.int64),
        (1_000_000, 1),
    )

    class InflatingSequence(list):
        def __init__(self, values):
            super().__init__(values)
            self.calls = [0] * len(values)

        def __getitem__(self, index):
            self.calls[index] += 1
            if self.calls[index] == 1:
                return super().__getitem__(index)
            return inflated

    budget = pid.ResourceBudget(
        max_bytes=1_000_000,
        max_pairwise_distances=100_000,
        max_operations_hint=10_000_000,
        max_threads=1,
    )
    sources = InflatingSequence([source1, source2])
    result = pid.compute_categorical_sxpid(sources, target, budget=budget)

    assert result.n_sources == 2
    assert sources.calls == [1, 1]


def test_categorical_source_cross_item_mutation_cannot_abort_or_bypass_budget():
    script = textwrap.dedent(
        """
        import numpy as np
        import pid_core_rs as pid

        n = 100
        source0 = np.zeros((1, 1), dtype=np.int64)
        source1 = np.zeros((1, 1), dtype=np.int64)
        source2 = np.zeros((1, 1), dtype=np.int64)
        source3 = np.zeros((n, 1), dtype=np.int64)
        target = np.zeros((1, 1), dtype=np.int64)

        class CrossItemMutatingSequence(list):
            def __getitem__(self, index):
                # Mutate an item whose callback already returned. The binding must not hold a
                # NumPy borrow guard across this user callback, and aggregate preflight must see
                # every final n-row shape rather than the earlier one-row shapes.
                if index == 0:
                    target.resize((n, 1), refcheck=False)
                elif index == 1:
                    source0.resize((n, 1), refcheck=False)
                elif index == 2:
                    source1.resize((n, 1), refcheck=False)
                elif index == 3:
                    source2.resize((n, 1), refcheck=False)
                return super().__getitem__(index)

        sources = CrossItemMutatingSequence([source0, source1, source2, source3])
        budget = pid.ResourceBudget(
            max_bytes=7_000,
            max_pairwise_distances=100_000,
            max_operations_hint=100_000_000,
            max_threads=1,
        )
        try:
            pid.compute_categorical_sxpid(sources, target, budget=budget)
        except pid.PidResourceError as error:
            assert error.code == "resource_limit_exceeded"
            assert error.fields["resource"] == "bytes"
            print("RESOURCE_REJECTED", flush=True)
        else:
            raise AssertionError("cross-item growth bypassed aggregate resource preflight")
        """
    )

    process = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert process.stdout == "RESOURCE_REJECTED\n"


@pytest.mark.skipif(
    not hasattr(signal, "setitimer"),
    reason="requires a Unix interval timer to inject a signal during the native copy",
)
def test_numpy_copy_releases_borrow_before_running_python_signal_handler():
    script = textwrap.dedent(
        """
        import signal

        import numpy as np
        import pid_core_rs as pid

        training = None
        handled = False

        def resize_input(_signum, _frame):
            global handled
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            training.resize((2, 1), refcheck=False)
            handled = True

        signal.signal(signal.SIGALRM, resize_input)
        quantizer = None
        for _attempt in range(3):
            training = np.linspace(0.0, 1.0, 2_000_000, dtype=np.float64).reshape(-1, 1).copy()
            handled = False
            signal.setitimer(signal.ITIMER_REAL, 0.005, 0.005)
            candidate = pid.EqualWidthQuantizer.fit(
                training,
                2,
                preprocessing_description="signal mutation regression",
            )
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            if handled and candidate.edges[0][-1] == 1.0:
                quantizer = candidate
                break

        assert quantizer is not None, "timer did not fire after the native copy began"
        assert training.shape == (2, 1)
        # Re-borrowing the resized array catches a stale rust-numpy borrow key. The first native
        # copy must have consumed and released its guard before the signal handler ran.
        pid.EqualWidthQuantizer.fit(
            training,
            2,
            preprocessing_description="post-resize reborrow",
        )
        output = quantizer.transform(np.array([[0.25], [0.75]], dtype=np.float64))
        assert output.values.tolist() == [[0], [1]]
        print("SIGNAL_MUTATION_SAFE", flush=True)
        """
    )

    process = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert process.stdout == "SIGNAL_MUTATION_SAFE\n"


def test_error_annotation_callbacks_run_after_numpy_borrows_are_released():
    script = textwrap.dedent(
        """
        import numpy as np
        import pid_core_rs as pid

        def exercise(error_type, array, invoke, expected_code):
            original_setattr = error_type.__setattr__
            callback_count = 0

            def resize_from_error_annotation(self, name, value):
                nonlocal callback_count
                if callback_count == 0:
                    array.resize((2, 1), refcheck=False)
                callback_count += 1
                return original_setattr(self, name, value)

            error_type.__setattr__ = resize_from_error_annotation
            try:
                try:
                    invoke()
                except error_type as error:
                    assert error.code == expected_code
                else:
                    raise AssertionError(f"expected {error_type.__name__}")
            finally:
                error_type.__setattr__ = original_setattr

            assert callback_count >= 2
            assert array.shape == (2, 1)

        resource_input = np.arange(4, dtype=np.float64).reshape(-1, 1).copy()
        tiny_budget = pid.ResourceBudget(max_bytes=1)
        exercise(
            pid.PidResourceError,
            resource_input,
            lambda: pid.EqualWidthQuantizer.fit(
                resource_input,
                2,
                preprocessing_description="resource error callback",
                budget=tiny_budget,
            ),
            "resource_limit_exceeded",
        )
        # Re-borrowing catches a stale rust-numpy key left by callback-driven resize.
        pid.EqualWidthQuantizer.fit(
            resource_input,
            2,
            preprocessing_description="resource callback reborrow",
        )

        nonfinite_input = np.array([[0.0], [1.0], [np.nan]], dtype=np.float64)
        exercise(
            pid.PidInputError,
            nonfinite_input,
            lambda: pid.EqualWidthQuantizer.fit(
                nonfinite_input,
                2,
                preprocessing_description="input error callback",
            ),
            "non_finite_input",
        )
        pid.EqualWidthQuantizer.fit(
            nonfinite_input,
            2,
            preprocessing_description="input callback reborrow",
        )
        print("ERROR_CALLBACKS_SAFE", flush=True)
        """
    )

    process = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert process.stdout == "ERROR_CALLBACKS_SAFE\n"


def test_mi_report_preserves_core_report_contract():
    rng = np.random.default_rng(17)
    x = rng.normal(size=(180, 1))
    y = x + 0.6 * rng.normal(size=(180, 1))
    declared_budget = pid.ResourceBudget(
        max_bytes=128_000_000,
        max_pairwise_distances=1_000_000,
        max_operations_hint=1_000_000_000,
        max_threads=1,
    )
    result = pid.compute_mi_report(
        x,
        y,
        k=4,
        training_split_id="train-v1",
        evaluation_split_id="eval-v1",
        budget=declared_budget,
        **PROVENANCE,
    )
    assert isinstance(result, pid.MiReport)
    assert math.isfinite(result.value_nats)
    assert result.signed_value_nats == result.value_nats
    assert result.status == "conditional_continuous"
    assert result.method_status == "restricted_domain"
    assert result.backend in {"brute_force", "exact_chebyshev_kd_tree"}
    assert not hasattr(result, "backend_fallback_occurred")
    assert result.estimand.units == "nats"
    assert result.provenance.training_split_id == "train-v1"
    assert len(result.provenance.input_hashes_sha256) == 2
    assert result.resource_estimate.pairwise_distances > 0
    assert result.resource_budget.max_bytes == declared_budget.max_bytes
    assert result.resource_estimate.estimated_bytes <= declared_budget.max_bytes
    assert result.local_diagnostics.joint_radius.min > 0.0
    assert result.assumption_ledger
    assert "diagnostics_do_not_prove_population_assumptions" in result.warning_codes


def test_noncontiguous_float_diagnostics_and_read_only_input():
    values = np.arange(120, dtype=np.float64).reshape(20, 6)[:, ::2]
    assert not values.flags.c_contiguous
    values.flags.writeable = False
    report = pid.diagnose_continuous_input(values, k=3)
    assert report.n_samples == 20
    assert report.ambient_dimension == 3
    assert isinstance(report.coordinates, tuple)
    assert report.coordinates[0].minimum_positive_spacing is not None
    assert report.coordinates[0].unrepresentable_positive_spacings == 0


def test_owned_copy_isolated_from_concurrent_numpy_mutation():
    values = np.arange(27_000, dtype=np.float64).reshape(9_000, 3)
    expected = pid.distance_concentration_report(values.copy())
    started = threading.Event()
    result: list[pid.DistanceConcentrationReport] = []

    def worker() -> None:
        started.set()
        result.append(pid.distance_concentration_report(values))

    thread = threading.Thread(target=worker)
    thread.start()
    assert started.wait(timeout=2)
    # Give the worker a scheduling opportunity. The main thread can resume only after the wrapper
    # has copied the NumPy buffer and detached with Rust-owned memory.
    time.sleep(0.02)
    assert thread.is_alive()
    values.fill(0.0)
    thread.join(timeout=20)
    assert not thread.is_alive()
    assert len(result) == 1
    assert result[0].pairwise_mean == expected.pairwise_mean
    assert result[0].nn_mean == expected.nn_mean


def test_long_rust_computation_releases_the_gil():
    values = np.arange(27_000, dtype=np.float64).reshape(9_000, 3)
    started = threading.Event()
    failures: list[BaseException] = []

    def worker() -> None:
        started.set()
        try:
            pid.distance_concentration_report(values)
        except (
            BaseException
        ) as error:  # pragma: no cover - diagnostic aid on CI failure
            failures.append(error)

    thread = threading.Thread(target=worker)
    thread.start()
    assert started.wait(timeout=2)
    # The sleep gives the worker time to enter Rust. If Rust retained the GIL, this thread could
    # not resume to observe the worker until the call had completed.
    time.sleep(0.02)
    observed_while_running = thread.is_alive()
    thread.join(timeout=30)
    assert not thread.is_alive()
    assert not failures
    assert observed_while_running, "long Rust call retained the GIL"


@pytest.mark.skipif(os.name == "nt", reason="POSIX SIGINT subprocess contract")
def test_sigint_cancels_and_joins_long_rust_worker_promptly():
    script = textwrap.dedent(
        """
        import time
        import numpy as np
        import pid_core_rs as pid
        # 49,995,000 pairs × 128 coordinates: comfortably within default declared budgets, but
        # intentionally far too much work to finish at the cancellation latency asserted below.
        values = np.arange(1_280_000, dtype=np.float64).reshape(10_000, 128)
        print("READY", flush=True)
        started = time.monotonic()
        try:
            pid.distance_concentration_report(values)
        except KeyboardInterrupt:
            elapsed = time.monotonic() - started
            idle_cpu_samples = []
            for _ in range(3):
                cpu_before_idle = time.process_time()
                time.sleep(0.25)
                idle_cpu_samples.append(time.process_time() - cpu_before_idle)
            # Output occurs only after the Rust worker has been joined. A mistakenly orphaned
            # worker spins throughout every idle sentinel interval; taking the minimum preserves
            # that signal while ignoring an isolated virtualized-runner scheduling spike.
            print(
                f"INTERRUPTED {elapsed:.6f} {min(idle_cpu_samples):.6f}",
                flush=True,
            )
        """
    )
    process = subprocess.Popen(
        [sys.executable, "-c", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    ready = process.stdout.readline()
    assert ready == "READY\n"
    time.sleep(0.1)
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
    remaining_stdout, stderr = process.communicate(timeout=8)
    stdout = ready + remaining_stdout
    assert process.returncode == 0, stderr
    interrupted = next(
        (line for line in stdout.splitlines() if line.startswith("INTERRUPTED ")),
        None,
    )
    assert interrupted is not None, stdout
    _, elapsed_text, idle_cpu_text = interrupted.split()
    assert float(elapsed_text) < 5.0, stdout
    # A truly orphaned spinning worker burns ~the whole of every 0.25 s sentinel window; a
    # healthy joined process measures ~2e-5 s (median over 25 runs on Apple Silicon). Requiring
    # only one of three intervals to fall below the bound tolerates an isolated virtualized-CI
    # scheduling spike without masking the continuous CPU signature of an orphaned worker.
    assert float(idle_cpu_text) < 0.2, stdout
