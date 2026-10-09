import run_ui_acceptance as b
from run_ui_acceptance import *
def genuine_conflict(e,o):
 e.login();p=e.page;create(e);p.locator('[data-book-room="1"]').click();f=p.locator('#booking-form');vals={'title':'保留输入冲突','date':'2030-04-12','start':'10:00','end':'11:00','attendees':'2'}
 for k,v in vals.items():f.locator('[name='+k+']').fill(v)
 before=e.snap();f.locator('[type=submit]').click();p.wait_for_function('() => document.querySelector("#booking-error").textContent.length>0');assert e.snap()==before;actual={k:f.locator('[name='+k+']').input_value() for k in vals};assert actual==vals;o['real_error']=p.locator('#booking-error').inner_text();o['retained']=actual;o['shot']=e.shot('real-conflict');f.locator('[name=start]').fill('12:00');f.locator('[name=end]').fill('13:00');f.locator('[type=submit]').click();p.locator('#booking-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');assert any(x['title']=='保留输入冲突' for x in e.api('/bookings')[1]['bookings']);o['retry_toast']=p.locator('#toast').inner_text()

def notices_failure(e,o):
 e.login('bob');p=e.page;create(e);e.nav('inbox');o['matrix']=[]
 for fault in ['503','network']:
  held=[];p.route('**/api/notifications/read',lambda r:held.append(r));p.locator('#mark-read').click();p.wait_for_timeout(50);assert p.locator('#mark-read').is_disabled() and len(held)==1
  if fault=='network':held[0].abort()
  else:held[0].fulfill(status=503,content_type='application/json',body='{"error":"标已读受控失败"}')
  p.unroute('**/api/notifications/read');p.wait_for_function('() => !document.querySelector("#mark-read").disabled');assert p.locator('.nav-badge').inner_text()=='1';assert e.api('/notifications')[1]['notifications'][0]['read']==False;o['matrix'].append({'fault':fault,'badge':'1','toast':p.locator('#toast').inner_text()})
 p.locator('#mark-read').click();p.wait_for_function('() => !state.loading && !document.querySelector(".nav-badge")');assert p.locator('#mark-read').is_disabled();o['real_read_success']=True

def timeline_manage(e,o):
 e.login('admin');p=e.page;room=e.api('/rooms')[1]['rooms'][0];a=create(e,room=room['id'],start='08:00',end='08:15');e.api('/rooms/'+str(room['id']),'PATCH',{**room,'active':False,'equipment':[]});e.nav('manage');card=p.locator('.room-card').filter(has=p.locator(f'[data-edit-room="{room["id"]}"]'));assert '基础会议空间' in card.inner_text();assert '已停用' in card.inner_text();card.locator('[data-edit-room]').click();assert not p.locator('#room-form [name=active]').is_checked();p.keyboard.press('Escape');e.nav('spaces');assert p.locator(f'[data-book-room="{room["id"]}"]').count()==0;o['disabled_editable_spaces_hidden']=True
 # Verify full admin team booking view and canCancel state at exact boundaries.
 e.nav('bookings');p.locator('[data-scope=team]').click();p.wait_for_function('() => !state.loading');o['team_before']=p.locator('.booking-row').all_inner_texts();p.clock.set_fixed_time(real_dt.fromisoformat('2030-04-12T08:00:00+08:00'));p.locator('[data-refresh]').click();p.wait_for_function('() => !state.loading');row=p.locator('.booking-row').filter(has=p.get_by_role('heading',name='API合成预约',exact=True));assert row.locator('.status-pill').inner_text()=='进行中';assert not row.locator('[data-cancel]').count();o['team_at_start']=row.inner_text()

def role_failures(e,o):
 e.login('admin');p=e.page;e.nav('manage');members=e.api('/members')[1]['members'];target=next(x['id'] for x in members if x['email']=='bob@meetspace.test');o['matrix']=[]
 for fault in ['session','reload']:
  pattern='**/api/session' if fault=='session' else '**/api/rooms*';p.route(pattern,lambda r:r.fulfill(status=503,content_type='application/json',body='{"error":"角色更新后受控失败"}'));p.locator(f'[data-member="{target}"]').select_option('admin' if fault=='session' else 'member');p.wait_for_timeout(150);text=p.locator('body').inner_text();assert '角色更新后受控失败' in text;o['matrix'].append({'fault':fault,'text':text,'shot':e.shot(fault)});p.unroute(pattern);p.reload();p.locator('#filter-date').wait_for();e.nav('manage')

def api_errors(e,o):
 p=e.page;p.locator('[data-account=alice]').click();p.locator('#login-form [name=password]').fill('wrong-public-fixture');p.locator('#login-form [type=submit]').click();p.wait_for_function('() => document.querySelector("#login-error").textContent.length>0');assert p.locator('#login-form').count();o['wrong_password']=p.locator('#login-error').inner_text();e.login();p.locator('[data-book-room]').first.click();f=p.locator('#booking-form');f.locator('[name=title]').fill('默认错误');p.route('**/api/bookings',lambda r:r.fulfill(status=503,content_type='application/json',body='{}'));f.locator('[type=submit]').click();p.wait_for_function('() => document.querySelector("#booking-error").textContent.length>0');assert p.locator('#booking-error').inner_text()=='请求失败，请稍后重试';o['default_error']=p.locator('#booking-error').inner_text();p.unroute('**/api/bookings')

if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=600
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True)
  group('real-booking-conflict-retry',['AI-interface-experience-9'],genuine_conflict)
  group('notification-mark-read-failure',['AI-WB-ui-notification-render'],notices_failure)
  group('manage-disabled-room-and-team-status',['AI-WB-ui-room-timeline-agenda','AI-WB-ui-booking-status-sort'],timeline_manage)
  group('role-post-success-load-errors',['AI-WB-ui-role-demotion-reload'],role_failures)
  group('api-default-error-and-wrong-password',['AI-WB-ui-api-error-session-transition'],api_errors)
  b.browser.close()
