"""Contract tests for the stable pid_core_rs 1.x extension surface."""

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


def gate2(rows: list[tuple[int, int, int]], repetitions: int = 8):
    repeated = rows * repetitions
    return tuple(
        np.asarray([[row[index]] for row in repeated], dtype=np.int64)
        for index in range(3)
    )


def test_default_module_is_stable_and_typed():
    expected = {
        "compute_mi_report",
        "compute_categorical_sxpid2",
        "compute_categorical_sxpid3",
        "compute_categorical_sxpid",
        "compute_categorical_imin_pid2",
        "compute_fitted_quantized_sxpid2",
        "EqualWidthQuantizer",
        "ResourceBudget",
        "stable",
        "diagnostics",
    }
    assert expected <= set(dir(pid))
    expects_experimental = os.environ.get("PID_CORE_RS_EXPECT_EXPERIMENTAL") == "1"
    assert hasattr(pid, "experimental") is expects_experimental
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
    assert result.atom(result.entries[0].antichain.sets) is not None
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
    np.testing.assert_array_equal(output.values, np.array([[0], [1]], dtype=np.int64))
    assert output.report.bin_edges == quantizer.edges
    assert len(output.report.training_data_hash_sha256) == 64
    assert len(output.report.transformed_data_hash_sha256) == 64

    constant = pid.EqualWidthQuantizer.fit(
        np.array([[3.0], [3.0]], dtype=np.float64),
        4,
        preprocessing_description="declared constant feature",
    )
    np.testing.assert_array_equal(
        constant.transform(np.array([[3.0]], dtype=np.float64)).values,
        np.array([[0]], dtype=np.int64),
    )


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
    assert result.backend_fallback_occurred is False
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
        except BaseException as error:  # pragma: no cover - diagnostic aid on CI failure
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
            cpu_before_idle = time.process_time()
            time.sleep(0.25)
            idle_cpu = time.process_time() - cpu_before_idle
            # Output occurs only after the Rust worker has been joined. Low process CPU during
            # the idle sentinel interval detects a mistakenly orphaned worker.
            print(f"INTERRUPTED {elapsed:.6f} {idle_cpu:.6f}", flush=True)
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
    assert float(idle_cpu_text) < 0.1, stdout
