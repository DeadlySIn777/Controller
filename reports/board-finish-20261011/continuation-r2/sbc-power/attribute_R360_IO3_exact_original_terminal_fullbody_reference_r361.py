"""Attribute each no-hole IO3 bypass body against the actual J1-rooted In4 fill."""
import json,pickle,hashlib,sys,time,traceback
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-R360-IO3-actual-J1-In4-exact-two-original-terminal-fullbody-reference-r361'
D=H/'sbc-power/CM79-R353-plus-no-hole-IO3-existing-annulus-current-independent-byte-source-native-proof-r360'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'receipt.json')=='63399c63f8222501bad737e59f39eb46a1e13d2aa1da7a2af5c4d856202c8ddf';mp=D/'model.pkl';assert sha(mp)=='69fe1c947f564c2e13a5ca7beac2f3dc1d344cdc3a55c51d7e1da53171ec3899';g,h,b,q,c=pickle.loads(mp.read_bytes());nt=pickle.loads((D/'only-seven-IO3-tracks-no-hole-no-delete.pkl').read_bytes())['tracks'];io=pickle.loads((D/'fresh-actual-IO3-after-groups.pkl').read_bytes());cache=H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354/actual-drilled-after-groups.pkl';assert sha(cache)=='339dbe2c2173388fa7384c697e6364dcf5b9c507e552e64836b08c55203ed4eb';lg=K.root(pickle.loads(cache.read_bytes())['/LOGIC_GND'],'J11001','2');ref=zero(unary_union([r['shape']for r in lg if r['kind']=='fill'and r['layer']=='In4.Cu']));(O/'actual-J1-In4-source-fill-reference.wkb').write_bytes(ref.wkb);nom=json.loads((H/'sbc-power/CM79-R353-IO3-existing-actual-annulus-no-hole-fixed-Cu-bypass-nomination-r359/receipt.json').read_text())['winner'];caps=[];ports=[]
 for field in ('source_existing_annulus','detached_existing_annulus'):
  p=nom[field];v=next(v for v in h['vias']if v['uuid']==p['UUID']);observed=[r for xs in io for r in xs if r['kind']=='via'and r['uuid']==v['uuid']and r['layer']=='In4.Cu'];radius=(v['d']/2 if observed else v['drill']/2)+.25+.025;cap=Point(v['x'],v['y']).buffer(radius,quad_segs=128);caps.append(cap);ports.append({'UUID':v['uuid'],'xy':[v['x'],v['y']],'diameter_mm':v['d'],'drill_mm':v['drill'],'actual_In4_annulus_observed':bool(observed),'named_original_terminal_own_guard_radius_mm':radius,'source_fill_reference_distance_mm':Point(v['x'],v['y']).distance(ref),'no_neighbor_hole_or_D4_credit':True})
 cap=zero(unary_union(caps));rows=[]
 for t in nt:
  body=zero(unary_union([r['shape']for xs in io for r in xs if r['kind']=='track'and r['uuid']==t['uuid']and r['layer']=='In3.Cu']));raw=body.difference(ref);outside=body.difference(cap).difference(ref);fn=O/(t['uuid']+'-outside-exact-two-original-terminal-reference-gap.wkb');fn.write_bytes(outside.wkb);a,bb=nearest_points(LineString([t['a'],t['b']]),ref);rows.append({'UUID':t['uuid'],'native_track':t,'actual_drilled_body_mm2':body.area,'raw_reference_gap_mm2':raw.area,'outside_exact_named_terminal_caps_gap_EMPTY':outside.is_empty,'outside_cap_gap_mm2':outside.area,'outside_cap_gap_bounds':list(outside.bounds)if not outside.is_empty else [],'outside_cap_gap_type':outside.geom_type,'outside_cap_gap_WKB_sha256':sha(fn),'nearest_axis_source_reference_points':[list(a.coords)[0],list(bb.coords)[0]],'own_terminal_finite_same_plane_boundary_transfer_and_signed_loop':'OPEN'})
 put(O/'exact-two-original-terminal-reference-guard-authority.json',ports);put(O/'all-seven-current-IO3-body-reference-attribution.json',rows);put(O/'receipt.json',{'verdict':'R360_EXACT_REFERENCE_ATTRIBUTION_RAW_FAILS_RETAINED','R360_receipt_sha256':sha(D/'receipt.json'),'model_sha256':sha(mp),'actual_J1_In4_source_fill_reference_sha256':sha(O/'actual-J1-In4-source-fill-reference.wkb'),'track_count':7,'outside_exact_original_terminal_gap_FAIL_count':sum(not x['outside_exact_named_terminal_caps_gap_EMPTY']for x in rows),'named_terminal_authority_only':ports,'model_source_native_changes':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R361',sha(O/'receipt.json'),'outside-terminal-fails',sum(not x['outside_exact_named_terminal_caps_gap_EMPTY']for x in rows),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
