"""Exact original LOAD-side power barrels after only hypothetical dc1a middle withdrawal."""
import sys,json,pickle,hashlib,time,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;sha=N.sha
B=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
S=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r295'
O=H/'sbc-power/CORE5-actual-two-original-LOAD-barrels-native-current-source-loop-attribution-r410'
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'WKB_sha256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();N.assert_R157_actual_before();g,h,b,q,c=pickle.loads(B.read_bytes());sb=json.loads((S/'source-binding.json').read_bytes());gf=S/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl';assert sha(gf)==sb['CORE5_actual_groups_SHA256'];groups=pickle.loads(gf.read_bytes());ledger=json.loads((S/'exact-original-middle-withdrawal-physical-source-ledger.json').read_text());right=ledger['two_full_width_source_test_anchors'][1];load=next(xs for xs in groups if any(r['kind']=='track'and r['uuid']==right['uuid']for r in xs));native=K.C.inventory((N.R157/'copy/board.kicad_pcb').read_bytes());viaMap={v['uuid']:v for v in h['vias']};trackMap={t['uuid']:t for t in h['tracks']};ids=sorted({r['uuid']for r in load if r['kind']=='via'});lg,_=N.bound_R663_before_groups({'/LOGIC_GND'});lgRoot=K.root(lg['/LOGIC_GND'],'J11001','2');refs=K.source_refs(lgRoot);rows=[]
 for uid in ids:
  v=viaMap[uid];assert uid in native[3];cu={ly:unary_union([r['shape']for r in load if r['kind']=='via'and r['uuid']==uid and r['layer']==ly])for ly in K.LAYERS};oldContacts=[]
  for r in load:
   if r['kind']=='via'and r['uuid']==uid or r['layer']not in cu:continue
   hit=r['shape'].intersection(cu[r['layer']])
   if hit.is_empty:continue
   oldContacts.append({'UUID':r['uuid'],'kind':r['kind'],'layer':r['layer'],'actual_contact':ds(hit),'native_current_track':trackMap.get(r['uuid'])})
  refRows={}
  cap=Point(v['x'],v['y']).buffer(v['d']/2+.275,quad_segs=128)
  for ly in('F.Cu','In3.Cu','B.Cu'):
   body=cu[ly];raw=body.difference(refs[ly]);outside=body.difference(cap).difference(refs[ly]);refRows[ly]={'raw_annulus_reference_gap':ds(raw),'only_exact_native_own_radius_mm':v['d']/2+.275,'body_outside_inner_exact_cap_reference_gap':ds(outside),'finite_incoming_current_and_terminal_boundary_transfer':'OPEN'}
  returns=[]
  for gv in h['vias']:
   if L.norm(gv['net'])!='/LOGIC_GND':continue
   distance=Point(gv['x'],gv['y']).distance(Point(v['x'],v['y']))
   if not .9<=distance<=1:continue
   overlap={}
   for ly in('In1.Cu','In4.Cu'):
    ann=unary_union([r['shape']for r in lgRoot if r['kind']=='via'and r['uuid']==gv['uuid']and r['layer']==ly]);fill=unary_union([r['shape']for r in lgRoot if r['kind']=='fill'and r['layer']==ly]);overlap[ly]=ann.intersection(fill).area
   if all(x>0 for x in overlap.values()):returns.append({'UUID':gv['uuid'],'xy_mm':[gv['x'],gv['y']],'pair_mm':distance,'actual_both_J1_SOURCE_annulus_plane_overlap_mm2':overlap,'original_native_UUID':gv['uuid']in native[3]})
  row={'UUID':uid,'xy_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'exact_original_native_chunk_sha256':hashlib.sha256(native[3][uid]).hexdigest(),'actual_current_LOAD_Cu_annulus_by_layer':{ly:ds(s)for ly,s in cu.items()},'old_actual_incoming_native_contacts':oldContacts,'existing_actual_ordinary_LG_returns':returns,'actual_source_LG_reference_and_exact_own_cap_diagnostics':refRows,'actual_SOURCE_CORE5_after_middle_withdrawal':False,'actual_LOAD_oldkeys_preservation_and_power_current_plating_SI_thermal':'OPEN'};rows.append(row);print('R410_LOAD_BARREL',uid,row['xy_mm'],row['diameter_drill_mm'],'returns',len(returns),flush=True)
 put(O/'only-two-original-actual-LOAD-port-native-annuli-incoming-widths-source-LG-returns.json',rows);put(O/'receipt.json',{'verdict':'ORIGINAL_EXISTING_LOAD_BARREL_ATTRIBUTION_NO_NEW_PORT_OR_TRACE_NOMINATION','actual_SOURCE_graph_R295_cache_SHA256':sha(gf),'actual_LOAD_retained_layer_keys':len(K.keys(load)),'original_LOAD_via_count':len(rows),'two_actual_existing_LOAD_barrels_are_distinct_from_R295_new_right_port':True,'all_original_SOURCE_and_LOAD_discrete_holes_flashes_anchor_and_fieldplanes_unchanged':True,'full1p25_In3_existing_LOAD_to_existing_SOURCE_body_and_finite_transfer':'OPEN','old_branch_track_width_current_bottlenecks_not_inferred_from_net_identity':True,'original_locked_dc1a_current_board_not_modified':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R410',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc()})
  raise
