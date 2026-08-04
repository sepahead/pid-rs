"""Focused safety checks for the default-off deprecated migration module."""

from __future__ import annotations

import numpy as np
import pytest

import pid_core_rs as pid


pytestmark = pytest.mark.skipif(
    not hasattr(pid, "experimental"),
    reason="requires a wheel built with the python-experimental feature",
)

MIGRATION_POLICY_ATTRIBUTES = frozenset(
    {
        "RESOURCE_MAX_BYTES",
        "RESOURCE_MAX_OPERATIONS_HINT",
        "RESOURCE_POLICY",
    }
)
MIGRATION_CLASSES = frozenset({"PlsProjector"})
MIGRATION_FUNCTIONS = frozenset(
    {
        "compute_co_information",
        "compute_discrete_pid2",
        "compute_discrete_pid3",
        "compute_discrete_sxpid2",
        "compute_discrete_sxpid3",
        "compute_discrete_sxpid_n",
        "compute_invariants",
        "compute_mi",
        "compute_mi_report",
        "compute_pid2",
        "compute_pid2_report",
        "compute_pid3",
        "compute_pid3_partial",
        "compute_quantized_sxpid2",
        "compute_quantized_sxpid3",
        "compute_quantized_sxpid_n",
        "compute_redundancy",
        "continuous_input_diagnostics",
        "distance_stats",
        "estimate_gromov_delta",
        "estimate_intrinsic_dimension",
        "hash_project",
        "pca_transform",
        "pls_transform",
        "sampled_four_point_delta_summary",
        "standardize",
    }
)


def migration():
    return pid.experimental.migration


def test_migration_public_surface_matches_exact_allowlist():
    module = migration()
    expected = MIGRATION_POLICY_ATTRIBUTES | MIGRATION_CLASSES | MIGRATION_FUNCTIONS
    observed = {name for name in dir(module) if not name.startswith("_")}

    assert observed == expected
    assert all(callable(getattr(module, name)) for name in MIGRATION_FUNCTIONS)
    assert all(isinstance(getattr(module, name), type) for name in MIGRATION_CLASSES)


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


def test_compute_invariants_returns_coherent_bounded_summary():
    rng = np.random.default_rng(7_420_031)
    latent = rng.normal(size=(96, 1))
    s1 = np.ascontiguousarray(latent + 0.35 * rng.normal(size=(96, 1)))
    s2 = np.ascontiguousarray(0.55 * latent + rng.normal(size=(96, 1)))
    target = np.ascontiguousarray(0.8 * s1 - 0.4 * s2 + 0.5 * rng.normal(size=(96, 1)))

    result = migration().compute_invariants(
        s1,
        s2,
        target,
        k=3,
        support_contract="assume_regular_full_dimensional",
    )

    assert set(result) == {
        "mi_s1_t",
        "mi_s2_t",
        "mi_s1s2_t",
        "co_information",
        "r_bar",
        "v_bar",
    }
    expected_co_information = (
        result["mi_s1_t"] + result["mi_s2_t"] - result["mi_s1s2_t"]
    )
    assert result["co_information"] == pytest.approx(
        expected_co_information,
        rel=0.0,
        abs=1e-12,
    )
    assert np.isfinite(result["r_bar"])
    assert np.isfinite(result["v_bar"])


@pytest.mark.parametrize(
    "method",
    [
        "heuristic_sketch",
        "local_min_ksg",
        "disjunction_from_local_mi",
    ],
)
def test_formula_labelled_heuristics_are_reachable_through_declared_wrappers(
    method: str,
):
    rng = np.random.default_rng(2_031)
    base = rng.normal(size=(250, 1))
    s1 = np.ascontiguousarray(base + 0.01 * rng.normal(size=(250, 1)))
    s2 = np.ascontiguousarray(base + 0.01 * rng.normal(size=(250, 1)))
    target = np.ascontiguousarray(base)

    paper_redundancy = migration().compute_redundancy(
        s1,
        s2,
        target,
        k=3,
        method="ehrlich_ksg",
        support_contract="assume_regular_full_dimensional",
    )
    redundancy = migration().compute_redundancy(
        s1,
        s2,
        target,
        k=3,
        method=method,
        support_contract="assume_regular_full_dimensional",
    )
    atoms = migration().compute_pid2(
        s1,
        s2,
        target,
        k=3,
        method=method,
        support_contract="assume_regular_full_dimensional",
    )

    assert np.isfinite(redundancy)
    assert abs(redundancy - paper_redundancy) > 1e-6
    assert atoms["redundancy"] == pytest.approx(redundancy, rel=0.0, abs=1e-12)
    assert all(np.isfinite(value) for value in atoms.values())


