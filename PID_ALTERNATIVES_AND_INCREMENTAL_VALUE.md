# Shared-exclusions PID in analysis, learning and sensor selection

Categorical Makkeh–Gutknecht–Wibral (MGW) PID describes a signed allocation of information under a specified joint law. It can help explain an interaction. A large synergy value alone does not establish that another sensor improves prediction, that a representation is useful, or that an action is worth its cost. The practical solution is to separate the allocation question from the decision objective, then test whether the allocation improves the decision.

This note uses the categorical shared-exclusions functional of Makkeh, Gutknecht and Wibral, version 5, with natural logarithms.[^mgw] Its [exact finite example](audit/evidence/mgw-fixed-world-added-information-2026-09-09.md) has retained [21-target Lean evidence](audit/formal/lean-mgw-fixed-world/PUBLICATION.md). The broader identities below have written derivations; their general Lean proofs remain open. Classical log-loss and information identities are not new PID methods. Proposed selection and learning procedures are not measured improvements.

## One exact comparison and its mechanism

Let $A,B,U$ be independent fair bits on the eight equally likely outcomes. The target is $Y=(A,B)$, the existing source is $A$, and the added source $C$ is either $U$ or $B$. The target, baseline and world remain fixed. Define $L=\log2$ and $r=\log(4/3)$, both in nats.

At a supported observation $(a,c,y)$, categorical MGW redundancy uses the source-match event $E=\{A=a\}\cup\{C=c\}$. Its local net value is

$$
i_\cap^{\rm sx}(y;a,c)
=\log\frac{P(E\cap\{Y=y\})}{P(E)P(Y=y)}.
$$

For both candidates, $P(E)=1/2+1/2-1/4=3/4$. The target match fixes $A=a$, so the target event is already inside $E$. The ratio is therefore 4/3. This statement concerns events on the common world; inconsistent source/target keys in the ambient product alphabet have zero probability. The average redundancy is $r$ because all supported local values equal $r$ and their probabilities sum to one.

Write $R$ for averaged redundancy, $U_A$ for unique baseline information, $U_C$ for unique added-source information, and $S$ for synergy. The two-source reconstruction gives

$$
U_A=I(A;Y)-R,\quad U_C=I(C;Y)-R,
\quad S=I(A,C;Y)-I(A;Y)-I(C;Y)+R.
$$

The MI triples $(I(A;Y),I(C;Y),I(A,C;Y))$ are $(L,0,L)$ for $U$ and $(L,L,2L)$ for $B$. Substitution gives:

| Added source | Redundancy $R$ | Unique added source $U_C$ | Synergy $S$ | Added CMI |
|---|---:|---:|---:|---:|
| Independent $U$ | $r$ | $-r$ | $r$ | $0$ |
| Missing target bit $B$ | $r$ | $L-r$ | $r$ | $L$ |

Subtracting the baseline reconstruction from the joint reconstruction proves

$$
I(C;Y\mid A)=I(A,C;Y)-I(A;Y)=U_C+S.
$$

The independent bit's negative unique contribution cancels its positive synergy. Clamping the unique contribution changes the quantity and breaks this identity. Negative unique information here is a signed MGW allocation; it does not establish a broken instrument or a harmful causal effect.

The full probability construction, all event counts, direct conditional-probability calculation and exact formal scope belong to the [retained finite comparison](audit/evidence/mgw-fixed-world-added-information-2026-09-09.md). The other atom values above follow the displayed subtractions; they are not additional named targets in its 21-target roster. Published MGW already includes signed cancellation. Scientific priority for the matched construction is not established.

## Why the obstruction can persist as a sensor improves

The retained hand derivation extends the example beyond two isolated choices. A real-valued channel parameter does not make these categorical variables continuous. Let $A,B$ be independent fair bits, let $N$ be an independent Bernoulli variable with parameter $e$, and set $C_e=B\mathbin{\mathrm{XOR}}N$. Initially take $0\le e\le1/2$, so larger $e$ means more corruption. The exact joint law on consistent keys is

$$
P(A=a,C_e=c,Y=(a,b))=
\begin{cases}(1-e)/4,&c=b,\\e/4,&c\ne b.\end{cases}
$$

All other ambient keys have mass zero. Four cells of each kind give total mass $4(1-e)/4+4e/4=1$. The source pair $(A,C_e)$ remains independent and uniform for every $e$. Its source-match union still has mass 3/4. On each supported key the added-source and joint-source MI log arguments are $2k$ and $4k$, where $k$ is $1-e$ or $e$; the baseline argument is $2$. Thus their difference cancels in synergy:

