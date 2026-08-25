# Separate SxPID3 informative-invariance Lean lane

This directory is an append-only formal lane. It is deliberately outside
audit/formal/lean, whose recursive source manifest, aggregate root, C7/v7
composite, and r12 replay receipt remain immutable.

Run from the repository root:

    (cd audit/formal/lean && lake exe cache get)
    python3 -I -S -B scripts/check-lean-sxpid3-informative-invariance.py
    python3 -O -I -S -B scripts/check-lean-sxpid3-informative-invariance.py
    python3 -I -S -B scripts/check-lean-sxpid3-informative-invariance-self-test.py
    python3 -O -I -S -B scripts/check-lean-sxpid3-informative-invariance-self-test.py
    python3 -I -S -B scripts/check-lean-sxpid3-informative-invariance-parity.py

Or run the separate Just entry point.  It fetches the pinned cache, enforces
byte-identical normal/optimized Lean checker and self-test output, replays the
bounded exact checker and hostile suite, and runs the stable no-default-feature
Rust public-API regression with warnings denied:

    just --justfile justfile.sxpid3-informative-invariance verify

The checker binds the exact standalone source, the exact local
SxEventBridge and Deterministic dependency bytes, the immutable aggregate
checker and root bytes, the Lake manifest/config/toolchain, all nine package
checkout revisions/origins/cleanliness, and the portable Lean 4.33.0 release
identity. It compiles only the dependency module and standalone source, then
audits all 16 theorem declarations against the permitted axiom basis.

The primary theorem status is arbitrary-finite algebra for a fixed finite
source product, supplied source-only event family, and any one supplied fixed
finite linear transform. Different finite target types are admissible when
complete source marginals agree. Exact path constancy is primary; the derivative
statement is only its corollary.

Prohibited inference: this lane does not establish that the supplied event
family is the MGW 18-node lattice, that supplied coefficients are its Mobius
inverse, or that Rust/count/binary64 code refines the Lean definitions. It gives
no misinformative/net invariance, no changing-source-alphabet or changing-lattice
result, and no continuous-estimator, sampling-to-population, calibration, causal,
authenticity, or priority result. Digest checks and hostile mutations are
custody/adequacy evidence, not independent mathematical truth. Normal and
optimized Python use the same Lean kernel and dependency closure. Nothing in
this lane is covered by, supersedes, or modifies C7, composite v7, toolchain
freeze r12, or replay receipt r12.
