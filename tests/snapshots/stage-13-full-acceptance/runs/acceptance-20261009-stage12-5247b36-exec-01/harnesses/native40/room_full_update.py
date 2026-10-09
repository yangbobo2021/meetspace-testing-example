import asyncio,json,os,traceback
from pathlib import Path
OUT=Path(__file__).resolve().parents[2]/'evidence/room-full-update';OUT.mkdir(exist_ok=True);os.environ['MEETSPACE_COVERAGE_AUDIT']=str(OUT)
import identity_env as h
from playwright.async_api import async_playwright
async def main():
 e=h.Env();o={'revision':h.REV,'method_id':'AI-space-administration-3','status':'unproven','steps':[]}
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  try:
   await e.start(browser,'full-room-update','admin');await e.nav('manage');p=e.p;await p.locator('#add-room').click();f=p.locator('#room-form');await f.locator('[name=name]').fill('新建全资料室');await f.locator('[name=location]').fill('初始位置');await f.locator('[name=capacity]').fill('5');await f.locator('[name=equipment][value=白板]').check();await f.locator('[type=submit]').click();await p.locator('#room-dialog').wait_for(state='hidden');await e.ready();st,b,_=h.req(e.url,'/api/rooms',cookie=await e.cookie());room=next(x for x in b['rooms'] if x['name']=='新建全资料室');rid=room['id'];expected={k:room[k] for k in ['name','location','capacity','equipment','active']};o['steps'].append({'operation':'create','record':room});await e.shot('created')
   changes=[{'name':'单字段新名称'},{'location':'单字段新位置'},{'capacity':9},{'equipment':['显示屏','电话会议']},{'active':False},{'name':'最终同时更新室','location':'最终新位置','capacity':11,'equipment':['白板','视频会议'],'active':True}]
   for idx,change in enumerate(changes):
    await e.nav('manage');await p.locator(f'[data-edit-room="{rid}"]').click();f=p.locator('#room-form')
    for k,v in change.items():
     if k=='equipment':
      for eq in ['显示屏','白板','视频会议','电话会议']:await f.locator('[name=equipment][value="'+eq+'"]').set_checked(eq in v)
     elif k=='active':await f.locator('[name=active]').set_checked(v)
     else:await f.locator('[name='+k+']').fill(str(v))
    await f.locator('[type=submit]').click();await p.locator('#room-dialog').wait_for(state='hidden');await e.ready();expected.update(change);st,b,_=h.req(e.url,'/api/rooms',cookie=await e.cookie());room=next(x for x in b['rooms'] if x['id']==rid);got={k:room[k] for k in expected};e.check('逐字段/全字段持久读取 '+str(idx),st==200 and got==expected,{'change':change,'expected':dict(expected),'actual':got});o['steps'].append({'operation':'patch','change':change,'expected':dict(expected),'actual':got});await e.shot('update-'+str(idx))
   await p.locator('[data-logout]:visible').first.click();await p.locator('#login-form').wait_for();await e.login('admin');await e.nav('manage');await p.locator(f'[data-edit-room="{rid}"]').click();f=p.locator('#room-form');ui={'name':await f.locator('[name=name]').input_value(),'location':await f.locator('[name=location]').input_value(),'capacity':int(await f.locator('[name=capacity]').input_value()),'equipment':await f.locator('[name=equipment]:checked').evaluate_all('(es)=>es.map(x=>x.value)'),'active':await f.locator('[name=active]').is_checked()};st,b,_=h.req(e.url,'/api/rooms',cookie=await e.cookie());record=next(x for x in b['rooms'] if x['id']==rid);e.check('退出重登UI全部字段和独立读取一致',ui==expected and all(record[k]==v for k,v in expected.items()),{'UI':ui,'expected':expected,'record':record});await e.shot('relogin-read-all-fields');o['status']='passed' if all(x['passed'] for x in e.checks) else 'failed'
  except Exception as ex:o.update(error=str(ex),traceback=traceback.format_exc())
  finally:
   o.update(checks=e.checks,events=e.events,responses=e.responses,screenshots=e.shots);(OUT/'results.json').write_text(json.dumps(o,ensure_ascii=False,indent=2));print(o['status'],o.get('error',''))
   await e.close();await browser.close()
asyncio.run(main())