$$
S_e=\log(4k)-\log2-\log(2k)+r=r.
$$

At $e=0$, the unequal cells are omitted; this formula never evaluates $\log0$. Directly averaging the added-information log ratios gives

$$
J_e=(1-e)\log[2(1-e)]+e\log(2e)=\log2-h(e),
$$

where $h(e)=-(1-e)\log(1-e)-e\log e$ and a zero-weight entropy term is zero. Therefore $J_0=\log2$, $J_{1/2}=0$, and $U_C=J_e-r$. Synergy remains constant across this change in available information. Under the known binary channel, the best classification error for the missing bit is $e$; the best log loss is $h(e)$.

This also identifies a learning failure condition. Any objective consisting only of this exact synergy is constant along the specified channel family. Where a parameter derivative exists, that derivative is zero. Adding only an acquisition-cost penalty ranks these candidates by cost, while leaving equal-cost quality differences unresolved. A noisy estimated gradient may vary; the population result does not identify that variation as useful signal.

The retained general calculation needs neither uniform nor independent sources. Let the full joint law of $(A,C,Y)$ be a normalized PMF on finite alphabets. Write $q(a,c)=P(A=a,C=c)$ and let $p_A,p_C$ be its marginals. Suppose $A$ is a deterministic function of $Y$ almost surely. At a supported source pair define

$$
d(a,c)=p_A(a)+p_C(c)-q(a,c).
$$

The union contains the target event up to a null set, and $0<d(a,c)\le1$. Hence

$$
R=-\sum_{q(a,c)>0}q(a,c)\log d(a,c),
\qquad S=R-I(A;C).
$$

To obtain the second equality, use $\mathrm H(A\mid Y)=0$ and $\mathrm H(A,C\mid Y)=\mathrm H(C\mid Y)$. The synergy's MI difference becomes

$$
[H(A,C)-H(C\mid Y)]-H(A)-[H(C)-H(C\mid Y)]
=-I(A;C).
$$

Both $R$ and $S$ are thus determined by the source joint law $q$ within this target-copy setting. This is a specific obstruction, not a statement that MGW synergy is always independent of task information. Source distributions, targets and source grouping must remain explicit when comparing systems. The general result and the channel family remain separate formal obligations; they do not inherit the fixed example's kernel evidence.

## Available information and learned prediction are different quantities

Let $H$ denote all observations available before acquisition, $C$ the candidate observation, and $Y$ a finite target. All expressions in this section refer to one fixed finite joint law. An exact law needs no IID sampling assumption. Estimating it from physical records requires a separate sampling model.

For each supported context $h$, a normalized predictor $f_0(y\mid h)$ must be positive wherever the true conditional probability $p(y\mid h)$ is positive. Expanding a logarithm gives

$$
\sum_y p(y\mid h)[-\log f_0(y\mid h)]
=H(p(\cdot\mid h))+D_{\rm KL}(p(\cdot\mid h)\Vert f_0(\cdot\mid h)).
$$

Only positive true masses contribute. The KL term is nonnegative: $-\log x\ge1-x$ for $x>0$ gives a lower bound 1 minus the predictor mass assigned to the true support, which is nonnegative. Equality is attained by the true conditional law. A zero prediction at positive true mass has infinite loss, not zero loss. These are classical properties of logarithmic scoring.[^scoring]

Average over $h$ and apply the same argument to $f_1(y\mid h,c)$. Define $D_0$ and $D_1$ as their respective expected conditional KL discrepancies. The difference in expected losses is exactly

$$
G:=E[-\log f_0(Y\mid H)]-E[-\log f_1(Y\mid H,C)]
=I(C;Y\mid H)+D_0-D_1.
$$

Three conclusions follow. With unrestricted Bayes predictors, $D_0=D_1=0$ and the best log-loss improvement equals CMI. With fitted predictors, $G$ also depends on their errors. A positive CMI can coexist with negative $G$ when the augmented predictor's extra error exceeds the available gain. Finally, $G$ is not a calibrated CMI estimate merely because it comes from two trained classifiers.

This relationship already underlies established acquisition methods. Covert et al. derive greedy conditional-information selection through one-step prediction loss, under Bayes prediction and restrictions on what the selector observes; their learned optimum also requires suitable model classes and optimization.[^dfs] Rewriting CMI as a PID sum does not create a distinct acquisition rule or a new optimality theorem.

## The recorded office example shows both distinctions

