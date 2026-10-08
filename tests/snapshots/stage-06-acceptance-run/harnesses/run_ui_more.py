import run_ui_acceptance as b
from run_ui_acceptance import *
def filters(e,o):
 e.login('admin');p=e.page;eq=['显示屏','白板','视频会议','电话会议'];o['matrix']=[]
 for n in [3,4,5,6,7,8,9,11,12,13]:
  c,d=e.api('/rooms','POST',{'name':'筛选室'+str(n),'location':'边界容量','capacity':n,'equipment':[eq[n%4],eq[(n+1)%4]],'active':True});assert c==201
 c,d=e.api('/rooms','POST',{'name':'停用大室','location':'停用','capacity':20,'equipment':eq,'active':False});assert c==201
 rooms=e.api('/rooms')[1]['rooms'];e.nav('spaces')
 for cap in ['','4','6','8','12']:
  for equip in ['']+eq:
   p.locator('#filter-capacity').select_option(cap);p.locator('#filter-equipment').select_option(equip);actual=sorted(int(x) for x in p.locator('[data-book-room]').evaluate_all('(els)=>els.map(e=>e.dataset.bookRoom)'));expected=sorted(x['id'] for x in rooms if x['active'] and (not cap or x['capacity']>=int(cap)) and (not equip or equip in x['equipment']));assert actual==expected;o['matrix'].append({'capacity':cap,'equipment':equip,'actual':actual,'expected':expected,'stats':p.locator('.stat-value').all_inner_texts()})
 for prev in ['','4','8']:
  p.locator('#filter-equipment').select_option('');p.locator('#filter-capacity').select_option(prev);p.locator('#filter-capacity').select_option('6');assert all('4 人' not in x and '5 人' not in x for x in p.locator('.room-info').all_inner_texts())
 for r in rooms:
  if r['active'] and r['capacity']>=12:
   c,d=e.api('/rooms/'+str(r['id']),'PATCH',{**r,'equipment':[x for x in r['equipment'] if x!='电话会议']});assert c==200
 e.nav('spaces');p.locator('#filter-capacity').select_option('12');p.locator('#filter-equipment').select_option('电话会议');assert p.locator('[data-book-room]').count()==0;assert '没有符合条件' in p.locator('.rooms-grid').inner_text();o['empty_shot']=e.shot('empty');p.locator('#filter-capacity').select_option('');assert p.locator('[data-book-room]').count()>0;p.locator('#filter-equipment').select_option('');assert p.locator('[data-book-room]').count()==sum(x['active'] for x in rooms);o['rooms']=rooms

def timeline(e,o):
 e.login();p=e.page;ids=[]
 for start,end in [('08:00','08:15'),('10:00','10:30'),('10:30','10:45'),('19:45','20:00')]:ids.append(create(e,start=start,end=end))
 def inspect(day,expected):
  e.nav('spaces');p.locator('#filter-date').fill(day);p.locator('#filter-date').dispatch_event('change');p.wait_for_function('() => !state.loading');card=p.locator('.room-card').filter(has=p.locator('[data-book-room="1"]'));slots=card.locator('.timeline span').evaluate_all('(els)=>els.map((e,i)=>e.classList.contains("occupied")?i:-1).filter(x=>x>=0)');assert card.locator('.timeline span').count()==48;assert slots==expected
  if card.locator('summary').count():card.locator('summary').click();assert card.locator('details').get_attribute('open') is not None
  return {'day':day,'occupied':slots,'agenda':card.inner_text(),'shot':e.shot(day+'-'+str(len(expected)))}
 o['before_cancel']=inspect('2030-04-12',[0,8,9,10,47]);assert e.api('/bookings/'+str(ids[1])+'/cancel','POST',{})[0]==200;o['after_cancel']=inspect('2030-04-12',[0,10,47]);o['empty']=inspect('2030-04-13',[])

