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


def lorentz_line_points() -> np.ndarray:
    parameters = np.array(
        [0.0, 0.07, 0.23, 0.51, 0.94, 1.58, 2.47, 3.61, 5.02],
        dtype=np.float64,
    )
    return np.ascontiguousarray(
        np.column_stack((np.cosh(parameters), np.sinh(parameters)))
    )


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


def test_hyperbolic_diagnostic_migration_paths_accept_lorentz_points():
    module = migration()
    points = lorentz_line_points()

    diagnostics = module.continuous_input_diagnostics(
        points,
        k=3,
        metric="hyperbolic_lorentz",
    )
    assert diagnostics["n_samples"] == points.shape[0]
    assert diagnostics["ambient_dimension"] == points.shape[1]

    intrinsic_dimension = module.estimate_intrinsic_dimension(
        points,
        k=3,
        metric="hyperbolic_lorentz",
    )
    assert np.isfinite(intrinsic_dimension)
    assert intrinsic_dimension > 0.0

    concentration = module.distance_stats(points, metric="hyperbolic_lorentz")
    assert concentration["pairwise_count"] == points.shape[0] * (points.shape[0] - 1) // 2
    assert np.isfinite(concentration["pairwise_mean"])

    four_point = module.sampled_four_point_delta_summary(
        points,
        n_samples=16,
        metric="hyperbolic_lorentz",
        seed=7,
    )
    assert four_point["sample_count"] == 16
    assert np.isfinite(four_point["mean"])

    with pytest.warns(DeprecationWarning):
        mean_delta = module.estimate_gromov_delta(
            points,
            n_samples=16,
            metric="hyperbolic_lorentz",
            seed=7,
        )
    assert mean_delta == four_point["mean"]


def test_hyperbolic_mi_report_preserves_typed_geometry_and_warning():
    points = lorentz_line_points()
    rng = np.random.default_rng(2_912_871_909)
    target_1 = rng.uniform(-0.6, 0.6, points.shape[0])
    target_2 = rng.uniform(-0.6, 0.6, points.shape[0])
    target = np.ascontiguousarray(
        np.column_stack(
            (
                np.hypot(np.hypot(target_1, target_2), 1.0),
                target_1,
                target_2,
            )
        )
    )

    report = migration().compute_mi_report(
        points,
        target,
        k=3,
        metric="hyperbolic_lorentz",
        support_contract="assume_smooth_manifold",
        preprocessing_description="fixed Lorentz-coordinate fixture",
        observation_model_description="smooth manifold-valued observations with finite MI",
        embedding_training_provenance="fixed test embedding; no learned parameters",
    )

    assert report["config"]["metric"] == "hyperbolic_lorentz"
    assert report["method"]["status"] == "experimental"
    assert report["method"]["geometry_model"] == "lorentz_hyperboloid"
    assert report["method"]["curvature"] == -1.0
    assert report["method"]["x_hyperbolic_dimension"] == 1
    assert report["method"]["y_hyperbolic_dimension"] == 2
    assert "hyperbolic_consistency_not_established" in {
        warning["code"] for warning in report["warnings"]
    }
