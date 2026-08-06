import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"savefig.dpi":300,"font.size":9,"axes.grid":True,"grid.alpha":.3,
                     "axes.axisbelow":True,"figure.facecolor":"white","savefig.bbox":"tight"})
R=json.load(open('article1_results.json')); M=R['models']; OUT="figures"
SEEDS=[1,2,3,4,5]
def agg(m,tag,k="macro_f1"):
    v=[M[f"{m}|{tag}|strat_seed{s}"][k] for s in SEEDS if f"{m}|{tag}|strat_seed{s}" in M]
    return (float(np.mean(v)),float(np.std(v))) if v else (np.nan,np.nan)
def one(m,tag,sp,k="macro_f1"): return M.get(f"{m}|{tag}|{sp}",{}).get(k,np.nan)

STRONG=["logreg","knn","rf","xgboost","lightgbm","rnn","cnn","dnn","ftt"]
CONDS=[("full\n(strat.)",lambda m:one(m,"full","strat_seed1")),
       ("clean\n(strat.)",lambda m:one(m,"clean","strat_seed1")),
       ("audited\n(strat., 5 seeds)",lambda m:agg(m,"audited")[0]),
       ("clean\n(temporal)",lambda m:one(m,"clean","temporal")),
       ("audited\n(temporal)",lambda m:one(m,"audited","temporal"))]

# ---- Figure 2 : two panels, zoomed ----
fig,axes=plt.subplots(1,2,figsize=(9.4,4.0),gridspec_kw={"width_ratios":[3,1]})
ax=axes[0]; cm=plt.get_cmap("tab10")
for i,m in enumerate(STRONG):
    ys=[f(m) for _,f in CONDS]
    ax.plot(range(5),ys,marker="o",ms=4.5,lw=1.4,label=m,color=cm(i%10))
    ax.annotate(m,(4,ys[4]),fontsize=7,xytext=(6,-2),textcoords="offset points",color=cm(i%10))
ax.set_xticks(range(5)); ax.set_xticklabels([c for c,_ in CONDS],fontsize=8)
ax.set_ylim(.965,1.0015); ax.set_ylabel("macro-F1")
ax.set_xlim(-.25,4.9)
ax.set_title("(a) supervised detectors (zoom)",fontsize=10)
ax.axvspan(-.25,2.5,color="#4C72B0",alpha=.05)
ax.axvspan(2.5,4.9,color="#C44E52",alpha=.05)
ax.text(1.1,.9663,"stratified protocol",fontsize=7.5,color="#31527d",ha="center")
ax.text(3.6,.9663,"temporal protocol",fontsize=7.5,color="#8c3339",ha="center")
ax2=axes[1]
for m,c in [("nb","#DD8452"),("majority","#8C8C8C")]:
    ax2.plot(range(5),[f(m) for _,f in CONDS],marker="o",ms=4.5,lw=1.4,label=m,color=c)
ax2.set_xticks(range(5)); ax2.set_xticklabels(["f/s","c/s","a/s","c/t","a/t"],fontsize=8)
ax2.set_ylim(0,.8); ax2.set_title("(b) weak baselines",fontsize=10); ax2.legend(fontsize=8)
fig.suptitle("Model ranking across feature conditions and evaluation protocols (60 s slice)",fontsize=11)
plt.tight_layout(); plt.savefig(f"{OUT}/fig2_before_after.pdf"); plt.savefig(f"{OUT}/fig2_before_after.png"); plt.close()

# ---- Figure 7 : ranking with CI, zoomed ----
bt=R['stats']['bootstrap']; ms=[m for m in sorted(bt,key=lambda m:bt[m]['macro_f1_mean']) if m!="nb"]
mu=[bt[m]['macro_f1_mean'] for m in ms]
lo=[mu[i]-bt[m]['macro_f1_ci95'][0] for i,m in enumerate(ms)]
hi=[bt[m]['macro_f1_ci95'][1]-mu[i] for i,m in enumerate(ms)]
fig,ax=plt.subplots(figsize=(5.6,3.3))
ax.errorbar(mu,range(len(ms)),xerr=[lo,hi],fmt="o",ms=5,capsize=3,color="#4C72B0")
ax.set_yticks(range(len(ms))); ax.set_yticklabels(ms)
ax.set_xlabel("macro-F1 (95 % bootstrap CI, audited condition, seed 1)")
ax.set_xlim(.993,1.0006)
ax.set_title("Stratified ranking: the top group is statistically indistinguishable",fontsize=10)
plt.tight_layout(); plt.savefig(f"{OUT}/fig7_ranking_ci.pdf"); plt.savefig(f"{OUT}/fig7_ranking_ci.png"); plt.close()

