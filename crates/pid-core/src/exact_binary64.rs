//! Exact, order-independent reduction of already represented finite binary64 values.
//!
//! This private arithmetic module is deliberately isolated from estimator-specific arithmetic
//! and custody packets. It supplies a correctly rounded sum of its binary64 inputs; it does not
//! make upstream estimates exact or transfer semantics between PID measures.

// Every finite binary64 is an integer multiple of 2^-1074. The largest significand occupies
// 2,098 bits at that scale; summing at most usize::MAX terms needs at most usize::BITS more.
const FINITE_SUM_LIMBS: usize = (2_098 + usize::BITS as usize).div_ceil(64);
// One add can propagate through the full accumulator in each of the significand's two limb
// fragments. Finalization can scan once for sign comparison, once for subtraction, once for the
// highest bit, and once for sticky bits. These are conservative limb-visit envelopes for resource
// hints, not CPU-instruction counts.
pub(crate) const EXACT_BINARY64_ADD_LIMB_VISIT_BOUND: usize = 2 * FINITE_SUM_LIMBS;
pub(crate) const EXACT_BINARY64_TOTAL_LIMB_VISIT_BOUND: usize = 4 * FINITE_SUM_LIMBS;

/// Streaming exact reduction of already represented finite binary64 values.
///
/// [`Self::total`] rounds the exact real sum once to binary64, using round-to-nearest with ties to
/// even. The result is independent of insertion order. This is an internal arithmetic primitive,
/// not an exact-real estimator: every inserted value may already contain approximation error.
/// Exact cancellation, including a collection containing only signed zeros, is canonicalized to
/// positive zero.
#[derive(Clone)]
pub(crate) struct ExactBinary64Accumulator {
    positive: [u64; FINITE_SUM_LIMBS],
    negative: [u64; FINITE_SUM_LIMBS],
    terms: usize,
}

impl Default for ExactBinary64Accumulator {
    fn default() -> Self {
        Self {
            positive: [0; FINITE_SUM_LIMBS],
            negative: [0; FINITE_SUM_LIMBS],
            terms: 0,
        }
    }
}

impl ExactBinary64Accumulator {
    /// Add one finite binary64 value exactly.
    ///
    /// `false` reports a non-finite input, an attempted call beyond `usize::MAX`, or an internal
    /// capacity violation. A rejected call leaves the accumulator byte-for-byte unchanged. The
    /// limb capacity is constructed so that the internal-capacity branch is unreachable for an
    /// accumulator built exclusively through this method; retaining the transactional branch
    /// makes that defensive failure contract testable instead of relying on partial mutation.
    /// Production reductions are additionally bounded by Rust collection lengths.
    pub(crate) fn add(&mut self, term: f64) -> bool {
        if !term.is_finite() {
            return false;
        }
        let Some(terms) = self.terms.checked_add(1) else {
            return false;
        };
        let bits = term.to_bits();
        let exponent = ((bits >> 52) & 0x7ff) as usize;
        let fraction = bits & ((1_u64 << 52) - 1);
        let significand = if exponent == 0 {
            fraction
        } else {
            (1_u64 << 52) | fraction
        };
        if significand == 0 {
            self.terms = terms;
            return true;
        }
        let shift = exponent.saturating_sub(1);
        let accumulator = if bits >> 63 == 0 {
            &mut self.positive
        } else {
            &mut self.negative
        };
        if !add_shifted_significand(accumulator, significand, shift) {
            return false;
        }
        self.terms = terms;
        true
    }

    pub(crate) fn total(&self) -> f64 {
        match self.positive.iter().rev().cmp(self.negative.iter().rev()) {
            std::cmp::Ordering::Equal => 0.0,
            std::cmp::Ordering::Greater => {
                let magnitude = subtract_finite_sum_limbs(&self.positive, &self.negative);
                round_finite_sum(&magnitude, false)
            }
            std::cmp::Ordering::Less => {
                let magnitude = subtract_finite_sum_limbs(&self.negative, &self.positive);
                round_finite_sum(&magnitude, true)
            }
        }
    }
}

