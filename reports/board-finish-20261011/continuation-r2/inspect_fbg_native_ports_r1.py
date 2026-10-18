"""Inspect actual inherited source/target flash masks, without granting prospective ports."""
import collections,hashlib,json,pickle
from pathlib import Path
H=Path(__file__).resolve().parent
import sys;sys.path.insert(0,str(H/'field-power'))
import fast_contacts as F
import native_pose_signal_contract as NC
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
mp=H/'sbc-power/core-pocket-outward-round-guards-r69/model.pkl';assert sha(mp)=='48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff'
old,h,b,z,current=pickle.loads(mp.read_bytes());parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
inv=NC.C.inventory(parent.read_bytes());groups=F.graph(current,'/motherboard_do/FIELD_B_0V');rows=[]
for xs in groups:
 named=[q for q in xs if q['kind']=='pad'and q['pin']]
 if not named:continue
 vids={q['uuid']for q in xs if q['kind']=='via'};native=[u for u in vids if u in inv[4]];flags=collections.Counter('REMOVE_UNUSED'if b'remove_unused_layers' in inv[4][u]else'NO_REMOVE_UNUSED_TOKEN'for u in native)
 counts=collections.Counter((q['layer'],q['kind'])for q in xs)
 rows.append({'actual_source_group':any((q['ref'],q['pin'])==('J11005','2')for q in named),'named_pad_count':len({q['uuid']for q in named}),'physical_contacts':len(xs),'physical_by_layer_and_kind':{l+':'+k:n for(l,k),n in counts.items()},'unique_existing_vias':len(vids),'native_existing_via_policy_counts':dict(flags),'actual_source_pad_ids':[q['uuid']for q in named if(q['ref'],q['pin'])==('J11005','2')],'representative_vias':[{'uuid':u,'actual_host_flashed':next(v['flashed']for v in h['vias']if v['uuid']==u),'exact_native_chunk':inv[4][u].decode()}for u in sorted(native)[:3]]})
out=H/'fbg-native-port-inspection-r1.json';assert not out.exists();out.write_text(json.dumps({'verdict':'ACTUAL_EXISTING_PORT_CENSUS_PROSPECTIVE_FLASH_OR_NEW_BARREL_GATES_SEPARATE','groups':rows,'inputs':{str(p.resolve()):sha(p)for p in(Path(__file__),mp,parent,Path(F.__file__))},'no_native_mutation_or_prospective_port_credit':True,'native_jobs':0,'adopted':False},indent=1)+'\n');print(json.dumps([{k:v for k,v in r.items()if k!='representative_vias'}for r in rows]))
