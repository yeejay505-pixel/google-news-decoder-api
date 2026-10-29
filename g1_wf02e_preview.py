"""G1 read-only candidate contract. NOT a WF-02E writer."""
from g1_unit_queue import read_cached
def handoff_preview(building,unit,db_path=None):
    result=read_cached(building,unit,db_path) if db_path is not None else read_cached(building,unit)
    if result["status"]!="VERIFIED":
        return {"contract":"G1_WF02E_PREVIEW_V1","building":building,"unit":unit,"status":"HOLD",
                "reason":"NO_UNCONFLICTED_CERTIFIED_HISTORY","writes":0,"outreach_enabled":False}
    evidence=result["evidence"]
    if evidence.get("identity_check")!="PROPERTY_HEADER_DOM_MATCH":
        return {"contract":"G1_WF02E_PREVIEW_V1","building":building,"unit":unit,"status":"HOLD",
                "reason":"SOURCE_HEADER_IDENTITY_UNVERIFIED","writes":0,"outreach_enabled":False}
    return {"contract":"G1_WF02E_PREVIEW_V1","building":building,"unit":unit,"status":"READY_FOR_REVIEW",
            "source":"DXBinteract Property History","source_path":evidence["source_path"],
            "evidence_key":evidence["evidence_key"],"observed_at_utc":evidence["observed_at_utc"],
            "transactions":evidence["events"],"writes":0,"outreach_enabled":False}
