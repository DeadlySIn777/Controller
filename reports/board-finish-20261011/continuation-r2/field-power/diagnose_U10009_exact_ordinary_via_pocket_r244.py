"""Construct exact local ordinary-via centre region on current hard proposals."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import complete_geometry_r2 as G
import regional_guarded_declared_projection_r140 as P
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from inventory import sha
O=H/'U10009-current-exact-ordinary-via-pocket-r244'
def main():
 assert not O.exists();O.mkdir();parent=H/'B3-envelope-scoped-LOGIC-projection-r233';g,h,b,z,_=pickle.loads((parent/'derived-full-input-model.pkl').read_bytes());restore_bound_generated_precision_states(b,z)
 fb=pickle.loads((H/'B3-subset-inherited-FBG-native-LOGIC-guard-correction-r241/corrected-owned-FBG-zone.pkl').read_bytes())[0];z=[fb if q['uuid']==fb['uuid'] else q for q in z];field=pickle.loads((H/'FIELD5-current-reference-envelope-correction-r238/proposed-corrected-zone.pkl').read_bytes())[0];z.append(field)
 pad=next(q for q in h['pads'] if(q['ref'],q['num'])==('U10009','4'));net=C.norm(pad['net']);anchor=Point(pad['x'],pad['y']);win=box(anchor.x-3,anchor.y-3,anchor.x+3,anchor.y+3);rec,trees=F.build({**h,'zones':[]});radius=.25;drill=.1;walls=[];ledger=[]
 for layer,tree in trees.items():
  for j in tree.query(win.buffer(1.0),predicate='intersects'):
   q=rec[layer][int(j)]
   if C.norm(q['net'])==net:continue
   required=G.gap(h,pad['net'],q['net'])+.025;cut=P.bounded_buffer(q['shape'],radius+required);walls.append(cut);ledger.append({'kind':q['kind'],'UUID':q['uuid'],'raw_net':q['net'],'layer':layer,'required_gap_mm':required,'cut_sha256':P.digest(cut)})
 for q in h['pads']:
  if q['smd']:
   for layer,rs in q['layers'].items():
    if layer not in ('F.Cu','B.Cu'):continue
    shape=unary_union(C.poly(rs))
    if not shape.intersects(win.buffer(.7)):continue
    cut=P.bounded_buffer(shape,drill+.275);walls.append(cut);ledger.append({'kind':'every_SMD_aperture','UUID':q['uuid'],'raw_net':q['net'],'layer':layer,'required_hole_gap_mm':.275,'cut_sha256':P.digest(cut)})
  for shape in C.poly(q.get('hole')or[]):
   if shape.intersects(win.buffer(.7)):walls.append(P.bounded_buffer(shape,drill+.275))
 for v in h['vias']:
  pt=Point(v['x'],v['y'])
  if pt.distance(win)<v['drill']/2+drill+.276:walls.append(P.bounded_buffer(pt,v['drill']/2+drill+.275))
 for q in z:
  if C.norm(q['net'])==net:continue
  # Only same-domain owned FIELD_GND may receive a future explicitly gated carve.
  if C.norm(q['net'])=='/motherboard_motors/FIELD_GND' and q['layer'] in ('In1.Cu','In2.Cu','In4.Cu'):continue
  if not q['shape'].intersects(win.buffer(1.0)):continue
  required=max(G.gap(h,pad['net'],q['net']),float(q.get('clearance_mm',.15)))+.025;cut=P.bounded_buffer(q['shape'],radius+required);walls.append(cut);ledger.append({'kind':'hard_owned_plane','UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'required_gap_mm':required,'cut_sha256':P.digest(cut)})
 for area in h['rule_areas']:
  if area.get('no_vias'):
   for shape in C.poly(area['outline']):
    if shape.intersects(win.buffer(.3)):walls.append(P.bounded_buffer(shape,radius+.025))
 legal=set_precision(win.difference(unary_union(walls)),1e-6);parts=[legal] if legal.geom_type=='Polygon' else [q for q in getattr(legal,'geoms',[]) if q.geom_type=='Polygon'];nominations=[]
 for part in sorted(parts,key=lambda q:q.distance(anchor)):
  point=part.representative_point();nominations.append({'xy_mm':list(point.coords[0]),'distance_from_pad_mm':point.distance(anchor),'legal_component_mm2':part.area})
 (O/'legal-centres.wkb').write_bytes(legal.wkb);(O/'obstacle-ledger.json').write_text(json.dumps(ledger,indent=1)+'\n',encoding='utf-8');receipt={'verdict':'EXACT_LOCAL_CENTRE_DIAGNOSTIC_OUTER_STUB_AND_SOURCE_SEARCH_REQUIRED','source_model_sha256':sha(parent/'derived-full-input-model.pkl'),'target_pad_UUID':pad['uuid'],'target_raw_net':pad['net'],'xy_mm':[pad['x'],pad['y']],'outer':'B.Cu','nominal_diameter_drill_mm':[.5,.2],'complete_all_layer_Cu_SMD_hole_spacing_guards':True,'legal_area_mm2':legal.area,'component_count':len(parts),'nearest_component_nominations':nominations[:8],'declarative_reservation_outer_stub_source_plane_oldcontact_reference_current_native':'OPEN','native_jobs':0,'board_written':False};(O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps(receipt),flush=True);print('R244 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
