"""Read-only existing-port candidates; actual native LG-local antipads stay hard."""
import hashlib,json,pickle,sys,time
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-native-local-antipad-direct-old-body-disjoint-screen-r320'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-screen.py').write_text(s,encoding='utf-8');mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());ap=H/'sbc-power/CM79-R315-fresh-sparse-current-source-native-reference-audit-r316';assert sha(ap/'receipt.json')=='bb93a32c96d7aab3f624152ae916eb52b128b4c899b4bc97e41cf2c2b230c249';gg=pickle.loads((ap/'actual-drilled-before-groups.pkl').read_bytes());root=K.root(gg['/LOGIC_GND'],'J11001','2');bank={ly:zero(sh)for ly,sh in K.source_refs(root).items()};old=next(t for t in h['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1');oldactual=zero(unary_union([r['shape']for xs in gg[L.norm(old['net'])]for r in xs if r['kind']=='track'and r['uuid']==old['uuid']]));anchors={label:zero(unary_union(L.poly([])))for label in('left','right')}
 for label,a,bb in(('left',old['a'],[116.2,202.35]),('right',[120.1,202.35],old['b'])):anchors[label]=oldactual.intersection(zero(Z.bounded_buffer(LineString([a,bb]),.625))).intersection(bank['F.Cu'])
 saved=H/'sbc-power/CM79-widened-ordinary-power-with-existing-actual-source-LG-port-pairs-r314';assert sha(saved/'receipt.json')=='fb3afa859d483a9cd6e21b496415c5a829904f9617135307e260e8c1b4cb263e';pairs=json.loads((saved/'ordinary-existing-source-port-pair-matrix.json').read_text())['matched'];bodyrows=[];omitted=[];dom=h['domains_normalized'];LG=dom['/LOGIC_GND'];max_native_LG_local=max(float(z['clearance_mm'])for z in c['zones']if z['net']=='/LOGIC_GND');maxradius=max(.375,.25+max(max_native_LG_local,.15)+.025);halo=zero(unary_union([Z.bounded_buffer(Point(rr['power']['x'],rr['power']['y']),maxradius+.000000003)for pp in pairs.values()for rr in pp])).envelope;(O/'conservative-all-candidate-native-antipad-envelope.wkb').write_bytes(halo.wkb)
 for t in c['tracks']:
  if t['layer']!='B.Cu'or t['net']=='/LOGIC_GND'or dom.get(L.norm(t['net']))!=LG:continue
  body=zero(L.body(t));
  if not body.envelope.intersects(halo):omitted.append({'old_track_UUID':t['uuid'],'whole_old_body_envelope_disjoint_from_every_conservative_native_antipad_halo':True});continue
  support=body.intersection(bank['B.Cu'])
  if not support.is_empty:bodyrows.append({'uuid':t['uuid'],'net':t['net'],'shape':support,'body_WKB_sha256':hashlib.sha256(body.wkb).hexdigest(),'BEFORE_supported_WKB_sha256':hashlib.sha256(support.wkb).hexdigest()})
 bt=STRtree([r['shape']for r in bodyrows]);actualbank={ly:[]for ly in('In1.Cu','In4.Cu')}
 for rr in root:
  if rr['kind']=='fill'and rr['layer']in actualbank:actualbank[rr['layer']].append(rr)
 zlocal={z['uuid']:float(z['clearance_mm'])for z in c['zones']};rows=[];accepted={label:[]for label in pairs};planes=[]
 for ly,rrs in actualbank.items():
  for u in sorted({r['uuid']for r in rrs}):planes.append({'source_zone_UUID':u,'layer':ly,'unchanged_native_plane_local_clearance_mm':zlocal[u],'power_to_LOGIC_domain_native_clearance_mm':.15,'full_POWER_via_Cu_radius_mm':.25,'new_reserve_mm':.025,'foreign_hole_to_Cu_minimum_radius_mm':.375,'exact_new_native_antipad_analytic_radius_mm':max(.375,.25+max(zlocal[u],.15)+.025)})
 put(O/'exact-actual-source-plane-local-antipad-authority.json',planes);put(O/'exact-full-body-disjoint-broad-phase-ledger.json',{'frozen_parent_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'halo_envelope_sha256':sha(O/'conservative-all-candidate-native-antipad-envelope.wkb'),'max_native_LG_local_mm':max_native_LG_local,'max_actual_native_antipad_radius_mm':maxradius,'unchanged_full_old_body_direct_BEFORE_reference_intersection':True,'all_omitted_old_B_bodies':omitted})
 for label,candidates in pairs.items():
  for index,rr in enumerate(candidates):
   pv=rr['power'];pt=Point(pv['x'],pv['y']);cuts={};authority=[]
   for ly,rs in actualbank.items():
    pieces=[]
    for u in sorted({r['uuid']for r in rs}):
     rad=max(.375,.25+max(zlocal[u],.15)+.025);cut=zero(Z.bounded_buffer(pt,rad));parts=[r['shape']for r in rs if r['uuid']==u and r['shape'].intersects(cut)]
     if parts:pieces.append(cut.intersection(zero(unary_union(parts))));authority.append({'source_zone_UUID':u,'layer':ly,'native_local_mm':zlocal[u],'full_unchanged_analytic_antipad_radius_mm':rad})
    cuts[ly]=zero(unary_union(pieces))
   drill=zero(Z.bounded_buffer(pt,.10000002));remaining=anchors[label].difference(drill);anchorloss=remaining.intersection(cuts['In1.Cu']);fn=O/(label+'-'+str(index)+'-retained-original-anchor-BEFORE-supported-reference-loss.wkb');fn.write_bytes(anchorloss.wkb);bad=[]
   for j in bt.query(cuts['In4.Cu'],predicate='intersects'):
    tr=bodyrows[int(j)];lost=tr['shape'].intersection(cuts['In4.Cu'])
    if lost.is_empty:continue
    fp=O/(label+'-'+str(index)+'-'+tr['uuid']+'-direct-whole-B-body-BEFORE-supported-loss.wkb');fp.write_bytes(lost.wkb);bad.append({'old_B_track_UUID':tr['uuid'],'raw_net':tr['net'],'full_old_B_body_WKB_sha256':tr['body_WKB_sha256'],'whole_old_B_body_actual_BEFORE_source_supported_WKB_sha256':tr['BEFORE_supported_WKB_sha256'],'loss_empty':False,'literal_loss_type':lost.geom_type,'literal_loss_area_mm2':lost.area,'literal_loss_WKB_sha256':sha(fp),'every_nonempty_dimension_retained_no_private_own_hole_credit':True})
   row={'label':label,'power':pv,'exact_existing_LG_port':rr['existing_actual_source_ground_port']['via'],'ordinary_return_pair_distance_mm':rr['ordinary_centre_distance_mm'],'all_actual_native_source_zone_antipad_radii':authority,'remaining_old_F_anchor_BEFORE_supported_loss_EMPTY':anchorloss.is_empty,'remaining_old_F_anchor_BEFORE_supported_loss_type':anchorloss.geom_type,'remaining_old_F_anchor_BEFORE_supported_loss_area_mm2':anchorloss.area,'remaining_old_F_anchor_loss_sha256':sha(fn),'direct_whole_old_B_body_before_supported_reference_losses':bad,'nominated':anchorloss.is_empty and not bad};rows.append(row)
   if row['nominated']:accepted[label].append(row)
 put(O/'all-existing-return-port-native-local-clearance-and-supported-reference-screen.json',rows);put(O/'receipt.json',{'verdict':'SOURCE_SUPPORTED_OLD_CU_SAFE_ORDINARY_POWER_PORT_PAIRS_PENDING_FULL_REQUALIFICATION'if all(accepted.values())else'NO_SOURCE_SUPPORTED_OLD_CU_SAFE_TWO_ENDED_POWER_PORT_NOMINEE_IN_DECLARED_EXISTING_PORT_PAIRS','model_sha256':sha(mp),'R316_before_graph_sha256':sha(ap/'actual-drilled-before-groups.pkl'),'R314_existing_port_receipt_sha256':sha(saved/'receipt.json'),'full_old_B_supported_body_count':len(bodyrows),'tested_existing_source_pair_counts':{label:len(p)for label,p in pairs.items()},'remaining_anchor_reference_FAIL_count':sum(not r['remaining_old_F_anchor_BEFORE_supported_loss_EMPTY']for r in rows),'direct_old_B_reference_FAIL_pair_count':sum(bool(r['direct_whole_old_B_body_before_supported_reference_losses'])for r in rows),'nominee_counts':{label:len(p)for label,p in accepted.items()},'native_LG_local_clearance_domain_copper_diameter_aperture_rules_or_signed_current_changes':0,'all_known_cm50_field_io3_CORE_current_native_failed_gates_retained':True,'no_model_source_board_native_job_or_adoption':True,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R320_COMPLETE',sha(O/'receipt.json'),len(rows),{k:len(v)for k,v in accepted.items()},flush=True)
if __name__=='__main__':main()
