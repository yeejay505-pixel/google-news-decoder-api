"""G1 isolated SQLite test store. No operational WF-02E connection."""
import json,sqlite3,os
from pathlib import Path

DB=Path("/data/g1-unit-history-test/evidence.sqlite3")
def persist(payload,db_path=DB):
    if payload.get("status")!="VERIFIED" or not payload.get("evidence_key"):
        return {"stored":False,"reason":"NOT_CERTIFIED"}
    db_path=Path(db_path)
    db_path.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(str(db_path),timeout=8,isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("CREATE TABLE IF NOT EXISTS unit_evidence (evidence_key TEXT PRIMARY KEY, building TEXT NOT NULL, unit TEXT NOT NULL, payload_json TEXT NOT NULL, inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("BEGIN IMMEDIATE")
        blob=json.dumps(payload,sort_keys=True)
        res=conn.execute("INSERT OR IGNORE INTO unit_evidence (evidence_key,building,unit,payload_json) VALUES(?,?,?,?)",
              (payload["evidence_key"],payload["building"],payload["unit"],blob))
        row=conn.execute("SELECT payload_json FROM unit_evidence WHERE evidence_key=?",(payload["evidence_key"],)).fetchone()
        conn.execute("COMMIT")
        loaded=json.loads(row[0])
        assert loaded["evidence_key"]==payload["evidence_key"]
        return {"stored":True,"duplicate":res.rowcount==0,"readback_verified":loaded==payload,
                "evidence_key":payload["evidence_key"],"store":"G1 isolated SQLite"}
    except Exception:
        if conn.in_transaction: conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def persist_review(payload, db_path=DB):
    """Persist unverified observations separately. NEVER promote to certified evidence."""
    if payload.get("status")!="CONFLICT_REQUIRES_REVIEW" or not payload.get("snapshot_id") or len(payload.get("events", []))<2:
        return {"stored":False,"reason":"NOT_A_CONFLICT_REVIEW"}
    db_path=Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(str(db_path),timeout=8,isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("""CREATE TABLE IF NOT EXISTS unit_review (
          snapshot_id TEXT PRIMARY KEY,
          building TEXT NOT NULL,
          unit TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          review_status TEXT NOT NULL CHECK(review_status='CONFLICT_REQUIRES_REVIEW'),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("BEGIN IMMEDIATE")
        blob=json.dumps(payload,sort_keys=True)
        added=conn.execute("INSERT OR IGNORE INTO unit_review(snapshot_id,building,unit,payload_json,review_status) VALUES(?,?,?,?,?)",
             (payload["snapshot_id"],payload["building"],payload["unit"],blob,"CONFLICT_REQUIRES_REVIEW")).rowcount
        row=conn.execute("SELECT payload_json FROM unit_review WHERE snapshot_id=?",(payload["snapshot_id"],)).fetchone()
        conn.execute("COMMIT")
        readback=json.loads(row[0])
        immutable=("snapshot_id","building","unit","source","source_path","events","conflicts","status","eligible_for_outreach")
        verified=all(readback.get(k)==payload.get(k) for k in immutable)
        if not verified:
            return {"stored":False,"reason":"SNAPSHOT_CONTENT_MISMATCH","duplicate":added==0,"review_only":True}
        return {"stored":True,"review_only":True,"eligible_for_outreach":False,"duplicate":added==0,
                "readback_verified":True,"snapshot_id":payload["snapshot_id"],"store":"G1 isolated unit_review"}
    except Exception:
        if conn.in_transaction:conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
