"""Classify actual C10036 native local copper without granting source credit."""
import sys,pickle,json,math,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import audit_c10036_actual_scoped_native_r34 as R
from shapely.geometry import Point
from shapely.ops import unary_union
C,G=A.C,A.G
out=HERE/'c10036-actual-local-native-diagnostic-r35.json';assert not out.exists();started=time.monotonic();cachepath=HERE/'c10036-native-r34-actual-model.pkl';m=pickle.loads(A.read(cachepath));receiptpath=HERE/'c10036-actual-native-reference-independent-r34.json';receipt=json.loads(A.read(receiptpath));assert C.sha(A.read(cachepath))==receipt['saved_actual_model_sha256'];recipe=json.loads(A.read(HERE/'c10036-r25-reference-bridge-recipe-r24.json'));retuid=recipe['new_return_UUID'];targetuid='be3d6ddb-80f4-51c6-a40b-13be7214ceb5';groups=m['groups'];local=next(xs for xs in groups if any(q['kind']=='via' and q['uuid']==retuid for q in xs));refs={l:unary_union([q['shape'] for q in local if q['kind']=='fill' and q['layer']==plane]) for l,plane in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};ann=Point(66.55,94.45).buffer(.25,quad_segs=128).difference(Point(66.55,94.45).buffer(.1,quad_segs=128));rows=[]
for u,ch in recipe['exact_new_chunks'].items():
 q=G.parse(u,ch.encode(),{})
 if q['kind']!='segment' or q['net']==R.GROUND:continue
 body=A.shape(q);lost=body.difference(refs[q['layer']]);vs=R.vertices(lost);radius=max((math.dist(p[:2],(66.55,95.35)) for p in vs),default=0);inside=q['net']==R.GATE and vs and radius<=.575
 rows.append({'uuid':u,'net':q['net'],'layer':q['layer'],'actual_local_paired_component_reference_gap_mm2':lost.area,'own_exact_disk_convex_containment':bool(inside),'maximum_gap_vertex_radius_mm':radius,'exact_own_disk_radius_mm':.575,'radius_expansion_mm':0,'locally_covered_except_exact_own_transition':lost.area<=1e-9 or bool(inside),'source_root_qualification':False})
small=[];big=[]
for n in receipt['unchanged_neighbor_prior_source_reference_losses']:
 (small if n['prior_source_reference_lost_mm2']<=1e-6 else big).append(n)
result={'verdict':'ACTUAL_LOCAL_BODY_AND_PAIRED_PLANE_DIAGNOSTIC_SOURCE_ROOT_STILL_OPEN','actual_native_receipt_sha256':C.sha(A.read(receiptpath)),'actual_local_component_pad_ids':[{'ref':q['ref'],'pin':q['pin'],'uuid':q['uuid']} for q in local if q['kind']=='pad'],'local_return_component_includes_C10036_2':any(q['kind']=='pad' and(q['ref'],q['pin'])==('C10036','2') for q in local),'local_return_component_includes_both_new_vias':all(any(q['kind']=='via' and q['uuid']==u for q in local) for u in(retuid,targetuid)),'actual_local_annular_plane_interior_mm2':{l:r.buffer(-.075).intersection(ann).area for l,r in refs.items()},'new_body_actual_local_reference':rows,'source_J11005_2_root_unresolved':True,'reference_or_SI_PASS':False,'strict_small_baseline_reference_differences':small,'strict_larger_baseline_reference_differences':big,'no_boundary_sliver_waiver':True,'all_proposal_PDNgates_remain_OPEN':True,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started,'native_jobs':0,'board_written':False};out.write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'both_new_same_local_component':result['local_return_component_includes_both_new_vias'],'target_same_local_component':result['local_return_component_includes_C10036_2'],'local_reference':rows,'small':len(small),'big':big}),flush=True)
