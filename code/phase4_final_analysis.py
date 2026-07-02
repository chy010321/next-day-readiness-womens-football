
#!/usr/bin/env python3
"""Fast Phase 4 final results generator using leakage-audited Phase 3 prediction files."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

PROJECT = Path('/mnt/data/soccermon_nextday_readiness_project')
P3 = PROJECT/'phase3_robustness_results'
OUT = Path('/mnt/data/soccermon_nextday_readiness_phase4')
FIG = OUT/'figures'; TAB=OUT/'tables'; SUP=OUT/'supplementary'
for p in [OUT,FIG,TAB,SUP]:p.mkdir(parents=True,exist_ok=True)

df=pd.read_csv(PROJECT/'soccermon_next_day_readiness_primary_pairs_v1.csv')
df['date']=pd.to_datetime(df['date'])
WELLNESS=['fatigue','mood','sleep_duration','sleep_quality','soreness','stress']
CAL=['day_of_week_num','month']
P2FS=['readiness','daily_load','fatigue','soreness','sleep_duration','sleep_quality']+CAL
SCENS=[
 ('Within Team A: 2020→2021','Within_TeamA_2020_to_2021','TeamA','TeamA'),
 ('Within Team B: 2020→2021','Within_TeamB_2020_to_2021','TeamB','TeamB'),
 ('Cross-team: Team A 2020→Team B 2021','Cross_TeamA2020_to_TeamB2021','TeamA','TeamB'),
 ('Cross-team: Team B 2020→Team A 2021','Cross_TeamB2020_to_TeamA2021','TeamB','TeamA'),
]

def calfrombase(d,base_col,w):
    """Fast cold-start sequential calibration using only forecast dates earlier than current date."""
    x=d.copy()
    x['_idx']=np.arange(len(x))
    x=x.sort_values(['player_id','date']).copy()
    x['_resid']=x['readiness_t1']-x[base_col]
    x['_adj']=x.groupby('player_id',sort=False)['_resid'].transform(lambda s:s.shift(1).rolling(w,min_periods=1).mean().fillna(0.0))
    x['_nh']=x.groupby('player_id',sort=False).cumcount().clip(upper=w)
    x['pred']=x[base_col]+x['_adj']
    return x.sort_values('_idx')[['pred','_nh']].reset_index(drop=True)

def prep(d, fs):
    x=d[fs].copy()
    for c in x:
        if c=='daily_load' or c.startswith('load_mean_') or c.startswith('load_sum_'):x[c]=np.log1p(x[c])
    return x

def p2base(train,test):
    pipe=Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('ridge',Ridge(alpha=10.0))])
    pipe.fit(prep(train,P2FS),train.readiness_t1)
    return pipe.predict(prep(test,P2FS))

def metrics(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float)
    sl,ic=np.polyfit(p,y,1)
    return {'n':int(len(y)),'MAE':float(mean_absolute_error(y,p)),'RMSE':float(mean_squared_error(y,p)**.5),'bias':float(np.mean(p-y)),'R2':float(r2_score(y,p)),'calibration_intercept':float(ic),'calibration_slope':float(sl)}

def boot(d,a,b,seed,nboot=2000):
    g=d.groupby('player_id',sort=False).apply(lambda z:pd.Series({'n':len(z),'aa':np.abs(z.readiness_t1-z[a]).sum(),'bb':np.abs(z.readiness_t1-z[b]).sum()}),include_groups=False)
    pt=g.aa.sum()/g.n.sum()-g.bb.sum()/g.n.sum()
    rng=np.random.default_rng(seed);n=g.n.to_numpy(float);aa=g.aa.to_numpy(float);bb=g.bb.to_numpy(float)
    vals=[]
    for z in range(0,nboot,500):
        k=min(500,nboot-z); ix=rng.integers(0,len(g),size=(k,len(g)))
        vals.append(aa[ix].sum(1)/n[ix].sum(1)-bb[ix].sum(1)/n[ix].sum(1))
    vals=np.concatenate(vals)
    return {'MAE_difference':float(pt),'CI_low':float(np.quantile(vals,.025)),'CI_high':float(np.quantile(vals,.975)),'bootstrap_resamples':int(nboot)}

perfs=[];diffrows=[];p2rows=[];players=[]
for si,(display,slug,src,tgt) in enumerate(SCENS):
    p=pd.read_csv(P3/f'predictions_{slug}.csv')
    p['date']=pd.to_datetime(p['date'])
    # P0 adaptive predictions from saved base; P1 adaptive predictions from saved leakage-audited cold values
    for w in [14,28,56]:
        p0=calfrombase(p,'pred_M0_autoreg',w)
        p[f'P0_w{w}']=p0.pred; p[f'P0_history_w{w}']=p0._nh
        p[f'P1_w{w}']=p[f'pred_M3cold_{w}']
        p[f'P1_history_w{w}']=p[f'n_residuals_cold_{w}']
        for code,label in [('P0','P0 adaptive autoregressive baseline'),('P1','P1 adaptive full-monitoring model')]:
            perfs.append({'scenario':display,'scenario_slug':slug,'model':label,'model_code':code,'residual_window_observations':w,**metrics(p.readiness_t1,p[f'{code}_w{w}'])})
        d=boot(p,f'P1_w{w}',f'P0_w{w}',20260702+si*1000+w)
        diffrows.append({'scenario':display,'scenario_slug':slug,'comparison':'P1 full monitoring − P0 autoregressive','residual_window_observations':w,'subset':'All 2021 eligible observations','test_pairs':len(p),'test_players':p.player_id.nunique(),**d})
        if w==28:
            stable=p[p.P0_history_w28>=28].copy()
            d=boot(stable,'P1_w28','P0_w28',20260702+si*3000)
            diffrows.append({'scenario':display,'scenario_slug':slug,'comparison':'P1 full monitoring − P0 autoregressive','residual_window_observations':w,'subset':'After 28 player-specific residuals','test_pairs':len(stable),'test_players':stable.player_id.nunique(),**d})
            # P2 cal at 28, obtained from original data with exact same training/test split
            tr=df[(df.team==src)&(df.year==2020)].copy();te=df[(df.team==tgt)&(df.year==2021)].copy()
            base2=p2base(tr,te)
            # assure test ordering matches saved prediction file (original data same ordering) 
            assert np.all(te.player_id.to_numpy()==p.player_id.to_numpy())
            q=p[['player_id','date','readiness_t1']].copy();q['p2base']=base2
            p2=calfrombase(q,'p2base',28)
            p['P2_w28']=p2.pred
            dd=boot(p,'P2_w28','P0_w28',20260702+si*4000)
            p2rows.append({'scenario':display,'scenario_slug':slug,'comparison':'P2 reduced monitoring − P0 autoregressive','residual_window_observations':w,'subset':'All 2021 eligible observations','test_pairs':len(p),'test_players':p.player_id.nunique(),**dd})
            # p2 perf
            perfs.append({'scenario':display,'scenario_slug':slug,'model':'P2 adaptive reduced-monitoring model','model_code':'P2','residual_window_observations':w,**metrics(p.readiness_t1,p.P2_w28)})
            gg=p.groupby('player_id',sort=False).apply(lambda z:pd.Series({'n_pairs':len(z),'mae_P0':np.abs(z.readiness_t1-z.P0_w28).mean(),'mae_P1':np.abs(z.readiness_t1-z.P1_w28).mean()}),include_groups=False).reset_index()
            gg['mae_difference_P1_minus_P0']=gg.mae_P1-gg.mae_P0;gg['scenario']=display;gg['scenario_slug']=slug;players.append(gg)
perfs=pd.DataFrame(perfs);diffs=pd.DataFrame(diffrows);p2s=pd.DataFrame(p2rows);players=pd.concat(players,ignore_index=True)
perfs.to_csv(OUT/'phase4_model_performance_full.csv',index=False);diffs.to_csv(OUT/'phase4_window_differences_full.csv',index=False);p2s.to_csv(OUT/'phase4_reduced_monitoring_differences.csv',index=False);players.to_csv(OUT/'phase4_player_level_differences.csv',index=False)

def mediqr(x,d=1):return f"{np.nanmedian(x):.{d}f} [{np.nanpercentile(x,25):.{d}f}, {np.nanpercentile(x,75):.{d}f}]"
columns=[('Team A, 2020','TeamA',2020),('Team A, 2021','TeamA',2021),('Team B, 2020','TeamB',2020),('Team B, 2021','TeamB',2021)]
defs=[
 ('Players contributing eligible pairs',lambda z:str(z.player_id.nunique())),
 ('Eligible player-day pairs',lambda z:f'{len(z):,}'),
 ('Calendar span',lambda z:f'{z.date.min().date()} to {z.date.max().date()}'),
 ('Current-day readiness, median [IQR]',lambda z:mediqr(z.readiness,1)),
 ('Next-day readiness, median [IQR]',lambda z:mediqr(z.readiness_t1,1)),
 ('Daily load (sRPE), median [IQR]',lambda z:mediqr(z.daily_load,0)),
 ('Training days, n (%)',lambda z:f'{int(z.training_day.sum()):,} ({100*z.training_day.mean():.1f})'),
 ('7-day wellness-report rate, median [IQR]',lambda z:mediqr(z.wellness_report_rate_7d,2)),
]
t1=[]
for lab,fn in defs:
    row={'Measure':lab}
    for col,t,y in columns:row[col]=fn(df[(df.team==t)&(df.year==y)])
    if lab=='Players contributing eligible pairs':row['All analytic pairs']=str(df.player_id.nunique())
    elif lab=='Eligible player-day pairs':row['All analytic pairs']=f'{len(df):,}'
    elif lab=='Calendar span':row['All analytic pairs']=f'{df.date.min().date()} to {df.date.max().date()}'
    elif lab.startswith('Current'):row['All analytic pairs']=mediqr(df.readiness,1)
    elif lab.startswith('Next'):row['All analytic pairs']=mediqr(df.readiness_t1,1)
    elif lab.startswith('Daily'):row['All analytic pairs']=mediqr(df.daily_load,0)
    elif lab.startswith('Training'):row['All analytic pairs']=f'{int(df.training_day.sum()):,} ({100*df.training_day.mean():.1f})'
    else:row['All analytic pairs']=mediqr(df.wellness_report_rate_7d,2)
    t1.append(row)
t1=pd.DataFrame(t1)
t2=pd.DataFrame([
 {'Model':'P0: adaptive autoregressive baseline','Population prediction model':'Ridge model using current-day readiness only','Sequential player adaptation':'Mean residual across preceding 28 eligible forecast dates for the same player; cold start in target 2021 period','Role':'Primary comparator'},
 {'Model':'P1: adaptive full-monitoring model','Population prediction model':'Ridge model using readiness; daily and 7-day load; training-day count; fatigue, mood, sleep duration, sleep quality, soreness, stress; weekday/month; reporting density','Sequential player adaptation':'Same 28-observation residual adjustment as P0','Role':'Primary intervention model'},
 {'Model':'P2: adaptive reduced-monitoring model','Population prediction model':'Ridge model using readiness; daily load; fatigue, soreness, sleep duration, sleep quality; weekday/month','Sequential player adaptation':'Same 28-observation residual adjustment as P0','Role':'Secondary parsimony sensitivity analysis'}
])
x=perfs[(perfs.residual_window_observations==28)&(perfs.model_code.isin(['P0','P1']))]
p0=x[x.model_code=='P0'].set_index('scenario');p1=x[x.model_code=='P1'].set_index('scenario');dd=diffs[(diffs.residual_window_observations==28)&(diffs['subset']=='All 2021 eligible observations')].set_index('scenario')
t3=[]
for disp,slug,src,tgt in SCENS:
    t3.append({'Evaluation setting':disp,'Test pairs':int(p0.loc[disp,'n']),'Test players':int(df[(df.team==tgt)&(df.year==2021)].player_id.nunique()),'P0 MAE':round(p0.loc[disp,'MAE'],3),'P1 MAE':round(p1.loc[disp,'MAE'],3),'P1 − P0 MAE (95% CI)':f"{dd.loc[disp,'MAE_difference']:+.3f} ({dd.loc[disp,'CI_low']:+.3f} to {dd.loc[disp,'CI_high']:+.3f})",'P0 RMSE':round(p0.loc[disp,'RMSE'],3),'P1 RMSE':round(p1.loc[disp,'RMSE'],3)})
t3=pd.DataFrame(t3)
s1=diffs[diffs['subset']=='All 2021 eligible observations'].copy();s1['P1 − P0 MAE (95% CI)']=s1.apply(lambda r:f"{r.MAE_difference:+.3f} ({r.CI_low:+.3f} to {r.CI_high:+.3f})",axis=1);s1=s1[['scenario','residual_window_observations','test_pairs','test_players','P1 − P0 MAE (95% CI)']].rename(columns={'scenario':'Evaluation setting','residual_window_observations':'Residual history window','test_pairs':'Test pairs','test_players':'Test players'})
s2=p2s.copy();s2['P2 − P0 MAE (95% CI)']=s2.apply(lambda r:f"{r.MAE_difference:+.3f} ({r.CI_low:+.3f} to {r.CI_high:+.3f})",axis=1);s2=s2[['scenario','test_pairs','test_players','P2 − P0 MAE (95% CI)']].rename(columns={'scenario':'Evaluation setting','test_pairs':'Test pairs','test_players':'Test players'})
s3=x[['scenario','model_code','MAE','RMSE','bias','R2','calibration_intercept','calibration_slope','n']].copy();s3['model_code']=s3.model_code.map({'P0':'P0 autoregressive','P1':'P1 full monitoring'});s3=s3.rename(columns={'scenario':'Evaluation setting','model_code':'Model','n':'Test pairs','calibration_intercept':'Calibration intercept','calibration_slope':'Calibration slope'})
for frame,folder,name in [(t1,TAB,'Table1_analytic_sample'),(t2,TAB,'Table2_model_specifications'),(t3,TAB,'Table3_primary_performance'),(s1,SUP,'TableS1_residual_window_sensitivity'),(s2,SUP,'TableS2_reduced_monitoring_sensitivity'),(s3,SUP,'TableS3_calibration_metrics')]:
    frame.to_csv(folder/(name+'.csv'),index=False)
    try:folder.joinpath(name+'.md').write_text(frame.to_markdown(index=False),encoding='utf-8')
    except:folder.joinpath(name+'.md').write_text(frame.to_csv(index=False),encoding='utf-8')
TAB.joinpath('phase4_tables.tex').write_text(t1.to_latex(index=False,escape=True,label='tab:sample',caption='Analytic sample by team and year.')+'\n\n'+t2.to_latex(index=False,escape=True,label='tab:models',caption='Forecasting model specifications.')+'\n\n'+t3.to_latex(index=False,escape=True,label='tab:primary',caption='Primary temporal and two-team transportability results.'),encoding='utf-8')

# visuals
fig,ax=plt.subplots(figsize=(11,6));ax.axis('off');ax.set_xlim(0,12);ax.set_ylim(0,7)
def box(x,y,w,h,text,fs=10):
    b=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.03,rounding_size=0.08',linewidth=1.2,edgecolor='black',facecolor='white');ax.add_patch(b);ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=fs,wrap=True)
def arr(a,b,c,d):ax.add_patch(FancyArrowPatch((a,b),(c,d),arrowstyle='->',mutation_scale=14,linewidth=1.2,color='black'))
box(.4,4.5,2.2,1.1,'SoccerMon subjective records\n50 elite women footballers\nTwo teams; 2020–2021')
box(3.3,4.5,2.4,1.1,'Primary analytic subset\n14,569 complete player-day pairs\nCurrent day t → readiness t+1')
box(6.5,4.5,2.2,1.1,'2020 source data\nPopulation ridge model\nTraining-only preprocessing',9)
box(9.4,4.5,2.2,1.1,'2021 target data\nSequential personalised residual adjustment\nEarlier forecast dates only',9)
for a,c in [(2.6,3.3),(5.7,6.5),(8.7,9.4)]:arr(a,5.05,c,5.05)
box(1,1.5,2.5,1.3,'P0\nAdaptive autoregressive baseline\nCurrent readiness + 28 prior residuals',9);box(4.75,1.5,2.5,1.3,'P1\nAdaptive full-monitoring model\nLoad + wellness + calendar + reporting density\n+ same residual adjustment',9);box(8.5,1.5,2.5,1.3,'Four evaluations\nWithin Team A\nWithin Team B\nTeam A → Team B\nTeam B → Team A',9);arr(5.5,4.5,2.25,2.8);arr(7.65,4.5,6,2.8);arr(10.5,4.5,9.75,2.8);ax.text(6,.45,'Primary estimand: ΔMAE = MAE(P1) − MAE(P0); positive values indicate higher error with the full monitoring panel.',ha='center',fontsize=10);fig.tight_layout();fig.savefig(FIG/'Figure1_study_design.png',dpi=300,bbox_inches='tight');fig.savefig(FIG/'Figure1_study_design.pdf',bbox_inches='tight');plt.close(fig)
sample=[]
for lab,t,y in columns:
    z=df[(df.team==t)&(df.year==y)];sample.append((lab,len(z),z.player_id.nunique()))
sample=pd.DataFrame(sample,columns=['label','pairs','players']);fig,ax=plt.subplots(figsize=(9,5.5));bars=ax.bar(sample.label,sample.pairs);ax.set_ylabel('Eligible player-day pairs');ax.set_title('Analytic next-day readiness pairs by team and year');ax.set_ylim(0,sample.pairs.max()*1.18)
for b,n,ppl in zip(bars,sample.pairs,sample.players):ax.text(b.get_x()+b.get_width()/2,b.get_height()+sample.pairs.max()*.025,f'{n:,}\n{ppl} players',ha='center',va='bottom',fontsize=9)
ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(FIG/'Figure2_analytic_sample.png',dpi=300,bbox_inches='tight');fig.savefig(FIG/'Figure2_analytic_sample.pdf',bbox_inches='tight');plt.close(fig)
forest=diffs[(diffs.residual_window_observations==28)&(diffs['subset']=='All 2021 eligible observations')].set_index('scenario').loc[[q[0] for q in SCENS]].reset_index();fig,ax=plt.subplots(figsize=(10,5.7));yy=np.arange(len(forest))[::-1];ax.axvline(0,linewidth=1,linestyle='--',color='black')
for yi,(_,r) in zip(yy,forest.iterrows()):ax.errorbar(r.MAE_difference,yi,xerr=[[r.MAE_difference-r.CI_low],[r.CI_high-r.MAE_difference]],fmt='o',capsize=4);ax.text(r.CI_high+.004,yi,f'{r.MAE_difference:+.3f} ({r.CI_low:+.3f}, {r.CI_high:+.3f})',va='center',fontsize=9)
ax.set_yticks(yy);ax.set_yticklabels(forest.scenario);ax.set_xlabel('MAE difference: full monitoring − autoregressive baseline (readiness points)');ax.set_title('Incremental forecasting value of the full daily monitoring panel');ax.text(.01,.02,'Positive values favour the personalised autoregressive baseline.',transform=ax.transAxes,fontsize=9);ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(FIG/'Figure3_primary_incremental_value.png',dpi=300,bbox_inches='tight');fig.savefig(FIG/'Figure3_primary_incremental_value.pdf',bbox_inches='tight');plt.close(fig)
sdf=diffs[diffs['subset']=='All 2021 eligible observations'];fig,ax=plt.subplots(figsize=(10,5.7));ax.axhline(0,linestyle='--',color='black',linewidth=1)
for name in [q[0] for q in SCENS]:
    z=sdf[sdf.scenario==name].sort_values('residual_window_observations');ax.errorbar(z.residual_window_observations,z.MAE_difference,yerr=[z.MAE_difference-z.CI_low,z.CI_high-z.MAE_difference],marker='o',capsize=3,label=name)
ax.set_xticks([14,28,56]);ax.set_xlabel('Sequential residual-history window (eligible observations)');ax.set_ylabel('MAE difference: full monitoring − autoregressive baseline');ax.set_title('Sensitivity of incremental value to the personal calibration window');ax.legend(frameon=False,fontsize=8,loc='upper left');ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(FIG/'Figure4_calibration_window_sensitivity.png',dpi=300,bbox_inches='tight');fig.savefig(FIG/'Figure4_calibration_window_sensitivity.pdf',bbox_inches='tight');plt.close(fig)
sl=x;order=[q[0] for q in SCENS];px=np.arange(len(order));pa=sl[sl.model_code=='P0'].set_index('scenario').loc[order];pb=sl[sl.model_code=='P1'].set_index('scenario').loc[order];fig,ax=plt.subplots(figsize=(10,5.7));ax.axhline(1,linestyle='--',color='black',linewidth=1);ax.plot(px,pa.calibration_slope,marker='o',label='P0: autoregressive baseline');ax.plot(px,pb.calibration_slope,marker='o',label='P1: full monitoring');ax.set_xticks(px);ax.set_xticklabels(['Within A','Within B','A→B','B→A']);ax.set_ylabel('Calibration slope (observed on predicted)');ax.set_xlabel('Temporal validation setting');ax.set_title('Calibration slopes under the primary 28-observation adaptation window');ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(FIG/'Figure5_calibration_slope.png',dpi=300,bbox_inches='tight');fig.savefig(FIG/'Figure5_calibration_slope.pdf',bbox_inches='tight');plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5.7));rng=np.random.default_rng(20260702)
for i,name in enumerate(order):
    z=players[players.scenario==name];ax.scatter(np.full(len(z),i)+rng.normal(0,.045,len(z)),z.mae_difference_P1_minus_P0,alpha=.75);md=z.mae_difference_P1_minus_P0.median();ax.plot([i-.2,i+.2],[md,md],color='black',linewidth=2)
ax.axhline(0,linestyle='--',color='black',linewidth=1);ax.set_xticks(range(len(order)));ax.set_xticklabels(['Within A','Within B','A→B','B→A']);ax.set_ylabel('Player-level MAE difference: P1 − P0');ax.set_xlabel('Temporal validation setting');ax.set_title('Heterogeneity of full-panel incremental error across players');ax.text(.01,.02,'Each point is one player; positive values indicate greater error with the full monitoring model.',transform=ax.transAxes,fontsize=9);ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(FIG/'Figure6_player_level_incremental_error.png',dpi=300,bbox_inches='tight');fig.savefig(FIG/'Figure6_player_level_incremental_error.pdf',bbox_inches='tight');plt.close(fig)

primary_lines=[]
for disp,slug,src,tgt in SCENS:
    r=t3[t3['Evaluation setting']==disp].iloc[0];primary_lines.append(f"- {disp}: P0 MAE {r['P0 MAE']:.3f}; P1 MAE {r['P1 MAE']:.3f}; ΔMAE {r['P1 − P0 MAE (95% CI)']}.")
bp=f"""# Manuscript Blueprint and Results Draft v1.0