def booking_status(e,o):
 e.login();p=e.page;a=create(e,start='10:00',end='11:00',title='有效边界');c=create(e,room=2,start='10:00',end='11:00',title='取消边界');e.api('/bookings/'+str(c)+'/cancel','POST',{});o['matrix']=[]
 for hh,expected in [('09:59:59','已确认'),('10:00:00','进行中'),('10:59:59','进行中'),('11:00:00','已结束'),('11:00:01','已结束')]:
  p.clock.set_fixed_time(real_dt.fromisoformat('2030-04-12T'+hh+'+08:00'));e.nav('bookings');row=p.locator('.booking-row').filter(has=p.get_by_role('heading',name='有效边界',exact=True));cancel=p.locator('.booking-row').filter(has=p.get_by_role('heading',name='取消边界',exact=True));assert row.locator('.status-pill').inner_text()==expected;assert cancel.locator('.status-pill').inner_text()=='已取消';assert row.locator('[data-cancel]').count()==(hh<'10:00:00');o['matrix'].append({'time':hh,'confirmed_status':row.locator('.status-pill').inner_text(),'cancelled_status':cancel.locator('.status-pill').inner_text(),'shot':e.shot(hh.replace(':',''))})
 p.clock.set_fixed_time(FIX);e.nav('bookings');p.locator(f'[data-cancel="{a}"]').click();assert all(x in p.locator('#confirm-copy').inner_text() for x in ['有效边界','10:00','云杉']);p.get_by_role('button',name='保留预约').click();assert next(x for x in e.api('/bookings')[1]['bookings'] if x['id']==a)['status']=='confirmed';p.locator(f'[data-cancel="{a}"]').click();p.locator('#confirm-cancel').click();p.locator('#confirm-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');assert next(x for x in e.api('/bookings')[1]['bookings'] if x['id']==a)['status']=='cancelled'

def notices(e,o):
 e.login('bob');p=e.page;e.nav('inbox');assert '暂时没有新消息' in p.locator('.content').inner_text();assert p.locator('.nav-badge').count()==0
 a=create(e,title='通知完整正文');e.nav('inbox');assert p.locator('.nav-badge').inner_text()=='1';o['created']=p.locator('.notice-row').all_inner_texts();e.api('/bookings/'+str(a)+'/cancel','POST',{});e.nav('inbox');assert p.locator('.nav-badge').inner_text()=='2';o['cancelled']=p.locator('.notice-row').all_inner_texts();assert all('#'+str(a) in x and '04/10 09:00' in x for x in o['cancelled']);p.locator('#mark-read').click();p.wait_for_function('() => !state.loading && document.querySelectorAll(".nav-badge").length===0');assert p.locator('#mark-read').is_disabled();assert p.locator('.notice-row').all_inner_texts()==o['cancelled']
 o['timezones']=[]
 for tz in ['UTC','Asia/Shanghai','America/Los_Angeles']:
  ctx=b.browser.new_context(storage_state=e.ctx.storage_state(),timezone_id=tz);q=ctx.new_page();q.clock.set_fixed_time(FIX);q.goto(e.url);q.locator('#filter-date').wait_for();q.locator('nav [data-page=inbox]').click();q.wait_for_function('() => !state.loading');texts=q.locator('.notice-row').all_inner_texts();assert texts==o['cancelled'];o['timezones'].append({'tz':tz,'notices':texts});ctx.close()

def expire(e,o):
 e.login('admin');p=e.page;create(e);o['branches']=[]
 for kind in ['booking','room','confirm','load']:
  if kind=='room':e.nav('manage');p.locator('#add-room').click();p.locator('#room-form [name=name]').fill('过期不保存');p.locator('#room-form [name=location]').fill('位置')
  elif kind=='confirm':e.nav('bookings');p.locator('[data-cancel]').first.click()
  else:e.nav('spaces');p.locator('[data-book-room]').first.click();p.locator('#booking-form [name=title]').fill('过期预约')
  before=e.snap()
  with sqlite3.connect(e.db) as c:c.execute('delete from sessions');c.commit()
  if kind=='load':e.page.keyboard.press('Escape');p.locator('nav [data-page=bookings]').click()
  elif kind=='confirm':p.locator('#confirm-cancel').click()
  else:p.locator('#'+kind+'-form [type=submit]').click()
  p.locator('#login-form').wait_for();assert p.locator('dialog[open]').count()==0;assert e.snap()==before;o['branches'].append({'kind':kind,'login':True,'open_dialogs':0,'business_unchanged':True,'shot':e.shot(kind)});e.login('admin')

