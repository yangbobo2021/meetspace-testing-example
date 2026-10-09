import run_ui_acceptance as b
from run_ui_acceptance import *
def state_paths(e,o):
 p=e.page;n=len(e.requests);p.evaluate('() => loadPage()');p.wait_for_timeout(50);assert len(e.requests)==n;o['load_without_user_network']=0;o['switches']=[]
 for target in ['alice','other']:
  e.login('admin');e.nav('bookings');p.locator('[data-scope=team]').click();p.wait_for_function('() => !state.loading');assert p.evaluate('() => state.scope')=='team';p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for();e.login(target);state=p.evaluate('() => ({page:state.page,scope:state.scope,user:state.user.email,rooms:state.rooms.map(x=>x.name),members:state.members})');assert state['scope']=='mine' and state['page']=='spaces' and state['user']==target+'@meetspace.test';assert state['members']==[]
  if target=='other':assert '云杉' not in state['rooms']
  o['switches'].append({**state,'shot':e.shot(target)});p.locator('[data-logout]:visible').first.click();p.locator('#login-form').wait_for()

def tie_sort(e,o):
 e.login('admin');p=e.page;a=create(e,room=1,title='同起点一');c=create(e,room=2,title='同起点二');o['matrix']=[]
 for scope in ['mine','team']:
  e.nav('bookings');p.locator('[data-scope='+scope+']').click();p.wait_for_function('() => !state.loading');titles=p.locator('.booking-row h3').all_inner_texts();assert '同起点一' in titles and '同起点二' in titles;o['matrix'].append({'scope':scope,'titles':titles,'shot':e.shot(scope)})
 e.api('/bookings/'+str(a)+'/cancel','POST',{});p.clock.set_fixed_time(real_dt.fromisoformat('2030-04-12T11:00:00+08:00'));p.locator('[data-refresh]').click();p.wait_for_function('() => !state.loading');o['ended_cancelled']=p.locator('.booking-row').all_inner_texts();assert p.locator('[data-cancel]').count()==0
if __name__=='__main__':
 data=json.load(open(RUN/'ui-results.json'));b.results={r['method_id']:{k:v for k,v in r.items() if k!='method_id'} for r in data['method_results']};b.groups=json.load(open(E/'progress.json'))['groups'];b.serial=950
 with sync_playwright() as pw:
  b.browser=pw.chromium.launch(headless=True);group('login-team-scope-and-no-user-load',['AI-WB-ui-login-navigation','AI-interface-experience-1','AI-WB-ui-load-parallel-error'],state_paths);group('same-start-admin-scope-status',['AI-WB-ui-booking-status-sort'],tie_sort);b.browser.close()
