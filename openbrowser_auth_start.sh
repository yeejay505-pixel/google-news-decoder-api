#!/bin/sh
set -eu
mkdir -p /data/openbrowser-broker/config /data/openbrowser-pool
printf '%s\n' '{"identities":{"dxb-poc":{"label":"DXBinteract controlled POC","site":"dxbinteract.com","slot":"pool-a","profile_dir":"/data/openbrowser-pool/profiles/dxb-poc","lang":"en-US","policy":{"max_parallel_sessions":1,"requires_human_auth":true}}}}' > /data/openbrowser-broker/config/identities.local.json
nginx
OPENBROWSER_BROKER_PORT=8768 openbrowser-broker
