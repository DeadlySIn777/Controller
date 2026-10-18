"""Freeze exact R100 physical return sheets and signed ports for a current solve."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from inventory import sha
import contact_layout as C
from fast_contacts import discrete_keys
H=Path(__file__).resolve().parent;ROOT=H.parent
BASE=ROOT/'CORE-In2-owned-notch-materialized-source-proposal-r100'
O=H/'R100-full-signed-FA-return-mesh-input-r269'
NET='/motherboard_motors/FIELD_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def digest(q):return hashlib.sha256(q.wkb).hexdigest()
def main():
 assert not O.exists();O.mkdir();rp=BASE/'receipt.json';r=json.loads(rp.read_text());mp=BASE/'model.pkl';assert sha(mp)=='db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635'==r['model_sha256']
 g,h,b,z,c=pickle.loads(mp.read_bytes());groups=pickle.loads((BASE/'groups.pkl').read_bytes());gs=groups[NET];root=next(xs for xs in gs if any(v['kind']=='pad' and (v['ref'],v['pin'])==('J11003','2') for v in xs));rootkeys=discrete_keys(root);pads={q['uuid']:q for q in h['pads']};vias={q['uuid']:q for q in h['vias']};ownpads=[q for q in h['pads'] if C.norm(q['net'])==NET];ownvias=[q for q in h['vias'] if C.norm(q['net'])==NET];holes=unary_union([sh for p in ownpads for sh in C.poly(p.get('hole') or [])]+[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128) for v in ownvias]);write(O/'hole-binding.json',{'net':NET,'pad_UUIDs':[p['uuid'] for p in ownpads if p.get('hole')],'via_UUIDs':[v['uuid'] for v in ownvias],'physical_drill_union_WKB_sha256':digest(holes),'only_own_holes_subtracted_after_same_net_union':'Foreign holes remain absent in already guarded native/new plane fill; no foreign discrete Cu belongs to this net.'});(O/'own-physical-drill-voids.wkb').write_bytes(holes.wkb)
 portrec=ROOT/'field-signed-port-allocation-r4/receipt.json';ledger=json.loads(portrec.read_text());terms=[q for q in ledger['terms'] if q['domain']=='FA'];ep={e['physical_pad_uuid']:e for q in terms for e in q['eligible_physical_endpoints']};portrows=[]
 for uid,e in ep.items():
  p=pads[uid];assert p['ref']==e['ref'] and p['num']==e['pin'] and p['net']==e['raw_net'];portrows.append({**e,'current_R100_pad_at_mm':[p['x'],p['y']],'actual_R100_layers':list(p['layers']),'root_connected':('pad',uid) in rootkeys,'actual_same_field_ground_net':C.norm(p['net'])==NET,'physical_hole':p.get('hole') or [],'pin_layers_polygons':p['layers']})
 # RTN is a device-side return port, not interchangeable with its GND pin.
 rt=[]
 for p in h['pads']:
  if p['ref'] in ['U11019','U11020','U11021','U11022'] and p['num'] in ['1','2','3','4','5','6','7','8']:rt.append({'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'raw_net':p['net'],'at_mm':[p['x'],p['y']],'layers':list(p['layers'])})
 sheets={};rows=[]
 for l in LAYERS:
  copper=unary_union([q['shape'] for q in root if q['layer']==l]).difference(holes);sheets[l]=copper;(O/(l.replace('.','-')+'-physical-sheet.wkb')).write_bytes(copper.wkb);tri=constrained_delaunay_triangles(copper);row={'layer':l,'physical_WKB_sha256':digest(copper),'area_mm2':copper.area,'bounds_mm':list(copper.bounds),'polygons':1 if copper.geom_type=='Polygon' else len(copper.geoms),'initial_constrained_triangles':len(tri.geoms)};rows.append(row);print(json.dumps(row),flush=True);write(O/'sheet-checkpoint.json',rows)
 q=next(q for q in z if q['uuid']=='e2fe644a-2849-5c69-8ebb-d1e94909cd4c');cuts=json.loads((BASE/'owned-remove-only-role-cuts.json').read_text());qr=next(v for v in cuts if v['UUID']==q['uuid'] and v['role']=='shape');assert digest(q['shape'])==qr['after_WKB_sha256'];(O/'e2fe-after-notch-physical.wkb').write_bytes(q['shape'].wkb)
 receipt={'verdict':'EXACT_R100_CURRENT_INPUTS_FROZEN_NUMERICAL_MODEL_NOT_YET_SOLVED','model_sha256':sha(mp),'parent_receipt_sha256':sha(rp),'owned_remove_only_role_cuts_sha256':sha(BASE/'owned-remove-only-role-cuts.json'),'CORE_R98_route_receipt_sha256':sha(ROOT/'CORE-bounded-owned-FAG-In2-notch-feed-proposal-r98/receipt.json'),'complete_signed146_term_receipt_sha256':sha(portrec),'FA_terms':terms,'physical_endpoint_rows':portrows,'FA_terms_signed_KCL_A':sum(q['signed_current_a'] for q in terms),'FA_ground_terms_signed_KCL_A':sum(q['signed_current_a'] for q in terms if any(e['raw_net'].replace('{slash}','/')==NET for e in q['eligible_physical_endpoints'])),'source':'J11003.2','shutdown_contact':'J11004.2 has no source injection','root_physical_keys':len(rootkeys),'sheets':rows,'own_plated_vias':ownvias,'RTN_device_pin_screen':rt,'removed_FAG_In2_area_mm2':qr['removed_mm2'],'source_current_A':4.58442937244,'mesh_port_allocation':'Each full conserved simplex term may choose one eligible physical endpoint. Equal pad, layer or barrel sharing is not a capacity assumption.','native_jobs':0,'board_written':False,'current_thermal_qualification':False};write(O/'receipt.json',receipt);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'terms':len(terms),'endpoints':len(portrows),'unrooted_same_ground_endpoints':[e['physical_pad_uuid'] for e in portrows if e['actual_same_field_ground_net'] and not e['root_connected']]}),flush=True)
if __name__=='__main__':main()
