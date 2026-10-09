"""Linux aarch64 OS依赖适配器：真实syscall返回后控制熵，执行前只在内存检查写载荷。
不替换业务函数/SQL；输出均为脱敏元数据，未知出口明确记录，不自行认证。
"""
import argparse,base64,collections,ctypes,errno,json,os,pathlib,signal,sys
P_TRACEME=0;P_SYSCALL=24;P_SETOPTIONS=0x4200;P_GETEVENTMSG=0x4201;P_GETREGSET=0x4204;P_GET_SYSCALL_INFO=0x420e
OPTIONS=1|2|4|8|16|64|0x100000
class Vec(ctypes.Structure): _fields_=[('base',ctypes.c_void_p),('length',ctypes.c_size_t)]
libc=ctypes.CDLL(None,use_errno=True);libc.ptrace.restype=ctypes.c_long
libc.ptrace.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.c_void_p]
libc.process_vm_readv.restype=ctypes.c_ssize_t;libc.process_vm_writev.restype=ctypes.c_ssize_t
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--tape');p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args();cmd=a.command[1:] if a.command and a.command[0]=='--' else a.command
out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
if not cmd or sys.platform!='linux' or os.uname().machine!='aarch64':raise SystemExit('requires Linux aarch64 and actual command')
def ptrace(op,pid,addr=0,data=0):
 r=libc.ptrace(op,pid,ctypes.c_void_p(addr),ctypes.c_void_p(data))
 if r==-1:raise OSError(ctypes.get_errno(),os.strerror(ctypes.get_errno()))
 return r
def regs(pid):
 b=(ctypes.c_ulonglong*34)();v=Vec(ctypes.cast(b,ctypes.c_void_p),ctypes.sizeof(b));ptrace(P_GETREGSET,pid,1,ctypes.addressof(v));return list(b)
def read(pid,address,n):
 if n<=0:return b''
 b=ctypes.create_string_buffer(n);l=Vec(ctypes.cast(b,ctypes.c_void_p),n);r=Vec(address,n);got=libc.process_vm_readv(pid,ctypes.byref(l),1,ctypes.byref(r),1,0)
 if got!=n:raise OSError(ctypes.get_errno(),f'read {got}/{n}')
 return b.raw
def write(pid,address,b):
 buf=ctypes.create_string_buffer(b);l=Vec(ctypes.cast(buf,ctypes.c_void_p),len(b));r=Vec(address,len(b));got=libc.process_vm_writev(pid,ctypes.byref(l),1,ctypes.byref(r),1,0)
 if got!=len(b):raise OSError(ctypes.get_errno(),f'write {got}/{len(b)}')
def group(pid):
 try:
  return int(next(x for x in pathlib.Path(f'/proc/{pid}/status').read_text().splitlines() if x.startswith('Tgid:')).split()[1])
 except (OSError,StopIteration):return pid

def pathfd(pid,f):
 try:return os.readlink(f'/proc/{pid}/fd/{f}')
 except OSError:return '<closed_or_unobserved>'
password=b'MeetSpace!2026';needles=[password,password.hex().encode(),base64.b64encode(password),bytes(x^0x55 for x in password)]
counters=collections.Counter();events=[];uncovered=set();prefix={};mappings={};sequence=0
pid=os.fork()
if pid==0:
 ptrace(P_TRACEME,0);os.kill(os.getpid(),signal.SIGSTOP);os.execvpe(cmd[0],cmd,os.environ)
(out/'child-pid.json').write_text(json.dumps({'pid':pid,'command':cmd}))
known={pid};pending={};exits={}
def relay(signum,frame):
 try:os.kill(pid,signum)
 except ProcessLookupError:pass
signal.signal(signal.SIGINT,relay);signal.signal(signal.SIGTERM,relay)

