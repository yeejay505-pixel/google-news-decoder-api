# Release 2 / Step 1 — DXBinteract source validation (2026-10-30)
Read-only audit; no change to WF-02A, WF-02C, WF-02E or Releases 1/3.

## Direct connector verification
- search_locations("Golf Heights"): exact project resolved, id 39106; path Golf Heights, Al Thanyah Third.
- get_sale_transactions(location=Golf Heights, 2022-12-01 through 2023-01-15, limit 5): returns individual sales with sale date, project, size, price, bedroom count, project property_id/ref, but NO exposed unit number or exact-unit lookup parameter. Sample had hasMore=true. A returned property_id is not proof of the requested apartment.
- get_rent_contracts(location=Golf Heights, from 2025-01-01, limit 5): returns four rent contracts (size, annual rent, lease dates, bed, floor), NO exposed unit number or exact-unit lookup. Absence of a unit-specific result is not evidence of no tenancy.
- get_location_summary(location=Golf Heights, 12m): summary metrics available; supply=null, so listed supply is not guaranteed.
- Connector contract: cannot search a specific unit number, retrieve full Property History by apartment number, or get individual active listing URLs, listing age, duplicate agents, or exclusivity. Do not mislabel building comparables as exact-unit evidence.

## Current n8n workflow audit (read-only)
- WF-02A Listing Opportunity Orchestrator: active, 11 nodes, validates input, calls WF-02E, outputs eligible/exclude/hold. Not a complete listing discovery crawler.
- WF-02C eligibility: active, 2 nodes.
- WF-02E: active, 35 nodes. DLD sourceStatus SOURCE_UNAVAILABLE (API_KEY_PENDING), Property Monitor SOURCE_UNAVAILABLE (API_NOT_CONNECTED), Bayut exact-unit path not connected and explicitly treats Golf Heights comparables as nonexact. Manual DXB path exists.
- WF-02E Normalize Evidence accepts dxbEvidence and normalizes sourceAdapter, matchStatus, matchConfidence, historyCoverage, sourcePropertyRecordId, checkedAt, latest sale/rent, saleAfterSource and rentAfterSource. Complete history/current owner must not be inferred from sample transaction data.

## Go/no-go
PASS for canonical project/market metrics and building sale/rent comparables.
PASS under previously tested human-authenticated browser G1 for page-attributed single-unit history; coverage unknown.
NOT AVAILABLE through current connector for exact-unit full history and per-listing discovery/deduplication.
Release 2 Step 1: VALIDATED WITH CAPABILITY LIMITS. Steps 3–5 remain open.
Do not attempt bulk paging to construct a dataset. Browser collection needs permission confirmation before unattended operation.
