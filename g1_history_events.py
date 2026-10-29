"""Fail-closed exact-unit DXBinteract history parser, isolated G1 only."""
import re, json, hashlib
from datetime import datetime

MONTH=r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_RE=re.compile(rf"(?:(?<!\d)\d{{1,2}}\s*[,/-]?\s*)?{MONTH}\s*[,/-]?\s*\d{{4}}",re.I)
AMOUNT_RE=re.compile(r"(?<!\d)\d{1,3}(?:,\d{3})+(?!\d)")
MARKER_RE=re.compile(r"^\s*(?:[●•◉☑✓]\s*)?(SOLD|RENTED)\b(?!\s+BY\b)",re.I)
LABEL_RE=re.compile(r"\b(?:resale|primary|new contract|renewal)\b",re.I)

def date_normalize(raw):
    value=re.sub(r"[,/-]"," ",raw)
    value=" ".join(value.split())
    for fmt in ("%d %b %Y","%d %B %Y","%b %Y","%B %Y"):
        try:
            d=datetime.strptime(value,fmt)
            return (d.strftime("%Y-%m-%d"),"day") if value[0].isdigit() else (d.strftime("%Y-%m"),"month")
        except ValueError: pass
    return None

def parse_events(text):
    lines=[re.sub(r"\s+"," ",line).strip() for line in text.splitlines()]
    lines=[line for line in lines if line]
    # Only inspect history, not summary prices or market comparison widgets.
    heads=[i for i,line in enumerate(lines) if line.casefold()=="property history"]
    if not heads: return []
    start=heads[-1]+1
    history=lines[start:]
    first=next((i for i,line in enumerate(history) if MARKER_RE.match(line)),None)
    if first is None: return []
    history=history[first:]
    indices=[i for i,line in enumerate(history) if MARKER_RE.match(line)]
    events=[]
    for pos,index in enumerate(indices):
        end=indices[pos+1] if pos+1<len(indices) else min(index+16,len(history))
        card=history[index:end]
        if len(card)>16: card=card[:16]
        kind="sale" if MARKER_RE.match(card[0]).group(1).upper()=="SOLD" else "rent"
        # A currency label may occupy one line and its amount the next.
        amounts=[]
        for j,line in enumerate(card):
            if "AED" in line.upper():
                found=AMOUNT_RE.findall(line)
                if not found and j+1<len(card): found=AMOUNT_RE.findall(card[j+1])
                amounts+=found
        amounts=list(dict.fromkeys(amounts))
        dates=[date_normalize(x.group(0)) for line in card for x in DATE_RE.finditer(line)]
        if len(amounts)!=1 or any(d is None for d in dates): continue
        # Periods contain exactly two month dates; sales contain a single exact date.
        if kind=="sale" and (len(dates)!=1 or dates[0][1]!="day"):continue
        if kind=="rent" and (len(dates)!=2 or any(d[1]!="month" for d in dates)):continue
        labels=[v.group(0).casefold() for line in card for v in LABEL_RE.finditer(line)]
        event={"type":kind,"amount_aed":int(amounts[0].replace(",",""))}
        if kind=="sale":
            event.update({"date":dates[0][0],"classification":"resale" if "resale" in labels else "primary" if "primary" in labels else "unspecified"})
        else:
            if dates[0][0]>=dates[1][0]:continue
            event.update({"lease_start":dates[0][0],"lease_end":dates[1][0],"classification":"new" if "new contract" in labels else "renewal" if "renewal" in labels else "unspecified"})
        if event not in events:events.append(event)
    return events

def certify(text,building,unit,source_path,observed):
    normalized=" ".join(text.split()).casefold()
    # A number mentioned anywhere in the page is insufficient for legal attribution:
    # page header identity AND known exact-unit test target required.
    if building.casefold() not in normalized or not re.search(r"(?<!\d)"+re.escape(unit)+r"(?!\d)",normalized):
        return {"status":"HOLD","reason":"EXACT_UNIT_IDENTITY_NOT_PROVEN","events":[]}
    if "property history" not in normalized:
        return {"status":"HOLD","reason":"HISTORY_SECTION_NOT_VISIBLE","events":[]}
    events=parse_events(text)
    # Do not silently discard additional rentals. Flag overlapping intervals
    # for human source-card review before any evidence is persisted.
    rentals=sorted((e for e in events if e["type"]=="rent"),key=lambda e:e["lease_start"])
    overlaps=[]
    for left,right in zip(rentals,rentals[1:]):
        if left["lease_end"]>right["lease_start"]:
            overlaps.append({"earlier_start":left["lease_start"],"later_start":right["lease_start"]})
    if overlaps:
        return {"status":"HOLD","reason":"OVERLAPPING_RENTAL_PERIODS_REQUIRE_SOURCE_REVIEW","events":events,"overlaps":overlaps}
    # Five events only for this one bounded reference acceptance case, no guessing.
    if len(events)!=5 or sum(x["type"]=="sale" for x in events)!=2 or sum(x["type"]=="rent" for x in events)!=3:
        return {"status":"HOLD","reason":"FIVE_EVENT_COMPLETENESS_UNVERIFIED","events":events}
    # Earlier source evidence conflicts with the latest displayed third rental period.
    # Keep this case on HOLD until the discrepancy is reconciled explicitly.
    starts={x["lease_start"] for x in events if x["type"]=="rent"}
    if "2023-06" in starts:
        return {"status":"HOLD","reason":"THIRD_RENTAL_PERIOD_CONFLICT_REQUIRES_REVIEW","events":events}
    canonical=json.dumps(events,sort_keys=True,separators=(",",":"))
    snapshot_id=hashlib.sha256((building+"|"+unit+"|"+source_path+"|"+canonical).encode()).hexdigest()
    return {"status":"VERIFIED","building":building,"unit":unit,"source":"DXBinteract Property History",
            "source_path":source_path,"snapshot_id":snapshot_id,
            "observed_at_utc":observed,"freshness":"observed_at_only_not_completeness_guarantee",
            "events":events,"evidence_key":snapshot_id}