def escaping(e,o):
 e.login('admin');p=e.page;payload='<img src=x onerror="window.__bb=1">';p.evaluate('() => {window.__bb=0}')
 code,data=e.api('/rooms','POST',{'name':payload,'location':payload,'capacity':8,'equipment':[],'active':True});assert code==201;room=data['room']['id'] if 'room' in data else data['id'];a=create(e,room=room,title=payload);o['sinks']=[]
 for page in ['spaces','bookings','inbox','manage']:
  e.nav(page)
  if page=='spaces':p.locator('#filter-date').fill('2030-04-12');p.locator('#filter-date').dispatch_event('change');p.wait_for_function('() => !state.loading');p.locator('.room-card').filter(has=p.locator(f'[data-book-room="{room}"]')).locator('summary').click()
  assert payload in p.locator('.content').inner_text();assert p.locator('img[src=x],script:not([src]),[onerror]').count()==0;assert p.evaluate('() => window.__bb')==0;o['sinks'].append({'page':page,'text':p.locator('.content').inner_text(),'shot':e.shot(page)})
 e.nav('bookings');p.locator(f'[data-cancel="{a}"]').click();assert payload in p.locator('#confirm-copy').inner_text();p.locator('#confirm-cancel').click();p.locator('#confirm-dialog').wait_for(state='hidden');e.nav('inbox');assert payload in p.locator('.notice-row').first.inner_text()

def draft(e,o):
 e.login();p=e.page;o['branches']=[]
 for field in ['same','whitespace','title','date','start','end','attendees']:
  e.nav('spaces');p.locator('[data-book-room]').first.click();f=p.locator('#booking-form')
  for k,v in {'title':'丢响应'+field,'date':'2030-04-15','start':'10:00','end':'11:00','attendees':'2'}.items():f.locator('[name='+k+']').fill(v)
  captured=[]
  def drop(r):captured.append(r.request.post_data_json);r.abort()
  p.route('**/api/bookings',drop);f.locator('[type=submit]').click();p.wait_for_function('() => document.querySelector("#booking-error").textContent.length>0');first=f.locator('[name=title]').input_value()
  if field=='whitespace':f.locator('[name=title]').fill(' '+first+' ')
  elif field!='same':f.locator('[name='+field+']').fill({'title':'更改主题','date':'2030-04-16','start':'10:15','end':'11:15','attendees':'3'}[field])
  f.locator('[type=submit]').click();p.wait_for_function('() => !document.querySelector("#booking-form [type=submit]").disabled');assert len(captured)==2;equal=captured[0]['idempotency_key']==captured[1]['idempotency_key'];assert equal==(field in ['same','whitespace']);o['branches'].append({'change':field,'key_equal':equal,'error':p.locator('#booking-error').inner_text(),'persisted_count':len(e.api('/bookings')[1]['bookings'])});p.unroute('**/api/bookings');p.keyboard.press('Escape')
 # Real commit, response loss, unchanged UI retry.
 e.nav('spaces');p.locator('[data-book-room]').first.click();f=p.locator('#booking-form')
 for k,v in {'title':'已提交响应丢失','date':'2030-04-16','start':'14:00','end':'15:00','attendees':'2'}.items():f.locator('[name='+k+']').fill(v)
 captured=[]
 def lose(r):captured.append(r.request.post_data_json);resp=r.fetch();assert resp.status==201;r.abort()
 p.route('**/api/bookings',lose);f.locator('[type=submit]').click();p.wait_for_function('() => document.querySelector("#booking-error").textContent.length>0');before=e.snap();p.unroute('**/api/bookings');f.locator('[type=submit]').click();p.locator('#booking-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');assert e.snap()==before;o['committed_response_loss']={'before':before,'after':e.snap(),'toast':p.locator('#toast').inner_text()}

if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=200
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True)
  group('filters-all-controls',['AI-room-discovery-5','AI-room-discovery-9','AI-WB-ui-filters-statistics'],filters)
  group('timeline-boundaries',['AI-room-discovery-7','AI-WB-ui-room-timeline-agenda'],timeline)
  group('status-exact-boundaries',['AI-reservation-management-3','AI-reservation-management-10','AI-WB-ui-booking-status-sort'],booking_status)
  group('notifications-render-timezones',['AI-notification-center-7','AI-WB-ui-notification-render'],notices)
  group('real-session-expiry-dialogs',['AI-interface-experience-10','AI-WB-ui-api-error-session-transition'],expire)
  group('stored-text-escaping',['AI-interface-experience-14','AI-WB-ui-text-escaping'],escaping)
  group('booking-draft-retry',['AI-interface-experience-16','AI-WB-ui-booking-draft-key'],draft,True)
  b.browser.close()
