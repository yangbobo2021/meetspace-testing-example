import run_ui_acceptance as b
from run_ui_acceptance import *
def statistics(e,o):
 e.login('admin');p=e.page;c,d=e.api('/rooms','POST',{'name':'第五室','location':'统计','capacity':8,'equipment':[],'active':True});assert c==201;rooms=e.api('/rooms')[1]['rooms'];
 for rr in rooms:
  if rr['active'] and rr['capacity']>=12:assert e.api('/rooms/'+str(rr['id']),'PATCH',{**rr,'equipment':[eq for eq in rr['equipment'] if eq!='电话会议']})[0]==200
 rid=next(r['id'] for r in rooms if r['name']=='第五室');p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();e.login();create(e);create(e,room=2);x=create(e,room=3);e.api('/bookings/'+str(x)+'/cancel','POST',{});create(e,day='2030-04-13');p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();e.login('bob');create(e,room=rid);p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();e.login('admin');r=next(r for r in rooms if r['id']==rid);assert e.api('/rooms/'+str(rid),'PATCH',{**r,'active':False})[0]==200;p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();e.login();o['normal']=[];capture_number=0
 def read(day,expected):
  nonlocal capture_number
  capture_number+=1
  e.nav('spaces');p.locator('#filter-date').fill(day);p.locator('#filter-date').dispatch_event('change');p.wait_for_function('() => !state.loading');actual=[int(''.join(x for x in t if x.isdigit())) for t in p.locator('.stat-value').all_inner_texts()];assert actual==expected,(actual,expected)
  p.locator('#filter-capacity').select_option('12');p.locator('#filter-equipment').select_option('电话会议');assert p.locator('[data-book-room]').count()==0;zero_shot=e.shot('zero-'+str(capture_number)+'-'+day);filtered=[int(''.join(x for x in t if x.isdigit())) for t in p.locator('.stat-value').all_inner_texts()];assert filtered==expected;p.locator('#filter-capacity').select_option('');p.locator('#filter-equipment').select_option('');return {'date':day,'stats':actual,'filtered':filtered,'identity':e.api('/session')[1]['user']['email'],'zero_matches':0,'zero_shot':zero_shot,'shot':e.shot('restored-'+str(capture_number)+'-'+day)}
 o['normal']=[read('2030-04-12',[4,3,2]),read('2030-04-13',[4,1,1])]
 # Shut down HTTP before preparing legacy cross-midnight records, preserving real schema/FKs.
 e.server.shutdown();e.server.server_close()
 with sqlite3.connect(e.db) as db:
  users={x[1]:x[0] for x in db.execute('select id,email from users')};uid=users['alice@meetspace.test'];vid=users['bob@meetspace.test'];bid=users['other@meetspace.test'];db.execute('delete from notifications');db.execute('delete from bookings');rows=[]
  for name,owner,room,start,end,status,team in [('H1',uid,1,'2030-04-11T23:45','2030-04-12T00:15','confirmed',1),('H2',uid,1,'2030-04-12T19:45','2030-04-13T00:15','confirmed',1),('H3',vid,rid,'2030-04-12T10:00','2030-04-12T11:00','confirmed',1),('H4',uid,2,'2030-04-11T23:45','2030-04-12T00:00','confirmed',1),('H5',uid,2,'2030-04-13T00:00','2030-04-13T00:15','confirmed',1),('H6',uid,3,'2030-04-12T12:00','2030-04-12T13:00','cancelled',1),('OTHER',bid,5,'2030-04-12T10:00','2030-04-12T11:00','confirmed',2)]:
   start=real_dt.fromisoformat(start+':00+08:00').astimezone(datetime.timezone.utc).isoformat();end=real_dt.fromisoformat(end+':00+08:00').astimezone(datetime.timezone.utc).isoformat();db.execute('insert into bookings(team_id,room_id,user_id,title,start,end,attendees,status,created_at,idempotency_key,request_hash) values(?,?,?,?,?,?,?,?,?,?,?)',(team,room,owner,name,start,end,2,status,FIX.isoformat(),name,'legacy-synthetic'));rows.append({'name':name,'user':owner,'room':room,'team':team,'start':start,'end':end,'status':status})
  db.commit();o['integrity']=db.execute('pragma integrity_check').fetchall();o['foreign_keys']=db.execute('pragma foreign_key_check').fetchall();assert o['integrity']==[('ok',)] and not o['foreign_keys']
 e.server=srv.ApplicationServer(('127.0.0.1',int(e.url.rsplit(':',1)[1])),srv.Store(e.db));threading.Thread(target=e.server.serve_forever,daemon=True).start();o['legacy_rows']=rows;o['legacy']=[read('2030-04-11',[4,2,2]),read('2030-04-12',[4,3,1]),read('2030-04-13',[4,2,1])]
 for who,expected in [('bob',[4,3,1]),('other',[1,1,1])]:
  p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();e.login(who);o['legacy'].append({'who':who,**read('2030-04-12',expected)})

