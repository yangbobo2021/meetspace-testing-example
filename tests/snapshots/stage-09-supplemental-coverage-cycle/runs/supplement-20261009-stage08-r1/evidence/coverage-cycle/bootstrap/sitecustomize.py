"""Coverage-only instrumentation of copied harnesses; no product or expectation changes."""
import os,sys,json,atexit
from pathlib import Path
if os.environ.get('COVERAGE_PROCESS_START'):
 if sys.version_info>=(3,14):os.environ['COVERAGE_CORE']='pytrace'
 import coverage
 coverage.process_startup()
base=Path(os.environ['MEETSPACE_COVERAGE_AUDIT'])
js={}; captures=0

def merge(value):
 global captures
 if not isinstance(value,dict):return
 captures+=1
 for name,cov in value.items():
  if name!='web/app.js':continue
  if name not in js:js[name]=cov;continue
  dest=js[name]
  for kind in ['s','f']:
   for k,v in cov[kind].items():dest[kind][k]=max(dest[kind].get(k,0),v)
  for k,values in cov['b'].items():dest['b'][k]=[max(a,b) for a,b in zip(dest['b'][k],values)]

def write_js():
 if js:
  d=base/'javascript-data';d.mkdir(exist_ok=True)
  (d/f'{os.environ.get("COVERAGE_AUDIT_JOB","child")}-{os.getpid()}.json').write_text(json.dumps({'coverage':js,'captures':captures,'counter_policy':'per-process max; presence coverage, not hit frequency'}))
atexit.register(write_js)
try:
 from playwright.sync_api import Page,BrowserContext,Browser
 def capture(page):
  try:
   if not page.is_closed():merge(page.evaluate('() => globalThis.__coverage__ || null'))
  except Exception:pass
 for name in ['goto','reload','close']:
  old=getattr(Page,name)
  def wrap(self,*args,_old=old,**kwargs):capture(self);return _old(self,*args,**kwargs)
  setattr(Page,name,wrap)
 old_context=BrowserContext.close
 def close_context(self,*a,**k):
  for page in self.pages:capture(page)
  return old_context(self,*a,**k)
 BrowserContext.close=close_context
 old_browser=Browser.close
 def close_browser(self,*a,**k):
  for context in self.contexts:
   for page in context.pages:capture(page)
  return old_browser(self,*a,**k)
 Browser.close=close_browser
except ImportError:pass
try:
 from playwright.async_api import Page as APage,BrowserContext as AContext,Browser as ABrowser
 async def acapture(page):
  try:
   if not page.is_closed():merge(await page.evaluate('() => globalThis.__coverage__ || null'))
  except Exception:pass
 for name in ['goto','reload','close']:
  old=getattr(APage,name)
  async def awrap(self,*a,_old=old,**k):await acapture(self);return await _old(self,*a,**k)
  setattr(APage,name,awrap)
 old_ac=AContext.close
 async def aclose(self,*a,**k):
  for p in self.pages:await acapture(p)
  return await old_ac(self,*a,**k)
 AContext.close=aclose
 old_ab=ABrowser.close
 async def abclose(self,*a,**k):
  for c in self.contexts:
   for p in c.pages:await acapture(p)
  return await old_ab(self,*a,**k)
 ABrowser.close=abclose
except ImportError:pass
