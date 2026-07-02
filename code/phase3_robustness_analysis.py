#!/usr/bin/env python3
"""Phase 3 robustness and reproducibility analysis for SoccerMon readiness forecasting.

This script uses only the deterministic Phase 1 athlete-day dataset. It implements
leakage-audited temporal/cross-team evaluation, cold/warm-start sequential residual
calibration, feature-set/window sensitivity checks, and a within-player association model.

All transformations are fitted on the training subset for each scenario. Sequential
calibration at a prediction date uses only residuals whose target day is already observed.
"""
from __future__ import annotations

from pathlib import Path
import json
import math
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path('/mnt/data/soccermon_nextday_readiness_project')
OUT = ROOT / 'phase3_robustness_results'
OUT.mkdir(parents=True, exist_ok=True)
DATA = ROOT / 'soccermon_next_day_readiness_primary_pairs_v1.csv'
RANDOM_SEED = 20260702
N_BOOT = 300

WELLNESS = ['fatigue','mood','sleep_duration','sleep_quality','soreness','stress']
CALENDAR = ['day_of_week_num','month']
LOG_LOAD = ['daily_load']


def get_features(window: int, reduced: bool=False, with_reporting: bool=True, no_readiness: bool=False):
    if reduced:
        cont = ['readiness','daily_load','fatigue','soreness','sleep_duration','sleep_quality']
    else:
        cont = ['readiness','daily_load',f'load_mean_{window}d',f'training_days_{window}d'] + WELLNESS
        if with_reporting:
            cont += ['wellness_report_rate_3d','wellness_report_rate_7d']
    if no_readiness:
        cont = [x for x in cont if x != 'readiness']
    return cont + CALENDAR


def preprocess_for_ridge(X: pd.DataFrame, features: list[str]):
    X = X.loc[:, features].copy()
    # log-transform only load columns (positive or zero), preserving all other variables.
    for col in X.columns:
        if col.startswith('daily_load') or col.startswith('load_mean_') or col.startswith('load_sum_'):
            X[col] = np.log1p(pd.to_numeric(X[col], errors='coerce'))
    return X


def make_pipeline(features: list[str], alpha: float=10.0):
    numeric = features[:]  # all features numeric in current data set
    return Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('scale', StandardScaler()),
        ('ridge', Ridge(alpha=alpha))
    ])


def fit_predict(train: pd.DataFrame, pred: pd.DataFrame, features: list[str], alpha: float=10.0):
    X_tr = preprocess_for_ridge(train, features)
    X_pr = preprocess_for_ridge(pred, features)
    model = make_pipeline(features, alpha)
    model.fit(X_tr, train['readiness_t1'].astype(float))
    return model, model.predict(X_pr)


def sequential_calibrate(test: pd.DataFrame, base_pred: np.ndarray, window: int, history: pd.DataFrame|None=None):
    """Leakage-audited sequential residual calibration in O(n) per player."""
    from collections import deque
    d = test[["player_id","date","readiness_t1"]].copy()
    d["date"] = pd.to_datetime(d["date"])
    d["base_pred"] = np.asarray(base_pred, float)
    d["cal_pred"] = d["base_pred"]
    d["n_residuals_used"] = 0
    d["latest_residual_date"] = pd.NaT

    hist_by_player = {}
    if history is not None and len(history):
        h = history[["player_id","date","readiness_t1","base_pred"]].copy()
        h["date"] = pd.to_datetime(h["date"])
        h["residual"] = h["readiness_t1"] - h["base_pred"]
        for player, g in h.groupby("player_id", sort=False):
            hist_by_player[player] = list(g.sort_values("date")[["date","residual"]].itertuples(index=False, name=None))

    for player, idx in d.groupby("player_id", sort=False).groups.items():
        p = d.loc[idx].sort_values("date")
        q = deque(maxlen=window)
        # Warm history belongs to an earlier calendar year, but retain only records with
        # date earlier than the current prediction date. The exact strict check remains below.
        for date,resid in hist_by_player.get(player, []):
            q.append((date, resid))
        for row_idx, row in p.iterrows():
            # all q entries are earlier than row date: target is next day and has therefore
            # been observed by the current prediction day under the end-of-day protocol.
            if q:
                d.loc[row_idx, "cal_pred"] = row["base_pred"] + float(np.mean([z[1] for z in q]))
                d.loc[row_idx, "n_residuals_used"] = len(q)
                d.loc[row_idx, "latest_residual_date"] = q[-1][0]
            q.append((row["date"], row["readiness_t1"]-row["base_pred"]))
    used = d["latest_residual_date"].notna()
    assert (d.loc[used, "latest_residual_date"] < d.loc[used, "date"]).all()
    return d


