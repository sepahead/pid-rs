# Adjudication of a mathematical and statistical review

Status: dated review record, 30 October 2026. It changes no theorem, estimator or evidence class by
itself. The repairs and additions that followed from it are listed in section 5.

## 1. What was reviewed, and by whom

On 28 October 2026 one AI agent wrote a mathematical and statistical review of the October research
in this repository. The review is kept outside the repository; it has 87,394 bytes and SHA-256
`30946ac52e8bd06da71c0f01f03c42f280da7167356c379813ad08e028722da7`. Its subjects were:

- the [source-partition report](../research/source-coupling-compression/EXPOSITION.md) of 24 October
  2026 and its scripts and data;
- the [binary allocation bound](../../output/BINARY_SXPID_ALLOCATION_BOUND_2026_10_13.md) and its
  [alternative routes](../../output/BINARY_SXPID_BOUND_ALTERNATIVES_2026_10_13.md);
- the [October research notes](../../output/RESEARCH_NOTES_2026_10_10.md);
- the restricted angular bound of 5 October 2026, summarized in
  [`RESEARCH_RESULTS_2026_10_05.md`](../../RESEARCH_RESULTS_2026_10_05.md);
- the SxPID3 certificate route and selected statistical and Rust code.

A second AI agent session adjudicated the review. It treated every claim, including its own, as a
hypothesis until the repository bytes or a computation settled it. Three further inputs were used
the same way:

- three auditors running a model of another vendor (OpenAI Codex), each started alone on the same
  written brief; one finished, and two stopped at a usage limit, so only their progress logs exist;
- a written assessment of the review by a further AI agent.

All of these are model output. Their agreement is correlated, not independent evidence. No human
reviewed this record.

The independent checks of this adjudication are kept as inert scripts in
[`math-stats-review-adjudication-2026-10-30/`](math-stats-review-adjudication-2026-10-30/). They read
the published data and write nothing. They are not repository commands.

## 2. Verdict on the review

The review is sound in its main mathematics and its reproduced defects. Its statistical discussion
is incomplete, and some sentences claim slightly more than its checks show.

| Review claim | Verdict | How it was checked |
|---|---|---|
| F1: the study runner looks for raw data in the wrong directory | Confirmed | `run_study_v3.py` took the second parent of its directory, which is `audit/research`; the scripts guide names the repository root. |
| F2: the post-study bound check reads files that were never published | Confirmed | `post_study_bound.py` read `POST_BOUND_INPUTS.json` and `campaign-v3-normal/`; neither exists in the study directory. |
| F3: the report still calls itself an unadmitted local draft | Confirmed | Report sections 8 and 10; its commit is an ancestor of `main`. Being on `main` does not settle the scientific questions that section 8 leaves open. |
| F4: the project selects Lean 4.33.0 although 4.35.0 is installed | Confirmed for this machine | The project file pins 4.33.0 and the launcher selects it there; 4.35.0 runs when called directly. The review's statements about the upstream release notes were checked online by one auditor only. |
| Coupling bound: event construction, nested-union inequality, common refinement, weights 22 and 1, inverse mass 65, coefficient 67, lower bound (8), $D=L+2R$ | Confirmed | An independent implementation computed the Möbius function by its recursion instead of matrix inversion and reproduced every constant. On 300 random distributions with deterministic and random recodings, no bound was violated; the movement never exceeded 4.1% of the coupling bound. |
| The range bound (11) beats the coupling bound on every distribution with movement | Confirmed | This is the report's own result; the review extends it from the six pooled to all 21 distributions with movement. |
| Binary bound $D\le(3+\beta)H(C)$ and $3\le K_\star\le3+\beta$ | Confirmed | Derivation re-read; the stress tests reproduced. |
| At most four target labels suffice for the binary supremum | Confirmed | For a fixed source distribution the change vector is affine in the label weights and the objective is convex, so its maximum is at a vertex of the weight polytope, which has at most four positive weights. |
| A target-conditioned form of the coupling bound | Confirmed | Reproduced independently; it improves the bound strictly on 13 of 30 distributions. See [addendum section 4](../research/source-coupling-compression/ADDENDUM-2026-10-30.md). |
| A lower bound from all seven information changes | Confirmed | It has a closed form, which the review did not find; see section 3. |
| Angular constants $B_8=1/60{,}162{,}048$, $A\ge r^2/12$, $1/1{,}253{,}376$, $1/1{,}410{,}048$ | Confirmed | Re-derived. The review omits the condition $0<\lvert a\rvert+\lvert b\rvert\le1/2$, which the repository already states. |
| The six appendix programs | Confirmed, with two gaps | They compute what the review says. The wire-format check does not compare the semantic header fields, and the angular arithmetic program is not included. One auditor checked all 90 headers separately and found them correct. |

Four sentences of the review should read differently:

- "$D=L+2R$ under deterministic compression": the identity holds for every pair of distributions on
  the same lattice; determinism only adds $L\ge0$.
- "a uniform relative error of $1/1{,}253{,}376$": only for $0<\lvert a\rvert+\lvert b\rvert\le1/2$
  and with every proper term evaluated exactly.
- "all 6,480 saved values matched": the exact products, signs and digests matched, and 90-digit
  decimal values lay inside the saved intervals. Two auditors also enclosed all 6,480 values with
  rational outward intervals; this record did not repeat that enclosure.
- "headers matched": the decoded rows, their order and the padding matched.

