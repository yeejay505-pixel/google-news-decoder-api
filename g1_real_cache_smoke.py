"""G1 safe startup cache probe; no browser or site access."""
from g1_unit_queue import read_cached
from g1_wf02e_preview import handoff_preview
for building,unit in (("Golf Heights","901"),("Lamtara 1","401")):
 try:
  record=read_cached(building,unit)
  preview=handoff_preview(building,unit)
  print("G1_REAL_CACHE_PROBE",{"building":building,"unit":unit,
        "cache_status":record["status"],"cache_source":record.get("source"),
        "event_count":len(record.get("evidence",record.get("review",{})).get("events",[])),
        "handoff_status":preview["status"],"writes":preview["writes"]},flush=True)
 except Exception as exc:
  print("G1_REAL_CACHE_PROBE_ERROR",{"building":building,"unit":unit,"error_type":type(exc).__name__},flush=True)
