# NASA Artemis II Human Research Data Methodology Challenge
## Counterfactual Inspiration4 Replay of ARC's Submitted IHB Methodology

**Autonomic Resilience Collective (ARC)**  
**Method:** Individualized Homeostatic Baseline (IHB): A Within-Subject Deep Phenotyping Framework  
**Status:** Retrospective counterfactual analysis, created after challenge adjudication. This document is not an original challenge submission and makes no claim about hypothetical placement.

## Purpose and source control

This replay answers one narrow question: **What would ARC's submitted IHB methodology have produced if ARC had selected NASA OSDR Inspiration4 as its proxy dataset?**

The analysis is anchored to ARC's final pre-deadline demonstration commit `d0c6eef45555eda62391076bd8f3676d78d9f7f7`. The original submission history and `main` branch remain unchanged. No IHB threshold was tuned after inspection of Inspiration4.

Challenge guidance is recorded as it existed rather than harmonized after the fact. ARC's retained Official Rules §7.1 named **NASA OSDR Inspiration4 data** as an example recommended dataset, while the public challenge page also instructed participants to use proxy datasets without using actual astronaut data. This replay therefore treats Inspiration4 as an allowed-by-one-official-source counterfactual, not as evidence that ARC's original dataset choice was unreasonable.

---

# Component 1 — Methodology Description

**Frozen. No substantive methodological change from ARC's submitted Component 1.**

IHB treats each subject as their own reference population. For every subject and metric:

1. **Baseline estimation.** Pre-event observations establish the individual's reference mean, SD, and within-subject 95% CI from observed values without interpolation.
2. **Phase segmentation.** Observations are assigned to operationally anchored pre-event, event, and recovery phases.
3. **Within-subject deviation scoring.** Each later observation is expressed relative to that individual's own baseline in baseline-SD units.
4. **Anomaly and recovery characterization.** Subject-calibrated deviations identify candidate perturbations; recovery is described by return toward baseline, persistence, direction reversal/overshoot, and endpoint.

Missing observations are excluded rather than imputed. The frozen demonstration retains `|z| >= 2` as the candidate-deviation threshold. The submitted example persistence criterion requiring at least three consecutive nights cannot be evaluated on sparse biospecimen sampling and is therefore marked **not evaluable** rather than replaced with a weaker post-hoc rule.

This counterfactual does **not** add population inference, empirical-Bayes variance borrowing, pooled-crew variance, external normative priors, or shrinkage to the frozen IHB track. Those are distinct methods and belong only in explicitly labeled sensitivity analyses.

---

# Component 2 — Demonstration Using Proxy Data

## Primary apples-to-apples dataset

The primary replay uses **NASA OSDR OSD-575**, the same real four-person Inspiration4 serum dataset used by the public first-place demonstration:

- Crew: C001–C004
- Preflight baseline: L-92, L-44, L-3
- Postflight: R+1, R+45, R+82, R+194
- Four serum panels
- 302 measurement analytes after excluding population/reference-range and percent-normalized helper columns
- No cross-crew imputation in IHB

NASA-transformed source files are downloaded directly at run time and recorded by SHA-256 in the audit output. The corrected source reconstruction contains nonmissing measurements at all seven timepoints, including 1,207 at R+194.

## Frozen IHB calculation

For astronaut `i`, feature `m`, and postflight timepoint `t`:

`IHB_z(i,m,t) = [x(i,m,t) - mean_pre(i,m)] / SD_pre(i,m)`

where `mean_pre` and `SD_pre` are estimated only from that astronaut's observed L-92, L-44, and L-3 values for that feature.

## Acute R+1 result on OSD-575

Of 301 R+1-evaluable analytes per astronaut, frozen IHB identified:

| Crew | Acute candidates `|z| >= 2` | Fraction of evaluable analytes |
|---|---:|---:|
| C001 | 116 | 38.5% |
| C002 | 43 | 14.3% |
| C003 | 46 | 15.3% |
| C004 | 35 | 11.6% |

These values are descriptive subject-specific departures, not population-significance calls.

## Recovery of IHB's own acute candidates

| Crew | Within ±2 SD at R+45 | R+82 | R+194 |
|---|---:|---:|---:|
| C001 | 66.1% | 29.3% | 26.7% |
| C002 | 58.1% | 67.4% | 51.2% |
| C003 | 19.6% | 30.4% | 32.6% |
| C004 | 77.1% | 40.0% | 60.0% |

The individual trajectories are non-monotonic. IHB therefore does not reduce recovery to a single group endpoint: the same acute feature can normalize, overshoot, re-diverge, or remain displaced differently in each crew member.

## Cross-method biological concordance with the public first-place signature

The first-place repository defines a 26-analyte acute response signature from R+1. Without importing its inferential machinery into IHB:

- all 26 signature analytes map directly to the frozen IHB source table;
- **22/26** cross frozen IHB's `|z| >= 2` threshold in at least one astronaut;
- **10/26** cross that threshold in at least two astronauts;
- the first-place direction and each astronaut's raw IHB change agree in **89/104 astronaut × analyte comparisons (85.6%)**.

For the first-place top nine analytes:

- **6/9** cross frozen IHB's threshold in at least one astronaut;
- **4/9** cross in at least two astronauts;
- direction agrees in **30/36 astronaut × analyte comparisons (83.3%)**.

