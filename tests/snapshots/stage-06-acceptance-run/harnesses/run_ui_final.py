import run_ui_acceptance as b
from run_ui_acceptance import *
def buttons(e,o):
 p=e.page;o['matrix']=[]
 for kind in ['login','booking','room','confirm']:
  for fault in ['success','business','503','network','nonjson']:
   if p.locator('#login-form').count():
    if kind!='login':e.login('admin')
   elif kind=='login':p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for()
   if kind=='login':p.locator('[data-account=admin]').click();pattern='**/api/login';button=p.locator('#login-form [type=submit]');error=p.locator('#login-error')
   elif kind=='booking':
    e.nav('spaces');p.locator('[data-book-room]').first.click();f=p.locator('#booking-form')
    for k,v in {'title':'按钮矩阵'+fault,'date':'2030-04-20','start':'10:00','end':'11:00','attendees':'2'}.items():f.locator('[name='+k+']').fill(v)
    pattern='**/api/bookings';button=f.locator('[type=submit]');error=p.locator('#booking-error')
   elif kind=='room':
    e.nav('manage');p.locator('#add-room').click();f=p.locator('#room-form');f.locator('[name=name]').fill('按钮空间'+fault);f.locator('[name=location]').fill('保留位置');pattern='**/api/rooms';button=f.locator('[type=submit]');error=p.locator('#room-error')
   else:
    bid=create(e,day='2030-04-21',start='14:00',end='15:00',title='取消按钮'+fault);e.nav('bookings');p.locator(f'[data-cancel="{bid}"]').click();pattern='**/api/bookings/*/cancel';button=p.locator('#confirm-cancel');error=p.locator('#confirm-error')
   held=[];p.route(pattern,lambda r:held.append(r));button.click();p.wait_for_timeout(100);assert len(held)==1 and button.is_disabled();p.keyboard.press('Enter');p.wait_for_timeout(70);assert len(held)==1
   if fault=='success':held[0].continue_()
   elif fault=='network':held[0].abort()
   elif fault=='nonjson':held[0].fulfill(status=200,body='not json',content_type='text/plain')
   else:held[0].fulfill(status=409 if fault=='business' else 503,body='{"error":"受控拒绝"}',content_type='application/json')
   p.unroute(pattern);p.wait_for_timeout(150)
   rec={'operation':kind,'fault':fault,'scope':'UI error display only for synthetic responses; success actual server','held_requests':1,'disabled':True}
   if fault!='success':
    assert error.inner_text();assert not button.is_disabled();rec['error']=error.inner_text();rec['screenshot']=e.shot(kind+'-'+fault)
    if kind=='booking':assert f.locator('[name=title]').input_value()=='按钮矩阵'+fault
    if kind=='room':assert f.locator('[name=location]').input_value()=='保留位置'
    button.click()
   if kind=='login':p.locator('#filter-date').wait_for()
   else:p.locator('#'+kind+'-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading')
   rec['completed_after_retry']=True;rec['toast']=p.locator('#toast').inner_text();o['matrix'].append(rec)
   if kind=='booking':
    bookings=e.api('/bookings')[1]['bookings'];created=next(x for x in bookings if x['title']=='按钮矩阵'+fault);e.api('/bookings/'+str(created['id'])+'/cancel','POST',{})

def timezone(e,o):
 e.login();create(e,start='08:00',end='08:15',title='早场');create(e,start='19:00',end='20:00',title='晚场');o['matrix']=[]
 for moment in ['2030-04-10T09:00:00+08:00','2030-04-10T23:59:59+08:00','2030-04-11T00:00:00+08:00']:
  baseline=None
  for tz in ['UTC','Asia/Shanghai','America/Los_Angeles']:
   ctx=b.browser.new_context(storage_state=e.ctx.storage_state(),timezone_id=tz);p=ctx.new_page();p.clock.set_fixed_time(real_dt.fromisoformat(moment));p.goto(e.url);p.locator('#filter-date').wait_for();default=p.locator('#filter-date').input_value();assert default==moment[:10];p.locator('#filter-date').fill('2030-04-12');p.locator('#filter-date').dispatch_event('change');p.wait_for_function('() => !state.loading');p.locator('.room-card summary').first.click();agenda=p.locator('.room-agenda').first.inner_text();p.locator('nav [data-page=bookings]').click();p.wait_for_function('() => !state.loading');booking=p.locator('.booking-row').all_inner_texts();p.locator('[data-cancel]').first.click();confirm=p.locator('#confirm-copy').inner_text();p.keyboard.press('Escape');p.locator('nav [data-page=inbox]').click();p.wait_for_function('() => !state.loading');notice=p.locator('.notice-row').all_inner_texts();record={'default':default,'agenda':agenda,'booking':booking,'confirm':confirm,'notice':notice};assert '08:00–08:15' in agenda and '19:00–20:00' in agenda
   if baseline is not None:assert record==baseline
   baseline=record;o['matrix'].append({'moment':moment,'tz':tz,**record});ctx.close()

def privacy(e,o):
 e.login();a=create(e,title='陈悦私有主题');p=e.page;alice=e.ctx.storage_state();p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();e.login('bob');create(e,start='12:00',end='13:00',title='周言私有主题');create(e,day='2030-04-13',title='次日主题');p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();o['matrix']=[]
 for who in ['admin','alice','bob']:
  e.login(who)
  for day in ['2030-04-12','2030-04-13']:
   p.locator('#filter-date').fill(day);p.locator('#filter-date').dispatch_event('change');p.wait_for_function('() => !state.loading');card=p.locator('.room-card').filter(has=p.locator('[data-book-room="1"]'));card.locator('summary').click();text=card.locator('details').inner_text();assert '陈悦私有主题' in text if who in ['admin','alice'] and day=='2030-04-12' else True
   if who=='bob' and day=='2030-04-12':assert '陈悦私有主题' not in text and '已预约' in text
   if who=='alice':assert '周言私有主题' not in text and '次日主题' not in text
   card.locator('summary').click();card.locator('summary').click();assert card.locator('details').inner_text()==text;o['matrix'].append({'who':who,'day':day,'text':text,'shot':e.shot(who+day)})
  p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for()

