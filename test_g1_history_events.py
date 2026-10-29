import unittest
from g1_history_events import parse_events,certify
FIXTURE="""Lamtara 1
401
Property History
SOLD
AED 3,600,000
13, Dec 2022
Resale
SOLD
AED 2,890,000
08, Feb 2022
Primary
RENTED
AED 190,000
Dec 2025 - Dec 2026
New Contract
"""
class Tests(unittest.TestCase):
 def test_events(self):
  events=parse_events(FIXTURE)
  self.assertEqual(len(events),3)
  self.assertEqual(sum(x["type"]=="sale" for x in events),2)
  self.assertEqual(events[-1]["lease_end"],"2026-12")
 def test_certification(self):
  self.assertEqual(certify(FIXTURE,"Lamtara 1","401","/search/4140564","2026-10-29T18:00Z")["status"],"VERIFIED")
 def test_other_unit_hold(self):
  self.assertEqual(certify(FIXTURE,"Lamtara 1","402","/search/4140564","2026-10-29T18:00Z")["status"],"HOLD")
 def test_missing_rent_hold(self):
  self.assertEqual(certify(FIXTURE.split("RENTED")[0],"Lamtara 1","401","/search/4140564","2026-10-29T18:00Z")["status"],"HOLD")
if __name__=="__main__": unittest.main()
