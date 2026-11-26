#!/usr/bin/env python3
"""Frozen S1 assignment driver. All state and credentials live outside Git."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, http.client, http.server, json, os, pathlib, signal, subprocess, sys, tempfile, threading, time, urllib.error, urllib.parse, urllib.request, uuid
from git_env import build_git_environment, redact_git_error

OWNER='researcher'; POLICIES=('contract-aware','candidate-reconciliation')
SCENARIOS=tuple('R'+str(i) for i in range(1,8))
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def api(url,token,method,path,body=None,timeout=8):
    raw=None if body is None else json.dumps(body).encode(); h={'Authorization':'token '+token,'Accept':'application/json'}
    if raw is not None: h['Content-Type']='application/json'
    q=urllib.request.Request(url.rstrip('/')+'/api/v1/'+path.lstrip('/'),data=raw,headers=h,method=method)
    try:
        with urllib.request.urlopen(q,timeout=timeout) as r: b=r.read(); return r.status,b
    except urllib.error.HTTPError as e: return e.code,e.read()
def parsed(pair):
    try:return json.loads(pair[1])
    except:return None
class Proxy(http.server.ThreadingHTTPServer): daemon_threads=True
class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def handle_request(self):
        n=int(self.headers.get('Content-Length','0')); payload=self.rfile.read(n) if n else None
        rules=self.server.rules; fault=next((x for x in rules if x['active'] and self.command==x['method'] and x['match'] in self.path),None)
        stamp={'time':now(),'method':self.command,'path':self.path,'fault':fault['name'] if fault else None}
        self.server.events.append(stamp)
        if fault and fault.get('mode')=='503':
            fault['active']=False if fault.get('once') else True; body=b'{"message":"S1 injected observer outage"}'
            stamp.update({'response_status':503,'response_body_sha256':hashlib.sha256(body).hexdigest(),'response_bytes':len(body)})
            self.send_response(503); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        conn=http.client.HTTPConnection(self.server.target.hostname,self.server.target.port,timeout=12)
        headers={k:v for k,v in self.headers.items() if k.lower() not in {'host','connection','content-length'}}
        conn.request(self.command,self.path,payload,headers); r=conn.getresponse(); body=r.read(); rh=r.getheaders(); status=r.status; conn.close()
        stamp.update({'upstream_status':status,'upstream_body_sha256':hashlib.sha256(body).hexdigest(),'upstream_response_bytes':len(body)})
        if fault and fault.get('mode')=='forward-drop':
            fault['active']=False; stamp['upstream_status']=status; stamp['ack_dropped']=True; self.server.barriers.append({'barrier':'upstream_effect_committed_ack_dropped','time':now(),'status':status,'path':self.path}); self.close_connection=True; return
        self.send_response(status)
        for k,v in rh:
            if k.lower() in {'content-type','content-length'}: self.send_header(k,v)
        if not any(k.lower()=='content-length' for k,v in rh): self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    do_GET=handle_request; do_POST=handle_request; do_PATCH=handle_request; do_PUT=handle_request; do_DELETE=handle_request

def main():
    p=argparse.ArgumentParser(); p.add_argument('--base-url'); p.add_argument('--owner-token-file'); p.add_argument('--observer-token-file'); p.add_argument('--capture-dir'); p.add_argument('--output'); p.add_argument('--repo-prefix',default='nir03-s1'); p.add_argument('--label-prefix',default='nir03-s1'); p.add_argument('--experiment-id',default='S1'); p.add_argument('--protocol',default='research/nir-03/supplementary/PREREGISTRATION.md'); p.add_argument('--worker-stage'); p.add_argument('--worker-repo'); p.add_argument('--worker-candidate'); p.add_argument('--worker-run'); p.add_argument('--worker-intent'); a=p.parse_args()
    if a.worker_stage: worker(a); return
    for field in ('base_url','owner_token_file','observer_token_file','capture_dir','output'):
        if not getattr(a,field): raise SystemExit('--'+field.replace('_','-')+' is required')
    base=a.base_url.rstrip('/'); owner_token=pathlib.Path(a.owner_token_file).read_text().strip(); observer_token=pathlib.Path(a.observer_token_file).read_text().strip(); out=pathlib.Path(a.output); out.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    captures=pathlib.Path(a.capture_dir); captures.mkdir(mode=0o700,parents=True,exist_ok=True); os.chmod(captures,0o700)
    target=urllib.parse.urlsplit(base); events=[]; barriers=[]; rules=[]
    server=Proxy(('127.0.0.1',0),ProxyHandler); server.target=target; server.rules=rules; server.events=events; server.barriers=barriers
    threading.Thread(target=server.serve_forever,daemon=True).start(); proxy=f'http://127.0.0.1:{server.server_address[1]}'
    version=api(base,owner_token,'GET','/version'); version_doc=parsed(version)
    if version[0]!=200 or '17.0.2' not in str(version_doc): raise SystemExit('Forgejo version preflight failed')
    assignments=[]
    for scenario in SCENARIOS:
      for policy in POLICIES:
        label=f'{a.label_prefix}-{scenario}-{policy}'; repo=f'{a.repo_prefix}-{scenario.lower()}-{policy[:3]}'.replace('_','-')[:100]
        row={'label':label,'scenario':scenario,'policy':policy,'repository':repo,'started_at':now(),'status':'started','proxy_url':proxy,'mutation_trace':[],'provider_mutations':[],'observer_captures':[],'barriers':[],'driver_claimed_classifications':[],'protocol_deviations':[]}
        assignments.append(row); rules.clear(); events.clear(); barriers.clear()
        base_sha=candidate_sha=competitor_sha=verify=None
        try:
            endpoint='/user/repos'; response=api(base,owner_token,'POST',endpoint,{'name':repo,'private':True,'auto_init':False,'default_branch':'main'}); st,b=response
            row['provider_mutations'].append(response_metadata(base,'POST',endpoint,response))
            if st not in (200,201): raise RuntimeError('repo creation HTTP '+str(st))
            # Separate ordinary account with repository read-only collaborator permission.
            endpoint=f'/repos/{OWNER}/{repo}/collaborators/s1-observer'; response=api(base,owner_token,'PUT',endpoint,{'permission':'read'}); st,b=response
            row['provider_mutations'].append(response_metadata(base,'PUT',endpoint,response))
            if st not in (201,204,200): row['protocol_deviations'].append(f'read collaborator grant HTTP {st}')
            runid=label
            identities={}
            def persist_predispatch(base_id,candidate_id,competitor_id,object_format):
                verify_id=hashlib.sha256(f'NIR03-S1-VERIFIED\n{runid}\n{candidate_id}\n'.encode()).hexdigest()
                intent={'schema':'nir03-s1-intent-v1','label':label,'repository':repo,'base_sha':base_id,'candidate_sha':candidate_id,'verification_id':verify_id,'object_format':object_format,'expected_effects':['feature ref at candidate','one exact PR','exact status receipt'],'created_at':now()}
                atomic(out.parent/(label+'.intent.json'),intent)
                identities.update({'verification_id':verify_id,'intent':intent})
                row.update({'run_id':runid,'base_sha':base_id,'candidate_sha':candidate_id,'verification_id':verify_id,'object_format':object_format,'intent_sha256':hashlib.sha256(json.dumps(intent,sort_keys=True).encode()).hexdigest()})
                if policy=='candidate-reconciliation':
                    atomic(out.parent/(label+'.candidate-ledger.json'),{'schema':'nir03-s1-ledger-v1','run_id':runid,'candidate_sha':candidate_id,'verification_id':verify_id,'expected_effects':{'ref':'unknown','pull_request':'unknown','status':'unknown'},'classification':'unknown','reason':'durable pre-dispatch intent; no authoritative recovery observations yet','updated_at':now()})
            base_sha,candidate_sha,competitor_sha,object_format,branch_visibility=make_fixture_and_push(base,owner_token,a.owner_token_file,repo,runid,scenario,predispatch=persist_predispatch)
            verify=identities['verification_id']
            ledger_path=out.parent/(label+'.candidate-ledger.json')
            intent=identities['intent']
            row.update({'run_id':runid,'base_sha':base_sha,'candidate_sha':candidate_sha,'verification_id':verify,'object_format':intent['object_format'],'intent_sha256':hashlib.sha256(json.dumps(intent,sort_keys=True).encode()).hexdigest()})
            row['fixture_branch_visibility']=branch_visibility
            if scenario not in ('R1',):
                row['mutation_trace'].append({'effect':'feature_ref','sha':competitor_sha if scenario=='R6' else candidate_sha,'time':now()})
            if scenario in ('R2','R3','R5','R7'):
                status_result=make_status(base,owner_token,repo,candidate_sha,verify)
                row['provider_mutations'].append(response_metadata(base,'POST',f'/repos/{OWNER}/{repo}/statuses/{candidate_sha}',status_result))
                if status_result[0] not in (200,201): raise RuntimeError(f'status setup HTTP {status_result[0]}')
                row['mutation_trace'].append({'effect':'status','http_status':status_result[0],'time':now()})
            if scenario in ('R2','R3','R7'):
                pr_result=make_pr(base,owner_token,repo,runid)
                row['provider_mutations'].append(response_metadata(base,'POST',f'/repos/{OWNER}/{repo}/pulls',pr_result))
                if pr_result[0] not in (200,201): raise RuntimeError(f'pull request setup HTTP {pr_result[0]}')
                row['mutation_trace'].append({'effect':'pull_request_seed','http_status':pr_result[0],'time':now()})
            if scenario=='R4':
                status_result=make_status(base,owner_token,repo,candidate_sha,verify)
                row['provider_mutations'].append(response_metadata(base,'POST',f'/repos/{OWNER}/{repo}/statuses/{candidate_sha}',status_result))
                if status_result[0] not in (200,201): raise RuntimeError(f'R4 status setup HTTP {status_result[0]}')
                rules.append({'name':'R4-forward-drop-create','method':'POST','match':f'/repos/{OWNER}/{repo}/pulls','mode':'forward-drop','active':True,'once':True})
                try:
                    response=api(proxy,owner_token,'POST',f'/repos/{OWNER}/{repo}/pulls',pr_body(runid),timeout=2)
                    row['provider_mutations'].append(response_metadata(proxy,'POST',f'/repos/{OWNER}/{repo}/pulls',response))
                except Exception as e: row['mutation_trace'].append({'effect':'ambiguous_create','transport_error':type(e).__name__,'acknowledgement':'dropped by proxy','time':now()})
                row['barriers'].extend(barriers)
            if scenario=='R6': row['mutation_trace'].append({'effect':'competing_ref','sha':competitor_sha,'time':now()})
            if scenario=='R5':
                for stage,barrier in [('read','after_first_remote_read'),('dispatch','after_first_missing_effect_dispatch'),('classify','before_final_durable_classification')]:
                    run_interrupted_worker(stage,proxy,a.owner_token_file,repo,candidate_sha,runid,out.parent/(label+'.intent.json'),row)
            # Fault rules are endpoint-specific and one-shot; each is captured by a separate observer subprocess.
            names=['branch'] if scenario in ('R1','R6') else (['pulls'] if scenario in ('R2','R4') else (['candidate_status'] if scenario in ('R3',) else (['branch','pulls','candidate_status'] if scenario=='R7' else [])))
            for name in names:
                fragment={'branch':f'/branches/feature','pulls':'/pulls?','candidate_status':f'/statuses/{candidate_sha}'}[name]
                rules.append({'name':scenario+'-'+name,'method':'GET','match':fragment,'mode':'503','active':True,'once':True})
                cap=observe(proxy,a.observer_token_file,repo,candidate_sha,base_sha,captures,label+'-'+name+'-outage')
                row['observer_captures'].append(cap)
                row['driver_claimed_classifications'].append('unknown')
                row['barriers'].append({'barrier':'fault_503_observed_by_independent_process','endpoint_class':name,'capture':pathlib.Path(cap).name,'time':now()})
                if policy=='candidate-reconciliation': atomic(ledger_path,{'schema':'nir03-s1-ledger-v1','run_id':runid,'candidate_sha':candidate_sha,'verification_id':verify,'expected_effects':{'ref':'unknown','pull_request':'unknown','status':'unknown'},'classification':'unknown','reason':'required independent read returned HTTP 503','failed_endpoint':name,'updated_at':now()})
                # R7 is a sequence: clear remaining fault rules only after each fault was recorded and repeat.
            rules.clear()
            # Recovery uses exact provider reads. R5's sole missing effect is dispatched only
            # after authoritative reads establish the candidate ref, status and absent PR.
            reads=recovery_reads(proxy,owner_token,repo,candidate_sha)
            row['recovery_reads']=reads
            if scenario=='R5' and reads.get('branch_sha')==candidate_sha and reads.get('candidate_status_http')==200 and reads.get('exact_pr_count')==0:
                recovery_endpoint=f'/repos/{OWNER}/{repo}/pulls'; recovery_response=api(proxy,owner_token,'POST',recovery_endpoint,pr_body(runid)); ps,pb=recovery_response
                row['provider_mutations'].append(response_metadata(proxy,'POST',recovery_endpoint,recovery_response))
                row['mutation_trace'].append({'effect':'recovery_pr_dispatch','http_status':ps,'time':now()})
                row['barriers'].append({'barrier':'first_missing_effect_dispatch_response_observed','http_status':ps,'time':now(),'synchronization':'provider HTTP response boundary'})
                # The next read is the recovery restart's final reconciliation boundary.
                reads=recovery_reads(proxy,owner_token,repo,candidate_sha); row['recovery_reads_after_dispatch']=reads
            terminal=observe(proxy,a.observer_token_file,repo,candidate_sha,base_sha,captures,label+'-terminal')
            row['observer_captures'].append(terminal)
            terminal_outcome=derive_terminal(proxy,owner_token,repo,candidate_sha,runid,verify,base_sha)
            row['driver_claimed_classifications'].append(terminal_outcome['classification'])
            row['terminal_recovery_observations']=terminal_outcome
            if policy=='candidate-reconciliation': atomic(ledger_path,{'schema':'nir03-s1-ledger-v1','run_id':runid,'candidate_sha':candidate_sha,'verification_id':verify,'expected_effects':terminal_outcome['effects'],'classification':terminal_outcome['classification'],'reason':'classification persisted after recovery reads','updated_at':now()})
            row['proxy_events']=list(events); row['barriers'].extend(barriers); row['ended_at']=now(); row['status']='executed'
        except Exception as e:
            row['status']='blocked'; row['error']={'type':type(e).__name__,'message':str(e).replace(owner_token,'[REDACTED]')[:500]}; row['ended_at']=now()
            if candidate_sha and base_sha:
                try: row['observer_captures'].append(observe(proxy,a.observer_token_file,repo,candidate_sha,base_sha,captures,label+'-blocked-terminal'))
                except Exception as _e: row['protocol_deviations'].append('terminal observer failed: '+type(_e).__name__)
        row['proxy_events']=list(events); row['barriers'].extend(barriers)
    clean_env=clean_python_environment()
    result={'schema':'nir03-s1-results-v1','experiment_id':a.experiment_id,'protocol':a.protocol,'label_prefix':a.label_prefix,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True,env=clean_env).strip(),'tool_versions':{'python':sys.version,'git':subprocess.check_output(['git','--version'],text=True,env=clean_env).strip(),'forgejo':version_doc},'environment':{'provider_origin':base,'proxy_origin':proxy,'read_only_observer_account':'s1-observer','observer_credential_scope':'read:repository,read:user'},'assignments':assignments,'ended_at':now()}
    atomic(out,result); server.shutdown()

def atomic(path,obj):
    path=pathlib.Path(path); path.parent.mkdir(mode=0o700,parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp'); fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f: json.dump(obj,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)
def response_metadata(base_url,method,path,response):
    status,body=response
    return {'time':now(),'method':method,'endpoint':base_url.rstrip('/')+'/api/v1/'+path.lstrip('/'),'http_status':status,'response_body_sha256':hashlib.sha256(body).hexdigest(),'response_body_bytes':len(body)}
def pr_body(marker):return {'head':f'{OWNER}:feature','base':'main','title':'NIR-03 S1 '+marker,'body':'Disposable preregistered synthetic publication '+marker}
def make_pr(base,tok,repo,marker): return api(base,tok,'POST',f'/repos/{OWNER}/{repo}/pulls',pr_body(marker))
def make_status(base,tok,repo,sha,verify): return api(base,tok,'POST',f'/repos/{OWNER}/{repo}/statuses/{sha}',{'state':'success','context':'nir03/s1/'+verify[:16],'description':'Synthetic S1 receipt '+verify})
def observe(url,tokfile,repo,sha,base_sha,capdir,label):
    cmd=[sys.executable,str(pathlib.Path(__file__).with_name('observer.py')),'--base-url',url,'--token-file',tokfile,'--repo',repo,'--candidate-sha',sha,'--base-sha',base_sha,'--capture-dir',str(capdir),'--label',label]
    # Separate interpreter/process; capture observer stdout only (capture path).
    r=subprocess.run(cmd,text=True,capture_output=True,timeout=45,env=clean_python_environment())
    if r.returncode: raise RuntimeError('observer process failed: '+r.stderr[-300:])
    return r.stdout.strip()
def recovery_reads(url,token,repo,candidate):
    q=urllib.parse.urlencode({'state':'all','head':'feature','base':'main'})
    out={}
    for n,path in [('branch',f'/repos/{OWNER}/{repo}/branches/feature'),('pulls',f'/repos/{OWNER}/{repo}/pulls?{q}'),('candidate_status',f'/repos/{OWNER}/{repo}/statuses/{candidate}')]:
        st,raw=api(url,token,'GET',path); d=None
        try:d=json.loads(raw)
        except:pass
        out[n+'_http']=st
        if n=='branch': out['branch_sha']=(d or {}).get('commit',{}).get('id') if isinstance(d,dict) else None
        elif n=='pulls': out['exact_pr_count']=sum(1 for x in (d or []) if (x.get('head') or {}).get('ref')=='feature' and (x.get('head') or {}).get('sha')==candidate and (x.get('base') or {}).get('ref')=='main') if isinstance(d,list) else None
        else: out['status_count']=len(d) if isinstance(d,list) else None
    return out
def derive_terminal(url,token,repo,candidate,runid,verify,base_sha):
    rr=recovery_reads(url,token,repo,candidate); q=urllib.parse.urlencode({'state':'all','head':'feature','base':'main'})
    ps,praw=api(url,token,'GET',f'/repos/{OWNER}/{repo}/pulls?{q}'); ss,sraw=api(url,token,'GET',f'/repos/{OWNER}/{repo}/statuses/{candidate}')
    try: pulls=json.loads(praw)
    except: pulls=None
    try: statuses=json.loads(sraw)
    except: statuses=None
    exact=[x for x in pulls if (x.get('head') or {}).get('ref')=='feature' and (x.get('head') or {}).get('sha')==candidate and (x.get('base') or {}).get('ref')=='main' and runid in (x.get('title','')+' '+x.get('body',''))] if isinstance(pulls,list) else []
    ctx='nir03/s1/'+verify[:16]
    # Forgejo's status-list response omits the SHA; the exact SHA is identified
    # by the GET resource path /statuses/{candidate} recorded by the observer.
    exact_s=[x for x in statuses if x.get('status',x.get('state'))=='success' and x.get('context')==ctx and verify in (x.get('description') or '')] if isinstance(statuses,list) else []
    ref=rr.get('branch_sha'); effects={'ref':'observed_candidate' if ref==candidate else ('observed_base' if ref==base_sha else ('observed_competing' if ref else ('observed_absent' if rr.get('branch_http')==404 else 'unknown'))),'pull_request':'observed_exact' if len(exact)==1 else ('observed_absent' if ps==200 and not exact else 'unknown'),'status':'observed_exact' if exact_s else ('observed_absent' if ss==200 and not statuses else 'unknown')}
    if None in (rr.get('branch_http'),ps,ss) or rr.get('branch_http') not in (200,404) or ps!=200 or ss!=200: cls='unknown'
    elif effects['ref']=='observed_competing': cls='conflict'
    elif effects['ref']=='observed_base' and not pulls and not statuses: cls='not_executed'
    elif effects['ref']=='observed_absent' and not pulls and not statuses: cls='not_executed'
    elif effects['ref']=='observed_candidate' and len(exact)==1 and exact_s: cls='complete'
    else: cls='unknown'
    return {'classification':cls,'effects':effects,'ref_sha':ref,'pull_http':ps,'status_http':ss,'exact_pr_count':len(exact),'exact_status_count':len(exact_s),'recovery_reads':rr}
def run_interrupted_worker(stage,url,tokenfile,repo,candidate,runid,intent,row):
    cmd=[sys.executable,str(pathlib.Path(__file__).resolve()),'--worker-stage',stage,'--base-url',url,'--owner-token-file',tokenfile,'--worker-repo',repo,'--worker-candidate',candidate,'--worker-run',runid,'--worker-intent',str(intent)]
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1,env=clean_python_environment())
    expected={'read':'after_first_remote_read','dispatch':'after_first_missing_effect_dispatch','classify':'before_final_durable_classification'}[stage]
    line=proc.stdout.readline().strip()
    stamp=now()
    try: event=json.loads(line)
    except Exception: event={'barrier':line.removeprefix('BARRIER ')}
    if event.get('barrier')!=expected:
        proc.kill(); proc.wait(); row['protocol_deviations'].append(f'R5 worker failed to reach synchronization barrier {expected}: {line[:120]}'); return
    os.kill(proc.pid,signal.SIGKILL); proc.wait(timeout=5)
    row['barriers'].append({'barrier':expected,'pid':proc.pid,'worker_exit':proc.returncode,'time':stamp,'kill_confirmed':proc.returncode==-signal.SIGKILL,'worker_event':event})
def worker(a):
    tok=pathlib.Path(a.owner_token_file).read_text().strip(); q=urllib.parse.urlencode({'state':'all','head':'feature','base':'main'})
    if a.worker_stage=='read':
        path=f'/repos/{OWNER}/{a.worker_repo}/branches/feature'; resp=api(a.base_url,tok,'GET',path)
        print(json.dumps({'barrier':'after_first_remote_read','provider_response':response_metadata(a.base_url,'GET',path,resp),'time':now()}),flush=True)
    elif a.worker_stage=='dispatch':
        get_path=f'/repos/{OWNER}/{a.worker_repo}/pulls?{q}'; read_response=api(a.base_url,tok,'GET',get_path); st,raw=read_response
        pulls=[]
        try:pulls=json.loads(raw)
        except:pass
        exact=[x for x in pulls if (x.get('head') or {}).get('ref')=='feature' and (x.get('head') or {}).get('sha')==a.worker_candidate and (x.get('base') or {}).get('ref')=='main'] if isinstance(pulls,list) else []
        dispatch_response=None; dispatch_path=f'/repos/{OWNER}/{a.worker_repo}/pulls'
        if st==200 and not exact: dispatch_response=api(a.base_url,tok,'POST',dispatch_path,pr_body(a.worker_run))
        print(json.dumps({'barrier':'after_first_missing_effect_dispatch','read_response':response_metadata(a.base_url,'GET',get_path,read_response),'dispatch_response':response_metadata(a.base_url,'POST',dispatch_path,dispatch_response) if dispatch_response else None,'time':now()}),flush=True)
    else:
        observations=recovery_reads(a.base_url,tok,a.worker_repo,a.worker_candidate)
        print(json.dumps({'barrier':'before_final_durable_classification','recovery_reads':observations,'time':now()}),flush=True)
    time.sleep(60)
def clean_python_environment():
    return {'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':os.environ.get('HOME','/tmp'),'LC_ALL':'C','TZ':'UTC','PYTHONIOENCODING':'utf-8'}
def wait_for_branch_visibility(base,token,repo,branch,expected_sha,timeout=15):
    deadline=time.monotonic()+timeout; evidence=[]
    while True:
        status,raw=api(base,token,'GET',f'/repos/{OWNER}/{repo}/branches/{branch}')
        body=None
        try: body=json.loads(raw)
        except: pass
        observed=(body or {}).get('commit',{}).get('id') if isinstance(body,dict) else None
        evidence.append({'time':now(),'http_status':status,'sha':observed})
        if status==200:
            if observed!=expected_sha: raise RuntimeError(f'provider branch SHA mismatch: expected {expected_sha}, observed {observed}')
            return evidence
        if status!=404: raise RuntimeError(f'provider branch visibility read HTTP {status}')
        if time.monotonic()>=deadline: raise RuntimeError(f'provider branch did not become visible within {timeout}s')
        time.sleep(0.25)
def make_fixture_and_push(base,token,tokenfile,repo,label,scenario,predispatch=None):
    with tempfile.TemporaryDirectory(prefix='nir03-s1-fixture-') as td:
        root=pathlib.Path(td); ask=root/'askpass.sh'; ask.write_text('#!/bin/sh\ncase "$1" in *Username*) echo researcher;; *) cat "$NIR03_TOKEN_FILE";; esac\n'); ask.chmod(0o700)
        env=build_git_environment(token=token,token_file=tokenfile,askpass=ask,home=root)
        def git(*args):
            r=subprocess.run(['git',*args],cwd=root,env=env,text=True,capture_output=True)
            if r.returncode: raise RuntimeError('fixture git failed: '+redact_git_error(r.stderr,token))
            return r.stdout.strip()
        git('init','--initial-branch=main'); git('config','core.autocrlf','false'); git('config','core.filemode','false')
        (root/'base.txt').write_text('NIR-03 S1 synthetic base fixture v1\n'); git('add','base.txt'); git('commit','-m','NIR-03 S1 base fixture'); base_sha=git('rev-parse','HEAD')
        (root/'candidate.txt').write_text('NIR-03 S1 candidate fixture: '+label+'\n'); git('add','candidate.txt'); git('commit','-m','NIR-03 S1 candidate '+label); candidate_sha=git('rev-parse','HEAD')
        competitor_sha=candidate_sha
        if scenario=='R6':
            (root/'competitor.txt').write_text('NIR-03 S1 competing writer fixture\n'); git('add','competitor.txt'); git('commit','-m','NIR-03 S1 competing writer '+label); competitor_sha=git('rev-parse','HEAD')
        object_format=git('rev-parse','--show-object-format')
        if predispatch: predispatch(base_sha,candidate_sha,competitor_sha,object_format)
        git('remote','add','origin',base+'/'+OWNER+'/'+repo+'.git')
        # Local main has advanced to the candidate commit; pin the provider's
        # main ref explicitly to the frozen base identity.
        git('push','origin',base_sha+':refs/heads/main')
        feature_target=base_sha if scenario=='R1' else (competitor_sha if scenario=='R6' else candidate_sha)
        git('push','origin',feature_target+':refs/heads/feature')
        branch_visibility=wait_for_branch_visibility(base,token,repo,'feature',feature_target)
        return base_sha,candidate_sha,competitor_sha,object_format,branch_visibility
if __name__=='__main__': main()
