import tempfile,unittest
from pathlib import Path
from g1_unit_queue import validate,process_fixture_queue,read_cached
from test_g1_history_events import FIXTURE
class QueueTests(unittest.TestCase):
 def test_dynamic_building_and_cached_read(self):
  text=FIXTURE.replace("Lamtara 1","Different Building").replace("\n401\n","\nB-17\n")
  with tempfile.TemporaryDirectory() as folder:
   db=Path(folder)/"test.sqlite3"
   result=process_fixture_queue("Different Building",["B-17","B-18"],{"B-17":{"text":text,"source_path":"/dubai-property-prices/search/12345","observed_at_utc":"2026-10-30T00:00:00Z"}},db)
   self.assertEqual(result["processed"],2)
   self.assertEqual(result["results"][0]["status"],"VERIFIED")
   self.assertEqual(result["results"][1]["status"],"HOLD")
   self.assertEqual(read_cached("Different Building","B-17",db)["status"],"VERIFIED")
 def test_bounded_limits(self):
  with self.assertRaises(ValueError):validate("Building",[str(x) for x in range(11)])
  with self.assertRaises(ValueError):validate("Building",["401","401"])
if __name__=="__main__":unittest.main()
