#!/usr/bin/env python3
"""Apples-to-apples frozen-IHB comparison on the first-place OSD-575 centerpiece.

Uses the same NASA OSDR study, four crew members, 302 serum analytes, and seven
serum timepoints used by the public first-place demonstration. IHB rules remain
frozen: each subject is their own reference; L-92/L-44/L-3 define mean/SD;
postflight observations are expressed in that subject's own baseline SD units;
missing data are excluded; |z|>=2 is the submitted candidate threshold.

The comparison layer downloads the first-place public output tables only to
measure concordance. It does not import or alter the first-place implementation.
"""
from __future__ import annotations
import hashlib, json, re, urllib.request
from pathlib import Path
import numpy as np
import pandas as pd

OSD_API="https://osdr.nasa.gov/osdr/data/osd/files/575"
WIN_SIG="https://raw.githubusercontent.com/PMN123/artemis2-normative-modeling-n4/main/outputs/tables/i4_acute_signature.csv"
WIN_REC="https://raw.githubusercontent.com/PMN123/artemis2-normative-modeling-n4/main/outputs/tables/i4_recovery_summary.csv"
SUBJECTS=["C001","C002","C003","C004"]
BASE=["L-92","L-44","L-3"]
POST=["R+1","R+45","R+82","R+194"]
TPS=BASE+POST
SAMPLE_RE=re.compile(r"(C00[1-4])[ _-]?(?:[a-z\-]+[_ -])?(L-92|L-44|L-3|R\+1|R\+45|R\+82|R\+194)",re.I)
FILES=[
 (re.compile(r"AlamarPanel_TRANSFORMED\.csv$",re.I),"alamar","Immune-Alamar"),
 (re.compile(r"CMP_TRANSFORMED\.csv$",re.I),"cmp","CMP"),
 (re.compile(r"cardiovascular_EvePanel_TRANSFORMED\.csv$",re.I),"cardio","Cardio-Eve"),
 (re.compile(r"immune_EvePanel_TRANSFORMED\.csv$",re.I),"immune_eve","Immune-Eve"),
]

def get_json(url):
 req=urllib.request.Request(url,headers={"User-Agent":"ARC-IHB-headtohead/1.0"})
 with urllib.request.urlopen(req,timeout=120) as r:return json.loads(r.read())
def dl(url,dst):
 dst=Path(dst); dst.parent.mkdir(parents=True,exist_ok=True)
 req=urllib.request.Request(url,headers={"User-Agent":"ARC-IHB-headtohead/1.0"})
 with urllib.request.urlopen(req,timeout=180) as r,dst.open("wb") as f:
  while True:
   b=r.read(1024*1024)
   if not b:break
   f.write(b)
 return dst
def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def norm(s):return re.sub(r"[^a-z0-9]+","",str(s).lower())

def osdr_files(root):
 data=get_json(OSD_API); allf=[]
 for _,st in data.get("studies",{}).items(): allf.extend(st.get("study_files",[]))
 rec=[]
 for rx,prefix,panel in FILES:
  m=[f for f in allf if rx.search(str(f.get("file_name","")))]
  uniq=[];seen=set()
  for f in m:
   u=f.get("remote_url")
   if u and u not in seen:seen.add(u);uniq.append(f)
  if len(uniq)!=1:raise RuntimeError(f"{panel}: expected one source file, got {[x.get('file_name') for x in uniq]}")
  f=uniq[0]; remote=f["remote_url"]; url=remote if str(remote).startswith("http") else "https://osdr.nasa.gov"+remote
  p=dl(url,Path(root)/str(f["file_name"]))
  rec.append({"prefix":prefix,"panel":panel,"path":str(p),"file_name":f["file_name"],"sha256":sha(p)})
 return rec

def parse_sample(x):
 m=SAMPLE_RE.search(str(x)); return (m.group(1).upper(),m.group(2).upper()) if m else (None,None)

