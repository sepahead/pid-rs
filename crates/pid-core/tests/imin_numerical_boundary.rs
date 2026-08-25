//! Exact finite witnesses and bounded binary-table checks for the `I_min` binary64 boundary.
//!
//! The exhaustive result is deliberately scoped to nonempty binary `(S1,S2,T)` count tables with
//! total count at most eight. It is an implementation gate, not a population theorem or a global
//! elementary-function error bound. Exact target-specific ordering does not certify an internal
//! argmin field: the public result intentionally exposes no such field.
//!
//! For a supported target value `t`, the exact rational product constructed below is
//! `exp(n_t * I_spec(S; t))`. The common positive factor `n_t` makes product order identical to
//! specific-information order. Multiplying each selected target product gives
//! `exp(n * Red)`, while the mutual-information products give `exp(n * I)`; their quotient is
//! therefore `exp(n * Syn)`. These identities justify the exact order and sign checks without
//! claiming that the binary64 logarithm is exact.

use std::cmp::Ordering;
use std::collections::BTreeMap;

use pid_core::stable::imin::{
    imin_pid2, imin_pid2_quantized, imin_pid2_quantized_with_budget, imin_pid2_with_budget,
    imin_pid2_with_budget_and_cancellation, IminPid2Result,
};
use pid_core::stable::quantized::{EqualWidthQuantizer, QuantizerConfig};
use pid_core::{CancellationToken, DiscreteMatRef, MatRef, ResourceBudget};

#[cfg(feature = "experimental-pipelines")]
use pid_core::experimental::pipelines::exploratory_same_sample_quantized_imin_pid2;

const CE_003: [usize; 8] = [0, 0, 0, 1, 1, 2, 3, 0];
const MINIMAL_SOURCE_SWAP: [usize; 8] = [0, 0, 0, 1, 1, 0, 0, 2];
const GENUINE_SMALL_POSITIVE_SYNERGY: [usize; 8] = [0, 0, 0, 1, 1, 1, 2, 3];
const HISTORICAL_MINIMAL_ORIGINAL_SYNERGY_BITS: u64 = 0x3c70_0000_0000_0000;
const HISTORICAL_MINIMAL_SWAPPED_SYNERGY_BITS: u64 = 0;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct PositiveRational {
    numerator: u128,
    denominator: u128,
}

impl PositiveRational {
    fn new(numerator: u128, denominator: u128) -> Self {
        assert!(denominator > 0);
        let divisor = gcd_u128(numerator, denominator);
        Self {
            numerator: numerator / divisor,
            denominator: denominator / divisor,
        }
    }

    fn cmp_exact(self, other: Self) -> Ordering {
        let left = self
            .numerator
            .checked_mul(other.denominator)
            .expect("N <= 8 exact-product cross multiplication fits u128");
        let right = other
            .numerator
            .checked_mul(self.denominator)
            .expect("N <= 8 exact-product cross multiplication fits u128");
        left.cmp(&right)
    }

    fn checked_mul(self, other: Self) -> Self {
        let cross_left = gcd_u128(self.numerator, other.denominator);
        let cross_right = gcd_u128(other.numerator, self.denominator);
        Self::new(
            (self.numerator / cross_left)
                .checked_mul(other.numerator / cross_right)
                .expect("N <= 8 exact rational numerator fits u128"),
            (self.denominator / cross_right)
                .checked_mul(other.denominator / cross_left)
                .expect("N <= 8 exact rational denominator fits u128"),
        )
    }

    fn checked_div(self, other: Self) -> Self {
        assert!(other.numerator > 0);
        self.checked_mul(Self::new(other.denominator, other.numerator))
    }

    fn checked_pow(self, exponent: u32) -> Self {
        let mut result = Self::new(1, 1);
        for _ in 0..exponent {
            result = result.checked_mul(self);
        }
        result
    }
}

fn gcd_u128(mut left: u128, mut right: u128) -> u128 {
    while right != 0 {
        let remainder = left % right;
        left = right;
        right = remainder;
    }
    left
}

