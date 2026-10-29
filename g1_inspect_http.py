"""Isolated, authenticated-through-nginx, on-demand G1 read-only inspection endpoint."""
import asyncio
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs
from g1_unit_queue import read_cached
from g1_wf02e_preview import handoff_preview
from g1_unit_history_adapter import inspect_open_tab
from g1_evidence_store import persist, persist_review

class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  route=urlsplit(self.path)
  if route.path not in ("/inspect","/cache","/handoff-preview"):
   self.send_error(404); return
  params=parse_qs(route.query)
  building=params.get("building",[""])[0]
  unit=params.get("unit",[""])[0]
  if route.path=="/inspect" and not building and not unit:
   building,unit="Lamtara 1","401" # legacy test endpoint only
  try:
   if not building or not unit: raise ValueError("EXPLICIT_BUILDING_AND_UNIT_REQUIRED")
   result=read_cached(building,unit) if route.path=="/cache" else handoff_preview(building,unit) if route.path=="/handoff-preview" else asyncio.run(inspect_open_tab(building,unit))
  except Exception as exc: result={"status":"HOLD","reason":"Inspection error","error_type":type(exc).__name__}
  evidence=result.get("event_certification") if route.path=="/inspect" and isinstance(result,dict) else None
  if evidence and evidence.get("status")=="VERIFIED":
   try: result["persistence"]=persist(evidence)
   except Exception as exc: result["persistence"]={"stored":False,"error_type":type(exc).__name__}
  review=result.get("review_record") if route.path=="/inspect" and isinstance(result,dict) else None
  if review and review.get("status")=="CONFLICT_REQUIRES_REVIEW":
   try: result["review_persistence"]=persist_review(review)
   except Exception as exc: result["review_persistence"]={"stored":False,"error_type":type(exc).__name__}
  blob=json.dumps(result,sort_keys=True).encode()
  self.send_response(200)
  self.send_header("Content-Type","application/json")
  self.send_header("Cache-Control","no-store")
  self.send_header("Content-Length",str(len(blob)))
  self.end_headers()
  self.wfile.write(blob)
 def log_message(self,*args): pass
HTTPServer(("127.0.0.1",8769),Handler).serve_forever()