def logout_retry(e,o):
 e.login();p=e.page;o['matrix']=[]
 for fault in ['503','network']:
  held=[];p.route('**/api/logout',lambda r:held.append(r));button=p.locator('[data-logout]:visible').first;button.click();p.wait_for_timeout(50);assert button.is_disabled() and len(held)==1
  if fault=='503':held[0].fulfill(status=503,content_type='application/json',body='{"error":"退出受控失败"}')
  else:held[0].abort()
  p.wait_for_function('() => !Array.from(document.querySelectorAll("[data-logout]")).find(e=>e.offsetParent!==null).disabled');assert e.api('/session')[0]==200;o['matrix'].append({'fault':fault,'toast':p.locator('#toast').inner_text(),'session_valid':True});p.unroute('**/api/logout')
 old=e.ctx.storage_state();p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();oldctx=b.browser.new_context(storage_state=old);assert oldctx.request.get(e.url+'/api/session').status==401;oldctx.close();o['old_session_401']=True

def keyboard_cancel(e,o):
 e.login();p=e.page;bid=create(e);e.nav('bookings');o['keys']=[]
 def reach(sel):
  for _ in range(80):
   if p.locator(sel).evaluate('(e)=>e===document.activeElement'):return
   p.keyboard.press('Tab')
  raise AssertionError(sel)
 reach(f'[data-cancel="{bid}"]');p.keyboard.press('Enter');assert p.locator('#confirm-dialog').is_visible();o['dialog_accessibility']=p.locator('#confirm-dialog').aria_snapshot();reach('#confirm-cancel');p.keyboard.press('Enter');p.locator('#confirm-dialog').wait_for(state='hidden');p.wait_for_function('() => !state.loading');assert next(x for x in e.api('/bookings')[1]['bookings'] if x['id']==bid)['status']=='cancelled';reach('nav [data-page=inbox]');p.keyboard.press('Enter');p.locator('#mark-read').wait_for();reach('#mark-read');p.keyboard.press('Enter');p.wait_for_function('() => !state.loading');o['accessibility']=p.locator('body').aria_snapshot()

def loading_more(e,o):
 e.login('admin');p=e.page;create(e);o['matrix']=[]
 for fault in ['network','500']:
  p.route('**/api/rooms*',lambda r:r.abort() if fault=='network' else r.fulfill(status=500,content_type='application/json',body='{"error":"受控500"}'));e.nav('bookings');assert p.locator('.retry-panel').count();o['matrix'].append({'fault':fault,'text':p.locator('.retry-panel').inner_text()});p.unroute('**/api/rooms*');p.locator('[data-refresh]').click();p.wait_for_function('() => !state.loading');assert p.locator('.booking-row').count()>0
 held=[];p.route('**/api/rooms*',lambda r:held.append(r));p.locator('nav [data-page=manage]').click();p.wait_for_timeout(80);assert '正在同步工作空间' in p.locator('.content').inner_text();assert not p.locator('.member-row').count();held[0].continue_();p.unroute('**/api/rooms*');p.wait_for_function('() => !state.loading');assert p.locator('.member-row').count();o['held_one_request_no_partial_render']=True

def dialogs_two_rooms(e,o):
 e.login();p=e.page;o['rooms']=[]
 rooms=e.api('/rooms')[1]['rooms']
 for room in [x for x in rooms if x['active']][:2]:
  p.locator(f'[data-book-room="{room["id"]}"]').click();assert p.locator('#booking-title').inner_text()=='预约 '+room['name'];assert room['location'] in p.locator('#booking-subtitle').inner_text();assert str(room['capacity']) in p.locator('#booking-subtitle').inner_text();assert p.locator('#booking-form [name=attendees]').get_attribute('max')==str(room['capacity'])
  for name in ['title','date','start','end','attendees']:p.locator('#booking-form [name='+name+']').focus();assert p.locator('#booking-form [name='+name+']').is_visible()
  o['rooms'].append({'id':room['id'],'title':p.locator('#booking-title').inner_text(),'subtitle':p.locator('#booking-subtitle').inner_text(),'rule':p.locator('#booking-form .form-note').inner_text(),'shot':e.shot(str(room['id']))});p.keyboard.press('Escape')

if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=400
 # Previous assertion was a demonstrable harness synchronization race, retained and explicitly classified, not an application failure.
 prior=b.results['AI-WB-ui-logout-races'];prior['status']='unproven';prior['actual']='305 首次网络分支复用了上一toast，未等待返回就检查disabled；该失败是harness同步问题，保留原证据并重跑。'
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True)
  group('statistics-midnight-fixture',['AI-room-discovery-8','AI-WB-ui-filters-statistics'],statistics)
  group('logout-full-retry',['AI-WB-ui-logout-races'],logout_retry)
  group('keyboard-cancel-notices',['AI-interface-experience-13','AI-WB-ui-accessibility-focus'],keyboard_cancel)
  group('load-network-wait-recovery',['AI-interface-experience-4','AI-WB-ui-load-parallel-error'],loading_more)
  group('two-room-dialog-details',['AI-interface-experience-5'],dialogs_two_rooms,True)
  b.browser.close()
