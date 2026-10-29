"""G1 offline lease-to-profile audit. No website navigation or snapshot requests."""
import json
import os
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path("/data/openbrowser-pool")
IDENTITIES = Path("/data/openbrowser-broker/config/identities.local.json")
IDENTITY = "dxb-poc"
SLOT = "pool-a"
EXPECTED_PROFILE = ROOT / "profiles" / "dxb-poc"
BASE = "http://127.0.0.1:8768/openbrowser/v1"

def report(name, value):
    print("G1_BINDING_" + name, json.dumps(value, sort_keys=True), flush=True)

def local_config():
    config = json.loads(IDENTITIES.read_text())
    identity = config.get("identities", {}).get(IDENTITY, {})
    values = {}
    slot_file = ROOT / "config" / (SLOT + ".env")
    for line in slot_file.read_text().splitlines() if slot_file.exists() else []:
        if line.startswith(("PROFILE_DIR=", "IDENTITY_ID=", "CHROME_LANG=")):
            k, v = line.split("=", 1)
            values[k] = v.strip().strip("'\"")
    report("CONFIG", {
        "identity_registered": bool(identity),
        "identity_slot_matches": identity.get("slot") == SLOT,
        "identity_profile_matches": identity.get("profile_dir") == str(EXPECTED_PROFILE),
        "slot_config_exists": slot_file.exists(),
        "slot_identity_matches": values.get("IDENTITY_ID") == IDENTITY,
        "slot_profile_matches": values.get("PROFILE_DIR") == str(EXPECTED_PROFILE),
        "profile_exists": EXPECTED_PROFILE.is_dir(),
    })

def browser_processes():
    results = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            raw = (proc / "cmdline").read_bytes().replace(b"\x00", b" ").decode(errors="replace")
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            continue
        if "--remote-debugging-port=9223" not in raw or "--user-data-dir=" not in raw:
            continue
        args = raw.split()
        user_dirs = [v.split("=", 1)[1] for v in args if v.startswith("--user-data-dir=")]
        results.append({
            "pid": int(proc.name),
            "profile_matches": bool(user_dirs) and user_dirs[0] == str(EXPECTED_PROFILE),
            "debug_port_matches": "--remote-debugging-port=9223" in args,
            "headless": "--headless" in args,
        })
    report("CHROME", {"count": len(results), "processes": results})

def request(path, payload=None):
    token = os.environ.get("OPENBROWSER_API_KEYS", "").split(",")[0]
    if not token:
        raise RuntimeError("OpenBrowser API key not configured")
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=body, headers=headers,
                                 method="POST" if body is not None else "GET")
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)

def audit_lease():
    lease = None
    try:
        lease = request("/leases", {"owner": "g1-offline-profile-binding", "identity_id": IDENTITY, "ttl_seconds": 90})
        # Explicit allowlist: do not log lease tokens, URLs, cookies or serialized response.
        safe = {}
        for key in ("identity_id", "slot", "slot_id", "browser_slot", "profile_dir", "profile_path"):
            if isinstance(lease.get(key), (str, int)):
                safe[key] = lease[key]
        report("LEASE", {
            "accepted": bool(lease.get("lease_id")),
            "reported_fields": safe,
            "identity_matches": safe.get("identity_id") == IDENTITY if "identity_id" in safe else None,
            "slot_matches": any(safe.get(k) == SLOT for k in ("slot", "slot_id", "browser_slot")) if any(k in safe for k in ("slot", "slot_id", "browser_slot")) else None,
            "profile_matches": any(safe.get(k) == str(EXPECTED_PROFILE) for k in ("profile_dir", "profile_path")) if any(k in safe for k in ("profile_dir", "profile_path")) else None,
        })
    except (urllib.error.URLError, ValueError, KeyError, RuntimeError) as exc:
        report("LEASE_ERROR", {"type": type(exc).__name__})
    finally:
        if lease and lease.get("lease_id"):
            try:
                request("/leases/" + lease["lease_id"] + "/release", {})
                report("LEASE_RELEASED", True)
            except (urllib.error.URLError, ValueError, RuntimeError):
                report("LEASE_RELEASED", False)

if __name__ == "__main__":
    try:
        local_config()
        browser_processes()
        audit_lease()
        report("NO_EXTERNAL_NAVIGATION", True)
    except (OSError, ValueError, KeyError) as exc:
        report("AUDIT_ERROR", {"type": type(exc).__name__})