/// Correctly round the exact real sum of finite binary64 inputs, independently of input order.
///
/// Non-finite inputs return `NaN`. Callers with a typed error boundary must validate or reject
/// that result. Exact zero is canonicalized to positive zero.
pub(crate) fn exact_binary64_sum<const N: usize>(terms: [f64; N]) -> f64 {
    let mut accumulator = ExactBinary64Accumulator::default();
    for term in terms {
        if !accumulator.add(term) {
            return f64::NAN;
        }
    }
    accumulator.total()
}

fn add_shifted_significand(
    accumulator: &mut [u64; FINITE_SUM_LIMBS],
    significand: u64,
    shift: usize,
) -> bool {
    let limb = shift / 64;
    let offset = shift % 64;
    let low = significand << offset;
    if !add_finite_sum_limb(accumulator, limb, low) {
        subtract_finite_sum_limb_modulo(accumulator, limb, low);
        return false;
    }
    if offset == 0 {
        return true;
    }
    let high = significand >> (64 - offset);
    if add_finite_sum_limb(accumulator, limb + 1, high) {
        true
    } else {
        // `add_finite_sum_limb` has applied its fragment modulo the accumulator width before it
        // observes a carry beyond the last limb. Undo the high and low fragments in reverse order
        // so the public `false` result is transactional even under an invariant-breaking state.
        subtract_finite_sum_limb_modulo(accumulator, limb + 1, high);
        subtract_finite_sum_limb_modulo(accumulator, limb, low);
        false
    }
}

fn add_finite_sum_limb(
    accumulator: &mut [u64; FINITE_SUM_LIMBS],
    mut index: usize,
    value: u64,
) -> bool {
    if value == 0 {
        return true;
    }
    if index >= accumulator.len() {
        return false;
    }
    let (sum, mut carry) = accumulator[index].overflowing_add(value);
    accumulator[index] = sum;
    while carry {
        index += 1;
        if index >= accumulator.len() {
            return false;
        }
        let (sum, next_carry) = accumulator[index].overflowing_add(1);
        accumulator[index] = sum;
        carry = next_carry;
    }
    true
}

/// Subtract one shifted limb modulo the fixed accumulator width.
///
/// This is the exact inverse of the mutation performed by [`add_finite_sum_limb`], including when
/// that addition reports a carry beyond the final limb. It is used only to roll back a defensive
/// capacity failure; accepted reductions do not pay for a second traversal.
fn subtract_finite_sum_limb_modulo(
    accumulator: &mut [u64; FINITE_SUM_LIMBS],
    mut index: usize,
    value: u64,
) {
    if value == 0 || index >= accumulator.len() {
        return;
    }
    let (difference, mut borrow) = accumulator[index].overflowing_sub(value);
    accumulator[index] = difference;
    while borrow {
        index += 1;
        if index >= accumulator.len() {
            return;
        }
        let (difference, next_borrow) = accumulator[index].overflowing_sub(1);
        accumulator[index] = difference;
        borrow = next_borrow;
    }
}

fn subtract_finite_sum_limbs(
    larger: &[u64; FINITE_SUM_LIMBS],
    smaller: &[u64; FINITE_SUM_LIMBS],
) -> [u64; FINITE_SUM_LIMBS] {
    let mut difference = [0_u64; FINITE_SUM_LIMBS];
    let mut borrow = false;
    for index in 0..FINITE_SUM_LIMBS {
        let (without_value, value_borrow) = larger[index].overflowing_sub(smaller[index]);
        let (value, carry_borrow) = without_value.overflowing_sub(u64::from(borrow));
        difference[index] = value;
        borrow = value_borrow || carry_borrow;
    }
    debug_assert!(!borrow);
    difference
}

fn highest_finite_sum_bit(value: &[u64; FINITE_SUM_LIMBS]) -> Option<usize> {
    value
        .iter()
        .rposition(|&limb| limb != 0)
        .map(|index| index * 64 + (63 - value[index].leading_zeros() as usize))
}

fn finite_sum_bit(value: &[u64; FINITE_SUM_LIMBS], bit: usize) -> bool {
    value
        .get(bit / 64)
        .is_some_and(|limb| limb & (1_u64 << (bit % 64)) != 0)
}