def test_formula_labelled_heuristic_method_token_is_not_ignored():
    values = np.arange(24, dtype=np.float64).reshape(12, 2)
    with pytest.raises(ValueError, match="Unknown method"):
        migration().compute_redundancy(
            values,
            values + 0.25,
            values - 0.5,
            method="not_a_method",
            support_contract="assume_regular_full_dimensional",
        )


@pytest.mark.parametrize(
    ("function_name", "dtype", "warning_pattern"),
    [
        ("compute_discrete_sxpid_n", np.int64, "omits typed atom interpretation"),
        (
            "compute_quantized_sxpid_n",
            np.float64,
            "num_bins-only quantization-provenance",
        ),
    ],
)
def test_n_source_calls_reject_huge_sequences_before_item_extraction(
    function_name: str,
    dtype,
    warning_pattern: str,
):
    target = np.array([[0], [1]], dtype=dtype)
    with pytest.warns(DeprecationWarning, match=warning_pattern):
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


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "negative_handling": "not-a-policy",
                "support_contract": "assume_smooth_manifold",
            },
            "Unknown negative_handling",
        ),
        ({"support_contract": "not-a-contract"}, "Unknown support_contract"),
    ],
)
def test_hyperbolic_compute_mi_parses_config_before_report_only_rejection(
    overrides: dict[str, str],
    message: str,
):
    points = lorentz_line_points()
    with pytest.raises(ValueError, match=message):
        migration().compute_mi(
            points,
            points,
            metric="hyperbolic_lorentz",
            **overrides,
        )


def test_hyperbolic_compute_mi_checks_shape_before_report_only_rejection():
    points = lorentz_line_points()
    with pytest.raises(ValueError, match="row count mismatch"):
        migration().compute_mi(
            points,
            points[:-1],
            metric="hyperbolic_lorentz",
            support_contract="assume_smooth_manifold",
        )


def test_hyperbolic_compute_mi_checks_support_before_report_only_rejection():
    points = lorentz_line_points()
    with pytest.raises(
        ValueError,
        match="support contract `known_quantized` is unsupported",
    ):
        migration().compute_mi(
            points,
            points,
            metric="hyperbolic_lorentz",
            support_contract="quantized",
        )


def test_valid_hyperbolic_compute_mi_reaches_report_only_rejection():
    points = lorentz_line_points()
    with pytest.raises(ValueError, match="available only through compute_mi_report"):
        migration().compute_mi(
            points,
            points,
            metric="hyperbolic_lorentz",
            support_contract="assume_smooth_manifold",
        )


def test_chebyshev_smooth_support_keeps_explicit_path_error():
    points = lorentz_line_points()
    message = "available only with an explicitly hyperbolic report"
    with pytest.raises(ValueError, match=message):
        migration().compute_mi(
            points,
            points,
            metric="chebyshev",
            support_contract="assume_smooth_manifold",
        )
    with pytest.raises(ValueError, match=message):
        migration().compute_mi_report(
            points,
            points[:-1],
            metric="chebyshev",
            support_contract="assume_smooth_manifold",
            preprocessing_description="",
            observation_model_description="continuous fixture",
        )


def test_hyperbolic_compute_mi_report_checks_provenance_before_support_compatibility():
    points = lorentz_line_points()
    with pytest.raises(ValueError, match="preprocessing_description must be nonempty"):
        migration().compute_mi_report(
            points,
            points,
            metric="hyperbolic_lorentz",
            support_contract="quantized",
            preprocessing_description="",
            observation_model_description="continuous fixture",
        )


def test_hyperbolic_compute_mi_report_parses_support_before_provenance():
    points = lorentz_line_points()
    with pytest.raises(ValueError, match="Unknown support_contract"):
        migration().compute_mi_report(
            points,
            points,
            metric="hyperbolic_lorentz",
            support_contract="not-a-contract",
            preprocessing_description="",
            observation_model_description="continuous fixture",
        )


def test_hyperbolic_compute_mi_report_checks_shape_before_support_compatibility():
    points = lorentz_line_points()
    with pytest.raises(ValueError, match="row count mismatch"):
        migration().compute_mi_report(
            points,
            points[:-1],
            metric="hyperbolic_lorentz",
            support_contract="quantized",
            preprocessing_description="fixed Lorentz-coordinate fixture",
            observation_model_description="continuous fixture",
        )


