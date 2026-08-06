import json, numpy as np, os
R=json.load(open('article1_results.json')); M=R['models']; T="tables"
os.makedirs(T,exist_ok=True); S=[1,2,3,4,5]
def agg(m,tag,k="macro_f1"):
    v=[M[f"{m}|{tag}|strat_seed{s}"][k] for s in S if f"{m}|{tag}|strat_seed{s}" in M]
    return (float(np.mean(v)),float(np.std(v))) if v else (np.nan,np.nan)
def one(m,tag,sp,k="macro_f1"): return M.get(f"{m}|{tag}|{sp}",{}).get(k,np.nan)
def f4(x): return "--" if (x is None or (isinstance(x,float) and np.isnan(x))) else f"{x:.4f}"
ORDER=["xgboost","lightgbm","rf","ftt","logreg","rnn","cnn","dnn","knn","nb","majority"]
NICE={"xgboost":"XGBoost","lightgbm":"LightGBM","rf":"Random forest","ftt":"FT-Transformer",
      "logreg":"Logistic reg.","rnn":"RNN","cnn":"1D CNN","dnn":"DNN","knn":"$k$-NN",
      "nb":"Naive Bayes","majority":"Majority class"}

# T1 intervals
rows=[]
for iv in ["5","10","30","60"]:
    s=R['interval_stats'][iv]
    pr=R['intervals'].get(iv,{}).get('probe_starttime') if iv!="60" else R['shortcut_probes']['starttime_only']['strat_mean']
    rows.append(f"{iv}\\,s & {s['total']:,} & {s['benign']:,} & {s['benign_share']*100:.2f} & {pr:.4f} \\\\")
open(f"{T}/t1_intervals.tex","w").write("\n".join(rows).replace(",","\\,"))

# T2 main
rows=[]
for m in ORDER:
    a=agg(m,"audited"); t=agg(m+"#tuned","audited")
    fpr=M.get(f"{m}|audited|strat_seed1",{}).get("binary",{}).get("fpr")
    rows.append(f"{NICE[m]} & {f4(one(m,'full','strat_seed1'))} & {f4(one(m,'clean','strat_seed1'))} & "
                f"{f4(a[0])}\\,$\\pm$\\,{a[1]:.4f} & {f4(t[0])} & "
                f"{f4(one(m,'audited','temporal'))} & {f4(one(m,'audited','strat_seed1','mcc'))} & "
                f"{('%.4f'%(fpr*100)) if fpr is not None else '--'} \\\\")
open(f"{T}/t2_main.tex","w").write("\n".join(rows))

# T3 blacklist / transferability
Tt={r['feature']:r for r in R['audit']['transfer_table']}
rows=[]
for f in ["StartTime","LastTime","Rank","Seq"]:
    rows.append(f"\\texttt{{{f}}} & positional & -- & -- & -- & by construction \\\\")
for f in ["Dur","RunTime","Mean","Sum","Min","Max","SIntPktMax","SIntPkt"]:
    r=Tt[f]
    rows.append(f"\\texttt{{{f}}} & behavioural & {r['importance']:.4f} & "
                f"{r['acc seule (stratifie)']:.3f} & {r['acc seule (temporel)']:.3f} & {r['transferabilite']:.2f} \\\\")
open(f"{T}/t3_blacklist.tex","w").write("\n".join(rows))

# T4 cost
rows=[]
for m in ORDER:
    c=R['cost'].get(m)
    if not c: continue
    a=agg(m,"audited")[0]
    rows.append(f"{NICE[m]} & {c['lat_p50_ms']:.2f} & {c['lat_p99_ms']:.2f} & "
                f"{c['throughput_512']:,.0f} & {c['size_mb']:.2f} & {f4(a)} \\\\".replace(",","\\,"))
open(f"{T}/t4_cost.tex","w").write("\n".join(rows))

# T5 calibration + hpo
rows=[]
for m in ORDER:
    c=R['calibration'].get(m); h=R['hpo'].get(m)
    if not c: continue
    rows.append(f"{NICE[m]} & {c['T']:.3f} & {c['ece_before']:.4f} & {c['ece_after']:.4f} & "
                f"{h['n_trials'] if h else '--'} & {h['search_time_s']:.0f} & "
                f"{h['best_val_macro_f1']-h['default_val_macro_f1']:+.4f} \\\\" if h else
                f"{NICE[m]} & {c['T']:.3f} & {c['ece_before']:.4f} & {c['ece_after']:.4f} & -- & -- & -- \\\\")
open(f"{T}/t5_calib_hpo.tex","w").write("\n".join(rows))

# T6 autoencoder
fam={}
for v in R['autoencoder'].values():
    for k,x in v['auroc_per_family'].items(): fam.setdefault(k,[]).append(x)
rows=[f"\\texttt{{{k}}} & {np.mean(v):.4f} & {np.std(v):.4f} \\\\"
      for k,v in sorted(fam.items(),key=lambda kv:np.mean(kv[1]))]
g=[v['auroc_global'] for v in R['autoencoder'].values()]
rows.append(f"\\midrule\n\\textbf{{all attacks}} & \\textbf{{{np.mean(g):.4f}}} & {np.std(g):.4f} \\\\")
open(f"{T}/t6_autoencoder.tex","w").write("\n".join(rows))

# T7 intervals x models
rows=[]
for iv in ["5","10","30","60"]:
    cells=[]
    for mod in ["lightgbm","xgboost","dnn"]:
        if iv=="60":
            v=agg(mod,"audited"); cells.append(f"{v[0]:.4f}\\,$\\pm$\\,{v[1]:.4f}")
        else:
            vv=[r['macro_f1'] for k,r in R['intervals'][iv]['runs'].items() if k.startswith(mod)]
            cells.append(f"{np.mean(vv):.4f}\\,$\\pm$\\,{np.std(vv):.4f}")
    rows.append(f"{iv}\\,s & {R['interval_stats'][iv]['benign_share']*100:.2f} & "+" & ".join(cells)+" \\\\")
open(f"{T}/t7_intervals_models.tex","w").write("\n".join(rows))
print("tables:",sorted(os.listdir(T)))
for f in sorted(os.listdir(T)):
    print("\n---",f); print(open(f"{T}/{f}").read()[:400])


# RSTRIP_LAST_ROW : les fragments sont \input dans un tabular ; TeX ne produit pas
# le \cr final quand un fichier \input se termine par "\\". Le "\\" de la derniere
# ligne est donc ecrit par main.tex, juste apres le \input.
import glob as _g, re as _re
for _f in _g.glob(f"{T}/*.tex"):
    _s = open(_f).read().rstrip()
    open(_f, "w").write(_re.sub(r"\\\\\\s*\\Z", "", _s).rstrip() + "\n")
