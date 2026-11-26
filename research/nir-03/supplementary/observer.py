#!/usr/bin/env python3
"""Independent read-only Forgejo observer for NIR-03 S1.

Each invocation makes direct API GETs through the configured observer URL and
stores exact raw response bodies in a private capture directory. Credentials
are read from a separate file and are never serialized.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, pathlib, sys, urllib.error, urllib.parse, urllib.request

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-url', required=True); p.add_argument('--token-file', required=True)
    p.add_argument('--owner', default='researcher'); p.add_argument('--repo', required=True)
    p.add_argument('--branch', default='feature'); p.add_argument('--candidate-sha', required=True)
    p.add_argument('--base-sha', required=True); p.add_argument('--capture-dir', required=True)
    p.add_argument('--label', required=True); a=p.parse_args()
    root=pathlib.Path(a.capture_dir); root.mkdir(mode=0o700,parents=True,exist_ok=True)
    os.chmod(root,0o700)
    token=pathlib.Path(a.token_file).read_text().strip()
    q=urllib.parse.urlencode({'state':'all','head':a.branch,'base':'main'})
    specs=[('branch',f'/repos/{a.owner}/{a.repo}/branches/{a.branch}'),
           ('pulls',f'/repos/{a.owner}/{a.repo}/pulls?{q}'),
           ('candidate_status',f'/repos/{a.owner}/{a.repo}/statuses/{a.candidate_sha}'),
           ('base_status',f'/repos/{a.owner}/{a.repo}/statuses/{a.base_sha}')]
    capture={'schema':'nir03-s1-observer-v1','label':a.label,'observer_process_pid':os.getpid(),'started_at':utc(),'endpoint_origin':a.base_url.rstrip('/'),'observations':[]}
    for name,path in specs:
        endpoint=a.base_url.rstrip('/')+'/api/v1'+path
        entry={'name':name,'method':'GET','endpoint':endpoint,'requested_sha':path.rsplit('/',1)[-1] if name.endswith('status') else None,'started_at':utc()}
        req=urllib.request.Request(endpoint,headers={'Authorization':'token '+token,'Accept':'application/json'},method='GET')
        try:
            with urllib.request.urlopen(req,timeout=8) as response:
                raw=response.read(); entry['http_status']=response.status
                entry['response_headers']={k:v for k,v in response.headers.items() if k.lower() not in {'set-cookie','authorization','www-authenticate'}}
        except urllib.error.HTTPError as e:
            raw=e.read(); entry['http_status']=e.code
            entry['response_headers']={k:v for k,v in e.headers.items() if k.lower() not in {'set-cookie','authorization','www-authenticate'}}
        except Exception as e:
            raw=b''; entry['http_status']=None; entry['transport_error']={'type':type(e).__name__,'message':str(e)[:400]}
        entry['ended_at']=utc(); entry['raw_body_sha256']=hashlib.sha256(raw).hexdigest()
        raw_path=root/(a.label+'-'+name+'-'+str(len(capture['observations']))+'.body')
        fd=os.open(raw_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f: f.write(raw)
        entry['raw_body_file']=str(raw_path)
        try:
            data=json.loads(raw) if raw else None
            entry['returned_identity_fields']=identity(name,data)
            entry['body_json']=data
        except Exception:
            entry['returned_identity_fields']=None
        capture['observations'].append(entry)
    capture['ended_at']=utc()
    out=root/(a.label+'-'+str(os.getpid())+'.json')
    fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf8') as f: json.dump(capture,f,indent=2,sort_keys=True); f.write('\n')
    print(str(out))

def identity(name,d):
    if name=='branch' and isinstance(d,dict): return {'ref':d.get('name'),'sha':(d.get('commit') or {}).get('id')}
    if name=='pulls' and isinstance(d,list): return [{'number':x.get('number'),'state':x.get('state'),'head_ref':(x.get('head') or {}).get('ref'),'head_sha':(x.get('head') or {}).get('sha'),'base_ref':(x.get('base') or {}).get('ref'),'merged':x.get('merged')} for x in d]
    if name.endswith('status') and isinstance(d,list): return [{'context':x.get('context'),'state':x.get('status',x.get('state')),'description':x.get('description')} for x in d]
    return d
if __name__=='__main__': main()
