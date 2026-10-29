"""Isolated, authenticated-through-nginx, on-demand G1 read-only inspection endpoint."""
import asyncio
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from g1_unit_history_adapter import inspect_open_tab

class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path != "/inspect":
   self.send_error(404); return
  try: result=asyncio.run(inspect_open_tab())
  except Exception as exc: result={"status":"HOLD","reason":"Inspection error","error_type":type(exc).__name__}
  blob=json.dumps(result,sort_keys=True).encode()
  self.send_response(200)
  self.send_header("Content-Type","application/json")
  self.send_header("Cache-Control","no-store")
  self.send_header("Content-Length",str(len(blob)))
  self.end_headers()
  self.wfile.write(blob)
 def log_message(self,*args): pass
HTTPServer(("127.0.0.1",8769),Handler).serve_forever()
