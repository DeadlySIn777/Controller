"""Supplement observed native bodies with exact circular cap authority."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib,json,pickle,sys,collections
from fractions import Fraction
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;sha=N.sha
AP=H/'R275-actual-selected-native-five-net-source-body-reference-audit-r278'
OUT=H/'R275-actual-source-body-exact-named-circular-cap-authority-r289'
def put(name,x):(OUT/name).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def components(s):
 if s.is_empty:return []
 if hasattr(s,'geoms'):return [p for q in s.geoms for p in components(q)]
 return [s]
def vertices(s):
 if s.geom_type=='Polygon':return list(s.exterior.coords)+[p for r in s.interiors for p in r.coords]
 return list(s.coords)
def main():
 assert not OUT.exists();OUT.mkdir();record=json.loads((AP/'receipt.json').read_bytes());mf=AP/'actual-five-net-after-model.pkl';gf=AP/'actual-five-net-all-drilled-after-groups.pkl';assert sha(mf)==record['after_actual_model_SHA256'];assert sha(gf)==record['after_actual_groups_SHA256'];after=pickle.loads(mf.read_bytes());groups=pickle.loads(gf.read_bytes());ctx=K.hole_context(after);tracks={t['uuid']:t for t in after['tracks']};vias={v['uuid']:v for v in after['vias']};bodyrows=json.loads((AP/'all-new-plus-restored-clock-actual-body-references.json').read_bytes());results=[]
 for row in bodyrows:
  t=tracks[row['UUID']];ground='/LOGIC_GND'if L.norm(t['net'])in('/LOGIC_GND','/motherboard_do/DOA_SDI_HOST')else'/motherboard_motors/FIELD_GND';source=K.root(groups[ground],'J11001'if ground=='/LOGIC_GND'else'J11003','2');refs=K.source_refs(source);body=K.A.shape({'kind':'segment',**t});body=body.difference(unary_union([ctx[0][int(i)]for i in ctx[1].query(body,predicate='intersects')]));raw=body.difference(refs[t['layer']]);realground=unary_union([r['shape']for r in source if r['kind']=='via'and r['layer']==K.MAP[t['layer']]])if L.norm(t['net'])==ground else unary_union([]);gap=raw.difference(realground);proof=[];failed=[]
  caps=[]
  for uid,rad in row['exact_named_caps']:
   v=vias[uid];xu=round(v['x']*1e6);yu=round(v['y']*1e6);assert v['x']==xu/1e6 and v['y']==yu/1e6;assert round(rad*1000)/1000==rad
   caps.append((uid,Fraction(xu,10**6),Fraction(yu,10**6),Fraction(round(rad*1000),1000)))
  for i,part in enumerate(components(gap)):
   points=vertices(part);certificates=[]
   for uid,x,y,rad in caps:
    excess=max(((Fraction(px)-x)**2+(Fraction(py)-y)**2-rad**2 for px,py in points),default=Fraction(0));certificates.append({'named_via_UUID':uid,'declared_exact_circle_radius_mm':float(rad),'maximum_exact_vertex_squared_radius_excess_mm2':str(excess),'ALL_vertices_in_SINGLE_closed_exact_circle':excess<=0})
   passed=any(r['ALL_vertices_in_SINGLE_closed_exact_circle']for r in certificates);proof.append({'component':i,'type':part.geom_type,'vertex_count':len(points),'single_convex_circle_certificates':certificates,'whole_piece_inside_exact_named_circle_by_convexity':passed})
   if not passed:failed.append(i);(OUT/(t['uuid']+'-component-'+str(i)+'-exact-circle-cap-not-certified.wkb')).write_bytes(part.wkb)
  results.append({'UUID':t['uuid'],'net':L.norm(t['net']),'layer':t['layer'],'actual_native_source_binding':'R278 exact actual model/groups','raw_boolean_source_gap_type':raw.geom_type,'actual_same_SOURCE_ground_annuli_credited_only_for_ground_net':L.norm(t['net'])==ground,'exact_circle_piece_proof':proof,'uncertified_component_indices':failed,'pass':not failed});print('R289_EXACT_CAP',t['uuid'],'uncertified',len(failed),flush=True)
 put('all-fourteen-actual-native-body-exact-circular-cap-certificates.json',results);bad=sum(not r['pass']for r in results);put('receipt.json',{'status':'ACTUAL_R275_NAMED_OWN_CIRCULAR_CAP_AUTHORITY_SCOPED_PASS_PARENT_GATES_OPEN'if not bad else'ACTUAL_R275_EXACT_CIRCULAR_CAP_AUTHORITY_REPAIR_OR_EXACT_UNION_PROOF_REQUIRED','parent_R278_receipt_SHA256':sha(AP/'receipt.json'),'parent_R278_status':record['status'],'parent_R278_counts':record['counts'],'actual_model_SHA256':sha(mf),'actual_groups_SHA256':sha(gf),'caps_declared_decimal_mm_exact_not_outward_polygon':True,'centre_native_1nm_IU_bound':True,'boundary_coordinates_interpreted_exact_binary64_Fraction':True,'whole_polygon_or_line_inside_single_convex_circle_certified':True,'zero_area_gap_witnesses_retained':True,'uncertified_new_body_count':bad,'outward_cut_polygons_NOT_expanded_cap_authority':True,'scope':'Exact cap authority for supplied actual conservative/native body polygons; does not waive raw source reference losses, actual foreign source-gain conflicts, current, full-board refill, native DRC or SI. A multi-circle piece not covered by a single-circle certificate remains unqualified rather than being declared impossible.','native_jobs':0,'adopted':False,'manufacturing_ready':False});print('R289_COMPLETE',sha(OUT/'receipt.json'),'uncertified',bad,flush=True)
if __name__=='__main__':main()
