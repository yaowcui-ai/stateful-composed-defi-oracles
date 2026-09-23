from pathlib import Path
import csv,hashlib,gzip,re,json
P=Path(__file__).resolve().parent
def sha(x):return hashlib.sha256(x).hexdigest()
rows=list(csv.DictReader((P/'SHA256SUMS.csv').open(encoding='utf-8')))
for r in rows:
 f=P/r['path'];assert f.is_file(),r['path'];assert sha(f.read_bytes())==r['sha256'],r['path']
mapping=list(csv.DictReader((P/'EVIDENCE_FILE_MAP.csv').open(encoding='utf-8')))
lookup={r['source_project_path']:r for r in mapping}
for r in mapping:
 b=(P/r['package_path']).read_bytes();b=gzip.decompress(b) if r['encoding']=='gzip' else b
 assert sha(b)==r['projected_content_sha256'],r['package_path']
for name in ['README_REVIEWER.md','SUPPLEMENT_S1_EXTENDED_TEXT.md']:
 text=(P/name).read_text('utf-8')
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if not link.startswith(('http:','https:','#')):assert (P/link.split('#')[0]).exists(),link
audit=P/'project/semantic_explanation_validation_v1/08_targeted_offline_closure_addendum/NONTRIVIAL_LABEL_EVIDENCE_AUDIT.csv'
rs=list(csv.DictReader(audit.open(encoding='utf-8-sig')))
for r in rs:
 for value in r['evidence_locator'].split(';'):
  value=re.sub(r':\d.*$','',value.strip())
  if '*' in value:
   import fnmatch
   pat='semantic_explanation_validation_v1/'+value
   assert any(fnmatch.fnmatch(x,pat) for x in lookup),value
  else:
   key=(value[3:] if value.startswith('../') else 'semantic_explanation_validation_v1/'+value)
   assert key in lookup,key
print(json.dumps({'files_verified':len(rows),'evidence_files':len(mapping),'label_rows_with_resolvable_locators':len(rs),'status':'PASS','network_requests':0,'scientific_executions':0},indent=2))
