"""Smoke + sanity tests for the pid_core_rs Python extension.

Run after building/installing the wheel (e.g. `maturin develop` then `pytest`).
"""
import sys

import numpy as np
import pytest

import pid_core_rs as pid

AC = "assume_absolutely_continuous"
PID2_PROVENANCE = {
    "source1_preprocessing_description": "source 1 standardized on training rows",
    "source2_preprocessing_description": "source 2 standardized on training rows",
    "target_preprocessing_description": "target left in measured units",
    "observation_model_description": "ideal continuous observation model; no post-hoc jitter",
}
PID3_PROVENANCE = {
    **PID2_PROVENANCE,
    "source3_preprocessing_description": "source 3 standardized on training rows",
}


def _synthetic(n=400, seed=0):
    rng = np.random.default_rng(seed)
    s1 = rng.standard_normal((n, 1))
    s2 = rng.standard_normal((n, 1))
    t = s1 + s2 + 0.2 * rng.standard_normal((n, 1))  # depends on both sources
    return s1, s2, t


def test_module_exports():
    expected = [
        "compute_mi", "compute_mi_report", "compute_redundancy", "compute_co_information",
        "compute_pid2", "compute_pid2_report", "compute_pid3_partial", "compute_pid3", "compute_discrete_pid2",
        "compute_discrete_pid3", "compute_discrete_sxpid2",
        "compute_discrete_sxpid3", "compute_discrete_sxpid_n", "compute_invariants",
        "compute_quantized_sxpid2", "compute_quantized_sxpid3",
        "compute_quantized_sxpid_n",
        "continuous_input_diagnostics",
        "estimate_intrinsic_dimension", "estimate_gromov_delta",
        "sampled_four_point_delta_summary",
        "distance_stats", "pls_transform", "standardize",
        "pca_transform", "hash_project", "PlsProjector",
    ]
    for fn in expected:
        assert hasattr(pid, fn), f"missing export: {fn}"


def _gate2(rows, reps=8, dtype=np.int64):
    s1, s2, t = [], [], []
    for _ in range(reps):
        for a, b, c in rows:
            s1.append([a]); s2.append([b]); t.append([c])
    return (np.array(s1, dtype=dtype), np.array(s2, dtype=dtype), np.array(t, dtype=dtype))


def test_discrete_sxpid2_and_matches_idtxl():
    # AND gate: IDTxl averaged shared(AND) = 0.12255624891826572 bits → nats.
    s1, s2, t = _gate2([(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)])
    out = pid.compute_discrete_sxpid2(s1, s2, t)
    want = 0.12255624891826572 * np.log(2.0)
    assert abs(out["redundancy"] - want) < 1e-9, out["redundancy"]
    # Reconstruction: atoms sum to I(S1,S2;T).
    total = out["redundancy"] + out["unique_s1"] + out["unique_s2"] + out["synergy"]
    assert abs(total - out["mi_s1s2_t"]) < 1e-9
    # Informative/misinformative split is reported and consistent.
    assert abs(out["redundancy"]
               - (out["redundancy_informative"] - out["redundancy_misinformative"])) < 1e-12


def test_discrete_sxpid_n_four_sources():
    # 4-way giant bit: all info in the all-singletons redundancy; reconstruction = ln 2.
    s0, s1, s2, s3, t = [], [], [], [], []
    for _ in range(4):
        for b in (0, 1):
            s0.append([b]); s1.append([b]); s2.append([b]); s3.append([b]); t.append([b])
    arr = lambda v: np.array(v, dtype=np.int64)
    out = pid.compute_discrete_sxpid_n([arr(s0), arr(s1), arr(s2), arr(s3)], arr(t))
    assert len(out) == 166, f"4-source lattice should have 166 atoms; got {len(out)}"
    total = sum(out.values())
    assert abs(total - np.log(2.0)) < 1e-9, total
    # The all-singletons key is "[1, 2, 4, 8]".
    assert abs(out["[1, 2, 4, 8]"] - np.log(2.0)) < 1e-9


