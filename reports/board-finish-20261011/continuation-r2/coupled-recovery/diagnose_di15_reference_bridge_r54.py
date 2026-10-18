"""Nominate a concrete rooted reference bridge for saved ordinary In2 path.

Measure exact native/current blockers first; no plane or contact waiver.
"""
import sys,json,pickle,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import construct_di6_direct_source_escape_r5 as K
from shapely.geometry import LineString,box
from shapely.ops import unary_union
C=A.C;GND='/LOGIC_GND';NET='/motherboard_di/DI15_LOGIC'
def main():
 started=time.monotonic();out=HERE/'di15-reference-bridge-diagnostic-r54.json';assert not out.exists();A.read(__file__);rp=HERE/'di15-root-LG-r18-DI6-bind-r50.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='e372e8ea1a703619f6c6e1002050624a070d01216b8d26f6f9f16b0de2c8114e';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h=cur['h'];g=cur['after'];planes=cur['source_planes'];pathr=json.loads(A.read(HERE/'di15-In2-physical-reference-diagnostic-r48.json'));pts=pathr['physical_paths_reference_not_qualified'][0]['In2_points_mm'];body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(pts,pts[1:])]);line=LineString(pts);win=box(110,81,137,123);rec,trees=F.build({**h,'zones':[]});rows=[];saved={}
 for l in('In1.Cu','In3.Cu'):
  gap=body.difference(planes[l]);allground=unary_union([sh for z in g['zones'] if L.norm(z['net'])==GND for sh in L.poly(z['fills'].get(l,[]))]);stale_unsourced=gap.intersection(allground);block=[];obstacles=[]
  for i in trees[l].query(win.buffer(1),predicate='intersects'):
   q=rec[l][int(i)];n=L.norm(q['net'])
   if n==GND:continue
   required=(.15 if h['domains_normalized'].get(n)==h['domains_normalized'].get(GND) else .6)+.025;mask=q['shape'].buffer(required,quad_segs=128);obstacles.append(mask)
   overlap=mask.intersection(gap)
   if not overlap.is_empty:block.append({'UUID':q['uuid'],'kind':q['kind'],'net':q['net'],'required_mm':required,'gap_blocked_area_mm2':overlap.area,'body_distance_mm':q['shape'].distance(body),'shape_WKB_sha256':C.sha(q['shape'].wkb)})
  hardplanes=[]
  for z in cur['zones']:
   n=L.norm(z['net'])
   if z['layer']!=l or n==GND or z['shape'].distance(win)>1:continue
   required=max(.15 if h['domains_normalized'].get(n)==h['domains_normalized'].get(GND) else .6,float(z.get('clearance_mm',.15)))+.025;mask=z['shape'].buffer(required,quad_segs=128);obstacles.append(mask);overlap=mask.intersection(gap)
   if not overlap.is_empty:hardplanes.append({'UUID':z['uuid'],'net':z['net'],'explicit_local_mm':float(z.get('clearance_mm',.15)),'required_mm':required,'gap_blocked_area_mm2':overlap.area,'shape_WKB_sha256':C.sha(z['shape'].wkb)})
  for z in h['rule_areas']:
   if l in z['layers'] and(z.get('no_tracks') or z.get('no_zones')):obstacles += [sh.buffer(.025,quad_segs=128) for sh in L.poly(z['outline'])]
  proposed_bridge=line.buffer(.20,quad_segs=128);legal=win.difference(unary_union(obstacles));remaining=proposed_bridge.difference(legal);rows.append({'reference_layer':l,'source_gap_mm2':gap.area,'gap_already_in_unrooted_ground_fill_mm2':stale_unsourced.area,'gap_physically_uncovered_mm2':gap.difference(allground).area,'minimum_proposed_reference_strip_width_mm':.4,'strip_full_body_reference_margin_mm':.1,'proposed_full_strip_blocked_mm2':remaining.area,'discrete_native_or_current_blockers':sorted(block,key=lambda q:-q['gap_blocked_area_mm2']),'owned_positive_plane_blockers':sorted(hardplanes,key=lambda q:-q['gap_blocked_area_mm2']),'same_domain_old_fill_retreat_not_credited_until_contact_source_audit':True});saved[l]={'actual_source_reference':planes[l].intersection(win.buffer(1)),'all_existing_ground_fill':allground.intersection(win.buffer(1)),'physical_ground_legal':legal,'reference_gap':gap,'proposed_strip':proposed_bridge,'blocked':remaining}
 cache=HERE/'di15-reference-bridge-r54-geometry.pkl';assert not cache.exists();cache.write_bytes(pickle.dumps(saved,protocol=5));report={'verdict':'EXACT_DI15_REFERENCE_BRIDGE_BLOCKERS_NOMINATED_NOT_QUALIFIED','R50_receipt_sha256':C.sha(A.read(rp)),'current_model_sha256':r['model_sha256'],'path':pts,'layers':rows,'saved_geometry':str(cache),'saved_geometry_sha256':C.sha(cache.read_bytes()),'strict_max_three_layer_segments':True,'all_original_contacts_source_return_current_native_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'layers':rows}),flush=True)
if __name__=='__main__':main()
