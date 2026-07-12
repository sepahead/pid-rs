"""Focused safety checks for the default-off deprecated migration module."""

from __future__ import annotations

import numpy as np
import pytest

import pid_core_rs as pid


pytestmark = pytest.mark.skipif(
    not hasattr(pid, "experimental"),
    reason="requires a wheel built with the python-experimental feature",
)


def migration():
    return pid.experimental.migration


def test_fixed_migration_resource_policy_is_explicit():
    module = migration()
    assert module.RESOURCE_MAX_BYTES == 1 << 30
    assert module.RESOURCE_MAX_OPERATIONS_HINT == 10_000_000_000
    assert "CPython" in module.RESOURCE_POLICY


@pytest.mark.parametrize(
    ("function_name", "dtype"),
    [
        ("compute_discrete_sxpid_n", np.int64),
        ("compute_quantized_sxpid_n", np.float64),
    ],
)
def test_n_source_calls_reject_huge_sequences_before_item_extraction(
    function_name: str,
    dtype,
):
    target = np.array([[0], [1]], dtype=dtype)
    with pytest.raises(ValueError, match="exactly two to 4 sources"):
        # Integer items would fail matrix extraction; the source-count error proves length is
        # checked first without materializing or visiting this enormous built-in sequence.
        getattr(migration(), function_name)(range(100_000_000), target)


def test_preprocessing_output_shape_is_rejected_before_core_allocation():
    values = np.array([[1.0], [2.0]], dtype=np.float64)
    with pytest.raises(MemoryError, match="resource limit exceeded"):
        migration().hash_project(values, 100_000_000)


def test_report_provenance_is_bounded_before_owned_copy():
    values = np.array([[0.0], [1.0], [2.0], [3.0]], dtype=np.float64)
    with pytest.raises(ValueError, match="too long"):
        migration().compute_mi_report(
            values,
            values,
            preprocessing_description="x" * (16 * 1024 + 1),
            observation_model_description="continuous fixture",
        )


def test_bounded_n_source_and_preprocessing_outputs_remain_compatible():
    s1 = np.array([[0], [0], [1], [1]], dtype=np.int64)
    s2 = np.array([[0], [1], [0], [1]], dtype=np.int64)
    target = np.bitwise_xor(s1, s2)
    lattice = migration().compute_discrete_sxpid_n([s1, s2], target)
    assert lattice

    projected = migration().hash_project(
        np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64),
        1,
    )
    assert projected["nrows"] == 2
    assert projected["ncols"] == 1
    assert len(projected["data"]) == 2
