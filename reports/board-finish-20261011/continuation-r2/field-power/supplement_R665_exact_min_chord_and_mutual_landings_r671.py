"""Correct the R665 maximum-radius label; retain nominal/min-chord distinction."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,math,itertools
from pathlib import Path
from shapely.geometry import Point
H=Path(__file__).resolve().parent
P=H/'R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665'
OUT=H/'R665-exact-min-chord-label-and-mutual-landing-supplement-r671'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
assert not OUT.exists();OUT.mkdir();assert sha(P/'receipt.json')=='f804da80445f226e7e10cfd9660b35bf6ba7dd3b935b2dbb7a542c32769cbabd'
pk=P/'only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl';assert sha(pk)=='4d7f1ea367403ac47c214970e5dd637f8672917fb8cd2360cc5eb18c325885d5';q=pickle.loads(pk.read_bytes());rows=json.loads((P/'all-23-local-landing-attempts-and-raw-failures.json').read_bytes());by={r['landing_UUID']:r for r in rows};width=[];pairs=[];errors=[]
for z in q:
 r=by[z['uuid']];axis=Point(*r['at_mm']);lo=axis.distance(z['zone_outline_shape'].exterior);hi=max(axis.distance(Point(x,y))for x,y in z['zone_outline_shape'].exterior.coords);assert hi==r['actual_polygon_max_radius_mm'];width.append({'UUID':z['uuid'],'old_via_UUID':z['existing_source_via_UUID'],'layer':z['layer'],'exact_intended_min_chord_radius_mm':lo,'exact_intended_max_vertex_radius_mm':hi,'exact_256_edge_min_chord_radial_annular_width_mm':lo-.1,'nominal_native_via_annular_radial_width_mm':.15,'R665_mislabeled_nominal_width_was_max_vertex_radius_minus_drill_radius_mm':r['nominal_barrel_annular_radial_width_mm'],'raw_min_chord_below_150um_mm':max(0.,.25-lo),'no_polygon_width_or_native_minfeature_capacity_claim':True,'native_CPP_flash_and_real_source_annulus':'OPEN_R667_R669'})
for a,b in itertools.combinations(q,2):
 if a['layer']!=b['layer']:continue
 if a['net']==b['net']:req=0.;inter=a['zone_outline_shape'].intersection(b['zone_outline_shape']);bad=not inter.is_empty
 else:req=.625;inter=a['shape'].intersection(b['shape']);bad=a['shape'].distance(b['shape'])<req
 row={'a':a['uuid'],'b':b['uuid'],'layer':a['layer'],'same_raw_net':a['net']==b['net'],'physical_gap_mm':a['shape'].distance(b['shape']),'required_domain_plus_planner_mm':req,'same_raw_native_intended_overlap_EMPTY':inter.is_empty if req==0 else None,'error':bad};pairs.append(row)
 if bad:errors.append(row)
put(OUT/'exact-minimum-chord-width-raw-distinction.json',width);put(OUT/'new-new-landing-mutual-guards.json',pairs);put(OUT/'receipt.json',{'status':'MUTUAL_GUARDS_PASS_EXACT_CHORD_WIDTH_RAW_SHORTFALL_NATIVE_CPP_MINFEATURE_SOURCE_PENDING'if not errors else'MUTUAL_GUARDS_REPAIR_REQUIRED','R665_receipt_SHA256':sha(P/'receipt.json'),'proposal_packet_SHA256':sha(pk),'all23_min_chord_widths_explicit':True,'R665_max_radius_label_error_corrected_without_geometry_change':True,'literal_nominal_150um_not_promoted_from_polygon_chords':True,'new_new_pairs_checked':len(pairs),'new_new_errors':errors,'geometry_chunks_models_masks_rules_UNCHANGED':True,'native_min_feature_barrel_current_thermal_SI_source':'OPEN_PENDING_ACTUAL_CPP_RESULT','native_jobs':0,'adopted':False});print('R671_COMPLETE',sha(OUT/'receipt.json'),'errors',len(errors),flush=True)