def scan(pid,fd,content,kind):
 target=pathfd(pid,fd)
 if target.startswith('socket:['):counters['protocol_socket_write']+=1;return
 key=(pid,fd);combo=prefix.get(key,b'')+content[:512]
 leaked=any(x and (x in content or x in combo) for x in needles);prefix[key]=(prefix.get(key,b'')+content)[-512:]
 counters['scanned_write_calls']+=1;events.append({'kind':kind,'path':target,'bytes':len(content),'leak':leaked})
 if leaked:counters['leaks']+=1

def enter(pid,r):
 number=r[8];args=r[:6];counters[f'syscall_{number}']+=1
 record={'number':number,'args':args}
 if number in (64,68):
  fd,addr,n=args[:3]
  if n>16*1024*1024:uncovered.add('large_write_over_16MiB')
  else:record['write']=(fd,read(pid,addr,n),'pwrite64' if number==68 else 'write')
 elif number==66:
  fd,addr,n=args[:3]
  if n>1024:uncovered.add('writev_over_1024_vectors')
  else:
   vectors=read(pid,addr,n*16);parts=[]
   for i in range(n):
    pointer=int.from_bytes(vectors[i*16:i*16+8],'little');size=int.from_bytes(vectors[i*16+8:i*16+16],'little')
    if size>16*1024*1024:uncovered.add('large_writev_over_16MiB');continue
    parts.append(read(pid,pointer,size))
   record['write']=(fd,b''.join(parts),'writev')
 elif number in (63,67,65):
  if '/dev/random' in pathfd(pid,args[0]) or '/dev/urandom' in pathfd(pid,args[0]):
   if number in (63,67):record['random_device']={'address':args[1],'path':pathfd(pid,args[0])}
   else:uncovered.add('random_device_readv_not_controlled')
 elif number==222:
  if args[2]&2 and args[3]&1 and not args[3]&32:
   record['mapping']={'length':args[1],'fd':args[4],'path':pathfd(pid,args[4])}
 elif number in (215,227,93,94):
  for key,m in list(mappings.items()):
   owner,address=key
   if owner!=group(pid):continue
   if number in (93,94) or (args[0]<address+m['length'] and address<args[0]+args[1]):
    if m['length']>16*1024*1024:uncovered.add('file_mmap_over_16MiB')
    else:
     try:
      content=read(pid,address,m['length']);leaked=any(x and x in content for x in needles);events.append({'kind':'file_shared_mapping_scan','path':m['path'],'bytes':m['length'],'leak':leaked});counters['scanned_shared_mappings']+=1
      if leaked:counters['leaks']+=1
     except OSError:uncovered.add('mapping_unreadable_before_flush_or_exit')
    if number==215:record.setdefault('unmapping',[]).append((key,dict(m)))
 elif number==216 and (group(pid),args[0]) in mappings:record['remapping']=dict(mappings[(group(pid),args[0])])
 elif number in (35,38,276):record['outlet_event']='unlink_or_rename'
 elif number in (206,211):
  # sendto/sendmsg are HTTP protocol if fd is server accepted socket; outbound connect separately invalidates scope.
  counters['network_send_calls']+=1
 elif number in (425,426,427,270,69,70,71,72,76,77,285):uncovered.add(f'unhandled_IO_syscall_{number}')
 return record