def test_sxpid_attributes_less_redundancy_than_imin_on_copy():
    # Two-bit COPY of independent sources: I_min over-attributes (1 bit), i^sx less (log 4/3).
    rows = [(0, 0, 0), (0, 1, 1), (1, 0, 2), (1, 1, 3)]
    s1, s2, t = _gate2(rows)
    imin = pid.compute_discrete_pid2(
        s1.astype(np.float64), s2.astype(np.float64), t.astype(np.float64), num_bins=4
    )
    sx = pid.compute_discrete_sxpid2(s1, s2, t)
    assert abs(imin["redundancy"] - np.log(2.0)) < 1e-9
    assert abs(sx["redundancy"] - np.log(4.0 / 3.0)) < 1e-9
    assert sx["redundancy"] < imin["redundancy"] - 1e-3


def test_compute_mi_positive():
    s1, _, t = _synthetic()
    mi = pid.compute_mi(s1, t, support_contract=AC)
    assert np.isfinite(mi) and mi > 0.0


def test_compute_mi_default_negative_handling_is_unclamped_allow():
    s1, _, t = _synthetic(seed=91)
    default = pid.compute_mi(s1, t, support_contract=AC)
    explicit_allow = pid.compute_mi(
        s1, t, negative_handling="allow", support_contract=AC
    )
    assert default == explicit_allow


def test_compute_mi_report_preserves_euclidean_provenance_and_diagnostics():
    x, _, y = _synthetic(n=160, seed=96)
    provenance = {
        "preprocessing_description": "training-fold z-score parameters applied without refitting",
        "observation_model_description": "i.i.d. draws with additive continuous sensor noise",
    }
    with pytest.raises(ValueError, match="support contract is unspecified"):
        pid.compute_mi_report(x, y, **provenance)

    report = pid.compute_mi_report(
        x,
        y,
        k=4,
        support_contract=AC,
        **provenance,
    )
    scalar = pid.compute_mi(x, y, k=4, support_contract=AC)
    assert report["estimate_nats"] == scalar
    assert report["config"] == {
        "n_samples": 160,
        "k": 4,
        "metric": "chebyshev",
        "negative_handling": "allow",
        "support_contract": AC,
    }
    assert report["method"] == {
        "status": "restricted_domain",
        "geometry_model": "ambient_chebyshev",
        "curvature": None,
        "x_hyperbolic_dimension": None,
        "y_hyperbolic_dimension": None,
    }
    assert report["provenance"] == {
        **provenance,
        "embedding_training_provenance": None,
    }
    assert report["warnings"] == [
        {
            "code": "sample_diagnostics_cannot_prove_support",
            "message": "sample diagnostics can identify observations incompatible with ideal estimator conditions, but cannot determine the cause or prove population continuity, a common reference measure, or finite mutual information",
        }
    ]
    assert report["diagnostics"]["x"]["n_samples"] == 160
    assert report["diagnostics"]["x"]["ambient_dimension"] == 1
    assert report["diagnostics"]["x"]["unique_rows"] == 160
    assert report["diagnostics"]["y"]["ambient_dimension"] == 1
    joint_shells = report["diagnostics"]["joint_shells"]
    assert joint_shells["query_count"] == 160
    assert joint_shells["zero_radius_queries"] == 0
    assert joint_shells["ambiguous_positive_shell_queries"] == 0
    assert set(joint_shells["kth_radius"]) == {
        "min", "p10", "median", "p90", "p99", "max"
    }
    assert 0.0 < joint_shells["kth_radius"]["min"]
    assert joint_shells["kth_radius"]["max"] >= joint_shells["kth_radius"]["min"]


def test_continuous_entry_points_fail_closed_without_support_contract():
    s1, s2, t = _synthetic(n=80, seed=92)
    s3 = np.random.default_rng(93).standard_normal((80, 1))
    calls = [
        lambda: pid.compute_mi(s1, t),
        lambda: pid.compute_redundancy(s1, s2, t),
        lambda: pid.compute_co_information(s1, s2, t),
        lambda: pid.compute_pid2(s1, s2, t),
        lambda: pid.compute_invariants(s1, s2, t),
        lambda: pid.compute_pid3_partial(s1, s2, s3, t, **PID3_PROVENANCE),
        lambda: pid.compute_pid3(
            s1,
            s2,
            s3,
            t,
            experimental_allow_mixed_dimension_lattice=True,
            **PID3_PROVENANCE,
        ),
    ]
    for call in calls:
        with pytest.raises(ValueError, match="support contract is unspecified"):
            call()


