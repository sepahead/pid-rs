"""Smoke + sanity tests for the pid_core_rs Python extension.

Run after building/installing the wheel (e.g. `maturin develop` then `pytest`).
"""
import numpy as np
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
        "compute_discrete_pid3", "compute_invariants",
        "estimate_intrinsic_dimension", "estimate_gromov_delta",
        "distance_stats", "pls_transform", "standardize",
        "pca_transform", "hash_project",
    ]
    for fn in expected:
        assert hasattr(pid, fn), f"missing export: {fn}"


def test_compute_mi_positive():
    s1, _, t = _synthetic()
    mi = pid.compute_mi(s1, t)
    assert np.isfinite(mi) and mi > 0.0


def test_pid2_atoms_reconstruct_joint_mi():
    s1, s2, t = _synthetic()
    atoms = pid.compute_pid2(s1, s2, t, negative_handling="allow")
    for key in ("redundancy", "unique_s1", "unique_s2", "synergy"):
        assert key in atoms and np.isfinite(atoms[key])

    joint = pid.compute_mi(np.hstack([s1, s2]), t, negative_handling="allow")
    total = sum(atoms.values())
    assert abs(total - joint) < 1e-6, f"atoms sum {total} != I(S1,S2;T) {joint}"