fn any_finite_sum_bits_below(value: &[u64; FINITE_SUM_LIMBS], bit_exclusive: usize) -> bool {
    let full_limbs = bit_exclusive / 64;
    if value[..full_limbs.min(value.len())]
        .iter()
        .any(|&limb| limb != 0)
    {
        return true;
    }
    let remaining = bit_exclusive % 64;
    remaining != 0
        && full_limbs < value.len()
        && value[full_limbs] & ((1_u64 << remaining) - 1) != 0
}

fn low_finite_sum_u64_after_shift(value: &[u64; FINITE_SUM_LIMBS], shift: usize) -> u64 {
    let limb = shift / 64;
    let offset = shift % 64;
    let low = value.get(limb).copied().unwrap_or(0) >> offset;
    if offset == 0 {
        low
    } else {
        low | (value.get(limb + 1).copied().unwrap_or(0) << (64 - offset))
    }
}

/// Round an exact nonzero integer multiple of 2^-1074 to binary64, ties to even.
fn round_finite_sum(magnitude: &[u64; FINITE_SUM_LIMBS], negative: bool) -> f64 {
    let sign = if negative { 1_u64 << 63 } else { 0 };
    let Some(highest) = highest_finite_sum_bit(magnitude) else {
        return f64::from_bits(sign);
    };
    if highest < 52 {
        return f64::from_bits(sign | magnitude[0]);
    }

    let cutoff = highest - 52;
    let mut significand = low_finite_sum_u64_after_shift(magnitude, cutoff);
    if cutoff > 0 {
        let halfway = finite_sum_bit(magnitude, cutoff - 1);
        let sticky = any_finite_sum_bits_below(magnitude, cutoff - 1);
        if halfway && (sticky || significand & 1 != 0) {
            significand += 1;
        }
    }

    let mut exponent = highest as i32 - 1074;
    if significand == 1_u64 << 53 {
        significand >>= 1;
        exponent += 1;
    }
    if exponent > 1023 {
        return f64::from_bits(sign | (0x7ff_u64 << 52));
    }
    let exponent_bits = (exponent + 1023) as u64;
    let fraction_bits = significand - (1_u64 << 52);
    f64::from_bits(sign | (exponent_bits << 52) | fraction_bits)
}

#[cfg(test)]
mod tests {
    use super::{exact_binary64_sum, ExactBinary64Accumulator, FINITE_SUM_LIMBS};
    use serde::Deserialize;

    const FIXTURE: &[u8] = include_bytes!("../tests/fixtures/exact_binary64_sum_oracle.json");
    const CHECKSUM: &str = include_str!("../tests/fixtures/exact_binary64_sum_oracle.json.sha256");
    const GENERATOR_SNAPSHOT: &[u8] =
        include_bytes!("../tests/fixtures/generate-exact-binary64-sum-oracle.py.snapshot");
    const GENERATOR_REPOSITORY_PATH: &str = "scripts/generate-exact-binary64-sum-oracle.py";

    #[derive(Deserialize)]
    struct Fixture {
        bounds: Bounds,
        cases: Vec<Case>,
        generator: Generator,
        schema: String,
        schema_revision: usize,
    }

    #[derive(Deserialize)]
    struct Bounds {
        core_arity: usize,
        deterministic_case_count: usize,
        named_case_count: usize,
        tested_arities: Vec<usize>,
        total_case_count: usize,
        variable_arity_case_count: usize,
    }

    #[derive(Deserialize)]
    struct Case {
        expected_bits: String,
        id: String,
        inputs_bits: Vec<String>,
        kind: String,
    }

    #[derive(Deserialize)]
    struct Generator {
        imports_pid_rs: bool,
        path: String,
        sha256: String,
        third_party_dependencies: Vec<String>,
    }

    #[derive(Deserialize)]
    struct CargoPackageContext {
        path_in_vcs: String,
    }

    fn parse_bits(text: &str) -> u64 {
        let digits = text
            .strip_prefix("0x")
            .expect("binary64 oracle bits must use a 0x prefix");
        assert_eq!(digits.len(), 16, "binary64 oracle bits must have 16 digits");
        u64::from_str_radix(digits, 16).expect("binary64 oracle bits must be hexadecimal")
    }

