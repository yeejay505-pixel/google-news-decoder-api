from pathlib import Path
import os, sqlite3, json
base=Path('/data/openbrowser-pool')
prof=base/'profiles/dxb-poc'
slot=base/'config/pool-a.env'
print('G1_CONTINUITY_PATH',str(prof),flush=True)
print('G1_CONTINUITY_PROFILE_EXISTS',prof.is_dir(),flush=True)
print('G1_CONTINUITY_PROFILE_MARKERS',json.dumps({x:(prof/x).exists() for x in ('Local State','Default/Cookies','Default/Network/Cookies','Default/Preferences','SingletonLock')}),flush=True)
print('G1_CONTINUITY_SLOT_CONFIG',slot.read_text()[:350] if slot.exists() else 'ABSENT',flush=True)
for db in ('Default/Network/Cookies','Default/Cookies'):
 p=prof/db
 if p.exists():
  try:
   con=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True,timeout=2)
   n=con.execute('select count(*) from cookies').fetchone()[0]
   domain=con.execute("select count(*) from cookies where host_key like '%dxbinteract.com'").fetchone()[0]
   con.close()
   print('G1_CONTINUITY_COOKIE_COUNTS',json.dumps({'total':n,'dxb_domain':domain}),flush=True)
  except Exception as e: print('G1_CONTINUITY_COOKIE_DB_UNAVAILABLE',type(e).__name__,flush=True)
print('G1_CONTINUITY_INSPECTION_COMPLETE',flush=True)
