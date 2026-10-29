import unittest
from g2_wf02e_inactive_adapter import project_g1_to_wf02e
BASE={"contract":"G1_WF02E_PREVIEW_V1","status":"READY_FOR_REVIEW",
 "building":"Golf Heights","unit":"901","evidence_key":"a"*64,
 "observed_at_utc":"2026-10-29T22:54:48+00:00",
 "transactions":[{"type":"sale","date":"2022-12-27","amount_aed":1336888}]}
CONTEXT={"building":"Golf Heights","unitNumber":"901","unitId":"TEST-GOLF901"}
class TestInactive(unittest.TestCase):
 def test_nominal_no_writes(self):
  x=project_g1_to_wf02e(BASE,CONTEXT)
  self.assertEqual(x["status"],"MAPPED_INACTIVE")
  self.assertEqual(x["writes"],0)
  self.assertFalse(x["outreach_enabled"])
  self.assertEqual(x["contactGate"],"HOLD")
  self.assertEqual(x["dxbEvidence"]["historyCoverage"],"PARTIAL")
  self.assertEqual(x["dxbEvidence"]["saleAfterSource"],"Unknown")
 def test_conflict_hold(self):
  x=project_g1_to_wf02e({**BASE,"status":"HOLD"},CONTEXT)
  self.assertEqual(x["status"],"HOLD")
  self.assertIsNone(x["dxbEvidence"])
 def test_mismatched_unit_hold(self):
  x=project_g1_to_wf02e(BASE,{**CONTEXT,"unitNumber":"902"})
  self.assertEqual(x["reason"],"UNIT_CONTEXT_MISMATCH")
 def test_sale_after_source_only_with_date(self):
  x=project_g1_to_wf02e(BASE,{**CONTEXT,"ownerSourceDate":"2022-01-01"})
  self.assertEqual(x["dxbEvidence"]["saleAfterSource"],"Yes")
 def test_no_false_negative_sale(self):
  x=project_g1_to_wf02e(BASE,{**CONTEXT,"ownerSourceDate":"2023-01-01"})
  self.assertEqual(x["dxbEvidence"]["saleAfterSource"],"Unknown")
if __name__=="__main__": unittest.main()