def test_support_contract_and_diagnostics_catch_mixed_support_hidden_by_joint_rows():
    # Bernoulli X plus a continuously perturbed Y: every joint row and every positive k=3
    # joint shell is unique, but X has an atomic marginal. Joint-shell uniqueness is therefore
    # not a certificate of absolute continuity.
    x = np.ascontiguousarray(
        np.array([[0.0], [0.0], [0.0], [0.0], [1.0], [1.0], [1.0], [1.0]])
    )
    y = np.ascontiguousarray(
        np.array([[0.01], [0.08], [0.19], [0.41], [1.03], [1.11], [1.29], [1.52]])
    )

    x_diagnostics = pid.continuous_input_diagnostics(x, k=3)
    joint_diagnostics = pid.continuous_input_diagnostics(
        np.ascontiguousarray(np.hstack([x, y])), k=3
    )
    assert x_diagnostics["n_samples"] == 8
    assert x_diagnostics["ambient_dimension"] == 1
    assert x_diagnostics["unique_rows"] == 2
    assert x_diagnostics["tied_row_groups"] == 2
    assert x_diagnostics["repeated_rows"] == 6
    assert x_diagnostics["max_row_multiplicity"] == 4
    assert x_diagnostics["coordinates"] == [
        {
            "coordinate": 0,
            "unique_values": 2,
            "tied_groups": 2,
            "repeated_observations": 6,
            "max_multiplicity": 4,
        }
    ]
    assert x_diagnostics["marginal_shells"]["query_count"] == 8
    assert x_diagnostics["marginal_shells"]["zero_radius_queries"] == 8
    assert set(x_diagnostics["marginal_shells"]["kth_radius"]) == {
        "min", "p10", "median", "p90", "p99", "max"
    }
    assert joint_diagnostics["unique_rows"] == 8
    assert joint_diagnostics["max_row_multiplicity"] == 1
    assert joint_diagnostics["marginal_shells"]["zero_radius_queries"] == 0
    assert joint_diagnostics["marginal_shells"]["ambiguous_positive_shell_queries"] == 0

    with pytest.raises(ValueError, match="support contract is unspecified"):
        pid.compute_mi(x, y)
    with pytest.raises(ValueError, match="unsupported"):
        pid.compute_mi(x, y, support_contract="atomic_or_mixed")
    with pytest.raises(ValueError, match="observed exact ties"):
        pid.compute_mi(x, y, support_contract=AC)

    rng = np.random.default_rng(94)
    smooth_x = np.ascontiguousarray(rng.standard_normal((120, 1)))
    smooth_y = np.ascontiguousarray(rng.standard_normal((120, 1)))
    assert np.isfinite(pid.compute_mi(smooth_x, smooth_y, support_contract=AC))
    with pytest.raises(ValueError, match="Unknown support_contract"):
        pid.compute_mi(smooth_x, smooth_y, support_contract="not_a_contract")


def test_smooth_manifold_contract_is_restricted_to_experimental_hyperbolic_mi():
    rng = np.random.default_rng(95)
    u = rng.normal(0.0, 0.4, 80)
    v = 0.6 * u + rng.normal(0.0, 0.2, 80)
    x = np.ascontiguousarray(np.column_stack([np.cosh(u), np.sinh(u)]))
    y = np.ascontiguousarray(np.column_stack([np.cosh(v), np.sinh(v)]))

    with pytest.raises(ValueError, match="only through compute_mi_report"):
        pid.compute_mi(
            x,
            y,
            metric="hyperbolic",
            support_contract="assume_smooth_manifold",
        )
    with pytest.raises(ValueError, match="unsupported"):
        pid.compute_mi(x, y, support_contract="assume_smooth_manifold")

    report_arguments = {
        "metric": "hyperbolic",
        "support_contract": "assume_smooth_manifold",
        "preprocessing_description": "projected to the upper unit hyperboloid",
        "observation_model_description": "smooth manifold-valued observations",
    }
    with pytest.raises(ValueError, match="require embedding_training_provenance"):
        pid.compute_mi_report(x, y, **report_arguments)

    training_provenance = (
        "encoder checkpoint sha256:0123456789abcdef; frozen before evaluation"
    )
    report = pid.compute_mi_report(
        x,
        y,
        embedding_training_provenance=training_provenance,
        **report_arguments,
    )
    assert report["config"]["metric"] == "hyperbolic_lorentz"
    assert report["config"]["support_contract"] == "assume_smooth_manifold"
    assert report["method"] == {
        "status": "experimental",
        "geometry_model": "lorentz_hyperboloid",
        "curvature": -1.0,
        "x_hyperbolic_dimension": 1,
        "y_hyperbolic_dimension": 1,
    }
    assert report["provenance"]["embedding_training_provenance"] == training_provenance
    replayed = pid.compute_mi_report(
        x,
        y,
        metric=report["config"]["metric"],
        support_contract=report["config"]["support_contract"],
        preprocessing_description=report["provenance"]["preprocessing_description"],
        observation_model_description=report["provenance"]["observation_model_description"],
        embedding_training_provenance=training_provenance,
    )
    assert replayed["estimate_nats"] == report["estimate_nats"]
    hyperbolic_warning = next(
        warning
        for warning in report["warnings"]
        if warning["code"] == "hyperbolic_consistency_not_established"
    )
    assert hyperbolic_warning["message"] == (
        "hyperbolic/manifold KSG is experimental and this implementation lacks a statistical consistency theorem"
    )


