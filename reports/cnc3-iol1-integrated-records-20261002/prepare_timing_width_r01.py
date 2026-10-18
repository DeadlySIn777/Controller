from pathlib import Path
import hashlib,json,shutil,subprocess
H=Path(__file__).resolve().parent;S=H/'timing-width-stage-r01';S.mkdir()
src=H/'timer-share-stage-r01/cnc3_stepgen_runtime.v';old=src.read_text()
new=old.replace('module cnc3_stepgen_runtime (','module cnc3_stepgen_runtime #(parameter integer TIMER_BITS=16) (')
new=new.replace('reg[15:0] delay_left,hold_left;','reg[TIMER_BITS-1:0] delay_left,hold_left;')
for name in ('setup','space','pulse','hold'):new=new.replace('<=%s_ticks;'%name,'<=%s_ticks[TIMER_BITS-1:0];'%name)
(S/'cnc3_stepgen_runtime.v').write_text(new,newline='\n');shutil.copyfile(src,S/'prior_runtime.v')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source_state=H/'crc-share-record-candidate-r01/inputs/motion/cnc3_motion_state.v'
validator=H/'crc-share-record-candidate-r01/inputs/motion/inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v'
(S/'scope.json').write_text(json.dumps({'scope':'Only actual motion composition instantiates TIMER_BITS10; generic runtime default16 preserves every16-bit value. Cold reset timing100 and accepted CONFIGURE structural timing bounds100..1023 guarantee all timer loadsfit10. No rate/pulse/drive/ABI field changes.','runtime_prior_sha256':sha(src),'runtime_next_sha256':sha(S/'cnc3_stepgen_runtime.v'),'actual_state_sha256':sha(source_state),'actual_structural_validator_sha256':sha(validator),'timing_config_boundary':{'min':100,'max':1023},'authority_or_fit_grant':False},indent=2)+'\n')
F=H/'timing-width-formal-r01';shutil.copytree(H/'timer-share-formal-r01',F,ignore=shutil.ignore_patterns('*.log','*.txt','receipt.json','input-witness.json'))
text=new.replace('output wire quiescent','output wire quiescent, output wire[63:0] timer_witness, output wire[31:0] phase_witness').replace(' assign quiescent=', ' assign timer_witness={high_left,low_left,setup_left,{{(16-TIMER_BITS){1\'b0}},hold_left}};\n assign phase_witness=phase;\n assign quiescent=')
(F/'new.v').write_text(text,newline='\n')
m=(F/'miter.v').read_text().replace('cnc3_stepgen_runtime new(','cnc3_stepgen_runtime #(.TIMER_BITS(10)) new(')
m=m.replace('always @* begin','''always @* begin
 assume(pulse_ticks<=1023 && space_ticks<=1023 && setup_ticks<=1023 && hold_ticks<=1023);
 assert(ot[63:58]==0 && ot[47:42]==0 && ot[31:26]==0 && ot[15:10]==0);
''')
(F/'miter.v').write_text(m,newline='\n');(F/'prove.ys').write_text((F/'prove.ys').read_text().replace('sat -seq','chformal -lower\nsat -set-assumes -seq'),newline='\n')
(F/'prove.sh').write_text((F/'prove.sh').read_text().replace('timer-share-formal-r01','timing-width-formal-r01').replace('timer-proof-r01','timing-width-proof-r01'),newline='\n')
before={str(p):sha(p) for p in [*F.glob('*.v'),F/'prove.ys',F/'prove.sh',S/'cnc3_stepgen_runtime.v',source_state,validator]}
u='/mnt/'+F.drive[0].lower()+F.as_posix()[2:]
r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh',u+'/prove.sh'],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=150)
(F/'command.log').write_text(r.stdout+r.stderr,newline='\n');passed=r.returncode==0 and 'Induction step proven: SUCCESS!' in (F/'proof.log').read_text() and all(sha(Path(p))==h for p,h in before.items())
(F/'receipt.json').write_text(json.dumps({'status':'PASS' if passed else 'FAIL','scope':'arbitrary all16-bit externalinputs constrained to0..1023; full sequential state/outputs/count/phase/timer equivalence between frozen16-bit reference and actual10-bit timer composition. Default16 unchanged. Accepted product100..1023 is subset.','exact_inputs':before,'inputs_unchanged':all(sha(Path(p))==h for p,h in before.items()),'proof_sha256':sha(F/'proof.log'),'exit_code':r.returncode,'physical_or_vendorfit':False},indent=2)+'\n')
assert passed
for kind,source in [('record','crc-share-record-candidate-r01'),('motion','timer-share-motion-candidate-r01')]:
 D=H/f'timing-width-{kind}-candidate-r01';shutil.copytree(H/source,D,ignore=shutil.ignore_patterns('__pycache__'))
 root=D/'inputs/motion' if kind=='record' else D
 shutil.copyfile(S/'cnc3_stepgen_runtime.v',root/'cnc3_stepgen_runtime.v')
 top=root/'cnc3_motion_spi.v';t=top.read_text();assert t.count('cnc3_stepgen_runtime generator(')==1;top.write_text(t.replace('cnc3_stepgen_runtime generator(','cnc3_stepgen_runtime #(.TIMER_BITS(10)) generator('),newline='\n')
 (D/'timing-width-provenance.json').write_text(json.dumps({'scope':json.loads((S/'scope.json').read_text()),'formal_receipt':str(F/'receipt.json'),'formal_receipt_sha256':sha(F/'receipt.json'),'only_implementation_delta':'shared runtime internaltimerwidth parameter; actual qualified config always100..1023, generic standalone default16 unchanged','fit_or_newratings':False},indent=2)+'\n')
 m=json.loads((D/'bundle-manifest.json').read_text());m['files']={p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts and (p.name not in ('bundle-manifest.json','freeze-receipt.json') if kind=='motion' else p not in (D/'bundle-manifest.json',D/'freeze-receipt.json'))};(D/'bundle-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 print(D,sha(D/'bundle-manifest.json'))
