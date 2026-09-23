"""Portable, offline integrity and field/pair verification. No network or writes."""
from pathlib import Path
import csv,json,hashlib,gzip
H=Path(__file__).resolve().parent
def rows(name):
    with (H/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def digest(b):return hashlib.sha256(b).hexdigest()
manifest=rows('sha256_manifest.csv')
for r in manifest:assert digest((H/r['path']).read_bytes())==r['sha256'],r['path']
obs={r['case_id']:r for r in json.loads((H/'normalized_observations.json').read_text())}
conditions=rows('g7_condition_results.csv');pairs=rows('g7_predeclared_pair_results.csv');fields=rows('g7_field_to_contrast_table.csv')
assert len(conditions)==27 and len(obs)==20 and len(pairs)==21
validpairs=collisions=0;missing=[]
for p in pairs:
    a,b=p['left_case'],p['right_case']
    if a not in obs or b not in obs:
        assert p['status']=='NOT_COMPARABLE_TECHNICAL_MISSINGNESS';missing.append(p['pair_id']);continue
    validpairs+=1;A,B=obs[a],obs[b]
    for label,key in [('Y_equal','Y'),('O1_equal','O1'),('O2_equal','O2')]:assert str(A[key]==B[key])==p[label],(p['pair_id'],label)
    if A['Y']!=B['Y'] and A['O1']==B['O1']:
        collisions+=1;assert A['O2']!=B['O2']
assert validpairs==15 and collisions==11 and set(missing)=={'PF01','PF02','PF03','PF04','PF05','PF08'}
assert len({json.dumps(x['O2'],sort_keys=True) for x in obs.values()})==20
for r in fields:
    A,B=obs[r['execution_A']],obs[r['execution_B']]
    assert json.loads(r['O1_A'])==A['O1'] and json.loads(r['O1_B'])==B['O1']
    names=r['critical_O2_fields'].split('; ');paths=r['O2_JSON_pointers'].split(';')
    for x,col in [(A,'O2_A'),(B,'O2_B')]:
        vals=json.loads(r[col])
        for name,path in zip(names,paths):
            v=x
            for k in path.lstrip('/').split('/'):v=v[int(k)] if isinstance(v,list) else v[k]
            assert vals[name]==v,(r['pair_id'],name)
assert len(fields)==15 and sum(r['role']=='INFORMATIVE_O1_COLLISION' for r in fields)==11
for r in rows('evidence_manifest.csv'):
    if r['path'].startswith('trace_archive/'):
        raw=gzip.decompress((H/r['path']).read_bytes());assert digest(raw)==r['original_sha256']
        trace=json.loads(raw);case=Path(r['path']).name.split('.')[0];rv=trace['returnValue']
        assert rv.startswith('0x') and not rv.startswith('0x0x')
        words=[int(rv[i:i+64],16) for i in range(2,len(rv),64)]
        decoded=[str(words[0]),bool(words[1])] if case in ('FC0','FC1') else [str(words[0])]
        assert decoded==obs[case]['O1'],case
print(json.dumps({'status':'PASS','distributed_files_verified':len(manifest),'conditions':27,'valid':20,'pairs':21,'evaluable_pairs':15,'informative_collisions':11,'field_rows':15,'additional_O3_splits':0,'network_calls':0}))