def test_pid2_atoms_reconstruct_joint_mi():
    s1, s2, t = _synthetic()
    # compute_pid2 has no negative_handling parameter: the core always computes the MI terms
    # unclamped (Allow) so the atoms sum exactly to the joint MI below.
    atoms = pid.compute_pid2(s1, s2, t, support_contract=AC)
    for key in ("redundancy", "unique_s1", "unique_s2", "synergy"):
        assert key in atoms and np.isfinite(atoms[key])

    joint = pid.compute_mi(
        np.hstack([s1, s2]),
        t,
        negative_handling="allow",
        support_contract=AC,
    )
    total = sum(atoms.values())
    assert abs(total - joint) < 1e-6, f"atoms sum {total} != I(S1,S2;T) {joint}"


def test_pid2_report_preserves_restricted_status_and_per_variable_provenance():
    s1, s2, t = _synthetic(n=180, seed=301)
    report = pid.compute_pid2_report(
        s1,
        s2,
        t,
        support_contract=AC,
        **PID2_PROVENANCE,
    )

    assert set(report) == {
        "atoms", "estimate_terms", "config", "method", "provenance", "warnings"
    }
    assert report["config"]["n_samples"] == 180
    assert report["config"]["source_ambient_dimensions"] == [1, 1]
    assert report["config"]["target_ambient_dimension"] == 1
    assert report["config"]["effective_negative_handling"] == "allow"
    assert report["config"]["isx_method"] == "ehrlich_ksg"
    assert report["method"]["status"] == "experimental_restricted_domain"
    assert report["provenance"] == PID2_PROVENANCE
    assert len(report["warnings"]) == 5
    assert {
        warning["code"] for warning in report["warnings"]
    } >= {
        "general_consistency_not_established",
        "relative_source_scaling_defines_estimand",
    }
    assert all(np.isfinite(value) for value in report["atoms"].values())
    assert all(np.isfinite(value) for value in report["estimate_terms"].values())


def test_fortran_order_array_is_rejected_not_silently_transposed():
    # A non-square Fortran-ordered (non-C-contiguous) array would be read column-major by the
    # row-major core and silently transposed. It must raise instead, and wrapping it in
    # np.ascontiguousarray must succeed and give the SAME result as the C-ordered original.
    rng = np.random.default_rng(7)
    x_c = rng.standard_normal((300, 3))                  # C-contiguous
    t = np.ascontiguousarray(x_c[:, :1] + 0.1 * rng.standard_normal((300, 1)))
    x_f = np.asfortranarray(x_c)                          # same values, F-contiguous
    assert not x_f.flags["C_CONTIGUOUS"]

    with pytest.raises(ValueError):
        pid.compute_mi(x_f, t)

    with pytest.raises(ValueError, match="C-contiguous"):
        pid.compute_mi_report(
            x_f,
            t,
            metric="not_a_metric",
            preprocessing_description=" ",
            observation_model_description=" ",
        )
    with pytest.raises(ValueError, match="C-contiguous"):
        pid.compute_pid2_report(
            x_f,
            x_c,
            t,
            metric="not_a_metric",
            **PID2_PROVENANCE,
        )
    with pytest.raises(ValueError, match="C-contiguous"):
        pid.compute_pid3_partial(
            x_f,
            x_c,
            x_c,
            t,
            metric="not_a_metric",
            **PID3_PROVENANCE,
        )

    mi_c = pid.compute_mi(x_c, t, support_contract=AC)
    mi_fixed = pid.compute_mi(np.ascontiguousarray(x_f), t, support_contract=AC)
    assert abs(mi_c - mi_fixed) < 1e-12