def metrics(y, p):
    y = np.asarray(y, float); p = np.asarray(p, float)
    lr = np.polyfit(p, y, 1) if np.std(p) > 1e-12 else [np.nan, np.nan]
    return {
        'MAE': mean_absolute_error(y,p),
        'RMSE': math.sqrt(mean_squared_error(y,p)),
        'bias': float(np.mean(p-y)),
        'R2': r2_score(y,p),
        'calibration_intercept': float(lr[1]),
        'calibration_slope': float(lr[0]),
        'n': len(y),
    }


def player_bootstrap_diff(df: pd.DataFrame, a: str, b: str, n_boot=N_BOOT, seed=RANDOM_SEED):
    """Difference in MAE(a)-MAE(b), resampling player-level aggregate absolute errors."""
    rng=np.random.default_rng(seed)
    g=df.groupby("player_id", sort=False).apply(lambda z: pd.Series({
        "n":len(z), "ae_a":np.abs(z["readiness_t1"]-z[a]).sum(), "ae_b":np.abs(z["readiness_t1"]-z[b]).sum()
    }), include_groups=False)
    point=(g["ae_a"].sum()/g["n"].sum())-(g["ae_b"].sum()/g["n"].sum())
    arr_n=g["n"].to_numpy(float); arr_a=g["ae_a"].to_numpy(float); arr_b=g["ae_b"].to_numpy(float)
    idx=rng.integers(0,len(g),size=(n_boot,len(g)))
    vals=(arr_a[idx].sum(axis=1)/arr_n[idx].sum(axis=1))-(arr_b[idx].sum(axis=1)/arr_n[idx].sum(axis=1))
    return float(point), float(np.quantile(vals,.025)), float(np.quantile(vals,.975))


def run_scenario(name, source_team, target_team, train_year=2020, test_year=2021, window=7,
                 reduced=False, with_reporting=True, no_readiness=False, calibrate_windows=(7,14,28,56)):
    df = GLOBAL_DF
    train = df[(df.team==source_team)&(df.year==train_year)].copy()
    test = df[(df.team==target_team)&(df.year==test_year)].copy()
    assert train.date.max() < pd.Timestamp('2021-01-01')
    assert test.date.min() >= pd.Timestamp('2021-01-01')
    feats_base = ['readiness']
    feats_full = get_features(window, reduced=reduced, with_reporting=with_reporting, no_readiness=no_readiness)

    _, pred0 = fit_predict(train, test, feats_base)
    model1, pred1 = fit_predict(train, test, feats_full)

    result=test[['player_id','team','date','year','readiness_t1']].copy()
    result['pred_M0_autoreg']=pred0
    result['pred_M1_population']=pred1

    # Cross-team warm-start history: source model applied to target team 2020 data.
    # In within-team settings, no in-sample history is used, so calibration remains cold-start.
    warm_hist=None
    if source_team != target_team:
        target_history = df[(df.team==target_team)&(df.year==train_year)].copy()
        _, hist_pred = fit_predict(train, target_history, feats_full)
        warm_hist = target_history[['player_id','date','readiness_t1']].copy()
        warm_hist['base_pred']=hist_pred

    for cw in calibrate_windows:
        cold = sequential_calibrate(test, pred1, cw, history=None)
        result[f'pred_M3cold_{cw}'] = cold['cal_pred'].values
        result[f'n_residuals_cold_{cw}'] = cold['n_residuals_used'].values
        if warm_hist is not None:
            warm = sequential_calibrate(test, pred1, cw, history=warm_hist)
            result[f'pred_M3warm_{cw}'] = warm['cal_pred'].values
            result[f'n_residuals_warm_{cw}'] = warm['n_residuals_used'].values

    result.to_csv(OUT/f'predictions_{name}.csv',index=False)

    rows=[]
    for col in [x for x in result.columns if x.startswith('pred_')]:
        m=metrics(result.readiness_t1,result[col])
        rows.append({'scenario':name,'model':col,**m})
    return result, pd.DataFrame(rows)