## Working title
**Does Daily Workload and Wellness Monitoring Add Incremental Value Beyond a Personalised Autoregressive Baseline for Next-Day Readiness? A Two-Team Temporal Study in Elite Women’s Football**

## Central answer
Across four leakage-controlled temporal and two-team transportability settings, the full daily workload–wellness panel did not reduce next-day readiness MAE beyond the personalised autoregressive baseline. Point estimates consistently indicated higher error for the full monitoring model.

## Draft structured abstract
### Background
Daily workload and wellness monitoring are widely used in elite football, but it remains uncertain whether a larger monitoring panel improves short-term readiness forecasts beyond an athlete’s own recent readiness history.

### Objective
To assess the incremental forecasting value and two-team transportability of a daily workload–wellness panel beyond a personalised autoregressive baseline for next-day self-reported readiness in elite women’s football.

### Methods
We conducted a secondary analysis of public SoccerMon subjective-monitoring data. The analytic sample contained 14,569 eligible player-day pairs from 50 players in two elite women’s football teams. Predictors measured no later than day *t* were used to forecast readiness at day *t+1*. A ridge autoregressive model using current readiness (P0) and a ridge full-monitoring model using current readiness, daily and 7-day load, wellness, calendar, and reporting-density variables (P1) were each supplemented by the same sequential player-specific residual adjustment based on 28 earlier eligible forecast dates. Models were trained using 2020 data and tested in 2021 within each team and across teams. The primary estimand was ΔMAE = MAE(P1) − MAE(P0), with player-cluster bootstrap confidence intervals.