def load_panel(rec):
 df=pd.read_csv(rec["path"],encoding="utf-8-sig",low_memory=False)
 sc="Sample ID" if "Sample ID" in df.columns else "Sample Name" if "Sample Name" in df.columns else df.columns[0]
 parsed=df[sc].map(parse_sample); df=df.copy();df["subject"]=[x[0] for x in parsed];df["timepoint"]=[x[1] for x in parsed]
 df=df[df.subject.isin(SUBJECTS)&df.timepoint.isin(TPS)].copy()
 # IHB uses measurement values, not the OSDR population/reference percent columns.
 feat={}
 for c in df.columns:
  lo=str(c).lower()
  if c in {sc,"subject","timepoint"} or "percent" in lo or "range" in lo or "normalized" in lo:continue
  if rec["prefix"] in {"alamar","immune_eve","cardio"} and "concentration" not in lo:continue
  if rec["prefix"]=="cmp" and "value" not in lo:continue
  v=pd.to_numeric(df[c],errors="coerce")
  if v.notna().any():feat[f"{rec['prefix']}__{c}"]=v
 out=pd.concat([df[["subject","timepoint"]].reset_index(drop=True),pd.DataFrame(feat).reset_index(drop=True)],axis=1)
 return out.drop_duplicates(["subject","timepoint"],keep="first").set_index(["subject","timepoint"])

def build_master(records):
 parts=[load_panel(r) for r in records]; m=parts[0]
 for p in parts[1:]:m=m.join(p,how="outer")
 grid=pd.MultiIndex.from_product([SUBJECTS,TPS],names=["subject","timepoint"])
 return m.reindex(grid)

def analyze(master):
 rows=[]
 for s in SUBJECTS:
  sm=master.xs(s,level="subject")
  for f in master.columns:
   b=pd.to_numeric(sm.loc[BASE,f],errors="coerce").dropna(); n=len(b); mu=float(b.mean()) if n else np.nan; sd=float(b.std(ddof=1)) if n>=2 else np.nan
   r={"subject":s,"feature":f,"baseline_n":n,"baseline_mean":mu,"baseline_sd":sd,"baseline_evaluable":bool(n>=2 and np.isfinite(sd) and sd>0)}
   for tp in POST:
    x=sm.loc[tp,f] if tp in sm.index else np.nan; x=float(x) if pd.notna(x) else np.nan
    suf=tp.replace("+","p")
    r[f"value_{suf}"]=x
    r[f"z_{suf}"]=(x-mu)/sd if r["baseline_evaluable"] and np.isfinite(x) else np.nan
    r[f"pct_{suf}"]=(x-mu)/mu*100 if np.isfinite(x) and np.isfinite(mu) and mu!=0 else np.nan
   rows.append(r)
 return pd.DataFrame(rows)

def panel_and_analyte(feature):
 prefix,raw=feature.split("__",1)
 panel={"alamar":"Immune-Alamar","cmp":"CMP","cardio":"Cardio-Eve","immune_eve":"Immune-Eve"}[prefix]
 # Strip unit/value suffix to recover the assay analyte stem.
 stem=re.split(r"_(?:concentration|value)(?:_|$)",raw,flags=re.I)[0]
 return panel,stem

def map_winner_signature(traj,winner):
 lookup={}
 for f in traj.feature.unique():
  p,a=panel_and_analyte(f); lookup[(p,norm(a))]=f
 rows=[]
 for rank,w in winner.reset_index(drop=True).iterrows():
  key=(str(w.panel),norm(w.analyte)); f=lookup.get(key)
  base={"winner_rank":rank+1,"panel":w.panel,"analyte":w.analyte,"winner_direction":w.direction,
        "winner_mean_log2fc":w.mean_log2_fold_change,"winner_q":w.q_moderated_BH,"winner_signflip_p":w.p_exact_signflip,
        "ihb_feature":f,"mapped":bool(f)}
  if f:
   g=traj[traj.feature==f]
   sign=1 if str(w.direction).lower()=="up" else -1
   z=pd.to_numeric(g.z_Rp1,errors="coerce"); pct=pd.to_numeric(g.pct_Rp1,errors="coerce")
   base.update({"n_evaluable":int(z.notna().sum()),"n_ihb_abs_z_ge2":int((z.abs()>=2).sum()),
                "n_direction_agree":int(((pct*sign)>0).sum()),"median_abs_ihb_z":float(z.abs().median()),
                "median_signed_pct_in_winner_direction":float((pct*sign).median())})
   for _,q in g.iterrows():
    base[f"{q.subject}_z_Rp1"]=q.z_Rp1;base[f"{q.subject}_pct_Rp1"]=q.pct_Rp1
  rows.append(base)
 return pd.DataFrame(rows)

