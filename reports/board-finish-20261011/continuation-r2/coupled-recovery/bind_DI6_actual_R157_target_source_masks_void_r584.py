"""Read-only full-native BEFORE binding for the existing DI6 target.

No selected fill or new native job. It binds actual all-net R157 fills and
observed masks, physical all-drill R663 source arrays and exact raw chunks.
Final combined all-net AFTER/native/SI/current qualification remains open.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import R157_native_selected_actual_conversion_r673 as N
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI6-actual-full-R157-target-source-mask-void-binding-r584'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return{'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 N.assert_R157_actual_before();ngf=pin(N.R157/'actual-full-refill-geometry.json','421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b');mf=pin(N.R157/'actual-full-refill-via-flashes.json','b64eb5a7ceab4c162699943ed5444554a93c7564cd391eb7dec4ce6e68512ce1');ng=json.loads(ngf.read_bytes());masks=json.loads(mf.read_bytes())['vias'];gg,missing=N.bound_R663_before_groups({'/LOGIC_GND'});assert not missing;pin(N.R663/'receipt.json','33703477904ca3cc046c80e741f59897c68c04d2c6dd13d307792d006b1bb1cd');pin(N.R663/'actual-R157-native-three-ground-all-drilled-groups.pkl','a24dcae5ae52ae71e548e7f75f2d1ec746324187cf1dc5ab67e01a4ef6f347b7');root=K.root(gg['/LOGIC_GND'],'J11001','2');keys=K.keys(root);refs={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')}
 parent=pin(P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl','ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4');g0,h0,b0,q0,c0=pickle.loads(parent.read_bytes());mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes());hv={v['uuid']:v for v in h['vias']};target=hv['0ff4e506-7bc1-48ad-91fd-aeb598e74c7a'];ret=hv['cb1390c8-49e9-4971-9ee8-740c03e5b93f'];source=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');nativepcb=pin(N.R157/'copy/board.kicad_pcb');orig=K.C.inventory(source.read_bytes())[3];ni=K.C.inventory(nativepcb.read_bytes())[3];nativevia={v['uuid']:v for v in ng['vias']};identity=K.A.N.SourceNets(source.read_bytes());rows=[]
 for v in(target,ret):
  uid=v['uuid'];assert orig[uid]==ni[uid];p=K.A.G.parse(uid,ni[uid],{});assert(p['net'],p['at'],p['d'],p['drill'])==(K.L.norm(v['net']),[v['x'],v['y']],v['d'],v['drill']);n=nativevia[uid];assert(n['net'],n['at'],n['w'],n['drill'])==(v['net'],[v['x'],v['y']],v['d'],v['drill']);f=OUT/(uid+'-exact-unchanged-native.chunk');f.write_bytes(ni[uid]);rows.append({'UUID':uid,'native_exact_original_chunk_SHA256':sha(f),'raw_net':v['net'],'at_mm':[v['x'],v['y']],'diameter_mm':v['d'],'drill_mm':v['drill'],'actual_all_net_R157_flash_layers':masks[uid]})
 assert 'In3.Cu'in masks[target['uuid']]and 'In4.Cu'in masks[ret['uuid']];ann=K.Z.bounded_disk(ret,ret['d']/2).difference(K.Z.bounded_disk(ret,ret['drill']/2));contact=ann.buffer(-.025,quad_segs=128).intersection(refs['In4.Cu']);returnpass=('via',ret['uuid'],'In4.Cu')in keys and not contact.is_empty and contact.area>.005
 zr=next(z for z in h0['zones']if z['uuid']=='c1d27fa1-452b-4e27-985d-5ad23644d800');assert zr['net']=='/LOGIC_GND'and float(zr['clearance_mm'])==.25;radius=target['d']/2+.25+.025;assert radius==.575;scope=K.Z.bounded_disk(target,.575);rp=pin(H/'DI6-positive-current-path-exact-raw-owned-chunks-r576/receipt.json','8cab96a28f7d8a202d8e84e469bb88f7d631d5bb3e619d1c749adb8d8e11383d');pr=json.loads(rp.read_bytes());pf=pin(pr['sparse_packet_file'],'ec40b4ee91ed3e43ead2653dd4a3db5413a9053be7a8e52b7d960a0ef998f72e');op=pickle.loads(pf.read_bytes());local=box(target['x']-1.5,target['y']-1.5,target['x']+1.5,target['y']+1.5);rect,trees=K.F.build({**h0,'vias':[{**v,'flashed':masks[v['uuid']]}for v in h0['vias']],'zones':[]});bodyrows=[];targetgaps=[];othercontributions=[]
 for t in op['tracks']:
  if t['layer']!='In3.Cu':continue
  body=LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128);gap=body.difference(refs['In4.Cu']);localgap=gap.intersection(scope)
  row={'new_UUID':t['uuid'],'actual_all_net_NATIVE_BEFORE_In4_source_gap':info(gap),'gap_in_exact_native_target575_scope':info(localgap),'gap_outside_target_scope':info(gap.difference(scope))};bodyrows.append(row)
  if localgap.is_empty:continue
  f=OUT/(t['uuid']+'-actual-native-BEFORE-target-gap.wkb');f.write_bytes(localgap.wkb);targetgaps.append({'file':str(f.resolve()),'SHA256':sha(f),'new_UUID':t['uuid']})
  for j in trees['In4.Cu'].query(local.buffer(1),predicate='intersects'):
   r=rect['In4.Cu'][int(j)]
   if r['uuid']==target['uuid']or K.L.norm(r['net'])=='/LOGIC_GND':continue
   s=r.get('source');same=h0['domains_normalized'][K.L.norm(r['net'])]==h0['domains_normalized']['/LOGIC_GND'];req=max(.25,.15 if same else .6)+.025
   if r['kind']=='via':mask=K.Z.bounded_disk(s,(s['d']if 'In4.Cu'in s['flashed']else s['drill'])/2+req)
   elif r['kind']=='track'and not s.get('m'):mask=K.Z.bounded_buffer(LineString([s['a'],s['b']]),s['w']/2+req)
   else:mask=K.Z.bounded_buffer(r['shape'],req)
   hit=mask.intersection(localgap)
   if not hit.is_empty:othercontributions.append({'new_UUID':t['uuid'],'other_kind':r['kind'],'other_UUID':r['uuid'],'raw_net':r['net'],'conservative_neighbor_native_clearance_mask_hit':info(hit)})
  for area in h0['rule_areas']:
   if 'In4.Cu'in area['layers']and area.get('no_zones'):
    hit=unary_union(K.L.poly(area['outline'])).intersection(localgap)
    if not hit.is_empty:othercontributions.append({'new_UUID':t['uuid'],'native_no_zones_UUID':area['uuid'],'hit':info(hit)})
 put(OUT/'all_In3_bodies_actual_full_native_BEFORE_source_gaps.json',bodyrows);put(OUT/'target-gap-other-native-copper-or-nozone-contributions.json',othercontributions)
 result={'verdict':'ACTUAL_FULL_NATIVE_R157_EXISTING_DI6_TARGET_MASK_SOURCE_AND_OWNVOID_BEFORE_BINDING_PASS_AFTER_OPEN'if returnpass and targetgaps and not othercontributions else'ACTUAL_NATIVE_TARGET_MASK_SOURCE_VOID_BINDING_REQUIRES_REVIEW','exact_native_original_target_return_rows':rows,'actual_before_J1_In4_return_key_rooted':returnpass,'finite_actual_BEFORE_source_annular_interior':info(contact),'native_target_old_zone_UUID':zr['uuid'],'native_old_local_clearance_mm':.25,'exact_no_enlargement_radius_mm':.575,'actual_native_BEFORE_target_gap_rows':targetgaps,'conservative_other_native_neighbor_or_nozone_contribution_count':len(othercontributions),'all_other_native_root_reference_gaps_retained':bodyrows,'only_actual_full_all_net_R157_fill_used_not_selected_blank_cache':True,'source_and_mask_gates_NOT_changed_or_forced':True,'all_current_AFTER_new_apertures_actual_native_foreign_source_gain_all_baseline_refs_DRC_SI_current':'OPEN; one later combined all-net refill under root after CORE repair, no selected trial','input_SHA256':pins,'all_raw_historical_CPP210nm_R14_window_R368_CORE_R7_ROOT42_planner_failures_preserved':True,'native_jobs':0,'adopted':False,'board_written':False,'elapsed_seconds':time.monotonic()-st};put(OUT/'receipt.json',result);print('R584_COMPLETE',sha(OUT/'receipt.json'),result['verdict'],'neighbor',len(othercontributions),'return',returnpass,flush=True)
if __name__=='__main__':main()
