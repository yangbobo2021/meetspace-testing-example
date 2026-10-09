import run_ui_acceptance as b
from run_ui_acceptance import *
def after_write_load_failure(e,o):
 e.login('admin');p=e.page;o['matrix']=[]
 for kind in ['booking','room','confirm']:
  if kind=='booking':
   e.nav('spaces');p.locator('[data-book-room]').first.click();f=p.locator('#booking-form')
   for k,v in {'title':'提交后加载失败','date':'2030-04-25','start':'10:00','end':'11:00','attendees':'2'}.items():f.locator('[name='+k+']').fill(v)
   button=f.locator('[type=submit]')
  elif kind=='room':e.nav('manage');p.locator('#add-room').click();f=p.locator('#room-form');f.locator('[name=name]').fill('提交后加载失败室');f.locator('[name=location]').fill('位置');button=f.locator('[type=submit]')
  else:e.nav('bookings');p.locator('[data-cancel]').first.click();button=p.locator('#confirm-cancel')
  def intercept(r):
   if r.request.method=='GET':r.fulfill(status=500,content_type='application/json',body='{"error":"保存后读取失败"}')
   else:r.continue_()
  p.route('**/api/rooms*',intercept);button.click();p.locator('#'+kind+'-dialog').wait_for(state='hidden');p.locator('.retry-panel').wait_for();assert '保存后读取失败' in p.locator('.retry-panel').inner_text();o['matrix'].append({'operation':kind,'error':p.locator('.retry-panel').inner_text(),'database':e.snap(),'shot':e.shot(kind)});p.unroute('**/api/rooms*');p.locator('[data-refresh]').click();p.wait_for_function('() => !state.loading');assert not p.locator('.retry-panel').count()

def draft_room_small(e,o):
 e.login('admin');p=e.page;c,d=e.api('/rooms','POST',{'name':'单人间','location':'小容量','capacity':1,'active':True,'equipment':[]});assert c==201;rid=d['room']['id'];e.nav('spaces');o['matrix']=[];keys=[]
 for room in [1,rid]:
  p.locator(f'[data-book-room="{room}"]').click();f=p.locator('#booking-form');assert f.locator('[name=attendees]').input_value()==('1' if room==rid else '2');assert f.locator('[name=attendees]').get_attribute('max')==('1' if room==rid else '8');f.locator('[name=title]').fill('新弹窗指纹');captured=[]
  def abort(r):captured.append(r.request.post_data_json);r.abort()
  p.route('**/api/bookings',abort);f.locator('[type=submit]').click();p.wait_for_function('() => document.querySelector("#booking-error").textContent.length>0');keys.append(captured[0]['idempotency_key']);o['matrix'].append({'room':room,'attendees':f.locator('[name=attendees]').input_value(),'max':f.locator('[name=attendees]').get_attribute('max')});p.unroute('**/api/bookings');p.keyboard.press('Escape')
 assert keys[0]!=keys[1];o['new_room_new_key']=True

def sort_more(e,o):
 e.login();p=e.page;ids=[]
 for day,start in [('2030-04-15','14:00'),('2030-04-13','12:00'),('2030-04-12','10:00'),('2030-04-14','13:00')]:ids.append(create(e,day=day,start=start,end=f'{int(start[:2])+1:02}:00',title=day))
 e.api('/bookings/'+str(ids[0])+'/cancel','POST',{});e.api('/bookings/'+str(ids[2])+'/cancel','POST',{});o['matrix']=[]
 for moment in ['2030-04-10T09:00:00+08:00','2030-04-13T13:00:00+08:00','2030-04-16T09:00:00+08:00']:
  p.clock.set_fixed_time(real_dt.fromisoformat(moment));e.nav('bookings');rs=e.api('/bookings')[1]['bookings'];now=real_dt.fromisoformat(moment);expected=[[x['title'] for x in sorted([x for x in rs if x['status']=='confirmed' and real_dt.fromisoformat(x['end'])>now],key=lambda x:x['start'])],[x['title'] for x in sorted([x for x in rs if x['status']=='cancelled' or real_dt.fromisoformat(x['end'])<=now],key=lambda x:x['start'],reverse=True)]];actual=p.locator('.list-panel').evaluate_all('(es)=>es.map(e=>Array.from(e.querySelectorAll("h3")).map(x=>x.textContent))');assert actual==expected;o['matrix'].append({'moment':moment,'expected':expected,'actual':actual,'shot':e.shot(moment[8:10])})

if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=800
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True)
  group('successful-write-followed-by-load-error',['AI-WB-ui-submit-button-matrix'],after_write_load_failure)
  group('small-room-and-new-draft',['AI-WB-ui-default-times','AI-WB-ui-booking-draft-key'],draft_room_small)
  group('cancelled-history-group-sort',['AI-reservation-management-4','AI-WB-ui-booking-status-sort'],sort_more)
  b.browser.close()