def test_hyperbolic_compute_mi_report_rejects_incompatible_support():
    points = lorentz_line_points()
    with pytest.raises(
        ValueError,
        match="support contract `known_quantized` is unsupported",
    ):
        migration().compute_mi_report(
            points,
            points,
            metric="hyperbolic_lorentz",
            support_contract="quantized",
            preprocessing_description="fixed Lorentz-coordinate fixture",
            observation_model_description="continuous fixture",
        )


def test_bounded_n_source_and_preprocessing_outputs_remain_compatible():
    s1 = np.array([[0], [0], [1], [1]], dtype=np.int64)
    s2 = np.array([[0], [1], [0], [1]], dtype=np.int64)
    target = np.bitwise_xor(s1, s2)
    with pytest.warns(DeprecationWarning, match="omits typed atom interpretation"):
        lattice = migration().compute_discrete_sxpid_n([s1, s2], target)
    assert lattice

    projected = migration().hash_project(
        np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64),
        1,
    )
    assert projected["nrows"] == 2
    assert projected["ncols"] == 1
    assert len(projected["data"]) == 2


def test_same_sample_imin_adapters_warn_about_measure_and_provenance_loss():
    states = np.array(
        [
            [0, 0, 0],
            [0, 0, 1],
            [0, 1, 0],
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 1, 1],
        ],
        dtype=np.float64,
    )
    s0 = np.ascontiguousarray(states[:, 0:1])
    s1 = np.ascontiguousarray(states[:, 1:2])
    s2 = np.ascontiguousarray(states[:, 2:3])
    target = np.ascontiguousarray(
        np.bitwise_xor(s0.astype(np.int64), s1.astype(np.int64)),
        dtype=np.float64,
    )

    calls = [
        lambda: migration().compute_discrete_pid2(s0, s1, target, num_bins=2),
        lambda: migration().compute_discrete_pid3(s0, s1, s2, target, num_bins=2),
    ]
    for call in calls:
        with pytest.warns(
            DeprecationWarning,
            match="evaluated sample, returns Williams-Beer I_min rather than shared exclusions",
        ):
            result = call()
        assert result
        assert all(type(key) is str for key in result)
        assert all(type(value) is float for value in result.values())


def test_flat_sxpid_adapters_warn_and_remain_str_to_float_dicts():
    states = np.array(
        [
            [0, 0, 0],
            [0, 0, 1],
            [0, 1, 0],
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 1, 1],
        ],
        dtype=np.int64,
    )
    s0 = np.ascontiguousarray(states[:, 0:1])
    s1 = np.ascontiguousarray(states[:, 1:2])
    s2 = np.ascontiguousarray(states[:, 2:3])
    target = np.ascontiguousarray(np.bitwise_xor(np.bitwise_xor(s0, s1), s2))
    f0 = np.ascontiguousarray(s0, dtype=np.float64)
    f1 = np.ascontiguousarray(s1, dtype=np.float64)
    f2 = np.ascontiguousarray(s2, dtype=np.float64)
    ftarget = np.ascontiguousarray(target, dtype=np.float64)

    module = migration()
    calls = [
        (lambda: module.compute_discrete_sxpid2(s0, s1, target), "omits typed atom interpretation"),
        (
            lambda: module.compute_quantized_sxpid2(f0, f1, ftarget, num_bins=2),
            "num_bins-only quantization-provenance component plus input/PMF and typed-atom provenance",
        ),
        (lambda: module.compute_discrete_sxpid3(s0, s1, s2, target), "omits typed atom interpretation"),
        (
            lambda: module.compute_quantized_sxpid3(f0, f1, f2, ftarget, num_bins=2),
            "num_bins-only quantization-provenance component plus input/PMF and typed-atom provenance",
        ),
        (lambda: module.compute_discrete_sxpid_n([s0, s1, s2], target), "omits typed atom interpretation"),
        (
            lambda: module.compute_quantized_sxpid_n(
                [f0, f1, f2],
                ftarget,
                num_bins=2,
            ),
            "num_bins-only quantization-provenance component plus input/PMF and typed-atom provenance",
        ),
    ]

    for call, warning_pattern in calls:
        with pytest.warns(DeprecationWarning, match=warning_pattern):
            result = call()
        assert result
        assert all(type(key) is str for key in result)
        assert all(type(value) is float for value in result.values())


