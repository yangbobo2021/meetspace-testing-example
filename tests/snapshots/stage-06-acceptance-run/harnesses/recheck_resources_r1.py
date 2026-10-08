"""Resource preflight only; no acceptance verdict. Run from repository root."""
import ast, datetime, hashlib, http.cookiejar, json, os, platform, re, sqlite3, subprocess, sys, tempfile, time
from pathlib import Path
from urllib.request import Request, build_opener, HTTPCookieProcessor, urlopen
ROOT=Path.cwd(); L=ROOT/'tests/delivery-acceptance'
sys.path.insert(0,'/Users/boboyang/work/sublangai/skills/app-delivery-acceptance/scripts')
import playbook as pb
pb.verify_project_binding(L,ROOT)
STAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
E=L/'evidence/resources'/STAMP; E.mkdir(parents=True)
files=['README.md','docs/release-handoff.md','docs/development-checks.md','app/server.py','web/app.js','web/index.html','web/style.css','tests/test_smoke.py','tests/delivery-acceptance/requirements.json']
base={'verified_at':STAMP,'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_sha256':{f:pb.digest(ROOT/f) for f in files},'python':sys.version,'platform':platform.platform(),'sqlite':sqlite3.sqlite_version}
results={}; decisions=[]
def record(key, description, value, **extra):
    path=E/(key+'.json'); pb.write_json(path,{**base,**value})
    decisions.append({'id':key,'kind':'local','description':description,'verification':{'status':'passed','evidence':str(path.relative_to(L))},'reuse_condition':'复用前检查源码与需求哈希、运行时和浏览器版本；每轮重建隔离数据并复验健康和身份。',**extra})
def start(db):
    cmd=[sys.executable,'-m','app.server','--host','127.0.0.1','--port','0','--db',str(db)]
    log=(E/'server.log').open('a')
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=log,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    line=proc.stdout.readline(); match=re.search(r'http://127.0.0.1:\d+',line)
    if not match: raise RuntimeError('Server failed to start')
    return proc,match.group(),log
def stop(proc,log):
    proc.terminate(); proc.wait(timeout=10); log.close()
def counts(db):
    with sqlite3.connect(db) as c:
        return {t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['teams','users','rooms','bookings','notifications','sessions']}
with tempfile.TemporaryDirectory(dir=L,prefix='resource-db-') as tmp:
    db=Path(tmp)/'preflight.sqlite'; proc,url,log=start(db)
    try:
        health=json.load(urlopen(url+'/api/health')); assert health['status']=='ok'
        initial=counts(db); assert [initial[x] for x in ['teams','users','rooms','bookings']]==[2,4,5,3]
        record('local-runtime','Python 标准库、Asia/Shanghai 时区、SQLite 和真实 HTTP 启动可用。',{'health':health,'command':[sys.executable,'-m','app.server','--host','127.0.0.1','--port','0','--db','<本轮台账内新数据库>'],'listen_url':url})
        # Extract only the public synthetic fixture; never persist password or session cookies.
        tree=ast.parse((ROOT/'app/server.py').read_text())
        password=next(n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='password_hash' and n.args and isinstance(n.args[0],ast.Constant))
        identities=[]
        for name,role,team in [('admin','admin',1),('alice','member',1),('bob','member',1),('other','admin',2)]:
            client=build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
            req=Request(url+'/api/login',data=json.dumps({'email':name+'@meetspace.test','password':password}).encode(),headers={'Content-Type':'application/json','X-Meeting-App':'1'})
            with client.open(req) as response: assert response.status==200
            user=json.load(client.open(url+'/api/session'))['user']; assert (user['role'],user['team_id'])==(role,team)
            identities.append({k:user[k] for k in ['id','email','role','team_id']})
        record('synthetic-identities','四个公开合成账号真实登录及当前身份可用；不需要真实凭据。',{'identities':identities,'credential_ref':'README.md#示例账号 (公开合成 fixture；非生产秘密)','cookies_recorded':False},credential_ref='README.md#示例账号',credential_reusable=True)
        browser_script=L/'harnesses/verify_resource_browser.py'
        browser=subprocess.run(['/Users/boboyang/.cloakbrowser-codex/venv/bin/python',str(browser_script),url,str(E)],capture_output=True,text=True)
        (E/'browser-tool.log').write_text(browser.stdout+browser.stderr)
        assert browser.returncode==0, 'Browser preflight failed; see browser-tool.log'
        info=json.loads((E/'browser.json').read_text())
        record('browser-targets','Chromium 桌面 1280×900 与窄屏触控模拟 390×844；不代表真实手机或跨浏览器验收。',info)
    finally: stop(proc,log)
    before=counts(db); proc,url,log=start(db)
    try: assert counts(db)==before; assert json.load(urlopen(url+'/api/health'))['status']=='ok'
    finally: stop(proc,log)
    fresh=Path(tmp)/'reset.sqlite'; proc,url,log=start(fresh)
    try: reset=counts(fresh); assert reset==initial
    finally: stop(proc,log)
    record('isolated-data','新文件初始化；同文件重启保留记录；重置使用另一个新文件并重建进程和浏览器上下文。',{'initial_counts':initial,'restart_counts':before,'fresh_reset_counts':reset,'default_database_touched':False,'cleanup':'仅删除本脚本创建的临时隔离目录；服务已停止。'})
imports=sorted({n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module}|{a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names})
assert all(x in sys.stdlib_module_names for x in imports)
record('service-inventory','未发现第三方业务服务；通知直接写本地 SQLite，页面资产本地提供，API 同源。无需第三方 Mock 或真实服务凭据。',{'python_imports':imports,'third_party_services':[],'browser_external_requests':info['external_requests'],'source_basis':['app/server.py: notify, imports, main','web/app.js: api','web/index.html: local assets','README.md and docs/release-handoff.md scope'],'integration_and_mock_assessment':'不适用：未发现第三方业务适配器或服务；不声明任何第三方集成测试通过。'})
with tempfile.TemporaryDirectory(dir=L,prefix='smoke-db-') as tmp:
    smoke=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],capture_output=True,text=True,env={**os.environ,'TMPDIR':tmp,'PYTHONDONTWRITEBYTECODE':'1'})
(E/'smoke.log').write_text(smoke.stdout+smoke.stderr); assert smoke.returncode==0
record('existing-test-command','现有 unittest 命令可执行；三个冒烟测试通过仅证明有限路径。',{'command':'python3 -m unittest discover -s tests -v','exit_code':smoke.returncode,'log':str((E/'smoke.log').relative_to(L))})
resources={'discovery_complete':True,'discovery_basis':'README、交接文档、app/server.py 全部导入及服务实现、web 全部资产/API、原有测试、已确认需求与现有空资源台账；本次真实启动/身份/数据重置/浏览器资源探测。','decisions':decisions,'limitations':['资源预检不替代 159 个场景的执行和独立证据审阅。','精确双时钟、并发屏障、SQL/提交故障与熵注入为后续场景执行 harness；本次未验证，不得据本次资源通过结论宣称这些能力已就绪。'],'verified_at':STAMP}
pb.write_json(E/'resource-recheck.json',resources)
print(json.dumps({'status':'resource_preflight_passed','evidence':str(E),'decisions':len(decisions)},ensure_ascii=False))
