# Coverage of a bootstrap percentile range on a four-row copy law

**Sepehr Mahmoudian** · 18 November 2026

## Research question

How often does the raw percentile range returned by the pid-rs block bootstrap contain the population redundancy when both categorical sources are exact copies of the target? On this law, with four independent rows and a fixed seed, **the range covers with probability 64/81 (79.01%)**. Both constant samples miss. Every nonconstant sample covers and every requested computation returns a finite value.

The distinction matters when reading a report labelled with a nominal 95% level. The parameter selects two ranks among bootstrap replicates. Actual coverage concerns repeated draws of the **original** four rows. Here those draws can be enumerated completely. A constant-sample argument already gave the upper bound 64/81 before execution. The new observation establishes that the implementation at the specified source revision attains that bound for Seed 7. [Recorded observation and verification](audit/evidence/finite-copy-bootstrap-coverage/README.md)

## Variables and definitions

The **sources** are two readings of the same binary label. The **target** is that label too. The **copy law** draws one label independently for each row, with probability one third of label one. The eight possible triples of binary labels include two occupied triples, all zeros and all ones. Observed rows supply the empirical probability mass function directly.

**Shared redundancy** is the average signed shared-exclusion information the two source events supply about the target. On this law, observing either source reveals the target exactly. **Entropy** is the expected negative natural logarithm of the label probability. Natural logarithms give information in **nats**. **Coverage** is the probability, over original samples from the copy law, that the returned closed range contains the exact population redundancy. [Makkeh, Gutknecht and Wibral, Section II, equations (1)–(3)](https://arxiv.org/html/2002.03356v5#S2)

In the equations below, $p$ is the probability of label one, $H(p)$ its binary entropy, $m$ the integer encoding an ordered sample, $k$ its number of ones, and $B$ the number of bootstrap replicates. A **balanced** replicate has exactly two ones. Its count among the replicates for one mask is $h_m$.

---

## Why two samples must miss

For a binary variable the population target in nats is

$$
H(p)=-p\ln p-(1-p)\ln(1-p),\qquad
H(1/3)=\tfrac13\ln(27/4)\approx0.636514.
$$

At an occupied label, the event “source one has this label or source two has this label” equals the target event. Its conditional target probability is one. The shared-exclusion point value is therefore the negative log of the label probability, and its average is the displayed entropy. Replacing the population law with the four empirical rows gives $H(k/4)$, with $0\ln 0=0$. Ordinary binary entropy thus provides a direct reference for the signed-net redundancy on this particular law.

There are sixteen ordered samples. Row $i$, for $0\leq i<4$, is bit $i$ of mask $m$, with the least significant bit first. Independence gives the probability of that **individual sequence** as

$$
\Pr(m)=(1/3)^k(2/3)^{4-k}=\frac{2^{4-k}}{81}.
$$

The all-zero mask has weight $16/81$ and the all-one mask has weight $1/81$. Resampling either one with replacement always yields a constant sample. Its empirical entropy and both unexpanded raw endpoints are zero. Thus the two constant masks alone contribute $17/81$ missed coverage.

### Which nonconstant samples cover?

For each mask the public algorithm resets Seed 7 and makes $B=200$ replicates of four draws with replacement. Block length one was fixed in advance. It sorts finite returned values using the binary64 total order. The nominal tail parameter is 0.05, represented by `3fa999999999999a` in hexadecimal. The equal-trim rule selects the zero-based order statistics at indices 5 and 194. [Historical percentile implementation](https://github.com/sepahead/pid-rs/blob/1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20/crates/pid-core/src/bootstrap.rs)

The possible exact resample entropies are $0$, $H(1/4)$ and $H(1/2)$. Only the last, produced by two ones, lies above the target. Each gap between the target and its adjacent level exceeds 0.04 nat. Consequently a closed range from ranks 5 and 194 covers exactly when it contains at least six balanced and at least six unbalanced replicates, or $6\le h_m\le194$. The numerical checks below apply this test to the actual binary64 endpoints.

---

## All sixteen outcomes

Complementing every binary label preserves the balanced status of each resample. The table pairs complementary masks for readability. Both members of each pair were run and checked. The two entries in the weight column are numerators over 81, in the same order as the masks.

| Mask pair | Weight numerators | Balanced out of 200 | Contains target? |
|:----------|:------------------|--------------------:|:-----------------|
| 0 and 15 | 16 and 1 | 0 | No |
| 1 and 14 | 8 and 2 | 36 | Yes |
| 2 and 13 | 8 and 2 | 41 | Yes |
| 3 and 12 | 4 and 4 | 69 | Yes |
| 4 and 11 | 8 and 2 | 42 | Yes |
| 5 and 10 | 4 and 4 | 72 | Yes |
| 6 and 9 | 4 and 4 | 73 | Yes |
| 7 and 8 | 2 and 8 | 47 | Yes |

For example, mask 1 encodes rows $(1,0,0,0)$ and has probability $8/81$. Its observed point is about 0.562335 nat. Of its 200 resamples, 36 are balanced. Its returned endpoints are zero and the represented value approximately 0.693147 nat. All fourteen nonconstant masks have this same endpoint pair. Only masks 0 and 15 give $[0,0]$. The exact covered mass is $1-17/81=64/81$ and the typed API failure mass is zero. The unweighted fraction of covered masks, $14/16$, gives the wrong probability for this unequal-mass law.

### Checks on the finite observation

The 3,200 replicate values, 16 point estimates, raw endpoints and separate index-probe output are retained as binary64 bit strings. The verifier reconstructs the 200 four-index tuples from the fixed V1 generator. The index-only oracle also agreed with the published SplitMix C reference. A checker uses rational logarithm enclosures to classify the returned endpoints against the population value. Its population enclosure is narrower than $2^{-160}$ nat and every nonconstant empirical value is within $2^{-48}$ nat of its count-specific exact entropy. A second calculation counts balanced resamples from the decoded indices and reproduces every row decision. Both Python modes used the same stored observation. [Verification package](audit/evidence/finite-copy-bootstrap-coverage/README.md) · [SplitMix reference](https://prng.di.unimi.it/splitmix.c)

---

## Rust implementation and computational cost

The standalone release driver calls `experimental::pipelines::block_bootstrap` with `experimental-pipelines` enabled, default features disabled and an independent-row sampling declaration. Its scalar callback converts four observed labels to a single-column categorical matrix, passes three identical views to `stable::categorical::discrete_sxpid2_averaged` and reads `red.net_nats()`. The reporter retains each indexed success or typed error and the actual optional summary. An additional bootstrap call on the row IDs observes the index schedule. [Exact Rust driver and lock](audit/evidence/finite-copy-bootstrap-coverage/README.md)

There are 16 point estimates and $16\times200$ resample evaluations of categorical redundancy, or 3,216 categorical calls. The index observer is called 201 times. For $n$ rows, block length one and $B$ replicates, the generic wrapper draws and copies $Bn$ indices or values per run, evaluates the callback $B+1$ times and sorts $B$ values in $O(B\log B)$ time. In serial execution the stored schedule uses $O(Bn)$ space plus $O(B)$ outcomes, one resample and the callback's scratch space. This driver also retains all sixteen reports for serialization. Here $n=4$, there are at most two occupied categorical triples, and no fitting or inference model is trained.

One offline release build took 39.92 seconds and the captured program stage took 3.19 seconds on arm64 macOS 26.5.1 with Rust 1.99.1. These wall times include process supervision. They describe one small run. The sampled resource limits were 4 GiB for building and 512 MiB for execution, with a one-MiB stdout limit. An unavailable summary, failed replicate, cancellation or invalid capture withholds a point coverage result. A fresh locked build of the published driver compiled successfully and produced a different executable digest. Checking the archived observation reproduced the original numerical judgment bytes. [Execution record and source identities](audit/evidence/finite-copy-bootstrap-coverage/record.json)

### Scope and citation

Exhaustive enumeration removes Monte Carlo uncertainty over these sixteen outer samples. The result is conditional on this seed, law, sample size, statistic, rank convention and software source. It supplies no frequentist guarantee for dependence, other seeds, continuous estimators or fitted quantization. The percentile summary stays descriptive. The analytical failure bound preceded the registered execution. One AI-assisted wrapper was reviewed and run once. The arithmetic checks share the law, inputs and mathematical reduction. No external human scientific review is claimed.

Cite **Sepehr Mahmoudian (2026), *Coverage of a bootstrap percentile range on a four-row copy law***, with the exact report commit or release. The measured runtime source was `1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20`. Cite the definition and software separately. [Makkeh, Gutknecht and Wibral (2021)](https://doi.org/10.1103/PhysRevE.103.032149) · [Software citation](CITATION.cff) · [PDF](output/pdf/finite-copy-bootstrap-coverage.pdf)
