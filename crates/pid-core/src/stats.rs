use crate::error::{PidError, PidResult};
use crate::resource::{try_vec_filled, ResourceBudget};

/// Mean of finite values, scaled before summation so avoidable intermediate overflow does not
/// reject a representable result.
pub(crate) fn finite_mean(values: &[f64], context: &'static str) -> PidResult<f64> {
    let (scale, mean_scaled) = scaled_mean_parts(values, context)?;
    let mean = scale * mean_scaled;
    if mean.is_finite() {
        Ok(mean)
    } else {
        Err(PidError::NumericalInstability { context })
    }
}

/// Population mean and standard deviation of finite values.
///
/// Both passes operate after division by `max(abs(x))`. This matters for data such as
/// `[0, f64::MAX]`: its mean and standard deviation are both finite, even though forming either
/// the raw sum or the raw variance overflows.
pub(crate) fn finite_mean_std_population(
    values: &[f64],
    context: &'static str,
) -> PidResult<(f64, f64)> {
    finite_mean_std(values, 0, context)
}

/// Sample mean and standard deviation (Bessel-corrected, denominator `n-1`).
#[cfg(feature = "experimental-pipelines")]
pub(crate) fn finite_mean_std_sample(
    values: &[f64],
    context: &'static str,
) -> PidResult<(f64, f64)> {
    finite_mean_std(values, 1, context)
}

fn finite_mean_std(values: &[f64], ddof: usize, context: &'static str) -> PidResult<(f64, f64)> {
    if values.len() <= ddof {
        return Err(PidError::InvalidConfig {
            context,
            message: "not enough values for the requested variance degrees of freedom",
        });
    }
    let (scale, mean_scaled) = scaled_mean_parts(values, context)?;
    if scale == 0.0 {
        return Ok((0.0, 0.0));
    }

    let sum_squared_scaled = compensated_sum(values.iter().map(|value| {
        let deviation = value / scale - mean_scaled;
        deviation * deviation
    }));
    let variance_scaled = sum_squared_scaled / (values.len() - ddof) as f64;
    // For |x| <= scale, the exact population variance is <= scale^2. Permit a small floating
    // tolerance, then restore that mathematical bound so `scale * sqrt(var)` cannot spuriously
    // overflow at `f64::MAX`.
    let variance_bound = values.len() as f64 / (values.len() - ddof) as f64;
    let tolerance = 64.0 * f64::EPSILON * variance_bound;
    if !variance_scaled.is_finite()
        || variance_scaled < -tolerance
        || variance_scaled > variance_bound + tolerance
    {
        return Err(PidError::NumericalInstability { context });
    }
    let std = scale * variance_scaled.clamp(0.0, variance_bound).sqrt();
    let mean = scale * mean_scaled;
    if mean.is_finite() && std.is_finite() {
        Ok((mean, std))
    } else {
        Err(PidError::NumericalInstability { context })
    }
}

fn scaled_mean_parts(values: &[f64], context: &'static str) -> PidResult<(f64, f64)> {
    if values.is_empty() {
        return Err(PidError::InvalidConfig {
            context,
            message: "need at least one value",
        });
    }
    if values.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NonFiniteInput { context });
    }
    let scale = values
        .iter()
        .fold(0.0_f64, |current, value| current.max(value.abs()));
    if scale == 0.0 {
        return Ok((0.0, 0.0));
    }

    let raw_mean_scaled =
        compensated_sum(values.iter().map(|value| value / scale)) / values.len() as f64;
    let tolerance = 64.0 * f64::EPSILON;
    if !raw_mean_scaled.is_finite() || raw_mean_scaled.abs() > 1.0 + tolerance {
        return Err(PidError::NumericalInstability { context });
    }
    Ok((scale, raw_mean_scaled.clamp(-1.0, 1.0)))
}

