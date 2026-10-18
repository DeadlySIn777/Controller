from pathlib import Path
import hashlib,json,shutil,subprocess
H=Path(__file__).resolve().parent;S=H/'crc-share-combinational-formal-r02';D=H/'crc-share-combinational-formal-r03'
if D.exists():raise RuntimeError('fresh proof required')
D.mkdir();shutil.copyfile(S/'miter.v',D/'miter.v')
(D/'prove.ys').write_text((S/'prove.ys').read_text().replace('opt\nsat','opt\nchformal -lower\nsat'),newline='\n')
(D/'prove.sh').write_text((S/'prove.sh').read_text().replace('formal-r02','formal-r03').replace('crc-datapath-r02','crc-datapath-r03'),newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in [*D.glob('*.v'),D/'prove.ys',D/'prove.sh',*(H/'crc-share-stage-r01').glob('*.v')]}
u='/mnt/'+D.drive[0].lower()+D.as_posix()[2:]
r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh',u+'/prove.sh'],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=150)
(D/'command.log').write_text(r.stdout+r.stderr,newline='\n');log=(D/'proof.log').read_text() if (D/'proof.log').exists() else '';passed=r.returncode==0 and 'SAT proof finished - no model found: SUCCESS!' in log and all(sha(Path(p))==h for p,h in before.items())
(D/'receipt.json').write_text(json.dumps({'status':'PASS' if passed else 'FAIL','formal_scope':'arbitrary32-bit TX/RX CRCs/arbitrary320-bit frame/arbitrary8-bit RX byte; PREP indices0..35 and final35 output, SHIFT update exactly equivalent. Combinational next-CRC proof, not full stateful temporal induction.','exact_inputs':before,'inputs_unchanged':all(sha(Path(p))==h for p,h in before.items()),'proof_log_sha256':sha(D/'proof.log'),'exit_code':r.returncode,'full_sequential_proof':False,'prior_r02':'retained FAIL: installed Yosys requires explicit chformal -lower for combinational $check cells; no source or assertion delta','physical_or_vendor_fit':False},indent=2)+'\n')
print('PASS' if passed else 'FAIL');raise SystemExit(0 if passed else 1)
