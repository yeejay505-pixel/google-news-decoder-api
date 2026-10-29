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