def test_invalid_config_raises_value_error():
    # Caller-supplied bad input maps to ValueError (not RuntimeError): k >= n is InvalidK.
    s1, _, t = _synthetic(n=12)
    with pytest.raises(ValueError):
        pid.compute_mi(s1, t, k=50, support_contract=AC)

    y_short = np.ascontiguousarray(t[:-1])
    with pytest.raises(ValueError, match="row count mismatch"):
        pid.compute_mi(
            s1,
            y_short,
            metric="hyperbolic_lorentz",
            support_contract="assume_smooth_manifold",
        )


def test_exact_categorical_relabeling_and_explicit_quantization_contracts():
    a = np.array([[0], [1], [100], [0], [1], [100]], dtype=np.int64)
    b = np.array([[100], [0], [50], [100], [0], [50]], dtype=np.int64)
    ta = np.array([[10], [20], [30], [10], [20], [30]], dtype=np.int64)
    tb = np.array([[2], [900], [41], [2], [900], [41]], dtype=np.int64)
    noise = np.full((6, 1), -7, dtype=np.int64)
    exact_a = pid.compute_discrete_sxpid2(a, noise, ta)
    exact_b = pid.compute_discrete_sxpid2(b, noise, tb)
    assert abs(exact_a["mi_s1s2_t"] - np.log(3.0)) < 1e-12
    for key in exact_a:
        assert abs(exact_a[key] - exact_b[key]) < 1e-12
    assert list(exact_a) == sorted(exact_a), "dict order must be deterministic"

    qa = a.astype(np.float64)
    qb = np.array([[0], [50], [100], [0], [50], [100]], dtype=np.float64)
    qnoise = np.zeros((6, 1), dtype=np.float64)
    quant_a = pid.compute_quantized_sxpid2(qa, qnoise, qa, num_bins=3)
    quant_b = pid.compute_quantized_sxpid2(qb, qnoise, qb, num_bins=3)
    assert quant_b["mi_s1s2_t"] - quant_a["mi_s1s2_t"] > 0.4

    with pytest.raises((TypeError, ValueError)):
        pid.compute_discrete_sxpid2(qa, qnoise, qa)
    with pytest.raises(ValueError):
        pid.compute_quantized_sxpid2(qa, qnoise, qa, num_bins=1)


def test_three_source_discrete_surfaces_execute():
    s0, s1, s2, t = [], [], [], []
    for _ in range(3):
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    s0.append([a]); s1.append([b]); s2.append([c]); t.append([a ^ b ^ c])
    ints = [np.asarray(values, dtype=np.int64) for values in (s0, s1, s2, t)]
    floats = [values.astype(np.float64) for values in ints]

    sx3 = pid.compute_discrete_sxpid3(*ints)
    qsx3 = pid.compute_quantized_sxpid3(*floats, num_bins=2)
    qsxn = pid.compute_quantized_sxpid_n(floats[:3], floats[3], num_bins=2)
    imin3 = pid.compute_discrete_pid3(*floats, num_bins=2)
    assert len(sx3) == len(qsx3) == len(qsxn) == len(imin3) == 18
    assert abs(sum(sx3.values()) - np.log(2.0)) < 1e-9
    assert list(sx3) == sorted(sx3)


