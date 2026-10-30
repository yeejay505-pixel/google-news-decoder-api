import unittest
from r2_public_listing_research_sample import research_sample
class PublicResearchFitness(unittest.TestCase):
 def test_real_public_observations_are_three_unlinked_leads(self):
  r=research_sample()
  self.assertEqual(r["input_count"],3)
  self.assertEqual(r["opportunity_count"],3)
  self.assertTrue(all(x["unit_number"] is None for x in r["opportunities"]))
 def test_every_observation_is_hold_not_deduplicated_by_layout(self):
  r=research_sample()
  for x in r["opportunities"]:
   self.assertEqual(x["status"],"HOLD")
   self.assertIn("SOURCE_AUTHORIZATION_UNCONFIRMED",x["reasons"])
   self.assertIn("UNIT_IDENTITY_UNCONFIRMED",x["reasons"])
   self.assertIn("UNKNOWN_LISTING_AGE",x["reasons"])
   self.assertIn("WEAK_OR_STALE_MARKET_SAMPLE",x["reasons"])
   self.assertIsNone(x["indicative_discount_pct"])
 def test_no_owner_actions_or_writes(self):
  r=research_sample()
  self.assertFalse(r["outreach_enabled"]);self.assertEqual(r["writes"],0)
if __name__=="__main__":unittest.main()