    fn array_reduction(values: &[f64]) -> f64 {
        macro_rules! reduce_array {
            ($length:literal) => {
                exact_binary64_sum::<$length>(
                    values
                        .try_into()
                        .expect("oracle case length must match its dispatched array arity"),
                )
            };
        }
        match values.len() {
            0 => reduce_array!(0),
            1 => reduce_array!(1),
            2 => reduce_array!(2),
            3 => reduce_array!(3),
            4 => reduce_array!(4),
            5 => reduce_array!(5),
            63 => reduce_array!(63),
            64 => reduce_array!(64),
            65 => reduce_array!(65),
            length => panic!("fixture contains undispatched array arity {length}"),
        }
    }

    fn assert_array_and_streaming_reductions(case: &Case, values: &[f64], expected: u64) {
        assert_eq!(
            array_reduction(values).to_bits(),
            expected,
            "case {} failed exact array reduction",
            case.id
        );
        let mut streaming = ExactBinary64Accumulator::default();
        for &value in values {
            assert!(
                streaming.add(value),
                "case {} rejected a finite term",
                case.id
            );
        }
        assert_eq!(
            streaming.total().to_bits(),
            expected,
            "case {} failed streaming reduction",
            case.id
        );
    }

    fn for_each_permutation(values: &mut [f64], start: usize, visit: &mut impl FnMut(&[f64])) {
        if start == values.len() {
            visit(values);
            return;
        }
        for index in start..values.len() {
            values.swap(start, index);
            for_each_permutation(values, start + 1, visit);
            values.swap(start, index);
        }
    }