The [retained Rust example](audit/evidence/real-occupancy-sensors-example-2026-09-08.md) uses light in lux and CO₂ in ppm, each mapped to four equal-width bins fitted only on 8,143 training rows. The target is the original binary occupancy label. UCI describes minute-scale time-series measurements and photograph-derived occupancy labels.[^occupancy] The nominal joint alphabet has 32 cells. In the later 9,752-row recording only 16 cells are occupied, four have fewer than five rows, and the minimum positive count is one. These are observed input statistics, not population support or effective sample-size guarantees.

The later recording's descriptive empirical values are:

| Quantity | Value |
|---|---:|
| Unique CO₂ contribution | -0.178691053 nats |
| MGW synergy | 0.180249065 nats |
| Added empirical CMI | 0.001558012 nats |
| Light-only predictor log loss | 0.047443 nats per row |
| Light-plus-CO₂ predictor log loss | 0.050762 nats per row |
| Light-only Brier score | 0.011556 |
| Light-plus-CO₂ Brier score | 0.011683 |

Values are rounded here; the [retained JSON](audit/evidence/real-occupancy-sensors-example-2026-09-08/descriptive-comparisons.json) contains full values, counts and predictor rules. Adding CO₂ corrected four classifications but worsened both probability scores. The positive synergy is nearly cancelled in CMI, and the fitted pair model does not realize even that small empirical information increment as a better log score. The finite cross-entropy identity explains why these observations are compatible. It does not establish population calibration or a causal reason for the model errors.

The [count-based loss decomposition](audit/evidence/occupancy-fixed-predictor-loss-decomposition-2026-09-10.md) reconstructs the original training-only add-one probability predictors and evaluates the two KL terms on each recorded empirical law. It uses exact count ratios until logarithmic evaluation. The values below are in nats per row; $G$ is baseline loss minus augmented loss.

| Recording | Rows | Added CMI | Baseline KL $D_0$ | Augmented KL $D_1$ | Gain $G$ |
|---|---:|---:|---:|---:|---:|
| Training | 8,143 | 0.004951869 | 0.000126287 | 0.000441196 | 0.004636960 |
| Earlier evaluation | 2,665 | 0.008709839 | 0.010744807 | 0.011425755 | 0.008028892 |
| Later evaluation | 9,752 | 0.001558012 | 0.014359564 | 0.019236545 | −0.003318968 |

On the later law, conditional entropy falls from $0.033083487$ to $0.031525474$ nats, while predictor KL discrepancy rises by $0.004876981$ nats. Consequently,

$$
G=0.001558012+0.014359564-0.019236545
\mathrel{\approx}-0.003318968\text{ nats}.
$$

This quantifies the mismatch between available information and the predictions actually made. It does not identify whether model class, sample size, distribution change or another mechanism caused that mismatch. All 19 reconstruction and historical-value comparisons are within the fixed $10^{-12}$-nat fixture tolerance; the largest residual is $1.53\times10^{-15}$ nats. The tolerance is not a proved floating-point error bound. Historical training predictor losses were absent and are not claimed as independently compared. No predictor was refitted for this calculation. All three recordings are now exposed development data; another analysis of them cannot be called untouched confirmation.

These records support an analysis of this representation and recording. They do not support removing CO₂ from all occupancy systems, a prospective placement decision, or a significance claim from 9,752 independent trials. The rows are temporally ordered. The example measured no sensor cost and trained no PID-guided learner.

## What to do in an analysis

First specify the target, source groups, time alignment, feature maps and law. Keep the original target meaning: occupancy, future collision, grasp outcome and prediction of another sensor are different questions. Fit preprocessing on training data; state whether the result concerns a fixed empirical PMF or a population estimator.

Report the informative, misinformative and signed net components. For a two-source comparison, show $U_C,S$ and their sum beside directly calculated CMI from the same law. A mismatch beyond the declared numerical error calls for a definition or implementation check. Agreement establishes reconstruction for that calculation, not estimator calibration.

Use the signed allocation to formulate a specific scientific question, such as which observed combinations create informative and misinformative contributions under the named event definition. Compare the conclusion with CMI, fixed-model masking, retrained ablation and an applicable interaction attribution. These comparators ask different questions. A negative unique atom cannot by itself label an observation wrong; a large synergy cannot by itself label a sensor necessary.

For three or four original source groups, retain the full named lattice and its grouping. CMI for adding one source to a baseline tuple remains a Shannon quantity. A separate two-source PID between that tuple and the new source is a different grouping; its atoms must not be presented as unchanged atoms of the original multivariate lattice without a proved mapping.

## What to optimize for a fixed sensor choice

