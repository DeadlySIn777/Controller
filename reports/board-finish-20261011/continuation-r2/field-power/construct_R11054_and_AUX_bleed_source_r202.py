"""Exact two-track ownership, static FIELD5 strap, current-sized AUX bleed refeed."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import copy,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import regional_guarded_declared_projection_r140 as P
B=H/'R11054-static-strap-AUX-bleed-search-base-r202';assert not B.exists();B.mkdir()
R=H/'R11054-rotated-AUX-source-search-base-r194';assert sha(R/'model.pkl')=='344b9416a4e86e12ca3587d2a4e1439e1ddd943510afcf3f33ae1fa9282827f3';g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z)
Q=H/'R11054-fault-preserving-exact-AUX-wall-r192';d=pickle.loads((Q/'nomination.pkl').read_bytes());withdraw={t['uuid'] for t in d['tracks']};h['tracks']=[t for t in h['tracks'] if t['uuid'] not in withdraw];fp=next(q for q in h['footprints'] if q['ref']=='R11054');fp['rot']=90
trials=json.loads((H/'R11054-coupled-no-hole-FIELD5-AUX-feed-r199/receipt.json').read_text(encoding='utf-8'))['attempts'];rr=trials[0]['FIELD5_route'];assert rr['length_mm']<.628 and rr['width_mm']==.2 and len(rr['points_mm'])==2
strap={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-R11054-static-FIELD5-strap-r202')),'net':rr['raw_net'],'layer':'F.Cu','a':rr['points_mm'][0],'b':rr['points_mm'][1],'w':.2,'locked':True,'prospective_not_native':True};h['tracks'].append(strap)
for q in z:
 for role in ('shape','zone_outline_shape'):
  raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb
late=H.parent/'sbc-power/IO3-group6-wider-existing-port-r193/accepted-zones.pkl';assert sha(late)=='01952e9a9374ac67da080769154bc828cfd6689bff207cb412d9a33d551e4362';b['field_regulated_search_hard_nominees']['planes']+=pickle.loads(late.read_bytes())
monitor=H.parent/'field-monitor-R9026-rotation-source-termination-r66/owned-delta.pkl';assert sha(monitor)=='2669504846249102a6afe479c78f627b7729d0992c48bc64f79a330f431149c5';md=pickle.loads(monitor.read_bytes());b['field_regulated_search_hard_nominees']['discrete']['tracks']+=md['tracks'];b['field_regulated_search_hard_nominees']['discrete']['vias']+=md['vias']
print('R202 exact FIELD5 strap plus owned bleed disconnection projection',flush=True);c,cuts=P.projected(g,h,z)
b['R11054_static_strap_and_AUX_bleed_refeed_search_r202']={'source_model_file':str((R/'model.pkl').resolve()),'source_model_sha256':sha(R/'model.pkl'),'R192_exact_old_two_track_and_FP_ownership_file':str((Q/'receipt.json').resolve()),'R192_sha256':sha(Q/'receipt.json'),'native_root_pose_mm_deg':[221,42.9,90],'new_FIELD5_strap':strap,'FIELD5_R11054_current_upper_A':.0005230769230769231,'AUX_R11055_bleed_current_upper_A':.000052307692307692306,'all_twelve_motor_AUX5_current_unchanged':True,'exact_old_AUX_component_diagnostic_file':str((H/'R11054-AUX-retained-endpoint-groups-r201/receipt.json').resolve()),'exact_old_AUX_component_diagnostic_sha256':sha(H/'R11054-AUX-retained-endpoint-groups-r201/receipt.json'),'native_FP_rotation_AND_old_delete_adapters_REQUIRED':True,'full76_oldcontacts_sources_refs_and_native_gates':'OPEN'}
(B/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,c),protocol=5));(B/'receipt.json').write_text(json.dumps({'model_sha256':sha(B/'model.pkl'),'parent_model_sha256':sha(R/'model.pkl'),'scope':'Construct exact separate R11055 bleed feed without changing AUX source/load/output limits; C5 remains withdrawn'},indent=1)+'\n',encoding='utf-8');(B/'new-FIELD5-static-strap.pkl').write_bytes(pickle.dumps([strap],protocol=5))
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8').replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'","OUT=HERE/'R11054-and-AUX-bleed-source-feed-r202';BASE=HERE/'R11054-static-strap-AUX-bleed-search-base-r202'")
s=s.replace('for bank,net,ref,pin,policy in PORTS:',"for bank,net,ref,pin,policy in [('AUX5B_BLEED','/motherboard_motors/AUX_5V_B','U11014','6',.000052307692307692306)]:")
s=s.replace("returnnet='/motherboard_motors/FIELD_GND' if bank in ('FIELD5','A3V3') else '/motherboard_do/FIELD_B_0V'","returnnet='/motherboard_motors/FIELD_GND'")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'","xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin'))==('R11055','1') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)","construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)")
s=s.replace('controller-regulated-r76/','controller-R11054-AUX5B-bleed-source-r202/').replace('.read_text()',".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
