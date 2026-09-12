# Inspiration4 Counterfactual Replay — Frozen IHB

## Question
What would ARC's submitted IHB methodology have shown if ARC had used the NASA OSDR Inspiration4 astronaut dataset as its Artemis II challenge proxy?

This branch is a post-challenge forensic replay. It starts from the final pre-deadline demonstration commit `d0c6eef45555eda62391076bd8f3676d78d9f7f7` and leaves the original submission history unchanged.

## Frozen-method rules
The primary analysis is intentionally constrained to the methodology described in ARC's submitted materials rather than optimized after seeing Inspiration4.

1. Each crew member is their own reference population.
2. For every metric, preflight observations establish that person's baseline mean, SD and within-subject 95% CI.
3. Later observations are expressed as deviations from that person's baseline in their own SD units.
4. Missing observations are excluded; they are not imputed.
5. `|z| >= 2` is retained as the candidate-deviation threshold.
6. Recovery is described against the same preflight baseline, including return toward the baseline and direction reversal/overshoot.
7. Cross-subject variance is not borrowed in the frozen IHB track.
8. The submitted persistence example (`>2 SD` across at least three consecutive nights) cannot be evaluated on the sparse biospecimen schedule and is therefore reported as *not evaluable*, not replaced by a weaker rule.

## Inspiration4 time mapping
- Baseline: `L-92`, `L-44`, `L-3`
- Acute postflight: `R+1`
- Recovery checkpoints: `R+45`, `R+82`

The three-point preflight baseline is much shallower than ARC's original 65-month validation record. That limitation is part of the stress test and will be reported, not hidden by pooling the four crew.

## Data policy
The fast pass uses the public 24 × 1115 harmonized Inspiration4 table in the post-challenge Puerta Angulo repository solely to establish that the replay executes end-to-end. It selects raw/value/concentration columns and excludes crew-normalized percent columns.

The publication-grade replay will reconstruct or verify inputs against NASA OSDR source studies (including OSD-569, OSD-575 and OSD-656) and compare hashes/results before any scientific claim is treated as final.

Microbiome/taxonomy features are held out of the first frozen replay because compositional abundance data require a transform that was not specified in ARC's submitted demonstration. They can be added later as a clearly labeled sensitivity/extension analysis rather than silently modifying the frozen method.

## Outputs
`run_frozen_ihb.py` writes:

- `IHB_Inspiration4_feature_trajectories.csv`
- `IHB_Inspiration4_subject_summary.csv`
- `IHB_Inspiration4_modality_summary.csv`
- `IHB_Inspiration4_top25_acute_by_subject.csv`
- `audit.json`

## Interpretation boundary
This track is descriptive, individualized physiology. It does not claim population inference from four astronauts. A later comparison layer can evaluate IHB beside winning and other public methods on signal localization, uncertainty, recovery characterization, cross-modal integration, interpretability, preprocessing burden, missingness handling and computational burden without pretending the approaches answer exactly the same statistical question.
