from pathlib import Path
import numpy as np, pandas as pd, json
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import statsmodels.formula.api as smf

ROOT=Path('/mnt/data/soccermon_nextday_readiness_project')
OUT=ROOT/'phase3_robustness_results'
OUT.mkdir(exist_ok=True)
df=pd.read_csv(ROOT/'soccermon_next_day_readiness_primary_pairs_v1.csv')
df['date']=pd.to_datetime(df['date'])

WELLNESS=['fatigue','mood','sleep_duration','sleep_quality','soreness','stress']
CAL=['day_of_week_num','month']

def feats(window,setting):
    if setting=='reduced_monitoring':
        return ['readiness','daily_load','fatigue','soreness','sleep_duration','sleep_quality']+CAL
    x=['readiness','daily_load',f'load_mean_{window}d',f'training_days_{window}d']+WELLNESS
    if setting=='full_with_reporting':x += ['wellness_report_rate_3d','wellness_report_rate_7d']
    if setting=='full_without_current_readiness':x=[z for z in x if z!='readiness']+['wellness_report_rate_3d','wellness_report_rate_7d']
    return x+CAL

def tx(a,fs):
    x=a[fs].copy()
    for c in x:
        if c=='daily_load' or c.startswith('load_mean_'):
            x[c]=np.log1p(x[c])
    return x

def fitpred(tr,te,fs):
    model=Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('ridge',Ridge(alpha=10.0))])
    model.fit(tx(tr,fs),tr.readiness_t1)
    return model.predict(tx(te,fs))

def met(y,p):
    slope,inter=np.polyfit(p,y,1) if np.std(p)>1e-12 else (np.nan,np.nan)
    return dict(MAE=mean_absolute_error(y,p),RMSE=mean_squared_error(y,p)**.5,bias=float(np.mean(p-y)),R2=r2_score(y,p),calibration_intercept=float(inter),calibration_slope=float(slope),n=len(y))

scens=[('Within_TeamA','TeamA','TeamA'),('Within_TeamB','TeamB','TeamB'),('Cross_A_to_B','TeamA','TeamB'),('Cross_B_to_A','TeamB','TeamA')]
settings=['full_with_reporting','full_without_reporting','reduced_monitoring','full_without_current_readiness']
rows=[]
for scen,src,tgt in scens:
    tr=df[(df.team==src)&(df.year==2020)]
    te=df[(df.team==tgt)&(df.year==2021)]
    for w in (3,7,14):
      for st in settings:
        fs=feats(w,st)
        p=fitpred(tr,te,fs)
        rows.append(dict(scenario=scen,load_window_days=w,feature_set=st,**met(te.readiness_t1,p)))
out=pd.DataFrame(rows)
out.to_csv(OUT/'phase3_sensitivity_population_models.csv',index=False)

# Summarize calibration window variants from completed primary table.
primary=pd.read_csv(OUT/'phase3_primary_performance.csv')
cal=primary[primary.model.str.contains('M3')].copy()
cal['warm_start']=cal.model.str.contains('warm')
cal['residual_window_observations']=cal.model.str.extract(r'_(\d+)$').astype(int)
cal.to_csv(OUT/'phase3_calibration_window_comparison.csv',index=False)

# Descriptive within-player fixed-effects association on the complete primary pairs.
a=df.copy()
a['log_daily_load']=np.log1p(a.daily_load)
a['log_load_mean_7d']=np.log1p(a.load_mean_7d)
formula='readiness_t1 ~ readiness + log_daily_load + log_load_mean_7d + fatigue + soreness + stress + mood + sleep_duration + sleep_quality + wellness_report_rate_7d + C(month) + C(player_id)'
fit=smf.ols(formula,data=a).fit(cov_type='cluster',cov_kwds={'groups':a.player_id})
coef=pd.DataFrame({'term':fit.params.index,'estimate':fit.params.values,'se':fit.bse.values,'p_value':fit.pvalues.values,'ci_low':fit.conf_int().iloc[:,0].values,'ci_high':fit.conf_int().iloc[:,1].values})
coef.to_csv(OUT/'within_player_fixed_effects_association.csv',index=False)
(OUT/'within_player_fixed_effects_association_summary.txt').write_text(fit.summary().as_text())

# Integrity and leakage audit
full=pd.read_csv(ROOT/'soccermon_next_day_readiness_full_panel_v1.csv')
full.date=pd.to_datetime(full.date)
lookup=full[['player_id','date','readiness']].copy(); lookup.date=lookup.date-pd.Timedelta(days=1);lookup=lookup.rename(columns={'readiness':'expected_t1'})
check=df[['player_id','date','readiness_t1']].merge(lookup,on=['player_id','date'],how='left',validate='one_to_one')
audit={
 'primary_rows':int(len(df)),
 'players':int(df.player_id.nunique()),
 'teams':int(df.team.nunique()),
 'target_alignment_exact':bool(np.allclose(check.readiness_t1,check.expected_t1,equal_nan=True)),
 'all_rows_current_wellness_complete':bool(df.wellness_complete_t.eq(1).all()),
 'all_rows_next_day_outcome_observed':bool(df.readiness_t1.notna().all()),
 'population_model_preprocessing_fit_within_training_split':True,
 'calibration_window_results_are_from_a_separate_sequential_run':True,
 'warning':'Phase 2 prototype model code was not available. Phase 3 reimplemented a transparent ridge-based model and a sequential residual calibration scheme from the Phase 1 deterministic CSV. Values should be treated as the reproducible primary analytical engine going forward, not combined numerically with Phase 2 prototype estimates.'
}
(OUT/'phase3_leakage_audit.json').write_text(json.dumps(audit,indent=2))

# Report
lines=['# Phase 3: Robustness, Reproducibility, and Leakage-Audited Results\n',
'## Why this phase was required\n',
'The Phase 2 files contained predictions and results but not the corresponding executable modelling script. This phase therefore reimplemented a transparent ridge-based population model and an online, player-specific residual-calibration procedure directly from the deterministic Phase 1 athlete-day file. The Phase 3 results are the reproducible analysis engine for the manuscript.\n',
'## Safeguards\n',
'- The target is readiness at calendar day *t+1*; model predictors are measured no later than day *t*.\n- Preprocessing is fit only to each scenario\'s 2020 training data.\n- Cold-start calibration uses only earlier 2021 observations from the same player.\n- Warm-start calibration is reported only in cross-team transfer, using target-team 2020 historical observations predicted by a source-team-only model.\n- No in-sample source-team residuals are used to initialize within-team personalised calibration.\n',
'## Reproducible primary performance\n',primary.round(4).to_markdown(index=False),'\n## Population-model sensitivity checks\n',out.round(4).to_markdown(index=False),'\n## Calibration-window comparison\n',cal.round(4).to_markdown(index=False),'\n## Interpretation boundary\n','All findings concern temporal forecasting of self-reported next-day readiness. They do not establish causal training-load effects, injury prediction, or clinical readiness thresholds.\n']
(OUT/'Phase3_robustness_report.md').write_text('\n'.join(lines))
print('completed',OUT)