/// Deterministic Neumaier compensated summation in iterator order.
///
/// Callers remain responsible for ensuring that the mathematical sum is representable. Keeping
/// this helper crate-visible lets estimators share one stable accumulation policy without exposing
/// it as part of the public API.
pub(crate) fn compensated_sum(values: impl IntoIterator<Item = f64>) -> f64 {
    let mut sum = 0.0;
    let mut correction = 0.0;
    for value in values {
        let next = sum + value;
        if sum.abs() >= value.abs() {
            correction += (sum - next) + value;
        } else {
            correction += (value - next) + sum;
        }
        sum = next;
    }
    sum + correction
}

/// Digamma / psi function ψ(x).
///
/// Implementation: recurrence to shift into a "large x" regime + asymptotic expansion.
///
/// Units: natural logarithm (nats).
#[cfg(any(feature = "experimental-heuristics", test))]
pub(crate) fn digamma(x: f64) -> f64 {
    debug_assert!(x.is_finite());
    debug_assert!(x > 0.0);

    let mut x = x;
    let mut acc = 0.0;

    // Recurrence for small x: ψ(x) = ψ(x+1) - 1/x
    // Shifting to 8 keeps the truncated Bernoulli expansion comfortably below 1e-13 error at
    // the small integer arguments retained by the non-cancelling research heuristic and
    // regression tests. Stopping at 6 leaves a ~9.3e-13 bias in psi(1).
    while x < 8.0 {
        acc -= 1.0 / x;
        x += 1.0;
    }

    // Asymptotic series (Stirling-like).
    // ψ(x) ≈ ln(x) - 1/(2x) - 1/(12x²) + 1/(120x⁴) - 1/(252x⁶) + 1/(240x⁸) - 1/(132x¹⁰) + 691/(32760x¹²) - ...
    let inv = 1.0 / x;
    let inv2 = inv * inv;
    let inv4 = inv2 * inv2;
    let inv6 = inv4 * inv2;
    let inv8 = inv4 * inv4;
    let inv10 = inv8 * inv2;
    let inv12 = inv6 * inv6;

    acc + x.ln() - 0.5 * inv - (1.0 / 12.0) * inv2 + (1.0 / 120.0) * inv4 - (1.0 / 252.0) * inv6
        + (1.0 / 240.0) * inv8
        - (1.0 / 132.0) * inv10
        + (691.0 / 32760.0) * inv12
}

/// Precompute ψ(i) for integer `i` in `0..=n` (with index 0 unused).
///
/// The non-cancelling research heuristic calls `digamma` repeatedly at small positive integer
/// count arguments. This helper preserves that general special-function path; coefficient-
/// cancelling KSG and shared-exclusions paths use [`shifted_harmonic_table`] instead.
#[cfg(feature = "experimental-heuristics")]
pub(crate) fn digamma_int_table(n: usize) -> PidResult<Vec<f64>> {
    let len = n.checked_add(1).ok_or(PidError::SizeOverflow {
        operation: "digamma_int_table",
    })?;
    let mut out = try_vec_filled("digamma_int_table", len, 0.0f64, ResourceBudget::default())?;
    for (i, v) in out.iter_mut().enumerate().skip(1) {
        *v = digamma(i as f64);
    }
    Ok(out)
}

/// Precompute the positive-integer part of digamma without Euler's constant.
///
/// The returned table is indexed by the positive digamma argument and stores
/// `table[m] = H_(m-1)`, with index zero unused. Prefixes use deterministic Neumaier
/// compensation. This has the same `n + 1` binary64 allocation shape as `digamma_int_table`,
/// but it is only definition-preserving where all Euler-constant coefficients cancel.
pub(crate) fn shifted_harmonic_table(n: usize) -> PidResult<Vec<f64>> {
    let len = n.checked_add(1).ok_or(PidError::SizeOverflow {
        operation: "shifted_harmonic_table",
    })?;
    let mut out = try_vec_filled(
        "shifted_harmonic_table",
        len,
        0.0_f64,
        ResourceBudget::default(),
    )?;
    let mut sum = 0.0_f64;
    let mut correction = 0.0_f64;
    // `argument` is the mathematical digamma argument and the table index; retaining that exact
    // correspondence makes the audited off-by-one contract visible at the write site.
    #[expect(
        clippy::needless_range_loop,
        reason = "the loop index is the audited digamma argument and table index"
    )]
    for argument in 2..=n {
        let value = 1.0 / (argument - 1) as f64;
        let next = sum + value;
        if sum.abs() >= value.abs() {
            correction += (sum - next) + value;
        } else {
            correction += (value - next) + sum;
        }
        sum = next;
        out[argument] = sum + correction;
    }
    Ok(out)
}

