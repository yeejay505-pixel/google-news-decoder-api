#!/bin/sh
set -eu
mkdir -p /data/openbrowser-broker/config /data/openbrowser-pool
printf '%s\n' '{"identities":{"dxb-poc":{"label":"DXBinteract controlled POC","site":"dxbinteract.com","slot":"pool-a","profile_dir":"/data/openbrowser-pool/profiles/dxb-poc","lang":"en-US","policy":{"max_parallel_sessions":1,"requires_human_auth":true}}}}' > /data/openbrowser-broker/config/identities.local.json
# Clear stale Chromium singleton markers from the previous container only.
# This runs before any browser is started in the new container.
profile=/data/openbrowser-pool/profiles/dxb-poc
if [ -d "$profile" ]; then
  rm -f "$profile/SingletonLock" "$profile/SingletonSocket" "$profile/SingletonCookie"
  echo "G1_CHROMIUM_STALE_PROFILE_LOCKS_CLEARED"
fi
nginx
OPENBROWSER_BROKER_PORT=8768 openbrowser-broker &
pid=$!
python - <<'PY'
import os, json, time, urllib.request
base="http://127.0.0.1:8768/openbrowser/v1"
key=os.environ["OPENBROWSER_API_KEYS"].split(",")[0]
headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","User-Agent":"g1-auth-poc/1.0"}
for i in range(30):
 try:
  with urllib.request.urlopen(urllib.request.Request(base+"/health",headers=headers),timeout=4) as r:
   if r.status==200:break
 except Exception:time.sleep(2)
else:
 print("G1_AUTH_BROKER_NOT_READY",flush=True);raise SystemExit(1)
print("G1_AUTH_BROKER_READY",flush=True)
payload={"owner":"g1-human-login","identity_id":"dxb-poc","url":"https://dxbinteract.com/","reason":"authorized_account_login","mode":"vnc"}
try:
 req=urllib.request.Request(base+"/auth/request",headers=headers,data=json.dumps(payload).encode(),method="POST")
 with urllib.request.urlopen(req,timeout=30) as r: data=json.load(r)
 print("G1_LOGIN_PORTAL_URL",data.get("portal_url","not_returned"),flush=True)
 print("G1_LOGIN_EXPIRES_AT",data.get("expires_at","unknown"),flush=True)
except Exception as e:print("G1_LOGIN_PORTAL_CREATE_FAILED",type(e).__name__,str(e)[:300],flush=True)
PY
# Perform a single non-extracting check against the persistent browser identity.
bash /app/ax_browser_broker/browser_pool/bin/launch_chrome.sh pool-a 9223 || true
python /app/openbrowser_auth_verify.py || true
wait "$pid"
