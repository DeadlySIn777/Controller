"""Independent true pad/track-caps/via/peer-plane gate before native trial."""
from pathlib import Path
import pickle,json,hashlib,sys
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely import STRtree
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import complete_geometry_r2 as G
O=H/'sbc-power/selected-CORE1V2-strict-geometry-r131'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def write(f,r):Path(f).write_text(json.dumps(r,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir()
 mp=H/'sbc-power/core1v2-extra-In4-source-guarded-input-r112/model.pkl';assert sha(mp)=='b58fed8889bb7fed0f5460e16680d7c56fc69b14e04b5f528c98e1fa6811c8b7'
 old,h,b,z,c=pickle.loads(mp.read_bytes())
 scope=H/'sbc-power/frozen-regional-source-exit-replay-r129/accepted-source-scope/receipt.json';assert sha(scope)=='03f79f5b1cad213c90af61747ccbbe6b6c35748d05c1cf04153846324e228513'
 qs=scope.parent/'proposed-zones.pkl';assert sha(qs)=='65bb9886f7fbc325f7a7397be1e0ed2b8d111283d8d7bdfe4285076abf935878';z=pickle.loads(qs.read_bytes());q=next(x for x in z if x['uuid']=='2f346139-8f65-5990-b9e5-9d669e6c9438');raw=q['net'];layer=q['layer'];shape=q['shape']
 peer_bind=[]
 for folder,qsha,dsha in [('field-power/regulated-four-retained-hard-snapshot-r127','82ab625dbe9310aa1287321a1e96f814a3408dead04200a8c4340882edf1b589','9651216efa39c190b8731162251cb4b68f6313f1b12c62f5eab45d2a452c891b'),('logic-return-r18-snapshot-1','943d222e160f478d8cc351f63489b5b07a4ef380a326e81b8e6f2a6d13a05a42',None),('field-power/regulated-reference-safe-source-replacements-r121','b53cb86a8827b613d2350952d5a76227bb52d5d666884136f416274e7a67aa03',None)]:
  qf=H/folder/'proposed-zones.pkl';assert sha(qf)==qsha;z+=pickle.loads(qf.read_bytes());peer_bind.append({'file':str(qf.resolve()),'sha256':qsha})
  if dsha:
   df=H/folder/'proposed-discrete.pkl';assert sha(df)==dsha;ds=pickle.loads(df.read_bytes())
   for key in ('tracks','vias'):
    ids={x['uuid']:x for x in h[key]}
    for x in ds[key]:
     if x['uuid'] in ids:assert x==ids[x['uuid']]
     else:h[key].append(x)
 pairs=[];errors=[];near=shape.buffer(2)
 def check(kind,o,gap,required):
  row={'kind':kind,'other_UUID':o['uuid'],'other_raw_net':o.get('net'),'actual_gap_mm':gap,'required_gap_mm':required};pairs.append(row)
  if gap<required:errors.append(row)
 for p in h['pads']:
  if p['net']!=raw:
   for s in C.poly(p['layers'].get(layer,[])):
    if near.intersects(s):check('exact_native_pad_polygon',p,shape.distance(s),G.gap(h,raw,p['net'])+.025)
  for s in C.poly(p.get('hole') or []):
   if p['net']!=raw and near.intersects(s):check('native_PTH_NPTH_hole',p,shape.distance(s),.275)
 ts=[t for t in h['tracks'] if t['layer']==layer and t['net']!=raw];lines=[LineString([t['a'],t['b']]) for t in ts];tree=STRtree(lines)
 for j in tree.query(shape.buffer(max([t['w']/2 for t in ts]+[0])+1),predicate='intersects'):
  t=ts[int(j)];d=shape.distance(lines[int(j)])-t['w']/2
  if d<1:check('true_track_caps',t,d,G.gap(h,raw,t['net'])+.025)
 vs=[v for v in h['vias'] if v['net']!=raw];points=[Point(v['x'],v['y']) for v in vs];tree=STRtree(points)
 for j in tree.query(near,predicate='intersects'):
  v=vs[int(j)];pt=points[int(j)]
  if layer in v['flashed']:check('actual_layer_via_annulus',v,shape.distance(pt)-v['d']/2,G.gap(h,raw,v['net'])+.025)
  check('all_layer_native_or_proposed_drill',v,shape.distance(pt)-v['drill']/2,.275)
 for p in z:
  if p['net']==raw or p['layer']!=layer:continue
  if near.intersects(p['shape']):check('actual_foreign_NEW_proposed_plane',p,shape.distance(p['shape']),max(G.gap(h,raw,p['net']),float(p.get('clearance_mm',.15)))+.025)
 for r in h['rule_areas']:
  if layer in r['layers'] and r.get('no_zones'):
   for s in C.poly(r['outline']):
    if shape.intersects(s):errors.append({'kind':'native_no_zones_area','rule_UUID':r.get('uuid')})
 outline=unary_union(C.poly(h['outline']));assert outline.covers(shape)
 jr=H/'sbc-power/core1v2-j7-independent-local-audit-r110/receipt.json';assert sha(jr)=='bbe71ab1846ce9b8a00b58b27b72e31e3c97cc9420014283d5201e13d005a659'
 assert not json.loads(jr.read_bytes())['errors']
 result={'verdict':'PASS_STRICT_ANALYTIC_SELECTED_NATIVE_NOMINEE' if not errors else 'FAIL_STRICT_ANALYTIC_SELECTED_NATIVE_NOMINEE','baseline_model_sha256':sha(mp),'source_scope_receipt_sha256':sha(scope),'all_owned_zones_sha256':sha(qs),'peer_bindings':peer_bind,'checked_shape_UUID':q['uuid'],'full_inventory_pads_true_track_caps_actual_flash_vias_all_holes_and_foreign_NEW_planes':True,'all_strict_no_gap_or_area_tolerance':True,'pairs':pairs,'errors':errors,'prior_J7_full_analytic_receipt_sha256':sha(jr),'native_run_authorization':'Root explicitly authorized existing test-only1 slot, contingent on this strict geometry gate.','wholeboard_retained_contacts_reference_current_and_native':'OPEN','board_written':False,'native_jobs':0}
 write(O/'receipt.json',result);print('R131_STRICT_SELECTED_GEOMETRY',len(pairs),len(errors),sha(O/'receipt.json'),errors[:10],flush=True)
if __name__=='__main__':main()