def test_continuous_estimators_and_diagnostics_execute():
    s1, s2, t = _synthetic(n=180, seed=11)
    s3 = np.random.default_rng(12).standard_normal((180, 1))
    red = pid.compute_redundancy(s1, s2, t, k=3, support_contract=AC)
    with pytest.raises(ValueError, match="source dimension mismatch"):
        pid.compute_redundancy(
            s1,
            np.ascontiguousarray(np.hstack([s2, s3])),
            t,
            k=3,
            support_contract=AC,
        )
    coinfo = pid.compute_co_information(s1, s2, t, k=3, support_contract=AC)
    invariants = pid.compute_invariants(s1, s2, t, k=3, support_contract=AC)
    with pytest.raises(ValueError, match="experimental_allow_mixed_dimension_lattice=true"):
        pid.compute_pid3(
            s1,
            s2,
            s3,
            t,
            k=3,
            support_contract=AC,
            **PID3_PROVENANCE,
        )
    partial_pid3 = pid.compute_pid3_partial(
        s1,
        s2,
        s3,
        t,
        k=3,
        support_contract=AC,
        **PID3_PROVENANCE,
    )
    pid3 = pid.compute_pid3(
        s1,
        s2,
        s3,
        t,
        k=3,
        experimental_allow_mixed_dimension_lattice=True,
        support_contract=AC,
        **PID3_PROVENANCE,
    )
    assert np.isfinite(red)
    assert np.isfinite(coinfo)
    assert partial_pid3["n_samples"] == 180
    assert partial_pid3["k"] == 3
    assert partial_pid3["metric"] == "chebyshev"
    assert partial_pid3["support_contract"] == AC
    assert partial_pid3["source_ambient_dimensions"] == [1, 1, 1]
    assert partial_pid3["target_ambient_dimension"] == 1
    assert partial_pid3["experimental"] is True
    assert partial_pid3["provenance"] == PID3_PROVENANCE
    assert partial_pid3["warnings"] == [
        "the support contract is caller-declared; sample checks can identify incompatible observations but cannot determine their cause or verify population support",
        "equal ambient branch dimensions do not establish equal intrinsic dimensions, compatible reference measures, or regular leading-order intersections",
        "relative source units and preprocessing are part of the shared-exclusions estimand and must be recorded alongside every reported result",
        "unavailable coordinates are not imputed; available atoms do not form a complete 18-atom decomposition",
    ]
    assert len(partial_pid3["redundancies"]) == 18
    assert sum(
        redundancy["value"] is not None
        for redundancy in partial_pid3["redundancies"].values()
    ) == 15
    assert partial_pid3["redundancies"]["[1, 6]"] == {
        "value": None,
        "branch_dimensions": [1, 2],
    }
    assert partial_pid3["redundancies"]["[2, 5]"] == {
        "value": None,
        "branch_dimensions": [1, 2],
    }
    assert partial_pid3["redundancies"]["[3, 4]"] == {
        "value": None,
        "branch_dimensions": [2, 1],
    }
    assert len(partial_pid3["atoms"]) == 18
    assert sum(atom["value"] is not None for atom in partial_pid3["atoms"].values()) == 8
    assert partial_pid3["atoms"]["[1]"]["unavailable_redundancies"] == ["[1, 6]"]
    assert partial_pid3["atoms"]["[3, 5, 6]"]["unavailable_redundancies"] == [
        "[1, 6]",
        "[2, 5]",
        "[3, 4]",
    ]
    assert np.isfinite(partial_pid3["atoms"]["[1, 2, 4]"]["value"])
    assert partial_pid3["atoms"]["[1, 2, 4]"]["unavailable_redundancies"] == []
    assert pid3["n_samples"] == 180
    assert pid3["k"] == 3
    assert pid3["metric"] == "chebyshev"
    assert pid3["support_contract"] == AC
    assert pid3["source_ambient_dimensions"] == [1, 1, 1]
    assert pid3["target_ambient_dimension"] == 1
    assert pid3["method_status"] == "experimental_mixed_dimension"
    assert pid3["experimental"] is True
    assert pid3["provenance"] == PID3_PROVENANCE
    assert len(pid3["warnings"]) == 3
    assert "mixed-dimensional" in pid3["warnings"][0]
    assert len(pid3["redundancies"]) == 18
    assert all(np.isfinite(value) for value in pid3["redundancies"].values())
    assert len(pid3["atoms"]) == 18
    assert all(np.isfinite(value) for value in pid3["atoms"].values())
    assert set(invariants) == {
        "co_information", "mi_s1_t", "mi_s1s2_t", "mi_s2_t", "r_bar", "v_bar"
    }
    assert abs(invariants["co_information"] - coinfo) < 1e-12

    x = np.ascontiguousarray(np.hstack([s1, s2, s3]))
    intrinsic = pid.estimate_intrinsic_dimension(x, k=8)
    delta_summary = pid.sampled_four_point_delta_summary(x, n_samples=100, seed=9)
    with pytest.warns(
        DeprecationWarning,
        match="estimate_gromov_delta is deprecated; use sampled_four_point_delta_summary",
    ):
        legacy_delta = pid.estimate_gromov_delta(x, n_samples=100, seed=9)
    stats = pid.distance_stats(x)
    assert np.isfinite(intrinsic) and intrinsic > 0.0
    assert delta_summary["sample_count"] == 100
    assert type(delta_summary["sample_count"]) is int
    assert delta_summary["diameter"] > 0.0
    assert delta_summary["mean"] == legacy_delta
    assert 0.0 <= delta_summary["median"] <= delta_summary["p90"]
    assert delta_summary["p90"] <= delta_summary["p99"] <= delta_summary["max"]
    assert delta_summary["monte_carlo_standard_error"] >= 0.0
    assert delta_summary["normalized_mean"] == pytest.approx(
        2.0 * delta_summary["mean"] / delta_summary["diameter"]
    )
    assert stats["pairwise_count"] == 180 * 179 / 2
    assert type(stats["pairwise_count"]) is int
    assert all(np.isfinite(value) for value in stats.values())