### Results
The full monitoring model did not reduce MAE in any evaluation setting. ΔMAE ranged from +0.016 to +0.056 readiness points. Three of four 95% player-cluster bootstrap intervals excluded zero in the direction of higher error for P1. Findings were directionally consistent after the sequential adaptation window was fully populated and when a reduced monitoring panel was evaluated.

### Conclusions
In these two elite women’s football teams, the evaluated daily workload–wellness panel did not demonstrate stable incremental forecasting value beyond a personalised autoregressive readiness baseline. The findings challenge the assumption that more daily monitoring variables necessarily improve short-term self-reported readiness prediction; they do not imply that workload or wellness are causally irrelevant.

## Introduction logic
1. Daily readiness, workload, and wellness monitoring are common in elite football, but participant burden and staff workload make incremental value important.
2. Individual athletes differ in baseline readiness and short-term response patterns, making a strong personal-history baseline essential.
3. Many studies focus on algorithm choice or random record splitting rather than incremental value under chronological and cross-team testing.
4. This study quantifies whether a full daily monitoring panel improves forecasts beyond a personalised autoregressive baseline.

## Results: manuscript-ready core text
### Analytic sample
The primary analytic file contained 14,569 eligible player-day pairs from 50 pseudonymised players. The target was self-reported readiness on the following calendar day. Team A contributed 3,812 eligible pairs in 2020 and 5,881 in 2021; Team B contributed 2,393 and 2,483, respectively (Table 1; Figure 2).

