import tempfile, unittest
from pathlib import Path
from g1_history_events import review_conflict
from g1_evidence_store import persist_review, persist
from test_g1_history_events import FIXTURE
class ConflictReviewTests(unittest.TestCase):
 def test_six_events_conflict_and_durable_duplicate(self):
  extra="● RENTED\nAED\n190,000\nJun 2023 - Jun 2024\nNew contract\n"
  six=FIXTURE.replace("● SOLD",extra+"● SOLD",1)
  record=review_conflict(six,"Lamtara 1","401","/search/test","2026-10-29T19:00:00Z")
  self.assertEqual(record["status"],"CONFLICT_REQUIRES_REVIEW",record)
  self.assertEqual(len(record["events"]),6)
  self.assertTrue(record["conflicts"]["overlapping_rental_periods"])
  with tempfile.TemporaryDirectory() as p:
   db=Path(p)/"test.sqlite3"
   first=persist_review(record,db)
   second=persist_review(record,db)
   self.assertTrue(first["stored"] and first["readback_verified"] and not first["duplicate"])
   self.assertTrue(second["duplicate"] and second["readback_verified"])
   self.assertFalse(persist(record,db)["stored"])
 def test_no_wrong_unit(self):
  r=review_conflict(FIXTURE,"Lamtara 1","402","/search/test","2026-10-29T19:00:00Z")
  self.assertEqual(r["status"],"HOLD")
if __name__=="__main__":unittest.main()
