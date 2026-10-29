"""Local WebGL2 capability check. Uses about:blank only; never visits DXBinteract."""
import asyncio,json
from playwright.async_api import async_playwright
async def main():
 try:
  async with async_playwright() as p:
   browser=await p.chromium.connect_over_cdp("http://127.0.0.1:9223",timeout=15000)
   context=browser.contexts[0]
   page=await context.new_page()
   try:
    result=await page.evaluate("""() => {
      const c=document.createElement('canvas');
      const gl=c.getContext('webgl2');
      return {webgl2:!!gl,renderer:gl?String(gl.getParameter(gl.RENDERER)).slice(0,100):null};
    }""")
    print("G1_WEBGL2_LOCAL_RESULT",json.dumps(result),flush=True)
   finally:
    await page.close()
    await browser.close()
 except Exception as exc:
  print("G1_WEBGL2_LOCAL_ERROR",type(exc).__name__,str(exc)[:140],flush=True)
asyncio.run(main())
