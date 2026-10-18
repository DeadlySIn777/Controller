"""Shared exact native export conversion and pinned R663 BEFORE selectors.

Caller must confine its single heavy host before importing numeric helpers.
All actual native holes/flash masks remain observed, never substituted/forced.
This module does not launch native jobs or qualify unselected fill caches.
"""
from pathlib import Path
import hashlib,json,pickle,collections,sys
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
R663=H/'R157-actual-three-ground-native-all-drill-source-groups-r663'
R157=ROOT/'R155-known-reference-native-diagnostic-r157/measure'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def assert_R157_actual_before():
 assert sha(R157/'actual-full-refill-geometry.json')=='421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b'
 assert sha(R157/'actual-full-refill-via-flashes.json')=='b64eb5a7ceab4c162699943ed5444554a93c7564cd391eb7dec4ce6e68512ce1'

def bound_R663_before_groups(normalized_nets):
 """Return only exact already-built LG/FG/FB groups; IO3 must be rebuilt."""
 assert_R157_actual_before()
 assert sha(R663/'receipt.json')=='33703477904ca3cc046c80e741f59897c68c04d2c6dd13d307792d006b1bb1cd'
 f=R663/'actual-R157-native-three-ground-all-drilled-groups.pkl'
 assert sha(f)=='a24dcae5ae52ae71e548e7f75f2d1ec746324187cf1dc5ab67e01a4ef6f347b7'
 groups=pickle.loads(f.read_bytes());nets=set(normalized_nets);known={n:groups[n]for n in nets if n in groups};missing=nets-set(known)
 assert missing<={'/IO_3V3'},('unknown baseline source',missing)
 return known,missing

def convert_selected_actual(h,model_candidate,native_geometry,actual_flashes,normalized_nets,source_pcb=None):
 """Map fresh native pad poses to supplied exact AFTER h, never BEFORE h.

For R275, the supplied AFTER h must carry native-attested moved R10007.
BEFORE conversion for IO3 uses original exact R155 h and actual R157 dump.
Single first-member native pad polygon is shared only on reported layers:
the exact PCB must retain default common pad shapes with no padstack override.
"""
 nets=set(normalized_nets)
 if source_pcb is not None:
  data=Path(source_pcb).read_bytes().lower()
  assert b'padstack'not in data and b'layer_shapes'not in data and b'custom_pad_primitives'not in data
 raws={p['net']for p in h['pads']if L.norm(p['net'])in nets};assert {L.norm(n)for n in raws}==nets
 index=collections.defaultdict(list)
 for p in h['pads']:
  if p['net']in raws:index[p['ref'],str(p['num']),p['x'],p['y'],p['net']].append(p)
 replacements={};ledger=[]
 for p in native_geometry['pads']:
  if p['net']not in raws:continue
  options=index[p['ref'],str(p['num']),*p['at'],p['net']]
  assert len(options)==1,('actual native physical pad must match supplied h exactly',p['ref'],p['num'],p['at'],p['net'])
  old=options[0];assert old['uuid']not in replacements
  replacements[old['uuid']]={**old,'layers':{ly:O.polys(p['poly'])for ly in p['layers']}}
  ledger.append({'UUID':old['uuid'],'ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'actual_native_at_mm':p['at'],'actual_reported_member_layers':p['layers'],'polygon_mode':'native .005 mm ERROR_INSIDE, common pad shape only'})
 assert set(replacements)=={p['uuid']for p in h['pads']if p['net']in raws}
 assert {v['uuid']for v in h['vias']}==set(actual_flashes)
 vias=[{**v,'flashed':list(actual_flashes[v['uuid']]),'mask_provenance':'fresh supplied ACTUAL native FlashLayer, never forced'}for v in h['vias']]
 pads=[replacements.get(p['uuid'],p)for p in h['pads']]
 zones=[{**z,'fills':{ly:O.polys(rs)for ly,rs in z['fills'].items()}}for z in native_geometry['zones']if z['net']in raws]
 candidate={**h,'pads':pads,'vias':vias,'zones':[z for z in model_candidate['zones']if z['net']not in raws]+zones}
 ctx=K.hole_context(candidate);assert len(ctx[0])==len(vias)+sum(len(L.poly(p.get('hole')or[]))for p in pads)
 return candidate,ctx,ledger

def fresh_selected_groups(candidate,context,normalized_nets):
 return {net:K.physical(candidate,net,context)[1]for net in sorted(normalized_nets)}