fn exact_specific_information_product(
    counts: &[usize; 8],
    source_axis: usize,
    target: usize,
) -> Option<PositiveRational> {
    let sample_count: usize = counts.iter().sum();
    let target_count: usize = counts
        .iter()
        .enumerate()
        .filter(|(index, _)| (*index & 1) == target)
        .map(|(_, count)| count)
        .sum();
    if target_count == 0 {
        return None;
    }

    let mut numerator = 1_u128;
    let mut denominator = 1_u128;
    for source in 0..2 {
        let source_count: usize = counts
            .iter()
            .enumerate()
            .filter(|(index, _)| source_value(*index, source_axis) == source)
            .map(|(_, count)| count)
            .sum();
        let joint_count: usize = counts
            .iter()
            .enumerate()
            .filter(|(index, _)| {
                source_value(*index, source_axis) == source && (*index & 1) == target
            })
            .map(|(_, count)| count)
            .sum();
        if joint_count == 0 {
            continue;
        }
        let exponent = u32::try_from(joint_count).expect("N <= 8 fits u32");
        numerator = numerator
            .checked_mul(((joint_count * sample_count) as u128).pow(exponent))
            .expect("N <= 8 exact numerator fits u128");
        denominator = denominator
            .checked_mul(((source_count * target_count) as u128).pow(exponent))
            .expect("N <= 8 exact denominator fits u128");
    }
    Some(PositiveRational::new(numerator, denominator))
}

fn exact_mi_product(counts: &[usize; 8], source_key: impl Fn(usize) -> usize) -> PositiveRational {
    let sample_count: usize = counts.iter().sum();
    let mut source_counts = BTreeMap::<usize, usize>::new();
    let mut target_counts = [0_usize; 2];
    let mut joint_counts = BTreeMap::<(usize, usize), usize>::new();
    for (index, &count) in counts.iter().enumerate() {
        let source = source_key(index);
        let target = index & 1;
        *source_counts.entry(source).or_default() += count;
        target_counts[target] += count;
        *joint_counts.entry((source, target)).or_default() += count;
    }

    let mut product = PositiveRational::new(1, 1);
    for ((source, target), joint_count) in joint_counts {
        if joint_count == 0 {
            continue;
        }
        let source_count = source_counts[&source];
        let target_count = target_counts[target];
        let ratio = PositiveRational::new(
            (joint_count * sample_count) as u128,
            (source_count * target_count) as u128,
        );
        product = product
            .checked_mul(ratio.checked_pow(u32::try_from(joint_count).expect("N <= 8 fits u32")));
    }
    product
}

fn exact_imin_redundancy_product(counts: &[usize; 8]) -> PositiveRational {
    let mut product = PositiveRational::new(1, 1);
    for target in 0..2 {
        let Some(source_one) = exact_specific_information_product(counts, 0, target) else {
            continue;
        };
        let source_two = exact_specific_information_product(counts, 1, target)
            .expect("a supported target occurs in both source-target tables");
        let minimum = if source_one.cmp_exact(source_two) == Ordering::Greater {
            source_two
        } else {
            source_one
        };
        product = product.checked_mul(minimum);
    }
    product
}

fn source_value(index: usize, source_axis: usize) -> usize {
    match source_axis {
        0 => (index >> 2) & 1,
        1 => (index >> 1) & 1,
        _ => panic!("binary table has exactly two source axes"),
    }
}

fn rows_from_counts(counts: &[usize; 8]) -> (Vec<usize>, Vec<usize>, Vec<usize>) {
    let sample_count: usize = counts.iter().sum();
    let mut source_one = Vec::with_capacity(sample_count);
    let mut source_two = Vec::with_capacity(sample_count);
    let mut target = Vec::with_capacity(sample_count);
    for (index, &count) in counts.iter().enumerate() {
        for _ in 0..count {
            source_one.push((index >> 2) & 1);
            source_two.push((index >> 1) & 1);
            target.push(index & 1);
        }
    }
    (source_one, source_two, target)
}

