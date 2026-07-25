# Exact reconstruction route memo

## Route record

- **Claim:** SX-CERTIFIED-AVERAGED-PID2-001 revision 1
- **Route:** exact integer event semantics and fixed-lattice reconstruction
- **Date:** 2026-07-24
- **Primary implementation:** `audit/tools/certified-sxpid/src/extract.rs`
- **Independent implementation:** `audit/tools/certified-sxpid/scripts/verify_certificate.py`
- **Disposition:** executably complete for inputs accepted by these implementations; no deductive
  byte-level refinement theorem

## Reconstruction path

1. Parse one strict canonical table.
2. Sum exact integer target masses.
3. For each supported key and four nodes, compute exact source-union mass and target-restricted
   source-union mass.
4. Check exact positive-denominator nesting.
5. Build informative, misinformative, and net rational-log terms.
6. Check the exact local net-ratio identity.
7. Reconstruct the three nonredundancy net cumulatives as direct mutual information.
8. Apply the fixed Möbius matrix separately to informative, misinformative, and net cumulatives.
9. Check exact zeta reconstruction as arithmetic self-consistency after proving $ZM=I_4$.
10. Serialize exactly 24 canonical expressions.

The Python route independently implements each step and does not import the Rust extractor. Its
qualification harness adds a third event path: for each of the 494 small tables, it scans all rows
against the four event predicates and compares all twelve cumulative expressions with the
inclusion--exclusion reconstruction.

## Semantic checkpoints

| Checkpoint | Producer | Independent verifier |
|---|---|---|
| Strict schema and canonical rows | `schema.rs` | `validate_input` |
| Full vector equality | `matches_collection` | independent state tuples |
| Redundancy disjunction | masks `[1,2]` | inclusion-exclusion, plus direct row-scan qualification |
| Target restriction | exact row-target equality | reconstructed target keys, plus direct row-scan qualification |
| Positive event nesting | exact inequalities | reconstructed positive denominators |
| Local net identity | exact rationals | exact `Fraction` terms |
| Direct MI identities | three exact maps | three independently reconstructed maps |
| Möbius/zeta inverse | integer matrices | separate integer matrices; reconstruction is arithmetic self-consistency |
| Coordinate completeness | exactly 24 | exactly 24 exact identities |

## Bounded attack record

The independent route enumerated all 494 binary complete-state count tables with total count
$1\le N\le4$. It reconstructed:

$$
494\times24=11{,}856
$$

coordinates and

$$
494\times3=1{,}482
$$

direct-MI identities.

It also checked

$$
494\times12=5{,}928
$$

cumulative event expressions by direct row scans. This extra path kills a retained mutation that
replaces

```text
source_one_target + source_two_target - keyed_count
```

with `max(source_one_target, source_two_target)`. The internal nesting checks, the three direct-MI
identities, and the symmetric XOR pin do not kill that mutant.

This is exhaustive only for that finite domain. It tests the independent reconstruction without
proving it for all allowed row counts, vector widths, token alphabets, or 1024-digit counts.

## Falsifiers retained

- XOR redundancy union replaced by joint intersection;
- target-restricted union replaced by the maximum branch mass;
- target or source vector equality shortened to a prefix;
- duplicate/reordered coordinate identity;
- exact coefficient changed with all adjacent digests resealed;
- another input paired with the original certificate;
- transient 1640-term growth above the 1638 ceiling; and
- Python boolean substituted for integer one.

See [../failures/retained-negative-controls.md](../failures/retained-negative-controls.md).

## Remaining bridges

1. A proof assistant does not yet identify the byte schema with the exact finite event model.
2. No checked theorem connects the published equations to the fixed implementation constants.
3. Python tuple/string/integer behavior remains part of the independent route's trusted computing
   base.
4. The current source snapshot lacks independent custody.