def subject_summary(traj):
 rows=[]
 for s,g in traj.groupby("subject"):
  z1=pd.to_numeric(g.z_Rp1,errors="coerce"); acute=g[z1.notna()&(z1.abs()>=2)].copy()
  r={"subject":s,"features":len(g),"features_Rp1_evaluable":int(z1.notna().sum()),"acute_candidates_abs_z_ge2":len(acute),
     "acute_candidate_fraction":len(acute)/z1.notna().sum() if z1.notna().sum() else np.nan}
  for tp in ["Rp45","Rp82","Rp194"]:
   z=pd.to_numeric(acute[f"z_{tp}"],errors="coerce"); valid=z.notna()
   r[f"acute_candidates_evaluable_{tp}"]=int(valid.sum());r[f"within_2sd_{tp}"]=int((valid&(z.abs()<2)).sum());r[f"outside_2sd_{tp}"]=int((valid&(z.abs()>=2)).sum())
   if valid.sum():r[f"fraction_within_2sd_{tp}"]=float((z[valid].abs()<2).mean())
  rows.append(r)
 return pd.DataFrame(rows)

def main():
 root=Path("counterfactual/inspiration4/headtohead_source");out=Path("counterfactual/inspiration4/headtohead_outputs");out.mkdir(parents=True,exist_ok=True)
 records=osdr_files(root);master=build_master(records);master.to_csv(out/"NASA_OSD575_7timepoint_302analyte_master.csv")
 traj=analyze(master);traj.to_csv(out/"IHB_OSD575_7timepoint_feature_trajectories.csv",index=False)
 ss=subject_summary(traj);ss.to_csv(out/"IHB_OSD575_subject_recovery_summary.csv",index=False)
 sigpath=dl(WIN_SIG,out/"first_place_i4_acute_signature.csv"); recpath=dl(WIN_REC,out/"first_place_i4_recovery_summary.csv")
 winner=pd.read_csv(sigpath); conc=map_winner_signature(traj,winner);conc.to_csv(out/"IHB_vs_first_place_signature_concordance.csv",index=False)
 top9=conc.head(9); allsig=conc
 def score(g):
  return {"mapped":int(g.mapped.sum()),"features_with_ihb_threshold_in_at_least_1_crew":int((g.n_ihb_abs_z_ge2>=1).sum()),
          "features_with_ihb_threshold_in_at_least_2_crew":int((g.n_ihb_abs_z_ge2>=2).sum()),
          "direction_agreements":int(g.n_direction_agree.sum()),"direction_comparisons":int(g.n_evaluable.sum())}
 report={"analysis":"Frozen IHB vs public first-place OSD-575 centerpiece","n_subjects":4,"n_timepoints":7,"timepoints":TPS,
         "n_measurement_features":int(len(master.columns)),"nasa_files":records,"top9":score(top9),"winner_signature_26":score(allsig),
         "first_place_signature_source":WIN_SIG,"first_place_recovery_source":WIN_REC,
         "interpretation_boundary":"Winner cohort-level effect/inference and IHB subject-level deviation are different estimands. Concordance is descriptive, not a placement score."}
 (out/"headtohead_summary.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps(report,indent=2));print("\nIHB recovery summary:\n",ss.to_string(index=False));print("\nWinner-signature concordance:\n",conc[["winner_rank","panel","analyte","winner_direction","n_ihb_abs_z_ge2","n_direction_agree","median_abs_ihb_z"]].to_string(index=False))
 if len(master.columns)!=302:raise SystemExit(f"Expected 302 OSD-575 measurement features, found {len(master.columns)}")
 if conc.mapped.sum()!=len(winner):raise SystemExit(f"Mapped {conc.mapped.sum()}/{len(winner)} winner signature features")

if __name__=="__main__":main()
