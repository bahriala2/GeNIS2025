import json, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"savefig.dpi":300,"font.size":9,"axes.grid":True,"grid.alpha":.3,
                     "axes.axisbelow":True,"figure.facecolor":"white","savefig.bbox":"tight"})
R=json.load(open('article1_results.json')); M=R['models']; OUT="figures"; S=[1,2,3,4,5]
CN=R['slice60']['classes']
def agg(m,t,k="macro_f1"):
    v=[M[f"{m}|{t}|strat_seed{s}"][k] for s in S if f"{m}|{t}|strat_seed{s}" in M]
    return float(np.mean(v)) if v else np.nan

# ---------- Fig 1 : capture timeline (Gantt) ----------
W={r['classe']:r for r in R['activity_windows']}
order=sorted(CN,key=lambda c:W[c]['debut (h)'])
fig,ax=plt.subplots(figsize=(8.6,3.4))
for i,c in enumerate(order):
    w=W[c]; span=max(w['fin (h)']-w['debut (h)'],.35)
    ben = c=="benign"
    ax.barh(i,span,left=w['debut (h)'],height=.55,
            color="#55A868" if ben else "#C44E52",alpha=.9,zorder=3)
    ax.text(w['fin (h)']+2,i,f"{w['flux']:,} flows · {w['duree active (h)']:.2f} h active"
            f"{' · '+str(w['fenetres'])+' windows' if w['fenetres']>1 else ''}",
            va="center",fontsize=6.8)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order,fontsize=8)
ax.set_ylim(-.7,len(order)-.05)
ax.set_xlim(-3,205); ax.set_xlabel("hours since start of capture (6 to 12 February 2025)")
ax.axvspan(56,96.2,color="#999999",alpha=.13,zorder=1)
ax.text(76,len(order)-1.35,"40 h with no\nlabelled traffic",ha="center",fontsize=7,color="#555555")
ax.set_title("Capture windows are narrow and mutually disjoint",fontsize=10)
plt.tight_layout(); plt.savefig(f"{OUT}/fig1_timeline.pdf"); plt.savefig(f"{OUT}/fig1_timeline.png"); plt.close()

# ---------- Fig 3 : per-family F1 vs interval ----------
IV=["5","10","30","60"]
det=np.full((len(CN),4),np.nan)
for j,iv in enumerate(IV):
    if iv=="60":
        pcf=M["lightgbm|audited|strat_seed1"]["per_class_f1"]
    else:
        ps=[r["per_class_f1"] for k,r in R["intervals"][iv]["runs"].items() if k.startswith("lightgbm")]
        pcf={c:float(np.mean([p[c] for p in ps])) for c in CN}
    for i,c in enumerate(CN): det[i,j]=pcf.get(c,np.nan)
fig,ax=plt.subplots(figsize=(5.4,3.8))
im=ax.imshow(det,aspect="auto",vmin=.6,vmax=1,cmap="viridis")
ax.set_xticks(range(4)); ax.set_xticklabels([f"{i} s" for i in IV])
ax.set_yticks(range(len(CN))); ax.set_yticklabels(CN,fontsize=8)
for i in range(len(CN)):
    for j in range(4):
        if not np.isnan(det[i,j]):
            ax.text(j,i,f"{det[i,j]:.3f}",ha="center",va="center",fontsize=6.8,
                    color="white" if det[i,j]<.83 else "black")
plt.colorbar(im,label="per-class F1 (LightGBM, audited)")
ax.set_xlabel("flow aggregation interval")
ax.set_title("Per-family detectability across aggregation intervals",fontsize=10)
plt.tight_layout(); plt.savefig(f"{OUT}/fig3_interval_heatmap.pdf"); plt.savefig(f"{OUT}/fig3_interval_heatmap.png"); plt.close()

# ---------- Fig 6 : per-class F1 across models ----------
ORD=["xgboost","lightgbm","rf","ftt","logreg","rnn","cnn","dnn","knn","nb"]
NICE={"xgboost":"XGBoost","lightgbm":"LightGBM","rf":"RF","ftt":"FT-Tr.","logreg":"LogReg",
      "rnn":"RNN","cnn":"CNN","dnn":"DNN","knn":"$k$-NN","nb":"NB"}
