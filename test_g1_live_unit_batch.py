import tempfile,unittest
from pathlib import Path
from g1_live_unit_batch import create_batch,status,record_observation
class BatchTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=Path(self.tmp.name)/"test.sqlite"
  self.q=create_batch("Golf Heights",["901","902"],self.db);self.bid=self.q["batch_id"]
 def tearDown(self):self.tmp.cleanup()
 def test_order_and_resume(self):
  self.assertEqual(self.q["next_unit"],"901")
  self.assertEqual(create_batch("Golf Heights",["901","902"],self.db)["next_unit"],"901")
  self.assertEqual(record_observation(self.bid,"902",{},self.db)["reason"],"UNKNOWN_OR_OUT_OF_ORDER")
 def test_reject_non_durable_or_wrong_unit(self):
  self.assertEqual(record_observation(self.bid,"901",{"event_certification":{"status":"VERIFIED","unit":"902"}},self.db)["reason"],"NO_DURABLE_MATCHING_EVIDENCE")
 def test_record_then_duplicate(self):
  obs={"event_certification":{"status":"VERIFIED","building":"Golf Heights","unit":"901","identity_check":"PROPERTY_HEADER_DOM_MATCH","snapshot_id":"s"},
       "persistence":{"readback_verified":True}}
  self.assertTrue(record_observation(self.bid,"901",obs,self.db)["accepted"])
  self.assertTrue(record_observation(self.bid,"901",obs,self.db)["duplicate"])
  self.assertEqual(status(self.bid,self.db)["next_unit"],"902")
 def test_conflict_held_and_no_outreach(self):
  obs={"review_record":{"status":"CONFLICT_REQUIRES_REVIEW","building":"Golf Heights","unit":"901","snapshot_id":"r"},
       "review_persistence":{"readback_verified":True}}
  self.assertEqual(record_observation(self.bid,"901",obs,self.db)["state"],"HOLD")
  self.assertFalse(status(self.bid,self.db)["outreach_enabled"])
if __name__=="__main__":unittest.main()
