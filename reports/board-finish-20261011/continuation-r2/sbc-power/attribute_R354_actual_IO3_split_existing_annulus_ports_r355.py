"""Exact source/group/nearest-gap attribution, existing annuli only, no model."""
import json,pickle,hashlib,sys,time,gc
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
D=H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354'
O=H/'sbc-power/CM79-R353-fresh-IO3-split-source-and-existing-annulus-port-attribution-r355'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert (D/'receipt.json').exists();r=json.loads((D/'receipt.json').read_text());assert r['model_sha256']=='de8e2af4143fe43491773e0e0339c39efb17cb1660072bf37ffc6a22c155255e';af=D/'actual-drilled-after-groups.pkl';assert sha(af)==r['actual_after_group_cache_sha256'];groups=pickle.loads(af.read_bytes())['/IO_3V3'];before=pickle.loads((D/'actual-drilled-before-groups.pkl').read_bytes())['/IO_3V3'];root=K.root(groups,'R18001','2');old=K.root(before,'R18001','2');oldkeys=K.keys(old);rootkeys=K.keys(root);detached=[xs for xs in groups if xs is not root and K.keys(xs)&oldkeys];mp=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r353/model.pkl';assert sha(mp)==r['model_sha256'];g,h,b,q,c=pickle.loads(mp.read_bytes());vp={v['uuid']:v for v in h['vias']};padmap={p['uuid']:p for p in h['pads']};ports=[];pads=[];layers=[]
 for gi,xs in enumerate([root,*detached]):
  seen=set()
  for rr in xs:
   if rr['kind']=='pad'and rr['uuid']in padmap:p=padmap[rr['uuid']];pads.append({'group':gi,'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'layer':rr['layer'],'actual_layer_area_mm2':rr['shape'].area})
   if rr['kind']!='via'or(rr['uuid'],rr['layer'])in seen:continue
   seen.add((rr['uuid'],rr['layer']));v=vp[rr['uuid']];ports.append({'group':gi,'UUID':v['uuid'],'raw_net':v['net'],'layer':rr['layer'],'x':v['x'],'y':v['y'],'diameter_mm':v['d'],'drill_mm':v['drill'],'actual_drill_subtracted_annulus_area_mm2':rr['shape'].area,'original_or_CM_new': 'original_or_preexisting','source_rooted_before':('via',v['uuid'],rr['layer'])in oldkeys,'source_rooted_after':gi==0})
  layers.append({'group':gi,'actual_retained_old_layer_keys':sorted([list(k)for k in K.keys(xs)&oldkeys]),'old_key_count':len(K.keys(xs)&oldkeys),'actual_pad_identities':sorted(set((rr['ref'],str(rr['pin']),rr['uuid'])for rr in xs if rr['kind']=='pad'))})
 gaps=[]
 for ly in K.LAYERS:
  aa=[rr for rr in root if rr['layer']==ly and rr['kind']=='fill'];bb=[rr for xs in detached for rr in xs if rr['layer']==ly and rr['kind']=='fill']
  if not aa or not bb:continue
  tree=STRtree([rr['shape']for rr in aa]);row=min(((rr['shape'].distance(aa[int(tree.nearest(rr['shape']))]['shape']),rr,aa[int(tree.nearest(rr['shape']))])for rr in bb),key=lambda row:row[0]);dist,z,a=row;pa,pb=nearest_points(a['shape'],z['shape']);gaps.append({'layer':ly,'source_zone_UUID':a['uuid'],'detached_zone_UUID':z['uuid'],'actual_gap_mm':dist,'actual_source_gap_xy':list(pa.coords)[0],'actual_detached_gap_xy':list(pb.coords)[0]})
 pairs=[]
 for ly in K.LAYERS:
  aa=[p for p in ports if p['group']==0 and p['layer']==ly];bb=[p for p in ports if p['group']>0 and p['layer']==ly]
  if not aa or not bb:continue
  tree=STRtree([Point(p['x'],p['y'])for p in aa])
  for p in bb:
   v=aa[int(tree.nearest(Point(p['x'],p['y'])))];pairs.append({'layer':ly,'center_distance_mm':Point(p['x'],p['y']).distance(Point(v['x'],v['y'])),'source_existing_annulus':v,'detached_existing_annulus':p,'no_new_barrel_or_net_alias':True})
 pairs.sort(key=lambda p:p['center_distance_mm']);put(O/'all-real-retained-pad-and-group-keys.json',layers);put(O/'all-existing-IO3-actual-annulus-source-ports.json',ports);put(O/'nearest-actual-fill-gaps.json',gaps);put(O/'finite-nearest-existing-cross-group-annulus-pairs.json',pairs);(O/'actual-IO3-before-after-groups.pkl').write_bytes(pickle.dumps({'before':before,'after':groups},protocol=5));out={'verdict':'R353_REAL_IO3_SPLIT_EXACT_SOURCE_AND_EXISTING_ANNULUS_ATTRIBUTION_NO_REPAIR','R354_receipt_sha256':sha(D/'receipt.json'),'model_sha256':sha(mp),'old_source_retained_keys':len(oldkeys),'retained_source_keys_after':len(rootkeys&oldkeys),'detached_old_keys':len(oldkeys-rootkeys),'detached_group_count':len(detached),'existing_actual_annulus_port_rows':len(ports),'nearest_fill_gaps':gaps,'nearest_existing_pairs':pairs[:12],'packet_sha256':sha(O/'actual-IO3-before-after-groups.pkl'),'every_original_source_direct_reference_current_signed_IO3_CORE5_ground_loop_native':'FAIL_OR_OPEN_RETAINED','original_source_board_native_changes':0,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',out);print('R355',sha(O/'receipt.json'),json.dumps({k:v for k,v in out.items()if k not in('nearest_existing_pairs',)}),flush=True)
if __name__=='__main__':main()
