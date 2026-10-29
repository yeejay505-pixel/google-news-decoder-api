"""Synthetic persistent-volume test only; no user data."""
from pathlib import Path
from g1_history_events import certify
from g1_evidence_store import persist
from test_g1_history_events import FIXTURE
db=Path("/data/g1-unit-history-test/synthetic_certification_v2.sqlite3")
payload=certify(FIXTURE,"Lamtara 1","401","/synthetic-fixture","2026-10-29T00:00:00Z")
assert payload["status"]=="VERIFIED",payload
first=persist(payload,db); second=persist(payload,db)
assert first["stored"] and first["readback_verified"]
assert second["stored"] and second["duplicate"] and second["readback_verified"]
print("G1_DURABLE_VOLUME_TEST",{"first_duplicate":first["duplicate"],"second_duplicate":second["duplicate"],"readback_verified":second["readback_verified"]},flush=True)
