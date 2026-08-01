# Foundational SxPID exact witness checker

This directly invoked, standard-library Python tool reconstructs the finite three-source
shared-exclusions witnesses used by the foundational audit. It generates the complete 18-node
antichain lattice, evaluates the named exact-rational systems, and rejects retained semantic
mutations.

Run it from the repository root:

```text
python3 -I -S audit/tools/foundational_sxpid/check_lcr_relation_witness.py
```

The output is bounded evidence for the named finite systems. It is not an arbitrary-distribution
theorem, a proof of Rust refinement, a floating-point error bound, estimator calibration,
independent custody, or downstream scientific validation. The paper-defined shared-exclusions PID
remains the audited object; this tool does not introduce another PID definition.
