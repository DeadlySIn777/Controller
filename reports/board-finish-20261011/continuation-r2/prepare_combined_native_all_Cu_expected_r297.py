"""Independent exact serialized Cu ledger for a staged combined diagnostic."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,hashlib,sys,re
from decimal import Decimal
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;sha=N.sha
candidate,out=map(Path,sys.argv[1:3]);assert candidate.is_file()and not out.exists();out.mkdir()
base=N.R157/'copy/board.kicad_pcb';assert sha(base)=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'
ledger=H/'field-power/R157-minimal-local-three-ground-landings-selected-native-r667/all-copper-expected.json';assert sha(ledger)=='d07e61db5231705f9edcbd1648650294e3f66ee9a9c8f915b36be1e6d423bcfb'
baseline=json.loads(ledger.read_bytes())['copper'];before=K.C.inventory(base.read_bytes());raw=candidate.read_bytes();after=K.C.inventory(raw);identity=K.A.N.SourceNets(raw)
assert len(baseline)==94402 and all(uid in before[3]for uid in baseline)
def iu(value):
 d=Decimal(value)*1000000;assert d==d.to_integral_value();return int(d)
def values(ch,name,count=1):
 match=re.search(rb'\('+name.encode()+rb'\s+([^()]+)\)',ch);assert match,(name,ch[:80]);parts=match.group(1).split();assert len(parts)>=count;return [iu(p.decode())for p in parts[:count]]
copper={};new=[];changed=[]
layers=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
for uid,ch in after[3].items():
 kind=K.C.pcbtext.chunk_kind(ch)
 if kind not in ('segment','via','arc'):continue
 if before[3].get(uid)==ch:
  assert uid in baseline;row=dict(baseline[uid])
 else:
  parsed=K.A.G.parse(uid,ch,{});net=identity.raw(parsed['net']);changed.append(uid)
  if kind=='via':
   diameter=values(ch,'size')[0];row={'kind':'via','raw_net':net,'at_IU':values(ch,'at',2),'drill_IU':values(ch,'drill')[0],'diameters_IU':{ly:diameter for ly in layers}}
   if uid not in before[3]:new.append(uid)
  else:
   row={'kind':kind,'raw_net':net,'start_IU':values(ch,'start',2),'end_IU':values(ch,'end',2),'width_IU':values(ch,'width')[0],'layer':parsed['layer']}
   if kind=='arc':row['mid_IU']=values(ch,'mid',2)
 row['locked_yes']=bool(re.search(rb'\(locked\s+yes\)|\(locked\)',ch));row['chunk_sha256']=hashlib.sha256(ch).hexdigest();copper[uid]=row
manifest=H/'coupled-recovery/Q0-DIC-DI6-exact-R157-minimal-sparse-native-replay-manifest-r588/minimal-exact-Q0-DIC-DI6-native-replay-manifest.json';assert sha(manifest)=='1c7fba1adc371ab8b3a4ffc78249cc63c0a2aec113ade7d4e683d21bd2b2b815';m=json.loads(manifest.read_bytes())
required=set(new)|{r['UUID']for r in m['exact_discrete_operations']if r.get('actual_native_NEW_all6_flash_required')}
assert all(uid in copper and copper[uid]['kind']=='via'for uid in required)
for uid in required:assert copper[uid]['drill_IU']>=200000 and min(copper[uid]['diameters_IU'].values())>=500000
mask=N.R157/'actual-full-refill-via-flashes.json';assert sha(mask)=='b64eb5a7ceab4c162699943ed5444554a93c7564cd391eb7dec4ce6e68512ce1'
expected={'board_path':str(candidate.resolve()),'board_sha256':sha(candidate),'copper':copper,'required_NEW_ordinary_all6':sorted(required),'baseline_full_native_mask_file':str(mask.resolve()),'baseline_full_native_mask_SHA256':sha(mask),'baseline_native_board':str(base.resolve()),'baseline_native_board_SHA256':sha(base),'known_inherited_failed_open_gates':'R7/CORE/current/SI/thermal/native DRC held; diagnostic only','adopted':False}
fp=out/'all-copper-expected.json';fp.write_text(json.dumps(expected,indent=1,allow_nan=False)+'\n',encoding='utf-8')
receipt={'status':'COMBINED_SERIALIZED_ALL_CU_INTEGER_IU_AND_LOCK_EXPECTED_LEDGER_READY_NATIVE_OPEN','candidate_SHA256':sha(candidate),'expected_file':str(fp.resolve()),'expected_SHA256':sha(fp),'baseline_copper_count':len(baseline),'candidate_copper_count':len(copper),'changed_copper_count':len(changed),'new_via_count':len(new),'required_NEW_all6_count':len(required),'all_unchanged_Cu_baseline_identity_bound':True,'decimal_native_IU_no_float_rounding':True,'native_jobs':0,'adopted':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps(receipt),flush=True)