/// Evaluate a cancelling four-integer-digamma KSG term from shifted harmonic prefixes.
///
/// For positive arguments satisfying `k <= x,y <= n`, this evaluates
/// `psi(k) + psi(n) - psi(x) - psi(y)` as the source-symmetric range expression
/// `(H_(n-1) - H_(max(x,y)-1)) - (H_(min(x,y)-1) - H_(k-1))`.
/// KSG's exclusive counts therefore pass `x = nx + 1`, while inclusive shared-exclusions counts
/// pass their count directly. The exact-real identity is universal on that integer domain; the
/// binary64 prefix evaluation is not a universal correct-rounding guarantee.
#[inline]
pub(crate) fn ksg_local_harmonic_term(
    shifted_harmonics: &[f64],
    k: usize,
    n: usize,
    x: usize,
    y: usize,
) -> f64 {
    debug_assert!(k > 0);
    debug_assert!(k <= x && x <= n);
    debug_assert!(k <= y && y <= n);
    debug_assert!(n < shifted_harmonics.len());
    let lower = x.min(y);
    let upper = x.max(y);
    (shifted_harmonics[n] - shifted_harmonics[upper])
        - (shifted_harmonics[lower] - shifted_harmonics[k])
}

#[cfg(test)]
mod tests {
    #[cfg(feature = "experimental-pipelines")]
    use super::finite_mean_std_sample;
    use super::{
        digamma, finite_mean, finite_mean_std_population, ksg_local_harmonic_term,
        shifted_harmonic_table,
    };
    use serde::Deserialize;

    const EULER_GAMMA: f64 = 0.577_215_664_901_532_9_f64;
    const KSG_ARITHMETIC_FIXTURE: &[u8] =
        include_bytes!("../tests/fixtures/ksg_local_arithmetic_oracle.json");
    const KSG_ARITHMETIC_CHECKSUM: &str =
        include_str!("../tests/fixtures/ksg_local_arithmetic_oracle.json.sha256");
    const KSG_ARITHMETIC_GENERATOR_SNAPSHOT: &[u8] =
        include_bytes!("../tests/fixtures/generate-ksg-local-arithmetic-oracle.py.snapshot");
    const KSG_ARITHMETIC_GENERATOR_REPOSITORY_PATH: &str =
        "scripts/generate-ksg-local-arithmetic-oracle.py";
    const KSG_ARITHMETIC_GENERATOR_SHA256: &str =
        "a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b";
    const KSG_EXHAUSTIVE_CASES: usize = 6_920;
    const KSG_STRESS_CASES: usize = 1_278;
    const KSG_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS: usize = 240;
    const KSG_ENDPOINT_CANCELLATION_STRESS_ZEROS: usize = 114;
    const KSG_ENDPOINT_CANCELLATION_ZEROS: usize = 354;
    const KSG_FULL_CORPUS_NONZEROS: usize = 7_844;
    const KSG_ENDPOINT_DIRECT_LEFT_NONZEROS: usize = 150;
    const KSG_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS: usize = 121;
    // This Rust-only comparator first rounds each stored Decimal text to binary64. The separate
    // directed-enclosure route checks the selected binary64 result against the exact rational.
    // The 32-epsilon gate is a finite-corpus margin under either metric, not a universal theorem.
    const KSG_ROUNDED_REFERENCE_OBSERVED_MAX_ERROR_NATS: f64 = 8.0 * f64::EPSILON;
    const KSG_ROUNDED_REFERENCE_MAX_ERROR_TIES: usize = 40;
    const KSG_ROUNDED_REFERENCE_MAX_ERROR_NATS: f64 = 32.0 * f64::EPSILON;

