"""G1 bounded read-only extraction from the already-open DXBinteract browser tab.
No navigation, clicks, API interception, cookies, or database writes.
"""
import asyncio
import json
import re
from datetime import datetime, timezone
from playwright.async_api import async_playwright
from urllib.request import urlopen
from urllib.parse import urlsplit
from g1_history_events import certify, transaction_boundary_diagnostic

HOST_RE = re.compile(r"^https://(?:www\.)?dxbinteract\.com(?:/|$)", re.I)
PRICE_RE = re.compile(r"(?:AED\s*)?([0-9][0-9,]{3,})\s*(?:AED)?", re.I)

def parse_reference(text, building="Lamtara 1", unit="401"):
    text = re.sub(r"\s+", " ", text or "")
    # Diagnostic evidence: do not infer a unit from prices alone.
    normalized = text.lower()
    identity = building.lower() in normalized and bool(re.search(r"(?<!\d)"+re.escape(unit)+r"(?!\d)", text))
    if not identity:
        return {"status":"HOLD","reason":"Exact building and unit not both present in currently visible page","building":building,"unit":unit}
    beds = bool(re.search(r"2\s*(?:beds?|bedrooms?)", text, re.I))
    size = bool(re.search(r"1[,]?356(?:\.0+)?\s*(?:sq\.?\s*ft|sqft)", text, re.I))
    sale = bool(re.search(r"(?:3,600,000|3600000)", text))
    rent = bool(re.search(r"(?:190,000|190000)", text))
    return {"status":"EVIDENCE_PRESENT" if all((beds,size,sale,rent)) else "INCOMPLETE",
            "building":building,"unit":unit,"reference_checks":{"two_bedrooms":beds,"size_1356_sqft":size,"sale_3600000":sale,"rent_190000":rent},
            "note":"Reference-value presence only; dates/event attribution still require review"}

def cdp_targets():
    # Local Chrome discovery only. Do not expose debugger WebSocket addresses.
    with urlopen('http://127.0.0.1:9223/json/list', timeout=5) as response:
        data=json.load(response)
    return [item for item in data if item.get('type')=='page' and HOST_RE.match(item.get('url',''))]

async def inspect_open_tab():
    """Attach directly to the existing page target; no navigation or network calls to site."""
    import websockets
    try:
        targets = cdp_targets()
    except Exception as exc:
        return {"status": "HOLD", "reason": "CDP_TARGET_INVENTORY_UNAVAILABLE", "error_type": type(exc).__name__}
    if len(targets) != 1:
        return {"status": "HOLD", "reason": "CDP_TARGET_COUNT_MISMATCH", "cdp_matching_targets": len(targets)}
    target = targets[0]
    original_url = target.get("url", "")
    target_id = target.get("id", "")
    debugger_url = target.get("webSocketDebuggerUrl", "")
    if not debugger_url.startswith("ws://127.0.0.1:9223/devtools/page/") or not target_id or not debugger_url.endswith("/" + target_id):
        return {"status": "HOLD", "reason": "INVALID_LOCAL_TARGET"}
    try:
        async with websockets.connect(debugger_url, open_timeout=8, close_timeout=3, max_size=2_000_000) as ws:
            async def evaluate(expression, request_id):
                await ws.send(json.dumps({"id": request_id, "method": "Runtime.evaluate",
                    "params": {"expression": expression, "returnByValue": True, "awaitPromise": False}}))
                while True:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
                    if msg.get("id") == request_id:
                        if "error" in msg or "exceptionDetails" in msg.get("result", {}):
                            raise ValueError("CDP_RUNTIME_EVALUATION_FAILED")
                        return msg.get("result", {}).get("result", {}).get("value")
            # Do not read content until target location has been reverified.
            live_url = await evaluate("location.href", 101)
            if live_url != original_url or not HOST_RE.match(live_url or ""):
                return {"status": "HOLD", "reason": "TARGET_CHANGED"}
            title = await evaluate("document.title", 102)
            # Text only, bounded. No HTML, cookies, network interception or session data.
            body = await evaluate("(document.body && document.body.innerText || '').slice(0,150000)", 103)
            if not isinstance(body, str) or not isinstance(title, str):
                return {"status": "HOLD", "reason": "NO_READABLE_PAGE"}
            if "just a moment" in title.lower() or "verify you are human" in body.lower():
                return {"status": "BLOCKED", "reason": "Challenge detected; no retry"}
            result = parse_reference(body)
            if result["status"] == "HOLD":
                return {**result, "target_path": urlsplit(original_url).path, "method": "direct-target-cdp"}
            # Race check after reading.
            if await evaluate("location.href", 104) != original_url:
                return {"status": "HOLD", "reason": "TARGET_CHANGED_DURING_READ"}
            evidence=certify(body, "Lamtara 1", "401", urlsplit(original_url).path, datetime.now(timezone.utc).isoformat())
            result["event_certification"]=evidence
            if evidence.get("status")=="HOLD":
                result["boundary_diagnostic"]=transaction_boundary_diagnostic(body)
            if evidence.get("status")=="HOLD":
                # Minimal, allowlisted diagnostic from history section only.
                # Never return owner names, addresses, phone numbers, or arbitrary DOM.
                # Search all visible lines rather than relying on a heading's last occurrence.
                # Only report strictly allowlisted tokens, never raw page or personal data.
                import re as _re
                candidates=body.splitlines()
                token_re=_re.compile(r"\b(?:AED|SOLD|RENTED|RENTAL|RENT|NEW|CONTRACT|RENEWAL|PRIMARY|RESALE|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JAN|FEB|MAR|APR|JUN|JUL|AUG|SEP|SEPT|OCT|NOV|DEC)\b|\d[\d,. /-]*",_re.I)
                keyword_re=_re.compile(r"\b(?:AED|SOLD|RENTED|RENTAL|RENT|NEW CONTRACT|RENEWAL|PRIMARY|RESALE)\b",_re.I)
                # Context window around transaction markers, redacted to allowlisted
                # labels, dates and currency only; never emit owner/agent text.
                event_marker=_re.compile(r"\b(?:SOLD|RENTED)\b",_re.I)
                amount_re=_re.compile(r"\bAED\s*\d[\d,]*(?:\.\d+)?\b",_re.I)
                date_re=_re.compile(r"\b(?:\d{1,2}\s*[,/-]?\s*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*[-/,]?\s*\d{4}\b",_re.I)
                keep_label=_re.compile(r"\b(?:SOLD|RENTED|Resale|Primary|New contract|Renewal)\b",_re.I)
                windows=[]
                for i,line in enumerate(candidates):
                    if not event_marker.search(line): continue
                    snippets=[]
                    for candidate in candidates[i:min(len(candidates),i+13)]:
                        if len(snippets)>0 and event_marker.search(candidate): break
                        tokens=amount_re.findall(candidate)+date_re.findall(candidate)+keep_label.findall(candidate)
                        if tokens: snippets.append(" | ".join(tokens)[:120])
                    windows.append({"marker":line.strip().upper(),"tokens":snippets[:9]})
                result["event_diagnostic"]={"card_windows":windows[:8],"visible_lines":len(candidates),"card_markers":len(windows)}


            result.update({"page_title": title[:120], "target_path": urlsplit(original_url).path,
                           "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                           "method": "direct-target-cdp", "stored": False})
            return result
    except Exception as exc:
        return {"status": "HOLD", "reason": "CDP_DIRECT_ATTACH_ERROR", "error_type": type(exc).__name__}

if __name__ == "__main__":
    print("G1_HANDOFF_RESULT", json.dumps(asyncio.run(inspect_open_tab()), sort_keys=True), flush=True)
