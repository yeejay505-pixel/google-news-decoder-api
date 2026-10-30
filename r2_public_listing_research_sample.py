"""Bounded PUBLIC-RESEARCH sample for source fitness, NOT an authorized listings feed.
Observed on Property Finder Golf Heights sale result page, 2026-10-30.
Research IDs are INTERNAL placeholders, not portal listing identifiers.
No individual apartment numbers, exact listing IDs, original publication times or ingestion rights.
"""
from r2_listing_opportunity_engine import analyze
INDEX_URL="https://www.propertyfinder.ae/en/buy/dubai/properties-for-sale-the-views-golf-heights.html"
OBSERVATIONS=[
 {"source":"propertyfinder-public-research","source_listing_id":"RESEARCH-001",
  "source_url":INDEX_URL,"authorization":"UNCONFIRMED","kind":"sale",
  "building":"Golf Heights","unit_identity_verified":False,
  "bedrooms":1,"size_sqft":758,"asking_aed":1950000,
  "first_seen":None,"agent_ref":"RESEARCH_AGENT_A"},
 {"source":"propertyfinder-public-research","source_listing_id":"RESEARCH-002",
  "source_url":INDEX_URL,"authorization":"UNCONFIRMED","kind":"sale",
  "building":"Golf Heights","unit_identity_verified":False,
  "bedrooms":1,"size_sqft":756,"asking_aed":1800000,
  "first_seen":None,"agent_ref":"RESEARCH_AGENT_A"},
 {"source":"propertyfinder-public-research","source_listing_id":"RESEARCH-003",
  "source_url":INDEX_URL,"authorization":"UNCONFIRMED","kind":"sale",
  "building":"Golf Heights","unit_identity_verified":False,
  "bedrooms":1,"size_sqft":758,"asking_aed":1790000,
  "first_seen":None,"agent_ref":"RESEARCH_AGENT_B"}
]
MARKET={"source":"DXBINTERACT_MATRIX","observed_at":"2026-10-30",
 "sample_count":2,"benchmark_price_sqft":2229.39}
def research_sample():
 return analyze(OBSERVATIONS,MARKET,as_of="2026-10-30")
