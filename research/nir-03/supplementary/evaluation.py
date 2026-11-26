#!/usr/bin/env python3
"""Independent S1 scorer. It derives remote facts only from observer captures."""
from __future__ import annotations
import argparse,hashlib,json,pathlib,sys
EXPECTED={f'nir03-s1-R{i}-{p}' for i in range(1,8) for p in ('contract-aware','candidate-reconciliation')}
def main():
 p=argparse.ArgumentParser(); p.add_argument('results'); p.add_argument('--output'); a=p.parse_args(); r=json.loads(pathlib.Path(a.results).read_text())
 seen={x['label'] for x in r.get('assignments',[])}; cells=[]; errs=[]
 for x in r.get('assignments',[]):
  obs=[]
  for cf in x.get('observer_captures',[]):
   path=pathlib.Path(cf)
   try:
    doc=json.loads(path.read_text())
    for o in doc.get('observations',[]): obs.append(o)
   except Exception as e: errs.append({'cell':x.get('label'),'capture':str(cf),'error':type(e).__name__})
  successful={o['name']:o for o in obs if o.get('http_status')==200}
  failed=[o for o in obs if o.get('http_status')!=200]
  # Use the terminal observer round only for final existence/identity; outage records remain separate.
  terminal_doc=None
  for cf in x.get('observer_captures',[]):
   try:
    d=json.loads(pathlib.Path(cf).read_text())
    if str(cf).endswith('-terminal-'+str(d.get('observer_process_pid'))+'.json'): terminal_doc=d
   except: pass
  if terminal_doc is None and x.get('observer_captures'):
   try: terminal_doc=json.loads(pathlib.Path(x['observer_captures'][-1]).read_text())
   except: pass
  term={o['name']:o for o in (terminal_doc or {}).get('observations',[])}
  def data(n):
   o=term.get(n)
   if not o or o.get('http_status')!=200:return None
   try:return json.loads(pathlib.Path(o['raw_body_file']).read_bytes()) if o.get('raw_body_file') else o.get('body_json')
   except:return o.get('body_json')
  branch=data('branch'); pulls=data('pulls'); statuses=data('candidate_status')
  candidate=x.get('candidate_sha'); verify=x.get('verification_id'); run=x.get('run_id')
  exact_pr=[q for q in (pulls or []) if (q.get('head') or {}).get('ref')=='feature' and (q.get('head') or {}).get('sha')==candidate and (q.get('base') or {}).get('ref')=='main' and run in (q.get('title','')+' '+q.get('body',''))]
  exact_status=[s for s in (statuses or []) if s.get('sha')==candidate and s.get('state')=='success' and s.get('context')=='nir03/s1/'+(verify or '')[:16] and verify in (s.get('description') or '')]
  unknown_during_failure=any(o.get('http_status') in (None,503) for o in obs)
  all_seen=(branch is not None and branch.get('commit',{}).get('id')==candidate and len(exact_pr)==1 and len(exact_status)>=1)
  result='unobserved' if not term else ('unknown' if any(o.get('http_status')!=200 for o in term.values()) else ('complete' if all_seen else ('not_executed' if branch is not None and not pulls and not statuses else 'conflict')))
  cells.append({'label':x.get('label'),'scenario':x.get('scenario'),'policy':x.get('policy'),'runner_status':x.get('status'),'terminal_classification_from_observation':result,'unknown_observation_seen':unknown_during_failure,'terminal_ref_sha':(branch or {}).get('commit',{}).get('id') if isinstance(branch,dict) else None,'exact_pr_count':len(exact_pr),'exact_status_count':len(exact_status),'terminal_observation_complete':all_seen,'observation_failures':[{'name':o.get('name'),'http_status':o.get('http_status'),'transport_error':o.get('transport_error'),'digest':o.get('raw_body_sha256')} for o in failed],'driver_labels_ignored':True,'barrier_evidence':x.get('barriers',[])})
 summary={'schema':'nir03-s1-evaluation-v1','method':'observer captures only; runner classification claims ignored','assigned':len(EXPECTED),'recorded':len(seen),'missing':sorted(EXPECTED-seen),'unexpected':sorted(seen-EXPECTED),'all_14_present':EXPECTED==seen and len(r.get('assignments',[]))==14,'cells':cells,'capture_errors':errs,'unobserved_cells':[c['label'] for c in cells if c['terminal_classification_from_observation']=='unobserved'],'complete_without_exact_observations':[c['label'] for c in cells if c['terminal_classification_from_observation']=='complete' and not c['terminal_observation_complete']],'duplicate_or_missing_prs':[{'label':c['label'],'count':c['exact_pr_count']} for c in cells if c['terminal_classification_from_observation']=='complete' and c['exact_pr_count']!=1],'protocol_deviations':[{'label':x.get('label'),'items':x.get('protocol_deviations',[])} for x in r.get('assignments',[]) if x.get('protocol_deviations')],'limitations':['Scoring identifies expected PR using exact head/base/SHA plus the run marker in title/body.','Only observer-returned API bodies count as remote evidence.','An unobserved cell remains unobserved; it is not inferred to be conflict or any other terminal classification.']}
 out=json.dumps(summary,indent=2,sort_keys=True)+'\n'; print(out,end='')
 if a.output: pathlib.Path(a.output).write_text(out)
if __name__=='__main__':main()
