import asyncio,json,traceback
import coverage_cycle_ui_identity as h
import pending_identity_guards as g
from playwright.async_api import async_playwright
E=h.AUDIT/'gap-completion';E.mkdir(exist_ok=True)
async def double401(e):
 held=[]
 async def hold(r):held.append(r)
 await e.p.route('**/api/rooms?*',hold);await e.p.route('**/api/bookings?*',hold)
 await e.p.locator('nav [data-page=bookings]').click();await g.arrived(held)
 for _ in range(500):
  if len(held)==2:break
  await asyncio.sleep(.01)
 assert len(held)==2;await e.invalidate('revocation');responses=[]
 for r in held:responses.append(await r.fetch())
 assert [r.status for r in responses]==[401,401];await held[0].fulfill(response=responses[0]);await e.p.locator('#login-form').wait_for();before=await e.observe();await held[1].fulfill(response=responses[1]);await e.p.wait_for_timeout(150);after=await e.observe();e.check('同世代第二真实401到达仍登录无旧空间',before==after and after['user'] is None and after['openDialogs']==0 and not await e.p.evaluate('state.identityPending'),{'before':before,'after':after,'real_statuses':[401,401]});await e.shot('double401');await e.p.unroute('**/api/rooms?*');await e.p.unroute('**/api/bookings?*');await e.login('admin')
async def pending(e,target):
 held=await g.patch_fault(e,target);idx=len(e.events);await e.p.locator('[data-refresh]').click();await g.arrived(held);before=e.events[idx:];o=await e.observe();e.check('pending先真实session且尚无业务读取',o['loading'] and not any(x.get('event')=='request' and any(p in x.get('path','') for p in ['/api/rooms','/api/bookings','/api/notifications','/api/members']) for x in before),{'events':before,'UI':o});r,resp=held[0];await r.fulfill(response=resp);await e.ready();later=e.events[idx:];o=await e.observe();hasmembers=any(x.get('event')=='request' and x.get('path')=='/api/members' for x in later);e.check('session确认后按真实member/admin完整读取',o['user']['role']==('member' if target==1 else 'admin') and hasmembers==(target!=1) and (target!=1 or (o['page']=='spaces' and o['scope']=='mine')) and not await e.p.evaluate('state.identityPending'),{'events':later,'UI':o});await e.shot('pending-resolved')
async def room(e,kind,fault):
 cookie=await e.cookie();st,data,_=h.req(e.url,'/api/rooms',cookie=cookie);assert st==200;orig=data['rooms'][0];orig.update({'equipment':['白板','电话会议'],'active':False,'capacity':7});assert h.req(e.url,'/api/rooms/1','PATCH',orig,cookie)[0]==200;await e.nav('manage')
 if kind=='edit':await e.p.locator('[data-edit-room="1"]').click()
 else:await e.p.locator('#add-room').click()
 f=e.p.locator('#room-form')
 async def values():return {'name':await f.locator('[name=name]').input_value(),'location':await f.locator('[name=location]').input_value(),'capacity':await f.locator('[name=capacity]').input_value(),'equipment':await f.locator('[name=equipment]:checked').evaluate_all('(es)=>es.map(e=>e.value).sort()'),'active':await f.locator('[name=active]').is_checked()}
 initial=await values();e.check('初始全字段/新增默认',initial=={'name':orig['name'],'location':orig['location'],'capacity':'7','equipment':sorted(orig['equipment']),'active':False} if kind=='edit' else initial['name']=='' and initial['location']=='' and initial['capacity']=='6' and initial['active'] is True and initial['equipment']==[],initial)
 await f.locator('[name=name]').fill('白桦' if fault=='business' else '新全字段空间-'+kind);await f.locator('[name=location]').fill('完整保留位置');await f.locator('[name=capacity]').fill('9');await f.locator('[name=active]').uncheck()
 for x in await f.locator('[name=equipment]').all():await x.uncheck()
 await f.locator('[value=显示屏]').check();await f.locator('[value=电话会议]').check();before=await values();dbbefore=e.snapshot();pattern='**/api/rooms/1' if kind=='edit' else '**/api/rooms'
 if fault=='network':await e.p.route(pattern,lambda r:r.abort('failed'))
 await f.locator('[type=submit]').click();await e.p.wait_for_function('() => document.querySelector("#room-error").textContent.length>0 && !document.querySelector("#room-form [type=submit]").disabled');after=await values();e.check('失败全部输入保留且业务不变',before==after and dbbefore==e.snapshot(),{'before':before,'after':after,'error':await e.p.locator('#room-error').inner_text()});await e.shot('retained')
 if fault=='network':await e.p.unroute(pattern)
 await f.locator('[name=name]').fill('合法恢复空间-'+kind+'-'+fault);final=await values();await f.locator('[type=submit]').click();await e.p.locator('#room-dialog').wait_for(state='hidden');await e.ready();st,d,_=h.req(e.url,'/api/rooms',cookie=await e.cookie());saved=next(r for r in d['rooms'] if r['name']==final['name']);e.check('恢复五字段完整保存且成功反馈',saved['location']==final['location'] and saved['capacity']==int(final['capacity']) and saved['active']==final['active'] and sorted(saved['equipment'])==final['equipment'] and (await e.observe())['toast']=='会议室已保存',saved)
 await e.p.locator('#add-room').click();reset=await values();e.check('保存后新增dialog完整reset',reset['name']==reset['location']=='' and reset['active'] and reset['capacity']=='6' and reset['equipment']==[],reset);await e.shot('new-reset')
async def main():
 results=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  cases=[('second-real401',double401,(),['AI-WB-ui-api-error-session-transition'])]+[('pending-barrier-'+str(t),pending,(t,),['AI-WB-ui-load-parallel-error']) for t in [1,2]]+[(f'room-{k}-{f}',room,(k,f),['AI-interface-experience-9','AI-WB-ui-room-edit-draft','AI-interface-experience-8']) for k in ['new','edit'] for f in ['business','network']]
  for name,fn,args,mids in cases:
   e=h.Env();o={'name':name,'method_ids':mids,'revision':h.REV,'source_hashes':h.HASHES};status='unproven'
   try:await e.start(browser,'gap-'+name,'admin',True);await fn(e,*args);status='passed' if e.checks and all(c['passed'] for c in e.checks) else 'failed'
   except Exception as ex:o['error']=str(ex);o['traceback']=traceback.format_exc()
   finally:
    o.update({'status':status,'checks':getattr(e,'checks',[]),'events':getattr(e,'events',[]),'responses':getattr(e,'responses',[]),'screenshots':getattr(e,'shots',[])});p=E/(name+'.json');p.write_text(json.dumps(o,ensure_ascii=False,indent=2));results.append({'name':name,'method_ids':mids,'status':status,'evidence':str(p.relative_to(h.AUDIT))});(h.AUDIT/'ui-gap-results.json').write_text(json.dumps({'revision':h.REV,'results':results},ensure_ascii=False,indent=2));print(name,status,o.get('error',''),flush=True)
    try:await e.close()
    except Exception:pass
  await browser.close()
if __name__=='__main__':asyncio.run(main())