    #[derive(Deserialize)]
    struct KsgArithmeticFixture {
        arithmetic: KsgArithmeticMetadata,
        bounds: KsgArithmeticBounds,
        cases: Vec<KsgArithmeticCase>,
        generator: KsgArithmeticGenerator,
        schema: String,
        schema_revision: usize,
    }

    #[derive(Deserialize)]
    struct KsgArithmeticMetadata {
        decimal_precision_digits: usize,
        endpoint_cancellation_exact_zero_case_count: usize,
        endpoint_cancellation_exact_zero_exhaustive_case_count: usize,
        endpoint_cancellation_exact_zero_rule: String,
        endpoint_cancellation_exact_zero_stress_case_count: usize,
        exact_identity: String,
        logarithm_unit: String,
    }

    #[derive(Deserialize)]
    struct KsgArithmeticBounds {
        exhaustive_case_count: usize,
        exhaustive_max_samples: usize,
        exhaustive_rule: String,
        stress_case_count: usize,
        stress_sample_sizes: Vec<usize>,
    }

    #[derive(Deserialize)]
    struct KsgArithmeticGenerator {
        imports_pid_rs: bool,
        path: String,
        sha256: String,
        third_party_dependencies: Vec<String>,
    }

    #[derive(Deserialize)]
    struct KsgArithmeticCase {
        expected_nats: String,
        k: usize,
        sample_count: usize,
        x_count: usize,
        y_count: usize,
    }

    #[derive(Deserialize)]
    struct CargoPackageContext {
        path_in_vcs: String,
    }

    fn harmonic(n: usize) -> f64 {
        // H_n = sum_{k=1..n} 1/k, with H_0 = 0.
        (1..=n).map(|k| 1.0 / (k as f64)).sum()
    }