Examples include strong cross-method agreement for CCL5 (down), S100A9 (down), S100A12 (down), IL-6 (up), CXCL8 (down), and MCP-1 (up). RANTES is a useful counterexample: the first-place analysis also reports unstable direction in leave-one-subject-out sensitivity, and IHB likewise shows marked crew heterogeneity.

## Broader multi-modal extension

A second, source-verified exploratory replay expands beyond the first-place OSD-575 centerpiece to transformed public Inspiration4 serum, urine-inflammation, and CBC data from OSD-575, OSD-656, and OSD-569. The six NASA source files reproduce the overlapping third-party harmonized cells exactly (`24,732 / 24,732`, maximum absolute difference `0.0`). This yields 516 selected measurements across six modality groups for the initial multi-modal IHB stress test.

That broader extension remains secondary to the exact OSD-575 head-to-head because it no longer compares identical input matrices.

---

# Component 3 — Application Narrative

ARC's original Artemis II application logic remains materially unchanged. The difference is that the counterfactual demonstration now executes it on an actual four-person spaceflight cohort rather than an N=1 terrestrial longitudinal analog.

The Inspiration4 replay supports four claims that were already present in the submitted narrative:

1. **A four-person crew can be characterized without treating four people as a population sample.** IHB produced a separate baseline and trajectory for every astronaut and analyte.
2. **Heterogeneous measurements become interpretable on a common individualized scale.** The same deviation equation operated across metabolic, cardiovascular, cytokine, immunoproteomic, urine, and CBC measurements without comparing raw units directly.
3. **Crew-average biology can conceal operationally important individual differences.** The first-place signature and IHB agree strongly in aggregate direction, yet IHB shows that the magnitude and even direction of particular biomarkers can differ sharply by astronaut.
4. **Recovery is a trajectory, not a binary endpoint.** The R+45, R+82, and R+194 results show normalization, persistence, overshoot, and re-divergence patterns that differ by subject and feature.

The replay also sharpens one limitation that the terrestrial demonstration did not expose: **IHB depends on sufficient temporal depth to estimate an individual's baseline variance reliably.** Three preflight biospecimen draws are enough to compute an SD but not enough to estimate it robustly. Features with exceptionally small three-point baseline SD can produce very large standardized deviations from modest raw percent changes. That behavior is preserved in the frozen result rather than corrected after inspection.

This is precisely why ARC's original optional recommendation for dense passive longitudinal measurement remains relevant: IHB becomes statistically better conditioned as the within-person reference history deepens.

---

# Component 4 — Supporting Documentation and Validation

## Reproducibility and provenance

The counterfactual branch contains:

- frozen-method pre-analysis plan;
- deterministic IHB replay adapter;
- direct NASA OSDR source-verification workflow;
- exact OSD-575 seven-timepoint head-to-head workflow;
- feature-level trajectories, subject summaries, and cross-method concordance tables;
- SHA-256 provenance for NASA source files;
- separate fast-pass, NASA-source, and first-place-comparison outputs.

The original pre-deadline ARC repository remains intact. The counterfactual branch was forked from the exact final submission commit and clearly labels every post-challenge addition.

## Baseline-depth stress test

The sparse preflight schedule reveals a specific frozen-IHB weakness. Among OSD-575 R+1 candidates, many threshold crossings are associated with very low three-point baseline coefficients of variation. For example, approximately 40% of C001 candidates and 43% of C003 candidates have a preflight baseline CV below 1%. Some very large `|z|` values therefore encode denominator instability rather than equivalently enormous raw biological changes.

This does not invalidate all IHB findings: the strongest comparison is where subject-specific direction and meaningful raw changes reproduce biology independently identified by the first-place approach. It does mean the unmodified `|z| >= 2` threshold should not be treated as a calibrated false-positive-control procedure when only three baseline samples exist.

## Interpretation boundary

The counterfactual supports the conclusion that **frozen IHB recovers much of the same acute Inspiration4 biology while representing it at a different inferential level**: personalized departure and recovery rather than cohort-level significance.

It does not support a claim that IHB would necessarily have ranked above the first-place submission. The first-place methodology contains statistical machinery that frozen IHB did not: empirical-Bayes variance moderation, exact sign-flip inference, BH multiplicity control, shrinkage-based multivariate departure scoring, assay-drift QC, Gaussian-process recovery modeling, and an external NHANES calibration layer. Conversely, IHB provides a direct individualized reference-frame interpretation without requiring external normative cohorts or cross-crew variance borrowing.

---

# Component 5 — Optional Superlative Criterion

**Substantively unchanged from ARC's original submission.** The counterfactual strengthens rather than weakens the original recommendation: continuous passive wearable physiology across the mission arc would supply the temporal depth that the sparse Inspiration4 biospecimen schedule lacks, while environmental logging would help distinguish endogenous physiological drift from operational exposure effects.

---

# Counterfactual conclusion

The cleanest statement supported by this replay is:

> When ARC's pre-submission IHB methodology is frozen and applied retrospectively to the same NASA Inspiration4 serum cohort used by the public first-place demonstration, it independently recovers most of the first-place acute response signature's direction and identifies substantial crew-specific perturbation and incomplete recovery. Its principal weakness on this dataset is not n=4 itself but the shallowness of the per-person preflight baseline, which makes unregularized baseline-SD normalization unstable for some analytes. The first-place method directly addresses that sparse-baseline/high-dimensional inference problem through variance borrowing and shrinkage; IHB preserves stronger individual interpretability and requires deeper temporal sampling to realize its intended operating regime.

That is the result to carry forward into any public or scientific comparison.
