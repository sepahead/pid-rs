# Fable 5 adversarial mathematical-paper review receipt

## Status

- Review date: 2026-07-24
- Model: `claude-fable-5`
- Invocation: Anthropic Messages API over direct HTTPS
- Tool access: none
- Visible-review disposition: no mathematical defect reported at confidence 0.80 or greater
- Evidentiary status: advisory only; not formal proof, executable evidence, independent
  reproduction, or peer review

The review covered the finite-alphabet plug-in convergence paper and the SxPID result under a
dependency coloring. It re-derived the principal equations from the supplied manuscript and proof
sources. It found one documentation defect at confidence 0.85 and three lower-severity scope or
exposition observations. It did not refute either paper's stated exact-real theorem.

## Frozen prompts

- `fable5-mathematical-papers-adversarial-prompt.md`, SHA-256
  `8645ed919ec4f8c04573121b571f7e9dd7ca95a286144013beb1fac45b8e128f`;
- `fable5-mathematical-papers-adversarial-retry-prompt.md`, SHA-256
  `0f033216ac9943898dcbd1ccce40d0e0bb995a40876faf155d21bc5a9cf75ac1`.

The API received file contents in memory. It received no credential values and had no filesystem,
shell, browser, or network tools. Raw model reasoning is not retained or treated as evidence.

## Non-secret API receipts

### Full-context attempt

- Response ID: `msg_011CdMJ41mxNeHEbDhsMaaTt`
- HTTP status: 200
- Stop reason: `max_tokens`
- Input tokens: 126,572
- Output tokens: 64,000
- Reported thinking tokens: 64,000
- Visible review text: none
- Context bytes: 278,148
- Raw-response SHA-256: recorded only as prefix `643765`
- Visible-extraction SHA-256: recorded only as prefix `01ba`
- Context SHA-256: recorded only as prefix `b174`

The prompt SHA-256 is the exact digest above. Other incomplete values are labeled as prefixes and
are not promoted to full digests. This zero-visible-text attempt is failure evidence only.

### Transport failure

One retry through the `TWELFTH` credential route returned HTTP 500 before a usable model response.
It has no response ID, model findings, or evidentiary content. The credential value is not
retained.

### Successful focused retry

- Credential route label: `EIGT`
- Response ID: `msg_011CdML8yTvSzKYRUQt5CznX`
- Model: `claude-fable-5`
- HTTP status: 200
- Stop reason: `end_turn`
- Input tokens: 126,950
- Output tokens: 103,898
- Reported thinking tokens: 95,933
- Context bytes: 279,123
- Raw-response SHA-256:
  `4fafcaec7f0f743ea3dac9d1da74d5529b8ed0f9ce1ae7bd0c0a8377853c6a8e`
- Visible-review SHA-256:
  `a96e792cfe64c0c62e55d657270fcebe7c9698048adc378bf63422aa6cae22c9`
- Context SHA-256:
  `212c894616901d532f7f78ab1555e95b93104d3b77922a0564ce222078bd3cc8`

Only this successful retry supports the findings below. The raw API response was retained outside
the repository only long enough to compute its digest and extract visible findings.

## Positive re-derivations

For the finite-alphabet paper, the review rechecked:

1. finite-support stabilization from coordinatewise convergence and support containment;
2. continuity of the keyed event logarithms, fixed Möbius transform, and finite averaging;
3. the i.i.d. and stationary-ergodic sampling corollaries and the zero-mass-cell argument;
4. continuity but possible nondifferentiability of the finite $I_{\min}$ minimum at a tie;
5. the conservative local $I_{\min}$ modulus; and
6. the clipped Fannes--Audenaert use for marginal entropies.

For the dependency-coloring paper, it rechecked:

1. generalized Hölder with the optimized color exponents and the
   $(\sum_j\sqrt{n_j})^2$ proxy;
2. the Chernoff exponent, subset-union factor, and absence of an additional factor two;
3. the telescoping all-prefix error allocation and drift decomposition;
4. the centered-total-variation path integral and logarithmic event modulus;
5. the nested-event and ordinary-diamond gradient diameters; and
6. the stated conditioned-coordinate bounds under their explicit nonnegativity premises.

## Findings and accepted corrections

| ID | Finding | Disposition |
|---|---|---|
| D1 | The finite paper said the Lean artifact “proves only” a short deterministic list even though the root imports additional event, support-change, dependence, and fractional-cover modules. Confidence: 0.85. | Fixed. Both papers now distinguish the deterministic core, the imported finite keyed-event and fractional-cover results, and the still-missing complete SxPID composition. The checker now inventories all 225 source declarations and audits all 177 source theorem axiom bases. |
| O2 | The prose said Lean did not encode Sx events, but `SxEventBridge` already formalized the heterogeneous keyed source, target, and target-restricted event layer. | Fixed in Markdown, LaTeX, limitations, and a separately compiled semantic contract. |
| O3 | “Exact conditions” in the frozen-transform abstract could be read as necessity, while the theorem states sufficient conditions. | Fixed to “explicit sufficient conditions.” |
| O4 | The dependency paper imports the published component-sign result rather than proving it in Lean; a precise restatement or future formal proof would improve the chain. Confidence below the defect threshold. | Retained as an explicit external theorem premise and formalization obligation. No new proof is claimed. |

## Suggested extensions not yet claimed

The reviewer suggested five mathematically plausible directions:

1. a one-color specialization of the subset concentration bound;
2. Bernstein or Bennett refinements when justified within colors;
3. a two-sided path floor using both endpoint laws;
4. a directional delta method for $I_{\min}$ minimizer ties; and
5. stitched or e-process sequential bounds.

These are research proposals only. None is represented as proved, implemented, calibrated, or
applicable to downstream systems. Each requires its own assumptions, proof, negative controls,
and comparison against the existing theorem before adoption.

## Residual boundary

The review does not verify manuscript-to-Lean correspondence, paper-to-Rust refinement, binary64
rounding, dependence assumptions in a concrete dataset, support-floor knowledge, statistical
calibration, continuous PID consistency, or downstream safety. Those boundaries remain explicit
in the papers and project limitations.
