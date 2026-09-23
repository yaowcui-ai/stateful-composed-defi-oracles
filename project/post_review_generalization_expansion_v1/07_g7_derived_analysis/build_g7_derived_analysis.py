"""Offline-only derivation from sealed G4/G6; no network or execution imports."""
import csv, json, hashlib, pathlib, collections

OUT = pathlib.Path(__file__).resolve().parent
PHASE = OUT.parent
PROJECT = PHASE.parent
G4 = PHASE / '04_g4_formal_selection_design_freeze'
G6 = PHASE / '06_g6_frozen_formal_execution'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x): (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvread(p): return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def csvwrite(name,rows):
    assert rows
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def md(name,s): (OUT/name).write_text(s+'\n',encoding='utf-8')

manifest=read(G6/'G6_EVIDENCE_MANIFEST.json')
protected=[G6/x['path'] for x in manifest['files']]
protected += [PHASE/x['path'] for x in csvread(G6/'G6_PROTECTED_G4_G5_SHA256.csv')]
protected += list((PROJECT/'journal_manuscript_phase').glob('*V0.2*'))
protected += [PROJECT/'journal_manuscript_phase'/n for n in ['JOURNAL_CLAIM_EVIDENCE_LOCK_V2.md','JOURNAL_MANUSCRIPT_LOCK_V2.md']]
baseline={str(p):sha(p) for p in protected}
assert all(sha(G6/x['path'])==x['sha256'] for x in manifest['files'])
assert all(sha(PHASE/x['path'])==x['sha256'] for x in csvread(G6/'G6_PROTECTED_G4_G5_SHA256.csv'))
csvwrite('G7_INPUT_PROTECTION_BASELINE.csv',[{'path':p,'sha256':h} for p,h in sorted(baseline.items())])
cases=csvread(G4/'G4_CONDITION_MATRIX_V1.csv')
pairs=csvread(G4/'G4_PAIRWISE_COMPARISON_LOCK_V1.csv')
raw_traces={}
for f in (G6/'raw').glob('*.json'):
    x=read(f)
    if x.get('request',{}).get('method') in ('debug_traceCall','debug_traceTransaction'):
        r=x.get('response',{}).get('result')
        if isinstance(r,dict): raw_traces.setdefault(sha_bytes:=hashlib.sha256(canon(r).encode()).hexdigest(),[]).append(str(f))
data={}; decoded=[]; adjud=[]; norm=[]
for c in cases:
    k=c['case_id'];d=read(G6/'deployed'/f'{k}.json');r=read(G6/'reference'/f'{k}.json')
    assert r['Y']=={'input_acceptance':c['Y_input_acceptance'],'return_source':c['Y_return_source'],'transition':c['Y_transition']}
    common={'case_id':k,'implementation':c['implementation'],'episode':c['episode'],'primary_entrypoint':c['primary_entrypoint']}
    row={**common,'valid_execution':d.get('valid_execution',False),'adjudication':'NOT_COMPARABLE_TECHNICAL_HISTORY_FAILURE','Y':canon(r['Y']),'witness_basis':'Retained technical failure/history invalid; no negative semantic inference','evidence_label':'DIRECT_OBSERVATION_OF_TECHNICAL_FAILURE','source_deployed':str(G6/'deployed'/f'{k}.json')}
    if not d.get('valid_execution'):
        adjud.append(row);continue
    assert d['history_integrity'] and d['comparable']
    tp=G6/d['trace'];t=read(tp);rv=t['returnValue']
    assert rv.startswith('0x') and not rv.startswith('0x0x') and (len(rv)-2)%64==0
    assert not t['failed'] and d['O1']['raw_return']=='0x'+rv
    words=[int(rv[i:i+64],16) for i in range(2,len(rv),64)]
    if c['primary_entrypoint']=='peekPrice()':
        assert len(words)==2 and words[1] in (0,1);o1=[str(words[0]),bool(words[1])];abi='(uint256,bool)'
    else:
        assert len(words)==1;o1=[str(words[0])];abi='(uint256)'
    rawpaths=raw_traces[hashlib.sha256(canon(t).encode()).hexdigest()]
    decoded.append({**common,'original_raw_return':d['O1']['raw_return'],'original_decode_error':canon(d['O1'].get('decoded','NA')),'frozen_trace_return':rv,'abi':abi,'corrected_full_O1_tuple':canon(o1),'corrected_price_component':str(words[0]),'correction':'DERIVED_ANALYSIS_CORRECTION_DUPLICATE_HEX_PREFIX','trace_path':str(tp),'trace_sha256':sha(tp),'matching_raw_rpc_paths':canon(rawpaths)})
    events=[{'topics':e['topics'],'data':e['data']} for e in d['events']]
    o2={'O1':o1,'pre':d['pre'],'post':d['post'],'events':events}
    o3={'O2':o2,'trace':t,'nonpublic_storage':[]}
    # Explicit semantic witness checks, independent of equality of observation tuples.
    pre,post=d['pre'],d['post']
    if k.startswith('V'):
        expected={'VA0':('0','0'),'VA1':('0','0'),'VA2':('0','1'),'VA3':('1','1'),'VA4':('1','0'),'VB0':('0','0'),'VB1':('0','1'),'VB2':('1','0')}[k]
        assert (pre['status'][0],post['status'][0])==expected
        assert words[0]==(1200000000000000000 if k in ('VB0','VB1') else 1000000000000000000)
        assert post['lastGoodIndex'][0]=='1000000000000000000'
        if k in ('VA2','VA3','VB1'): assert pre['lastGoodPrice']==post['lastGoodPrice']
        if k=='VA3': assert any(s['op']=='REVERT' for s in t['structLogs'])
        basis='Bound schedule/source, cache/status pre/post, ordered target update events and retained trace; numeric equality is not used to label provenance.'
    elif k.startswith('A'):
        main=k in ('AA0','AA1','AA4','AB0','AB2')
        assert post['rawUnderlying'][2] is main
        assert words[0]==(1200000000000000000000000000000 if k=='AB0' else 1000000000000000000000000000000)
        assert pre==post # designated primary is a pure read
        if k=='AA3':
            old=read(G6/'deployed/AA2.json')['post'];assert pre['main']==old['main'] and pre['raw1']!=old['raw1'] and pre['raw2']==old['raw2']
        if k=='AA4': assert pre['main']!=read(G6/'deployed/AA3.json')['post']['main']
        basis='Public source boolean, raw reporter/aggregate records and setup-prefix MainFeedFail/MainFeedSync receipts; updates attributed to prefix, not pure primary read.'
    else:
        assert words[0]==27936237197953895
        if k=='FC0': assert pre==post and o1[1] is True
        if k=='FC1': assert pre['delayedPrice']!=post['delayedPrice'] and pre['latestPrice']!=post['latestPrice'] and o1[1] is True
        if k in ('FC2','FC3'):
            assert pre==post and post['isPriceOk'][0] is (k=='FC2') and post['isPriceFresh'][0] is (k=='FC2')
        basis='Exact-source temporal predicates, retained records and public validity getters; FC0/1 complete tuple preserved; no inference for absent F_A/F_B episodes.'
    row.update(adjudication='COMPATIBLE_AFTER_DERIVED_RETURN_DECODING',witness_basis=basis,evidence_label='DERIVED_RESULT_SUPPORTED_BY_FROZEN_EXECUTION')
    adjud.append(row);data[k]={'O1':o1,'O2':o2,'O3':o3,'Y':r['Y'],'d':d}
    norm.append({'case_id':k,'O1':o1,'O2':o2,'O3_trace_sha256':sha(tp),'Y':r['Y']})
csvwrite('G7_RETURN_DECODING_CORRECTED_DERIVED.csv',decoded)
csvwrite('G7_CONDITION_LEVEL_ADJUDICATION.csv',adjud)
dump('G7_NORMALIZED_OBSERVATIONS.json',norm)
split_witness={'PV01':'status 0->0 versus 0->1 and events','PV02':'cache/status pre/post and events','PV03':'pre-status/transition events differ; does not isolate trigger independently of history','PV04':'status 0->1 versus 1->0','PV05':'returned 1.2e18 versus 1e18','PV06':'different retained price histories within same Y enumeration','PA01':'isFromMainFeed true versus false','PA02':'isFromMainFeed and prefix history','PA03':'raw1 updated with aggregate unchanged; prefix MainFeedFail','PA04':'MainFeedSync/aggregate refresh and isFromMainFeed','PA05':'returned 1.2e30 versus 1e30','PA06':'isFromMainFeed false versus true','PA07':'main/raw cache values differ despite same Y and same backup return','PF06':'delayed/latest timestamps and lastUpdateTS change','PF07':'isPriceFresh/isPriceOk true versus false'}
prs=[]
for p in pairs:
    a,b=p['left_case'],p['right_case'];ok=a in data and b in data
    row={**p,'status':'EVALUABLE' if ok else 'NOT_COMPARABLE_TECHNICAL_MISSINGNESS','Y_equal':'NA','O1_equal':'NA','O2_equal':'NA','O3_equal':'NA','O2_informative_split':False,'O3_informative_split':False,'construction_result':'NOT_EVALUABLE','separating_evidence':split_witness.get(p['pair_id'],'Endpoint absent/invalid; not a negative result')}
    if ok:
        eq=[canon(data[a][x])==canon(data[b][x]) for x in ('Y','O1','O2','O3')]
        assert eq[0]==(p['predeclared_Y_relation']!='DIFFERENT')
        row.update(Y_equal=eq[0],O1_equal=eq[1],O2_equal=eq[2],O3_equal=eq[3],O2_informative_split=not eq[0] and eq[1] and not eq[2],O3_informative_split=not eq[0] and eq[2] and not eq[3],construction_result='MATCHES_PREDECLARED_NUMERIC_RELATION')
        assert eq[1]==p['numeric_relation_design'].startswith('COLLISION')
    prs.append(row)
csvwrite('G7_PREDECLARED_PAIR_RESULTS.csv',prs)
parts=[]
for layer in ('O1','O2','O3'):
    rows=[]
    for prefix,imp in [('V','VESTA'),('A','AURIGAMI'),('F','FATHOM')]:
        groups=collections.defaultdict(list)
        for k,x in data.items():
            if k.startswith(prefix):groups[canon(x[layer])].append(k)
        for i,(key,members) in enumerate(groups.items(),1):
            ys=sorted(set(canon(data[k]['Y']) for k in members))
            rows.append({'implementation':imp,'layer':layer,'class_id':f'{prefix}_{layer}_{i}','members':';'.join(members),'member_count':len(members),'Y_labels':canon([json.loads(y) for y in ys]),'Y_label_count':len(ys),'observation_tuple_sha256':hashlib.sha256(key.encode()).hexdigest(),'interpretation':'Finite-matrix class only; singleton is not global semantic identification'})
    csvwrite(f'G7_{layer}_PARTITIONS.csv',rows);parts.extend(rows)
md('G7_Y_ANNOTATED_PARTITIONS.md','# Y-annotated finite partitions\n\nO1 is the full G4 return tuple, including Fathom boolean. No cross-ABI scalarization. O2 events omit transaction/block identity and retain ordered topics/data. O3 uses collected opcode trace with empty nonpublic storage.\n\n| Layer | Implementation | Members | Y labels |\n|---|---|---|---|\n'+'\n'.join(f"| {r['layer']} | {r['implementation']} | {r['members']} | {r['Y_labels']} |" for r in parts)+'\n\nAll O2/O3 classes are singleton in the observed matrix. This is descriptive, not a semantic identification theorem. PV06/PA07 are counterexamples to equating observation distinction with Y distinction.')
md('G7_RETURN_DECODING_CORRECTION.md','# G7 return decoding correction\n\nStatus: DERIVED_ANALYSIS_CORRECTION. No new execution.\n\nThe runner traceTx/traceCall prepended `0x` to an already prefixed returnValue. All 20 valid deployed records contain the duplicate-prefix wrapper; ten pure-call records also record decode_error. Every corresponding frozen trace has legal ABI return bytes and matches a raw RPC trace record. The CSV lists every affected record, original field/error, original trace bytes, full corrected tuple, raw locator and trace digest. G6 files, errors and RPC/trace bytes remain unchanged.\n\nFathom FC0/FC1 preserve `(27936237197953895,true)`; FC2/FC3 preserve the single price tuple. Other records have one uint256 result. No correction to target execution, input, time, reference, selected pair or scenario was made.\n\nThis correction is separate from Compound T2 formula replay and the earlier VE10 action classifier correction. It changes evidence representation, not deployed behavior.\n\nAffected IDs: '+', '.join(x['case_id'] for x in decoded)+'.')
md('G7_MISSINGNESS_AND_NONCOMPARABILITY.md','# Missingness and non-comparability\n\n27 planned/attempted conditions; 20 valid executions; 7 technical non-comparable: FA0–FA3, FB0–FB2.\n21 predeclared pairs; 15 evaluable; 6 non-comparable: PF01, PF02, PF03, PF04, PF05, PF08.\n\nFailures concentrate in Fathom F_A/F_B: archive rate limits/missing trie and invalid inherited episode history. They are not random missingness, oracle reverts, or negative mechanism results. FC0–FC3 are the independently initialized valid F_C episode. No endpoint substitution, rerun or value tuning is used in this analysis.\n\nThe missing pairs prevent execution claims about Fathom caught-error behavior, different-price history, and complete delayed-state characterization. Denominators remain separate for implementations, episodes, conditions and pairs.')
md('G7_NUISANCE_CONTROL_RESULTS.md','# Nuisance controls\n\nPV06: VA2/VB1 share frozen Y enumeration but have different legal cached-price histories; O1 and O2 differ.\nPA07: AA2/AB1 share frozen Y and the same backup numeric return, but retained main/raw records differ, so O2 differs.\n\nThese predeclared controls demonstrate that distinct complete observation tuples need not denote distinct Y categories. No accuracy/precision/recall or global identifiability is calculated. PV03 also differs in transition history, so an O2 split there does not isolate stale versus call-failure cause at otherwise equal state.')
counts={'planned_conditions':27,'valid_execution_records':len(data),'technical_noncomparable':len(cases)-len(data),'predeclared_pairs':len(prs),'evaluable_pairs':sum(r['status']=='EVALUABLE' for r in prs),'noncomparable_pairs':sum(r['status']!='EVALUABLE' for r in prs),'different_Y_evaluable':sum(r['Y_equal'] is False for r in prs),'O1_collisions_among_different_Y':sum(r['Y_equal'] is False and r['O1_equal'] is True for r in prs),'noncollision_different_Y_controls':sum(r['Y_equal'] is False and r['O1_equal'] is False for r in prs),'O2_informative_splits':sum(r['O2_informative_split'] for r in prs),'O3_additional_splits':sum(r['O3_informative_split'] for r in prs)}
assert list(counts.values())==[27,20,7,21,15,6,13,11,2,11,0],counts
assert len(decoded)==20 and all(sha(pathlib.Path(p))==h for p,h in baseline.items())
dump('G7_DERIVATION_VERIFICATION.json',{'status':'PASS','counts':counts,'input_manifest_files':722,'protected_G4_G5':189,'all_input_hashes_unchanged':True,'raw_trace_match_count':20,'full_tuple_preserved':True,'all_predeclared_numeric_relations_evaluable_match':True,'formal_execution':'CLOSED','manuscript_revision':'NOT_STARTED_IN_THIS_SCRIPT'})
outputs=[{'path':f.name,'sha256':sha(f)} for f in sorted(OUT.iterdir()) if f.is_file() and f.name!='G7_FINAL_DERIVED_ANALYSIS_LOCK.json']
dump('G7_FINAL_DERIVED_ANALYSIS_LOCK.json',{'status':'SEALED','schema':'g7-derived-analysis-lock-v1','counts':counts,'O1':'FULL_RETURN_TUPLE_AS_FROZEN_IN_G4','evidence':'DERIVED_RESULT_FROM_FROZEN_G6','correction':'DUPLICATE_HEX_PREFIX_ANALYSIS_ONLY','reference_scope':'Predeclared source/schedule labels, not an independently executed complete simulator','lineage_scope':'BOUNDED_PUBLIC_PROVENANCE','files':outputs,'new_execution':False,'forbidden':['accuracy','precision','recall','success rate','information recovery rate','ecosystem prevalence','O2 universal sufficiency','O3 necessity','full Fathom state machine','joint temporal/enforcement established']})
print(json.dumps({'status':'PASS','counts':counts,'files':len(outputs)+1}))
