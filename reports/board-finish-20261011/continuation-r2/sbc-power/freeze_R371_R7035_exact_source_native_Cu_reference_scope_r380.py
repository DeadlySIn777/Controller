"""Freeze the real R7035 source, native local AST and existing contacts before a move."""
import json,pickle,hashlib,sys,time
from pathlib import Path
from shapely.ops import unary_union
from shapely.geometry import Point
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
from verify_source import parse,children,child,atom
O=H/'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r380'
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=D/'model.pkl';assert sha(mp)=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';g,h,b,q,c=pickle.loads(mp.read_bytes());source=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';sn=parse(source.read_text(encoding='utf-8'));comp=next(x for x in children(child(sn,'components'),'comp')if atom(x,'ref')=='R7035');pins={}
 for net in children(child(sn,'nets'),'net'):
  for node in children(net,'node'):
   if atom(node,'ref')=='R7035':pins[atom(node,'pin')]=atom(net,'name')
 assert set(pins)=={'1','2'};fp=next(f for f in h['footprints']if f['ref']=='R7035');pads=[p for p in h['pads']if p['ref']=='R7035'];assert len(pads)==2 and all(L.norm(p['net'])==L.norm(pins[str(p['num'])])for p in pads);native=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=A.C.inventory(native.read_bytes());chunk=iv[3][fp['uuid']];fn=O/(fp['uuid']+'.exact-original-R7035-native-footprint-chunk');fn.write_bytes(chunk);ast=parse(chunk.decode());assert child(ast,'at')[1:]==[str(fp['x']),str(fp['y'])]or [float(x)for x in child(ast,'at')[1:3]]==[fp['x'],fp['y']];padnodes=children(ast,'pad');assert len(padnodes)==2 and {atom(x,'uuid')for x in padnodes}=={p['uuid']for p in pads};rec,trees=F.build(c,layers={'F.Cu'});contacts=[];neighborcourts=[]
 for p in pads:
  sh=unary_union(L.poly(p['layers']['F.Cu']));hits=[]
  for j in trees['F.Cu'].query(sh,predicate='intersects'):
   rr=rec['F.Cu'][int(j)]
   if rr['uuid']==p['uuid']or L.norm(rr['net'])!=L.norm(p['net']):continue
   intersection=rr['shape'].intersection(sh)
   if not intersection.is_empty:hits.append({'UUID':rr['uuid'],'kind':rr['kind'],'raw_net':rr['net'],'actual_old_pad_contact_type':intersection.geom_type,'actual_old_pad_contact_mm2':intersection.area,'shape_WKB_sha256':hashlib.sha256(rr['shape'].wkb).hexdigest(),'original_native':rr['uuid']in iv[3]})
  contacts.append({'pin':p['num'],'pad_UUID':p['uuid'],'raw_net':p['net'],'xy':[p['x'],p['y']],'smd':p['smd'],'layer_shape_WKB_sha256':hashlib.sha256(sh.wkb).hexdigest(),'retained_old_direct_contacts':hits})
 center=Point(fp['x'],fp['y'])
 for f in h['footprints']:
  if f['ref']=='R7035':continue
  for ps in f['courtyard'].values():
   for sh in L.poly(ps):
    if center.distance(sh)<4:neighborcourts.append({'ref':f['ref'],'UUID':f['uuid'],'courtyard_bounds':list(sh.bounds),'courtyard_WKB_sha256':hashlib.sha256(sh.wkb).hexdigest()})
 groups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K;lg=K.root(groups['/LOGIC_GND'],'J11001','2');ref=unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']=='In1.Cu']);refrows=[]
 for p in pads:
  sh=unary_union(L.poly(p['layers']['F.Cu']));gap=sh.difference(ref);refrows.append({'pin':p['num'],'actual_original_full_SMD_In1_reference_gap_EMPTY':gap.is_empty,'actual_original_reference_gap_mm2':gap.area,'raw_gap_type':gap.geom_type})
 packet={'footprint':fp,'pads':pads,'exact_native_footprint_chunk':chunk,'exact_native_footprint_AST':ast,'source_component_AST':comp,'source_pin_nets':pins,'old_direct_contacts':contacts};(O/'exact-original-R7035-source-native-pose-contact-packet.pkl').write_bytes(pickle.dumps(packet,protocol=5));put(O/'actual-old-pad-direct-Cu-contact-authority.json',contacts);put(O/'hard-neighbor-courtyard-scope.json',neighborcourts);put(O/'actual-original-whole-SMD-source-In1-reference.json',refrows);put(O/'receipt.json',{'verdict':'R7035_EXACT_SOURCE_NATIVE_LOCAL_AST_AND_RETAINED_CONTACT_SCOPE_FROZEN_MOVE_NOT_APPLIED','current_R371_model_sha256':sha(mp),'fresh_source_sha256':sha(source),'native_source_sha256':sha(native),'native_footprint_uuid':fp['uuid'],'native_footprint_chunk_sha256':sha(fn),'source_value':atom(comp,'value'),'source_footprint':atom(comp,'footprint'),'source_pin_nets':pins,'original_pose':{'xy':[fp['x'],fp['y']],'side':fp['side'],'angle':fp.get('angle',fp.get('rot'))},'packet_sha256':sha(O/'exact-original-R7035-source-native-pose-contact-packet.pkl'),'pad_UUIDs_preserved':[p['uuid']for p in pads],'old_contact_counts':[len(r['retained_old_direct_contacts'])for r in contacts],'original_full_SMD_reference_rows':refrows,'source_electrical_function':'Two-terminal passive component with exact source value and nets preserved; relocation changes physical pose only. Source circuit interpretation and full electrical qualification remain separate.','genuine_pose_new_stubs_actual_native_masks_old_source_keys_reference_and_geometry':'OPEN','POWER_D4_or_rule_courtyard_edit':False,'model_source_native_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R380',sha(O/'receipt.json'),atom(comp,'value'),pins,fp,flush=True)
if __name__=='__main__':main()