def test_three_source_imin_and_mgw_flat_key_sets_do_not_identify_method():
    states = np.array(
        [
            [0, 0, 0],
            [0, 0, 1],
            [0, 1, 0],
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 1, 1],
        ],
        dtype=np.float64,
    )
    sources = [np.ascontiguousarray(states[:, index : index + 1]) for index in range(3)]
    target = np.ascontiguousarray(
        np.bitwise_xor(
            sources[0].astype(np.int64),
            sources[1].astype(np.int64),
        ),
        dtype=np.float64,
    )
    module = migration()

    with pytest.warns(DeprecationWarning, match="Williams-Beer I_min"):
        imin = module.compute_discrete_pid3(*sources, target, num_bins=2)
    with pytest.warns(DeprecationWarning, match="categorical MGW output"):
        mgw = module.compute_quantized_sxpid3(*sources, target, num_bins=2)

    assert set(imin) == set(mgw)
    assert len(imin) == 18


def test_quantized_sxpid_python_paths_share_exact_rust_boundary_semantics():
    boundary = np.float64(0.3)
    successor = np.nextafter(boundary, np.float64(1.0))
    numeric = np.ascontiguousarray(
        np.array([0.0, boundary, successor, 1.0], dtype=np.float64).reshape(-1, 1)
    )
    exact_significand_labels = np.array([[0], [2], [3], [9]], dtype=np.int64)
    materialized_edge_labels = np.array([[0], [3], [3], [9]], dtype=np.int64)
    module = migration()

    with pytest.warns(DeprecationWarning, match="num_bins-only quantization-provenance"):
        quantized2 = module.compute_quantized_sxpid2(
            numeric, numeric, numeric, num_bins=10
        )
    with pytest.warns(DeprecationWarning, match="omits typed atom interpretation"):
        expected2 = module.compute_discrete_sxpid2(
            exact_significand_labels,
            exact_significand_labels,
            exact_significand_labels,
        )
        rejected_old2 = module.compute_discrete_sxpid2(
            materialized_edge_labels,
            materialized_edge_labels,
            materialized_edge_labels,
        )
    assert quantized2 == expected2
    assert quantized2 != rejected_old2

    with pytest.warns(DeprecationWarning, match="num_bins-only quantization-provenance"):
        quantized3 = module.compute_quantized_sxpid3(
            numeric,
            numeric,
            numeric,
            numeric,
            num_bins=10,
        )
    with pytest.warns(DeprecationWarning, match="omits typed atom interpretation"):
        expected3 = module.compute_discrete_sxpid3(
            exact_significand_labels,
            exact_significand_labels,
            exact_significand_labels,
            exact_significand_labels,
        )
    assert quantized3 == expected3

    with pytest.warns(DeprecationWarning, match="num_bins-only quantization-provenance"):
        quantized_n = module.compute_quantized_sxpid_n(
            [numeric, numeric, numeric],
            numeric,
            num_bins=10,
        )
    with pytest.warns(DeprecationWarning, match="omits typed atom interpretation"):
        expected_n = module.compute_discrete_sxpid_n(
            [
                exact_significand_labels,
                exact_significand_labels,
                exact_significand_labels,
            ],
            exact_significand_labels,
        )
    assert quantized_n == expected_n


def test_quantized_sxpid_n_preserves_asymmetric_source_order_and_mask_semantics():
    states = np.array(
        [
            [(row >> bit) & 1 for bit in range(4)]
            for row in range(16)
        ],
        dtype=np.int64,
    )
    categorical_sources = [
        np.ascontiguousarray(states[:, index : index + 1]) for index in range(4)
    ]
    target = np.ascontiguousarray(
        (
            (categorical_sources[0] & (1 - categorical_sources[1]))
            | (categorical_sources[2] & categorical_sources[3])
        ),
        dtype=np.int64,
    )
    numeric_sources = [
        np.ascontiguousarray(source.astype(np.float64) * scale + offset)
        for source, scale, offset in zip(
            categorical_sources,
            [2.0, 7.0, 11.0, 19.0],
            [-3.0, 5.0, 101.0, -41.0],
            strict=True,
        )
    ]
    numeric_target = np.ascontiguousarray(target, dtype=np.float64)
    module = migration()

    with pytest.warns(DeprecationWarning, match="num_bins-only quantization-provenance"):
        quantized = module.compute_quantized_sxpid_n(
            numeric_sources,
            numeric_target,
            num_bins=2,
        )
        swapped = module.compute_quantized_sxpid_n(
            [
                numeric_sources[3],
                numeric_sources[1],
                numeric_sources[2],
                numeric_sources[0],
            ],
            numeric_target,
            num_bins=2,
        )
    with pytest.warns(DeprecationWarning, match="omits typed atom interpretation"):
        expected = module.compute_discrete_sxpid_n(categorical_sources, target)

    assert quantized == expected
    assert quantized != swapped


