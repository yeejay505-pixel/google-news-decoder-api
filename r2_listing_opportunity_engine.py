"""Release 2 Step 4: offline, authorized-listing discovery and opportunity review.
No scraping, external calls, outreach, or WF-02E writes.
"""
import hashlib,json,datetime,re
from collections import defaultdict
def norm(x): return re.sub(r"\s+"," ",str(x or "").strip()).casefold()
def parse_date(x):
 try:return datetime.date.fromisoformat(str(x)[:10])
 except (ValueError,TypeError):return None
def analyze(listings,market,as_of="2026-10-30"):
 if not isinstance(listings,list) or len(listings)>100:raise ValueError("LISTING_BATCH_LIMIT_100")
 today=parse_date(as_of)
 if not today or not isinstance(market,dict):raise ValueError("INVALID_CONTEXT")
 rows=[];seen=set()
 for a in listings:
  if not isinstance(a,dict):raise ValueError("INVALID_LISTING")
  source=norm(a.get("source"));ref=str(a.get("source_listing_id") or "").strip()
  if not source or not ref or len(ref)>150:raise ValueError("SOURCE_ID_REQUIRED")
  ident=(source,ref)
  if ident in seen:continue
  seen.add(ident)
  kind=norm(a.get("kind","sale"))
  building=norm(a.get("building"))
  bedroom=a.get("bedrooms")
  unit=norm(a.get("unit_number"))
  size=a.get("size_sqft");ask=a.get("asking_aed")
  listed=parse_date(a.get("first_seen"))
  verified=bool(a.get("unit_identity_verified")) and bool(unit)
  # Do not infer duplicate units from bedroom, size or price alone.
  group=("EXACT",building,unit,kind) if verified else ("SOURCE",source,ref,kind)
  checks=[]
  if not building or kind not in ("sale","rent"):checks.append("INVALID_LOCATION_OR_KIND")
  if not isinstance(size,(int,float)) or size<=0:checks.append("INVALID_SIZE")
  if not isinstance(ask,(int,float)) or ask<=0:checks.append("INVALID_PRICE")
  if not listed or listed>today:checks.append("UNKNOWN_LISTING_AGE")
  age=(today-listed).days if listed and listed<=today else None
  benchmark=market.get("benchmark_price_sqft") if kind=="sale" else market.get("benchmark_annual_rent")
  benchmark_ok= isinstance(benchmark,(int,float)) and benchmark>0 and market.get("sample_count",0)>=5 and market.get("observed_at") and parse_date(market["observed_at"]) and (today-parse_date(market["observed_at"])).days<=90
  if not benchmark_ok:checks.append("WEAK_OR_STALE_MARKET_SAMPLE")
  if not verified:checks.append("UNIT_IDENTITY_UNCONFIRMED")
  if a.get("authorization")!="AUTHORIZED_INPUT":checks.append("SOURCE_AUTHORIZATION_UNCONFIRMED")
  rows.append({"source":source,"source_listing_id":ref,"building":building,"unit_number":unit or None,
   "bedrooms":bedroom,"kind":kind,"size_sqft":size,"asking_aed":ask,"age_days":age,
   "group":group,"warnings":checks,"verified_unit":verified,"market_eligible":benchmark_ok,
   "benchmark":benchmark,"source_url":a.get("source_url"),"agent_ref":a.get("agent_ref")})
 grouped=defaultdict(list)
 for row in rows:grouped[row["group"]].append(row)
 results=[]
 for group,items in grouped.items():
  is_exact=group[0]=="EXACT"
  agents=len(set(str(x.get("agent_ref") or x["source"]) for x in items))
  asks=[x["asking_aed"] for x in items if isinstance(x["asking_aed"],(int,float)) and x["asking_aed"]>0]
  min_ask=min(asks) if asks else None
  age=max([x["age_days"] for x in items if x["age_days"] is not None],default=None)
  issues=sorted(set(z for x in items for z in x["warnings"]))
  if is_exact and len(items)>1:issues.append("POSSIBLE_SAME_UNIT_DUPLICATE")
  if is_exact and agents>1:issues.append("MULTIPLE_AGENT_LISTINGS")
  bench=items[0]["benchmark"]
  size=items[0]["size_sqft"]
  discount=None
  if all(x["market_eligible"] for x in items) and min_ask and isinstance(size,(int,float)) and size>0:
   expected=bench*size if items[0]["kind"]=="sale" else bench
   discount=round((expected-min_ask)/expected*100,2) if expected>0 else None
  # Ranking is editorial triage, never a contact recommendation.
  score=min(100,max(0,30 + min(age or 0,180)//6 + (10 if is_exact else 0)
      +(15 if is_exact and len(items)>1 else 0)
      +(min(20,max(0,int(discount*2))) if discount is not None else 0)))
  decision="REVIEW" if not issues else "HOLD"
  opportunity_id=hashlib.sha256(json.dumps(group,sort_keys=True).encode()).hexdigest()[:20]
  results.append({"opportunity_id":opportunity_id,"building":items[0]["building"],
   "unit_number":items[0]["unit_number"] if is_exact else None,"kind":items[0]["kind"],
   "listing_count":len(items),"distinct_agent_refs":agents,
   "sources":[{"source":x["source"],"id":x["source_listing_id"]} for x in items],
   "min_asking_aed":min_ask,"oldest_age_days":age,
   "indicative_discount_pct":discount,"score":score,"status":decision,
   "reasons":issues,"contact_gate":"HOLD","outreach_enabled":False,
   "exclusivity":"UNKNOWN","ownership_currentness":"UNVERIFIED"})
 results.sort(key=lambda x:(-x["score"],x["opportunity_id"]))
 return {"engine":"RELEASE2_STEP4_ISOLATED_V1","mode":"OFFLINE_AUTHORIZED_INPUT",
  "as_of":as_of,"input_count":len(listings),"unique_source_listings":len(rows),
  "opportunity_count":len(results),"opportunities":results,
  "market_context":{"sample_count":market.get("sample_count"),
   "source":market.get("source"),"observed_at":market.get("observed_at")},
  "writes":0,"outreach_enabled":False}
