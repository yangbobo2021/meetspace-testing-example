import pathlib,re,json,collections
base=pathlib.Path(__file__).resolve().parent/'mapping-metadata';results=[]
for file in sorted(base.glob('*-mapping-metadata.log')):
 regions=[];pending={};mremaps=[];protect=collections.Counter();unknown=[];shared_write_enable=[];counts=collections.Counter();shared=[];clone_vm=[]
 def remove(start,end):
  nonlocal_dummy=None
  new=[]
  for m in regions:
   if m['end']<=start or m['start']>=end:new.append(m);continue
   if m['start']<start:new.append(dict(m,end=start))
   if m['end']>end:new.append(dict(m,start=end))
  regions[:]=new
 def category(m):
  if 'MAP_ANONYMOUS' in m['flags']:return 'anonymous_private' if 'MAP_PRIVATE' in m['flags'] else 'anonymous_shared'
  return 'shared_file' if 'MAP_SHARED' in m['flags'] else 'private_file'
 for line_number,line in enumerate(file.read_text().splitlines(),1):
  match=re.match(r'^(\d+)\s+[\d.]+\s+(.*)$',line)
  if not match:continue
  pid,call=match.groups()
  if '<unfinished ...>' in call:pending[pid]=call.split('<unfinished ...>')[0];continue
  if call.startswith('<... '):
   resume=re.match(r'<\.\.\. (\w+) resumed>(.*)',call)
   if not resume or pid not in pending:continue
   call=pending.pop(pid)+resume[2]
  name=call.split('(',1)[0];counts[name]+=1
  if name=='execve' and call.endswith('= 0'):regions.clear();continue
  if name in ['clone','clone3'] and 'CLONE_VM' in call:clone_vm.append({'line':line_number,'pid':pid,'shared_vm':True})
  if name=='mmap':
   x=re.match(r'mmap\((.*)\)\s+=\s+(0x[0-9a-f]+)$',call)
   if not x:continue
   parts=x[1].split(', ')
   if len(parts)!=6:unknown.append({'line':line_number,'reason':'mmap_parse'});continue
   start=int(x[2],16);length=int(parts[1]);end=start+((length+4095)//4096)*4096
   m={'start':start,'end':end,'flags':parts[3],'fd_path':parts[4],'initial_protection':parts[2],'origin_mmap_line':line_number}
   remove(start,end);regions.append(m)
   if 'MAP_SHARED' in parts[3]:shared.append(dict(m))
  elif name=='munmap':
   x=re.match(r'munmap\((0x[0-9a-f]+), (\d+)\) = 0$',call)
   if x:remove(int(x[1],16),int(x[1],16)+((int(x[2])+4095)//4096)*4096)
  elif name=='mremap':
   x=re.match(r'mremap\((0x[0-9a-f]+), (\d+), (\d+), ([^)]+)\) = (0x[0-9a-f]+)$',call)
   if not x:unknown.append({'line':line_number,'reason':'mremap_parse','call':call});continue
   start=int(x[1],16);oldlen=int(x[2]);newlen=int(x[3]);newaddr=int(x[5],16)
   owners=[m for m in regions if m['start']<=start and m['end']>=start+oldlen]
   if len(owners)!=1:unknown.append({'line':line_number,'reason':'mremap_input_mapping_unknown'});continue
   old=owners[0];mremaps.append({'line':line_number,'pid':pid,'old_address':hex(start),'old_length':oldlen,'new_address':hex(newaddr),'new_length':newlen,'source_mapping_flags':old['flags'],'source_fd_path':old['fd_path'],'source_mmap_line':old['origin_mmap_line'],'classification':category(old)})
   remove(start,start+oldlen);remove(newaddr,newaddr+newlen);regions.append(dict(old,start=newaddr,end=newaddr+newlen))
  elif name=='mprotect':
   x=re.match(r'mprotect\((0x[0-9a-f]+), (\d+), ([^)]+)\) = 0$',call)
   if not x:continue
   start=int(x[1],16);end=start+int(x[2]);owners=[m for m in regions if m['start']<end and start<m['end']];cursor=start
   for m in sorted(owners,key=lambda m:m['start']):
    if m['start']>cursor:break
    cursor=max(cursor,m['end'])
   if cursor<end:unknown.append({'line':line_number,'reason':'mprotect_input_mapping_unknown','range':[hex(start),int(x[2])],'requested_protection':x[3]})
   cats=set(category(m) for m in owners)
   for cat in cats:protect[cat]+=1
   if 'PROT_WRITE' in x[3]:
    for m in owners:
     if 'MAP_SHARED' in m['flags'] and 'PROT_WRITE' not in m['initial_protection']:shared_write_enable.append({'line':line_number,'path':m['fd_path'],'initial_protection':m['initial_protection'],'new_protection':x[3]})
 results.append({'trace':file.name,'counts':dict(counts),'actual_mremap':mremaps,'mprotect_input_categories':dict(protect),'shared_file_mappings':shared,'shared_readonly_to_write_mprotect':shared_write_enable,'unknown':unknown,'clone_vm_count':len(clone_vm)})
report={'revision':'5247b360276f2900d20fdeab96bd75bb3ece73fa','formal_verdict':None,'rows':results,'all_observed_mremap_inputs_anonymous_private':all(r['actual_mremap'] and all(m['classification']=='anonymous_private' for m in r['actual_mremap']) for r in results),'tracked_shared_file_mremap_observed':any(m['classification']=='shared_file' for r in results for m in r['actual_mremap']),'shared_readonly_to_write_observed':any(r['shared_readonly_to_write_mprotect'] for r in results),'unknown_count':sum(len(r['unknown']) for r in results),'unknown_write_permission_mprotect':[u for r in results for u in r['unknown'] if u['reason']=='mprotect_input_mapping_unknown' and 'PROT_WRITE' in u.get('requested_protection','')],'unknown_scope_explanation':'每生命周期6个未由用户态mmap登记的起始exec映射mprotect均仅PROT_READ，不新增写权限；原地址/范围未隐藏，不据此宣称完整追溯初始ELF映射。所有实际mremap来源对应此前MAP_PRIVATE|MAP_ANONYMOUS fd=-1映射；共享只读文件到写权限转换未观察到。','scope':'Independent current-source actual mapping metadata sample of initialization/seed business and same-db restart; not identical record of the original62 traces. Each original lifecycle records4 mremap count; actual addresses/anonymous origin are captured here, original per-call mapping attributes were not logged.'}
(base/'mapping-metadata-analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='rows'}));print([(r['trace'],r['counts'].get('mremap'),r['counts'].get('mprotect'),r['mprotect_input_categories'],r['unknown']) for r in results])
