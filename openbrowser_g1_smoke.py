import json, os, time, urllib.request, urllib.error
BASE="http://127.0.0.1:8767/openbrowser/v1"
KEY=os.environ.get("OPENBROWSER_API_KEYS","").split(",")[0]
HEAD={"Authorization":"Bearer "+KEY,"Content-Type":"application/json","User-Agent":"openbrowser-g1-poc/1.0"}
def call(path,data=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=HEAD,method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
for n in range(40):
    try:
        r=call("/health")
        print("G1_BROKER_HEALTH",json.dumps(r)[:180],flush=True)
        break
    except Exception:
        time.sleep(2)
else:
    print("G1_BROKER_UNREACHABLE",flush=True);raise SystemExit(2)
for url in ["https://example.com","https://www.dxbinteract.com/dubai-property-prices"]:
    lease=None
    try:
        lease=call("/leases",{"owner":"g1-readonly-poc","ttl_seconds":120})
        lid=lease.get("lease_id")
        if not lid:raise RuntimeError("NO_LEASE_ID")
        try: nav=call("/browser/navigate",{"lease_id":lid,"url":url})
        except urllib.error.HTTPError as err:
            print("G1_NAV_ERROR",url,err.code,str(err.read(300))[:200],flush=True);continue
        snap=call("/browser/snapshot",{"lease_id":lid})
        clean=json.dumps(snap)
        challenge=any(x in clean.lower() for x in ["just a moment","cloudflare","verify you are human","access denied"])
        print("G1_RESULT",json.dumps({"url":url,"navigate_ok":True,"challenge_detected":challenge,"snapshot_bytes":len(clean),"title_hint":clean[:160]}),flush=True)
    except Exception as exc:
        print("G1_ERROR",url,type(exc).__name__,str(exc)[:180],flush=True)
    finally:
        if lease and lease.get("lease_id"):
            try:call("/leases/"+lease["lease_id"]+"/release",{})
            except Exception as ex:print("G1_RELEASE_ERROR",type(ex).__name__,flush=True)
print("G1_TEST_COMPLETE",flush=True)
