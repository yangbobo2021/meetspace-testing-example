import run_ui_acceptance as b
from run_ui_acceptance import *
from run_ui_supplement import statistics

def edit_buttons(e,o):
 e.login('admin');p=e.page;o['matrix']=[]
 for fault in ['success','business','network','503','nonjson']:
  e.nav('manage');p.locator('[data-edit-room]').first.click();f=p.locator('#room-form');original=f.locator('[name=name]').input_value();f.locator('[name=location]').fill('编辑保留-'+fault);button=f.locator('[type=submit]');held=[];p.route('**/api/rooms/*',lambda r:held.append(r));button.click();p.wait_for_timeout(50);assert button.is_disabled() and len(held)==1;p.keyboard.press('Enter');assert len(held)==1
  if fault=='success':held[0].continue_()
  elif fault=='network':held[0].abort()
  elif fault=='nonjson':held[0].fulfill(status=200,body='bad')
  else:held[0].fulfill(status=409 if fault=='business' else 503,content_type='application/json',body='{"error":"编辑受控失败"}')
  p.unroute('**/api/rooms/*')
  if fault!='success':p.wait_for_function('() => !document.querySelector("#room-form [type=submit]").disabled');assert p.locator('#room-error').inner_text();assert f.locator('[name=location]').input_value()=='编辑保留-'+fault;o['matrix'].append({'fault':fault,'error':p.locator('#room-error').inner_text(),'shot':e.shot(fault)});button.click()
  p.locator('#room-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');assert next(x for x in e.api('/rooms')[1]['rooms'] if x['name']==original)['location']=='编辑保留-'+fault

def keyboard_error(e,o):
 e.login();p=e.page;e.nav('spaces');p.locator('[data-book-room]').first.click();f=p.locator('#booking-form');f.locator('[name=title]').fill('键盘失败后修改');f.locator('[name=date]').fill('2030-04-12');f.locator('[name=start]').fill('10:00');f.locator('[name=end]').fill('10:00');# keyboard submission hits server ordering rule
 f.locator('[type=submit]').focus();p.keyboard.press('Enter');p.wait_for_function('() => document.querySelector("#booking-error").textContent.length>0');o['alert_tree']=p.locator('#booking-dialog').aria_snapshot();assert 'alert' in o['alert_tree'];f.locator('[name=end]').focus();p.keyboard.press('ArrowUp');# use keys to set hour through select+type, browser-native time input
 f.locator('[name=end]').fill('11:00');f.locator('[type=submit]').focus();p.keyboard.press('Enter');p.locator('#booking-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');o['status_tree']=p.locator('#toast').aria_snapshot();assert '预约成功' in o['status_tree'];o['focus_after']=p.evaluate('() => document.activeElement.tagName')

def escaping_more(e,o):
 e.login('admin');p=e.page;payload="&<>\"'";long='<img src=x onerror="window.__bb=1">';o['sinks']=[]
 with sqlite3.connect(e.db) as db:db.execute('update users set name=? where team_id=1',(long,));db.execute('update teams set name=? where id=1',(payload+long,));db.commit()
 p.reload();p.locator('#filter-date').wait_for();assert long in p.locator('.profile-name').inner_text();assert payload+long in p.locator('.workspace').inner_text();e.nav('manage');assert long in p.locator('.member-info').first.inner_text();assert p.locator('[data-member]').first.get_attribute('aria-label')==long+'的角色';assert not p.locator('img[src=x],[onerror]').count();o['profile_member_team_dom']=p.locator('body').aria_snapshot();o['screenshot']=e.shot('profile-member-team')
 # Legitimate short text including all escape characters through room API.
 code,data=e.api('/rooms','POST',{'name':payload,'location':payload,'capacity':4,'active':True,'equipment':[]});assert code==201;e.nav('manage');edit=p.get_by_role('button',name='编辑'+payload,exact=True);assert edit.count()==1;edit.click();assert p.locator('#room-title').inner_text()=='编辑 '+payload;assert p.locator('#room-form [name=name]').input_value()==payload;o['room_attrs']=edit.get_attribute('aria-label');p.keyboard.press('Escape')

def narrow_complete(e,o):
 p=e.page;e.login('admin');long='长中文会议室名称'*5;long=long[:40];code,data=e.api('/rooms','POST',{'name':long,'location':'长中文位置'*15,'capacity':12,'equipment':['白板'],'active':True});assert code==201;rid=data['room']['id'];o['matrix']=[]
 for width,height in [(1440,900),(390,844),(320,740)]:
  p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();p.set_viewport_size({'width':width,'height':height});e.login('admin');p.locator('#filter-capacity').select_option('12');p.locator('#filter-equipment').select_option('白板');p.locator(f'[data-book-room="{rid}"]').click();f=p.locator('#booking-form');f.locator('[name=title]').fill('长标题中文'*19);f.locator('[name=date]').fill('2030-04-24');f.locator('[name=start]').fill('10:00');f.locator('[name=end]').fill('11:00');rect=p.locator('#booking-dialog').bounding_box();assert rect['width']<=width;f.locator('[type=submit]').click();p.locator('#booking-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');a=next(x for x in e.api('/bookings')[1]['bookings'] if x['room_id']==rid and x['status']=='confirmed');e.nav('bookings');p.locator(f'[data-cancel="{a["id"]}"]').click();p.locator('#confirm-cancel').click();p.locator('#confirm-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');e.nav('inbox');assert p.locator('.notice-row').count();layout=p.evaluate('() => ({width:innerWidth,height:innerHeight,scroll:document.documentElement.scrollWidth})');assert layout['scroll']<=width;o['matrix'].append({'width':width,'height':height,'layout':layout,'booking':a['id'],'text':p.locator('.notice-row').first.inner_text(),'screenshot':e.shot(str(width))})

def login_only(e,o):
 p=e.page;o['choices']=[]
 for who in ['admin','alice','bob','other']:
  p.locator(f'[data-account={who}]').click();assert p.locator('[name=email]').input_value()==who+'@meetspace.test';assert p.locator('[name=password]').input_value()=='MeetSpace!2026';assert not any(x['path']=='/api/login' for x in e.requests);assert e.api('/session')[0]==401;o['choices'].append(who)
 p.locator('#login-form [type=submit]').click();p.locator('#filter-date').wait_for();assert e.api('/session')[1]['user']['email']=='other@meetspace.test';o['final_identity']='other@meetspace.test'

if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=500
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True)
  group('statistics-full-corrected-harness',['AI-room-discovery-8','AI-WB-ui-filters-statistics'],statistics,True)
  group('edit-room-button-matrix',['AI-interface-experience-7','AI-WB-ui-submit-button-matrix'],edit_buttons)
  group('keyboard-alert-status',['AI-interface-experience-13','AI-WB-ui-accessibility-focus'],keyboard_error)
  group('escaping-user-team-attributes',['AI-interface-experience-14','AI-WB-ui-text-escaping'],escaping_more)
  group('three-viewport-long-content',['AI-interface-experience-12','AI-WB-ui-responsive-breakpoints'],narrow_complete,True)
  group('demo-choice-no-login',['AI-interface-experience-2','AI-WB-ui-login-navigation'],login_only,True)
  b.browser.close()