Let a candidate package $d$ supply $C_d$ at cost $k(d)$. Assume all candidates share the same target and pre-acquisition information law, and that acquisition does not change that target. For a declared loss $\ell$, compatible decision classes in which the augmented rule can ignore the new observation, and finite Bayes risks, define its decision value by

$$
V_\ell(d)=\inf_f E[\ell(Y,f(H))]
-\inf_g E[\ell(Y,g(H,C_d))]-\lambda k(d).
$$

The coefficient $\lambda\ge0$ converts nonnegative acquisition cost to the units of the chosen loss; it needs an explicit decision meaning. For log loss with unrestricted correct predictors this becomes $I(C_d;Y\mid H)-\lambda k(d)$. For a real fitted system, evaluate its held-out loss difference and cost. Include the option to acquire nothing. An estimated PID sum alone supplies neither acquisition costs nor unobserved sensor outcomes.

With only two to four fixed, available sensor packages there are at most 16 subsets, including the empty set. If fitting and evaluating those subsets is affordable, compare them directly before training an RL policy. Count physical packages separately from candidate locations: four installed cameras selected from hundreds of poses do not give only 16 placement choices. Finite source count also does not bound the joint feature alphabet.

CMI does not replace every task loss. For example, set $Y=B$ for a fair bit $B$ and take the baseline to be constant. Let a reveal indicator, independent of $B$, equal one with probability $3/5$. The first sensor reveals $B$ when the indicator is one and otherwise reports an explicit erasure. Its CMI is $(3/5)\log2$ and its optimal classification error is $1/5$. The second sensor flips $B$ with independent Bernoulli noise of parameter $1/10$. Its CMI is $\log2-h(1/10)$ and its optimal classification error is $1/10$. The erasure channel has more information but worse classification error. Indeed $h(1/10)>(2/5)\log2$ is equivalent to $10^{10}>16\cdot9^9$. This is a finite written counterexample, not a new formally checked target. Select the actual loss before ranking candidates.

## What to do in representation learning

Keep task loss and resource constraints as the primary measured objectives. Use MGW diagnostics on frozen representations to investigate a declared interaction question. Then compare the same learner with and without a proposed PID feature or regularizer, at matched data access, model capacity and tuning cost. A useful hypothesis is that the signed vector helps a gating model cope with specified sensor failures beyond what task training and CMI features achieve. It remains a hypothesis until that comparison succeeds on untouched episodes or environments.

Keep the baseline representation fixed or separately constrain its predictive quality. Suppose both raw sources equal a fair target $Y$. With encoded baseline $H=Y$ and candidate $C=Y$, additional CMI is zero. A trainable baseline encoder can instead output a constant: CMI rises to $\log2$, although the pair already predicted $Y$ perfectly. The gain objective has rewarded damaging the baseline. A primary joint task loss and an explicit baseline-quality constraint distinguish that change from improving the candidate.

An arbitrary synergy weight also changes the objective. For the same two-source law,

$$
U_C+\beta S=I(C;Y\mid H)+(\beta-1)S.
$$

Here $\beta$ is an atom weight, separate from the cost conversion $\lambda$. Only $\beta=1$ preserves the information increment identically. In the independent-$U$ example, $\beta>1$ gives a positive score $(\beta-1)r$ despite zero added information; $\beta<1$ gives a negative score. A deliberately different utility may use such a weight, but its interpretation and benefit need separate evidence.

Do not infer a usable gradient through empirical binning from differentiability of a probability functional. Hard category assignments can remain constant as an encoder parameter changes and jump at a bin boundary. A soft probability model defines its own law and fitting objective; its derivative needs an explicit path from parameters to that law. Changing the target or mixing source groups before decomposition changes the estimand. Measure-specific atom values must not silently become physical-sensor attributions.

Use the retained noisy channel as a required negative control for a synergy-only learner. Hold the target, source alphabets, source joint law and cost fixed. The exact synergy reward is flat while optimal task loss changes. If an estimated reward ranks the channels, determine whether sampling error, leakage, altered source laws or another reward term produced the ranking. Do not credit that ranking to the constant population functional.

Independent noise categories with positive probability provide another control. Let $A$ be uniform on $m\ge1$ values, let $Y=(A,B)$ for any finite $B$, and let $C$ be uniform on $n\ge1$ values and independent of the whole target. Then $P(A=a,C=c)=1/(mn)$ and the union mass is $(m+n-1)/(mn)$. The source MI is zero, so the displayed general formula gives $S=\log[mn/(m+n-1)]$. For $m>1$, the ratio increases with $n$: its difference between $n+1$ and $n$ has positive numerator $m(m-1)$. Thus synergy increases even though $I(C;Y\mid A)=0$. Unused labels do not satisfy the uniform positive-mass assumption. Fix representation capacity and test this failure mode before rewarding a rise in synergy during training.

