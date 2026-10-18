"""Fresh selected LOGIC_GND baseline matching the exact eleven-item DI6 trial."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
import native_pose_signal_contract as NC
H=Path(__file__).resolve().parent;OUT=H/'di6-matched-native-baseline-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
assert not OUT.exists();parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
trial=H/'di6-native-diagnostic-r1';rpath=H/'coupled-recovery/di6-native-owned-ledger-r14/receipt.json';assert sha(rpath)=='6d7dcdc50a10393138761a0067fb73325eace8307800358d72723adcbb1afd79';r=json.loads(rpath.read_bytes())
expected_path=trial/'expected-Cu.json';expected=json.loads(expected_path.read_bytes());after=trial/'copy/board.kicad_pcb';assert sha(after)==expected['board_sha256']=='41eca28f00df07808c189ed0e58150d1a6d2dc6cffcdac2d5f8f0429d521e5ec'
removed={x['UUID']for x in r['exact_new_chunk_files']};assert len(removed)==11;original=NC.C.inventory(parent.read_bytes());rows={u:x for u,x in expected['copper'].items()if u not in removed};assert set(rows)==set(original[4])
assert all(hashlib.sha256(original[4][u]).hexdigest()==x['chunk_sha256']for u,x in rows.items())
OUT.mkdir();copy=OUT/'copy';copy.mkdir();board=copy/'board.kicad_pcb';shutil.copy2(parent,board);assert sha(board)==sha(parent)
for ext in('.kicad_pro','.kicad_dru'):
 assert sha(parent.with_suffix(ext))==sha((trial/'copy/board.kicad_pcb').with_suffix(ext));shutil.copy2(parent.with_suffix(ext),board.with_suffix(ext))
ep=OUT/'expected-Cu.json';write(ep,{'board_path':str(board.resolve()),'board_sha256':sha(board),'copper':rows})
helper=H/'native_di6_scoped_refill_r1.py';cmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(helper.resolve()),str(board.resolve()),str(ep.resolve()),str((OUT/'scoped-native-fill').resolve())]
inputs={str(p.resolve()):sha(p)for p in(Path(__file__),parent,parent.with_suffix('.kicad_pro'),parent.with_suffix('.kicad_dru'),rpath,expected_path,after,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),ep,helper)}
write(OUT/'inputs.json',inputs);write(OUT/'invocation.json',{'command':cmd,'exact_same_source_pose_project_rule_context_as_DI6_trial':True,'only_DI6_11_items_absent':True,'existing_slot':'test-only1','new_heavy_slots':0,'all_other_fills_unvalidated':True})
env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
print('DI6_MATCHED_EEDF_LOGIC_NATIVE_BASELINE_START',flush=True)
with(OUT/'scoped-fill.log').open('w')as log:run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
assert all(sha(p)==v for p,v in inputs.items());fr=OUT/'scoped-native-fill/receipt.json';write(OUT/'receipt.json',{'verdict':'MATCHED_EEDF_ONLY_LOGIC_NATIVE_REFILL_COMPLETE_DI6_DELTA_REVIEW_OPEN'if run.returncode==0 else'FAIL_MATCHED_DI6_NATIVE_BASELINE_FILL','candidate_sha256':sha(board),'exact_same_source_pose_project_rules_and_fill_helper_as_after':True,'only_exact_DI6_11additions_absent':True,'fresh_selected_raw_net':'/LOGIC_GND','native_fill_exit':run.returncode,'scoped_fill_receipt_sha256':sha(fr)if fr.exists()else None,'all_other_fills_and_finaljoint_source_reference_current_DRC_SI':'OPEN','adopted':False});print(json.dumps({'native_exit':run.returncode,'baseline_board_sha256':sha(board)}),flush=True)
raise SystemExit(run.returncode)
