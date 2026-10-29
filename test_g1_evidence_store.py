import tempfile,unittest
from pathlib import Path
from g1_history_events import certify
from g1_evidence_store import persist
from test_g1_history_events import FIXTURE
class TestPersistence(unittest.TestCase):
 def test_new_duplicate_readback_and_hold(self):
  payload=certify(FIXTURE,"Lamtara 1","401","/search/test","2026-10-29T18:00:00Z")
  self.assertEqual(payload["status"],"VERIFIED",payload)
  with tempfile.TemporaryDirectory() as folder:
   db=Path(folder)/"evidence.sqlite3"
   first=persist(payload,db); second=persist(payload,db)
   self.assertTrue(first["stored"] and first["readback_verified"])
   self.assertFalse(first["duplicate"])
   self.assertTrue(second["duplicate"] and second["readback_verified"])
   self.assertFalse(persist({"status":"HOLD"},db)["stored"])
if __name__=="__main__":unittest.main()