### Primary incremental-value comparison
Under the prespecified 28-observation sequential residual window, the full monitoring model did not improve MAE over the personalised autoregressive baseline in any setting (Table 3; Figure 3):
{chr(10).join(primary_lines)}

Positive ΔMAE values indicate higher absolute forecast error for the full monitoring model. Three of four player-cluster bootstrap intervals excluded zero in the direction of higher error for P1; the within-Team-A result was near null and included zero.

### Sensitivity analyses
Changing the sequential adaptation window from 14 to 56 prior eligible observations did not reverse the direction of the primary result (Figure 4; Table S1). When evaluation was restricted to records with 28 prior player-specific residuals available, the full monitoring model remained directionally worse in all four scenarios. A reduced monitoring panel likewise did not demonstrate incremental MAE improvement over the autoregressive baseline (Table S2).

### Calibration and heterogeneity
Calibration slopes for both models were below one in every scenario, consistent with attenuated predicted variability relative to the observed readiness scale (Figure 5; Table S3). Player-level MAE differences varied, but scenario-level medians remained above zero (Figure 6). This descriptive heterogeneity should not be interpreted as evidence of a causal player-specific moderator.

## Discussion guardrails
- State: “The evaluated panel did not demonstrate stable incremental forecasting value beyond the evaluated personal-history baseline.”
- Do not state: “Workload and wellness do not matter,” “teams should stop monitoring,” or “the study identifies causal effects.”
- Describe the cross-team tests as a two-team transportability assessment, not general external validation.
- Do not make injury or clinical claims.