fn evaluate_counts(counts: &[usize; 8], swap_sources: bool) -> IminPid2Result {
    let (source_one, source_two, target) = rows_from_counts(counts);
    let sample_count = target.len();
    let source_one = DiscreteMatRef::new(&source_one, sample_count, 1).unwrap();
    let source_two = DiscreteMatRef::new(&source_two, sample_count, 1).unwrap();
    let target = DiscreteMatRef::new(&target, sample_count, 1).unwrap();
    if swap_sources {
        imin_pid2(source_two, source_one, target).unwrap()
    } else {
        imin_pid2(source_one, source_two, target).unwrap()
    }
}

fn scalar_bits(result: &IminPid2Result) -> [u64; 7] {
    [
        result.redundancy.to_bits(),
        result.unique_s1.to_bits(),
        result.unique_s2.to_bits(),
        result.synergy.to_bits(),
        result.mi_s1_t.to_bits(),
        result.mi_s2_t.to_bits(),
        result.mi_s1s2_t.to_bits(),
    ]
}

fn mapped_scalar_bits(original: &IminPid2Result, swapped: &IminPid2Result) -> ([u64; 7], [u64; 7]) {
    (
        scalar_bits(original),
        [
            swapped.redundancy.to_bits(),
            swapped.unique_s2.to_bits(),
            swapped.unique_s1.to_bits(),
            swapped.synergy.to_bits(),
            swapped.mi_s2_t.to_bits(),
            swapped.mi_s1_t.to_bits(),
            swapped.mi_s1s2_t.to_bits(),
        ],
    )
}

fn assert_same_numeric_result(expected: &IminPid2Result, actual: &IminPid2Result) {
    assert_eq!(scalar_bits(expected), scalar_bits(actual));
}

fn visit_weak_compositions(
    remaining: usize,
    index: usize,
    counts: &mut [usize; 8],
    visitor: &mut impl FnMut([usize; 8]),
) {
    if index == counts.len() - 1 {
        counts[index] = remaining;
        visitor(*counts);
        return;
    }
    for count in 0..=remaining {
        counts[index] = count;
        visit_weak_compositions(remaining - count, index + 1, counts, visitor);
    }
}

#[test]
fn ce_003_retains_the_exact_tie_and_public_no_argmin_boundary() {
    let source_one = exact_specific_information_product(&CE_003, 0, 1).unwrap();
    let source_two = exact_specific_information_product(&CE_003, 1, 1).unwrap();
    assert_eq!(source_one.cmp_exact(source_two), Ordering::Equal);
    assert_eq!(343_u128 * 972, 1372_u128 * 243);
    assert_eq!(343_u128 * 972, 333_396);

    let original = evaluate_counts(&CE_003, false);
    let swapped = evaluate_counts(&CE_003, true);
    let (original_bits, swapped_bits) = mapped_scalar_bits(&original, &swapped);
    assert_eq!(original_bits, swapped_bits);

    let serialized = serde_json::to_value(&original).unwrap();
    let object = serialized.as_object().unwrap();
    assert_eq!(
        object.len(),
        9,
        "a new public result field requires claim review"
    );
    for field in [
        "redundancy",
        "unique_s1",
        "unique_s2",
        "synergy",
        "mi_s1_t",
        "mi_s2_t",
        "mi_s1s2_t",
        "input",
        "empirical_pmf",
    ] {
        assert!(object.contains_key(field));
    }
    assert!(!object.contains_key("argmin"));
    assert!(!object.contains_key("tie"));
}

