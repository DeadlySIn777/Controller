"""Read-only exact endpoint and native-reference inventory from local cache."""
import sys,pickle,json
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import contact_layout as L
import audit_aux_exact_raw as A
from shapely.geometry import Point,box
v=pickle.loads((HERE/'di6-fault-local-components-r3.pkl').read_bytes());h=v['h']
for u,q in v['parsed_restored'].items():print('RESTORE',json.dumps({k:z for k,z in q.items() if k!='shape'}),flush=True)
for net in ('/motherboard_di/DI6_LOGIC','/motherboard_io_control/DI_SENSOR_G2_FAULT'):
 print('NATIVEPADS',net,json.dumps([{k:p[k] for k in ('uuid','ref','num','net','at','smd') if k in p} for p in h['pads'] if L.norm(p['net'])==net]),flush=True)
 for t in h['tracks']:
  if L.norm(t['net'])==net and (Point(t['a']).distance(box(112,96,122,106))<1 or Point(t['b']).distance(box(112,96,122,106))<1):print('TRACK',json.dumps(t),flush=True)
print('ROOTCACHE',json.dumps({k:type(z).__name__ for k,z in h.get('_rooted_refs',{}).items()}),flush=True)
