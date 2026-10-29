import unittest
from g1_unit_history_adapter import parse_reference
class AdapterTests(unittest.TestCase):
 def test_reference(self):
  r=parse_reference("Lamtara 1 apartment 401 2 bedrooms 1,356 sqft Resale AED 3,600,000 Rent AED 190,000")
  self.assertEqual(r["status"],"EVIDENCE_PRESENT")
 def test_no_exact_unit(self):
  r=parse_reference("Lamtara 1 apartment 402 2 bedrooms 1,356 sqft AED 3,600,000 AED 190,000")
  self.assertEqual(r["status"],"HOLD")
 def test_no_building(self):
  r=parse_reference("Other Building 401 2 beds 1356 sqft AED 3,600,000 AED 190,000")
  self.assertEqual(r["status"],"HOLD")
 def test_missing_rent(self):
  r=parse_reference("Lamtara 1 401 2 beds 1356 sqft AED 3,600,000")
  self.assertEqual(r["status"],"INCOMPLETE")
if __name__=="__main__":unittest.main()
