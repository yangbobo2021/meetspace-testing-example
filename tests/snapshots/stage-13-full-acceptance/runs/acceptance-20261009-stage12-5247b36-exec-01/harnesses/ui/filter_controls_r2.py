import json
import run_ui_acceptance as b
from run_ui_acceptance import *
def matrix(e,o):
 e.login('admin');p=e.page;equipment=['显示屏','白板','视频会议','电话会议']
 for cap in [3,4,5,6,7,8,9,11,12,13]:
  assert e.api('/rooms','POST',{'name':'控件边界'+str(cap),'location':'真实筛选','capacity':cap,'equipment':[equipment[cap%4],equipment[(cap+1)%4]],'active':True})[0]==201
 assert e.api('/rooms','POST',{'name':'停用容量20','location':'不可预约','capacity':20,'equipment':equipment,'active':False})[0]==201
 rooms=e.api('/rooms')[1]['rooms'];o['room_properties']=rooms;e.nav('spaces');opts=p.locator('#filter-capacity option').evaluate_all('(es)=>es.map(e=>({value:e.value,label:e.textContent}))');o['options']=opts;assert [x['value'] for x in opts]==['','4','6','8','12'];labels={x['value']:x['label'] for x in opts};initial=[x for x in p.locator('.stat-value').all_inner_texts()];o['steps']=[];before=e.snap()
 def choose(cap,eq):
  p.locator('#filter-capacity').select_option(label=labels[cap]);p.locator('#filter-equipment').select_option(label=eq if eq else '全部设备')
  actual=sorted(map(int,p.locator('[data-book-room]').evaluate_all('(es)=>es.map(e=>e.dataset.bookRoom)')));expected=sorted(r['id'] for r in rooms if r['active'] and (not cap or r['capacity']>=int(cap)) and (not eq or eq in r['equipment']));state=p.evaluate('({capacity:state.capacity,equipment:state.equipment})');selected=p.locator('#filter-capacity option:checked').inner_text();assert actual==expected and selected==labels[cap] and str(state['capacity'])==cap and state['equipment']==eq,(actual,expected,state);assert p.locator('.stat-value').all_inner_texts()==initial;o['steps'].append({'capacity':cap,'equipment':eq,'selected_label':selected,'state':state,'actual':actual,'expected':expected})
 for cap in labels:
  for eq in ['']+equipment:choose(cap,eq)
 for prior in ['','4','8']:choose(prior,'');choose('6','');assert all(r['id'] not in o['steps'][-1]['actual'] for r in rooms if r['capacity'] in [4,5]);assert all(r['id'] in o['steps'][-1]['actual'] for r in rooms if r['active'] and r['capacity'] in [6,8])
 choose('8','白板');choose('8','');choose('','');choose('8','白板');choose('','白板');choose('','');assert e.snap()==before;o['full_matrix_shot']=e.shot('full-controls')
 # Separate zero match baseline via real admin edit, leaving real 4-seat match and inactive high match.
 for r in rooms:
  if r['active'] and r['capacity']>=12:assert e.api('/rooms/'+str(r['id']),'PATCH',{**r,'equipment':[x for x in r['equipment'] if x!='电话会议']})[0]==200
 r=next(r for r in rooms if r['capacity']==4 and r['active']);assert e.api('/rooms/'+str(r['id']),'PATCH',{**r,'equipment':['电话会议']})[0]==200
 p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();e.login('alice');rooms=e.api('/rooms')[1]['rooms'];initial=p.locator('.stat-value').all_inner_texts();choose('12','电话会议');assert not p.locator('[data-book-room]').count();assert p.locator('#filter-capacity').is_enabled() and p.locator('#filter-equipment').is_enabled();o['zero_text']=p.locator('.content').inner_text();o['zero_shot']=e.shot('zero');choose('','电话会议');assert r['id'] in o['steps'][-1]['actual'];choose('','');o['recovered_shot']=e.shot('recovered')
if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=1600
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True);group('native-filter-labels-and-orders',['AI-room-discovery-5','AI-room-discovery-9','AI-WB-ui-filters-statistics'],matrix,True);b.browser.close()