# ---- Figure 9 : transferability spectrum ----
T=sorted(R['audit']['transfer_table'],key=lambda r:r['transferabilite'])
fig,ax=plt.subplots(figsize=(9.2,3.2))
cols=["#C44E52" if r['raccourci']=="OUI" else "#4C72B0" for r in T]
ax.bar(range(len(T)),[r['transferabilite'] for r in T],color=cols,width=.8)
ax.axhline(.5,color="k",ls="--",lw=.9,label="blacklist threshold (0.50)")
ax.set_xticks(range(len(T))); ax.set_xticklabels([r['feature'] for r in T],rotation=90,fontsize=5.2)
ax.set_ylabel("transferability\n$acc_{temporal}/acc_{stratified}$")
ax.set_xlim(-.7,len(T)-.3); ax.set_ylim(0,1.15)
ax.annotate("8 features excluded\n(all with zero permutation importance)",(3.5,.36),
            fontsize=7.5,color="#8c3339",ha="left",
            xytext=(11,.20),textcoords="data",
            arrowprops=dict(arrowstyle="->",color="#8c3339",lw=.8))
ax.set_title("Single-feature transferability spectrum (63 behavioural features)",fontsize=10)
ax.legend(fontsize=8,loc="lower right")
plt.tight_layout(); plt.savefig(f"{OUT}/fig9_transferability_spectrum.pdf")
plt.savefig(f"{OUT}/fig9_transferability_spectrum.png"); plt.close()

# ---- Figure 10 (new) : autoencoder per-family AUROC ----
fam={}
for v in R['autoencoder'].values():
    for k,x in v['auroc_per_family'].items(): fam.setdefault(k,[]).append(x)
ks=sorted(fam,key=lambda k:np.mean(fam[k]))
mu=[np.mean(fam[k]) for k in ks]; sd=[np.std(fam[k]) for k in ks]
fig,ax=plt.subplots(figsize=(6.2,3.2))
ax.barh(ks,mu,xerr=sd,color=["#C44E52" if m<.5 else "#55A868" for m in mu],capsize=3)
ax.axvline(.5,color="k",ls="--",lw=.9,label="chance (0.50)")
g=[v['auroc_global'] for v in R['autoencoder'].values()]
ax.axvline(np.mean(g),color="#4C72B0",ls="-.",lw=1.1,label=f"global AUROC {np.mean(g):.3f}")
ax.set_xlabel("AUROC of the benign-trained autoencoder (one-vs-benign)")
ax.set_xlim(0,1); ax.legend(fontsize=8,loc="lower right")
ax.set_title("Reconstruction error is anti-correlated with volumetric floods",fontsize=10)
plt.tight_layout(); plt.savefig(f"{OUT}/fig10_autoencoder.pdf"); plt.savefig(f"{OUT}/fig10_autoencoder.png"); plt.close()

# ---- Figure 5 : cost vs performance ----
fig,ax=plt.subplots(figsize=(6.0,4.0))
for m,c in R['cost'].items():
    if m=="majority": continue
    f1=agg(m,"audited")[0]
    if np.isnan(f1): continue
    deep=m in ("rnn","cnn","dnn","ftt")
    ax.scatter(c['throughput_512'],f1,s=46,color="#C44E52" if deep else "#4C72B0",
               marker="^" if deep else "o",zorder=3)
    ax.annotate(m,(c['throughput_512'],f1),fontsize=7.5,xytext=(6,3),textcoords="offset points")
ax.set_xscale("log"); ax.set_xlabel("CPU throughput (flows/s, batch 512, log scale)")
ax.set_ylabel("macro-F1 (audited, 5 seeds)"); ax.set_ylim(.993,1.0008)
ax.scatter([],[],color="#4C72B0",marker="o",label="classical / tree"); ax.scatter([],[],color="#C44E52",marker="^",label="deep")
ax.legend(fontsize=8,loc="lower left")
ax.set_title("Inference cost versus detection quality",fontsize=10)
plt.tight_layout(); plt.savefig(f"{OUT}/fig5_cost.pdf"); plt.savefig(f"{OUT}/fig5_cost.png"); plt.close()
print("regenerated:", sorted(__import__('os').listdir(OUT)))