def keyboard(e,o):
 p=e.page;o['keys']=[]
 def reach(selector):
  for i in range(70):
   if p.locator(selector).evaluate('(el)=>el===document.activeElement'):break
   p.keyboard.press('Tab')
  else:raise AssertionError('键盘无法到达 '+selector)
  style=p.locator(selector).evaluate('(el)=>({outline:getComputedStyle(el).outline,shadow:getComputedStyle(el).boxShadow})');o['keys'].append({'target':selector,'focus':style})
 reach('#login-form [name=email]');p.keyboard.type('admin@meetspace.test');p.keyboard.press('Tab');p.keyboard.type('MeetSpace!2026');p.keyboard.press('Enter');p.locator('#filter-date').wait_for();reach('[data-book-room="1"]');p.keyboard.press('Enter');assert p.locator('#booking-dialog').is_visible();reach('#booking-form [name=title]');p.keyboard.type('键盘预约');reach('#booking-form [name=date]');p.keyboard.press('ArrowUp');# Date field keyboard locale unpredictable; retain default valid today.
 reach('#booking-form [type=submit]');p.keyboard.press('Enter');p.wait_for_timeout(150)
 if p.locator('#booking-dialog').is_visible():o['date_keyboard_error']=p.locator('#booking-error').inner_text();p.keyboard.press('Escape')
 else:p.wait_for_function('() => !state.loading');o['saved']=True
 reach('nav [data-page=manage]');p.keyboard.press('Enter');p.locator('#add-room').wait_for();reach('#add-room');p.keyboard.press('Enter');reach('#room-form [name=name]');p.keyboard.type('键盘会议室');reach('#room-form [name=location]');p.keyboard.type('键盘位置');reach('#room-form [type=submit]');p.keyboard.press('Enter');p.locator('#room-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');o['labels']=p.locator('input,select,button').evaluate_all('(es)=>es.map(e=>({tag:e.tagName,aria:e.getAttribute("aria-label"),labels:Array.from(e.labels||[]).map(x=>x.textContent),text:e.textContent}))');o['accessibility']=p.locator('body').aria_snapshot();assert p.locator('#toast').get_attribute('role')=='status'

def logout(e,o):
 e.login();p=e.page;o['matrix']=[]
 for fault in ['503','network']:
  pattern='**/api/logout';p.route(pattern,lambda r:r.abort() if fault=='network' else r.fulfill(status=503,content_type='application/json',body='{"error":"退出受控失败"}'));button=p.locator('[data-logout]:visible').first;button.click();p.wait_for_function('() => document.querySelector("#toast").textContent.length>0');assert not button.is_disabled();assert e.api('/session')[0]==200;o['matrix'].append({'fault':fault,'toast':p.locator('#toast').inner_text(),'session_valid':True});p.unroute(pattern)
 old=e.ctx.storage_state();p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();oldctx=b.browser.new_context(storage_state=old);assert oldctx.request.get(e.url+'/api/session').status==401;oldctx.close();assert not p.locator('dialog[open]').count();o['real_logout_old_session_rejected']=True

def sort(e,o):
 e.login('admin');p=e.page
 for day,start,title in [('2030-04-14','14:00','晚创建先'),('2030-04-12','10:00','早创建后'),('2030-04-13','12:00','中间')]:create(e,day=day,start=start,end=f'{int(start[:2])+1:02}:00',title=title)
 o['matrix']=[]
 for moment in ['2030-04-10T09:00:00+08:00','2030-04-12T11:00:00+08:00','2030-04-15T09:00:00+08:00']:
  p.clock.set_fixed_time(real_dt.fromisoformat(moment));e.nav('bookings');actual=p.locator('.list-panel').evaluate_all('(es)=>es.map(e=>Array.from(e.querySelectorAll("h3")).map(h=>h.textContent))');records=e.api('/bookings')[1]['bookings'];now=real_dt.fromisoformat(moment);up=sorted([x for x in records if x['status']=='confirmed' and real_dt.fromisoformat(x['end'])>now],key=lambda x:x['start']);history=sorted([x for x in records if x['status']=='cancelled' or real_dt.fromisoformat(x['end'])<=now],key=lambda x:x['start'],reverse=True);assert actual==[[x['title'] for x in up],[x['title'] for x in history]];o['matrix'].append({'moment':moment,'actual':actual,'shot':e.shot(moment[11:13])})

if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=300
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True)
  group('submit-button-fault-matrix',['AI-interface-experience-7','AI-interface-experience-9','AI-interface-experience-8','AI-WB-ui-submit-button-matrix'],buttons)
  group('timezone-full-views',['AI-interface-experience-15','AI-WB-ui-timezone-format'],timezone,True)
  group('agenda-privacy',['AI-room-discovery-6'],privacy,True)
  group('keyboard-only',['AI-interface-experience-13','AI-WB-ui-accessibility-focus'],keyboard)
  group('logout-failure-recovery',['AI-WB-ui-logout-races'],logout)
  group('booking-group-sort',['AI-reservation-management-4','AI-WB-ui-booking-status-sort'],sort)
  b.browser.close()
