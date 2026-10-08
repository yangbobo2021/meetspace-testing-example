"""Independent native UI completion check for normal self demotion."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

HERE=Path(__file__).resolve().parent
os.environ['MEETSPACE_COVERAGE_AUDIT']=str(HERE/'reviewer-normal-demotion')
spec=importlib.util.spec_from_file_location('reviewer_demotion_tools',HERE/'dev-ui-identity-corrected/execute_ui_identity.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  e=h.Env()
  try:
   await e.start(browser,'normal-completed','admin',True)
   await e.nav('manage')
   responses_before=len(e.responses)
   await e.p.locator('[data-member="1"]').select_option('member')
   await e.p.wait_for_function('() => state.user?.role === "member" && state.page === "spaces" && !state.loading && !state.identityPending && !document.querySelector("nav [data-page=manage]") && document.querySelector("#toast").textContent === "成员角色已更新"')
   obs=await e.observe()
   seen=e.responses[responses_before:]
   e.check('真实PATCH及session响应先于完成的member界面',any(x['method']=='PATCH' and x['path']=='/api/members/1' and x['status']==200 for x in seen) and any(x['path']=='/api/session' and x['status']==200 for x in seen) and e.roles()[0][-1]=='member' and not obs['manage'] and obs['user']['role']=='member' and obs['scope']=='mine' and not obs['loadError'],{'UI':obs,'roles':e.roles(),'responses':seen})
   status,body,_=h.req(e.url,'/api/members',cookie=await e.cookie())
   e.check('同一真实session管理员API已拒绝',status==403,{'status':status,'body':body})
   await e.shot('completed')
   evidence={'scope':'independent development regression, not formal all-scenario acceptance','source_sha256':h.HASHES,'browser':browser.version,'checks':e.checks,'events':e.events,'responses':e.responses,'screenshots':e.shots,'status':'passed' if all(c['passed'] for c in e.checks) else 'failed'}
   (HERE/'reviewer-normal-demotion.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
   print(evidence['status'])
  finally:
   await e.close();await browser.close()

asyncio.run(main())
