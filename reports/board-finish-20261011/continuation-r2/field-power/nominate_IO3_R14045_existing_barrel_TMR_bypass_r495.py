"""Finite no-new-hole IO3 bypass around the exact native converter no-zone.

All discrete/owned foreign Cu is hard. Original foreign filled regions alone
may retreat normally; this nominee grants no contact/current/reference pass.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time,re,hashlib,uuid,math
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
M=H/'R155-FA-plus-IO3-TMR-individual-local-scope-witnesses-r491/model.pkl'
A=H/'R155-FA-plus-IO3-TMR-individual-scopes-source-contact-native-nozone-r493'
D=H.parent/'R155-known-reference-native-diagnostic-r157/measure/project/board.kicad_dru'
O=H/'IO3-R14045-existing-native-barrel-TMR-legal-bypass-nomination-r495'
NET='/IO_3V3';VIA='498e9bfd-bcf6-4711-864a-ddfe55479c3a'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic();assert sha(M)=='c41d00e4c79e6374fbdc5a8167de451fbd4c84f8350cb41935cea3e0ae4a6abf'
 g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q);groups=pickle.loads((A/'fresh-IO3-actual-drilled-groups.pkl').read_bytes())[NET];root=K.root(groups,'R18001','2');target=next(xs for xs in groups if any(r['kind']=='pad'and(r['ref'],str(r['pin']))==('R14045','2')for r in xs));assert K.keys(root).isdisjoint(K.keys(target));via=next(v for v in h['vias']if v['uuid']==VIA);assert(via['d'],via['drill'])==(.6,.3)
 rec,_=F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda n:.15 if dom[L.norm(n)]==dom[NET]else .6;allholes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in h['vias']]+[s for p in h['pads']for s in L.poly(p.get('hole')or[])];holeunion=unary_union(allholes);own_ids={z['uuid']for z in q}
 forbidden=[a for a in h['rule_areas']if a.get('no_zones')];dtext=D.read_text(encoding='utf-8')
 for name,condition,what in re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)\)',dtext):
  if 'zone'not in what.split()or NET in re.findall(r"A.NetName != '([^']+)'",condition):continue
  names=re.findall(r"A.intersectsArea\('([^']+)'\)",condition);assert len(names)==1
  ars=[a for a in h['rule_areas']if a.get('name')==names[0]];assert len(ars)==1;forbidden+=ars
 # Ground reference masks must remain exact whenever their real plane layer is affected.
 old=pickle.loads((H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl').read_bytes());protect={'In1.Cu':[],'In4.Cu':[]}
 for net,ref,pin in K.ROOTS[:3]:
  rr=K.source_refs(K.root(old[net],ref,pin))
  for t in c['tracks']:
   if t['layer']not in K.MAP:continue
   supported=L.body(t).intersection(rr[t['layer']]);layer=K.MAP[t['layer']]
   if not supported.is_empty:protect[layer].append(N.bounded_buffer(supported,max(.15,gap(net))+.0251))
 rows=[];accepted=None
 for layer in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu'):
  source=unary_union([r['shape']for r in root if r['layer']==layer]);sink=unary_union([r['shape']for r in target if r['kind']=='via'and r['uuid']==VIA and r['layer']==layer]);assert not sink.is_empty
  for window_mm in (20.,40.):
   window=box(via['x']-window_mm,via['y']-window_mm,via['x']+window_mm,via['y']+window_mm);outline=unary_union(L.poly(h['outline'])).buffer(-.525).intersection(window);obstacles=[]
   for r in rec[layer]:
    if L.norm(r['net'])==NET or not r['shape'].intersects(window.buffer(1)):continue
    if r['kind']=='via':s=N.bounded_disk(r['source'],r['source']['d']/2+gap(r['net'])+.0251)
    elif r['kind']=='track'and not r['source'].get('m'):s=N.bounded_buffer(LineString([r['source']['a'],r['source']['b']]),r['source']['w']/2+gap(r['net'])+.0251)
    else:s=N.bounded_buffer(r['shape'],gap(r['net'])+.0251)
    obstacles.append(lit(s))
   for z in q:
    if z['layer']!=layer or L.norm(z['net'])==NET:continue
    req=max(.15,float(z.get('clearance_mm',.15)),gap(z['net']))+.0251
    for role in ('shape','zone_outline_shape'):
     if z[role].intersects(window.buffer(1)):obstacles.append(lit(N.bounded_buffer(z[role],req)))
   for z in c['zones']:
    if z['uuid']not in own_ids or L.norm(z['net'])==NET or layer not in z['fills']:continue
    for sh in L.poly(z['fills'][layer]):
     if sh.intersects(window.buffer(1)):obstacles.append(lit(N.bounded_buffer(sh,max(.15,float(z['clearance_mm']),gap(z['net']))+.0251)))
   for area in forbidden:
    if layer in area['layers']:
     sh=unary_union(L.poly(area['outline']))
     if sh.intersects(window.buffer(1)):obstacles.append(lit(N.bounded_buffer(sh,.0251)))
   obstacles+=protect.get(layer,[])
   for v in h['vias']:
    if L.norm(v['net'])==NET:continue
    pt=Point(v['x'],v['y'])
    if pt.intersects(window.buffer(1)):obstacles.append(lit(N.bounded_disk(v,v['drill']/2+.2751)))
   for p in h['pads']:
    if not p.get('npth'):continue
    for sh in L.poly(p.get('hole')or[]):
     if sh.intersects(window.buffer(1)):obstacles.append(lit(N.bounded_buffer(sh,.2751)))
   free=lit(outline).difference(unary_union(obstacles));freefile=O/(layer+'-'+str(window_mm)+'-exact-hard-body-free.wkb');freefile.write_bytes(free.wkb)
   for width in (1.,.5,.3):
    center=free.buffer(-width/2-.0000001);faces=[f for f in RF.parts(center)if f.intersects(sink)and f.intersects(source)];row={'layer':layer,'window_mm':window_mm,'core_width_mm':width,'source_to_target_free_face_count':len(faces),'native_original_foreign_fill_soft_only':True}
    for face in sorted(faces,key=lambda f:f.distance(Point(via['x'],via['y']))):
     src=face.intersection(source.buffer(-.03));dst=face.intersection(sink)
     if src.is_empty or dst.is_empty:continue
     aa,bb=nearest_points(dst,src);start=tuple(aa.coords[0]);end=tuple(bb.coords[0]);points,proof=T.route(face,start,end);line=LineString(points);body=lit(N.bounded_buffer(line,width/2));assert free.covers(body)
     src_overlap=body.intersection(source).area;dst_overlap=body.intersection(sink).area
     if src_overlap<=0 or dst_overlap<=0:continue
     # Own existing plated holes are voids only in physical Cu, never in native intended outlines.
     physical=body.difference(holeunion);uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'IO3-R14045-TMR-r495:'+layer+':'+str(points)));new={'uuid':uid,'net':NET,'layer':layer,'shape':physical,'zone_outline_shape':body,'priority':124,'clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3,'purpose':'Restore retained R14045 IO3 branch around exact native TMR forbidden area','prospective_not_native':True}
     accepted={'q':new,'path':points,'proof':proof,'source_overlap_mm2':src_overlap,'target_existing_native_annular_overlap_mm2':dst_overlap,'layer':layer,'core_width_mm':width,'length_mm':line.length,'body_exact_hard_free_covered':True,'existing_target_via':via,'native_own_barrel_center_inside_intended':body.covers(Point(via['x'],via['y']))};row['nominee']=accepted.copy();row['nominee'].pop('q');break
    rows.append(row);put(O/'checkpoint.json',rows);print('R495 case',layer,window_mm,width,len(faces),'ACCEPTED_GEOMETRY'if accepted else'NO_GEOMETRY',flush=True)
    if accepted:break
   if accepted:break
  if accepted:break
 if accepted:(O/'only-new-IO3-bypass-q-nominee.pkl').write_bytes(pickle.dumps(accepted,protocol=5))
 put(O/'receipt.json',{'status':'GEOMETRIC_NOMINEE_ONLY_FULL_SOURCE_CONTACT_REFERENCE_CURRENT_NATIVE_OPEN'if accepted else'FINITE_NO_GEOMETRIC_NOMINEE','base_model_SHA256':sha(M),'source_groups_SHA256':sha(A/'fresh-IO3-actual-drilled-groups.pkl'),'cases':rows,'new_holes':0,'new_tracks':0,'original_Cu_or_outline_changes':0,'nominee_file_SHA256':sha(O/'only-new-IO3-bypass-q-nominee.pkl')if accepted else None,'foreign_original_fill_withdrawal_and_all_direct_source_oldref_gates':'OPEN','no_fake_MAP_shadow_or_equal_current_sharing':True,'all_prior_R491_contact_and_inherited_FAIL_flags_retained':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R495 receipt',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