def test_same_sample_pid_families_reject_identical_mi_coordinates_as_method_identity():
    source1 = np.array([[0.0], [0.0], [1.0], [1.0]], dtype=np.float64)
    source2 = np.array([[0.0], [1.0], [0.0], [1.0]], dtype=np.float64)
    target = np.array([[0.0], [1.0], [2.0], [3.0]], dtype=np.float64)
    module = migration()

    with pytest.warns(DeprecationWarning, match="Williams-Beer I_min"):
        imin = module.compute_discrete_pid2(source1, source2, target, num_bins=4)
    with pytest.warns(DeprecationWarning, match="categorical MGW output"):
        mgw = module.compute_quantized_sxpid2(source1, source2, target, num_bins=4)

    expected_mi = {
        "mi_s1_t": np.log(2.0),
        "mi_s2_t": np.log(2.0),
        "mi_s1s2_t": np.log(4.0),
    }
    for key, expected in expected_mi.items():
        assert imin[key] == pytest.approx(expected, abs=1e-12)
        assert mgw[key] == pytest.approx(expected, abs=1e-12)
        assert imin[key] == pytest.approx(mgw[key], abs=1e-12)
    assert imin["redundancy"] == pytest.approx(np.log(2.0), abs=1e-12)
    assert mgw["redundancy"] == pytest.approx(np.log(4.0 / 3.0), abs=1e-12)
    assert imin["redundancy"] != pytest.approx(mgw["redundancy"], abs=1e-12)


@pytest.mark.parametrize(
    ("function_name", "source_count", "row_count", "resource", "requested"),
    [
        ("compute_quantized_sxpid2", 2, 17_676, "operations_hint", 10_000_780_308),
        ("compute_quantized_sxpid3", 3, 5_555, "operations_hint", 10_001_821_940),
        ("compute_quantized_sxpid_n", 4, 1_119, "operations_hint", 10_008_977_187),
        pytest.param(
            "compute_discrete_pid2",
            2,
            813_441,
            "bytes",
            1_073_742_120,
            marks=pytest.mark.skipif(
                np.dtype(np.uintp).itemsize != 8,
                reason="64-bit Rust layout witness",
            ),
        ),
        pytest.param(
            "compute_discrete_pid3",
            3,
            110_924,
            "bytes",
            1_073_745_040,
            marks=pytest.mark.skipif(
                np.dtype(np.uintp).itemsize != 8,
                reason="64-bit Rust layout witness",
            ),
        ),
    ],
)
def test_same_sample_python_wrappers_preserve_aggregate_resource_rejections(
    function_name: str,
    source_count: int,
    row_count: int,
    resource: str,
    requested: int,
):
    values = np.zeros((row_count, 1), dtype=np.float64)
    function = getattr(migration(), function_name)
    if function_name.endswith("_n"):
        arguments = ([values] * source_count, values)
    else:
        arguments = (*([values] * source_count), values)

    with pytest.warns(DeprecationWarning):
        with pytest.raises(
            MemoryError,
            match=rf"resource limit exceeded for {resource} \(requested {requested}, limit ",
        ):
            function(*arguments, num_bins=2)


@pytest.mark.skipif(np.dtype(np.uintp).itemsize != 8, reason="64-bit usize witness")
@pytest.mark.parametrize(
    ("function_name", "warning_pattern"),
    [
        ("compute_discrete_pid2", "Williams-Beer I_min"),
        ("compute_quantized_sxpid2", "num_bins-only quantization-provenance"),
    ],
)
def test_python_legacy_preflight_is_stricter_than_rust_exact_significand_domain(
    function_name: str,
    warning_pattern: str,
):
    values = np.array([[0.0], [1.0]], dtype=np.float64)
    num_bins = (1 << 53) + 3
    # Three one-column inputs retain six labels plus three legacy `(num_bins + 1)` edge terms:
    # 6 * sizeof(usize) + 3 * (num_bins + 1) * sizeof(f64).
    expected_bytes = 216_172_782_113_783_952

    with pytest.warns(DeprecationWarning, match=warning_pattern):
        with pytest.raises(
            MemoryError,
            match=rf"resource limit exceeded for bytes \(requested {expected_bytes}, limit ",
        ):
            getattr(migration(), function_name)(
                values,
                values,
                values,
                num_bins=num_bins,
            )


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
    assert (
        concentration["pairwise_count"] == points.shape[0] * (points.shape[0] - 1) // 2
    )
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
