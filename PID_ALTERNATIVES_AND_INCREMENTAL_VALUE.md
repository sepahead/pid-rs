# PID and competing methods: what must improve

Literature review: 5 September 2026. This note names relevant alternatives and complementary methods. It is a comparison plan, not a completed performance ranking. A paper's reported best result applies to its stated task, data and comparison date. No experiment reported here establishes a pid-rs advantage on a physical sensor system.

## Start with the question

Use a predictive model when the question is whether observations predict a label. Use calibration and proper scoring rules when the quality of predicted probabilities matters. Use Bayesian design when a justified observation model and an expected utility define the experiment. Use an information decomposition when the allocation of target information among specified source groups is itself the question.

For pid-rs, the primary categorical object is the Makkeh–Gutknecht–Wibral (MGW) shared-exclusions functional. It evaluates a specified finite joint law in nats. Its informative and misinformative components have event semantics; their net difference can be negative. Williams–Beer $I_{\min}$, BROJA and continuous Ehrlich shared exclusions are separate objects. The [method catalog](method-catalog.json) records the implemented routes and their assumptions.

The [sensor and Galadriel guide, Section 8](PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md#8-what-pid-adds-beyond-simpler-methods) gives the broader comparator matrix, two required fairness panels and explicit criteria for preferring no PID.

## Named recent methods

These are candidates for an applicable comparison. They are not all implementations of the same task or the same PID.

| Method and source | What it contributes | Fair comparison with pid-rs |
|---|---|---|
| **CoMM**, Dufumier et al., ICLR 2025, [What to align in multimodal contrastive learning?](https://proceedings.iclr.cc/paper_files/paper/2025/hash/108030643e640ac050e0ed5e6aace48f-Abstract-Conference.html) | Learns fused representations through contrastive training. The paper reports strong results on seven multimodal tasks. Its theoretical analysis assumes suitable minimal label-preserving multimodal augmentations. | Compare downstream performance and representation quality under matched data and training budgets. CoMM is a learner; a computed MGW atom vector is not a replacement predictor. Its interaction analysis does not establish MGW source correspondence. |
| **I²MoE**, Xin et al., ICML 2025, [Interpretable Multimodal Interaction-aware Mixture-of-Experts](https://proceedings.mlr.press/v267/xin25c.html) | Uses interaction experts, weakly supervised interaction losses and a reweighting model for prediction and local/global interpretation. | This is a direct competitor to a claim of useful interaction explanations. Compare the registered explanation question as well as task loss. Expert weights are not automatically exact MGW information atoms. |
| **RollingQ**, Ni et al., ICML 2025, [Reviving the Cooperation Dynamics in Multimodal Transformer](https://proceedings.mlr.press/v267/ni25a.html) | Changes attention queries to address modality preference that can suppress adaptive fusion. | A candidate predictive baseline where modality quality varies. Compare to the complete trained method, including training cost. Attention allocation and PID allocation have different definitions. |
| **CVX and BATCH**, Liang et al., NeurIPS 2023, [Quantifying & Modeling Multimodal Interactions](https://proceedings.neurips.cc/paper_files/paper/2023/hash/575286a73f238b6516ce0467d67eadb2-Abstract-Conference.html) | Computes or approximates a two-source PID defined through the Bertschinger et al. coupling optimization. The paper reports multimodal dataset, model and model-selection studies. | Essential prior work for claims that PID helps multimodal analysis. This is the BROJA family, not MGW shared exclusions. CVX's mathematical optimization target does not imply exact floating-point solutions; BATCH adds learned approximations. Compare functional sensitivity and useful conclusions, not atom error against an MGW answer. |

These papers already study multimodal interactions. Thus, “we analyze redundancy, uniqueness and synergy” is not a sufficient novelty claim. The contribution must name a new result, implementation guarantee, computational improvement or demonstrated scientific use that survives comparison.

MultiBench provides a published evaluation framework for generalization, resource cost and noisy or missing modalities ([Liang et al., 2021](https://arxiv.org/abs/2107.07502)). [MULTIBENCH++, AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/39963) extends the available multimodal benchmark options. Select compatible tasks and freeze the data, model and code versions before a local study. A benchmark suite is evaluation infrastructure, not a competing fusion estimator. Neither suite by itself validates the Crebain observation model.

## Established alternatives and complementary tools

Recent models do not remove the need for strong simple baselines.

- **Joint MI and conditional MI:** measure total target information and the increment from another source. Under one fixed exact law, conditional MI is the chain-rule increment of joint MI. Do not count those two descriptions of the same greedy rule as independent victories.
- **Fixed-model and retrained ablation:** measure sensitivity of one model and the performance recoverable after removing an input. Report them separately; masking can create unfamiliar inputs, while retraining changes the model.
- **Shapley–Taylor interaction attribution:** allocates effects to interactions up to a specified order for a declared coalition function. It is a genuine interaction-analysis comparator, not merely an individual-feature ranking. Freeze its order, background law and coalition evaluation convention. Its set-function semantics differ from the MGW event lattice ([Sundararajan et al., 2020](https://proceedings.mlr.press/v119/sundararajan20a.html)).
- **Bayesian expected information gain and Gaussian-process design:** directly address data acquisition under a specified probabilistic model. Deep Adaptive Design amortizes sequential design computation ([Foster et al., 2021](https://proceedings.mlr.press/v139/foster21a.html)). The classical Gaussian-process placement result uses its own objective and approximation premises; it is not a guarantee for a PID objective ([Krause et al., 2008](https://www.jmlr.org/papers/v9/krause08a.html)). These are established comparators, not claims about the latest best method on every design problem.
- **Williams–Beer $I_{\min}$ and BROJA:** test sensitivity to the definition of redundancy or uniqueness. BROJA fixes the source–target marginals and optimizes over compatible couplings ([Bertschinger et al., 2014](https://doi.org/10.3390/e16042161)). Different definitions can correctly give different answers on the same law.

## What PID can add

A named PID separates contributions that a single total-information or co-information value leaves combined. For any two-source decomposition satisfying the usual reconstruction identities, conditional MI combines the corresponding unique contribution and synergy. A PID provides a definition-specific allocation of that combined amount; it does not create more predictive information in the observed variables. The [existing algebra and functional discussion](PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md) states the equations and sign convention.

The distinction matters in examples. For independent fair bits $A,B$ and $T=A\mathbin{\mathrm{XOR}}B$, the total information is $\ln 2$. BROJA assigns zero redundancy and unique information, and synergy $\ln 2$. Categorical MGW assigns redundancy $\ln(2/3)$, each unique atom $\ln(3/2)$ and synergy $\ln(4/3)$. Both reconstruct the same total. The MGW definition conditions on the inclusive source-equality event; BROJA optimizes a different object. The published examples and their definitions, rather than a generic word such as “synergy,” determine these values ([MGW, 2021](https://arxiv.org/html/2002.03356v5), [Bertschinger et al., 2014](https://doi.org/10.3390/e16042161)).

Three kinds of additional value deserve separate evaluation:

1. **Scientific explanation.** Does the named allocation answer a predeclared question that MI/CMI, ablation and an applicable interaction attribution leave unresolved? A different number is insufficient; record the conclusion it changes and the evidence supporting that conclusion.
2. **Reliable computation.** Can the same finite-law MGW result be computed with a proved error bound, fewer resources or a detectable implementation error? Compare with the direct calculation on the same law. A bound is useful even without improved classification, but runtime and numerical claims still need their own evidence.
3. **Predictive or decision benefit.** Does adding a fixed PID-derived diagnostic or selection rule improve the registered downstream criterion on untouched data? Compare the same base model with and without that addition. The base learner's success cannot be credited to a diagnostic computed afterward.

Any proposed bounded or randomized MGW calculation must establish correspondence with the named functional and compare against direct evaluation of the same law. An exact mathematical construction alone does not establish a runtime gain or calibrate a population estimator.

## A comparison that can reject PID

Before examining final results, select the applicable methods and fix the data version, labels, source groups, observation model, sampling unit, splits, preprocessing, training budget, evaluation metrics, numerical margins and stopping rule. This note does not supply a preregistered benchmark. The repository's [research workflow](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md) defines the required candidate and judge separation.

Report two panels: compatible methods on the same frozen representation, and each method with its appropriate representation under equal nested tuning resources. The first isolates objective choice; the second tests practical end-to-end performance. A continuous method must not be forced through coarse bins merely to help categorical PID. Repeated frames from one recording must not be counted as independent test episodes. Quantization, missingness and changing support need explicit treatment.

Retain every registered outcome, including no advantage, unstable conclusions across PID definitions, failures on sparse alphabets and cases where a simpler method wins. Prefer the alternative if it answers the question with equal or better evidence and lower cost. For Crebain and Galadriel, current bounded offline conformance fixtures establish neither field performance nor a PID advantage over these methods.
