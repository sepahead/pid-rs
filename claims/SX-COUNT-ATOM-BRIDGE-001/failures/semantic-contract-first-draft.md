# Rejected first semantic-contract draft

Date: 10 August 2026

Disposition: **rejected and replaced; zero replay credit**.

## What failed

The first draft of `PidFiniteConvergenceSxPid2AtomSemanticContract.lean` did not compile under the
pinned Lean 4.32.0 toolchain. It left finite-sum and 12-coordinate product goals unsolved, emitted a
warning-as-error for an unused count argument, and failed to establish positive total count for the
chosen witness. It therefore supplied no semantic-contract evidence.

## Correction

The final contract uses an explicit asymmetric eight-key binary space with three positive anchors
of counts one, two, and one. It proves the complete count facts, all local informative,
misinformative, and net rational arguments, the cumulative products, the 12 atom products, and the
uniform scaled-log identity. The count-two anchor makes the empirical exponent observable rather
than allowing an unweighted product to pass accidentally.

The final contract is compiled separately from the main module and its exact bytes are bound by the
finite-convergence checker. Baseline-first isolated semantic variations change its order, signs,
count arguments, weights, exponents, products, or scale and must fail. This note records the failed
draft so later readers do not confuse intermediate source presence with completed kernel replay.
