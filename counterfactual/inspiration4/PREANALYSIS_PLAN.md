# Pre-analysis and Method-Comparison Plan

Locked before inspecting frozen-IHB results on Inspiration4.

## Counterfactual question
What would the IHB methodology ARC actually submitted have produced if ARC had selected the NASA OSDR Inspiration4 crew as the challenge proxy dataset?

This is not a reconstruction of a hypothetical different ARC method. The frozen track preserves ARC's submitted analytical claims and changes the proxy dataset.

## Source-control facts
- Base code/history: final pre-deadline ARC demonstration commit `d0c6eef45555eda62391076bd8f3676d78d9f7f7`.
- Challenge guidance must be represented as conflicting rather than simplified: the public proxy-data page states proxy data should mirror Artemis II without using actual astronaut data, while retained Official Rules §7.1 expressly named NASA OSDR Inspiration4 as an example recommended dataset.
- The publicly released winner summary states that the first-place Transfer-Calibrated Normative Modeling submission demonstrated its method on the four-person Inspiration4 crew.

## Frozen IHB track
Primary formula, per subject `i`, metric `m` and post-baseline observation `t`:

`z_i,m,t = (x_i,m,t - mean_i,m,pre) / sd_i,m,pre`

Preflight baseline is L-92, L-44 and L-3. R+1 is the acute postflight checkpoint; R+45 and R+82 are recovery checkpoints. Missing values are excluded. No crew-level variance is borrowed.

The submitted ±2 SD candidate-deviation rule is retained. The submitted example persistence condition of at least three consecutive nights is not evaluable with sparse biospecimen collection and will not be replaced.

## Primary outputs
1. Per-crew, per-feature acute deviation at R+1 in individual-baseline SD units.
2. Per-crew recovery trajectory at R+45 and R+82 relative to the same baseline.
3. Counts/fractions of evaluable features crossing |z| >= 2, by crew member and modality.
4. Direction reversal/overshoot relative to the acute perturbation.
5. Ranked feature deviations, clearly descriptive rather than population-significance claims.

## Known stress test
Three preflight points provide a shallow estimate of each person's baseline SD. The frozen track will expose this limitation rather than stabilize it with pooled crew variance, empirical Bayes, external priors or shrinkage. Those are separate methods and may be evaluated later as sensitivity analyses.

## Comparison target: first-place public methodology
The public winner summary describes Transfer-Calibrated Normative Modeling as a high-resolution case-series approach combining variance-borrowing empirical-Bayes tests, exact permutation inference, shrinkage-based multivariate scoring and Gaussian-process recovery modeling on a common calibrated scale, demonstrated on Inspiration4 and reporting an acute inflammatory signature plus per-crew recovery trajectories.

A fair comparison will therefore distinguish *different inferential targets*. IHB asks how far each astronaut moves from their own observed stable reference frame. The first-place stack additionally borrows/stabilizes information and performs formal small-sample/multivariate inference.

## Comparison axes fixed in advance
- Individual localization: can a result be traced to a specific crew member and metric?
- Acute signal: what perturbations are detected at/near R+1?
- Recovery: how directly are R+45/R+82 recovery, persistence and overshoot represented?
- Multimodal common scale: how are heterogeneous units made comparable?
- Uncertainty: how honestly is uncertainty represented with n=4 and sparse within-person baselines?
- Multiplicity/high dimensionality: descriptive individualized scoring versus formal multiple-testing/shrinkage machinery.
- Quality control: susceptibility to assay drift, zeros, missingness and low-variance baselines.
- External information: whether inference depends on cross-crew variance, external cohorts, priors or transfer calibration.
- Interpretability/actionability: what a flight surgeon or HRP analyst can understand and act on.
- Computational burden: runtime, dependencies, model-fitting complexity and edge/onboard feasibility.
- Reproducibility: number of preprocessing/modeling choices required before a result is produced.

## Claims we will not make
- We will not infer a hypothetical NASA placement from the counterfactual alone.
- We will not claim that matching a published biological finding proves methodological superiority.
- We will not tune IHB thresholds after seeing Inspiration4 and then call them part of the original method.
- We will not treat the third-party harmonized table as the final source of truth; publication-grade results require NASA OSDR source verification.

## Sensitivity/extension track (only after frozen results are locked)
Potential extensions may include robust baseline scale estimators, empirical-Bayes stabilization, compositional transforms for microbiome data, and dense wearable/clinical controlled-access datasets. Every extension will be labeled as post-submission and kept separate from the frozen counterfactual.
