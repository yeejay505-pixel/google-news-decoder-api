import unittest
from r2_listing_opportunity_engine import analyze
MARKET={"source":"DXBINTERACT_MATRIX","observed_at":"2026-10-30","sample_count":8,"benchmark_price_sqft":2200,"benchmark_annual_rent":105000}
def sample(ref,unit="901",verified=True,agent="A",authorization="AUTHORIZED_INPUT",kind="sale"):
 return {"source":"authorized-portal","source_listing_id":ref,"building":"Golf Heights",
 "unit_number":unit,"unit_identity_verified":verified,"kind":kind,"bedrooms":1,
 "size_sqft":757,"asking_aed":1650000 if kind=="sale" else 103000,
 "first_seen":"2026-08-01","agent_ref":agent,"authorization":authorization}
class Step4Tests(unittest.TestCase):
 def test_same_unit_multiple_agent_grouping_and_hold(self):
  r=analyze([sample("L1",agent="A"),sample("L2",agent="B")],MARKET)
  self.assertEqual(r["opportunity_count"],1)
  x=r["opportunities"][0]
  self.assertEqual(x["listing_count"],2)
  self.assertIn("MULTIPLE_AGENT_LISTINGS",x["reasons"])
  self.assertEqual(x["status"],"HOLD")
  self.assertEqual(x["contact_gate"],"HOLD")
 def test_no_merge_when_unit_not_proven(self):
  r=analyze([sample("L1",verified=False),sample("L2",verified=False)],MARKET)
  self.assertEqual(r["opportunity_count"],2)
 def test_dedupe_same_source_id(self):
  r=analyze([sample("L1"),sample("L1")],MARKET)
  self.assertEqual(r["unique_source_listings"],1)
 def test_different_sale_rent_remain_separate(self):
  r=analyze([sample("L1"),sample("L2",kind="rent")],MARKET)
  self.assertEqual(r["opportunity_count"],2)
 def test_limited_sample_not_price_verdict(self):
  r=analyze([sample("L1")],{**MARKET,"sample_count":2})
  x=r["opportunities"][0]
  self.assertIsNone(x["indicative_discount_pct"])
  self.assertIn("WEAK_OR_STALE_MARKET_SAMPLE",x["reasons"])
 def test_unauthorized_hold(self):
  r=analyze([sample("L1",authorization="UNKNOWN")],MARKET)
  self.assertIn("SOURCE_AUTHORIZATION_UNCONFIRMED",r["opportunities"][0]["reasons"])
 def test_no_outreach_and_writes(self):
  r=analyze([sample("L1")],MARKET)
  self.assertFalse(r["outreach_enabled"]);self.assertEqual(r["writes"],0)
  self.assertFalse(r["opportunities"][0]["outreach_enabled"])
 def test_batch_limit(self):
  with self.assertRaises(ValueError):analyze([sample(str(i)) for i in range(101)],MARKET)
if __name__=="__main__":unittest.main()
