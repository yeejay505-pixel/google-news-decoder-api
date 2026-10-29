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
python /app/openbrowser_continuity_inspect.py
bash /app/ax_browser_broker/browser_pool/bin/launch_chrome.sh pool-a 9223
sleep 3
python /app/openbrowser_restored_tabs.py
python /app/openbrowser_auth_verify.py
wait "$pid"
