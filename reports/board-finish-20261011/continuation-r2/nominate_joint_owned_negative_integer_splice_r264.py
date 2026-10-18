"""Only new cut vertices inward-quantized; old owned vertices remain exact."""
import ast,copy,hashlib,json,pickle,sys,math
from fractions import Fraction
from pathlib import Path
from shapely.geometry import Polygon,MultiPolygon,GeometryCollection
from shapely import set_precision
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'field-power/diagnose_overlap_exact_inward_intersection_vertices_r617.py';tree=ast.parse(source.read_text());helpers=[x.value.value for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='helper'for t in x.targets)];assert len(helpers)==1;exec(compile(helpers[0],'exact_R617_inward_helper','exec'))
bp=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';mp=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl';assert sha(bp)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'and sha(mp)=='765ce30b24ed3109b7c938f964775690a99f08504c464313bcf712b078421440'
g0,h0,b0,q0,c0=pickle.loads(bp.read_bytes());g,h,b,q,c=pickle.loads(mp.read_bytes());old={z['uuid']:z for z in q0};q=copy.deepcopy(q);b=copy.deepcopy(b);OUT=H/'joint-R253-only-new-negative-cut-intersection-native-integer-splice-r264';assert not OUT.exists();OUT.mkdir();rows=[];failed=[];changed={}
def ds(sh):return {'empty':sh.is_empty,'area_mm2':sh.area,'length_mm':sh.length,'type':sh.geom_type,'bounds_mm':None if sh.is_empty else list(sh.bounds),'WKB_SHA256':hashlib.sha256(sh.wkb).hexdigest()}
for z in q:
 if z['uuid']not in old:continue
 for role in('shape','zone_outline_shape'):
  before=old[z['uuid']][role];literal=z[role]
  if before.wkb==literal.wkb:continue
  assert literal.difference(before).is_empty
  after,vertices=inward_union(literal,[before]);assert set_precision(after,1e-6,mode='pointwise').wkb==after.wkb
  gain=after.difference(before);literal_gain=after.difference(literal);extra=literal.difference(after);path=OUT/(z['uuid']+'-'+role+'-integer.wkb');path.write_bytes(after.wkb);vpath=OUT/(z['uuid']+'-'+role+'-only-new-inward-vertices.json');vpath.write_text(json.dumps(vertices,indent=1)+'\n')
  row={'UUID':z['uuid'],'role':role,'net':K.L.norm(z['net']),'layer':z['layer'],'before_WKB_SHA256':hashlib.sha256(before.wkb).hexdigest(),'raw_current_WKB_SHA256':hashlib.sha256(literal.wkb).hexdigest(),'integer_WKB_SHA256':sha(path),'actual_gain_vs_original':ds(gain),'actual_gain_vs_raw_current':ds(literal_gain),'explicit_new_intersection_negative_wedges':ds(extra),'only_new_vertices_changed':len(vertices),'old_existing_vertex_tokens_preserved':True,'integer_file':str(path.resolve()),'vertex_ledger_file':str(vpath.resolve()),'vertex_ledger_SHA256':sha(vpath),'max_displacement_mm':max((x['displacement_mm']for x in vertices),default=0)};rows.append(row)
  if not gain.is_empty or not literal_gain.is_empty:failed.append(row)
  z[role]=after;changed[z['uuid']]=z
  print('R264_ROLE',z['uuid'],role,len(vertices),'GAIN',gain.is_empty,literal_gain.is_empty,flush=True)
# Rebuild only the owned physical arrays corresponding to these explicitly
# changed roles; original native filled arrays remain literally untouched.
zones=[]
for z in c['zones']:
 if z['uuid']in changed:
  qq=changed[z['uuid']];assert set(z['fills'])=={qq['layer']};zones.append({**z,'fills':{qq['layer']:K.GE.records(qq['shape'])}})
 else:zones.append(z)
after={**c,'zones':zones};previous={(x['new_generated_UUID'],x['role']):x for x in b['generated_precision_state_ledger']};ledger=[]
for z in q:
 for role in('shape','zone_outline_shape'):
  digest=hashlib.sha256(z[role].wkb).hexdigest();pr=previous[z['uuid'],role]
  if digest==pr['unchanged_WKB_SHA256']:ledger.append(pr)
  else:ledger.append({'new_generated_UUID':z['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':digest})
b['generated_precision_state_ledger']=ledger;b['explicit_native_new_cut_vertex_splice']={'source_model_SHA256':sha(mp),'source_ancestor_SHA256':sha(bp),'all_old_vertex_tokens_exact':True,'no_global_projection':True,'declared_extra_negative_wedge_rows':rows,'fresh_source_direct_reference_and_native_gate':'OPEN'};b['final_new_zone_coords_integer_nm_canonical_before_audit']=all(set_precision(z[r],1e-6,mode='pointwise').wkb==z[r].wkb for z in q for r in('shape','zone_outline_shape'))
out=OUT/'model.pkl';out.write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));(OUT/'all-exact-role-splice-ledgers.json').write_text(json.dumps(rows,indent=1)+'\n');(OUT/'raw-native-integer-literal-gain-failures.json').write_text(json.dumps(failed,indent=1)+'\n');result={'status':'NEW_CUT_ONLY_INTEGER_NATIVE_NOMINEE_LITERAL_GAIN_FREE_FRESH_GATES_OPEN'if not failed else'NEW_CUT_INTEGER_NATIVE_RAW_LITERAL_GAIN_FAILURE_HELD','before_model_SHA256':sha(bp),'source_model_SHA256':sha(mp),'model_SHA256':sha(out),'helper_source_SHA256':sha(source),'only_new_vertex_spliced_roles':len(rows),'raw_gain_failure_count':len(failed),'all_old_discrete_Cu_FP_and_original_native_fill_arrays_exact':True,'all_unmodified_role_coordinates_exact':True,'explicit_negative_wedge_scope_for_fresh_reference_review':True,'native_integer_coordinate_property':b['final_new_zone_coords_integer_nm_canonical_before_audit'],'source_direct_reference_native_current':'OPEN','native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R264_COMPLETE',sha(out),'FAILS',len(failed),'RECEIPT',sha(OUT/'receipt.json'),flush=True)
