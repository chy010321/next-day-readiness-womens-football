from pathlib import Path
from collections import deque
import numpy as np,pandas as pd
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score

ROOT=Path('/mnt/data/soccermon_nextday_readiness_project/phase3_robustness_results')
OUT=ROOT/'phase3_personal_baseline_challenge.csv'

def calibrate(d,base_col,w):
    d=d[['player_id','date','readiness_t1',base_col]].copy();d.date=pd.to_datetime(d.date)
    out=np.empty(len(d)); ns=np.zeros(len(d),int)
    for player,idx in d.groupby('player_id',sort=False).groups.items():
        p=d.loc[idx].sort_values('date')
        q=deque(maxlen=w)
        for j,row in p.iterrows():
            out[d.index.get_loc(j)] = row[base_col]+(np.mean([v for _,v in q]) if q else 0)
            ns[d.index.get_loc(j)] = len(q)
            q.append((row.date,row.readiness_t1-row[base_col]))
    return out,ns

def rolling_mean(d,w):
    d=d[['player_id','date','readiness_t1']].copy();d.date=pd.to_datetime(d.date)
    out=np.empty(len(d));ns=np.zeros(len(d),int)
    for player,idx in d.groupby('player_id',sort=False).groups.items():
        p=d.loc[idx].sort_values('date');q=deque(maxlen=w)
        for j,row in p.iterrows():
            out[d.index.get_loc(j)] = np.mean(q) if q else np.nan
            ns[d.index.get_loc(j)] = len(q)
            q.append(row.readiness_t1)
    return out,ns

def met(y,p):
    keep=np.isfinite(p)
    return dict(MAE=mean_absolute_error(y[keep],p[keep]),RMSE=mean_squared_error(y[keep],p[keep])**.5,R2=r2_score(y[keep],p[keep]),n=int(keep.sum()))
rows=[]
for path in ROOT.glob('predictions_*2021.csv'):
    d=pd.read_csv(path); scen=path.stem.replace('predictions_','')
    y=d.readiness_t1.to_numpy(float)
    for base in ['pred_M0_autoreg','pred_M1_population']:
        for w in [14,28,56]:
            p,n=calibrate(d,base,w)
            rows.append({'scenario':scen,'model':f'{base}_residual_calibration_{w}',**met(y,p),'mean_history_records_used':n.mean()})
    for w in [14,28,56]:
        p,n=rolling_mean(d,w)
        rows.append({'scenario':scen,'model':f'personal_rolling_mean_{w}',**met(y,p),'mean_history_records_used':n.mean()})
res=pd.DataFrame(rows);res.to_csv(OUT,index=False)
print(res.to_string(index=False))
