import datetime,json,os,re,sqlite3,subprocess,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path.cwd(); R=ROOT/'tests/delivery-acceptance/runs/acceptance-20261008T-full-0b386b4-r1';E=R/'evidence/notification-runtime-control'; E.mkdir(exist_ok=True)
observations=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True)
 for label,python in [('python312',sys.executable),('python314','/opt/homebrew/bin/python3')]:
  db=E/(label+'.sqlite');db.unlink(missing_ok=True);log=(E/(label+'-server.log')).open('w')
  proc=subprocess.Popen([python,'-m','app.server','--host','127.0.0.1','--port','0','--db',str(db)],stdout=subprocess.PIPE,stderr=log,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  try:
   line=proc.stdout.readline();url=re.search(r'http://127.0.0.1:\d+',line).group();ctx=browser.new_context(viewport={'width':1280,'height':900},timezone_id='Asia/Shanghai');page=ctx.new_page();page.goto(url);page.locator('[data-account=alice]').click();page.locator('#login-form button[type=submit]').click();page.locator('[data-book-room="4"]').wait_for();page.locator('[data-book-room="4"]').click()
   day=(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date()+datetime.timedelta(days=1)).isoformat()
   for key,value in {'title':'真实运行时通知完整性','date':day,'start':'10:00','end':'11:00','attendees':'2'}.items():page.locator(f'#booking-form [name={key}]').fill(value)
   page.locator('#booking-form button[type=submit]').click();page.locator('#booking-dialog').wait_for(state='hidden');page.locator('nav [data-page=inbox]').click();page.locator('.notice-row').wait_for()
   response=ctx.request.get(url+'/api/notifications');body=response.json();message=body['notifications'][0]['message'];shot=E/(label+'-notification.png');page.screenshot(path=str(shot),full_page=True)
   control=subprocess.check_output([python,'-c',"import datetime,json,sys,locale; x=datetime.datetime.fromisoformat('2030-04-11T10:00:00+08:00'); print(json.dumps({'python':sys.version,'strftime':x.strftime('%m月%d日 %H:%M'),'locale_time':locale.getlocale(locale.LC_TIME)}))"],text=True)
   observations.append({'runtime':json.loads(control),'command':[python,'-m','app.server','--host','127.0.0.1','--port','0','--db',str(db.relative_to(R))],'clock':'real wall clock, no adapters, no browser interception','day':day,'http_status':response.status,'notification':body,'visible_text':page.locator('.notice-row').inner_text(),'screenshot':str(shot.relative_to(R)),'expected':'通知包含主题、会议室、北京时间月日及10:00–11:00完整时段','passed':day[5:7]+'月'+day[8:10]+'日 10:00–11:00' in message})
   ctx.close()
  finally:proc.terminate();proc.wait(timeout=10);log.close()
 browser.close()
(E/'results.json').write_text(json.dumps({'revision':'0b386b4bd37b01eb996c5e74215ab1a4463a9487','observations':observations,'conclusion':'Python3.12真实目标通知日期/开始时间缺失；Python3.14对照不抵消该失败。'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'python':x['runtime']['python'],'passed':x['passed']} for x in observations]))
