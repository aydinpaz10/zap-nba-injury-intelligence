"""Constrained optimizers extracted from the production training scripts."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

def fit_win(x,y,C,adjusted):
 n=len(y);penalty=np.ones(x.shape[1]);penalty[0]=0
 def obj(w):
  z=x@w;p=expit(z);return np.mean(np.logaddexp(0,z)-y*z)+np.sum(penalty*w*w)/(2*C*n),x.T@(p-y)/n+penalty*w/(C*n)
 bounds=[(None,None)]*x.shape[1]
 if adjusted:bounds[-1]=(0,None)
 result=minimize(obj,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',bounds=bounds,options={'maxiter':2000,'ftol':1e-12,'gtol':1e-8})
 if not result.success:raise RuntimeError(result.message)
 return result.x

def xy(rows):return np.array([x for r in rows for x in [r['home_features'],r['away_features']]]),np.array([y for r in rows for y in [r['actual_home'],r['actual_away']]])
def fit_score(rows,alpha):
 x,y=xy(rows);penalty=np.ones(x.shape[1]);penalty[0]=0
 def fn(w):
  residual=x@w-y;return (residual@residual+alpha*np.sum(penalty*w*w))/(2*len(y)),(x.T@residual+alpha*penalty*w)/len(y)
 bounds=[(None,None)]*8;bounds[6]=(None,0);bounds[7]=(0,None)
 r=minimize(fn,np.array([110.,1.,1.,1.,3.,0.,0.,0.]),jac=True,bounds=bounds,method='L-BFGS-B',options={'maxiter':3000,'ftol':1e-12,'gtol':1e-7});assert r.success,r.message;return r.x
