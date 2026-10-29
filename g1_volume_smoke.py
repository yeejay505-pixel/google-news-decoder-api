"""G1 synthetic durable-volume smoke; never stores user records."""
from pathlib import Path
from g1_history_events import certify
from g1_evidence_store import persist
fixture="""Lamtara 1
401
Property History
SOLD
AED 3,600,000
13, Dec 2022
Resale
RENTED
AED 190,000
Dec 2025 - Dec 2026
New Contract
"""
db=Path("/data/g1-unit-history-test/synthetic_certification.sqlite3")
payload=certify(fixture,"Lamtara 1","401","/synthetic-fixture","2026-10-29T00:00:00Z")
assert payload["status"]=="VERIFIED",payload
first=persist(payload,db)
second=persist(payload,db)
assert first["stored"] and first["readback_verified"]
assert second["stored"] and second["duplicate"] and second["readback_verified"]
print("G1_DURABLE_VOLUME_TEST", {"first_duplicate":first["duplicate"],"second_duplicate":second["duplicate"],"readback_verified":second["readback_verified"],"store":"isolated volume synthetic"},flush=True)
