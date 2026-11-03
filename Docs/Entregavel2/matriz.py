import sys; sys.path.insert(0, r"C:\Users\vitor\Documents\GitHub\TCC2\Codigo")
import json, numpy as np, xgboost as xgb
from modelo import treinar_zurique as T
d,_=T.preparar(); d=T.atributos(d)
treino, teste = d[d.ts < T.CORTE], d[d.ts >= T.CORTE].reset_index(drop=True)
t=json.load(open(T.METRICAS if hasattr(T,"METRICAS") else r"modelo/resultados/metricas_zurique.json"))["tercis_nivel"] if False else [0.0693,0.2946]
m=xgb.XGBRegressor(); m.load_model(T.MODELO)
p=m.predict(teste[T.COLUNAS]).clip(0,1); y=teste.alvo.to_numpy()
h=teste.ts.dt.hour.to_numpy(); n=(h>=18)|(h<6)
fr,fp=T.faixa(y[n],t),T.faixa(p[n],t)
M=np.zeros((3,3),int)
for a,b in zip(fr,fp): M[a,b]+=1
print(M.tolist(), M.trace()/M.sum(), M.sum())
for k in range(3):
    pr=M[k,k]/M[:,k].sum(); rc=M[k,k]/M[k].sum(); print(k, round(pr,3), round(rc,3), round(2*pr*rc/(pr+rc),3))