Mx=np.array([[M[f"{m}|audited|strat_seed1"]["per_class_f1"][c] for m in ORD] for c in CN])
fig,ax=plt.subplots(figsize=(7.2,3.8))
im=ax.imshow(Mx,aspect="auto",vmin=0,vmax=1,cmap="RdYlGn")
ax.set_xticks(range(len(ORD))); ax.set_xticklabels([NICE[m] for m in ORD],rotation=30,ha="right",fontsize=8)
ax.set_yticks(range(len(CN))); ax.set_yticklabels(CN,fontsize=8)
for i in range(len(CN)):
    for j in range(len(ORD)):
        ax.text(j,i,f"{Mx[i,j]:.2f}",ha="center",va="center",fontsize=6.3,
                color="black" if Mx[i,j]>.35 else "white")
plt.colorbar(im,label="per-class F1")
ax.set_title("Per-class F1, audited condition (seed 1)",fontsize=10)
plt.tight_layout(); plt.savefig(f"{OUT}/fig6_per_class_f1.pdf"); plt.savefig(f"{OUT}/fig6_per_class_f1.png"); plt.close()

# ---------- Fig 8 : transferability scatter ----------
T=R['audit']['transfer_table']; ch=R['audit']['chance']
DUP={"Dur","RunTime","Mean","Sum","Min","Max"}
fig,ax=plt.subplots(figsize=(6.0,4.8))
xs=np.linspace(0,1.04,60)
ax.fill_between(xs,.5*xs,.7*xs,color="#DD8452",alpha=.16,zorder=1,
                label="grey zone ($0.5\\leq\\tau\\leq0.7$)")
seen=False
for r in T:
    x,y=r['acc seule (stratifie)'],r['acc seule (temporel)']
    if r['feature'] in DUP:
        if seen: continue
        seen=True
        ax.scatter(x,y,s=105,color="#C44E52",zorder=5,edgecolor="k",linewidth=.6)
        ax.annotate("Dur = RunTime = Mean = Sum = Min = Max\n(six numerically identical columns)",
                    (x,y),fontsize=7,xytext=(-30,-46),textcoords="offset points",
                    color="#8c3339",ha="right",
                    arrowprops=dict(arrowstyle="->",color="#8c3339",lw=.8))
        continue
    sh=r['raccourci']=="OUI"
    ax.scatter(x,y,s=52 if sh else 20,color="#C44E52" if sh else "#4C72B0",
               zorder=4 if sh else 2,edgecolor="k" if sh else "none",linewidth=.6 if sh else 0)
    if sh:
        ax.annotate(r['feature'],(x,y),fontsize=7.5,xytext=(-8,9),
                    textcoords="offset points",color="#8c3339",ha="right")
ax.plot(xs,xs,"k--",lw=.8,label="perfect transfer ($\\tau=1$)",zorder=3)
ax.plot(xs,.5*xs,color="#C44E52",ls="-.",lw=1.0,label="exclusion threshold ($\\tau=0.5$)",zorder=3)
ax.axhline(ch,color="gray",ls=":",lw=.8,zorder=1)
ax.axvline(3*ch,color="gray",ls=":",lw=.8,zorder=1)
ax.text(1.02,ch+.015,"chance",fontsize=6.8,color="gray",ha="right")
ax.text(3*ch+.012,.86,"$3\\times$ chance",fontsize=6.8,color="gray",rotation=90,va="top")
ax.set_xlim(0,1.06); ax.set_ylim(0,1.06)
ax.set_xlabel("single-feature accuracy — stratified split")
ax.set_ylabel("single-feature accuracy — temporal split")
ax.set_title("Every excluded feature belongs to a family of near-duplicates",fontsize=10)
ax.legend(fontsize=7.5,loc="upper left",framealpha=.95)
plt.tight_layout(); plt.savefig(f"{OUT}/fig8_transferability.pdf"); plt.savefig(f"{OUT}/fig8_transferability.png"); plt.close()
print("regenerated fig1, fig3, fig6, fig8 in English")
