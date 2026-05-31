#!/usr/bin/env python3
"""
IHB Deep Phenotyping Framework - Demonstration on Proxy Data
NASA Artemis II Human Research Data Methodology Challenge
Autonomic Resilience Collective | Buckingham & Johnson, 2026

Runs end-to-end on oura_data_studyday.csv (study_day, hrv_rmssd).
Study day is indexed to event onset (Day 0); no calendar dates are used,
which protects subject privacy while leaving every statistic unchanged.
Outputs (figures + phase table) are written to outputs/.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

DATA_FILE = "oura_data_studyday.csv"
OUTDIR = "outputs"
os.makedirs(OUTDIR, exist_ok=True)

# Event onset = study day 0. Gestation = 299 days (from last menstrual period).
GEST = 299
FREEZE_DAY = 709          # publication freeze: study day for 2026-02-27
LMP_DAY = -GEST           # last menstrual period, relative to onset

INK="#1B3A5C"; ACC="#2C7FB8"; POS="#2E8B57"; NEG="#C0504D"; GOLD="#E8A33D"
plt.rcParams.update({"figure.facecolor":"white","axes.facecolor":"white","savefig.facecolor":"white",
 "font.family":"DejaVu Sans","axes.grid":True,"grid.color":"#E6E6E6","grid.linewidth":0.8,"font.size":11})

df = pd.read_csv(DATA_FILE).sort_values("study_day").reset_index(drop=True)
d = df[df["study_day"] <= FREEZE_DAY].copy()
valid = int(d["hrv_rmssd"].notna().sum())

# Phase boundaries in study-day units (standard clinical boundaries: trimesters, postpartum intervals, weaning)
PHASES = [
    ("Pre-event baseline", d["study_day"].min(), LMP_DAY),
    ("First trimester",    LMP_DAY,        LMP_DAY+91),
    ("Second trimester",   LMP_DAY+91,     LMP_DAY+182),
    ("Third trimester",    LMP_DAY+182,    0),
    ("Early postpartum",   0,              91),
    ("Mid postpartum",     91,             182),
    ("Post-weaning",       182,            365),
    ("Late postpartum",    365,            FREEZE_DAY+1),
]
rows=[]
for name, lo, hi in PHASES:
    s = d[(d["study_day"]>=lo)&(d["study_day"]<hi)]["hrv_rmssd"].dropna()
    ci = 1.96*s.std(ddof=1)/np.sqrt(len(s))
    rows.append({"phase":name,"n":len(s),"mean_ms":round(s.mean(),1),
                 "sd_ms":round(s.std(ddof=1),1),
                 "ci_low":round(s.mean()-ci,1),"ci_high":round(s.mean()+ci,1)})
summary = pd.DataFrame(rows)
BASE = summary.loc[0,"mean_ms"]; BSD = summary.loc[0,"sd_ms"]
summary["pct_vs_baseline"] = round((summary["mean_ms"]-BASE)/BASE*100,1)
summary.to_csv(os.path.join(OUTDIR,"IHB_phase_summary.csv"), index=False)

pb = d[(d["study_day"]>=-14)&(d["study_day"]<0)]["hrv_rmssd"].dropna()
print(f"Valid nights (frozen window): {valid}")
print(summary.to_string(index=False))
print(f"\nPre-event 14d window: N={len(pb)} mean={pb.mean():.1f} "
      f"(+{(pb.mean()-BASE)/BASE*100:.1f}%) peak={pb.max():.0f} (+{(pb.max()-BASE)/BASE*100:.0f}%)")
print(f"Late-PP supercompensation: {summary.iloc[-1].mean_ms} ms (+{summary.iloc[-1].pct_vs_baseline}%)")

# 7-day moving average over study-day (visualization only; no interpolation)
ser = d.set_index("study_day")["hrv_rmssd"]
sma = ser.rolling(7, min_periods=3).mean()

# FIG 1 - full trajectory
fig,ax=plt.subplots(figsize=(12,4.6))
bands=["#EEF2F6","#FBEFD6","#F6E2C8","#F0D2C0","#E9D6D0","#DCE7DC","#CFE3CF","#C2E0C8"]
for (name,lo,hi),c in zip(PHASES,bands): ax.axvspan(lo,min(hi,FREEZE_DAY),color=c,zorder=0)
ax.scatter(d["study_day"],d["hrv_rmssd"],s=5,color=ACC,alpha=0.35,zorder=2,label="Nightly rMSSD")
ax.plot(sma.index,sma.values,color=INK,lw=1.6,zorder=3,label="7-day moving average")
ax.axhline(BASE,ls="--",lw=1.3,color="#555",zorder=3,label=f"Individualized baseline ({BASE:.1f} ms)")
ax.axvline(0,color=GOLD,lw=2,zorder=4); ax.text(0,ax.get_ylim()[1]*0.97,"  Event onset (Day 0)",color="#9A6B12",fontsize=9,va="top",fontweight="bold")
ax.set_ylabel("HRV  rMSSD (ms)"); ax.set_xlabel("Study day (Day 0 = event onset)")
ax.set_title("IHB Deep Phenotyping: 65-Month Longitudinal Trajectory",fontweight="bold",color=INK,fontsize=12)
ax.legend(loc="upper left",framealpha=0.9,fontsize=8.5,ncol=2); ax.margins(x=0.01)
fig.tight_layout(); fig.savefig(f"{OUTDIR}/01_full_trajectory.png",dpi=160); plt.close()

# FIG 2 - phase deviations
fig,ax=plt.subplots(figsize=(11,4.8))
cols=[POS if v>=0 else NEG for v in summary["pct_vs_baseline"]]
ax.bar(range(len(summary)),summary["pct_vs_baseline"],color=cols,edgecolor="white",width=0.72); ax.axhline(0,color="#555",lw=1.1,ls="--")
for i,(v,n) in enumerate(zip(summary["pct_vs_baseline"],summary["n"])):
    ax.text(i,v+(1.2 if v>=0 else -1.2),f"{v:+.1f}%\n(n={n})",ha="center",va="bottom" if v>=0 else "top",fontsize=8.5)
ax.set_xticks(range(len(summary))); ax.set_xticklabels(summary["phase"],rotation=25,ha="right",fontsize=9)
ax.set_ylabel("Deviation from individual baseline (%)")
ax.set_title("IHB Phase Deviation Scores  (each bar = deviation from the subject's own baseline)",fontweight="bold",color=INK,fontsize=11.5)
ax.legend(handles=[Patch(color=POS,label="Above individual baseline"),Patch(color=NEG,label="Below individual baseline")],loc="upper left",fontsize=9); ax.margins(y=0.18)
fig.tight_layout(); fig.savefig(f"{OUTDIR}/02_phase_deviations.png",dpi=160); plt.close()

# FIG 3 - anomaly detection window
win=d[(d["study_day"]>=-25)&(d["study_day"]<0)].dropna(subset=["hrv_rmssd"]).copy()
win["z"]=(win["hrv_rmssd"]-BASE)/BSD
fig,(a1,a2)=plt.subplots(2,1,figsize=(11,6.4),sharex=True,gridspec_kw={"height_ratios":[1.25,1]})
a1.axhspan(BASE-2*BSD,BASE+2*BSD,color="#EEF2F6",label="Individual ±2 SD band")
a1.axhline(BASE,ls="--",color="#555",lw=1.2,label=f"Individual baseline ({BASE:.1f} ms)")
a1.scatter(win["study_day"],win["hrv_rmssd"],c=[POS if z>2 else ACC for z in win["z"]],s=42,zorder=3)
a1.plot(win["study_day"],win["hrv_rmssd"],color=INK,lw=1.4,zorder=2); a1.axvline(0,color=GOLD,lw=2)
a1.set_ylabel("HRV rMSSD (ms)"); a1.set_title("IHB Anomaly Detection: Pre-Event Window  |  Subject-Specific Deviation Scoring",fontweight="bold",color=INK,fontsize=11.5); a1.legend(loc="upper left",fontsize=8.5)
a2.bar(win["study_day"],win["z"],color=[POS if z>2 else(NEG if z<-2 else ACC) for z in win["z"]],width=0.7)
a2.axhline(0,color="#555",lw=1); a2.axhline(2,ls=":",color=POS,lw=1.2); a2.axhline(-2,ls=":",color=NEG,lw=1.2); a2.axvline(0,color=GOLD,lw=2)
a2.set_ylabel("Deviation (individual SD)"); a2.set_xlabel("Days relative to event onset (Day 0)")
fig.tight_layout(); fig.savefig(f"{OUTDIR}/03_anomaly_detection_window.png",dpi=160); plt.close()

# FIG 4 - recovery trajectory
post=d[d["study_day"]>=0].dropna(subset=["hrv_rmssd"]).copy()
ps=post.set_index("study_day")["hrv_rmssd"].rolling(7,min_periods=3).mean()
fig,ax=plt.subplots(figsize=(12,4.6))
ax.scatter(post["study_day"],post["hrv_rmssd"],s=5,color=ACC,alpha=0.3,label="Nightly rMSSD")
ax.plot(ps.index,ps.values,color=INK,lw=1.7,label="7-day moving average"); ax.axhline(BASE,ls="--",color="#555",lw=1.3,label=f"Individual baseline ({BASE:.1f} ms)")
ax.fill_between(ps.index,BASE,ps.values,where=(ps.values>=BASE),color=POS,alpha=0.25,label="Above baseline (supercompensation)")
ax.fill_between(ps.index,BASE,ps.values,where=(ps.values<BASE),color=NEG,alpha=0.22,label="Below baseline")
ax.set_xlabel("Days post-event onset"); ax.set_ylabel("HRV rMSSD (ms)")
ax.set_title("IHB Recovery Trajectory: Return to and Beyond Individual Baseline",fontweight="bold",color=INK,fontsize=12)
ax.legend(loc="upper left",fontsize=8.5,ncol=2); ax.margins(x=0.01)
fig.tight_layout(); fig.savefig(f"{OUTDIR}/04_recovery_trajectory.png",dpi=160); plt.close()

# FIG 5 - continued recovery extension (full export beyond freeze)
last=df["study_day"].max()
def wm(days):
    x=df[df["study_day"]>last-days]["hrv_rmssd"].dropna(); return len(x),x.mean()
latepp=summary.iloc[-1].mean_ms
n180,m180=wm(180); n90,m90=wm(90); n30,m30=wm(30)
labels=["Pre-event\nbaseline","Late postpartum\n(publication)","Recent 180d","Recent 90d","Recent 30d"]
vals=[BASE,latepp,round(m180,1),round(m90,1),round(m30,1)]
ns=[summary.loc[0,"n"],summary.iloc[-1].n,n180,n90,n30]
cl=["#9aa7b3","#2E8B57","#3f9e6a","#2C7FB8","#1B3A5C"]
fig,ax=plt.subplots(figsize=(11,4.6))
ax.bar(range(len(vals)),vals,color=cl,edgecolor="white",width=0.66); ax.axhline(BASE,ls="--",color="#777",lw=1.1)
for i,(v,n) in enumerate(zip(vals,ns)): ax.text(i,v+1.5,f"{v:.1f} ms\n({(v-BASE)/BASE*100:+.0f}%, n={n})",ha="center",va="bottom",fontsize=9)
ax.set_xticks(range(len(vals))); ax.set_xticklabels(labels,fontsize=9.5); ax.set_ylabel("HRV rMSSD (ms)"); ax.set_ylim(0,max(vals)*1.2)
ax.set_title("Continued Recovery: Recent Months vs the 65-Month Baseline",fontweight="bold",color=INK,fontsize=12)
fig.tight_layout(); fig.savefig(f"{OUTDIR}/05_continued_recovery.png",dpi=160); plt.close()

print("\nAll outputs written to", OUTDIR)