## Strengths
- Public peer-reviewed longitudinal data source.
- Strict day-*t* to day-*t+1* target alignment.
- No random record-level train/test split.
- Strong personalised comparator.
- Bidirectional two-team transportability assessment.
- Player-cluster bootstrap intervals and residual-window sensitivity analyses.

## Limitations
- The outcome is self-reported readiness rather than an objective clinical endpoint.
- Eligibility required complete current-day wellness reports, so the estimates apply to report-complete days.
- Only two teams and one monitoring protocol were available.
- The study used subjective data and did not incorporate the GPS component.
- The analysis tests parsimonious ridge-based implementations; it is an incremental-value study, not an exhaustive algorithm competition.

## Core references
- Midoglu et al. (2024), *Scientific Data* 11:553. DOI: 10.1038/s41597-024-03386-x.
- SoccerMon dataset, Zenodo DOI: 10.5281/zenodo.10033832.
"""
OUT.joinpath('Manuscript_Blueprint_and_Results_Draft_v1.md').write_text(bp,encoding='utf-8')
OUT.joinpath('Figure_legends.md').write_text("""# Figure legends

**Figure 1. Study design and leakage-controlled forecasting protocol.** Each record was defined at the player-day level. Variables reported no later than calendar day *t* were used to forecast self-reported readiness at *t+1*. Population models were fitted only to source-team data from 2020. Sequential player-specific residual calibration used only residuals from earlier forecast dates in the target 2021 period.

