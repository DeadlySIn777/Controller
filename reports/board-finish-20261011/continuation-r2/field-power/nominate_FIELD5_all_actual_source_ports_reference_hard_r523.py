"""Fresh all-source finite-annulus FIELD5 search; no repeated fixed endpoint.

Read-only on R515. Only failed owned61cb is excluded from source. Original
IO3 fills, all other positive proposals, every actual old track and DC-q
BEFORE-supported reference are hard. Same-domain FG cuts remain nominations.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time,re,hashlib,uuid,math,traceback
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import fast_contacts as F
import tri_route as T
import guarded_declared_settings_projection_r58 as N
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import restore_field_current_mixed_precision_states_r366 as MS
import physical_reference_losses_r3_zero_r208 as RF
from inventory import sha
M=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl'
PORT=H/'FIELD5-failed-In4-withdrawal-actual-source-target-port-census-r521'
S=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368'
D=H.parent/'R155-known-reference-native-diagnostic-r157/measure/project/board.kicad_dru'
O=H/'FIELD5-all-source-finite-annulus-old-reference-hard-nomination-r523'
NET='/motherboard_power_entry/FIELD_5V';FG='/motherboard_motors/FIELD_GND';OLD='61cb8179-7754-5031-bbea-0da464bf816f';VIA='0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3'
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic();assert sha(M)=='4f70c8271d57724e41005d19c178ba597059085e7192955d7605cf20d501f862';assert sha(PORT/'receipt.json')=='b23987f44bec07514632508846981765c8883ed78bb321e1f2a590d4e15e0ee5'
 g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q);groups=pickle.loads((PORT/'actual-FIELD5-groups-with-only-failed-In4-owned-zone-withdrawn.pkl').read_bytes());sourcegroup=K.root(groups,'L11003','2');target=next(xs for xs in groups if any(r['kind']=='via'and r['uuid']==VIA for r in xs));assert K.keys(sourcegroup).isdisjoint(K.keys(target));via=next(v for v in h['vias']if v['uuid']==VIA);raw=via['net'];assert L.norm(raw)==NET
 rec,_=F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda n:.15 if dom[L.norm(n)]==dom[NET]else .6;allholes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in h['vias']]+[s for p in h['pads']for s in L.poly(p.get('hole')or[])];holeunion=unary_union(allholes);ownids={z['uuid']for z in q}
 forbidden=[a for a in h['rule_areas']if a.get('no_zones')];text=D.read_text(encoding='utf-8')
 for name,cond,what in re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)\)',text):
  if'zone'not in what.split()or raw in re.findall(r"A.NetName != '([^']+)'",cond):continue
  names=re.findall(r"A.intersectsArea\('([^']+)'\)",cond);assert len(names)==1;forbidden.append(next(a for a in h['rule_areas']if a.get('name')==names[0]))
 # All unchanged ground arrays under R515 are exact R368 by R517 certificate.
 old=pickle.loads((S/'actual-drilled-current-groups.pkl').read_bytes());bankrefs={net:K.source_refs(K.root(old[net],ref,pin))for net,ref,pin in K.ROOTS[:3]};protect={'In1.Cu':None,'In4.Cu':None}
 def supported_masks(layer,win):
  out=[];regional=win.buffer(2)
  for bank,rr in bankrefs.items():
   req=max(.15,gap(bank))+.0251
   for t in c['tracks']:
    if t['layer']not in K.MAP or K.MAP[t['layer']]!=layer or dom[L.norm(t['net'])]!=dom[bank]:continue
    if not t.get('m'):
     bounds=box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2)
     if not bounds.intersects(regional):continue
    body=L.body(t);supported=body.intersection(rr[t['layer']]).intersection(regional)
    if not supported.is_empty:out.append(lit(N.bounded_buffer(supported,req)))
   for z in q:
    if z['uuid']==OLD or z['layer']not in K.MAP or K.MAP[z['layer']]!=layer or dom[L.norm(z['net'])]!=dom[bank]or not z['shape'].intersects(regional):continue
    supported=lit(z['shape']).intersection(rr[z['layer']]).intersection(regional)
    if not supported.is_empty:out.append(lit(N.bounded_buffer(supported,req)))
  return out
 rows=[];accepted=None;scope_soft=[]
 for layer in ('In3.Cu','In2.Cu','In1.Cu','In4.Cu'):
  source=unary_union([r['shape']for r in sourcegroup if r['layer']==layer]);ann=unary_union([r['shape']for r in target if r['kind']=='via'and r['uuid']==VIA and r['layer']==layer]);assert not ann.is_empty
  for extra in (20.,40.,80.):
   win=box(via['x']-extra,via['y']-extra,via['x']+extra,via['y']+extra);query=win.buffer(2);outline=unary_union(L.poly(h['outline'])).buffer(-.525).intersection(win);obstacles=[];soft=[]
   for r in rec[layer]:
    if L.norm(r['net'])==NET or not r['shape'].intersects(query):continue
    if r['kind']=='via':v=r['source'];s=N.bounded_disk(v,max(v['d']/2+gap(r['net'])+.0251,v['drill']/2+.2751))
    elif r['kind']=='track'and not r['source'].get('m'):t=r['source'];s=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap(r['net'])+.0251)
    else:s=N.bounded_buffer(r['shape'],gap(r['net'])+.0251)
    obstacles.append(lit(s))
   for z in q:
    if z['uuid']==OLD or z['layer']!=layer or L.norm(z['net'])==NET:continue
    if L.norm(z['net'])==FG:soft.append({'UUID':z['uuid'],'raw_net':z['net'],'kind':'OWNED_NEW_SAME_DOMAIN_FG','shape':z['shape']});continue
    req=max(.15,float(z['clearance_mm']),gap(z['net']))+.0251
    for role in ('shape','zone_outline_shape'):
     if z[role].intersects(query):obstacles.append(lit(N.bounded_buffer(z[role],req)))
   for z in c['zones']:
    if z['uuid']==OLD or layer not in z['fills']or L.norm(z['net'])==NET:continue
    sh=unary_union(L.poly(z['fills'][layer])).intersection(query)
    if sh.is_empty:continue
    if L.norm(z['net'])==FG:soft.append({'UUID':z['uuid'],'raw_net':z['net'],'kind':'ACTUAL_SAME_DOMAIN_FG','shape':sh});continue
    # Every original IO3 layer remains hard to prevent the known383-key cut.
    if z['uuid']in ownids or L.norm(z['net'])=='/IO_3V3':obstacles.append(lit(N.bounded_buffer(sh,max(.15,float(z['clearance_mm']),gap(z['net']))+.0251)))
    else:soft.append({'UUID':z['uuid'],'raw_net':z['net'],'kind':'ORIGINAL_FOREIGN_FILL_NORMAL_LOCAL_WITHDRAWAL_ONLY','shape':sh})
   for area in forbidden:
    if layer in area['layers']:
     sh=unary_union(L.poly(area['outline']))
     if sh.intersects(query):obstacles.append(lit(N.bounded_buffer(sh,.0251)))
   for pad in h['pads']:
    if not pad.get('npth'):continue
    for sh in L.poly(pad.get('hole')or[]):
     if sh.intersects(query):obstacles.append(lit(N.bounded_buffer(sh,.2751)))
   if layer in protect:obstacles+=supported_masks(layer,win)
   free=lit(outline).difference(unary_union(obstacles));ff=O/(layer+'-'+str(extra)+'-exact-hard-body-free.wkb');ff.write_bytes(free.wkb)
   for width in (.50,.35,.30):
    center=free.buffer(-(width/2+.0001)/math.cos(math.pi/256),quad_segs=64)
    # Restrict target endpoint to a real annulus within the final cap radius;
    # this preserves native intended centre coverage without a fake landing.
    sink=ann.intersection(Point(via['x'],via['y']).buffer(width/2-.005,quad_segs=128));faces=[f for f in RF.parts(center)if f.intersects(sink)and f.intersects(source)]
    row={'layer':layer,'window_mm':extra,'core_width_mm':width,'all_actual_source_group_used':True,'source_target_same_free_face_count':len(faces),'supported_old_track_and_DC_before_reference_hard':layer in protect,'original_IO3_actual_fill_hard':True};rows.append(row)
    for face in sorted(faces,key=lambda f:f.distance(Point(via['x'],via['y']))):
     src=face.intersection(source.buffer(-.02));dst=face.intersection(sink)
     if src.is_empty or dst.is_empty:continue
     aa,bb=nearest_points(dst,src);points,proof=T.route(face,tuple(aa.coords[0]),tuple(bb.coords[0]));line=LineString(points);body=lit(N.bounded_buffer(line,width/2));assert free.covers(body)
     assert body.covers(Point(via['x'],via['y']))
     physical=body.difference(holeunion);uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'FIELD5-allsource-R523:'+layer+':'+str(points)));new={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':body,'priority':124,'clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3,'purpose':'Replace failedFIELD5 In4 with actual source-group annular bridge','prospective_not_native':True}
     affected=[{'UUID':s['UUID'],'raw_net':s['raw_net'],'kind':s['kind'],'prospective_guard_overlap_mm2':s['shape'].intersection(lit(N.bounded_buffer(body,max(.15,gap(s['raw_net']))+.025))).area}for s in soft if s['shape'].intersects(body.buffer(.8))]
     accepted={'q':new,'path':points,'proof':proof,'source_overlap_mm2':body.intersection(source).area,'target_existing_native_annular_overlap_mm2':body.intersection(ann).area,'layer':layer,'core_width_mm':width,'length_mm':line.length,'exact_hard_free_true_body_covered':True,'existing_target_via':via,'native_own_barrel_center_inside_intended':True,'soft_cut_obligations':affected};row['nominee']={k:v for k,v in accepted.items()if k!='q'};break
    put(O/'checkpoint.json',rows);print('R523',layer,extra,width,len(faces),'NOMINEE'if accepted else'NO_GEOMETRY',flush=True)
    if accepted:break
   if accepted:break
  if accepted:break
 if accepted:(O/'only-one-new-FIELD5-actual-source-port-nominee.pkl').write_bytes(pickle.dumps(accepted,protocol=5))
 put(O/'receipt.json',{'status':'ALL_ACTUAL_SOURCE_FINITE_ANNULUS_NOMINATION_SOURCE_REFERENCE_CURRENT_NATIVE_OPEN'if accepted else'FINITE_ALL_ACTUAL_SOURCE_PORTS_NO_NOMINEE','model_sha256':sha(M),'source_port_census_sha256':sha(PORT/'receipt.json'),'only_failed_owned_In4_withdrawn':OLD,'cases':rows,'nominee_sha256':sha(O/'only-one-new-FIELD5-actual-source-port-nominee.pkl')if accepted else None,'same_domain_FG_and_original_foreign_filled_cuts':'NOT_APPLIED_EXACT_LOCAL_REPLAY_FULLSOURCE_REFERENCE_GATES_REQUIRED','no_holes_native_discrete_rule_design_edits':True,'all_current_IO3_positive_fills_hard':True,'native_fullfilled_finite_contacts_flash_masks_loop_current_thermal':'OPEN','full_field_load_A':.341130981,'routing_reservation_A':.36,'R46513directrefs_and383IO3_FAIL_not_overlaid':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R523 receipt',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'no_native_source_or_model_acceptance':True})
  raise
