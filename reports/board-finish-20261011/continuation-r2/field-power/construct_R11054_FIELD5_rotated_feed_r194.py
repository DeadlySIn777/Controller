"""Actual FIELD5 source feed for fixed-FAULT R11054 on the exact AUX nominee."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import copy,pickle,json,sys
from pathlib import Path
from shapely import set_precision
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import regional_guarded_declared_projection_r140 as P
B=H/'R11054-rotated-AUX-source-search-base-r194';assert not B.exists();B.mkdir()
R=H/'B3-exact-IO3-preserving-search-base-r189';g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z)
Q=H/'R11054-fault-preserving-exact-AUX-wall-r192';assert sha(Q/'nomination.pkl')=='4ad58ad47943f15351ea01090025c615e2adedffc47ae15eb334718c368077f3';d=pickle.loads((Q/'nomination.pkl').read_bytes());r=json.loads((Q/'receipt.json').read_text(encoding='utf-8'))
oldpad=next(q for q in h['pads'] if q['uuid']==d['pad1']['uuid']);assert oldpad==r['old_pad1'];oldfp=next(q for q in h['footprints'] if q['ref']=='R11054');assert oldfp==r['old_FP'];removed={q['uuid'] for q in r['owned_original_two_tracks']};assert all(next(q for q in h['tracks'] if q['uuid']==o['uuid'])==o for o in r['owned_original_two_tracks'])
h['pads']=[d['pad1'] if q['uuid']==oldpad['uuid'] else q for q in h['pads']];h['footprints']=[d['footprint'] if q['ref']=='R11054' else q for q in h['footprints']];h['tracks']=[q for q in h['tracks'] if q['uuid'] not in removed]+d['tracks']
for q in z:
 for role in ('shape','zone_outline_shape'):
  raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==raw
print('R194 rotated pad and AUX exact candidate projection',flush=True);c,cuts=P.projected(g,h,z)
b['R11054_fixed_FAULT_rotated_supply_and_exact_two_AUX_track_ownership']={'receipt_file':str((Q/'receipt.json').resolve()),'receipt_sha256':sha(Q/'receipt.json'),'nomination_file':str((Q/'nomination.pkl').resolve()),'nomination_sha256':sha(Q/'nomination.pkl'),'old_pad1':oldpad,'new_pad1':d['pad1'],'old_fp':oldfp,'new_fp':d['footprint'],'exact_old_track_deletes':r['owned_original_two_tracks'],'new_tracks':d['tracks'],'native_pose_rotation_requires_exact_ast_adapter':True,'source_BOM_node_roles_and_pin2_contact_limits_unchanged':True}
(B/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,c),protocol=5));(B/'receipt.json').write_text(json.dumps({'model_sha256':sha(B/'model.pkl'),'parent_model_sha256':sha(R/'model.pkl'),'exact_local_nominee_sha256':sha(Q/'nomination.pkl'),'scope':'Search only, source feed/contact/current/native unfinished; old C5 remains withdrawn'},indent=1)+'\n',encoding='utf-8')
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8').replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'","OUT=HERE/'R11054-rotated-FIELD5-source-feed-r194';BASE=HERE/'R11054-rotated-AUX-source-search-base-r194'")
s=s.replace('for bank,net,ref,pin,policy in PORTS:',"for bank,net,ref,pin,policy in [x for x in PORTS if x[0]=='FIELD5']:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'","xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin'))==('R11054','1') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):","for margin in(8.,25.,60.,140.,None):\n    for width in(.35,.5):")
s=s.replace("native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)","construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)")
s=s.replace('controller-regulated-r76/','controller-R11054-FIELD5-source-r194/').replace('.read_text()',".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
