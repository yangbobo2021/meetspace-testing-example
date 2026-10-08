import json,sys
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
url=sys.argv[1]; out=Path(sys.argv[2]); external=[]; devices=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    for width,height,touch in [(1280,900,False),(390,844,True)]:
        ctx=browser.new_context(viewport={'width':width,'height':height},has_touch=touch,is_mobile=touch,timezone_id='Asia/Shanghai')
        page=ctx.new_page(); errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:external.append(r.url) if urlsplit(r.url).netloc!=urlsplit(url).netloc and r.url.startswith('http') else None)
        page.goto(url); page.get_by_role('heading',name='欢迎回来').wait_for()
        page.get_by_role('button',name='陈悦 · 成员').click()
        page.get_by_role('button',name='登录工作空间').click()
        page.locator('#login-form').wait_for(state='detached')
        page.get_by_text('云杉',exact=True).first.wait_for()
        capability=page.evaluate('({secureContext:isSecureContext,randomUUID:typeof crypto.randomUUID,viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth})')
        assert capability['randomUUID']=='function' and not errors
        screenshot=f'browser-{width}.png'; page.screenshot(path=str(out/screenshot),full_page=True)
        devices.append({'viewport':[width,height],'touch_emulation':touch,'capabilities':capability,'page_errors':errors,'screenshot':screenshot})
        ctx.close()
    version=browser.version; browser.close()
assert not external
(out/'browser.json').write_text(json.dumps({'browser_version':version,'devices':devices,'external_requests':external},ensure_ascii=False,indent=2))