#[test]
fn minimal_source_swap_witness_uses_exact_represented_sum_without_clamping() {
    let (source_one, source_two, target) = rows_from_counts(&MINIMAL_SOURCE_SWAP);
    assert!(source_two
        .iter()
        .zip(&target)
        .all(|(source, target)| source == target));
    for target_value in 0..2 {
        let source_one_product =
            exact_specific_information_product(&MINIMAL_SOURCE_SWAP, 0, target_value).unwrap();
        let source_two_product =
            exact_specific_information_product(&MINIMAL_SOURCE_SWAP, 1, target_value).unwrap();
        assert_eq!(
            source_one_product.cmp_exact(source_two_product),
            Ordering::Less
        );
    }

    let original = evaluate_counts(&MINIMAL_SOURCE_SWAP, false);
    let swapped = evaluate_counts(&MINIMAL_SOURCE_SWAP, true);
    assert_eq!(original.mi_s1s2_t.to_bits(), original.mi_s2_t.to_bits());
    assert_eq!(original.redundancy.to_bits(), original.mi_s1_t.to_bits());
    assert_eq!(swapped.mi_s1s2_t.to_bits(), swapped.mi_s1_t.to_bits());
    assert_eq!(swapped.redundancy.to_bits(), swapped.mi_s2_t.to_bits());
    assert_eq!(original.synergy.to_bits(), 0);
    assert_eq!(swapped.synergy.to_bits(), 0);
    let (original_bits, swapped_bits) = mapped_scalar_bits(&original, &swapped);
    assert_eq!(original_bits, swapped_bits);

    // Executable negative control for the pre-repair left-associated residual. The two source
    // orders represented the same mathematical coordinate multiset but produced different bits.
    let historical_original =
        ((original.mi_s1s2_t - original.mi_s1_t) - original.mi_s2_t) + original.redundancy;
    let historical_swapped =
        ((swapped.mi_s1s2_t - swapped.mi_s1_t) - swapped.mi_s2_t) + swapped.redundancy;
    assert_eq!(
        historical_original.to_bits(),
        HISTORICAL_MINIMAL_ORIGINAL_SYNERGY_BITS
    );
    assert_eq!(
        historical_swapped.to_bits(),
        HISTORICAL_MINIMAL_SWAPPED_SYNERGY_BITS
    );
    assert_ne!(historical_original.to_bits(), historical_swapped.to_bits());

    let sample_count = target.len();
    let source_one_ref = DiscreteMatRef::new(&source_one, sample_count, 1).unwrap();
    let source_two_ref = DiscreteMatRef::new(&source_two, sample_count, 1).unwrap();
    let target_ref = DiscreteMatRef::new(&target, sample_count, 1).unwrap();
    let budgeted = imin_pid2_with_budget(
        source_one_ref,
        source_two_ref,
        target_ref,
        ResourceBudget::default(),
    )
    .unwrap();
    assert_same_numeric_result(&original, &budgeted);

    let cancellation = CancellationToken::new();
    let cancellable = imin_pid2_with_budget_and_cancellation(
        source_one_ref,
        source_two_ref,
        target_ref,
        ResourceBudget::default(),
        &cancellation,
    )
    .unwrap();
    assert_same_numeric_result(&original, &cancellable);

    let training = [0.0, 1.0];
    let quantizer = EqualWidthQuantizer::fit(
        MatRef::new(&training, training.len(), 1).unwrap(),
        2,
        QuantizerConfig::default(),
    )
    .unwrap();
    let source_one_f64: Vec<f64> = source_one.iter().map(|&value| value as f64).collect();
    let source_two_f64: Vec<f64> = source_two.iter().map(|&value| value as f64).collect();
    let target_f64: Vec<f64> = target.iter().map(|&value| value as f64).collect();
    let quantized_source_one = quantizer
        .transform_with_report(MatRef::new(&source_one_f64, sample_count, 1).unwrap())
        .unwrap();
    let quantized_source_two = quantizer
        .transform_with_report(MatRef::new(&source_two_f64, sample_count, 1).unwrap())
        .unwrap();
    let quantized_target = quantizer
        .transform_with_report(MatRef::new(&target_f64, sample_count, 1).unwrap())
        .unwrap();
    let quantized = imin_pid2_quantized(
        &quantized_source_one,
        &quantized_source_two,
        &quantized_target,
    )
    .unwrap();
    assert_same_numeric_result(&original, &quantized);
    let quantized_budgeted = imin_pid2_quantized_with_budget(
        &quantized_source_one,
        &quantized_source_two,
        &quantized_target,
        ResourceBudget::default(),
    )
    .unwrap();
    assert_same_numeric_result(&original, &quantized_budgeted);

    #[cfg(feature = "experimental-pipelines")]
    {
        let same_sample = exploratory_same_sample_quantized_imin_pid2(
            MatRef::new(&source_one_f64, sample_count, 1).unwrap(),
            MatRef::new(&source_two_f64, sample_count, 1).unwrap(),
            MatRef::new(&target_f64, sample_count, 1).unwrap(),
            2,
        )
        .unwrap();
        assert_same_numeric_result(&original, &same_sample.categorical_result);
    }
}

