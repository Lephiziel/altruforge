#!/usr/bin/env python3
"""Frozen S1 assignment driver. All state and credentials live outside Git."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, http.client, http.server, json, os, pathlib, signal, subprocess, sys, tempfile, threading, time, urllib.error, urllib.parse, urllib.request, uuid

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
            self.send_response(503); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        conn=http.client.HTTPConnection(self.server.target.hostname,self.server.target.port,timeout=12)
        headers={k:v for k,v in self.headers.items() if k.lower() not in {'host','connection','content-length'}}
        conn.request(self.command,self.path,payload,headers); r=conn.getresponse(); body=r.read(); rh=r.getheaders(); status=r.status; conn.close()
        if fault and fault.get('mode')=='forward-drop':
            fault['active']=False; stamp['upstream_status']=status; stamp['ack_dropped']=True; self.server.barriers.append({'barrier':'upstream_effect_committed_ack_dropped','time':now(),'status':status,'path':self.path}); self.close_connection=True; return
        self.send_response(status)
        for k,v in rh:
            if k.lower() in {'content-type','content-length'}: self.send_header(k,v)
        if not any(k.lower()=='content-length' for k,v in rh): self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    do_GET=handle_request; do_POST=handle_request; do_PATCH=handle_request; do_PUT=handle_request; do_DELETE=handle_request

def main():
    p=argparse.ArgumentParser(); p.add_argument('--base-url'); p.add_argument('--owner-token-file'); p.add_argument('--observer-token-file'); p.add_argument('--capture-dir'); p.add_argument('--output'); p.add_argument('--repo-prefix',default='nir03-s1'); p.add_argument('--worker-stage'); p.add_argument('--worker-repo'); p.add_argument('--worker-candidate'); p.add_argument('--worker-run'); p.add_argument('--worker-intent'); a=p.parse_args()
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
        label=f'nir03-s1-{scenario}-{policy}'; repo=f'{a.repo_prefix}-{scenario.lower()}-{policy[:3]}'.replace('_','-')[:100]
        row={'label':label,'scenario':scenario,'policy':policy,'repository':repo,'started_at':now(),'status':'started','proxy_url':proxy,'mutation_trace':[],'observer_captures':[],'barriers':[],'driver_claimed_classifications':[],'protocol_deviations':[]}
        assignments.append(row); rules.clear(); events.clear(); barriers.clear()
        try:
            st,b=api(base,owner_token,'POST','/user/repos',{'name':repo,'private':True,'auto_init':False,'default_branch':'main'})
            if st not in (200,201): raise RuntimeError('repo creation HTTP '+str(st))
            # Separate ordinary account with repository read-only collaborator permission.
            st,b=api(base,owner_token,'PUT',f'/repos/{OWNER}/{repo}/collaborators/s1-observer',{'permission':'read'})
            if st not in (201,204,200): row['protocol_deviations'].append(f'read collaborator grant HTTP {st}')
            runid=label
            base_sha,candidate_sha,competitor_sha=make_fixture_and_push(base,owner_token,a.owner_token_file,repo,runid,scenario)
            verify=hashlib.sha256(f'NIR03-S1-VERIFIED\n{runid}\n{candidate_sha}\n'.encode()).hexdigest()
            intent={'schema':'nir03-s1-intent-v1','label':label,'repository':repo,'base_sha':base_sha,'candidate_sha':candidate_sha,'verification_id':verify,'expected_effects':['feature ref at candidate','one exact PR','exact status receipt'],'created_at':now()}
            atomic(out.parent/(label+'.intent.json'),intent)
            ledger_path=out.parent/(label+'.candidate-ledger.json')
            if policy=='candidate-reconciliation':
                atomic(ledger_path,{'schema':'nir03-s1-ledger-v1','run_id':runid,'candidate_sha':candidate_sha,'verification_id':verify,'expected_effects':{'ref':'unknown','pull_request':'unknown','status':'unknown'},'classification':'unknown','reason':'durable pre-dispatch intent; no authoritative recovery observations yet','updated_at':now()})
            row.update({'run_id':runid,'base_sha':base_sha,'candidate_sha':candidate_sha,'verification_id':verify,'intent_sha256':hashlib.sha256(json.dumps(intent,sort_keys=True).encode()).hexdigest()})
            if scenario not in ('R1',):
                row['mutation_trace'].append({'effect':'feature_ref','sha':competitor_sha if scenario=='R6' else candidate_sha,'time':now()})
            if scenario in ('R2','R3','R5','R7'):
                make_status(base,owner_token,repo,candidate_sha,verify)
                row['mutation_trace'].append({'effect':'status','time':now()})
            if scenario in ('R2','R3','R7'):
                make_pr(base,owner_token,repo,runid); row['mutation_trace'].append({'effect':'pull_request_seed','time':now()})
            if scenario=='R4':
                make_status(base,owner_token,repo,candidate_sha,verify)
                rules.append({'name':'R4-forward-drop-create','method':'POST','match':f'/repos/{OWNER}/{repo}/pulls','mode':'forward-drop','active':True,'once':True})
                try: api(proxy,owner_token,'POST',f'/repos/{OWNER}/{repo}/pulls',pr_body(runid),timeout=2)
                except Exception as e: row['mutation_trace'].append({'effect':'ambiguous_create','transport_error':type(e).__name__,'time':now()})
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
                ps,pb=api(proxy,owner_token,'POST',f'/repos/{OWNER}/{repo}/pulls',pr_body(runid))
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
            row['status']='blocked'; row['error']={'type':type(e).__name__,'message':str(e)[:500]}; row['ended_at']=now()
            try: row['observer_captures'].append(observe(proxy,a.observer_token_file,repo,candidate_sha,base_sha,captures,label+'-blocked-terminal'))
            except Exception as _e: row['protocol_deviations'].append('terminal observer failed: '+type(_e).__name__)
        row['proxy_events']=list(events); row['barriers'].extend(barriers)
    result={'schema':'nir03-s1-results-v1','protocol':'research/nir-03/supplementary/PREREGISTRATION.md','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'tool_versions':{'python':sys.version,'git':subprocess.check_output(['git','--version'],text=True).strip(),'forgejo':version_doc},'environment':{'provider_origin':base,'proxy_origin':proxy,'read_only_observer_account':'s1-observer','observer_credential_scope':'read:repository,read:user'},'assignments':assignments,'ended_at':now()}
    atomic(out,result); server.shutdown()

def atomic(path,obj):
    path=pathlib.Path(path); path.parent.mkdir(mode=0o700,parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp'); fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f: json.dump(obj,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)
def pr_body(marker):return {'head':f'{OWNER}:feature','base':'main','title':'NIR-03 S1 '+marker,'body':'Disposable preregistered synthetic publication '+marker}
def make_pr(base,tok,repo,marker): return api(base,tok,'POST',f'/repos/{OWNER}/{repo}/pulls',pr_body(marker))
def make_status(base,tok,repo,sha,verify): return api(base,tok,'POST',f'/repos/{OWNER}/{repo}/statuses/{sha}',{'state':'success','context':'nir03/s1/'+verify[:16],'description':'Synthetic S1 receipt '+verify})
def observe(url,tokfile,repo,sha,base_sha,capdir,label):
    cmd=[sys.executable,str(pathlib.Path(__file__).with_name('observer.py')),'--base-url',url,'--token-file',tokfile,'--repo',repo,'--candidate-sha',sha,'--base-sha',base_sha,'--capture-dir',str(capdir),'--label',label]
    # Separate interpreter/process; capture observer stdout only (capture path).
    r=subprocess.run(cmd,text=True,capture_output=True,timeout=45)
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
    exact_s=[x for x in statuses if x.get('sha')==candidate and x.get('state')=='success' and x.get('context')==ctx and verify in (x.get('description') or '')] if isinstance(statuses,list) else []
    ref=rr.get('branch_sha'); effects={'ref':'observed_candidate' if ref==candidate else ('observed_competing' if ref and ref!=candidate else ('observed_absent' if rr.get('branch_http')==404 else 'unknown')),'pull_request':'observed_exact' if len(exact)==1 else ('observed_absent' if ps==200 and not exact else 'unknown'),'status':'observed_exact' if exact_s else ('observed_absent' if ss==200 and not statuses else 'unknown')}
    if None in (rr.get('branch_http'),ps,ss) or rr.get('branch_http') not in (200,404) or ps!=200 or ss!=200: cls='unknown'
    elif effects['ref']=='observed_competing': cls='conflict'
    elif effects['ref']=='observed_absent' and not pulls and not statuses: cls='not_executed'
    elif effects['ref']=='observed_candidate' and len(exact)==1 and exact_s: cls='complete'
    else: cls='unknown'
    return {'classification':cls,'effects':effects,'ref_sha':ref,'pull_http':ps,'status_http':ss,'exact_pr_count':len(exact),'exact_status_count':len(exact_s),'recovery_reads':rr}
def run_interrupted_worker(stage,url,tokenfile,repo,candidate,runid,intent,row):
    cmd=[sys.executable,str(pathlib.Path(__file__).resolve()),'--worker-stage',stage,'--base-url',url,'--owner-token-file',tokenfile,'--worker-repo',repo,'--worker-candidate',candidate,'--worker-run',runid,'--worker-intent',str(intent)]
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    expected={'read':'after_first_remote_read','dispatch':'after_first_missing_effect_dispatch','classify':'before_final_durable_classification'}[stage]
    line=proc.stdout.readline().strip()
    stamp=now()
    if line!='BARRIER '+expected:
        proc.kill(); proc.wait(); row['protocol_deviations'].append(f'R5 worker failed to reach synchronization barrier {expected}: {line[:120]}'); return
    os.kill(proc.pid,signal.SIGKILL); proc.wait(timeout=5)
    row['barriers'].append({'barrier':expected,'pid':proc.pid,'worker_exit':proc.returncode,'time':stamp,'kill_confirmed':proc.returncode==-signal.SIGKILL})
def worker(a):
    tok=pathlib.Path(a.owner_token_file).read_text().strip(); q=urllib.parse.urlencode({'state':'all','head':'feature','base':'main'})
    if a.worker_stage=='read': api(a.base_url,tok,'GET',f'/repos/{OWNER}/{a.worker_repo}/branches/feature'); print('BARRIER after_first_remote_read',flush=True)
    elif a.worker_stage=='dispatch':
        st,raw=api(a.base_url,tok,'GET',f'/repos/{OWNER}/{a.worker_repo}/pulls?{q}')
        pulls=[]
        try:pulls=json.loads(raw)
        except:pass
        exact=[x for x in pulls if (x.get('head') or {}).get('ref')=='feature' and (x.get('head') or {}).get('sha')==a.worker_candidate and (x.get('base') or {}).get('ref')=='main'] if isinstance(pulls,list) else []
        if st==200 and not exact: api(a.base_url,tok,'POST',f'/repos/{OWNER}/{a.worker_repo}/pulls',pr_body(a.worker_run))
        print('BARRIER after_first_missing_effect_dispatch',flush=True)
    else:
        recovery_reads(a.base_url,tok,a.worker_repo,a.worker_candidate)
        print('BARRIER before_final_durable_classification',flush=True)
    time.sleep(60)
def make_fixture_and_push(base,token,tokenfile,repo,label,scenario):
    with tempfile.TemporaryDirectory(prefix='nir03-s1-fixture-') as td:
        root=pathlib.Path(td); ask=root/'askpass.sh'; ask.write_text('#!/bin/sh\ncase "$1" in *Username*) echo researcher;; *) cat "$NIR03_TOKEN_FILE";; esac\n'); ask.chmod(0o700)
        env=os.environ.copy(); env.update({'LC_ALL':'C','TZ':'UTC','GIT_ALLOW_PROTOCOL':'http','GIT_CONFIG_GLOBAL':os.devnull,'GIT_CONFIG_NOSYSTEM':'1','GIT_TERMINAL_PROMPT':'0','GIT_ASKPASS':str(ask),'NIR03_TOKEN_FILE':str(tokenfile),'GIT_AUTHOR_NAME':'NIR-03 S1','GIT_AUTHOR_EMAIL':'nir03-s1@example.invalid','GIT_COMMITTER_NAME':'NIR-03 S1','GIT_COMMITTER_EMAIL':'nir03-s1@example.invalid','GIT_AUTHOR_DATE':'2020-01-01T00:00:00 +0000','GIT_COMMITTER_DATE':'2020-01-01T00:00:00 +0000'})
        def git(*args):
            r=subprocess.run(['git',*args],cwd=root,env=env,text=True,capture_output=True)
            if r.returncode: raise RuntimeError('fixture git failed: '+r.stderr[-250:])
            return r.stdout.strip()
        git('init','--initial-branch=main'); git('config','core.autocrlf','false'); git('config','core.filemode','false')
        (root/'base.txt').write_text('NIR-03 S1 synthetic base fixture v1\n'); git('add','base.txt'); git('commit','-m','NIR-03 S1 base fixture'); base_sha=git('rev-parse','HEAD')
        (root/'candidate.txt').write_text('NIR-03 S1 candidate fixture: '+label+'\n'); git('add','candidate.txt'); git('commit','-m','NIR-03 S1 candidate '+label); candidate_sha=git('rev-parse','HEAD')
        competitor_sha=candidate_sha
        if scenario=='R6':
            (root/'competitor.txt').write_text('NIR-03 S1 competing writer fixture\n'); git('add','competitor.txt'); git('commit','-m','NIR-03 S1 competing writer '+label); competitor_sha=git('rev-parse','HEAD')
        # Credential is passed only to the git child process and never appears in output/logs.
        git('remote','add','origin',base+'/'+OWNER+'/'+repo+'.git')
        env['GIT_CONFIG_COUNT']='2'; env['GIT_CONFIG_KEY_0']='http.extraheader'; env['GIT_CONFIG_VALUE_0']='Authorization: token '+token
        git('push','origin','main:refs/heads/main')
        if scenario!='R1': git('push','origin',('HEAD' if scenario=='R6' else candidate_sha)+':refs/heads/feature')
        return base_sha,candidate_sha,competitor_sha
if __name__=='__main__': main()