## Sequential acquisition and robotics

A sequential selector must condition on the actual available history, including which sensors were queried, their observations, timing and past actions. A legal selector cannot inspect the target or an unacquired sensor. If action $D$ is randomized only from the recorded history $H$, with independent randomization, then $D$ carries no extra target information conditional on $H$. The value of its next observation must still be computed under the corresponding conditional observation law. Hidden selection inputs invalidate that simplification.

Pointwise PID has an additional data requirement: its argument includes the realized target and candidate reading. It can be evaluated after a labelled event for analysis or training diagnostics. It cannot be supplied to a deployed pre-acquisition gate when either value is unknown. A legal feature may instead summarize training data or integrate over a declared predictive observation model. Such a model-based feature has its own estimation error; it is not an observed exact PID value.

Two conditional operations must be kept distinct. Fix a finite law $P(H,C,Y)$, and let $u_C^P,s^P$ be its pointwise MGW atoms. For each supported anchor,

$$
u_C^P(h,c,y)+s^P(h,c,y)
=\log\frac{P(y\mid h,c)}{P(y\mid h)}.
$$

This follows by cancelling the redundancy terms and subtracting the baseline local MI from the joint local MI. For a history value with $P(H=h)>0$, average these already-defined functions:

$$
E_P[u_C^P+s^P\mid H=h]
=\sum_{c,y:P(c,y\mid h)>0}P(c,y\mid h)
\log\frac{P(y\mid h,c)}{P(y\mid h)}
=I_P(C;Y\mid H=h).
$$

Computing a new PID under the conditional law $P_h=P(\cdot\mid H=h)$ is different. In that law the baseline source is constant. Its matching event has probability one, so redundancy is zero; baseline MI is zero and joint MI equals candidate MI, so synergy is also zero. The candidate's averaged unique term equals the same conditional MI, but the allocation has changed. For the fair-bit completing sensor, the original-law conditional mean synergy is $r$, while the recomputed conditional-law synergy is zero. Neither operation licenses access to the unknown target or candidate. A prospective score must integrate both out under the selected model and retain which operation it used.

A greedy CMI rule optimizes a one-step information increment under its premises. It is not automatically optimal over a sensing budget. For independent fair $A,B$ and target $A\mathbin{\mathrm{XOR}}B$, either single observation has zero MI, while the pair has $\log2$. Stopping whenever a single observation has zero gain misses the informative pair. Small subset enumeration or lookahead addresses this example; a general approximation guarantee needs additional assumptions.

Use a learned acquisition policy when history and action spaces justify it. Compare with direct task-loss acquisition and an applicable information-design method. Deep Adaptive Design is an established model-based sequential design comparator; Gaussian-process sensor placement supplies a different model and objective.[^dad][^gp] Their results do not prove a guarantee for an MGW reward.

For passive sensing, the target may remain fixed while observations accumulate. Moving a camera, touching an object or taking a robot action can instead change the observation process or the task outcome. A world/action model must specify those transitions and observation laws. Observational CMI cannot identify unobserved intervention outcomes. A VLA or world-action model can be evaluated as a predictor or controller in that experiment; its name supplies no calibration or PID benefit.

## Continuous observations and large representations

The finite results above apply to categorical MGW, including declared quantized estimands. They do not establish the corresponding statements for the continuous shared-exclusions functional of Ehrlich et al., which uses a different density construction and relative source scales.[^ehrlich] The retained office example's binary occupancy target is outside pid-rs's current purely continuous support contract. Adding noise would change its observation model.

For continuous or hyperbolic representations, specify support, source dimensions, coordinate gauge, dependence, moment or information-finiteness premises, and estimator conditions separately. A learned low-dimensional codebook can make a categorical calculation feasible, but changes the estimand and can discard useful information. Two to four high-dimensional sources can still yield an enormous joint alphabet or unreliable neighbor geometry. No theorem here removes that problem.

## An optional bound for a fixed decision comparison

This classical bound concerns fitted prediction loss, not PID-estimator calibration. Fix $K\ge1$ predictor pairs before observing $n\ge1$ independent, identically distributed validation episodes, independently of the data used to fit or select those pairs. For a finite target with $m\ge1$ labels, require normalized predictive PMFs with every label probability at least $\epsilon$, where $0<\epsilon\le1/m$. Define $b=\log(1/\epsilon)$.

