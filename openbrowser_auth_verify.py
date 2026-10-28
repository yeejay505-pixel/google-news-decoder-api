import os,json,time,urllib.request,urllib.error
base="http://127.0.0.1:8768/openbrowser/v1"
headers={"Authorization":"Bearer "+os.environ["OPENBROWSER_API_KEYS"].split(",")[0],"Content-Type":"application/json","User-Agent":"g1-auth-verify/1.0"}
def call(path,data=None):
 req=urllib.request.Request(base+path,headers=headers,data=None if data is None else json.dumps(data).encode(),method="GET" if data is None else "POST")
 try:
  with urllib.request.urlopen(req,timeout=40) as r:return json.load(r)
 except urllib.error.HTTPError as ex:
  print("G1_VERIFY_HTTP_ERROR",path,ex.code,ex.read(400).decode(errors="replace"),flush=True);raise
lease=None
try:
 print("G1_VERIFY_PROFILE_STATUS",json.dumps(call("/profiles/status"))[:850],flush=True)
 lease=call("/leases",{"owner":"g1-readonly-auth-verification","identity_id":"dxb-poc","ttl_seconds":180})
 lid=lease["lease_id"];print("G1_VERIFY_LEASE_OK",flush=True)
 nav=call("/browser/navigate",{"lease_id":lid,"url":"https://dxbinteract.com/"})
 print("G1_VERIFY_NAV",json.dumps({k:nav.get(k) for k in ("status","title","url")})[:550],flush=True)
 snap=call("/browser/snapshot",{"lease_id":lid})
 body=str(snap.get("bodyText","")).lower()
 blocked=any(x in (str(nav.get("title",""))+" "+body).lower() for x in ("just a moment","cloudflare","verify you are human","access denied"))
 print("G1_VERIFY_RESULT",json.dumps({"title":snap.get("title"),"url":snap.get("url"),"challenge":blocked,"profile":"dxb-poc","body_length":len(body)}),flush=True)
except Exception as ex:print("G1_VERIFY_ERROR",type(ex).__name__,str(ex)[:200],flush=True)
finally:
 if lease and lease.get("lease_id"):
  try:call("/leases/"+lease["lease_id"]+"/release",{})
  except Exception as ex:print("G1_VERIFY_RELEASE_ERROR",str(ex)[:100],flush=True)
print("G1_VERIFY_COMPLETE",flush=True)
