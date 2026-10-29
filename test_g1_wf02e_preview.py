import tempfile,unittest
from pathlib import Path
from g1_wf02e_preview import handoff_preview
from g1_unit_queue import read_cached
from g1_evidence_store import persist,persist_review
from g1_history_events import certify,review_conflict
from test_g1_history_events import FIXTURE
class HandoffTests(unittest.TestCase):
 def test_old_cached_record_is_held_without_browser(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"cache.sqlite"
   e=certify(FIXTURE,"Lamtara 1","401","/search/test","2026-10-30T00:00Z")
   self.assertTrue(persist(e,path)["stored"])
   self.assertEqual(read_cached("Lamtara 1","401",path)["source"],"CACHE")
   preview=handoff_preview("Lamtara 1","401",path)
   self.assertEqual(preview["status"],"HOLD")
   self.assertEqual(preview["writes"],0)
 def test_header_verified_fixture_makes_review_candidate_only(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"cache.sqlite"
   e=certify(FIXTURE,"Lamtara 1","401","/search/test","2026-10-30T00:00Z")
   e["identity_check"]="PROPERTY_HEADER_DOM_MATCH"
   self.assertTrue(persist(e,path)["stored"])
   preview=handoff_preview("Lamtara 1","401",path)
   self.assertEqual(preview["status"],"READY_FOR_REVIEW")
   self.assertFalse(preview["outreach_enabled"])
   self.assertEqual(preview["writes"],0)
 def test_conflict_blocks_handoff(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/"cache.sqlite"
   extra="● RENTED\\nAED\\n190,000\\nJun 2023 - Jun 2024\\nNew contract\\n"
   data=FIXTURE.replace("● SOLD",extra+"● SOLD",1)
   review=review_conflict(data,"Lamtara 1","401","/search/test","2026-10-30T00:00Z")
   self.assertEqual(review["status"],"CONFLICT_REQUIRES_REVIEW")
   self.assertTrue(persist_review(review,path)["stored"])
   self.assertEqual(handoff_preview("Lamtara 1","401",path)["status"],"HOLD")
if __name__=="__main__":unittest.main()
