import tempfile,unittest
from pathlib import Path
from g1_history_events import certify
from g1_evidence_store import persist
class TestPersistence(unittest.TestCase):
 def test_new_duplicate_readback_and_hold(self):
  fixture="Lamtara 1\n401\nProperty History\nSOLD\nAED 3,600,000\n13, Dec 2022\nResale\nRENTED\nAED 190,000\nDec 2025 - Dec 2026\nNew Contract"
  payload=certify(fixture,"Lamtara 1","401","/search/test","2026-10-29T18:00:00Z")
  self.assertEqual(payload["status"],"VERIFIED")
  with tempfile.TemporaryDirectory() as folder:
   db=Path(folder)/"evidence.sqlite3"
   first=persist(payload,db); second=persist(payload,db)
   self.assertTrue(first["stored"] and first["readback_verified"])
   self.assertFalse(first["duplicate"])
   self.assertTrue(second["duplicate"] and second["readback_verified"])
   self.assertFalse(persist({"status":"HOLD"},db)["stored"])
if __name__=="__main__":unittest.main()
