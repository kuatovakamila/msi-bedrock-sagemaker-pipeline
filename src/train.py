# skylearn+optuna+artifact tar 

import argparse, numpy as np,pandas as pd
import tempfile 
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split 
from sklearn.metrics import roc_auc_score, f1_score 
import joblib
import os, json, tarfile

try:
    import optuna
except ImportError:
    optuna = None 

def train_eval(df):
    x = df[["speed_kph","accel_g","brake_ratio","engine_temp"]].values
    y = df["label"].values 
    xtr,xte,ytr,yte = train_test_split(x,y, test_size=0.2, random_state=7,stratify=y)


    def fit_predict():
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=7)
        model.fit(xtr)
        pred = (model.predict(xte) ==-1).astype(int)
        scores = -model.decision_function(xte)
        return model, {"roc_auc": roc_auc_score(yte, scores), "f1": f1_score(yte, pred)}
    
    if optuna:
        def obj(trial):
            n_estimators = trial.suggest_int("n_estimators", 50, 300)
            max_samples = trial.suggest_float("max_samples", 0.1, 1.0)
            contamination = trial.suggest_float("contamination", 0.01, 0.15)
            
            model = IsolationForest(
                n_estimators=n_estimators,
                max_samples=max_samples,
                contamination=contamination,
                random_state=7
            )
            model.fit(xtr)
            pred = (model.predict(xte) == -1).astype(int)
            scores = -model.decision_function(xte)
            return roc_auc_score(yte, scores)
        
        study = optuna.create_study(direction='maximize')
        study.optimize(obj, n_trials=10)
        best_params = study.best_params
        
        model = IsolationForest(**best_params, random_state=7)
        model.fit(xtr)
        pred = (model.predict(xte) == -1).astype(int)
        scores = -model.decision_function(xte)
        return model, {"roc_auc": roc_auc_score(yte, scores), "f1": f1_score(yte, pred)}
    else:
        return fit_predict()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default ="data/telematics.csv")
    parser.add_argument("--out", default="artifacts/artifacts.tar.gz")
    parser.add_argument("--metrics_out", default="artifacts/metrics.json")
    args = parser.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok = True)

    df = pd.read_csv(args.data)
    model, metrics = train_eval(df)

    with tempfile.TemporaryDirectory() as d:
        model_path = os.path.join(d,"model.pkl")
        joblib.dump(model, model_path)
        with tarfile.open(args.out, 'w:gz') as tar:
            tar.add(model_path, arcname='model.pkl')
    with open(args.metrics_out,'w') as f:
        json.dump(metrics,f,indent=2)
    print("METRICS:", json.dumps(metrics))
