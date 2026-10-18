"""Run one combined all-net fill on existing main1, then cached native DRC.

Original R157 CLI is left running. No adoption or fabrication output.
"""
import datetime,hashlib,json,os,shlex,shutil,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
STAGE=H/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753'
board=STAGE/'FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb'
assert sha(board)=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
manifest=STAGE/'final-stage-manifest.json';assert sha(manifest)=='50016f4cc0f0928bf34d186b1fa6e912f6229ed88bb090eb788058486306253e'
recovery=H/'coupled-recovery/Q0-DIC-DI6-exact-R157-minimal-sparse-native-replay-manifest-r588/minimal-exact-Q0-DIC-DI6-native-replay-manifest.json';assert sha(recovery)=='1c7fba1adc371ab8b3a4ffc78249cc63c0a2aec113ade7d4e683d21bd2b2b815'
expected=H/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json';assert sha(expected)=='13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3'
native=H/'native_combined_all_net_fill_and_real_saved_cache_r298.py';assert native.is_file()
OUT=H/'combined-R753-one-full-native-fill-cached-DRC-r299';assert not OUT.exists();OUT.mkdir()
source=H/'R155-known-reference-native-diagnostic-r157/measure/copy';copy=OUT/'copy';filled=OUT/'filled-copy';copy.mkdir();filled.mkdir()
for p in source.iterdir():
 if p.name=='board.kicad_pcb' or p.name.endswith('.lck'):continue
 for destination in (copy,filled):
  if p.is_dir():shutil.copytree(p,destination/p.name)
  else:shutil.copy2(p,destination/p.name)
candidate=copy/'board.kicad_pcb';candidate.write_bytes(board.read_bytes());assert sha(candidate)==sha(board)
for suffix in ('.kicad_pro','.kicad_dru'):
 assert sha(candidate.with_suffix(suffix))==sha(source/('board'+suffix))==sha(filled/('board'+suffix))
for key in ('board.kicad_sch','sch.net','fp-lib-table'):assert (copy/key).is_file()and sha(copy/key)==sha(filled/key)
wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavym.sh');testwrapper=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh')
args=['sh',wrapper.as_posix(),'kicad','C:/Program Files/KiCad/10.0/bin/python.exe',native.as_posix(),candidate.as_posix(),expected.as_posix(),(OUT/'native-full').as_posix(),(filled/'board.kicad_pcb').as_posix()]
env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env.get('PATH','')
pins={str(p.resolve()):sha(p)for p in(Path(__file__),board,manifest,recovery,expected,native,wrapper,testwrapper,candidate,candidate.with_suffix('.kicad_pro'),candidate.with_suffix('.kicad_dru'))}
pins.update({str(p.resolve()):sha(p)for p in copy.rglob('*')if p.is_file()});pins.update({str(p.resolve()):sha(p)for p in filled.rglob('*')if p.is_file()})
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def state(phase,**x):put('status.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':phase,'adopted':False,**x});print('R299',phase,flush=True)
def check():assert all(sha(p)==v for p,v in pins.items()),'Frozen combined input changed'
put('launch-and-inputs.json',{'pins':pins,'native_fill_command':args,'existing_native_fill_slot':'main1','subsequent_native_cached_DRC_slot':'test-only1','full_CPP_fill_calls':1,'native_full_CLI_without_refill_reads_real_saved_CPP_cache':True,'original_R157_full_CLI_uninterrupted':True,'new_heavy_slots':0,'manufacturing_ready':False,'adopted':False})
state('ONE_COMBINED_FULL_NATIVE_CPP_MAIN1_RUNNING',candidate_SHA256=sha(candidate))
with (OUT/'native-full.log').open('w',encoding='utf-8')as log:run=subprocess.run(['C:/Program Files/Git/bin/bash.exe','-c',' '.join(shlex.quote(x)for x in args)],env=env,stdout=log,stderr=subprocess.STDOUT)
check();put('native-process-completion.json',{'exit_code':run.returncode,'log_SHA256':sha(OUT/'native-full.log')})
if run.returncode:state('FULL_NATIVE_FAILED_RESULTS_PRESERVED',exit_code=run.returncode);raise SystemExit(run.returncode)
receipt=json.loads((OUT/'native-full/receipt.json').read_bytes());assert receipt['candidate_SHA256']==sha(candidate)and receipt['full_native_CPP_Fill_calls']==1 and not receipt['discrete_Cu_errors']and receipt['native_saved_reload_Cu_pose_match']
saved=filled/'board.kicad_pcb';assert sha(saved)==receipt['genuine_CPP_filled_diagnostic_copy_SHA256'];pins[str(saved.resolve())]=sha(saved)
reloadmask=json.loads((OUT/'native-full/saved-native-reload-via-flashes.json').read_bytes())
if not reloadmask['matches_in_memory_full_native_flash_sets']:
 state('SAVED_NATIVE_FLASH_SET_DIFFERENCE_HELD_NO_CACHED_DRC');raise SystemExit(1)
state('ACTUAL_FULL_NATIVE_COMPLETE_CACHED_DRC_TEST_ONLY_RUNNING',full_native_receipt_SHA256=sha(OUT/'native-full/receipt.json'))
drcargs=['sh',testwrapper.as_posix(),'kicad','C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--output',(OUT/'drc.json').as_posix(),'board.kicad_pcb']
put('cached-native-DRC-command.json',{'args':drcargs,'working_directory':str(filled.resolve()),'saved_board_SHA256':sha(saved),'no_refill_because_cache_is_the_actual_completed_CPP_full_fill':True,'old_or_new_mask_failures_still_raw_FAILED':receipt['old_actual_or_NEW_ordinary_mask_errors']})
with (OUT/'drc.log').open('w',encoding='utf-8')as log:drc=subprocess.run(['C:/Program Files/Git/bin/bash.exe','-c',' '.join(shlex.quote(x)for x in drcargs)],cwd=filled,env=env,stdout=log,stderr=subprocess.STDOUT)
check();assert (OUT/'drc.json').is_file(),'Native CLI produced no report'
put('receipt.json',{'status':'COMBINED_NATIVE_FULL_FILL_AND_NATIVE_CACHED_DRC_COMPLETE_ALL_SOURCE_REFERENCE_CURRENT_REVIEW_OPEN','candidate_SHA256':sha(candidate),'native_full_receipt_SHA256':sha(OUT/'native-full/receipt.json'),'saved_actual_CPP_cache_SHA256':sha(saved),'native_DRC_SHA256':sha(OUT/'drc.json'),'native_DRC_exit_code':drc.returncode,'input_SHA256':pins,'all_native_fill_source_contacts_joins_masks_oldrefs_true_guards_current_and_SI_need_independent_review':True,'original_R157_full_CLI_uninterrupted':True,'new_heavy_slots':0,'adopted':False,'manufacturing_ready':False});state('FULL_NATIVE_AND_CACHED_DRC_COMPLETE_REVIEW_OPEN')
