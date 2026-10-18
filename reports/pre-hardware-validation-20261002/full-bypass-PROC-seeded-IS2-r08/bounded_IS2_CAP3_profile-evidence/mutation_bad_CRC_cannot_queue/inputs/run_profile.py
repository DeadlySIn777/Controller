"""Fresh actual C-driver to actual Verilated IS2 page0; no live/external edits."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,time,os
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:]
def main(out,mutation):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True);copied=out/'inputs';copied.mkdir()
 sources=[p for p in HERE.rglob('*')if p.is_file() and '__pycache__' not in p.parts and p.name not in ['bundle-manifest.json','freeze-receipt.json']]
 before={str(p):sha(p) for p in sources}
 for p in sources:
  q=copied/p.relative_to(HERE);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
 if mutation:
  path=copied/'rtl/cnc3_motion_spi.v';s=path.read_text()
  if mutation=='foreign_consumes':s=s.replace('page_in_flight && read_session &&','page_in_flight && 1\'b1 &&')
  elif mutation=='CMD_consumes':s=s.replace('if(snapshot_start)page_in_flight<=snapshot_fb && page_pending;', 'if(snapshot_start)begin page_in_flight<=snapshot_fb && page_pending;if(!snapshot_fb)page_pending<=0;end')
  elif mutation=='bad_CRC_queues':s=s.replace('if(page_request_accepted)page_pending<=1;', 'if(page_request_accepted || (frame_bad && rejection_header_valid && rejection_header[7:0]==5))page_pending<=1;')
  elif mutation=='fake_index':
   path=copied/'rtl/cnc3_is2_cap3_page0.v';s=path.read_text().replace("32'h00013ffb","32'h00013fff")
  else:raise RuntimeError('unknown mutation')
  assert s!=path.read_text();path.write_text(s,newline='\n')
 executions=[];error=None;observations={};generated={}
 distro=os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder')
 def run(name,args,timeout=1200,allow_fail=False):
  start=time.time();r=subprocess.run(args,capture_output=True,timeout=timeout)
  log=out/(name+'.log');log.write_bytes(r.stdout+r.stderr)
  executions.append({'stage':name,'command':args,'exit_code':r.returncode,'seconds':round(time.time()-start,3),'log_sha256':sha(log)})
  if r.returncode and not allow_fail:raise RuntimeError(name+' failed')
  return r
 try:
  obj=out/'obj'
  run('verilate',['wsl','-d',distro,'--','verilator','--cc','--compiler','clang','--top-module','cnc3_motion_spi','--Mdir',unix(obj),'-Wall','-Wno-fatal',*[unix(p)for p in sorted((copied/'rtl').glob('*.v'))]])
  generated={str(q):sha(q) for q in obj.iterdir()if q.suffix in ['.cpp','.h']}
  for name,source in [('codec',copied/'driver/cnc3_proto.c'),('IS2',copied/'driver/cnc3.c'),('IS1',copied/'originals/cnc3.c')]:
   run('C-'+name,['wsl','-d',distro,'--','clang','-std=c11','-O1','-Wall','-Wextra','-Werror','-pedantic','-Wconversion','-Wshadow','-I'+unix(source.parent),'-c',unix(source),'-o',unix(out/(name+'.o'))])
  for name in (['IS2']if mutation else ['IS2','IS1']):
   exe=out/('probe-'+name)
   args=['wsl','-d',distro,'--','clang++','-std=c++17','-O1','-pthread','-I/usr/share/verilator/include','-I/usr/share/verilator/include/vltstd','-I'+unix(obj),'-I'+unix(copied),'-I'+unix(copied/'driver')]
   if name=='IS1':args.append('-DORIGINAL_DRIVER')
   args += [unix(copied/'profile_probe.cpp'),*[unix(q)for q in sorted(obj.glob('*.cpp'))],unix(out/(name+'.o')),unix(out/'codec.o'),'/usr/share/verilator/include/verilated.cpp','/usr/share/verilator/include/verilated_threads.cpp','-o',unix(exe)]
   run('compile-'+name,args)
   r=run('actual-'+name,['wsl','-d',distro,'--cd',unix(out),'--',unix(exe)],allow_fail=bool(mutation))
   if r.returncode==0:observations[name]=json.loads((out/'observation.json').read_text());shutil.copy2(out/'observation.json',out/('observation-'+name+'.json'))
   elif mutation:
    log=(out/('actual-'+name+'.log')).read_text()
    wanted={'foreign_consumes':'actual RTL snapshot is real CRC-valid CAP3','CMD_consumes':'actual RTL snapshot is real CRC-valid CAP3','bad_CRC_queues':'bad CRC READ_PAGE cannot queue','fake_index':'unsupported index/event/telemetry bits'}[mutation]
    observations['mutation']={'compiled_runtime_rejected':wanted in log,'reason':log.strip()[-700:]}
 except Exception as e:error=repr(e)
 unchanged=all(sha(Path(q))==h for q,h in before.items())
 generated_unchanged=all(sha(Path(q))==h for q,h in generated.items())
 passed=not error and unchanged and generated_unchanged and (observations.get('mutation',{}).get('compiled_runtime_rejected',False) if mutation else set(observations)=={'IS1','IS2'})
 receipt={'status':'PASS' if passed else 'FAIL','mutation':mutation,'error':error,'input_sha256':before,'inputs_unchanged':unchanged,'generated_model_sha256':generated,'generated_model_unchanged':generated_unchanged,'executions':executions,'observation':observations,'scope_flags':{'actual_compiled_C_driver_to_actual_Verilated_SPI_CAP3':passed and not mutation,'real_IS2_inventory_only_incomplete_profile':True,'complete_provider_qualification':False,'ACTIVE_outputs_motion_HAL':False,'physical_clock_or_device_fit':False},'output_hashes':{q.relative_to(out).as_posix():sha(q)for q in out.rglob('*')if q.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'error':error,'observation':observations}));return 0 if passed else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--mutation',choices=['foreign_consumes','CMD_consumes','bad_CRC_queues','fake_index']);a=p.parse_args();raise SystemExit(main(a.out.resolve(),a.mutation))
