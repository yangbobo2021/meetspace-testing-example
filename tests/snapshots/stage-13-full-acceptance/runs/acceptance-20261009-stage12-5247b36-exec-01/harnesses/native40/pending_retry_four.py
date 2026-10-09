import asyncio,json,os,traceback
from pathlib import Path
OUT=Path(__file__).resolve().parents[2]/'evidence/pending-retry-four';OUT.mkdir(exist_ok=True);os.environ['MEETSPACE_COVERAGE_AUDIT']=str(OUT)
import identity_env as h
from playwright.async_api import async_playwright
async def one(e,target,fault):
 await e.nav('manage');count=0
 async def intercept(r):
  nonlocal count
  count+=1
  if count==1:await r.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'INITIAL_PENDING'}))
  elif count==2:
   if fault=='503':await r.fulfill(status=503,content_type='application/json',body=json.dumps({'error':'RETRY_PENDING_503'}))
   else:await r.abort('failed')
  else:await r.continue_()
 await e.p.route('**/api/session',intercept);await e.p.locator(f'[data-member="{target}"]').select_option('member' if target==1 else 'admin');await e.p.wait_for_function('() => state.identityPending && !state.loading && state.loadError === "INITIAL_PENDING"');baseline=e.snapshot();idx=len(e.events);await e.p.locator('[data-refresh]').click();await e.p.wait_for_function('() => state.identityPending && !state.loading && !!state.loadError && state.loadError !== "INITIAL_PENDING"');o=await e.observe();ev=e.events[idx:];role='member' if target==1 else 'admin';e.check('重试再失败保持待确认身份及当前错误零业务预取',o['user']['role']==role and o['retry'] and o['loadError']!='INITIAL_PENDING' and not o['loading'] and o['toast']!='成员角色已更新' and baseline==e.snapshot() and not any(x.get('event')=='request' and any(v in x.get('path','') for v in ['/api/rooms','/api/bookings','/api/notifications','/api/members']) for x in ev),{'UI':o,'events':ev});await e.shot('retry-failed');idx=len(e.events);await e.p.locator('[data-refresh]').click();await e.p.wait_for_function('() => !state.identityPending && !state.loading && !state.loadError && !!state.user');o=await e.observe();ev=e.events[idx:];e.check('真实session恢复按member/admin加载且提交不回滚',count==3 and o['user']['role']==role and not o['loadError'] and o['manage']==(target==2) and o['page']==('spaces' if target==1 else 'manage') and baseline==e.snapshot() and any(x.get('path')=='/api/session' for x in ev) and any(x.get('path')=='/api/members' for x in ev)==(target==2),{'UI':o,'events':ev});await e.shot('recovered')
async def main():
 rows=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for target in [1,2]:
   for fault in ['503','network']:
    name=f'pending-target-{target}-retry-{fault}';e=h.Env();o={'name':name,'status':'unproven','revision':h.REV}
    try:
     await e.start(browser,name,'admin',True);await one(e,target,fault);o['status']='passed' if all(x['passed'] for x in e.checks) else 'failed'
    except Exception as ex:o.update(error=str(ex),traceback=traceback.format_exc())
    finally:
     o.update(checks=e.checks,events=e.events,screenshots=e.shots);(OUT/(name+'.json')).write_text(json.dumps(o,ensure_ascii=False,indent=2));rows.append({'name':name,'status':o['status'],'evidence':name+'.json'});(OUT/'results.json').write_text(json.dumps({'results':rows},indent=2));print(name,o['status'],o.get('error',''));await e.close()
  await browser.close()
asyncio.run(main())
