import argparse, numpy as np, pandas as pd, os
from numpy.random import default_rng

rng = default_rng(7) 

def synth(n = 5000, anomaly_fraction = 0.05):
    normal = np.column_stack([
        rng.normal(60,15,n), # normal, deviation (speed)
        rng.normal(30,10,n),# acceleration
        rng.beta(2,8,n), # beta distribution (braking ration)
        rng.normal(85,5,n)]) # engine temp 
    
    y = np.zeros(n, dtype=int)
    k = int(n * anomaly_fraction)
    if k > 0:
        idx = rng.choice(n, size = k, replace= False)
        normal[idx,0] = rng.normal(120,20,k) # speed anomaly 
        normal[idx,2] = rng.normal(8,2,k) # agressive braking
        y[idx] = 1
        df = pd.DataFrame(normal,columns= ["speed_kph","accel_g","brake_ratio","engine_temp"])
        df["label"] = y
        return df
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out",default='data/telematics.csv')
    parser.add_argument("--n",default=5000, type=int)
    parser.add_argument("--anomaly_fraction",default=0.05,type=float)
    args= parser.parse_args()
    df = synth(args.n, args.anomaly_fraction)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index = False)
    print(f"Wrote {args.out}, shape: {df.shape}")
    
# normally distributed random data




