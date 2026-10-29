"""Conservative G1 history parser. No browser access, no side effects."""
import re, hashlib, json
from datetime import datetime

DATE = r"(?:\d{1,2}[,\s/-]+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[,\s/-]+\d{4}"
DATE_RE = re.compile(DATE, re.I)
MONEY_RE = re.compile(r"(?:AED\s*)(\d{1,3}(?:,\d{3})+(?:\.\d+)?)", re.I)
SALE_RE = re.compile(r"\b(?:SOLD|RESALE|PRIMARY(?:\s+SALE)?)\b", re.I)
RENT_RE = re.compile(r"\b(?:RENTED|RENTAL|NEW CONTRACT|RENEWAL|RENT CONTRACT)\b", re.I)

def normalized_date(value):
    s=re.sub(r"[,/-]", " ", value)
    s=" ".join(s.split())
    for fmt in ("%d %b %Y","%d %B %Y","%b %Y","%B %Y"):
        try: return datetime.strptime(s,fmt).strftime("%Y-%m-%d" if s[0].isdigit() else "%Y-%m")
        except ValueError: pass
    return None

def parse_events(text):
    # Parse small, independently labelled transaction cards; never bind an amount
    # to a distant date or to the property's summary/yield.
    lines=[re.sub(r"\s+"," ",x).strip() for x in text.splitlines()]
    lines=[x for x in lines if x]
    cards=[]
    for i,line in enumerate(lines):
        kind = "sale" if SALE_RE.search(line) else ("rent" if RENT_RE.search(line) else None)
        if not kind: continue
        # Card starts at event marker, stop before next event marker.
        tail=[]
        for chunk in lines[i:i+9]:
            if tail and (SALE_RE.search(chunk) or RENT_RE.search(chunk)): break
            tail.append(chunk)
        excerpt=" ".join(tail)
        amounts=MONEY_RE.findall(excerpt)
        dates=DATE_RE.findall(excerpt)
        # Reject multiple conflicting figures or missing date.
        if len(amounts)!=1 or not dates: continue
        amount=int(float(amounts[0].replace(",","")))
        dates_normalized=[normalized_date(v) for v in dates]
        if not all(dates_normalized): continue
        if kind=="sale" and len(dates_normalized)!=1: continue
        if kind=="rent" and len(dates_normalized)>2: continue
        event={"type":kind,"amount_aed":amount,
               "date":dates_normalized[0] if kind=="sale" else None,
               "lease_start":dates_normalized[0] if kind=="rent" and len(dates_normalized)==2 else None,
               "lease_end":dates_normalized[1] if kind=="rent" and len(dates_normalized)==2 else None,
               "date_precision":"month" if len(dates[0].split())==2 else "day",
               "classification":("resale" if re.search(r"\bresale\b",excerpt,re.I) else "primary" if re.search(r"\bprimary\b",excerpt,re.I) else "unspecified") if kind=="sale" else ("renewal" if re.search(r"\brenewal\b",excerpt,re.I) else "new" if re.search(r"\bnew\b",excerpt,re.I) else "unspecified")}
        if kind=="rent" and len(dates_normalized)==1:
            # A single month is insufficient to establish a lease period.
            continue
        cards.append(event)
    dedup={json.dumps(e,sort_keys=True):e for e in cards}
    return list(dedup.values())

def certify(text, building, unit, source_path, observed):
    flat=" ".join(text.split()).casefold()
    if building.casefold() not in flat or not re.search(r"(?<!\d)"+re.escape(unit)+r"(?!\d)",flat):
        return {"status":"HOLD","reason":"EXACT_UNIT_IDENTITY_NOT_PROVEN","events":[]}
    if "property history" not in flat: return {"status":"HOLD","reason":"HISTORY_SECTION_NOT_VISIBLE","events":[]}
    events=parse_events(text)
    if not any(e["type"]=="sale" for e in events) or not any(e["type"]=="rent" for e in events):
        return {"status":"HOLD","reason":"SALE_AND_RENT_EVENTS_NOT_BOTH_VERIFIED","events":events}
    key=hashlib.sha256((building+"|"+unit+"|"+source_path+"|"+json.dumps(events,sort_keys=True)).encode()).hexdigest()
    return {"status":"VERIFIED","building":building,"unit":unit,"source":"DXBinteract Property History","source_path":source_path,
            "observed_at_utc":observed,"freshness":"observed_at_only_not_completeness_guarantee",
            "events":events,"evidence_key":key}
