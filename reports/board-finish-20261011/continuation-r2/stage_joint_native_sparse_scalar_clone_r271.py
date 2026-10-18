"""Disposable exact R157 clone plus only the scoped joint copper/FP/FG patch."""
import hashlib,json,sys,shutil
from pathlib import Path
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from verify_source import parse,children,child,atom
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb';assert sha(source)=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38';raw=source.read_bytes();iv=K.C.inventory(raw)
cu=H/'U10003-HOST-joint-exact-native-Cu-and-attested-pose-packet-r263';rp=cu/'receipt.json';assert sha(rp)=='d037415a7ea492edfc89541369b121815e561633972b484d1c0a100ac80a23c5';r=json.loads(rp.read_bytes());op=cu/'exact-native-discrete-and-pose-operation.json';assert sha(op)==r['operation_ledger_SHA256'];rows=json.loads(op.read_bytes())
zones=H/'U10003-HOST-two-new-FG-only-exact-native-integer-profile-r267/receipt.json';assert sha(zones)=='48736ecadfa2c27a71b0ad82e21766eb92c4194327bc307b7d09700a1fae458b';zr=json.loads(zones.read_bytes());new={};removed={};replaced={};newcu=[];zspec=[]
for row in rows:
 uid=row['uuid'];action=row['action']
 if action=='replace_footprint_root_pose_only':
  before=Path(row['before_file']);after=Path(row['after_file']);assert sha(before)==row['before_SHA256']and sha(after)==row['after_SHA256'];assert iv[3][uid]==before.read_bytes();replaced[uid]=after.read_bytes();continue
 p=Path(row['file']);assert sha(p)==row['SHA256'];ch=p.read_bytes()
 if action=='remove':assert iv[3][uid]==ch;removed[uid]=ch
 else:assert action=='add'and uid not in iv[3];new[uid]=ch;pa=K.A.G.parse(uid,ch,{});curow={k:pa[k]for k in (('kind','net','layer','w','a','b')if pa['kind']=='segment'else('kind','net','at','d','drill'))};newcu.append({**curow,'uuid':uid,'raw_net':atom(parse(ch.decode()),'net'),'locked':row['locked_yes']})
for z in zr['rows']:
 uid=z['UUID'];p=Path(z['chunk_file']);assert sha(p)==z['chunk_SHA256']and uid not in iv[3]and uid not in new;new[uid]=p.read_bytes();a=parse(p.read_text());rings=[[[int(round(float(v[1])*1e6)),int(round(float(v[2])*1e6))]for v in child(poly,'pts')[1:]]for poly in children(a,'polygon')]
 zspec.append({'uuid':uid,'raw_net':z['net'],'layer':z['layer'],'rings_IU':rings,'declared_native_settings':{'priority':126,'local_clearance_IU':150000,'minimum_thickness_IU':150000,'thermal_gap_IU':150000,'thermal_spoke_IU':300000,'island_removal_mode':1}})
assert (len(removed),len(replaced),len(newcu),len(zspec))==(6,1,17,2)
candidate=raw
for uid,ch in removed.items():assert candidate.count(ch)==1;candidate=candidate.replace(ch,b'',1)
for uid,ch in replaced.items():old=iv[3][uid];assert candidate.count(old)==1;candidate=candidate.replace(old,ch,1)
at=candidate.rfind(b')');assert at>=0;candidate=candidate[:at]+b''.join(new.values())+candidate[at:];afteriv=K.C.inventory(candidate)
assert set(afteriv[3])==set(iv[3])-set(removed)|set(new)
assert all(afteriv[3][u]==ch for u,ch in iv[3].items()if u not in removed and u not in replaced)
assert all(afteriv[3][u]==ch for u,ch in {**new,**replaced}.items())
OUT=H/'U10003-HOST-R157-exact-sparse-native-API-clone-r271';assert not OUT.exists();OUT.mkdir();copy=OUT/'copy';copy.mkdir();pcb=copy/'board.kicad_pcb';pcb.write_bytes(candidate)
for suffix in('.kicad_pro','.kicad_dru'):
 p=source.with_suffix(suffix);assert p.exists();shutil.copy2(p,pcb.with_suffix(suffix));assert sha(p)==sha(pcb.with_suffix(suffix))
spec={'candidate_sha256':sha(pcb),'source_native_file':str(source.resolve()),'source_native_SHA256':sha(source),'zones':zspec,'removed_original_Cu_UUIDs':sorted(removed),'new_Cu':newcu,'R10007_pose':[207.5,141.717,180.0],'R10007_native_attestation_file':str((H/'R10007-exact-native-B-pose-and-pad-mask-attestation-r237/receipt.json').resolve()),'R10007_native_attestation_SHA256':'07e29a3b923c4c8a0a73a2704d32939a5bcd10d7b712cba589639ec34b914a7d','all_inherited_R157_mask_reference_TMR_and_eight_overlap_failures':'RETAINED'};sp=OUT/'expected-native-API.json';sp.write_text(json.dumps(spec,indent=1)+'\n')
result={'status':'EXACT_SPARSE_R157_NATIVE_CLONE_READY_API_FILL_OPEN','parent_SHA256':sha(source),'candidate_SHA256':sha(pcb),'Cu_recipe_SHA256':sha(rp),'zone_recipe_SHA256':sha(zones),'native_spec_SHA256':sha(sp),'original_Cu_deletes':6,'new_tracks':13,'new_vias':4,'new_zones':2,'root_FP_replacements':1,'all_other_native_source_chunks_byte_identical':True,'all_original_zone_outlines_profiles_and_filled_cache_exact':True,'no_live_board_modified':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R271_SPARSE_NATIVE',sha(pcb),'RECEIPT',sha(OUT/'receipt.json'),flush=True)
