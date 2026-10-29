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
    try:
        targets=cdp_targets()
    except Exception as exc:
        return {"status":"HOLD","reason":"CDP_TARGET_INVENTORY_UNAVAILABLE","error_type":type(exc).__name__}
    if len(targets)!=1:
        return {"status":"HOLD","reason":"CDP_TARGET_COUNT_MISMATCH","cdp_matching_targets":len(targets)}
    target=targets[0]
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9223", timeout=12000)
        try:
            if not browser.contexts:
                return {"status":"HOLD","reason":"No existing browser context"}
            from urllib.parse import urlsplit
            all_pages=[page for context in browser.contexts for page in context.pages]
            pages=[page for page in all_pages if HOST_RE.match(page.url)]
            if len(pages)!=1:
                hosts=[]
                for tab in all_pages:
                    parts=urlsplit(tab.url)
                    host=(parts.hostname or parts.scheme or "unknown").lower()
                    if host not in hosts: hosts.append(host)
                return {"status":"HOLD","reason":"CDP_TARGET_MISMATCH","cdp_matching_targets":len(targets),"cdp_target_path":urlsplit(target.get("url","")).path,"playwright_matching_tabs":len(pages),"total_visible_tabs":len(all_pages),"visible_tab_hosts":hosts[:10],"browser_contexts":len(browser.contexts)}
            page=pages[0]
            title=await page.title()
            body=await page.locator("body").inner_text(timeout=8000)
            if "just a moment" in title.lower() or "verify you are human" in body.lower():
                return {"status":"BLOCKED","reason":"Challenge detected; no retry"}
            result=parse_reference(body)
            result["page_title"]=title[:120]
            result["observed_at_utc"]=datetime.now(timezone.utc).isoformat()
            result["method"]="existing-tab-read-only"
            return result
        finally:
            await browser.close()

if __name__=="__main__":
    print("G1_HANDOFF_RESULT",json.dumps(asyncio.run(inspect_open_tab()),sort_keys=True),flush=True)
