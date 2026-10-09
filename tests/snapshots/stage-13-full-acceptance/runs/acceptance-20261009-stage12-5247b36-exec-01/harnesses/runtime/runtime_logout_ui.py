import sys,json,datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path(sys.argv[2]);rows=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);c=b.new_context();page=c.new_page();page.clock.install(time=datetime.datetime.fromisoformat('2030-04-10T09:00:00+08:00'));page.goto(sys.argv[1]);page.locator('[data-account=alice]').click();page.locator('#login-form button[type=submit]').click();page.locator('[data-logout]').first.wait_for();page.screenshot(path=str(out/('restart-ui-'+sys.argv[3]+'.png')),full_page=True);assert 'meetspace_session' not in page.evaluate('document.cookie');page.evaluate("history.pushState({},'', '/sub/path')");assert 'meetspace_session' not in page.evaluate('document.cookie');r=page.evaluate("fetch('/api/session').then(r=>r.json())");assert r['user']['id']==2;page.locator('[data-logout]').first.click();page.locator('#login-form').wait_for();assert not [x for x in c.cookies() if x['name']=='meetspace_session'];page.goto(sys.argv[1]);page.locator('#login-form').wait_for();page.screenshot(path=str(out/('logout-ui-'+sys.argv[3]+'.png')),full_page=True);rows.append({'subpath_authenticated':True,'httpOnly':True,'logout_cookie_removed':True,'reload_login':True});b.close()
(out/('ui-logout-'+sys.argv[3]+'.json')).write_text(json.dumps(rows));print('Real UI reload, subpath cookie, logout, reload login passed')
