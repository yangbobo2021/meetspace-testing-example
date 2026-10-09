import sys,json,datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
base=sys.argv[1];out=Path(sys.argv[2]);results=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for account,uid in [('admin',1),('alice',2),('bob',3),('other',4)]:
  c=b.new_context(timezone_id='Asia/Shanghai');page=c.new_page();page.clock.install(time=datetime.datetime.fromisoformat('2030-04-10T09:00:00+08:00'));page.goto(base);page.locator('#login-form').wait_for();page.locator('input[name=email]').fill(account+'@meetspace.test');page.locator('input[name=password]').fill('MeetSpace!2026');page.get_by_role('button',name='登录工作空间').click();page.locator('#login-form').wait_for(state='detached');page.wait_for_timeout(200);r=page.evaluate("fetch('/api/session').then(r=>r.json())");assert r['user']['id']==uid;page.reload();page.locator('#login-form').wait_for(state='detached');page.screenshot(path=str(out/('ui-'+account+'.png')),full_page=True);cookies=c.cookies();assert all(x['httpOnly'] and x['sameSite']=='Lax' and x['path']=='/' for x in cookies);assert 'meetspace_session' not in page.evaluate('document.cookie');results.append({'account':account,'identity':r,'cookie_attributes_valid':True,'reload_authenticated':True});c.close()
 results.append({'browser_version':b.version});b.close()
(out/'ui-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print('Four real UI logins, reloads, identity and cookie attributes passed')
