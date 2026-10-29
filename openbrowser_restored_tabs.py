import json,urllib.request,asyncio
from playwright.async_api import async_playwright
async def main():
 try:
  with urllib.request.urlopen("http://127.0.0.1:9223/json/list",timeout=7) as r:tabs=json.load(r)
  print("G1_RESTORED_TABS",json.dumps([{"url_host":t.get("url","").split("/")[2] if "://" in t.get("url","") else t.get("url","")[:35],"title":t.get("title","")[:90]} for t in tabs if t.get("type")=="page"])[:800],flush=True)
  async with async_playwright() as p:
   b=await p.chromium.connect_over_cdp("http://127.0.0.1:9223")
   contexts=b.contexts
   pages=contexts[0].pages if contexts else []
   print("G1_RESTORED_PAGE_COUNT",len(pages),flush=True)
   for page in pages[:3]:
    print("G1_RESTORED_PAGE",json.dumps({"host":page.url.split("/")[2] if "://" in page.url else page.url,"title":(await page.title())[:110]}),flush=True)
   await b.close()
 except Exception as e:print("G1_RESTORED_INSPECT_ERROR",type(e).__name__,str(e)[:220],flush=True)
asyncio.run(main())
