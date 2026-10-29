"""Offline bounded G1 queue: no browser navigation, no outreach."""
import re,sqlite3,json
from pathlib import Path
from g1_history_events import certify,review_conflict
from g1_evidence_store import persist,persist_review,DB
def validate(building,units):
 if not isinstance(building,str) or not 2<=len(building.strip())<=120:raise ValueError("INVALID_BUILDING")
 if not isinstance(units,list) or not 1<=len(units)<=10:raise ValueError("QUEUE_LIMIT")
 clean=[]
 for unit in units:
  if not isinstance(unit,str) or not re.fullmatch(r"[A-Za-z0-9-]{1,16}",unit):raise ValueError("INVALID_UNIT")
  if unit in clean:raise ValueError("DUPLICATE_UNIT")
  clean.append(unit)
 return building.strip(),clean
def process_fixture_queue(building, units, pages, db_path=DB):
 building,units=validate(building,units)
 rows=[]
 for unit in units:
  page=pages.get(unit)
  if not isinstance(page,dict) or not isinstance(page.get("text"),str):
   rows.append({"unit":unit,"status":"HOLD","reason":"MISSING_MANUAL_PAGE"});continue
  path=page.get("source_path","")
  if not re.fullmatch(r"/dubai-property-prices/search/\d+",path):
   rows.append({"unit":unit,"status":"HOLD","reason":"INVALID_SOURCE_PATH"});continue
  evidence=certify(page["text"],building,unit,path,page.get("observed_at_utc",""))
  if evidence["status"]=="VERIFIED":
   receipt=persist(evidence,db_path)
   rows.append({"unit":unit,"status":"VERIFIED","receipt":receipt})
  else:
   review=review_conflict(page["text"],building,unit,path,page.get("observed_at_utc",""))
   receipt=persist_review(review,db_path) if review["status"]=="CONFLICT_REQUIRES_REVIEW" else {"stored":False}
   rows.append({"unit":unit,"status":"HOLD","reason":evidence.get("reason"),"review_receipt":receipt})
 return {"mode":"OFFLINE_FIXTURE_ONLY","building":building,"processed":len(rows),"results":rows}
def read_cached(building,unit,db_path=DB):
 building,units=validate(building,[unit])
 if not Path(db_path).exists():return {"status":"NOT_FOUND"}
 conn=sqlite3.connect(str(db_path))
 try:
  verified=conn.execute("SELECT payload_json FROM unit_evidence WHERE building=? AND unit=? ORDER BY inserted_at DESC LIMIT 1",(building,unit)).fetchone() if conn.execute("SELECT name FROM sqlite_master WHERE name='unit_evidence'").fetchone() else None
  review=conn.execute("SELECT payload_json FROM unit_review WHERE building=? AND unit=? ORDER BY created_at DESC LIMIT 1",(building,unit)).fetchone() if conn.execute("SELECT name FROM sqlite_master WHERE name='unit_review'").fetchone() else None
  if review:return {"status":"HOLD","source":"CACHE","review":json.loads(review[0]),"eligible_for_outreach":False}
  if verified:return {"status":"VERIFIED","source":"CACHE","evidence":json.loads(verified[0]),"eligible_for_outreach":False}
  return {"status":"NOT_FOUND"}
 finally:conn.close()
