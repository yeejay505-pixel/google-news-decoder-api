"""G2 inactive WF-02E evidence adapter: pure, no network, no writes."""
from datetime import datetime,timezone

def project_g1_to_wf02e(preview, context):
    result={"contract":"G2_WF02E_INACTIVE_V1","active":False,"writes":0,"outreach_enabled":False,
            "status":"HOLD","reason":"UNVERIFIED_G1_INPUT","dxbEvidence":None}
    if not isinstance(preview,dict) or not isinstance(context,dict):return result
    if preview.get("contract")!="G1_WF02E_PREVIEW_V1" or preview.get("status")!="READY_FOR_REVIEW":
        return {**result,"reason":"G1_PREVIEW_NOT_READY"}
    building=context.get("building")
    unit=context.get("unitNumber")
    if not building or not unit or building!=preview.get("building") or str(unit)!=str(preview.get("unit")):
        return {**result,"reason":"UNIT_CONTEXT_MISMATCH"}
    key=preview.get("evidence_key")
    observed=preview.get("observed_at_utc")
    events=preview.get("transactions")
    if not isinstance(key,str) or len(key)!=64 or not isinstance(events,list) or not events:
        return {**result,"reason":"MISSING_EVIDENCE"}
    try:
        dt=datetime.fromisoformat(observed.replace("Z","+00:00"))
        if dt.tzinfo is None or dt>datetime.now(timezone.utc):
            raise ValueError("invalid timestamp")
    except (ValueError,AttributeError,TypeError):
        return {**result,"reason":"INVALID_OBSERVED_TIME"}
    sales=sorted([e for e in events if e.get("type")=="sale" and e.get("date")],key=lambda e:e["date"])
    rents=sorted([e for e in events if e.get("type")=="rent" and e.get("lease_start")],key=lambda e:e["lease_start"])
    s=sales[-1] if sales else {}
    r=rents[-1] if rents else {}
    source_date=context.get("ownerSourceDate")
    # No source date means no inference about sale relative to owner data.
    sale_after="Unknown"
    if source_date and s.get("date"):
        try:
            date=datetime.fromisoformat(source_date.replace("Z","+00:00")).date()
            sale_after="Yes" if datetime.fromisoformat(s["date"]).date()>date else "Unknown"
        except (ValueError,AttributeError,TypeError):pass
    evidence={"sourceAdapter":"DXBINTERACT_G1","sourceMethod":"HUMAN_AUTHENTICATED_PAGE_READ",
        "sourceAuthority":"DXBinteract displayed property history",
        "sourcePropertyRecordId":key,"matchStatus":"EXACT_MATCH",
        "matchConfidence":90,"historyCoverage":"PARTIAL",
        "latestSaleDate":s.get("date"),"latestSalePriceAED":s.get("amount_aed"),
        "latestRentStart":r.get("lease_start"),"latestRentEnd":r.get("lease_end"),
        "latestAnnualRentAED":r.get("amount_aed"),
        "saleAfterSource":sale_after,"rentAfterSource":"Unknown",
        "checkedAt":observed,"authSessionStatus":"OBSERVED",
        "sourceStatus":"OBSERVED_PARTIAL","evidenceLevel":"B — Page-attributed, uncorroborated",
        "evidenceSummary":"G1 snapshot; historical coverage unknown; no proof of legal title or owner currentness"}
    return {**result,"status":"MAPPED_INACTIVE","reason":"NO_WORKFLOW_CONNECTION",
        "dxbEvidence":evidence,"context":{"building":building,"unitNumber":str(unit),
          "buildingId":context.get("buildingId"),"unitId":context.get("unitId")},
        "contactGate":"HOLD","verificationMode":"RESEARCH"}