    #[test]
    fn packaged_ksg_generator_snapshot_matches_workspace_source_when_available() {
        let manifest_dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR"));
        let workspace_generator = manifest_dir
            .join("../..")
            .join(KSG_ARITHMETIC_GENERATOR_REPOSITORY_PATH);
        match std::fs::read(&workspace_generator) {
            Ok(live_generator) => assert_eq!(
                live_generator, KSG_ARITHMETIC_GENERATOR_SNAPSHOT,
                "packaged KSG generator snapshot differs from the canonical workspace source"
            ),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                let marker_path = manifest_dir.join(".cargo_vcs_info.json");
                // CONTEXT: Cargo places this metadata file in normalized package source trees.
                // Its path binding distinguishes the intended package layout from an arbitrary
                // source omission; it is not archive-authenticity or provenance evidence.
                let marker_metadata =
                    std::fs::symlink_metadata(&marker_path).unwrap_or_else(|marker_error| {
                        panic!(
                            "canonical KSG generator source is absent without a qualifying \
                             package-context marker; cannot inspect {}: {marker_error}",
                            marker_path.display()
                        )
                    });
                assert!(
                    marker_metadata.file_type().is_file(),
                    ".cargo_vcs_info.json package-context marker must be a regular file"
                );
                let marker: CargoPackageContext = serde_json::from_slice(
                    &std::fs::read(&marker_path)
                        .expect("cannot read .cargo_vcs_info.json package-context marker"),
                )
                .expect(".cargo_vcs_info.json package-context marker must contain valid JSON");
                assert_eq!(
                    marker.path_in_vcs, "crates/pid-core",
                    ".cargo_vcs_info.json package-context marker does not identify the pid-core \
                     source path"
                );
            }
            Err(error) => panic!(
                "cannot read canonical KSG generator source {}: {error}",
                workspace_generator.display()
            ),
        }
    }

    #[test]
    fn cargo_package_context_rejects_duplicate_path_bindings() {
        let ambiguous = br#"{
            "path_in_vcs": "forged",
            "path_in_vcs": "crates/pid-core"
        }"#;
        assert!(
            serde_json::from_slice::<CargoPackageContext>(ambiguous).is_err(),
            "duplicate package-context path bindings must be rejected"
        );
    }

    #[test]
    fn digamma_matches_known_integer_values() {
        // ψ(1) = -γ
        let psi1 = digamma(1.0);
        assert!((psi1 + EULER_GAMMA).abs() < 1e-12, "psi(1)={psi1}");

        // ψ(n) = H_{n-1} - γ for integer n>=2
        for n in 2..=25usize {
            let psi_n = digamma(n as f64);
            let expected = harmonic(n - 1) - EULER_GAMMA;
            assert!(
                (psi_n - expected).abs() < 5e-14,
                "psi({n})={psi_n} expected={expected}"
            );
        }
    }

    #[test]
    fn digamma_recurrence_holds() {
        // ψ(x+1) = ψ(x) + 1/x
        let x = 3.7;
        let lhs = digamma(x + 1.0);
        let rhs = digamma(x) + 1.0 / x;
        assert!((lhs - rhs).abs() < 5e-13, "lhs={lhs} rhs={rhs}");
    }

    #[test]
    fn ksg_integer_harmonic_range_matches_decimal_oracle() {
        let mut checksum_fields = KSG_ARITHMETIC_CHECKSUM.split_whitespace();
        let expected_hash = checksum_fields
            .next()
            .expect("KSG arithmetic checksum must contain a SHA-256 digest");
        assert_eq!(
            checksum_fields.next(),
            Some("ksg_local_arithmetic_oracle.json"),
            "KSG arithmetic checksum filename changed"
        );
        assert_eq!(
            checksum_fields.next(),
            None,
            "KSG arithmetic checksum has trailing fields"
        );
        assert_eq!(
            pid_runlog::sha256_hex(KSG_ARITHMETIC_FIXTURE),
            expected_hash,
            "KSG arithmetic fixture does not match its committed SHA-256 digest"
        );

        let fixture: KsgArithmeticFixture = serde_json::from_slice(KSG_ARITHMETIC_FIXTURE)
            .expect("KSG arithmetic fixture must contain valid JSON");
        assert_eq!(fixture.schema, "pid-rs/ksg-local-arithmetic-oracle");
        assert_eq!(fixture.schema_revision, 2);
        assert_eq!(fixture.arithmetic.decimal_precision_digits, 80);
        assert_eq!(
            fixture
                .arithmetic
                .endpoint_cancellation_exact_zero_case_count,
            KSG_ENDPOINT_CANCELLATION_ZEROS
        );
        assert_eq!(
            fixture
                .arithmetic
                .endpoint_cancellation_exact_zero_exhaustive_case_count,
            KSG_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS
        );
        assert_eq!(
            fixture.arithmetic.endpoint_cancellation_exact_zero_rule,
            "{nx,ny}={k-1,n-1}; cancel equal symbolic harmonic terms before Decimal evaluation"
        );
        assert_eq!(
            fixture
                .arithmetic
                .endpoint_cancellation_exact_zero_stress_case_count,
            KSG_ENDPOINT_CANCELLATION_STRESS_ZEROS
        );
        assert_eq!(
            fixture.arithmetic.exact_identity,
            "H_(k-1) + H_(n-1) - H_(nx) - H_(ny)"
        );
        assert_eq!(fixture.arithmetic.logarithm_unit, "nats");
        assert_eq!(fixture.bounds.exhaustive_case_count, KSG_EXHAUSTIVE_CASES);
        assert_eq!(fixture.bounds.exhaustive_max_samples, 16);
        assert_eq!(
            fixture.bounds.exhaustive_rule,
            "2 <= n <= bound; 1 <= k < n; k-1 <= nx,ny < n"
        );
        assert_eq!(fixture.bounds.stress_case_count, KSG_STRESS_CASES);
        assert_eq!(
            fixture.bounds.stress_sample_sizes,
            [17, 32, 64, 256, 4_096, 65_536, 1_000_000]
        );
        assert_eq!(fixture.cases.len(), KSG_EXHAUSTIVE_CASES + KSG_STRESS_CASES);
        let endpoint_cancellation_cases = fixture
            .cases
            .iter()
            .filter(|case| {
                let low = case.k - 1;
                let high = case.sample_count - 1;
                matches!(
                    (case.x_count, case.y_count),
                    (x, y) if (x, y) == (low, high) || (x, y) == (high, low)
                )
            })
            .collect::<Vec<_>>();
        assert_eq!(
            endpoint_cancellation_cases.len(),
            KSG_ENDPOINT_CANCELLATION_ZEROS
        );
        assert!(endpoint_cancellation_cases
            .iter()
            .all(|case| case.expected_nats == "0"));
        let endpoint_cancellation_exhaustive_cases = endpoint_cancellation_cases
            .iter()
            .filter(|case| case.sample_count <= 16)
            .count();
        let endpoint_cancellation_stress_cases = endpoint_cancellation_cases
            .iter()
            .filter(|case| case.sample_count > 16)
            .count();
        assert_eq!(
            endpoint_cancellation_exhaustive_cases, KSG_ENDPOINT_CANCELLATION_EXHAUSTIVE_ZEROS,
            "row-derived exhaustive endpoint-cancellation count changed"
        );
        assert_eq!(
            endpoint_cancellation_stress_cases, KSG_ENDPOINT_CANCELLATION_STRESS_ZEROS,
            "row-derived stress endpoint-cancellation count changed"
        );
        let canonical_zero_cases = fixture
            .cases
            .iter()
            .filter(|case| case.expected_nats == "0")
            .collect::<Vec<_>>();
        assert_eq!(canonical_zero_cases.len(), KSG_ENDPOINT_CANCELLATION_ZEROS);
        assert!(canonical_zero_cases.iter().all(|case| {
            let low = case.k - 1;
            let high = case.sample_count - 1;
            (case.x_count, case.y_count) == (low, high)
                || (case.x_count, case.y_count) == (high, low)
        }));
        assert_eq!(
            fixture.generator.path,
            KSG_ARITHMETIC_GENERATOR_REPOSITORY_PATH
        );
        assert!(!fixture.generator.imports_pid_rs);
        assert!(fixture.generator.third_party_dependencies.is_empty());
        assert_eq!(
            pid_runlog::sha256_hex(KSG_ARITHMETIC_GENERATOR_SNAPSHOT),
            KSG_ARITHMETIC_GENERATOR_SHA256,
            "packaged KSG fixture-generator snapshot changed from the reviewed revision-4 digest"
        );
        assert_eq!(
            fixture.generator.sha256, KSG_ARITHMETIC_GENERATOR_SHA256,
            "KSG arithmetic fixture is not bound to the reviewed live generator digest"
        );

        let max_argument = fixture
            .cases
            .iter()
            .map(|case| case.sample_count)
            .max()
            .expect("KSG arithmetic fixture must be nonempty");
        let shifted_harmonics = shifted_harmonic_table(max_argument)
            .expect("bounded shifted harmonic table must fit the default resource budget");
        let mut naive_shifted_harmonics = vec![0.0_f64; max_argument + 1];
        let mut naive_total = 0.0_f64;
        for (argument, prefix) in naive_shifted_harmonics.iter_mut().enumerate().skip(2) {
            naive_total += 1.0 / (argument - 1) as f64;
            *prefix = naive_total;
        }
        let mut maximum_rounded_reference_error = 0.0_f64;
        let mut first_maximum = None;
        let mut maximum_error_ties = 0_usize;
        let mut swap_bit_asymmetries = 0_usize;
        let mut full_corpus_positive_zero_outputs = 0_usize;
        let mut full_corpus_negative_zero_outputs = 0_usize;
        let mut full_corpus_nonzero_outputs = 0_usize;
        let mut endpoint_positive_zero_outputs = 0_usize;
        let mut endpoint_direct_left_nonzeros = 0_usize;
        let mut endpoint_direct_left_negative_zeros = 0_usize;
        let mut naive_prefix_direct_left_nonzeros = 0_usize;
        let mut naive_prefix_direct_left_negative_zeros = 0_usize;
        for case in &fixture.cases {
            assert!(case.sample_count >= 2);
            assert!((1..case.sample_count).contains(&case.k));
            assert!((case.k - 1..case.sample_count).contains(&case.x_count));
            assert!((case.k - 1..case.sample_count).contains(&case.y_count));
            let rounded_reference = case
                .expected_nats
                .parse::<f64>()
                .expect("Decimal oracle value must be representable as finite f64");
            let actual = ksg_local_harmonic_term(
                &shifted_harmonics,
                case.k,
                case.sample_count,
                case.x_count + 1,
                case.y_count + 1,
            );
            let source_swapped = ksg_local_harmonic_term(
                &shifted_harmonics,
                case.k,
                case.sample_count,
                case.y_count + 1,
                case.x_count + 1,
            );
            assert!(
                rounded_reference.is_finite() && actual.is_finite() && source_swapped.is_finite(),
                "every frozen-corpus reference and selected helper output must be finite"
            );
            match actual.to_bits() {
                bits if bits == 0.0_f64.to_bits() => full_corpus_positive_zero_outputs += 1,
                bits if bits == (-0.0_f64).to_bits() => full_corpus_negative_zero_outputs += 1,
                _ => full_corpus_nonzero_outputs += 1,
            }
            let low = case.k - 1;
            let high = case.sample_count - 1;
            if (case.x_count, case.y_count) == (low, high)
                || (case.x_count, case.y_count) == (high, low)
            {
                assert_eq!(
                    actual.to_bits(),
                    0.0_f64.to_bits(),
                    "endpoint cancellation must follow the selected positive-zero path"
                );
                endpoint_positive_zero_outputs += 1;
                let direct_left = ((shifted_harmonics[case.k]
                    + shifted_harmonics[case.sample_count])
                    - shifted_harmonics[case.x_count + 1])
                    - shifted_harmonics[case.y_count + 1];
                endpoint_direct_left_nonzeros += usize::from(direct_left != 0.0);
                endpoint_direct_left_negative_zeros +=
                    usize::from(direct_left.to_bits() == (-0.0_f64).to_bits());
                let naive_direct_left = ((naive_shifted_harmonics[case.k]
                    + naive_shifted_harmonics[case.sample_count])
                    - naive_shifted_harmonics[case.x_count + 1])
                    - naive_shifted_harmonics[case.y_count + 1];
                naive_prefix_direct_left_nonzeros += usize::from(naive_direct_left != 0.0);
                naive_prefix_direct_left_negative_zeros +=
                    usize::from(naive_direct_left.to_bits() == (-0.0_f64).to_bits());
            }
            swap_bit_asymmetries += usize::from(actual.to_bits() != source_swapped.to_bits());
            let error = if actual.is_finite() && rounded_reference.is_finite() {
                (actual - rounded_reference).abs()
            } else {
                f64::INFINITY
            };
            if error > maximum_rounded_reference_error {
                maximum_rounded_reference_error = error;
                first_maximum = Some((
                    case.sample_count,
                    case.k,
                    case.x_count,
                    case.y_count,
                    actual,
                    rounded_reference,
                ));
                maximum_error_ties = 1;
            } else if error == maximum_rounded_reference_error {
                maximum_error_ties += 1;
            }
        }

        assert_eq!(swap_bit_asymmetries, 0);
        assert_eq!(
            (
                full_corpus_positive_zero_outputs,
                full_corpus_negative_zero_outputs,
                full_corpus_nonzero_outputs,
            ),
            (KSG_ENDPOINT_CANCELLATION_ZEROS, 0, KSG_FULL_CORPUS_NONZEROS,),
            "direct full-corpus selected-output +0/-0/nonzero partition changed"
        );
        assert_eq!(
            endpoint_positive_zero_outputs,
            KSG_ENDPOINT_CANCELLATION_ZEROS
        );
        assert_eq!(
            endpoint_direct_left_nonzeros, KSG_ENDPOINT_DIRECT_LEFT_NONZEROS,
            "ordinary left association over the selected Neumaier prefix changed"
        );
        assert_eq!(
            endpoint_direct_left_negative_zeros, 0,
            "ordinary left association produced a negative zero on an endpoint"
        );
        assert_eq!(
            naive_prefix_direct_left_nonzeros, KSG_NAIVE_PREFIX_DIRECT_LEFT_NONZEROS,
            "ordinary left association over the naive prefix changed"
        );
        assert_eq!(
            naive_prefix_direct_left_negative_zeros, 0,
            "ordinary left association over the naive prefix produced a negative zero"
        );
        assert_eq!(
            maximum_rounded_reference_error, KSG_ROUNDED_REFERENCE_OBSERVED_MAX_ERROR_NATS,
            "the frozen binary64-rounded-reference maximum changed: {first_maximum:?}"
        );
        assert!(
            matches!(first_maximum, Some((4_096, 1, 2_048, 2_048, _, _))),
            "the first maximum-attaining tuple changed: {first_maximum:?}"
        );
        assert_eq!(
            maximum_error_ties, KSG_ROUNDED_REFERENCE_MAX_ERROR_TIES,
            "the frozen binary64-rounded-reference maximum-error tie multiplicity changed"
        );
        assert!(
            maximum_rounded_reference_error <= KSG_ROUNDED_REFERENCE_MAX_ERROR_NATS,
            "binary64-rounded-reference error {maximum_rounded_reference_error:.17e} nats \
             exceeds the declared bound {KSG_ROUNDED_REFERENCE_MAX_ERROR_NATS:.17e}; \
             first maximum: {first_maximum:?}"
        );
    }

    #[test]
    fn ksg_shifted_harmonic_indices_cover_off_by_one_boundaries() {
        let shifted = shifted_harmonic_table(4).unwrap();
        assert_eq!(shifted[1].to_bits(), 0.0_f64.to_bits());
        assert_eq!(ksg_local_harmonic_term(&shifted, 1, 2, 1, 1), 1.0);
        for (k, x, y, expected) in [
            (1, 1, 1, 11.0 / 6.0),
            (2, 2, 2, 5.0 / 6.0),
            (3, 4, 4, -1.0 / 3.0),
        ] {
            let actual = ksg_local_harmonic_term(&shifted, k, 4, x, y);
            assert!((actual - expected).abs() <= 2.0 * f64::EPSILON);
            assert_eq!(
                actual.to_bits(),
                ksg_local_harmonic_term(&shifted, k, 4, y, x).to_bits()
            );
        }
    }

    #[test]
    fn scaled_moments_keep_representable_extreme_results_finite() {
        let (mean, std) = finite_mean_std_population(&[0.0, f64::MAX], "extreme moments").unwrap();
        assert_eq!(mean, f64::MAX * 0.5);
        assert_eq!(std, f64::MAX * 0.5);

        let (mean, std) =
            finite_mean_std_population(&[-f64::MAX, f64::MAX], "extreme moments").unwrap();
        assert_eq!(mean, 0.0);
        assert_eq!(std, f64::MAX);

        assert_eq!(
            finite_mean(&[f64::MAX; 4], "extreme mean").unwrap(),
            f64::MAX
        );
    }

    #[test]
    fn scaled_moments_reject_empty_or_nonfinite_input() {
        assert!(finite_mean(&[], "empty mean").is_err());
        assert!(finite_mean_std_population(&[f64::NAN], "nan moments").is_err());
        #[cfg(feature = "experimental-pipelines")]
        assert!(finite_mean_std_sample(&[1.0], "singleton sample").is_err());
    }
}