Each log loss lies in $[0,b]$. For candidate $j$ and episode $i$, let $D_{ij}$ be the baseline-minus-augmented loss, averaged within that nonempty episode. Then $D_{ij}\in[-b,b]$, even when frames inside the episode are dependent. Define $G_j=E[D_{ij}]$ and $\widehat G_j=n^{-1}\sum_iD_{ij}$. The estimand weights episodes equally; it is not automatically pooled per-frame risk when episode lengths differ.

When $b>0$ and $t>0$, Hoeffding's bound for range length $2b$, followed by a union bound over the fixed $K$ pairs, gives

$$
P\!\left(\max_{1\le j\le K}|\widehat G_j-G_j|>t\right)
\le 2K\exp\!\left(-\frac{nt^2}{2b^2}\right).
$$

Thus, for $0<\delta<1$ and $b>0$, a simultaneous radius is

$$
t=b\sqrt{\frac{2\log(2K/\delta)}n}.
$$

If $b=0$, all allowed losses and gains are zero, and the zero-radius conclusion holds directly. Correlation between candidates on the same episode does not invalidate the union bound. Independence of episodes remains necessary for this stated Hoeffding application.[^hoeffding]

For fixed known costs, a positive lower bound $\widehat G_j-t-\lambda k(j)$ supports a positive expected net gain under these premises. New adaptive encoder, model or parameter searches are not covered by a smaller reported $K$. A probability floor changes the predictor; it must preserve normalization and be fitted or fixed before evaluation. These bounds may be too loose to resolve small effects. The office recordings do not supply $9,752$ independent episodes, so their row count cannot be inserted into this formula. This is a written specialization of a classical result; a corresponding Lean statistical theorem remains open.

## Comparison methods and acceptance protocol

The following survey was recorded on 5 September 2026. It names alternatives to test, not a completed performance ranking. The practical derivations above were revised on 10 September 2026.

### Named recent methods

These are candidates for an applicable comparison. They are not all implementations of the same task or the same PID.