while known:
 try:child,status=os.waitpid(-1,0x40000000)
 except ChildProcessError:break
 if os.WIFEXITED(status) or os.WIFSIGNALED(status):
  exits[str(child)]={'exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None};known.discard(child);pending.pop(child,None);continue
 if not os.WIFSTOPPED(status):continue
 event=status>>16;sig=os.WSTOPSIG(status)
 try:
  if child not in known:known.add(child)
  if event in (1,2,3):
   value=ctypes.c_ulong();ptrace(P_GETEVENTMSG,child,0,ctypes.addressof(value));known.add(value.value);parent_group=group(child);child_group=group(value.value)
   if child_group!=parent_group:
    for (owner,address),mapping in list(mappings.items()):
     if owner==parent_group:mappings[(child_group,address)]=dict(mapping)
   events.append({'kind':'child_process_or_thread','pid':value.value,'parent_group':parent_group,'child_group':child_group,'inherited_shared_mappings':sum(1 for owner,address in mappings if owner==child_group)});ptrace(P_SYSCALL,child);continue
  if event==4:pending.pop(child,None);events.append({'kind':'exec','pid':child});ptrace(P_SYSCALL,child);continue
  if sig==signal.SIGSTOP:ptrace(P_SETOPTIONS,child,0,OPTIONS);ptrace(P_SYSCALL,child);continue
  if sig==signal.SIGTRAP|0x80:
   r=regs(child);info=ctypes.create_string_buffer(128);ptrace(P_GET_SYSCALL_INFO,child,128,ctypes.addressof(info));op=info.raw[0]
   if op==1:pending[child]=enter(child,r)
   elif op==2 and child in pending:
    rec=pending.pop(child);ret=int.from_bytes(info.raw[24:32],'little',signed=True);n=rec['number']
    if (n==278 or 'random_device' in rec) and ret>0:
     random_address=rec['args'][0] if n==278 else rec['random_device']['address'];sequence+=1;before=read(child,random_address,ret)
     if a.tape:
      import hashlib
      b=b'';i=0
      while len(b)<ret:b+=hashlib.sha256((a.tape+':'+str(sequence)+':'+str(i)).encode()).digest();i+=1
      write(child,random_address,b[:ret]);after=b[:ret]
     else:after=before
     if ret==32:
      token=base64.urlsafe_b64encode(after).rstrip(b'=');needles.extend([token,token.hex().encode(),base64.b64encode(token)])
     events.append({'kind':'getrandom' if n==278 else 'random_device_read','pid':child,'bytes':ret,'source':'real_linux_getrandom_syscall' if n==278 else rec['random_device']['path'],'controlled_return':bool(a.tape)})
    if 'mapping' in rec and ret>=0:
     mappings[(group(child),ret)]=rec['mapping'];events.append({'kind':'file_shared_mapping','pid':child,'address_alias':len(mappings),'path':rec['mapping']['path'],'bytes':rec['mapping']['length']})
    if 'unmapping' in rec and ret==0:
     start=rec['args'][0];end=start+((rec['args'][1]+4095)//4096)*4096
     for key,m in rec['unmapping']:
      owner,address=key;mappings.pop(key,None);old_end=address+m['length']
      if address<start:left=dict(m);left['length']=start-address;mappings[(owner,address)]=left
      if old_end>end:right=dict(m);right['length']=old_end-end;mappings[(owner,end)]=right
    if 'remapping' in rec and ret>=0:
     mappings.pop((group(child),rec['args'][0]),None);rec['remapping']['length']=rec['args'][2];mappings[(group(child),ret)]=rec['remapping']
    if 'write' in rec and ret>0:fd,b,kind=rec['write'];scan(child,fd,b[:ret],kind)
    if 'outlet_event' in rec:events.append({'kind':rec['outlet_event'],'pid':child,'syscall':n,'result':ret})
    if n==203 and ret==0:uncovered.add('outbound_connect_requires_destination_observation')
   ptrace(P_SYSCALL,child);continue
  ptrace(P_SYSCALL,child,0,0 if sig==signal.SIGTRAP else sig)
 except (OSError,ValueError) as e:
  uncovered.add(f'tracer_error:{type(e).__name__}:{e}');
  try:ptrace(P_SYSCALL,child)
  except OSError:pass
report={'adapter':'ptrace_syscall_linux_aarch64','tape_alias':a.tape or 'real_os','root_pid':pid,'events':events,'counters':dict(counters),'uncovered':sorted(uncovered),'exits':exits,'formal_verdict':None,'limitations':['syscall trace and payload scanning require independent outlet/schema review','session expiration time adaptation and restart need outer matrix harness','does not claim encrypted/unknown storage harmless without field inspection']}
(out/'os-events.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
