#!/usr/bin/env python3
"""Rebuild the frozen-IHB fast-pass input directly from NASA OSDR.

Downloads only the transformed, machine-readable Inspiration4 tables used by
our initial serum/urine/CBC counterfactual, reconstructs the 24-row
subject×timepoint grid, and compares that reconstruction against the public
post-challenge harmonized table used for the fast pass.

No IHB thresholds or statistics are altered here. This is provenance/source
verification only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd

API = "https://osdr.nasa.gov/osdr/data/osd/files/{num}"
FASTPASS_URL = "https://raw.githubusercontent.com/engimine/HRP_Artemis_II/main/publicacion/_v3_master_table.csv"
SUBJECTS = ["C001", "C002", "C003", "C004"]
TPS = ["L-92", "L-44", "L-3", "R+1", "R+45", "R+82"]
SAMPLE_RE = re.compile(r"(C00[1-4])[ _-]?(?:[a-z\-]+[_ -])?(L-92|L-44|L-3|R\+1|R\+45|R\+82)", re.I)

WANTED = {
    "575": [
        (re.compile(r"AlamarPanel_TRANSFORMED\.csv$", re.I), "alamar"),
        (re.compile(r"CMP_TRANSFORMED\.csv$", re.I), "cmp"),
        (re.compile(r"cardiovascular_EvePanel_TRANSFORMED\.csv$", re.I), "cardio"),
        (re.compile(r"immune_EvePanel_TRANSFORMED\.csv$", re.I), "immune_eve"),
    ],
    "656": [(re.compile(r"urine[._]immune[._]AlamarPanel_TRANSFORMED\.csv$", re.I), "urine")],
    "569": [(re.compile(r"CBC_TRANSFORMED\.csv$", re.I), "cbc")],
}

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

def fetch_json(url: str):
    req=urllib.request.Request(url, headers={"User-Agent":"ARC-IHB-source-verification/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())

def download(url: str, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    req=urllib.request.Request(url, headers={"User-Agent":"ARC-IHB-source-verification/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r, dst.open("wb") as f:
        while True:
            b=r.read(1024*1024)
            if not b: break
            f.write(b)

def enumerate_osdr_files(num: str):
    data=fetch_json(API.format(num=num))
    out=[]
    for _,study in data.get("studies",{}).items():
        out.extend(study.get("study_files",[]))
    return out

def find_and_download(root: Path):
    records=[]
    for num, patterns in WANTED.items():
        all_files=enumerate_osdr_files(num)
        for rx,prefix in patterns:
            matches=[f for f in all_files if rx.search(str(f.get("file_name","")))]
            if not matches:
                raise RuntimeError(f"OSD-{num}: no file matched {rx.pattern}")
            # Prefer an exact transformed CSV; if version metadata duplicates it,
            # use the first unique remote URL and record all ambiguity explicitly.
            seen=set(); uniq=[]
            for f in matches:
                u=f.get("remote_url")
                if u and u not in seen:
                    seen.add(u); uniq.append(f)
            if len(uniq) != 1:
                raise RuntimeError(f"OSD-{num} {prefix}: expected 1 unique match, got {len(uniq)}: {[x.get('file_name') for x in uniq]}")
            f=uniq[0]
            remote=str(f["remote_url"])
            url=remote if remote.startswith("http") else "https://osdr.nasa.gov"+remote
            name=str(f.get("file_name") or Path(remote).name)
            dst=root/f"OSD-{num}"/name
            download(url,dst)
            records.append({"osd":f"OSD-{num}","prefix":prefix,"file_name":name,"remote_url":remote,
                            "declared_size":f.get("file_size"),"downloaded_size":dst.stat().st_size,
                            "sha256":sha256(dst),"local_path":str(dst)})
            print(f"Downloaded OSD-{num} {prefix}: {name} ({dst.stat().st_size/1e6:.2f} MB)")
    return records

def parse_sample(s):
    m=SAMPLE_RE.search(str(s))
    if not m: return None,None
    return m.group(1).upper(),m.group(2).upper().replace("R+","R+")

def load_source(path: Path, prefix: str):
    df=pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    sample_col="Sample ID" if "Sample ID" in df.columns else "Sample Name" if "Sample Name" in df.columns else df.columns[0]
    parsed=df[sample_col].apply(parse_sample)
    df=df.copy(); df["subject"]=[x[0] for x in parsed]; df["timepoint"]=[x[1] for x in parsed]
    df=df[df["subject"].isin(SUBJECTS) & df["timepoint"].isin(TPS)].copy()
    drop={sample_col,"subject","timepoint","spaceflight","_modality","Unnamed: 2"}
    feat=df.drop(columns=[c for c in df.columns if c in drop or "Unnamed" in str(c)], errors="ignore")
    feat=feat.apply(pd.to_numeric, errors="coerce").dropna(axis=1,how="all")
    feat=feat.loc[:,~feat.columns.duplicated()]
    feat.columns=[f"{prefix}__{c}" for c in feat.columns]
    idx=df[["subject","timepoint"]].reset_index(drop=True); feat=feat.reset_index(drop=True)
    out=pd.concat([idx,feat],axis=1).drop_duplicates(["subject","timepoint"],keep="first")
    return out.set_index(["subject","timepoint"])

def build_master(records):
    parts=[]
    for r in records:
        parts.append(load_source(Path(r["local_path"]),r["prefix"]))
    master=parts[0]
    for p in parts[1:]: master=master.join(p,how="outer",lsuffix="",rsuffix="_dup")
    master=master.loc[:,~master.columns.str.endswith("_dup")]
    master=master.loc[:,~master.columns.duplicated()]
    grid=pd.MultiIndex.from_product([SUBJECTS,TPS],names=["subject","timepoint"])
    return master.reindex(grid)

def get_fastpass(path: Path):
    if not path.exists(): download(FASTPASS_URL,path)
    f=pd.read_csv(path,low_memory=False)
    return f.set_index(["subject","timepoint"])

def compare(source, fast):
    common=[c for c in source.columns if c in fast.columns]
    only_source=sorted(set(source.columns)-set(fast.columns))
    only_fast=sorted(set(fast.columns)-set(source.columns))
    rows=[]; mismatch_examples=[]
    total_numeric=0; close_numeric=0; missing_match=0; missing_total=0; max_abs=0.0
    for c in common:
        a=pd.to_numeric(source[c],errors="coerce")
        b=pd.to_numeric(fast[c],errors="coerce")
        miss=(a.isna()==b.isna()); missing_match+=int(miss.sum()); missing_total+=len(miss)
        both=a.notna() & b.notna(); n=int(both.sum()); total_numeric+=n
        if n:
            av=a[both].to_numpy(float); bv=b[both].to_numpy(float)
            cl=np.isclose(av,bv,rtol=1e-10,atol=1e-12,equal_nan=True)
            close_numeric+=int(cl.sum())
            diff=np.abs(av-bv); max_abs=max(max_abs,float(diff.max()))
            if not cl.all() and len(mismatch_examples)<25:
                bad=np.where(~cl)[0]
                idxs=a[both].index
                for j in bad[:3]:
                    mismatch_examples.append({"feature":c,"subject":idxs[j][0],"timepoint":idxs[j][1],
                                              "nasa":float(av[j]),"fastpass":float(bv[j]),"abs_diff":float(diff[j])})
    return {
        "source_columns":len(source.columns),"fastpass_columns":len(fast.columns),"overlap_columns":len(common),
        "source_only_columns":only_source,"fastpass_only_column_count":len(only_fast),
        "numeric_cells_compared":total_numeric,"numeric_cells_equal_within_tolerance":close_numeric,
        "numeric_match_fraction":(close_numeric/total_numeric if total_numeric else None),
        "missingness_cells_compared":missing_total,"missingness_match_fraction":(missing_match/missing_total if missing_total else None),
        "max_abs_numeric_difference":max_abs,"mismatch_examples":mismatch_examples,
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--workdir",default="counterfactual/inspiration4/nasa_source")
    ap.add_argument("--outdir",default="counterfactual/inspiration4/source_verification")
    args=ap.parse_args(); work=Path(args.workdir); out=Path(args.outdir); out.mkdir(parents=True,exist_ok=True)
    records=find_and_download(work)
    source=build_master(records); source.to_csv(out/"NASA_OSDR_source_master.csv")
    fast_path=out/"fastpass_reference.csv"; fast=get_fastpass(fast_path)
    report=compare(source,fast)
    report["nasa_files"]=records; report["fastpass_reference_url"]=FASTPASS_URL; report["fastpass_sha256"]=sha256(fast_path)
    (out/"source_comparison.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("nasa_files","source_only_columns","mismatch_examples")},indent=2))
    if report["overlap_columns"] < 100: raise SystemExit("Too few overlapping source columns; verification failed")
    if report["numeric_match_fraction"] is None or report["numeric_match_fraction"] < 0.999:
        raise SystemExit("Source values do not sufficiently reproduce fast-pass harmonization")

if __name__=="__main__": main()