#[test]
fn genuine_small_positive_synergy_is_not_clamped_to_zero() {
    // Reconstruct exp(8 * Syn) from the empirical count law as
    // exp(8J) exp(8Red) / (exp(8I1) exp(8I2)). This binds the exact sign certificate to the
    // actual fixture rather than merely asserting its final numerator and denominator.
    const NUMERATOR: u64 = 823_543;
    const DENOMINATOR: u64 = 800_000;
    let joint = exact_mi_product(&GENUINE_SMALL_POSITIVE_SYNERGY, |index| index >> 1);
    let source_one = exact_mi_product(&GENUINE_SMALL_POSITIVE_SYNERGY, |index| (index >> 2) & 1);
    let source_two = exact_mi_product(&GENUINE_SMALL_POSITIVE_SYNERGY, |index| (index >> 1) & 1);
    let redundancy = exact_imin_redundancy_product(&GENUINE_SMALL_POSITIVE_SYNERGY);
    let exact_synergy_product = joint
        .checked_mul(redundancy)
        .checked_div(source_one.checked_mul(source_two));
    assert_eq!(
        exact_synergy_product,
        PositiveRational::new(NUMERATOR as u128, DENOMINATOR as u128)
    );
    assert!(exact_synergy_product.numerator > exact_synergy_product.denominator);
    let binary64_analytic_reference = ((NUMERATOR as f64) / (DENOMINATOR as f64)).ln() / 8.0;
    assert!(binary64_analytic_reference > 0.0 && binary64_analytic_reference < 0.01);

    let result = evaluate_counts(&GENUINE_SMALL_POSITIVE_SYNERGY, false);
    assert!(
        result.synergy > 0.0,
        "a genuine positive atom must not be silently clamped"
    );
    assert!(
        (result.synergy - binary64_analytic_reference).abs() <= 32.0 * f64::EPSILON,
        "result={} binary64-analytic-reference={binary64_analytic_reference}",
        result.synergy
    );
}

#[test]
fn bounded_binary_tables_freeze_exact_tie_events_and_source_swap_equivariance() {
    let mut table_count = 0_usize;
    let mut tie_events = 0_usize;
    let mut tie_events_by_total = [0_usize; 9];
    let mut tie_events_by_target = [0_usize; 2];
    let mut source_swap_mismatches = 0_usize;
    let mut first_source_swap_mismatch = None;

    for (total, tie_events_for_total) in tie_events_by_total.iter_mut().enumerate().skip(1) {
        let mut counts = [0_usize; 8];
        visit_weak_compositions(total, 0, &mut counts, &mut |counts| {
            table_count += 1;
            for (target, tie_events_for_target) in tie_events_by_target.iter_mut().enumerate() {
                let Some(source_one) = exact_specific_information_product(&counts, 0, target)
                else {
                    continue;
                };
                let source_two = exact_specific_information_product(&counts, 1, target)
                    .expect("every supported target occurs in every source-target table");
                let exact_order = source_one.cmp_exact(source_two);

                if exact_order == Ordering::Equal {
                    tie_events += 1;
                    *tie_events_for_total += 1;
                    *tie_events_for_target += 1;
                }
            }

            let original = evaluate_counts(&counts, false);
            let swapped = evaluate_counts(&counts, true);
            let (original_bits, swapped_bits) = mapped_scalar_bits(&original, &swapped);
            if original_bits != swapped_bits {
                source_swap_mismatches += 1;
                first_source_swap_mismatch.get_or_insert(counts);
            }
        });
    }

    assert_eq!(table_count, 12_869);
    assert_eq!(tie_events, 5_070);
    for (total, expected) in [8, 36, 104, 230, 464, 800, 1_344, 2_084]
        .into_iter()
        .enumerate()
    {
        assert_eq!(tie_events_by_total[total + 1], expected);
    }
    for (target, expected) in [2_535, 2_535].into_iter().enumerate() {
        assert_eq!(tie_events_by_target[target], expected);
    }
    assert_eq!(
        source_swap_mismatches, 0,
        "first source-swap mismatch: {first_source_swap_mismatch:?}"
    );
}
