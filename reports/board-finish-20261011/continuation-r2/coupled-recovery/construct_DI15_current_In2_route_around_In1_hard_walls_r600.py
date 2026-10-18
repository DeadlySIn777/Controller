"""Change only NEW DI15 path to avoid exact In1 reference-extension walls.

Frozen physical/free and source masks are reused; no site grid or old Cu
rip-up. A new ground shape is nomination only until actual source checks.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import construct_DI15_current_ordinary_F_In2_F_pairs_r592 as R
import tri_route as T
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI15-NEW-In2-route-around-exact-In1-hard-walls-r600'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return{'type':s.geom_type,'empty':s.is_empty,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p):
  p=Path(p);pins[str(p.resolve())]=sha(p);return p
 ca=pickle.loads(pin(H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592/bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl').read_bytes());ex=pickle.loads(pin(H/'DI15-current-missing-In1-actual-source-extension-r596/only-NEW-reference-shape-nomination-and-exact-legal-mask.pkl').read_bytes());opts=json.loads(pin(H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592/source-and-target-continuous-ordinary-pair-options.json').read_bytes());legal=ex['legal'];before=ex['before_root'].intersection(legal.envelope.buffer(1));refpotential=before.union(legal);inner=ca['free'][R.NET,'In2.Cu'].intersection(refpotential.buffer(-.105025,quad_segs=128));attempts=[];selected=None
 for a in opts['source']:
  for z in opts['target']:
   row={'source':a['signal'],'target':z['signal']};attempts.append(row);parts=[s for s in R.pieces(inner)if s.covers(Point(a['signal']))and s.covers(Point(z['signal']))];row['actual_potential_referenced_transport_common_components']=len(parts)
   if not parts:continue
   pts,search=T.route(parts[0],tuple(a['signal']),tuple(z['signal']));pts=[[round(x,6),round(y,6)]for x,y in pts]
   if len(pts)<2 or not parts[0].covers(LineString(pts)):continue
   line=LineString(pts);body=K.Z.bounded_buffer(line,.105);missing=body.difference(before);desired=K.Z.bounded_buffer(line,.275);patch=set_precision(desired.intersection(legal).buffer(-.000025,quad_segs=128),.000001);pieces=[s for s in R.pieces(patch)if not s.intersection(missing).is_empty];patch=unary_union(pieces);gap=body.difference(before.union(patch));attach=[{'WKB_SHA256':K.C.sha(s.wkb),'before_source_overlap_mm2':s.intersection(before).area}for s in pieces]
   row.update({'In2_points_mm':pts,'length_mm':line.length,'route_search':search,'new_only_patch':info(patch),'new_body_source_union_gap':info(gap),'source_attachment_nominations':attach})
   if gap.is_empty and all(x['before_source_overlap_mm2']>.005 for x in attach):selected={'operation':row,'shape':patch,'source_return_options':a['returns'],'target_return_options':z['returns']};break
  if selected:break
 file=OUT/'only-NEW-path-and-ground-extension-NOMINATION_ONLY.pkl';file.write_bytes(pickle.dumps({'selected':selected,'attempts':attempts,'before_source':before,'legal_new_ground_mask':legal},protocol=5));put(OUT/'exact-NEW-path-construction-attempts.json',attempts);put(OUT/'receipt.json',{'verdict':'DI15_NEW_PATH_AROUND_IN1_HARD_WALLS_SOURCE_NOMINATED_OPEN'if selected else'DI15_NEW_PATH_AROUND_IN1_HARD_WALLS_BOUNDED_INCOMPLETE','selected':selected['operation']if selected else None,'input_SHA256':pins,'nomination_file':str(file.resolve()),'nomination_SHA256':sha(file),'original_or_power_Cu_removed':0,'old_FP_net_rule_mask_changes':0,'full_drilled_source_current_oldcontact_newbody_zero_oldreference_native_SI':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R600_COMPLETE',sha(OUT/'receipt.json'),'selected',bool(selected),flush=True)
if __name__=='__main__':main()