**Figure 2. Analytic sample by team and year.** Bars show the number of eligible player-day pairs with complete current-day wellness data and observed next-day readiness. Labels report contributing players in each team-year subset.

**Figure 3. Primary incremental-value comparison.** Points and horizontal intervals show player-cluster bootstrap estimates and 95% confidence intervals for ΔMAE = MAE(P1) − MAE(P0) under the primary 28-observation sequential calibration window. Positive values indicate higher absolute error for P1.

**Figure 4. Sensitivity to the residual-history window.** Player-cluster bootstrap estimates and 95% confidence intervals for 14-, 28-, and 56-observation windows. Positive values indicate higher absolute error for P1.

**Figure 5. Calibration slope diagnostic.** Calibration slopes estimated from a linear regression of observed readiness on predicted readiness. The dashed reference is slope = 1.

**Figure 6. Player-level heterogeneity.** Each point represents one player’s P1−P0 MAE difference for the primary 28-observation analysis. Positive values indicate higher error for P1; black segments denote scenario-specific medians.
""",encoding='utf-8')
OUT.joinpath('References_core.bib').write_text("""@article{Midoglu2024,
  author = {Midoglu, Cise and Kj{\\ae}reng Winther, Andreas and Boeker, Matthias and Dahl Pettersen, Susann and Pedersen, Sigurd and Ragab, Nourhan and Kupka, Tomas and Hicks, Steven A. and Randers, Morten Bredsgaard and Jain, Ramesh and Dagenborg, H{\\aa}vard J. and Pettersen, Svein Arne and Johansen, Dag and Riegler, Michael A. and Halvorsen, P{\\aa}l},
  title = {A large-scale multivariate soccer athlete health, performance, and position monitoring dataset},
  journal = {Scientific Data},
  year = {2024},
  volume = {11},
  pages = {553},
  doi = {10.1038/s41597-024-03386-x}
}
@dataset{SoccerMonZenodo,
  author = {Midoglu, Cise and Boeker, Matthias and Kj{\\ae}reng Winther, Andreas and Pettersen, Svein Arne and Johansen, Dag and Riegler, Michael and Halvorsen, P{\\aa}l and Hicks, Steven},
  title = {SoccerMon: A Large-Scale Multivariate Soccer Athlete Health, Performance, and Position Monitoring Dataset},
  year = {2024},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.10033832}
}
""",encoding='utf-8')
OUT.joinpath('phase4_integrity_summary.json').write_text(json.dumps({'analytic_pairs':int(len(df)),'unique_players':int(df.player_id.nunique()),'teams':int(df.team.nunique()),'primary_comparison':'P1 full monitoring − P0 autoregressive','residual_history_window':28,'bootstrap':'player-cluster nonparametric, 2000 resamples','time_alignment':'predictors from t or earlier; outcome readiness at t+1','random_record_split_used':False,'claim_boundary':'incremental forecasting only; no causal, injury or clinical claims'},indent=2),encoding='utf-8')
OUT.joinpath('README_Phase4.md').write_text("""# Phase 4 Results Package
This package contains final manuscript-facing figures, tables, result datasets, a reproducible analysis script, figure legends, core references, and a manuscript blueprint.

**Primary effect:** ΔMAE = MAE(P1 adaptive full monitoring) − MAE(P0 adaptive autoregressive baseline). Positive values mean that the daily workload–wellness panel produced higher absolute next-day readiness error.

**Scope:** longitudinal observational forecasting of self-reported next-day readiness. This package does not support causal, clinical, injury-prediction, or deployment claims.
""",encoding='utf-8')
# exact code
OUT.joinpath('phase4_final_analysis.py').write_text(Path(__file__).read_text(encoding='utf-8'),encoding='utf-8')
print(t3.to_string(index=False))
print('DONE',OUT)
