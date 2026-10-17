"""Portable Phase 4A scorer accepting explicitly precomputed historical features.

This does not maintain transaction history. It requires trusted causal features
with the bundled schema; callers must not substitute fabricated missing history.
"""
from pathlib import Path
from datetime import datetime
import argparse, hashlib, json, math

TRANSACTION_FEATURES=['amount_paid','amount_received','log_amount_paid','log_amount_received','hour','weekday','day_of_month','payment_currency','receiving_currency','payment_format']
CATEGORIES=['payment_currency','receiving_currency','payment_format']

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Bundle:
    def __init__(self,path):
        import lightgbm as lgb
        self.path=Path(path).resolve();self.metadata=json.loads((self.path/'bundle.json').read_text())
        for name,expected in self.metadata['files_sha256'].items():
            p=(self.path/name).resolve()
            if not p.is_relative_to(self.path) or digest(p)!=expected:raise ValueError('Bundle integrity failure: '+name)
        self.schema=json.loads((self.path/'historical_feature_schema.json').read_text())
        self.config=json.loads((self.path/'preprocessing.json').read_text())
        self.model=json.loads((self.path/'model.json').read_text())
        self.booster=lgb.Booster(model_file=str(self.path/'booster.txt'))
        self.history_names=self.schema['ordered_features'];self.combined=self.model['experiment']=='C_combined'
        expected=(TRANSACTION_FEATURES if self.combined else [])+self.history_names
        if expected!=self.model['ordered_features'] or self.booster.feature_name()!=expected:raise ValueError('Feature order mismatch')
        if self.model['threshold']!=self.metadata['threshold']:raise ValueError('Threshold mismatch')
        self.lookups={k:{s:i for i,s in enumerate(v)} for k,v in self.config['categories'].items()}
    def vector(self,row):
        if set(row)!={'transaction','historical'}:raise ValueError('Use transaction and historical objects only')
        transaction=row['transaction'];history=row['historical']
        if not isinstance(transaction,dict) or set(transaction)!={'timestamp','amount_paid','amount_received',*CATEGORIES}:raise ValueError('Six transaction fields required')
        if not isinstance(transaction['timestamp'],str):raise ValueError('ISO timestamp required')
        t=datetime.fromisoformat(transaction['timestamp'])
        if t.tzinfo is not None:raise ValueError('Naive benchmark timestamps required')
        values=[]
        for key in ['amount_paid','amount_received']:
            v=transaction[key]
            if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<0:raise ValueError('Invalid '+key)
            values.append(float(v))
        paid,received=values
        for key in CATEGORIES:
            if not isinstance(transaction[key],str) or not transaction[key]:raise ValueError('Invalid '+key)
        values=[paid,received,math.log1p(paid),math.log1p(received),t.hour,t.weekday(),t.day]+[self.lookups[k].get(transaction[k],-1) for k in CATEGORIES]
        if not isinstance(history,dict) or set(history)!=set(self.history_names):raise ValueError('Exactly eight historical fields required')
        hv=[]
        for field in self.schema['fields']:
            name=field['name'];v=history[name]
            if v is None:
                if not field['nullable']:raise ValueError('Unexpected null '+name)
                hv.append(float('nan'));continue
            if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<0:raise ValueError('Invalid history '+name)
            if field['dtype']=='int64' and (not isinstance(v,int) or v>2**53):raise ValueError('Integer history required '+name)
            if name=='is_new_counterparty' and v not in (0,1):raise ValueError('Invalid binary flag')
            hv.append(float(v))
        return (values if self.combined else [])+hv
    def predict(self,rows):
        import numpy as np
        if not rows:return []
        x=np.asarray([self.vector(r) for r in rows],dtype='float64');p=self.booster.predict(x,num_threads=4)
        return [{'risk_score':float(v),'alert':bool(v>=self.metadata['threshold']),'threshold':self.metadata['threshold'],'model_version':self.metadata['model_version']} for v in p]
    def verify_examples(self):
        data=json.loads((self.path/'examples.json').read_text());actual=self.predict(data['inputs'])
        for a,e in zip(actual,data['expected'],strict=True):
            if abs(a['risk_score']-e['risk_score'])>data['absolute_tolerance'] or a['alert']!=e['alert'] or a['alert']!=(a['risk_score']>=self.metadata['threshold']):raise ValueError('Prediction mismatch')
        return {'verified_examples':len(actual),'absolute_tolerance':data['absolute_tolerance'],'model_version':self.metadata['model_version'],'precomputed_history_only':True}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True,type=Path);p.add_argument('--verify-examples',action='store_true');p.add_argument('--input',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();b=Bundle(a.bundle)
    if a.verify_examples:result=b.verify_examples()
    elif a.input:result=b.predict(json.loads(a.input.read_text()))
    else:p.error('Supply --input or --verify-examples')
    s=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if a.output:a.output.write_text(s)
    else:print(s,end='')
if __name__=='__main__':main()
