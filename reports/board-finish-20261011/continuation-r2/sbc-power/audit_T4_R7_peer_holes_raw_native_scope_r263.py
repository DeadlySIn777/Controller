"""Independent final local safeguards/peer capsules on frozen R262 stages.

Real drill-subtracted new-copper references, native rule/raw-net binding and
hard DIC/C1022 bodies are checked. No qualification/adoption follows.
"""
import hashlib,json,pickle,sys,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import guarded_power_projection_r44 as Z
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import physical_reference_losses_r3_zero_r208 as RF
O=H/'sbc-power/T4-R7-R262-independent-peer-hole-native-rule-source-scope-r263'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 assert not O.exists();O.mkdir();parent=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r262';stage=parent/'T4-plus-R7';mp=stage/'model.pkl';assert mp.exists();cr=json.loads((stage/'construction-receipt.json').read_text());assert sha(mp)==cr['model_sha256'];g,h,b,q,c=pickle.loads(mp.read_bytes());before=pickle.loads((H/'coupled-recovery/CORE-R112-per-polygon-immutable-owned-construction-r250/model.pkl').read_bytes())[4]
 deltas=[pickle.loads((H/'sbc-power'/p).read_bytes())for p in('T4-duplicate-CORE5-fullwidth-detour-nominee-r256/proposed-discrete.pkl','R7-NW-fullwidth-two-B-trunk-detour-nominations-r259/first-nominee-discrete.pkl')];tracks=[t for d in deltas for t in d['tracks']];nv=[v for d in deltas for v in d['vias']];removed={uid for d in deltas for uid in d['removed_original_track_UUIDs']};old={}
 for net,layer in{(L.norm(t['net']),t['layer'])for t in before['tracks']if t['uuid']in removed}:old[net,layer]=unary_union([Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2)for t in before['tracks']if t['uuid']in removed and(L.norm(t['net']),t['layer'])==(net,layer)])
 pp=H/'coupled-recovery/DIC-C1022-exact-R250-current-construction-r256/new-owned-discrete.pkl';assert sha(pp)=='bb1e5159bd82b520150b0b40834b6cff7714458ba5a0356f826c9fef28ea36c3';peer=pickle.loads(pp.read_bytes());put(O/'peer-packet-shape-keys.json',list(peer))
 pt=peer.get('tracks',peer.get('new_tracks',[]));pv=peer.get('vias',peer.get('new_vias',[]));assert len(pt)==21 and len(pv)==5
 source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=A.N.SourceNets(source.read_bytes());assert all(identity.raw(L.norm(x['net']))==x['net']for x in tracks+nv+pt+pv);dru=H/'sbc-native-contract-r1/copy/board.kicad_dru';assert sha(dru)=='159c4614968368a7d88946cc71cc341f886fd22b356ced1d0738252dbeb65fe4'
 dom=h['domains_normalized'];gap=lambda a,b:.15 if dom.get(L.norm(a))==dom.get(L.norm(b))else .6;checks=[];errors=[];inherited=[]
 holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']+pv]+[(p['uuid'],p['net'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for uid,net,sh in holes]);outline=unary_union(L.poly(h['outline'])).buffer(-.525);reserved,exempt=A.reservations()
 for x in tracks+nv:
  via='d'in x;axis=Point(x['x'],x['y'])if via else LineString([x['a'],x['b']]);r=x['d']/2 if via else x['w']/2;body=Z.bounded_buffer(axis,r);prior=old.get((L.norm(x['net']),x.get('layer')));nov=body.difference(prior)if prior is not None else body;layers=K.LAYERS if via else[x['layer']]
  if not outline.covers(body):errors.append({'kind':'native_edge','UUID':x['uuid']})
  for rule in h['rule_areas']:
   if set(layers)&set(rule['layers'])and rule.get('no_vias'if via else'no_tracks')and any(body.distance(sh)<.025 for sh in L.poly(rule['outline'])):errors.append({'kind':'native_rule_area','UUID':x['uuid'],'rule_UUID':rule['uuid']})
  for rule in reserved['keepouts']:
   if L.norm(x['net'])not in exempt.get(rule['name'],set())and set(layers)&set(rule['layers'])and any(body.distance(sh)<.025 for sh in L.poly(rule['outline'])):errors.append({'kind':'frozen_reservation','UUID':x['uuid'],'rule':rule['name']})
  if not via:
   for j in ht.query(body.buffer(.285),predicate='intersects'):
    uid,net,sh=holes[int(j)]
    if L.norm(net)==L.norm(x['net']):continue
    d=axis.distance(sh)-r-.005;ng=nov.distance(sh)-.005 if not nov.is_empty else None;row={'kind':'track_every_foreign_hole','UUID':x['uuid'],'foreign_UUID':uid,'guarded_full_body_gap_mm':d,'guarded_novel_body_gap_mm':ng,'required_mm':.275,'inherited_unchanged_original_anchor_only':d<.275 and(ng is None or ng>=.275)};checks.append(row)
    if d<.275 and ng is not None and ng<.275:errors.append(row)
    if row['inherited_unchanged_original_anchor_only']:inherited.append(row)
  for y in pt+pv:
   yvia='d'in y
   if not via and not yvia and x['layer']!=y['layer']:continue
   if L.norm(y['net'])==L.norm(x['net']):continue
   ya=Point(y['x'],y['y'])if yvia else LineString([y['a'],y['b']]);yr=y['d']/2 if yvia else y['w']/2;d=axis.distance(ya)-r-yr;req=gap(x['net'],y['net'])+.025;row={'kind':'hard_DIC_C1022_peer_capsule','UUID':x['uuid'],'peer_UUID':y['uuid'],'full_true_gap_mm':d,'required_mm':req};checks.append(row)
   if d<req:errors.append(row)
 groups=pickle.loads((stage/'actual-drilled-groups.pkl').read_bytes());lg=K.root(groups['/LOGIC_GND'],'J11001','2');refs=K.source_refs(lg);newholeids={v['uuid']for v in nv};nativeholes=[sh for uid,net,sh in holes if uid not in newholeids];context=STRtree(nativeholes);cutnew=[Z.bounded_disk(v,v['drill']/2+.00000002)for v in nv];newrefs=[]
 for t in tracks:
  full=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);actual=full.difference(unary_union([nativeholes[int(i)]for i in context.query(full,predicate='intersects')]+[sh for sh in cutnew if sh.intersects(full)]));prior=old.get((L.norm(t['net']),t['layer']));novel=actual.difference(prior)if prior is not None else actual;fullgap=actual.difference(refs[t['layer']]);ng=novel.difference(refs[t['layer']]);f=O/(t['uuid']+'-actual-drilled-fullbody-reference-gap.wkb');f.write_bytes(fullgap.wkb);nf=O/(t['uuid']+'-actual-drilled-novel-Cu-reference-gap.wkb');nf.write_bytes(ng.wkb);newrefs.append({'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'actual_drilled_fullbody_source_reference_gap_mm2':fullgap.area,'actual_drilled_fullbody_source_reference_gap_empty':fullgap.is_empty,'actual_drilled_only_novel_Cu_source_reference_gap_mm2':ng.area,'actual_drilled_only_novel_Cu_gap_empty':ng.is_empty,'fullgap_sha256':sha(f),'novelgap_sha256':sha(nf),'real_drill_subtraction_no_generic_own_disk_reference_credit':True})
 v=nv[0];ann=Z.bounded_disk(v,v['d']/2).difference(Z.bounded_disk(v,v['drill']/2+.00000002));areas={l:ann.intersection(unary_union([r['shape']for r in lg if r['kind']=='fill'and r['layer']==l])).area for l in K.LAYERS};ground={pin:any(r['kind']=='pad'and(r['ref'],r['pin'])==('U1001',pin)for r in lg)for pin in('T1','T4','R7')};reg=any(r['kind']=='pad'and(r['ref'],r['pin'])==('U2001','4')for r in lg)
 put(O/'native_rules_every_hole_and_hard_peer_checks.json',checks);put(O/'native_rules_every_hole_and_hard_peer_errors.json',errors);put(O/'inherited_unchanged_anchor_every_hole_facts.json',inherited);put(O/'new_actual_drilled_body_source_reference.json',newrefs);receipt={'verdict':'LOCAL_RULE_HOLE_PEER_RAW_NET_SOURCE_SCOPE_PASS_INHERITED_AND_NEW_REFERENCE_GATES_RETAINED'if not errors else'LOCAL_RULE_HOLE_PEER_RAW_NET_SCOPE_FAIL','exact_R262_joint_model_sha256':sha(mp),'exact_DIC_C1022_peer_packet_sha256':sha(pp),'original_native_DRU_sha256':sha(dru),'all_raw_source_net_names_exact':True,'new_ordinary_0p5_0p2_actual_native_U1001_pad_via0p125_authority_preserved':True,'new_via_masks_explicit_prospective_NOT_native_flash_proof':True,'check_count':len(checks),'error_count':len(errors),'new_actual_drilled_body_reference_rows':newrefs,'new_ground_via_actual_finite_source_rooted_fill_annular_Cu_mm2_by_layer':areas,'literal_actual_J1_rooted_FPGA_ground_pads':ground,'literal_U2001_GND4_same_actual_ground_root':reg,'new_ground_body_reference_fail_count':sum(not r['actual_drilled_fullbody_source_reference_gap_empty']for r in newrefs if r['raw_net']=='/LOGIC_GND'),'new_power_body_reference_fail_count':sum(not r['actual_drilled_fullbody_source_reference_gap_empty']for r in newrefs if r['raw_net']!='/LOGIC_GND'),'full_planner_extra_reserve_native_actual_current_transient_and_all_CORE_body_gates':'FAIL_OR_OPEN_RETAINED','native_jobs':0,'board_written':False,'adopted':False,'script_sha256':sha(__file__)};put(O/'receipt.json',receipt);print('R263_COMPLETE',len(errors),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