def test_preprocessing_exports_shapes_and_values():
    rng = np.random.default_rng(21)
    x = np.ascontiguousarray(rng.standard_normal((64, 4)))
    y = np.ascontiguousarray((x[:, :1] - 0.3 * x[:, 1:2]))
    calls = [
        pid.standardize(x),
        pid.pca_transform(x, out_dim=2),
        pid.pls_transform(x, y, out_dim=2),
        pid.hash_project(x, out_dim=3, seed=7),
    ]
    expected_cols = [4, 2, 2, 3]
    for out, ncols in zip(calls, expected_cols):
        assert out["nrows"] == 64
        assert out["ncols"] == ncols
        data = np.asarray(out["data"])
        assert data.shape == (64 * ncols,)
        assert np.all(np.isfinite(data))
        assert list(out) == ["data", "ncols", "nrows"]


def test_fitted_pls_projector_transforms_held_out_rows_without_refitting():
    rng = np.random.default_rng(29)
    x = np.ascontiguousarray(rng.standard_normal((80, 4)))
    y = np.ascontiguousarray(x[:, :1] - 0.3 * x[:, 1:2])
    x_train = np.ascontiguousarray(x[:60])
    y_train = np.ascontiguousarray(y[:60])
    x_test = np.ascontiguousarray(x[60:])

    projector = pid.PlsProjector.fit(x_train, y_train, out_dim=2)
    held_out = projector.transform(x_test)
    fitted_training = projector.transform(x_train)
    compatibility_training = pid.pls_transform(x_train, y_train, out_dim=2)

    assert (projector.in_dim, projector.out_dim, projector.target_dim) == (4, 2, 1)
    assert held_out["nrows"] == 20 and held_out["ncols"] == 2
    assert np.all(np.isfinite(np.asarray(held_out["data"])))
    assert np.array_equal(fitted_training["data"], compatibility_training["data"])
    assert "training-only" in pid.pls_transform.__doc__.lower()

    with pytest.raises(ValueError):
        projector.transform(np.ascontiguousarray(x_test[:, :3]))


def test_hash_project_rejects_unallocatable_output_instead_of_panicking():
    x = np.ones((1, 1), dtype=np.float64)
    with pytest.raises(ValueError, match="too large|overflow"):
        pid.hash_project(x, out_dim=sys.maxsize)


def test_fitted_pls_transform_keeps_representable_extreme_held_out_score():
    x_train = np.ascontiguousarray([[-3e-300], [-1e-300], [1e-300], [3e-300]])
    y_train = np.ascontiguousarray([[-3.0], [-1.0], [1.0], [3.0]])
    held_out = np.ascontiguousarray([[1e300]])

    projector = pid.PlsProjector.fit(x_train, y_train, out_dim=1)
    score = projector.transform(held_out)["data"][0]

    assert np.isfinite(score)
    assert abs(abs(score) / 1e300 - 1.0) < 1e-12
