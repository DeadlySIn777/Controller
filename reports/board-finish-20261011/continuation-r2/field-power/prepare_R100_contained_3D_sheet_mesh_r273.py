"""Contained triangular current domain, real barrel layers and exact load ports."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time,gc
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
from fast_contacts import discrete_keys
H=Path(__file__).resolve().parent;ROOT=H.parent;BASE=ROOT/'CORE-In2-owned-notch-materialized-source-proposal-r100';IN=H/'R100-full-signed-FA-return-mesh-input-r269';O=H/'R100-contained-real-barrel-3D-mesh-r273';NET='/motherboard_motors/FIELD_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def digest(q):return hashlib.sha256(q.wkb).hexdigest()
def main():
 assert not O.exists();O.mkdir();mp=BASE/'model.pkl';assert sha(mp)=='db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635';g,h,b,z,c=pickle.loads(mp.read_bytes());groups=pickle.loads((BASE/'groups.pkl').read_bytes());root=next(xs for xs in groups[NET] if any(v['kind']=='pad' and (v['ref'],v['pin'])==('J11003','2') for v in xs));keys=discrete_keys(root);ir=json.loads((IN/'receipt.json').read_text());holes=shapely.from_wkb((IN/'own-physical-drill-voids.wkb').read_bytes());ports=[]
 for q in h['pads']:
  if C.norm(q['net'])!=NET or ('pad',q['uuid']) not in keys:continue
  layers={l:unary_union(C.poly(rs)).difference(holes) for l,rs in q['layers'].items()};layers={l:sh for l,sh in layers.items() if not sh.is_empty};hole=unary_union(C.poly(q.get('hole') or []));ports.append({'kind':'pad','UUID':q['uuid'],'ref':q['ref'],'pin':q['num'],'at_mm':[q['x'],q['y']],'plated_hole_mm':2*(hole.area/np.pi)**.5 if not hole.is_empty else None,'layer_contact_shapes':layers,'physical_pad_record':q,'barrel_is_plated':not hole.is_empty,'mask_scope':'Bound actual/prospective host layer polygon; final native requirement remains separate.'})
 for q in h['vias']:
  if C.norm(q['net'])!=NET or ('via',q['uuid']) not in keys:continue
  ls=q.get('flashed');assert ls is not None;ann=Point(q['x'],q['y']).buffer(q['d']/2,quad_segs=128).difference(holes);ports.append({'kind':'via','UUID':q['uuid'],'at_mm':[q['x'],q['y']],'plated_hole_mm':q['drill'],'layer_contact_shapes':{l:ann for l in ls},'barrel_is_plated':True,'physical_via_record':q,'mask_scope':'Only exact bound actual/prospective flash layers; not all-six by inference.'})
 # Freeze the literal separate RTN physical records; no conductivity shortcut.
 rtn=[q for q in h['pads'] if q['ref'] in ('U11015','U11016') and q['num'] in ('5','11')];assert len(rtn)==4;write(O/'RTN-exact-separate-ports.json',[{'ref':q['ref'],'pin':q['num'],'UUID':q['uuid'],'raw_net':q['net'],'at_mm':[q['x'],q['y']],'layers':list(q['layers'])} for q in rtn]);(O/'ports.pkl').write_bytes(pickle.dumps(ports,protocol=5));rows=[]
 del g,h,b,z,c,groups,root;gc.collect()
 for layer in LAYERS:
  raw=shapely.from_wkb((IN/(layer.replace('.','-')+'-physical-sheet.wkb')).read_bytes());contained=raw.simplify(.001,preserve_topology=True).buffer(-.0012,join_style=2).intersection(raw);outside=contained.difference(raw).area;assert outside<1e-12;domain_file=O/(layer.replace('.','-')+'-contained-numerical-domain.wkb');domain_file.write_bytes(contained.wkb)
  # Supply an explicit mesh boundary inside every real SMD current pad.
  # Plated contact nodes occur on the physical hole boundary already present.
  patches=[v['layer_contact_shapes'][layer].intersection(contained) for v in ports if v['kind']=='pad' and not v['barrel_is_plated'] and layer in v['layer_contact_shapes']];patches=[s for s in patches if s.area>1e-14];patch=unary_union(patches);outside_patch=contained.difference(patch);triangles=[]
  for domain in [outside_patch,patch]:
   if domain.is_empty:continue
   tr=shapely.constrained_delaunay_triangles(domain);triangles.extend(np.asarray(shapely.get_coordinates(t))[:3] for t in tr.geoms)
  T=np.asarray(triangles,dtype=np.float64);np.save(O/(layer.replace('.','-')+'-triangles.npy'),T);row={'layer':layer,'exact_physical_WKB_sha256':digest(raw),'contained_domain_WKB_sha256':digest(contained),'exact_physical_area_mm2':raw.area,'contained_domain_area_mm2':contained.area,'removed_for_numerical_subset_mm2':raw.difference(contained).area,'added_physical_Cu_mm2':outside,'triangles':len(T),'literal_SMD_current_contact_patches':len(patches),'numerical_subset_does_not_edit_board_geometry':True,'simplify_tolerance_mm':.001,'inward_numeric_reserve_mm':.0012};rows.append(row);write(O/'checkpoint.json',rows);print(json.dumps(row),flush=True)
  del raw,contained,T,triangles;gc.collect()
 receipt={'verdict':'CONTAINED_REAL_BARREL_CURRENT_MESH_PREPARED_NOT_SOLVED','R100_model_sha256':sha(mp),'R100_receipt_sha256':sha(BASE/'receipt.json'),'input_exact_physical_sheet_receipt_sha256':sha(IN/'receipt.json'),'complete_signed146_port_receipt_sha256':ir['complete_signed146_term_receipt_sha256'],'separate_RTN_physical_receipt_sha256':sha(O/'RTN-exact-separate-ports.json'),'port_pickle_sha256':sha(O/'ports.pkl'),'rows':rows,'rooted_physical_contact_ports':len(ports),'rooted_plated_ports':sum(v['barrel_is_plated'] for v in ports),'source':'J11003.2','source_current_A':4.584429372438923,'complete_positive_FA_ground_cut_A':4.816879372438923,'unrooted_full_load_endpoints':[{'ref':e['ref'],'pin':e['pin'],'UUID':e['physical_pad_uuid']} for e in ir['physical_endpoint_rows'] if e['actual_same_field_ground_net'] and not e['root_connected']],'actual_stackup_copper_centres_mm':[.0175,.2725,.6375,.8925,1.2575,1.5125],'stackup_scope':'Original serialized35um copper and .22/.33/.22/.33/.22 dielectric; these total1.53mm beforemask vs general1.6mm, manufacturing thickness/layer height/plating not qualified.','native_jobs':0,'board_written':False,'adopted':False};write(O/'receipt.json',receipt);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'total_triangles':sum(r['triangles'] for r in rows),'ports':len(ports),'plated_ports':sum(v['barrel_is_plated'] for v in ports)}),flush=True)
if __name__=='__main__':main()
