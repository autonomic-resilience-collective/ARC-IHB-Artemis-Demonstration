#!/usr/bin/env python3
"""IHB Inspiration4 counterfactual replay.

Apply the IHB methodology submitted to the 2026 NASA Artemis II Human Research
Data Methodology Challenge to public Inspiration4 data without retuning the
method after seeing the astronaut measurements.

Frozen IHB rules carried forward:
- each subject is their own reference population;
- pre-event observations define that subject/metric baseline mean and SD;
- later observations are expressed in that subject's baseline SD units;
- missing values are excluded, not imputed;
- +/-2 SD is retained as the candidate deviation threshold;
- recovery is characterized relative to the same pre-event baseline.

Dataset translation registered before analysis:
- baseline: L-92, L-44, L-3
- acute post-flight: R+1
- recovery: R+45, R+82
- >=3 consecutive-night persistence is not evaluable on sparse biospecimen
  sampling and is not replaced by a weaker rule.

The fast pass uses the public 24x1115 harmonized table from the post-challenge
Puerta Angulo repository for execution speed. Publication-grade results must be
reconstructed/verified against NASA OSDR source files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd

DEFAULT_URL = "https://raw.githubusercontent.com/engimine/HRP_Artemis_II/main/publicacion/_v3_master_table.csv"
BASELINE_TPS = ("L-92", "L-44", "L-3")
POST_TPS = ("R+1", "R+45", "R+82")
TIME_ORDER = BASELINE_TPS + POST_TPS
FROZEN_SUBMISSION_COMMIT = "d0c6eef45555eda62391076bd8f3676d78d9f7f7"

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def obtain_input(path, url):
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading fast-pass table from {url}")
        urllib.request.urlretrieve(url, path)
    return path

def modality_for(col):
    low = col.lower()
    if low.startswith("alamar__"): return "serum_alamar"
    if low.startswith("cmp__"): return "serum_cmp"
    if low.startswith("cardio__"): return "serum_cardiovascular"
    if low.startswith("immune_eve__"): return "serum_immune"
    if low.startswith("urine__"): return "urine_inflammation"
    if low.startswith("cbc__"): return "whole_blood_cbc"
    if low.startswith("tax_") or low.startswith("taxonomy"): return "microbiome"
    return low.split("__",1)[0] if "__" in low else "other"

def is_primary_measurement_column(col):
    low = col.lower()
    if low in {"subject","timepoint","spaceflight"}: return False
    # Compositional microbiome data are held for a later preregistered transform;
    # the submitted demo did not specify a compositional-data transform.
    if low.startswith("tax_") or low.startswith("taxonomy"): return False
    # Avoid crew-normalized and reference-range columns. IHB derives its own
    # subject-specific reference from measurement values.
    if "percent" in low or "normalized" in low or "range" in low: return False
    if low.startswith("alamar__"):
        return "concentration" in low or low.endswith("_npq")
    if low.startswith("cardio__") or low.startswith("immune_eve__"):
        return "concentration" in low
    if low.startswith("urine__"):
        return "concentration" in low or low.endswith("_npq")
    if low.startswith("cmp__") or low.startswith("cbc__"):
        return "value" in low
    return False

def prepare(df):
    required = {"subject","timepoint"}
    missing = required - set(df.columns)
    if missing: raise ValueError(f"Missing required columns: {sorted(missing)}")
    x = df[df["timepoint"].isin(TIME_ORDER)].copy()
    x["subject"] = x["subject"].astype(str)
    x["timepoint"] = x["timepoint"].astype(str)
    features = [c for c in x.columns if is_primary_measurement_column(c)]
    if not features: raise ValueError("No eligible measurement columns found")
    for c in features:
        x[c] = pd.to_numeric(x[c], errors="coerce").replace([np.inf,-np.inf],np.nan)
    return x, features

def analyze_feature(x, subject, feature):
    s = x[x["subject"] == subject].set_index("timepoint")[feature]
    baseline = s.reindex(BASELINE_TPS).dropna()
    n = int(len(baseline))
    mean = float(baseline.mean()) if n else np.nan
    sd = float(baseline.std(ddof=1)) if n >= 2 else np.nan
    sem = sd / math.sqrt(n) if n >= 2 and np.isfinite(sd) else np.nan
    out = {
        "subject":subject,"feature":feature,"modality":modality_for(feature),
        "baseline_n":n,"baseline_mean":mean,"baseline_sd":sd,
        "baseline_ci_low":mean-1.96*sem if np.isfinite(sem) else np.nan,
        "baseline_ci_high":mean+1.96*sem if np.isfinite(sem) else np.nan,
        "baseline_evaluable":bool(n >= 2 and np.isfinite(sd) and sd > 0),
    }
    for tp in POST_TPS:
        value = s.get(tp, np.nan)
        value = float(value) if pd.notna(value) else np.nan
        z = (value-mean)/sd if out["baseline_evaluable"] and np.isfinite(value) else np.nan
        pct = ((value-mean)/mean*100) if np.isfinite(value) and np.isfinite(mean) and mean != 0 else np.nan
        suffix = tp.replace("+","p").replace("-","m")
        out[f"value_{suffix}"] = value
        out[f"z_{suffix}"] = z
        out[f"pct_{suffix}"] = pct
    z1,z45,z82 = out["z_Rp1"],out["z_Rp45"],out["z_Rp82"]
    out["acute_candidate_2sd"] = bool(np.isfinite(z1) and abs(z1) >= 2)
    out["within_2sd_R45"] = bool(np.isfinite(z45) and abs(z45) < 2)
    out["within_2sd_R82"] = bool(np.isfinite(z82) and abs(z82) < 2)
    out["acute_direction"] = "up" if np.isfinite(z1) and z1>0 else "down" if np.isfinite(z1) and z1<0 else "none_or_missing"
    out["overshoot_R45"] = bool(np.isfinite(z1) and np.isfinite(z45) and z1 != 0 and z45 != 0 and np.sign(z1) != np.sign(z45))
    out["overshoot_R82"] = bool(np.isfinite(z1) and np.isfinite(z82) and z1 != 0 and z82 != 0 and np.sign(z1) != np.sign(z82))
    return out

def summarize_subjects(long):
    rows=[]
    for subject,g in long.groupby("subject",sort=True):
        ev=g[g["baseline_evaluable"]].copy()
        z1=pd.to_numeric(ev["z_Rp1"],errors="coerce")
        acute=ev[z1.notna() & (z1.abs()>=2)]
        denom=int(z1.notna().sum())
        rows.append({
            "subject":subject,"features_selected":int(len(g)),
            "features_baseline_evaluable":int(len(ev)),"features_with_Rp1_z":denom,
            "acute_candidates_abs_z_ge_2":int(len(acute)),
            "acute_candidate_fraction":float(len(acute)/denom) if denom else np.nan,
            "median_abs_z_Rp1":float(z1.abs().median()) if denom else np.nan,
            "max_abs_z_Rp1":float(z1.abs().max()) if denom else np.nan,
            "acute_candidates_within_2sd_R45":int(acute["within_2sd_R45"].sum()),
            "acute_candidates_within_2sd_R82":int(acute["within_2sd_R82"].sum()),
            "acute_candidates_overshoot_R45":int(acute["overshoot_R45"].sum()),
            "acute_candidates_overshoot_R82":int(acute["overshoot_R82"].sum()),
        })
    return pd.DataFrame(rows)

def summarize_modalities(long):
    rows=[]
    for (subject,modality),g in long.groupby(["subject","modality"],sort=True):
        ev=g[g["baseline_evaluable"]].copy(); z1=pd.to_numeric(ev["z_Rp1"],errors="coerce")
        ok=z1.notna(); cand=ok & (z1.abs()>=2)
        rows.append({"subject":subject,"modality":modality,"features_evaluable_Rp1":int(ok.sum()),
                     "acute_candidates_abs_z_ge_2":int(cand.sum()),
                     "acute_candidate_fraction":float(cand.sum()/ok.sum()) if ok.sum() else np.nan,
                     "median_abs_z_Rp1":float(z1[ok].abs().median()) if ok.any() else np.nan})
    return pd.DataFrame(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="counterfactual/inspiration4/data/i4_master_fastpass.csv")
    p.add_argument("--url",default=DEFAULT_URL)
    p.add_argument("--outdir",default="counterfactual/inspiration4/outputs")
    args=p.parse_args()
    inp=obtain_input(args.input,args.url); outdir=Path(args.outdir); outdir.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(inp,low_memory=False); x,features=prepare(df); subjects=sorted(x["subject"].dropna().unique().tolist())
    long=pd.DataFrame([analyze_feature(x,s,f) for s in subjects for f in features])
    long.to_csv(outdir/"IHB_Inspiration4_feature_trajectories.csv",index=False)
    ss=summarize_subjects(long); ss.to_csv(outdir/"IHB_Inspiration4_subject_summary.csv",index=False)
    ms=summarize_modalities(long); ms.to_csv(outdir/"IHB_Inspiration4_modality_summary.csv",index=False)
    ranked=long[pd.to_numeric(long["z_Rp1"],errors="coerce").notna()].copy(); ranked["abs_z_Rp1"]=ranked["z_Rp1"].abs()
    ranked=ranked.sort_values(["subject","abs_z_Rp1"],ascending=[True,False])
    ranked.groupby("subject",group_keys=False).head(25).to_csv(outdir/"IHB_Inspiration4_top25_acute_by_subject.csv",index=False)
    audit={
      "analysis":"IHB Inspiration4 frozen-method counterfactual fast pass",
      "frozen_submission_commit":FROZEN_SUBMISSION_COMMIT,"input_url":args.url,"input_sha256":sha256(inp),
      "input_rows":int(df.shape[0]),"input_columns":int(df.shape[1]),"subjects":subjects,
      "baseline_timepoints":list(BASELINE_TPS),"post_timepoints":list(POST_TPS),"features_selected":len(features),
      "modalities_selected":sorted({modality_for(f) for f in features}),
      "rules":{"reference":"within-subject only; no cross-subject variance borrowing","missingness":"exclude; no imputation",
               "deviation_score":"(observation - individual baseline mean) / individual baseline SD","candidate_threshold":"absolute z >= 2",
               "persistence_rule":"not evaluable on sparse biospecimen schedule; not replaced","population_inference":False},
      "fast_pass_limitation":"Third-party harmonized table used for execution speed; primary replay must rebuild/verify NASA OSDR source columns."
    }
    (outdir/"audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    print("IHB Inspiration4 frozen-method fast pass complete")
    print(f"Input: {df.shape[0]} rows x {df.shape[1]} columns; selected measurements: {len(features)}")
    print(ss.to_string(index=False))

if __name__ == "__main__": main()
