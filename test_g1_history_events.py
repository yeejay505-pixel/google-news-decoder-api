import unittest
from g1_history_events import parse_events,certify
FIXTURE="Lamtara 1\n401\nProperty History\n● RENTED\nAED\n190,000\nDec 2025 - Dec 2026\nNew contract\n● RENTED\nAED\n195,000\nNov 2024 - Nov 2025\nNew contract\n● RENTED\nAED\n195,000\nNov 2023 - Nov 2024\nNew contract\n● SOLD\nAED\n3,600,000\n13, Dec 2022\nResale\nSold by Individual\n● SOLD\nAED\n2,890,000\n08, Feb 2022\nPrimary\nSold by Developer\n"
class Tests(unittest.TestCase):
 def test_five_events(self):
  events=parse_events(FIXTURE)
  self.assertEqual(len(events),5,events)
  self.assertEqual(sum(e["type"]=="sale" for e in events),2)
  self.assertEqual(sum(e["type"]=="rent" for e in events),3)
  self.assertEqual(events[0]["amount_aed"],190000)
  self.assertEqual(events[0]["lease_end"],"2026-12")
  self.assertEqual(events[3]["date"],"2022-12-13")
 def test_certification(self):
  self.assertEqual(certify(FIXTURE,"Lamtara 1","401","/search/test","2026-10-29T18:00Z")["status"],"VERIFIED")
 def test_other_unit_hold(self):
  self.assertEqual(certify(FIXTURE,"Lamtara 1","402","/search/test","2026-10-29T18:00Z")["status"],"HOLD")
 def test_missing_rent_hold(self):
  self.assertEqual(certify(FIXTURE.split("● RENTED")[0],"Lamtara 1","401","/search/test","2026-10-29T18:00Z")["status"],"HOLD")
 def test_conflicting_rental_period_hold(self):
  changed=FIXTURE.replace("Nov 2023 - Nov 2024","Jun 2023 - Jun 2024")
  receipt=certify(changed,"Lamtara 1","401","/search/test","2026-10-29T18:00Z")
  self.assertEqual(receipt["status"],"HOLD")
  self.assertEqual(receipt["reason"],"THIRD_RENTAL_PERIOD_CONFLICT_REQUIRES_REVIEW")
 def test_spurious_overlapping_rental_hold(self):
  extra="● RENTED\\nAED\\n190,000\\nApr 2024 - Jun 2026\\nNew contract\\n"
  changed=FIXTURE.replace("● SOLD",extra+"● SOLD",1)
  receipt=certify(changed,"Lamtara 1","401","/search/test","2026-10-29T18:00Z")
  self.assertEqual(receipt["status"],"HOLD")
  self.assertIn(receipt["reason"],("OVERLAPPING_RENTAL_PERIODS_REQUIRE_SOURCE_REVIEW","FIVE_EVENT_COMPLETENESS_UNVERIFIED"))
if __name__=="__main__":unittest.main()
