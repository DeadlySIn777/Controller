"""Concrete complete old-loop replacement, no counterfactual wall credit."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy,uuid
from pathlib import Path
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import complete_geometry_r2 as G
B=H.parent/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112';O=H/'U11025-exact-health-loop-ground-escape-r318';FG='/motherboard_motors/FIELD_GND'
DELETE={'65a27018-bf6d-4c9a-afe9-01fa772e311c','d4d5b9aa-b33a-4350-a843-5c6fd9f36935','77755826-f876-44cd-b805-7cd14f4ce422','ad620043-e26c-4d97-865f-ddd42957541c','6f70ba3f-8623-446b-8427-a210e4c19ff8','eabfe87a-5c24-4e74-a39e-8d3e758e7aaa','7e46856c-37f2-4b41-a013-fef698447188','ce5fab45-4624-43f3-a5e3-58f55eb678d1','713bdbf4-9c3a-41bf-b9fc-61ae5cc9f82c','1ef62b0f-b15e-44ee-9e1d-26b41ad26a1c','21a59b50-0664-4fa0-97dd-761f281a8da0'}
def write(f,v):f.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());pads={q['num']:q for q in h['pads'] if q['ref']=='U11025'};health=pads['4']['net'];ground=pads['2']['net'];removed=[t for t in h['tracks'] if t['uuid'] in DELETE];assert len(removed)==11 and all(t['net']==health and t['layer']=='F.Cu' and t['w']==.2 for t in removed)
 routes=[(health,[(309.3565,153.908),(309.35,151.72),(310.75,151.72),(310.75,153.408),(311.5315,153.408)],.2,'health-loop'),(ground,[(311.0315,154.558),(310.2,154.558),(310.2,152.0)],.2,'ground-escape')];tracks=[]
 for net,pts,w,role in routes:
  for i,(a,bb) in enumerate(zip(pts,pts[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-field-r318-'+role+'-'+str(i))),'net':net,'a':list(a),'b':list(bb),'w':w,'layer':'F.Cu','locked':False})
 hc=copy.deepcopy(h);hc['tracks']=[q for q in hc['tracks'] if q['uuid'] not in DELETE]+tracks;cc=copy.deepcopy(c);cc['tracks']=[q for q in cc['tracks'] if q['uuid'] not in DELETE]+tracks;rec,trees=F.build({**hc,'zones':[]});tm={q['uuid']:q for q in hc['tracks']};vm={q['uuid']:q for q in hc['vias']};checks=[]
 for t in tracks:
  axis=LineString([t['a'],t['b']]);body=axis.buffer(t['w']/2,quad_segs=256)
  for i in trees['F.Cu'].query(body.buffer(.627),predicate='intersects'):
   item=rec['F.Cu'][int(i)]
   if item['net']==t['net']:continue
   req=G.gap(h,t['net'],item['net'])+.025;gap=axis.distance(item['shape'])-t['w']/2
   if item['kind']=='track':other=tm[item['uuid']];gap=axis.distance(LineString([other['a'],other['b']]))-(t['w']+other['w'])/2
   elif item['kind']=='via':v=vm[item['uuid']];gap=axis.distance(Point(v['x'],v['y']))-t['w']/2-v['d']/2
   checks.append({'new_UUID':t['uuid'],'new_raw_net':t['net'],'foreign_UUID':item['uuid'],'kind':item['kind'],'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
  for q in z:
   if q['layer']!='F.Cu' or q['net']==t['net']:continue
   req=max(G.gap(h,t['net'],q['net']),q.get('clearance_mm',.15))+.025;gap=axis.distance(q['shape'])-t['w']/2
   if gap<req+.01:checks.append({'new_UUID':t['uuid'],'foreign_UUID':q['uuid'],'kind':'owned_foreign_plane','required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
  for q in hc['rule_areas']:
   if not q.get('no_tracks') or 'F.Cu' not in q['layers']:continue
   overlap=sum(body.intersection(x).area for x in C.poly(q['outline']))
   if overlap>1e-12:checks.append({'new_UUID':t['uuid'],'foreign_UUID':q.get('uuid',q.get('name')),'kind':'native_or_reserved_no_tracks_requires_exact_applicability','overlap_mm2':overlap,'PASS':False,'rule_area':q})
 oldgroups=pickle.loads((B/'groups.pkl').read_bytes())[FG];oldroot=next(xs for xs in oldgroups if any(i['kind']=='pad' and(i['ref'],i['pin'])==('J11003','2') for i in xs));reference=unary_union([i['shape'] for i in oldroot if i['kind']=='fill' and i['layer']=='In1.Cu']);sourceF=unary_union([i['shape'] for i in oldroot if i['layer']=='F.Cu']);coverage=[]
 for t in tracks:
  body=LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=256);coverage.append({'UUID':t['uuid'],'raw_net':t['net'],'length_mm':LineString([t['a'],t['b']]).length,'actual_J3_rooted_In1_full_body_gap_mm2':body.difference(reference).area,'actual_J3_rooted_F_Cu_contact_mm2':body.intersection(sourceF).area})
 print('R318 exact new tracks',len(tracks),'Cu/errors',len(checks),sum(not q['PASS'] for q in checks),'health refs',sum(q['actual_J3_rooted_In1_full_body_gap_mm2'] for q in coverage if q['raw_net']==health),flush=True)
 write(O/'analytic-checks.json',checks);write(O/'paired-reference-coverage.json',coverage);(O/'proposed-discrete.pkl').write_bytes(pickle.dumps({'tracks':tracks,'vias':[]},protocol=5));write(O/'exact-owned-old-track-rows.json',removed);(O/'model.pkl').write_bytes(pickle.dumps((g,hc,b,z,cc),protocol=5));errors=[q for q in checks if not q['PASS']];r={'verdict':'EXACT_COUPLED_LOOP_CONCRETE_NOMINATION_ANALYTIC_PASS_CONTACT_NATIVE_OPEN' if not errors else 'EXACT_COUPLED_LOOP_NOMINATION_REJECTED_GUARD','base_model_SHA256':sha(B/'model.pkl'),'deleted_original_UUIDs':sorted(DELETE),'new_tracks':6,'new_vias':0,'no_pad_net_or_pose_changed':True,'exact_raw_health_net':health,'exact_raw_ground_net':ground,'analytic_errors':errors,'coverage':coverage,'model_SHA256':sha(O/'model.pkl'),'owned_discrete_SHA256':sha(O/'proposed-discrete.pkl'),'ground_normal_reservation_A':.001,'health_width_preserved_mm':.2,'new_ground_width_mm':.2,'full_source_and_retained_contact_proof':'OPEN','native_fill_DRC_current_reference':'OPEN','board_written':False,'native_jobs':0,'adopted':False};write(O/'receipt.json',r);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'errors':len(errors)}),flush=True)
if __name__=='__main__':main()