    #[test]
    fn generator_snapshot_matches_workspace_source_when_available() {
        let manifest_dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR"));
        let workspace_generator = manifest_dir.join("../..").join(GENERATOR_REPOSITORY_PATH);
        match std::fs::read(&workspace_generator) {
            Ok(live_generator) => assert_eq!(
                live_generator, GENERATOR_SNAPSHOT,
                "packaged exact-sum generator snapshot differs from the workspace source"
            ),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                let marker_path = manifest_dir.join(".cargo_vcs_info.json");
                let marker: CargoPackageContext = serde_json::from_slice(
                    &std::fs::read(&marker_path).unwrap_or_else(|marker_error| {
                        panic!(
                            "exact-sum generator source is absent without readable package context at {}: {marker_error}",
                            marker_path.display()
                        )
                    }),
                )
                .expect(".cargo_vcs_info.json package context must contain valid JSON");
                assert_eq!(marker.path_in_vcs, "crates/pid-core");
            }
            Err(error) => panic!(
                "cannot inspect exact-sum generator {}: {error}",
                workspace_generator.display()
            ),
        }
    }

    #[test]
    fn fraction_oracle_matches_array_and_streaming_reductions_across_declared_orders() {
        let expected_hash = CHECKSUM
            .split_whitespace()
            .next()
            .expect("exact-sum checksum must contain a SHA-256 digest");
        assert_eq!(
            pid_runlog::sha256_hex(FIXTURE),
            expected_hash,
            "exact-sum fixture does not match its committed SHA-256 sidecar"
        );

        let fixture: Fixture =
            serde_json::from_slice(FIXTURE).expect("exact-sum fixture must contain valid JSON");
        assert_eq!(fixture.schema, "pid-rs/exact-binary64-sum-oracle");
        assert_eq!(fixture.schema_revision, 2);
        assert_eq!(fixture.bounds.core_arity, 4);
        assert_eq!(fixture.bounds.named_case_count, 24);
        assert_eq!(fixture.bounds.deterministic_case_count, 512);
        assert_eq!(fixture.bounds.variable_arity_case_count, 25);
        assert_eq!(
            fixture.bounds.tested_arities,
            vec![0, 1, 2, 3, 4, 5, 63, 64, 65]
        );
        assert_eq!(fixture.bounds.total_case_count, 561);
        assert_eq!(fixture.cases.len(), fixture.bounds.total_case_count);
        assert_eq!(fixture.generator.path, GENERATOR_REPOSITORY_PATH);
        assert!(!fixture.generator.imports_pid_rs);
        assert!(fixture.generator.third_party_dependencies.is_empty());
        assert_eq!(
            pid_runlog::sha256_hex(GENERATOR_SNAPSHOT),
            fixture.generator.sha256,
            "fixture is not bound to the packaged generator snapshot"
        );

        let observed_variable_cases = fixture
            .cases
            .iter()
            .filter(|case| case.kind == "variable-arity-boundary")
            .count();
        assert_eq!(
            observed_variable_cases,
            fixture.bounds.variable_arity_case_count
        );

        for case in &fixture.cases {
            assert!(
                fixture
                    .bounds
                    .tested_arities
                    .contains(&case.inputs_bits.len()),
                "case {} has undeclared arity {}",
                case.id,
                case.inputs_bits.len()
            );
            let inputs = case
                .inputs_bits
                .iter()
                .map(|text| {
                    let value = f64::from_bits(parse_bits(text));
                    assert!(value.is_finite(), "case {} is non-finite", case.id);
                    value
                })
                .collect::<Vec<_>>();
            let expected = parse_bits(&case.expected_bits);
            if inputs.len() <= 5 {
                let mut permutation = inputs.clone();
                let mut observed_permutations = 0usize;
                for_each_permutation(&mut permutation, 0, &mut |values| {
                    assert_array_and_streaming_reductions(case, values, expected);
                    observed_permutations += 1;
                });
                let expected_permutations = (1..=inputs.len()).product::<usize>().max(1);
                assert_eq!(observed_permutations, expected_permutations);
            } else {
                assert_array_and_streaming_reductions(case, &inputs, expected);
                let mut reversed = inputs.clone();
                reversed.reverse();
                assert_array_and_streaming_reductions(case, &reversed, expected);
                let mut rotated = inputs.clone();
                rotated.rotate_left(1);
                assert_array_and_streaming_reductions(case, &rotated, expected);
                rotated.rotate_right(2);
                assert_array_and_streaming_reductions(case, &rotated, expected);
            }
        }
    }

    #[test]
    fn rejected_additions_leave_the_accumulator_unchanged() {
        let mut non_finite = ExactBinary64Accumulator::default();
        assert!(non_finite.add(1.0));
        let before_non_finite = non_finite.clone();
        assert!(!non_finite.add(f64::INFINITY));
        assert_eq!(non_finite.positive, before_non_finite.positive);
        assert_eq!(non_finite.negative, before_non_finite.negative);
        assert_eq!(non_finite.terms, before_non_finite.terms);

        let mut exhausted = ExactBinary64Accumulator {
            terms: usize::MAX,
            ..ExactBinary64Accumulator::default()
        };
        let before_exhausted = exhausted.clone();
        assert!(!exhausted.add(0.0));
        assert_eq!(exhausted.positive, before_exhausted.positive);
        assert_eq!(exhausted.negative, before_exhausted.negative);
        assert_eq!(exhausted.terms, before_exhausted.terms);

        // This state cannot be reached through successful `add` calls: it deliberately fills every
        // positive limb to exercise the defensive carry-beyond-capacity rollback.
        let mut capacity = ExactBinary64Accumulator {
            positive: [u64::MAX; FINITE_SUM_LIMBS],
            ..ExactBinary64Accumulator::default()
        };
        let before_capacity = capacity.clone();
        assert!(!capacity.add(f64::from_bits(1)));
        assert_eq!(capacity.positive, before_capacity.positive);
        assert_eq!(capacity.negative, before_capacity.negative);
        assert_eq!(capacity.terms, before_capacity.terms);

        // `nextUp(1)` begins at limb 15 with offset 62. Its low fragment succeeds at limb 15,
        // while the deliberately saturated suffix makes the high fragment carry past capacity.
        // This exercises rollback of both fragments rather than only the first-fragment branch.
        let mut split_capacity = ExactBinary64Accumulator::default();
        split_capacity.positive[16..].fill(u64::MAX);
        let before_split_capacity = split_capacity.clone();
        assert!(!split_capacity.add(f64::from_bits(0x3ff0_0000_0000_0001)));
        assert_eq!(split_capacity.positive, before_split_capacity.positive);
        assert_eq!(split_capacity.negative, before_split_capacity.negative);
        assert_eq!(split_capacity.terms, before_split_capacity.terms);
    }
}