| Method and source | What it contributes | Fair comparison with pid-rs |
|---|---|---|
| **CoMM**, Dufumier et al., ICLR 2025, [What to align in multimodal contrastive learning?](https://proceedings.iclr.cc/paper_files/paper/2025/hash/108030643e640ac050e0ed5e6aace48f-Abstract-Conference.html) | Learns fused representations through contrastive training. The paper reports strong results on seven multimodal tasks. Its theoretical analysis assumes suitable minimal label-preserving multimodal augmentations. | Compare downstream performance and representation quality under matched data and training budgets. CoMM is a learner; a computed MGW atom vector is not a replacement predictor. Its interaction analysis does not establish MGW source correspondence. |
| **I²MoE**, Xin et al., ICML 2025, [Interpretable Multimodal Interaction-aware Mixture-of-Experts](https://proceedings.mlr.press/v267/xin25c.html) | Uses interaction experts, weakly supervised interaction losses and a reweighting model for prediction and local/global interpretation. | This is a direct competitor to a claim of useful interaction explanations. Compare the registered explanation question as well as task loss. Expert weights are not automatically exact MGW information atoms. |
| **RollingQ**, Ni et al., ICML 2025, [Reviving the Cooperation Dynamics in Multimodal Transformer](https://proceedings.mlr.press/v267/ni25a.html) | Changes attention queries to address modality preference that can suppress adaptive fusion. | A candidate predictive baseline where modality quality varies. Compare to the complete trained method, including training cost. Attention allocation and PID allocation have different definitions. |
| **CVX and BATCH**, Liang et al., NeurIPS 2023, [Quantifying & Modeling Multimodal Interactions](https://proceedings.neurips.cc/paper_files/paper/2023/hash/575286a73f238b6516ce0467d67eadb2-Abstract-Conference.html) | Computes or approximates a two-source PID defined through the Bertschinger et al. coupling optimization. The paper reports multimodal dataset, model and model-selection studies. | Essential prior work for claims that PID helps multimodal analysis. This is the BROJA family, not MGW shared exclusions. CVX's mathematical optimization target does not imply exact floating-point solutions; BATCH adds learned approximations. Compare functional sensitivity and useful conclusions, not atom error against an MGW answer. |

These papers already study multimodal interactions. Thus, “we analyze redundancy, uniqueness and synergy” is not a sufficient novelty claim. The contribution must name a new result, implementation guarantee, computational improvement or demonstrated scientific use that survives comparison.

MultiBench provides a published evaluation framework for generalization, resource cost and noisy or missing modalities ([Liang et al., 2021](https://arxiv.org/abs/2107.07502)). [MULTIBENCH++, AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/39963) extends the available multimodal benchmark options. Select compatible tasks and freeze the data, model and code versions before a local study. A benchmark suite is evaluation infrastructure, not a competing fusion estimator. Neither suite by itself validates the Crebain observation model.

### Established alternatives and complementary tools

Recent models do not remove the need for strong simple baselines.

- **Joint MI and conditional MI:** measure total target information and the increment from another source. Under one fixed exact law, conditional MI is the chain-rule increment of joint MI. Do not count those two descriptions of the same greedy rule as independent victories.
- **Fixed-model and retrained ablation:** measure sensitivity of one model and the performance recoverable after removing an input. Report them separately; masking can create unfamiliar inputs, while retraining changes the model.
- **Shapley–Taylor interaction attribution:** allocates effects to interactions up to a specified order for a declared coalition function. It is a genuine interaction-analysis comparator, not merely an individual-feature ranking. Freeze its order, background law and coalition evaluation convention. Its set-function semantics differ from the MGW event lattice ([Sundararajan et al., 2020](https://proceedings.mlr.press/v119/sundararajan20a.html)).
- **Bayesian expected information gain and Gaussian-process design:** directly address data acquisition under a specified probabilistic model. Deep Adaptive Design amortizes sequential design computation ([Foster et al., 2021](https://proceedings.mlr.press/v139/foster21a.html)). The classical Gaussian-process placement result uses its own objective and approximation premises; it is not a guarantee for a PID objective ([Krause et al., 2008](https://www.jmlr.org/papers/v9/krause08a.html)). These are established comparators, not claims about the latest best method on every design problem.
- **Williams–Beer $I_{\min}$ and BROJA:** test sensitivity to the definition of redundancy or uniqueness. BROJA fixes the source–target marginals and optimizes over compatible couplings ([Bertschinger et al., 2014](https://doi.org/10.3390/e16042161)). Different definitions can correctly give different answers on the same law.

### What PID can add

A named PID separates contributions that a single total-information or co-information value leaves combined. For any two-source decomposition satisfying the usual reconstruction identities, conditional MI combines the corresponding unique contribution and synergy. A PID provides a definition-specific allocation of that combined amount; it does not create more predictive information in the observed variables. The [existing algebra and functional discussion](PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md) states the equations and sign convention.

The distinction matters in examples. For independent fair bits $A,B$ and $T=A\mathbin{\mathrm{XOR}}B$, the total information is $\ln 2$. BROJA assigns zero redundancy and unique information, and synergy $\ln 2$. Categorical MGW assigns redundancy $\ln(2/3)$, each unique atom $\ln(3/2)$ and synergy $\ln(4/3)$. Both reconstruct the same total. The MGW definition conditions on the inclusive source-equality event; BROJA optimizes a different object. The published examples and their definitions, rather than a generic word such as “synergy,” determine these values ([MGW, 2021](https://arxiv.org/html/2002.03356v5), [Bertschinger et al., 2014](https://doi.org/10.3390/e16042161)).

Three kinds of additional value deserve separate evaluation:

1. **Scientific explanation.** Does the named allocation answer a predeclared question that MI/CMI, ablation and an applicable interaction attribution leave unresolved? A different number is insufficient; record the conclusion it changes and the evidence supporting that conclusion.
2. **Reliable computation.** Can the same finite-law MGW result be computed with a proved error bound, fewer resources or a detectable implementation error? Compare with the direct calculation on the same law. A bound is useful even without improved classification, but runtime and numerical claims still need their own evidence.
3. **Predictive or decision benefit.** Does adding a fixed PID-derived diagnostic or selection rule improve the registered downstream criterion on untouched data? Compare the same base model with and without that addition. The base learner's success cannot be credited to a diagnostic computed afterward.

Any proposed bounded or randomized MGW calculation must establish correspondence with the named functional and compare against direct evaluation of the same law. An exact mathematical construction alone does not establish a runtime gain or calibrate a population estimator.

### A comparison that can reject PID

Before examining final results, select the applicable methods and fix the data version, labels, source groups, observation model, sampling unit, splits, preprocessing, training budget, evaluation metrics, numerical margins and stopping rule. This note does not supply a preregistered benchmark. The repository's [research workflow](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md) defines the required candidate and judge separation.

Report two panels: compatible methods on the same frozen representation, and each method with its appropriate representation under equal nested tuning resources. The first isolates objective choice; the second tests practical end-to-end performance. A continuous method must not be forced through coarse bins merely to help categorical PID. Repeated frames from one recording must not be counted as independent test episodes. Quantization, missingness and changing support need explicit treatment.

Retain every registered outcome, including no advantage, unstable conclusions across PID definitions, failures on sparse alphabets and cases where a simpler method wins. Prefer the alternative if it answers the question with equal or better evidence and lower cost. For Crebain and Galadriel, current bounded offline conformance fixtures establish neither field performance nor a PID advantage over these methods.

## Follow-up work and acceptance conditions

| Work | Concrete next step | Evidence needed to accept it |
|---|---|---|
| Preserve the fixed comparison | Keep its complete proof, source map, PDF and failed controls linked | Exact committed artifacts and required replay/integration evidence |
| Close the general channel result | Reuse the retained finite-law interface; prove actual pushforward/event and support identities before the atom formula | Exact theorem types, kernel-checked proofs and admitted controls; no free cumulative hypotheses |
| Explain fitted-model failures | Completed for the three retained occupancy recordings; extend only under a new declared study | [Counts-based loss decomposition](audit/evidence/occupancy-fixed-predictor-loss-decomposition-2026-09-10.md); no population claim |
| Static two-to-four-sensor study | Compare affordable subsets on fixed features and on appropriately fitted alternatives | Same episode splits, target, cost and tuning budget; signed PID, CMI and chosen task losses |
| PID-assisted learning | Add the signed diagnostic only as a separately tested component | Improvement beyond task-only and CMI-assisted controls, with failed outcomes retained |
| Sequential study | Specify history, feasible actions, observation/transition law and total budget | Compare lookahead/design and policy baselines; evaluate complete trajectories |
| Uncertainty | Declare independent sampling units or a justified dependence model | A bound or calibration result for that exact procedure; frame count alone is insufficient |

The main negative findings are constructive: synergy alone can be insensitive to useful channel changes; CMI need not rank a different task loss; fitted models need not realize available information; greedy acquisition can miss complementary pairs; and selection or preprocessing can change the scientific object. Each failure points to a specific correction and a test that can reject the proposed use of PID.

[^mgw]: Makkeh, Gutknecht and Wibral. *Introducing a differentiable measure of pointwise shared information*. arXiv:2002.03356v5, 2021; Physical Review E 103, 032149. [Version 5](https://arxiv.org/html/2002.03356v5). Shared-exclusions definition and neural goal-function discussion; no new learning benefit is inferred here.
[^scoring]: Gneiting and Raftery. *Strictly Proper Scoring Rules, Prediction, and Estimation*. JASA 102(477), 359–378, 2007, Example 3. [Author-hosted paper](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf). Logarithmic scoring, Shannon entropy and KL divergence.
[^dfs]: Covert et al. *Learning to Maximize Mutual Information for Dynamic Feature Selection*. ICML 2023, Sections 3–4, Propositions 1–2 and Theorem 1. [Proceedings paper](https://proceedings.mlr.press/v202/covert23a/covert23a.pdf). This is prior conditional-information acquisition work, not a MGW method.
[^occupancy]: Candanedo. *Occupancy Detection*, UCI Machine Learning Repository, 2016. [DOI 10.24432/C5X01N](https://doi.org/10.24432/C5X01N). The dataset is licensed under CC BY 4.0. All displayed results concern the repository's stated fitted transformations and retained records.
[^dad]: Foster, Ivanova, Malik and Rainforth. *Deep Adaptive Design: Amortizing Sequential Bayesian Experimental Design*. ICML 2021. [Proceedings paper](https://proceedings.mlr.press/v139/foster21a/foster21a.pdf).
[^gp]: Krause, Singh and Guestrin. *Near-Optimal Sensor Placements in Gaussian Processes: Theory, Efficient Algorithms and Empirical Studies*. JMLR 9, 235–284, 2008. [Paper](https://www.jmlr.org/papers/volume9/krause08a/krause08a.pdf).
[^ehrlich]: Ehrlich et al. *Partial Information Decomposition for Continuous Variables based on Shared Exclusions: Analytical Formulation and Estimation*. arXiv:2311.06373v3; Physical Review E 110, 014115, 2024. [Version 3](https://arxiv.org/html/2311.06373v3). Relative-scale and support assumptions remain separate from categorical MGW.
[^hoeffding]: Hoeffding. *Probability Inequalities for Sums of Bounded Random Variables*. JASA 58(301), 13–30, 1963. [DOI 10.1080/01621459.1963.10500830](https://doi.org/10.1080/01621459.1963.10500830). Independent bounded-variable concentration; no PID calibration theorem is claimed.
