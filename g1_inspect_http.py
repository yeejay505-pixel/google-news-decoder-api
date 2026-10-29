"""Isolated, authenticated-through-nginx, on-demand G1 read-only inspection endpoint."""
import asyncio
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs
from g1_unit_queue import read_cached
from g1_wf02e_preview import handoff_preview
from g1_live_unit_batch import create_batch, status as batch_status, record_observation
from g1_unit_history_adapter import inspect_open_tab
from g1_evidence_store import persist, persist_review

class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  route=urlsplit(self.path).path
  if route not in ("/batch-create","/batch-capture"):
   self.send_error(404); return
  try:
   count=int(self.headers.get("Content-Length","0"))
   if count<2 or count>4096: raise ValueError("INVALID_REQUEST_SIZE")
   obj=json.loads(self.rfile.read(count))
   if route=="/batch-create":
    response=create_batch(obj.get("building"),obj.get("units"))
   else:
    bid=obj.get("batch_id")
    previous=batch_status(bid)
    if previous.get("status")=="NOT_FOUND":raise ValueError("UNKNOWN_BATCH")
    unit=previous.get("next_unit")
    if not unit:response={"status":"COMPLETE","batch":previous}
    else:
     inspected=asyncio.run(inspect_open_tab(previous["building"],unit))
     ev=inspected.get("event_certification",{})
     review=inspected.get("review_record",{})
     if ev.get("status")=="VERIFIED":
      inspected["persistence"]=persist(ev)
     elif review.get("status")=="CONFLICT_REQUIRES_REVIEW":
      inspected["review_persistence"]=persist_review(review)
     receipt=record_observation(bid,unit,inspected)
     response={"unit":unit,"receipt":receipt,"batch":batch_status(bid)}
  except Exception as exc:
   response={"status":"HOLD","reason":"BATCH_OPERATION_FAILED","error_type":type(exc).__name__}
  self.send_json(response)
 def send_json(self,obj):
  blob=json.dumps(obj,sort_keys=True).encode()
  self.send_response(200)
  self.send_header("Content-Type","application/json")
  self.send_header("Cache-Control","no-store")
  self.send_header("Content-Length",str(len(blob)))
  self.end_headers()
  self.wfile.write(blob)

 def do_GET(self):
  route=urlsplit(self.path)
  if route.path=="/batch-operator":
   blob="<!doctype html><html lang=\"en\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>G1 Two-Unit Batch</title><style>body{font:16px system-ui,sans-serif;max-width:620px;margin:48px auto;padding:0 20px}button{font:inherit;padding:14px 18px;cursor:pointer;margin:8px 8px 8px 0}pre{background:#f4f4f4;white-space:pre-wrap;overflow-wrap:anywhere;padding:16px}p{line-height:1.5}</style><h2>Release 2 — Golf Heights 901 → 902</h2><p>Keep the DXBinteract Property History → All tab open in the secure browser. Do not change units until the queue says 902 is next.</p><button onclick=\"start()\">1. Initialize 901 → 902</button><button onclick=\"capture()\">2. Capture current unit</button><p id=\"message\">No batch initialized yet.</p><pre id=\"output\"></pre><script>let batchId;const message=document.querySelector('#message'),output=document.querySelector('#output');async function call(route,payload){const response=await fetch(route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!response.ok)throw Error('HTTP '+response.status);return response.json()}function render(x){output.textContent=JSON.stringify(x,null,2);const b=x.batch||x;batchId=b.batch_id||batchId;message.textContent=x.receipt?.accepted===false?'HOLD: '+x.receipt.reason:b.next_unit?'Next unit: '+b.next_unit:b.state==='COMPLETE'?'Batch complete':x.reason||'Review result';}async function start(){try{render(await call('/g1-batch-create',{building:'Golf Heights',units:['901','902']}))}catch(e){message.textContent=e.message}}async function capture(){if(!batchId){message.textContent='Initialize the batch first';return}try{render(await call('/g1-batch-capture',{batch_id:batchId}))}catch(e){message.textContent=e.message}}</script></html>".encode()
   self.send_response(200)
   self.send_header("Content-Type","text/html; charset=utf-8")
   self.send_header("Cache-Control","no-store")
   self.send_header("Content-Length",str(len(blob)))
   self.end_headers()
   self.wfile.write(blob)
   return
  if route.path not in ("/inspect","/cache","/handoff-preview","/batch-status"):
   self.send_error(404); return
  params=parse_qs(route.query)
  building=params.get("building",[""])[0]
  unit=params.get("unit",[""])[0]
  if route.path=="/inspect" and not building and not unit:
   building,unit="Lamtara 1","401" # legacy test endpoint only
  try:
   if route.path!="/batch-status" and (not building or not unit): raise ValueError("EXPLICIT_BUILDING_AND_UNIT_REQUIRED")
   result=batch_status(params.get("batch_id",[""])[0]) if route.path=="/batch-status" else read_cached(building,unit) if route.path=="/cache" else handoff_preview(building,unit) if route.path=="/handoff-preview" else asyncio.run(inspect_open_tab(building,unit))
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
