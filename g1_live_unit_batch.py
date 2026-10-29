"""Release 2 Step 3: bounded manual-page queue with durable checkpoints.
Never navigates or searches DXBinteract. Operator opens each page manually.
"""
import json,sqlite3,hashlib
from pathlib import Path
from g1_unit_queue import validate,DB

def _connect(path):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(str(path),timeout=8,isolation_level=None)
 c.execute("PRAGMA journal_mode=WAL")
 c.execute("""CREATE TABLE IF NOT EXISTS g1_unit_batch(
 batch_id TEXT NOT NULL, building TEXT NOT NULL, unit TEXT NOT NULL,
 ordinal INTEGER NOT NULL, state TEXT NOT NULL CHECK(state IN ('PENDING','VERIFIED','HOLD')),
 receipt_json TEXT, PRIMARY KEY(batch_id,unit))""")
 return c

def create_batch(building,units,db_path=DB):
 building,units=validate(building,units)
 identity=json.dumps([building,units],separators=(",",":"))
 batch_id=hashlib.sha256(identity.encode()).hexdigest()[:24]
 c=_connect(db_path)
 try:
  c.execute("BEGIN IMMEDIATE")
  for i,unit in enumerate(units):
   c.execute("INSERT OR IGNORE INTO g1_unit_batch(batch_id,building,unit,ordinal,state) VALUES(?,?,?,?,'PENDING')",(batch_id,building,unit,i))
  c.execute("COMMIT")
 finally:c.close()
 return status(batch_id,db_path)

def status(batch_id,db_path=DB):
 if not Path(db_path).exists():return {"status":"NOT_FOUND"}
 c=_connect(db_path)
 try:
  rows=c.execute("SELECT building,unit,ordinal,state,receipt_json FROM g1_unit_batch WHERE batch_id=? ORDER BY ordinal",(batch_id,)).fetchall()
  if not rows:return {"status":"NOT_FOUND"}
  return {"batch_id":batch_id,"building":rows[0][0],"state":"COMPLETE" if all(r[3]!='PENDING' for r in rows) else "IN_PROGRESS",
   "units":[{"unit":r[1],"state":r[3],"receipt":json.loads(r[4]) if r[4] else None} for r in rows],
   "next_unit":next((r[1] for r in rows if r[3]=='PENDING'),None),
   "browser_navigation":"MANUAL_ONLY","outreach_enabled":False}
 finally:c.close()

def record_observation(batch_id,unit,inspection,db_path=DB):
 c=_connect(db_path)
 try:
  c.execute("BEGIN IMMEDIATE")
  row=c.execute("SELECT building,unit,state,ordinal FROM g1_unit_batch WHERE batch_id=? AND unit=?",(batch_id,unit)).fetchone()
  next_row=c.execute("SELECT unit FROM g1_unit_batch WHERE batch_id=? AND state='PENDING' ORDER BY ordinal LIMIT 1",(batch_id,)).fetchone()
  if not row or (row[2]=='PENDING' and (not next_row or next_row[0]!=unit)):
   c.execute("ROLLBACK");return {"accepted":False,"reason":"UNKNOWN_OR_OUT_OF_ORDER"}
  if row[2]!='PENDING':
   c.execute("COMMIT");return {"accepted":True,"duplicate":True,"state":row[2]}
  evidence=inspection.get("event_certification") or {}
  review=inspection.get("review_record") or {}
  verified=evidence.get("status")=="VERIFIED" and evidence.get("building")==row[0] and str(evidence.get("unit"))==unit and evidence.get("identity_check")=="PROPERTY_HEADER_DOM_MATCH" and inspection.get("persistence",{}).get("readback_verified") is True
  conflict=review.get("status")=="CONFLICT_REQUIRES_REVIEW" and review.get("building")==row[0] and str(review.get("unit"))==unit and inspection.get("review_persistence",{}).get("readback_verified") is True
  if not verified and not conflict:
   c.execute("ROLLBACK");return {"accepted":False,"reason":"NO_DURABLE_MATCHING_EVIDENCE"}
  state="VERIFIED" if verified else "HOLD"
  receipt={"snapshot_id":evidence.get("snapshot_id") if verified else review.get("snapshot_id"),
           "source":"G1_ISOLATED","verified_page_identity":verified,"outreach_enabled":False}
  c.execute("UPDATE g1_unit_batch SET state=?, receipt_json=? WHERE batch_id=? AND unit=?",(state,json.dumps(receipt),batch_id,unit))
  c.execute("COMMIT")
  return {"accepted":True,"duplicate":False,"state":state,"receipt":receipt}
 except:
  if c.in_transaction:c.execute("ROLLBACK")
  raise
 finally:c.close()
