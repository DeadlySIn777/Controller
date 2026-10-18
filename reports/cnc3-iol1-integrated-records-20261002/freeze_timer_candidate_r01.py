from pathlib import Path
import hashlib,json,shutil,subprocess
H=Path(__file__).resolve().parent
S=H/'timer-share-stage-r01';F=H/'timer-share-formal-r01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',newline='\n')
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
assert 'PASS exact timer sharing cycles=1200029 edges=4332 profiles=12' in (S/'equivalence.log').read_text()
assert 'Induction step proven: SUCCESS!' in (F/'proof.log').read_text()
before=json.loads((F/'input-witness.json').read_text());assert all(sha(Path(p))==h for p,h in before.items())
M=H/'timer-share-mutations-r01'
if M.exists():raise RuntimeError('fresh output required')
M.mkdir();original=(S/'cnc3_stepgen_runtime.v').read_text();rows=[]
mutations=[('wrong_low_delay','delay_left<=space_ticks','delay_left<=pulse_ticks'),('count_sign','dir?32\'hffffffff:32\'d1','dir?32\'d1:32\'hffffffff'),('truncate_on_stop','if(stop || rate==0)phase<=0;','if(stop || rate==0)begin phase<=0;step<=0;end'),('shared_hold_timer','hold_left<=hold_ticks','hold_left<=pulse_ticks')]
for name,old,new in mutations:
 assert original.count(old)==1,(name,original.count(old));d=M/name;d.mkdir()
 (d/'cnc3_stepgen_runtime.v').write_text(original.replace(old,new),newline='\n')
 for fn in ['cnc3_stepgen_runtime_reference.v','tb_timer_equivalence.sv']:shutil.copyfile(S/fn,d/fn)
 cmd=f"cd '{unix(d)}' && iverilog -g2012 -s tb_timer_equivalence -o timer.vvp cnc3_stepgen_runtime_reference.v cnc3_stepgen_runtime.v tb_timer_equivalence.sv && vvp timer.vvp"
 r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','bash','-lc',cmd],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=90)
 log=r.stdout+r.stderr;(d/'execute.log').write_text(log,newline='\n')
 passed=r.returncode!=0 and 'counter/output/phase mismatch' in log
 rows.append({'name':name,'status':'PASS' if passed else 'FAIL','actual_compiled_mutation_rejected':passed,'exit_code':r.returncode,'mutant_sha256':sha(d/'cnc3_stepgen_runtime.v'),'log_sha256':sha(d/'execute.log')})
 assert passed,rows[-1]
write(M/'receipt.json',{'status':'PASS','rows':rows,'original_exact_runtime_sha256':sha(S/'cnc3_stepgen_runtime.v'),'scope':'actual compiled old/new cycle-equivalence oracle rejects semantic mutants; no physical or vendor fit claim'})
write(S/'equivalence-receipt.json',{'status':'PASS','cycles':1200029,'edges':4332,'profiles':12,'exact_inputs':before,'inputs_unchanged':all(sha(Path(p))==h for p,h in before.items()),'formal_induction_receipt':str(F/'receipt.json'),'compiled_mutation_receipt':str(M/'receipt.json'),'scope':'all 16-bit timing values retained; actual simulated edge/reset/enable/stop/runtime profile equivalence and arbitrary-input two-state sequential induction, not electrical timing'})
write(F/'receipt.json',{'status':'PASS','evidence':'Yosys arbitrary-input two-state sequential SAT temporal induction; reachable HIGH/LOW/SETUP exclusion proved jointly with outputs/count/phase/all timer witnesses; no input timing/rate restriction','induction_length':1,'original_inputs':before,'inputs_unchanged':all(sha(Path(p))==h for p,h in before.items()),'proof_log_sha256':sha(F/'proof.log'),'physical_or_vendor_fit':False})
for kind,source in [('motion','constant-compare-motion-candidate-r01'),('record','constant-compare-record-candidate-r01')]:
 dest=H/f'timer-share-{kind}-candidate-r01'
 if dest.exists():raise RuntimeError('fresh candidate required')
 shutil.copytree(H/source,dest,ignore=shutil.ignore_patterns('__pycache__'))
 target=dest/'cnc3_stepgen_runtime.v' if kind=='motion' else dest/'inputs/motion/cnc3_stepgen_runtime.v'
 old_hash=sha(target);shutil.copyfile(S/'cnc3_stepgen_runtime.v',target)
 write(dest/'timer-sharing-provenance.json',{'status':'PASS','prior_candidate':str(H/source),'old_sha256':old_hash,'new_sha256':sha(target),'equivalence_receipt':str(S/'equivalence-receipt.json'),'formal_receipt':str(F/'receipt.json'),'mutation_receipt':str(M/'receipt.json'),'only_runtime_delta':'mutually-exclusive timers and signed count increment share arithmetic; exact16-bit inputs unchanged','device_or_abi_or_physical_ratings_changed':False})
 # Record snapshot includes its nested motion manifest, unlike motion runner.
 if kind=='record':
  inner=dest/'inputs/motion';m=json.loads((inner/'bundle-manifest.json').read_text());m['files']={p.relative_to(inner).as_posix():sha(p) for p in inner.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('bundle-manifest.json','freeze-receipt.json')};write(inner/'bundle-manifest.json',m)
 manifest=json.loads((dest/'bundle-manifest.json').read_text())
 manifest['files']={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file() and '__pycache__' not in p.parts and (p.name not in ('bundle-manifest.json','freeze-receipt.json') if kind=='motion' else p not in (dest/'bundle-manifest.json',dest/'freeze-receipt.json'))}
 write(dest/'bundle-manifest.json',manifest)
 print(dest,sha(dest/'bundle-manifest.json'))