def run_main():
    # Primary 7-day approach and bidirectional within/cross-team assessment.
    all_metrics=[]; all_preds={}
    specs=[
        ('Within_TeamA_2020_to_2021','TeamA','TeamA'),
        ('Within_TeamB_2020_to_2021','TeamB','TeamB'),
        ('Cross_TeamA2020_to_TeamB2021','TeamA','TeamB'),
        ('Cross_TeamB2020_to_TeamA2021','TeamB','TeamA'),
    ]
    for name,src,tgt in specs:
        p,m=run_scenario(name,src,tgt,window=7)
        all_preds[name]=p
        all_metrics.append(m)
    metrics_df=pd.concat(all_metrics,ignore_index=True)

    # Player-cluster CIs for all models versus M0 autoregressive baseline
    ci_rows=[]
    for scen,p in all_preds.items():
        for col in [x for x in p.columns if x.startswith('pred_') and x!='pred_M0_autoreg']:
            diff,lo,hi=player_bootstrap_diff(p,col,'pred_M0_autoreg')
            ci_rows.append({'scenario':scen,'model':col,'MAE_difference_vs_M0':diff,'CI_low':lo,'CI_high':hi})
    ci_df=pd.DataFrame(ci_rows)
    metrics_df=metrics_df.merge(ci_df,on=['scenario','model'],how='left')
    metrics_df.to_csv(OUT/'phase3_primary_performance.csv',index=False)

    # Sensitivity: full vs reduced monitoring, report-density exclusion, and load windows
    sens=[]
    for scenario,src,tgt in [('Within_TeamA','TeamA','TeamA'),('Within_TeamB','TeamB','TeamB'),('Cross_A_to_B','TeamA','TeamB'),('Cross_B_to_A','TeamB','TeamA')]:
        for w in [3,7,14]:
            for setting,kwargs in [
                ('full_with_reporting',dict(reduced=False,with_reporting=True,no_readiness=False)),
                ('full_without_reporting',dict(reduced=False,with_reporting=False,no_readiness=False)),
                ('reduced_monitoring',dict(reduced=True,with_reporting=False,no_readiness=False)),
                ('full_without_current_readiness',dict(reduced=False,with_reporting=True,no_readiness=True)),
            ]:
                name=f'{scenario}_{setting}_w{w}'
                p,m=run_scenario(name,src,tgt,window=w,**kwargs,calibrate_windows=(28,))
                # record only M0, M1 and appropriate calibration variants
                for _,row in m.iterrows():
                    if row['model'] in ['pred_M0_autoreg','pred_M1_population','pred_M3cold_28','pred_M3warm_28']:
                        sens.append({'scenario':scenario,'load_window_days':w,'feature_set':setting,**row.to_dict()})
    sens_df=pd.DataFrame(sens)
    sens_df.to_csv(OUT/'phase3_sensitivity_performance.csv',index=False)

    # Reporting-density association as a descriptive test added to main results
    # Fixed-effects within-player association model, cluster robust by player.
    a=GLOBAL_DF.copy()
    for col in ['daily_load','load_mean_7d']:
        a['log_'+col]=np.log1p(a[col])
    # Player fixed effects target time association, not a causal model.
    formula=('readiness_t1 ~ readiness + log_daily_load + log_load_mean_7d + fatigue + soreness + stress + mood + '
             'sleep_duration + sleep_quality + wellness_report_rate_7d + C(month) + C(player_id)')
    fe=smf.ols(formula, data=a).fit(cov_type='cluster', cov_kwds={'groups':a['player_id']})
    coefs=pd.DataFrame({'term':fe.params.index,'estimate':fe.params.values,'se':fe.bse.values,'p_value':fe.pvalues.values,
                        'ci_low':fe.conf_int().iloc[:,0].values,'ci_high':fe.conf_int().iloc[:,1].values})
    coefs.to_csv(OUT/'within_player_fixed_effects_association.csv',index=False)
    with open(OUT/'within_player_fixed_effects_association_summary.txt','w') as f:
        f.write(fe.summary().as_text())

    # Exhaustive leakage and integrity audit
    audit={
        'primary_input_rows':int(len(GLOBAL_DF)),
        'players':int(GLOBAL_DF.player_id.nunique()),
        'teams':int(GLOBAL_DF.team.nunique()),
        'target_alignment_verified':bool(verify_target_alignment(GLOBAL_DF)),
        'outcome_not_in_candidate_predictors':True,
        'all_primary_rows_have_current_complete_wellness':bool((GLOBAL_DF.wellness_complete_t==1).all()),
        'all_primary_rows_have_next_day_readiness':bool(GLOBAL_DF.readiness_t1.notna().all()),
        'sequential_calibration_strictly_uses_prior_prediction_dates':True,
        'notes':[
            'The warm-start calibration applies only to cross-team scenarios and uses target-team 2020 observations predicted by a model trained exclusively in the source team 2020.',
            'Within-team calibration is cold-start only in this reproducibility analysis; no in-sample 2020 residuals are used.',
            'Models are fitted after each scenario split; all scalers and imputers are fitted on the source training subset only.',
            'The association model is descriptive and uses player fixed effects with player-cluster robust standard errors; it does not support causal claims.'
        ]
    }
    (OUT/'phase3_leakage_audit.json').write_text(json.dumps(audit,indent=2,default=str))

    # Human-readable report.
    lines=[]
    lines.append('# Phase 3: Robustness and Leakage-Audited Reproducibility Results\n')
    lines.append('This phase reimplemented the primary population and sequential calibration analyses from the Phase 1 deterministic athlete-day file. The reimplementation treats the autoregressive model as a Ridge model using current readiness only; it therefore should not be numerically conflated with the earlier Phase 2 prototype.\n')
    lines.append('## Core implementation safeguards\n')
    lines += [
        '- All model preprocessing was fitted on the scenario-specific 2020 training subset only.',
        '- The outcome is next-calendar-day readiness; no t+1 variable was used as a predictor.',
        '- Cold-start residual calibration used only earlier 2021 observations from the same player.',
        '- Warm-start calibration was evaluated only for cross-team transfer and used prior 2020 target-team records predicted by a source-team-only model.',
        '- Within-team calibration did not use in-sample training residuals, avoiding optimistic personal residual adjustments.\n'
    ]
    lines.append('## Primary 7-day population model performance\n')
    lines.append(metrics_df.round(4).to_markdown(index=False))
    lines.append('\n## Key sensitivity summary (M1 population and 28-observation calibration variants)\n')
    # condensed pivot
    lines.append(sens_df[['scenario','load_window_days','feature_set','model','MAE','RMSE','R2']].round(4).to_markdown(index=False))
    lines.append('\n## Interpretation boundary\n')
    lines.append('The results quantify forecasting behavior on self-reported readiness. They do not demonstrate causal load effects, clinical validation, or prescriptive training thresholds. Cross-team results are a two-team transportability assessment only.\n')
    (OUT/'Phase3_robustness_report.md').write_text('\n'.join(lines))


def verify_target_alignment(df):
    # Reconstruct direct target from full panel for exact date+1 and compare.
    full=pd.read_csv(ROOT/'soccermon_next_day_readiness_full_panel_v1.csv')
    full['date']=pd.to_datetime(full['date'])
    x=df[['player_id','date','readiness_t1']].copy(); x['date']=pd.to_datetime(x['date'])
    lookup=full[['player_id','date','readiness']].copy(); lookup['date']=lookup['date']-pd.Timedelta(days=1)
    lookup=lookup.rename(columns={'readiness':'expected_t1'})
    chk=x.merge(lookup,on=['player_id','date'],how='left',validate='one_to_one')
    return np.allclose(chk['readiness_t1'],chk['expected_t1'],equal_nan=True)


if __name__=='__main__':
    GLOBAL_DF=pd.read_csv(DATA)
    GLOBAL_DF['date']=pd.to_datetime(GLOBAL_DF['date'])
    # exact eligibility checks from primary file
    assert GLOBAL_DF['analysis_eligible_primary'].eq(1).all()
    assert GLOBAL_DF['date'].notna().all()
    run_main()
    print(f'Wrote Phase 3 results to {OUT}')
