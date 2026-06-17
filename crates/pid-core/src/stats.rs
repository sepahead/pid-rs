/// Digamma / psi function ψ(x).
///
/// Implementation: recurrence to shift into a "large x" regime + asymptotic expansion.
///
/// Units: natural logarithm (nats).
pub fn digamma(x: f64) -> f64 {
    debug_assert!(x.is_finite());
    debug_assert!(x > 0.0);

    let mut x = x;
    let mut acc = 0.0;

    // Recurrence for small x: ψ(x) = ψ(x+1) - 1/x
    while x < 6.0 {
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
/// KSG-style estimators call `digamma` many times with small positive integers
/// (`k`, `N`, and neighbor counts). This helper avoids repeated work while keeping
/// semantics identical.
pub fn digamma_int_table(n: usize) -> Vec<f64> {
    let mut out = vec![0.0f64; n.saturating_add(1)];
    for (i, v) in out.iter_mut().enumerate().skip(1) {
        *v = digamma(i as f64);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::digamma;

    const EULER_GAMMA: f64 = 0.577_215_664_901_532_9_f64;

    fn harmonic(n: usize) -> f64 {
        // H_n = sum_{k=1..n} 1/k, with H_0 = 0.
        (1..=n).map(|k| 1.0 / (k as f64)).sum()
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
                (psi_n - expected).abs() < 1e-12,
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
}
