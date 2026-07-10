"""Smoke + sanity tests for the pid_core_rs Python extension.

Run after building/installing the wheel (e.g. `maturin develop` then `pytest`).
"""
import sys

import numpy as np
import pytest

import pid_core_rs as pid


def _synthetic(n=400, seed=0):
    rng = np.random.default_rng(seed)
    s1 = rng.standard_normal((n, 1))
    s2 = rng.standard_normal((n, 1))
    t = s1 + s2 + 0.2 * rng.standard_normal((n, 1))  # depends on both sources
    return s1, s2, t


def test_module_exports():
    expected = [
        "compute_mi", "compute_redundancy", "compute_co_information",
        "compute_pid2", "compute_pid3", "compute_discrete_pid2",
        "compute_discrete_pid3", "compute_discrete_sxpid2",
        "compute_discrete_sxpid3", "compute_discrete_sxpid_n", "compute_invariants",
        "compute_quantized_sxpid2", "compute_quantized_sxpid3",
        "compute_quantized_sxpid_n",
        "estimate_intrinsic_dimension", "estimate_gromov_delta",
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
    mi = pid.compute_mi(s1, t)
    assert np.isfinite(mi) and mi > 0.0


def test_pid2_atoms_reconstruct_joint_mi():
    s1, s2, t = _synthetic()
    # compute_pid2 has no negative_handling parameter: the core always computes the MI terms
    # unclamped (Allow) so the atoms sum exactly to the joint MI below.
    atoms = pid.compute_pid2(s1, s2, t)
    for key in ("redundancy", "unique_s1", "unique_s2", "synergy"):
        assert key in atoms and np.isfinite(atoms[key])

    joint = pid.compute_mi(np.hstack([s1, s2]), t, negative_handling="allow")
    total = sum(atoms.values())
    assert abs(total - joint) < 1e-6, f"atoms sum {total} != I(S1,S2;T) {joint}"


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

    mi_c = pid.compute_mi(x_c, t)
    mi_fixed = pid.compute_mi(np.ascontiguousarray(x_f), t)
    assert abs(mi_c - mi_fixed) < 1e-12


def test_invalid_config_raises_value_error():
    # Caller-supplied bad input maps to ValueError (not RuntimeError): k >= n is InvalidK.
    s1, _, t = _synthetic(n=12)
    with pytest.raises(ValueError):
        pid.compute_mi(s1, t, k=50)


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
    red = pid.compute_redundancy(s1, s2, t, k=3)
    coinfo = pid.compute_co_information(s1, s2, t, k=3)
    invariants = pid.compute_invariants(s1, s2, t, k=3)
    pid3 = pid.compute_pid3(s1, s2, s3, t, k=3)
    assert np.isfinite(red)
    assert np.isfinite(coinfo)
    assert len(pid3) == 18 and all(np.isfinite(value) for value in pid3.values())
    assert set(invariants) == {
        "co_information", "mi_s1_t", "mi_s1s2_t", "mi_s2_t", "r_bar", "v_bar"
    }
    assert abs(invariants["co_information"] - coinfo) < 1e-12

    x = np.ascontiguousarray(np.hstack([s1, s2, s3]))
    intrinsic = pid.estimate_intrinsic_dimension(x, k=8)
    delta = pid.estimate_gromov_delta(x, n_samples=100, seed=9)
    stats = pid.distance_stats(x)
    assert np.isfinite(intrinsic) and intrinsic > 0.0
    assert np.isfinite(delta) and delta >= 0.0
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
