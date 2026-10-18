"""Measure saved physical DI15 paths against actual drilled R18 source planes.

Also complete the frozen DI6 remote-return plated-pad diagnostic, on its
actual matched native model. Neither diagnostic qualifies a route or gap.
"""
import sys,json,pickle,time,math
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_c10036_r24_full_independent_r30 as Q
from shapely.geometry import Point,box
from shapely.ops import unary_union
C=A.C
def main():
 started=time.monotonic();out=HERE/'di15-r18-adjacent-plane-diagnostic-r52.json';assert not out.exists();A.read(__file__)
 brp=HERE/'di15-root-LG-r18-DI6-bind-r50.json';br=json.loads(A.read(brp));assert C.sha(A.read(brp))=='e372e8ea1a703619f6c6e1002050624a070d01216b8d26f6f9f16b0de2c8114e';rr=A.read(br['model_path']);assert C.sha(rr)==br['model_sha256'];cur=pickle.loads(rr);planes=cur['source_planes'];rp=HERE/'di15-In2-physical-reference-diagnostic-r48.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='1cedbf65cb3dcc2c377c5685bd89dced3d6b7028dce7e6cdd0185cc214322394';rows=[]
 for i,path in enumerate(r['physical_paths_reference_not_qualified']):
  pts=path['In2_points_mm'];body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(pts,pts[1:])]);gaps={}
  for l in('In1.Cu','In3.Cu'):
   gap=body.difference(planes[l]);p=HERE/('di15-r52-path-'+str(i)+'-'+l+'-gap.wkb');assert not p.exists();p.write_bytes(gap.wkb);gaps[l]={'gap_mm2':gap.area,'gap_bounds_mm':gap.bounds if not gap.is_empty else None,'gap_WKB_file':str(p),'gap_WKB_sha256':C.sha(gap.wkb),'rooted_plane_WKB_sha256':C.sha(planes[l].wkb)}
  rows.append({'path_index':i,'signal_sites':path['signal_sites'],'In2_points_mm':pts,'length_mm':path['length_mm'],'full_body_WKB_sha256':C.sha(body.wkb),'actual_drilled_adjacent_source_plane_measurements':gaps,'no_union_reference_or_return_credit':True})
 print('DI15_R18_ACTUAL_ADJACENT_REFERENCE_GAPS',[(q['path_index'],{l:r['gap_mm2'] for l,r in q['actual_drilled_adjacent_source_plane_measurements'].items()}) for q in rows],flush=True)
 nrp=HERE/'di6-matched-actual-native-independent-r27.json';nr=json.loads(A.read(nrp));assert C.sha(A.read(nrp))=='c56ae1566e40cd7d385ba790873d24645bd4b36719900dc5ca3ddec320acd8b8';raw=A.read(nr['saved_matched_actual_model']);assert C.sha(raw)==nr['saved_matched_actual_model_sha256'];nm=pickle.loads(raw);ng=nm['after'];rootkeys=Q.discrete_keys(nm['after_root']);vc=(342.56,100.827);win=box(vc[0]-2,vc[1]-2,vc[0]+2,vc[1]+2);ref={l:nm['after_refs'][l].intersection(win).buffer(-.075) for l in('F.Cu','B.Cu')};pads=[]
 for p in ng['pads']:
  holes=unary_union(L.poly(p.get('hole') or []))
  if L.norm(p['net'])!='/LOGIC_GND' or holes.is_empty or p.get('smd'):continue
  centre=holes.centroid;d=Point(vc).distance(centre)
  if d>1.5:continue
  ann={l:unary_union(L.poly(p['layers'].get(plane,[]))).difference(holes) for l,plane in(('F.Cu','In1.Cu'),('B.Cu','In4.Cu'))};contact={l:ann[l].intersection(ref[l]).area for l in ann};pads.append({'UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'net':p['net'],'hole_centre_mm':list(centre.coords)[0],'hole_to_signal_centre_min_edge_mm':holes.distance(Point(vc)),'centre_distance_mm':d,'actual_source_rooted_J11001_2':('pad',p['uuid']) in rootkeys,'actual_annotated_pad_layers':list(p['layers']),'finite_used_plane_annular_interior_mm2':contact,'ordinary_existing_return_nominee':.81<=d<=1 and('pad',p['uuid']) in rootkeys and all(a>=.004 for a in contact.values())})
 report={'verdict':'ACTUAL_DRILLED_R18_ADJACENT_PLANES_AND_MATCHED_REMOTE_PLATED_PADS_DIAGNOSED_ONLY','R50_receipt_sha256':C.sha(A.read(brp)),'current_model_sha256':br['model_sha256'],'R48_receipt_sha256':C.sha(A.read(rp)),'paths':rows,'DI6_R27_sha256':C.sha(A.read(nrp)),'remote_actual_LOGIC_GND_plated_pad_candidates':pads,'remote_unchanged_MOTION_transition_UUID':'237f91e0-a23b-4de7-8c1f-a116ad5338d0','DI6_strict_three_matched_native_remote_slivers':'OPEN','R18_strict_27_FBG_reference_losses':'OPEN_ROOT_CORRECTION_REQUIRED','current_all_contacts_r06_r07_native_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'remote_plated_pads':pads}),flush=True)
if __name__=='__main__':main()
