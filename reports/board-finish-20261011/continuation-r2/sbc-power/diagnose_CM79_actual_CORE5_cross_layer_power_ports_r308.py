"""Source-bound actual native CORE5 ports and permitted multilayer scope."""
import hashlib,json,pickle,sys,time
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
O=H/'sbc-power/CM79-actual-CORE5-existing-annuli-multilayer-port-authority-r308'
NET='/mc_local_power/CORE_5V';UID='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());src=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(src)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=A.C.inventory(src.read_bytes());old=next(t for t in h['tracks']if t['uuid']==UID);axis=LineString([old['a'],old['b']]);_,groups=K.physical(c,NET,K.hole_context(c));power=next(xs for xs in groups if any(r['kind']=='track'and r['uuid']==UID for r in xs));sourcekeys=K.keys(power);fills={ly:unary_union([r['shape']for r in power if r['layer']==ly and r['kind']=='fill'])for ly in K.LAYERS};rows=[]
 for v in sorted((v for v in h['vias']if L.norm(v['net'])==NET),key=lambda v:Point(v['x'],v['y']).distance(axis)):
  if v['uuid']not in iv[3]:continue
  xy=Point(v['x'],v['y']);annuli={ly:unary_union([r['shape']for r in power if r['kind']=='via'and r['uuid']==v['uuid']and r['layer']==ly])for ly in K.LAYERS};rows.append({'kind':'native_via','UUID':v['uuid'],'raw_net':v['net'],'exact_xy_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'exact_current_body_source_key_layers':[ly for ly in K.LAYERS if('via',v['uuid'],ly)in sourcekeys],'actual_current_finite_annulus_mm2_by_layer':{ly:sh.area for ly,sh in annuli.items()if not sh.is_empty},'actual_current_same_root_fill_contact_mm2_by_layer':{ly:annuli[ly].intersection(fills[ly]).area for ly in K.LAYERS if not annuli[ly].is_empty},'distance_to_original_F_trunk_mm':xy.distance(axis),'distance_to_original_A_B_mm':[xy.distance(Point(old['a'])),xy.distance(Point(old['b']))],'existing_native_chunk_sha256':hashlib.sha256(iv[3][v['uuid']]).hexdigest(),'no_flash_or_hole_modified':True})
 for p in h['pads']:
  if L.norm(p['net'])!=NET or p['smd']or p['npth']:continue
  rr=[r for r in power if r['kind']=='pad'and r['uuid']==p['uuid']];xy=Point(p['x'],p['y']);rows.append({'kind':'native_plated_pad','UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'exact_xy_mm':[p['x'],p['y']],'actual_rooted_finite_annulus_mm2_by_layer':{ly:unary_union([r['shape']for r in rr if r['layer']==ly]).area for ly in K.LAYERS},'distance_to_original_F_trunk_mm':xy.distance(axis),'distance_to_original_A_B_mm':[xy.distance(Point(old['a'])),xy.distance(Point(old['b']))],'no_layer_or_hole_modified':True})
 rows.sort(key=lambda r:r['distance_to_original_F_trunk_mm']);put(O/'all-existing-native-CORE5-actual-root-annuli-and-ports.json',rows);reserve,exempt=A.reservations();rules=[{'name':r['name'],'layers':r['layers'],'exact_CORE5_existing_exemption':NET in exempt.get(r['name'],set()),'declared_exempt_normalized_nets':sorted(exempt.get(r['name'],set()))}for r in reserve['keepouts']if r['name']in('RESERVE_KEEPOUT_PAIR_4','RESERVE_KEEPOUT_PAIR_5','RESERVE_KEEPOUT_PAIR_6','RESERVE_KEEPOUT_PAIR_8')];put(O/'exact-local-power-reservation-layer-authority.json',rules)
 put(O/'receipt.json',{'verdict':'READ_ONLY_SOURCE_BOUND_ACTUAL_NATIVE_POWER_ANNULI_PORT_CENSUS','exact_failed_diagnostic_model_sha256':sha(mp),'source_native_sha256':sha(src),'actual_CORE5_group_count':len(groups),'original_F_trunk_group_actual_layer_key_count':len(sourcekeys),'native_port_count':len(rows),'first24_local_ports':rows[:24],'local_reserved_layer_rules':rules,'full_signed_current_return_capacity_thermal_oldref_and_native':'OPEN_FAIL_RETAINED','no_generic_disk_or_nominal_layer_flag_used_as_source_port':True,'model_source_board_rules_or_annuli_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R308_COMPLETE',sha(O/'receipt.json'),len(rows),flush=True)
if __name__=='__main__':main()
