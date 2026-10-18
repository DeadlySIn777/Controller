"""Read-only exact HOST drill guard attribution, no PCB mutation."""
import pickle,json,sys,hashlib
from pathlib import Path
from shapely.geometry import LineString,Point
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
p=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r247/model.pkl';assert hashlib.sha256(p.read_bytes()).hexdigest()=='9b5ce5fcc6fcf741f73ba48cd15ab396a022115ba7110ee3d4c7fc27459cbf86'
g,h,b,q,c=pickle.loads(p.read_bytes());t=next(x for x in h['tracks']if x['uuid']=='0e1758e0-b441-5845-bba2-0626dfeed39d');v=next(x for x in h['vias']if x['uuid']=='084a6392-6353-41cd-9668-f8a6f427319e');axis=LineString([t['a'],t['b']]);pt=Point(v['x'],v['y']);close=axis.interpolate(axis.project(pt))
related=[x for x in h['tracks']if K.L.norm(x['net'])==K.L.norm(t['net'])and any(a==bb for a in(t['a'],t['b'])for bb in(x['a'],x['b']))]
out=H/'U10003-HOST-current-single-drill-deficit-attribution-r249';assert not out.exists();out.mkdir();result={'model_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'track':t,'foreign_via':v,'closest_axis_point':[close.x,close.y],'actual_axis_to_center_mm':axis.distance(pt),'actual_track_to_drill_gap_mm':axis.distance(pt)-t['w']/2-v['drill']/2,'guarded_gap_mm':axis.distance(pt)-t['w']/2-v['drill']/2-.005,'required_guarded_gap_mm':.275,'endpoint_adjacent_tracks':related,'source_geometry_mutations':0};(out/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print(json.dumps(result,indent=1),flush=True)
