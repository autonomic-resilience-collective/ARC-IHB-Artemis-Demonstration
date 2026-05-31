IHB Deep Phenotyping Framework — Demonstration on Proxy Data
NASA Artemis II Human Research Data Methodology Challenge
Autonomic Resilience Collective | Buckingham & Johnson, 2026
research@autonomicresiliencecollective.org
================================================================

WHAT THIS IS
------------
A complete, reproducible demonstration of the Individualized Homeostatic
Baseline (IHB) within-subject deep phenotyping framework, applied to a
65-month longitudinal proxy dataset. Running the notebook regenerates every
figure and the phase-summary table reported in the Methodology Description
(Component 1) and Supporting Documentation (Component 4).

PRIVACY NOTE
------------
The dataset is indexed by STUDY DAY (Day 0 = event onset), not calendar
dates. No calendar dates are included in this package. IHB uses only
relative timing and phase membership, so this transformation is analytically
lossless: every statistic is identical to a calendar-indexed analysis.

PROXY DATASET
-------------
Selected under the challenge "Bring Your Own Data" provision (Official Rules
Section 7.1). The dataset is an astronaut-analog control: a healthy, active,
adult monitored continuously under free-living conditions across a pre-event baseline, a
defined extreme physiological event, and an extended recovery — the
pre/during/post arc the challenge targets, with the strongly preferred
longitudinal (within-individual) structure.

  Instrument        : Oura Ring Gen 3, nightly rMSSD (ECG-validated, r^2 = 0.98)
  Indexing          : study day relative to event onset (Day 0)
  Canonical window  : study days up to +709 (frozen at 2026-02-27, the publication cutoff)
  Window            : ~1,815 nights (frozen at 2026-02-27 publication cutoff)
  Valid nights      : 1,713 with valid nightly rMSSD (94.4% complete)
  Study design      : free-living, non-interventional; no ongoing clinical
                      management of the subject's physiology
  Preprocessing     : raw nightly values; no interpolation or synthetic fill
  Peer review       : findings published at ACM BCB 2026 (see citation below)

REQUIREMENTS
------------
  Python 3.8+
  pip install numpy pandas matplotlib scipy

HOW TO RUN
----------
  1. Keep oura_data_studyday.csv (columns: study_day, hrv_rmssd) in this folder.
  2. Option A (notebook): open ARC_IHB_Demonstration.ipynb and Run All.
     Option B (script):   python3 ihb_demo_studyday.py
  3. All outputs are written to ./outputs/. The code runs end-to-end with
     no modification required by the reviewer.

OUTPUTS GENERATED
-----------------
  outputs/01_full_trajectory.png          65-month trajectory, phase bands, baseline
  outputs/02_phase_deviations.png         within-subject phase deviation scores
  outputs/03_anomaly_detection_window.png pre-event window, +/-2 SD detection
  outputs/04_recovery_trajectory.png      post-event recovery & supercompensation
  outputs/05_continued_recovery.png       recent months vs the 65-month baseline
  outputs/IHB_phase_summary.csv           phase means, SD, 95% CI, % deviation

KEY REPRODUCED RESULTS (within-subject; baseline = 79.5 ms)
-----------------------------------------------------------
  Second trimester        62.5 ms   -21.4%
  Third trimester         58.8 ms   -26.0%
  Early postpartum        55.7 ms   -29.9%   (peripartum minimum, lactation)
  Late postpartum (23 mo) 100.1 ms  +25.9%   (supercompensation)
  Pre-event 14-day window 114.9 ms  +44.5%   (peak 171 ms, day -4, +115%)

These reproduce the peer-reviewed publication's findings. A post-publication
"continued recovery" extension (Figure 5) shows recent trailing-window means
rising further above baseline (+31% to +43%), reported as a supplementary
observation, not a revision to the published results.

CITATION
--------
Buckingham, C.N. & Johnson, K. (2026). A Computational Framework for Deep
Phenotyping of Maternal Autonomic Resilience Using 65 Months of Continuous
Wearable Biometric Data. ACM BCB 2026, Rende (CS), Italy.
https://doi.org/10.1145/3807503.3816889