## 3. What the review missed

Every item below was recomputed from the published data for this record.

1. **The evaluation days differ strongly from the training days.** On every office test row the
   carbon-dioxide bit is 1. Of the office validation and test rows, 54.5% and 49.0% fall outside the
   two pairs that the code keeps, against 16.1% in training. On the room validation days both motion
   bits are constant. The office movements therefore measure a training-frozen code under this
   shift.
2. **Why no information is lost on the office evaluation days.** On test days the code is one-to-one
   on the pairs that occur. On validation days it merges two pairs only for rows with light off, and
   all of those rows are unoccupied.
3. **In-sample scores and an untested branch.** 205 of the 445 score records are computed on
   training rows. No record contains a context absent from training, so the fallback for unseen
   contexts is never exercised.
4. **Refitting also changes the smoothing**, because a merged context receives one pseudocount per
   class where the original contexts had one each.
5. **The worse room validation score after refitting** comes from 196 rows with light on: in
   training, the merged rows with light on were 98% occupied. This accounts for the observed change
   to four decimal places.
6. **Sparse cells and plug-in bias.** For example, the room training distribution occupies 21 of 32
   cells, and six of them hold at most five rows.
7. **The lower bound from all seven information changes has a closed form**: the largest total
   variation of the changes along a maximal chain of source sets. The proof, exact integer
   certificates and a checker are in [addendum section 2](../research/source-coupling-compression/ADDENDUM-2026-10-30.md).
   It improves the report's lower bound on six office distributions; for office validation it rises
   from 0.4024 to 0.4346 nats.
8. **The saved records hold a third upper bound**, `continuity_upper_interval`. It is never discussed
   and lies between 49.3 and 270.3 nats on the distributions with movement, so it is uninformative.
9. **The SxPID3 qualification corpus never has full support.** Its count tables have at most five
   rows, but full support of three binary sources and a binary target needs 16 rows.
10. **Numerical evidence on the binary constant.** A differential-evolution search over four-label
    targets, run at several fixed values of $H(C)$, found no ratio $D/H(C)$ above 3. The largest
    ratio rose as $H(C)$ fell (from 2.21 at $H(C)=0.6$ to 2.72 at $H(C)=0.005$), and the best
    distributions had the rare exclusive-or form. Along that family the ratio is 2.58, 2.77, 2.84 and
    2.88 for departure probabilities $10^{-2}$, $10^{-4}$, $10^{-6}$ and $10^{-8}$. This supports the
    conjecture $K_\star=3$, approached only as $H(C)\to0$; it does not prove it.

## 4. The further assessment

| Item | Verdict |
|---|---|
| Confirmation of the review's main results | Correct. |
| M1: under deterministic recoding the target-free costs $a_\beta$ vanish | Wrong as first stated, and corrected in the same text: the code maps the pair $(S_2,S_3)$ jointly, so $H(S'_B\mid S_B)>0$ for source sets that split the pair. The remaining remarks repeat $V_{\{1\}}=0$, which the report already uses, or are not derived. |
| M2: a third, unexamined bound is computed by the runner | Correct (item 8 above). Its claimed tightening of an earlier local note was not checked here. |
| M3: shift, and smoothing pollution in the room data | Correct for the room data. Wrong for office validation, where three pairs occur and the merge is not one-to-one; zero information loss there has the reason given in item 2. Its suggested Laplace-smoothing cause for the office test scores does not hold, because every office context has at least 144 training rows. |
| M4: other packages were not reviewed | Outside the review's stated scope; not a defect of the review. |
| M5: nonnegative component atoms constrain the atom changes | Correct. The lower side gave nothing beyond the closed form above. The upper side lies below the range bound on all 30 distributions; on the 21 with movement it is lower by 0.5% to 40%; see [addendum section 3](../research/source-coupling-compression/ADDENDUM-2026-10-30.md). |
| M6: cancellation in the angular evaluator | The advice is correct: evaluate $J_M(a,b)-J_M(a,0)$ from its positive series. One wording is wrong: the linear terms of $2R(1/2)-R(2/3)$ do not cancel; they combine to $a^2/6$, and with the logarithmic terms the leading term is $11a^2/72$, as the assessment itself computes. |

## 5. Changes made in the repository

- `audit/research/source-coupling-compression/verification/run_study_v3.py` finds the raw data
  under the repository root and accepts `--raw-dir`. A replay from the pinned raw files reproduces
  all 121 published campaign files byte for byte in ordinary and optimized Python; only the timing
  file differs.
- `.../verification/post_study_bound.py` checks the published input manifest
  `POST_BOUND_INPUTS.json`, reads the published campaign and writes to a new directory. Its replay
  reproduces `evidence/coupling-bound.json` byte for byte in both modes.
- New: `.../verification/chain_lower_certificate.py` (exact certificates for the closed-form lower
  bound), `.../verification/component-sandwich-exploratory.py.txt` and
  `.../ADDENDUM-2026-10-30.md`.
- The binary allocation note gains a dated section with the four-label reduction and the numerical
  search.
- The report's Markdown and PDF are unchanged. Its status sentence (F3) and the addendum join the
  report when it is republished with a new visual review.

## 6. Limits

This record is AI-agent work. Its arithmetic checks are exact where stated and binary64 elsewhere;
the optimization results are not certificates. It gives no formal proof, no population or
calibration statement and no claim of priority.
