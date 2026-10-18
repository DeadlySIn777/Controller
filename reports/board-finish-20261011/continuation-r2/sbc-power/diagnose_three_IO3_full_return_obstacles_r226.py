"""Exact full foreign envelopes and actual local source-return candidates."""
import hashlib,json,pickle,sys,traceback
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/three-IO3-full-return-obstacle-diagnosis-r226'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def root(gs):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11001','2')for q in xs))
def main():
 assert not O.exists();O.mkdir()
 base=H/'sbc-power/C1022-zero-gap-source-feed-independent-r221';assert sha(base/'model.pkl')=='261f92035b05f1346bc805d43df3f7b67a2c0c638892ee43c01856d57196182a'
 g,h,b,z,c=pickle.loads((base/'model.pkl').read_bytes());ps=PS.restore_bound_generated_precision_states(b,z);groups=pickle.loads((base/'groups.pkl').read_bytes());lg=root(groups['/LOGIC_GND']);keys={(q['kind'],q['uuid'],q['layer'])for q in lg if q['kind']!='fill'}
 d=H/'sbc-power/five-IO3-feed-actual-return-gap-diagnosis-r223';assert sha(d/'receipt.json')=='0a720e8c335c8838605874429c80ecf6f92eab9ef671750c9cbea082128bd910';selected=[r for r in json.loads((d/'receipt.json').read_text())['rows']if r['nominee']['ref']in('C1018','U14401','U21003')];assert len(selected)==3
 records,trees=F.build({**h,'zones':[]});rows=[]
 for old in selected:
  r=old['nominee'];layer=old['required_reference_layer'];gap=from_wkb(Path(r['reference_gap_file']).read_bytes());p=Point(*gap.centroid.coords[0]);cuts=[];ledger=[]
  def add(kind,uid,net,cut,**kw):
   hit=cut.intersection(gap)
   if hit.is_empty:return
   cuts.append(cut);ledger.append({'kind':kind,'UUID':uid,'raw_net':net,'gap_overlap_mm2':hit.area,'cut_WKB_sha256':digest(cut),**kw})
  # These are explicit full planning envelopes, not the inscribed F.build caps.
  for j in trees[layer].query(gap.buffer(1.5),predicate='intersects'):
   q=records[layer][int(j)]
   if C.norm(q['net'])=='/LOGIC_GND':continue
   clear=max(.15,GP.G.gap(h,'/LOGIC_GND',q['net']))+.025
   if q['kind']=='track':t=q['source'];cut=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear)
   elif q['kind']=='via':v=q['source'];cut=GP.bounded_disk(v,max(v['drill']/2+.275,v['d']/2+clear))
   else:cut=GP.bounded_buffer(q['shape'],clear+.000020)
   add('actual_discrete_full_Cu_guard',q['uuid'],q['net'],cut,clearance_before_Cu_radius_mm=clear)
  for v in h['vias']:
   if Point(v['x'],v['y']).distance(gap)>1.5:continue
   add('every_physical_drill',v['uuid'],v['net'],GP.bounded_disk(v,v['drill']/2+.275),radius_mm=v['drill']/2+.275)
  for pad in h['pads']:
   for hole in C.poly(pad.get('hole')or[]):
    if hole.distance(gap)<1:add('every_physical_pad_hole',pad['uuid'],pad['net'],GP.bounded_buffer(hole,.275))
  for q in z:
   if q['layer']!=layer or C.norm(q['net'])=='/LOGIC_GND' or q['shape'].distance(gap)>1.5:continue
   clear=max(.15,float(q['clearance_mm']),GP.G.gap(h,'/LOGIC_GND',q['net']))+.025
   add('owned_foreign_plane_full_guard',q['uuid'],q['net'],GP.bounded_buffer(q['shape'],clear),clearance_mm=clear,physical_WKB_sha256=digest(q['shape']))
  for q in h['zones']:
   if C.norm(q['net'])=='/LOGIC_GND':continue
   for sh in C.poly(q['fills'].get(layer,[])):
    if sh.distance(gap)>1.5:continue
    clear=max(.15,float(q['clearance_mm']),GP.G.gap(h,'/LOGIC_GND',q['net']))+.025
    add('native_foreign_fill_full_guard',q['uuid'],q['net'],GP.bounded_buffer(sh,clear),clearance_mm=clear,native_fill_WKB_sha256=digest(sh))
  for q in h['rule_areas']:
   if layer not in q['layers']or not q.get('no_zones'):continue
   for sh in C.poly(q['outline']):
    if sh.distance(gap)<1:add('actual_native_no_zones',q['uuid'],'',GP.bounded_buffer(sh,.025))
  # Real source-return barrels/pads; current masks remain actual/prospective
  # as recorded. Nothing here qualifies a terminal aperture.
  returns=[]
  for v in h['vias']:
   if C.norm(v['net'])!='/LOGIC_GND'or Point(v['x'],v['y']).distance(gap)>2:continue
   used=[l for l in v['flashed']if('via',v['uuid'],l)in keys];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));fills=unary_union([q['shape']for q in lg if q['kind']=='fill'and q['layer']==layer]);area=ann.intersection(fills.buffer(-.025,quad_segs=128)).area
   returns.append({'kind':'via','UUID':v['uuid'],'x':v['x'],'y':v['y'],'d':v['d'],'drill':v['drill'],'distance_from_gap_mm':Point(v['x'],v['y']).distance(gap),'actual_or_prospective_flashes':v['flashed'],'actual_J1_source_layer_keys':used,'finite_reference_annular_interior_mm2':area,'original_native_198b_discrete_record':next((q for q in g['vias']if q['uuid']==v['uuid']),None)})
  for pad in h['pads']:
   if C.norm(pad['net'])!='/LOGIC_GND'or Point(pad['x'],pad['y']).distance(gap)>2:continue
   returns.append({'kind':'pad','ref':pad['ref'],'pin':pad['num'],'UUID':pad['uuid'],'x':pad['x'],'y':pad['y'],'actual_J1_source_layers':[l for l in pad['layers']if('pad',pad['uuid'],l)in keys],'distance_from_gap_mm':Point(pad['x'],pad['y']).distance(gap)})
  freegap=gap.difference(unary_union(cuts));(O/(r['ref']+'-gap-not-forbidden-by-full-envelopes.wkb')).write_bytes(freegap.wkb)
  rows.append({'ref':r['ref'],'pin':r['pin'],'reference_layer':layer,'gap_mm2':gap.area,'full_guard_attribution':ledger,'full_guard_union_gap_mm2':gap.intersection(unary_union(cuts)).area,'remaining_not_forbidden_gap_mm2':freegap.area,'nearby_actual_source_return_candidates':returns,'no_terminal_aperture_credit_or_reference_qualification':True})
 put(O/'receipt.json',{'verdict':'EXACT_THREE_RETURN_GAP_FULL_OBSTACLE_AND_SOURCE_PORT_DIAGNOSIS_ONLY','positive_base_model_sha256':sha(base/'model.pkl'),'R223_receipt_sha256':sha(d/'receipt.json'),'precision_restore':ps,'rows':rows,'native_jobs':0,'board_written':False,'geometry_changed':False,'script_sha256':sha(__file__)})
 print('R226_COMPLETE',sha(O/'receipt.json'),[(q['ref'],q['remaining_not_forbidden_gap_mm2'],len(q['nearby_actual_source_return_candidates']))for q in rows],flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
