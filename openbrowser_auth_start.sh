#!/bin/sh
set -eu
: "${OPENBROWSER_UI_USER:?Missing UI username}"
: "${OPENBROWSER_UI_PASSWORD:?Missing UI password}"
: "${OPENBROWSER_API_KEYS:?Missing broker API key}"
mkdir -p /run /data/openbrowser-broker/config /data/openbrowser-pool
umask 077
printf '%s:%s\n' "$OPENBROWSER_UI_USER" "$(printf '%s' "$OPENBROWSER_UI_PASSWORD" | openssl passwd -apr1 -stdin)" > /run/openbrowser-ui.htpasswd
chgrp www-data /run/openbrowser-ui.htpasswd
chmod 640 /run/openbrowser-ui.htpasswd
printf '%s\n' '{"identities":{"dxb-poc":{"label":"DXBinteract human handoff","site":"dxbinteract.com","slot":"pool-a","profile_dir":"/data/openbrowser-pool/profiles/dxb-poc","lang":"en-US","policy":{"max_parallel_sessions":1,"requires_human_auth":true}}}}' > /data/openbrowser-broker/config/identities.local.json
profile=/data/openbrowser-pool/profiles/dxb-poc
if [ -d "$profile" ]; then
 rm -f "$profile/SingletonLock" "$profile/SingletonSocket" "$profile/SingletonCookie"
fi
# Hard stop after one hour: no session may continue beyond this window.
(sleep 3600; echo "G1_SESSION_TIME_LIMIT"; kill -TERM 1) &
nginx
OPENBROWSER_BROKER_PORT=8768 openbrowser-broker &
broker_pid=$!
CHROME_HEADLESS=0 bash /app/g1_webgl_launcher.sh pool-a 9223
display_file=/data/openbrowser-pool/state/pool-a.display
i=0
while [ ! -s "$display_file" ] && [ "$i" -lt 20 ]; do sleep 1; i=$((i+1)); done
[ -s "$display_file" ] || { echo "G1_NO_DISPLAY"; exit 1; }
display="$(cat "$display_file")"
x11vnc -display "$display" -rfbport 5900 -listen 127.0.0.1 -forever -shared -nopw -quiet &
websockify --web /usr/share/novnc 127.0.0.1:6081 127.0.0.1:5900 &
python /app/g1_webgl_local_check.py
python /app/openbrowser_continuity_inspect.py
python /app/openbrowser_auth_verify.py
python -m unittest -q test_g1_unit_history_adapter test_g1_history_events test_g1_evidence_store
python /app/g1_volume_smoke.py
python /app/g1_inspect_http.py &
echo "G1_LIVE_BROWSER_READY"
wait "$broker_pid"
