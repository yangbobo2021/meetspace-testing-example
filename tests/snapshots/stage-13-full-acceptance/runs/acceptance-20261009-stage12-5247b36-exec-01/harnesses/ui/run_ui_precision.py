import run_ui_acceptance as b
from run_ui_acceptance import *
def keyboard_full_error(e,o):
 p=e.page;o['sequence']=[]
 def reach(sel):
  for i in range(100):
   if p.locator(sel).evaluate('(e)=>e===document.activeElement'):o['sequence'].append(sel);return
   p.keyboard.press('Tab')
  raise AssertionError(sel)
 reach('#login-form [name=email]');p.keyboard.type('admin@meetspace.test');reach('#login-form [name=password]');p.keyboard.type('MeetSpace!2026');p.keyboard.press('Enter');p.locator('#filter-date').wait_for();reach('nav [data-page=manage]');p.keyboard.press('Enter');p.locator('#add-room').wait_for();reach('#add-room');p.keyboard.press('Enter');reach('#room-form [name=name]');p.keyboard.type('云杉');reach('#room-form [name=location]');p.keyboard.type('键盘位置');reach('#room-form [type=submit]');p.keyboard.press('Enter');p.wait_for_function('() => document.querySelector("#room-error").textContent.length>0');o['alert']=p.locator('#room-dialog').aria_snapshot();assert 'alert' in o['alert'];reach('#room-form [name=name]');p.keyboard.press('Meta+A');p.keyboard.type('键盘修正成功');reach('#room-form [type=submit]');p.keyboard.press('Enter');p.locator('#room-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');o['status']=p.locator('#toast').aria_snapshot();assert '会议室已保存' in o['status'];o['screenshot']=e.shot('keyboard-only-success')

def long_breakpoints(e,o):
 e.login('admin');p=e.page;name=('合法长中文空间'*6)[:40];location=('合法中文位置'*13)[:80];code,data=e.api('/rooms','POST',{'name':name,'location':location,'capacity':12,'active':True,'equipment':[]});assert code==201
 with sqlite3.connect(e.db) as c:c.execute('update users set email=? where email=?',('synthetic-long-'+('a'*55)+'@example.test','bob@meetspace.test'));c.commit()
 o['matrix']=[]
 for width in [375,390,599,600,601,849,850,851,1149,1150,1151,1440,1499,1500,1501]:
  p.set_viewport_size({'width':width,'height':900 if width>600 else 844});e.nav('manage');layout=p.evaluate('() => ({w:innerWidth,s:document.documentElement.scrollWidth})');assert layout['s']<=width;p.get_by_role('button',name='编辑'+name,exact=True).click();rect=p.locator('#room-dialog').bounding_box();assert rect['x']>=0 and rect['width']<=width;o['matrix'].append({'width':width,'layout':layout,'dialog':rect,'shot':e.shot(str(width))});p.keyboard.press('Escape')

def escaping_privacy(e,o):
 e.login('alice');p=e.page;payload='<img src=x onerror="window.__bb=1">';create(e,title=payload);p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();e.login('bob');p.locator('#filter-date').fill('2030-04-12');p.locator('#filter-date').dispatch_event('change');p.wait_for_function('() => !state.loading');p.locator('.room-card summary').first.click();assert payload not in p.locator('.room-agenda').inner_text();assert '已预约' in p.locator('.room-agenda').inner_text();o['private_agenda']=p.locator('.room-agenda').inner_text();p.locator('[data-book-room]').first.click();f=p.locator('#booking-form');f.locator('[name=title]').fill('错误展示');p.route('**/api/bookings',lambda r:r.fulfill(status=400,content_type='application/json',body=json.dumps({'error':payload})));f.locator('[type=submit]').click();p.wait_for_function('() => document.querySelector("#booking-error").textContent.length>0');assert p.locator('#booking-error').inner_text()==payload;assert not p.locator('img[src=x],[onerror]').count();o['error_payload']=p.locator('#booking-error').inner_text();p.unroute('**/api/bookings');p.keyboard.press('Escape');p.route('**/api/logout',lambda r:r.fulfill(status=503,content_type='application/json',body=json.dumps({'error':payload})));p.locator('[data-logout]:visible').first.click();p.wait_for_function('() => document.querySelector("#toast").textContent.length>0');assert p.locator('#toast').inner_text()==payload;assert not p.locator('img[src=x],[onerror]').count();o['toast_payload']=p.locator('#toast').inner_text();p.unroute('**/api/logout')

if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=700
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True)
  group('keyboard-only-real-error-correction',['AI-interface-experience-13','AI-WB-ui-accessibility-focus'],keyboard_full_error)
  group('long-content-all-breakpoints',['AI-WB-ui-responsive-breakpoints'],long_breakpoints)
  group('escape-private-agenda-error-toast',['AI-interface-experience-14','AI-WB-ui-text-escaping'],escaping_privacy)
  b.browser.close()
