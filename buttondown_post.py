#!/usr/bin/env python3
"""Post one Main Street AI Brief issue to Buttondown. Called once per normal issue day by the daily publishing job (step 8).
Usage: python3 buttondown_post.py <issue-slug> [--dry-run]
Reads the API key from env BUTTONDOWN_API_KEY only; never prints/logs/writes it.
Mode switch: file site/buttondown_mode.txt = 'draft' (default, creates a DRAFT for the owner to review) or 'send' (queues to subscribers).
Exit codes: 0 done/skip-ok, 3 Sabbath skip, 4 already exists (idempotent stop), 5 abort (report to the owner), 6 not-eligible."""
import json, os, re, subprocess, sys, html, urllib.request, urllib.error
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bd_brand import brand
from datetime import datetime
from zoneinfo import ZoneInfo
SITE=os.environ.get("MSAIB_SITE") or os.path.dirname(os.path.abspath(__file__))  # the generator folder (holds public-prod/, sabbath_gate.py, config.json); defaults to this script's own folder
STATE=f"{SITE}/buttondown_state.json"; MODEF=f"{SITE}/buttondown_mode.txt"
API="https://api.buttondown.com/v1"; PROD="https://mainstreetaibrief.com/"
def die(code,msg): print(msg); sys.exit(code)
def call(method,path,payload=None):
    key=os.environ.get("BUTTONDOWN_API_KEY") or die(5,"ABORT: BUTTONDOWN_API_KEY not set")
    req=urllib.request.Request(API+path,data=None if payload is None else json.dumps(payload).encode(),method=method,
        headers={"Authorization":"Token "+key,"Content-Type":"application/json"})
    try:
        r=urllib.request.urlopen(req,timeout=60); return r.status,json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        t=e.read().decode()
        try: return e.code,json.loads(t)
        except Exception: return e.code,{"detail":t[:300]}
def main():
    a=[x for x in sys.argv[1:] if not x.startswith("--")]; dry="--dry-run" in sys.argv
    if len(a)!=1: die(5,"ABORT: usage: buttondown_post.py <issue-slug> [--dry-run]")
    slug=a[0]
    # 1. Sabbath gate
    g=subprocess.run(["python3",f"{SITE}/sabbath_gate.py"],capture_output=True,text=True)
    if g.returncode!=0: die(3,"SKIP (Sabbath): "+g.stdout.strip())
    # 2. mode switch
    mode=(open(MODEF).read().strip().lower() if os.path.exists(MODEF) else "draft")
    if mode not in ("draft","send"): die(5,f"ABORT: bad mode {mode!r} in {MODEF}")
    # 3. local idempotency state
    st=json.load(open(STATE)) if os.path.exists(STATE) else {}
    if slug in st: die(4,f"STOP (already posted, state file): {slug} -> {st[slug]}")
    # 4. take the issue from the production feed that step 7 published
    feed=open(f"{SITE}/public-prod/feed.xml").read()
    item=next((i for i in re.findall(r"<item>(.*?)</item>",feed,re.S) if f"/issues/{slug}.html</link>" in i),None)
    if not item: die(6,f"NOT ELIGIBLE: no feed item for {slug}")
    subject=html.unescape(re.search(r"<title>(.*?)</title>",item).group(1))
    body=html.unescape(re.search(r"<description>(.*?)</description>",item,re.S).group(1))
    pub=re.search(r"<pubDate>(.*?)</pubDate>",item).group(1)
    from email.utils import parsedate_to_datetime
    today=datetime.now(ZoneInfo("America/New_York")).date()
    if parsedate_to_datetime(pub).date()!=today: die(6,f"NOT ELIGIBLE: feed item date {pub!r} is not today ({today}); not sending an old issue")
    # 5. template-syntax guard (Buttondown renders Django templates; address lives in the newsletter footer setting, not the body)
    bad=[t for t in ("{{","{%","{#") if t in body or t in subject]
    if bad: die(5,f"ABORT: body/subject contains template token(s) {bad}; not posting")
    # 6. live check
    url=f"{PROD}issues/{slug}.html"
    code=subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}","-L","--max-time","30",url],capture_output=True,text=True).stdout
    if code!="200": die(5,f"ABORT: live check {url} returned {code}")
    # 7. remote idempotency: any existing email with this slug or subject (any status except deleted) => stop
    nxt="/emails"; seen=[]
    while nxt:
        c,d=call("GET",nxt)
        if c!=200: die(5,f"ABORT: list emails failed {c} {str(d)[:200]}")
        seen+=d["results"]; nxt=d["next"].replace(API,"") if d.get("next") else None
    for e in seen:
        if e["status"]!="deleted" and (e["slug"]==slug or e["subject"].strip()==subject.strip()):
            if not dry: st[slug]=e["id"]; json.dump(st,open(STATE,"w"),indent=1)
            die(4,f"STOP (already in Buttondown): {e['id']} status={e['status']}")
    # 8. send-mode preconditions: a mailing address must be in the newsletter footer, and the account must show a verified sending domain
    c,n=call("GET","/newsletters"); nl=n["results"][0] if c==200 and n.get("results") else {}
    if mode=="send":
        if not nl.get("footer","").strip(): die(5,"ABORT: send mode but newsletter footer (mailing address) is empty")
        if nl.get("sending_domain_status")!="valid": die(5,"ABORT: sending domain not valid")
    if dry: die(0,f"DRY RUN OK: mode={mode} subject={subject!r} body_len={len(body)} would POST status=draft (then PATCH about_to_send only if mode=send)")
    # 9. create DRAFT first (never sends), verify, then (send mode only) queue
    c,e=call("POST","/emails",{"subject":subject,"slug":slug,"body":"<!-- buttondown-editor-mode: fancy -->"+brand(body),
        "status":"draft","canonical_url":url,"archival_mode":"disabled"})
    if c!=201: die(5,f"ABORT: create failed {c} {str(e)[:300]}")
    st[slug]={"id":e["id"],"mode":mode,"status":"draft"}; json.dump(st,open(STATE,"w"),indent=1)
    if mode=="send":
        c2,e2=call("PATCH","/emails/"+e["id"],{"status":"about_to_send"})
        if c2!=200: die(5,f"ABORT: draft {e['id']} created but queue failed {c2} {str(e2)[:300]}")
        st[slug]["status"]=e2["status"]; json.dump(st,open(STATE,"w"),indent=1)
    print(f"OK mode={mode} id={e['id']} status={st[slug]['status']}")
main()
