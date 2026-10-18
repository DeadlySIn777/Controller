"""Exact physical pad/barrel inventory for a signed multipath LG solver."""
import hashlib,json,pickle,sys,collections
from pathlib import Path
from shapely.ops import unary_union
from shapely.geometry import Point
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import physical_reference_losses_r3_zero_r208 as RF
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
O=H/'sbc-power/R265-signed-LG-physical-multiport-inventory-r269'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();mp=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r265/T4-plus-R7/model.pkl';assert sha(mp)=='e81143a727821d906558e6edce30088da3d410eb0dda8630f80d8fe85e1f16bf';g,h,b,q,c=pickle.loads(mp.read_bytes());gp=mp.parent/'actual-drilled-groups.pkl';gs=pickle.loads(gp.read_bytes());lg=K.root(gs['/LOGIC_GND'],'J11001','2');rootkeys=K.keys(lg);pfile=H/'sbc-power/signed-return-scenarios-r1.json';assert sha(pfile)=='e1b14aeafe8802907ae92cd5ceb8c0c9ad42bf7beaf343d6c3886cdc1da165af';signed=json.loads(pfile.read_text());actualsource=Path(signed['source']);assert sha(actualsource)==signed['source_sha256'];pads=collections.defaultdict(list)
 for p in h['pads']:
  if p['net']=='/LOGIC_GND':pads[p['ref'],str(p['num'])].append(p)
 mapped=[];unrooted=[];missing=[];unique={}
 for group in signed['groups']:
  ids=[];bad=[]
  for req in group['ground_node_candidates']:
   pp=pads.get((req['ref'],str(req['pin'])),[])
   if not pp:missing.append(req);continue
   for p in pp:
    entry={'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'at':[p['x'],p['y']],'actual_layers':list(p['layers']),'source_rooted_actual_layers':[l for l in p['layers']if('pad',p['uuid'],l)in rootkeys],'source_selector_logical_pad_multiplicity':len(pp),'actual_whole_pad_layers_all_source_rooted':all(('pad',p['uuid'],l)in rootkeys for l in p['layers'])};unique[p['uuid']]=entry;ids.append(p['uuid'])
    if not entry['actual_whole_pad_layers_all_source_rooted']:bad.append(entry);unrooted.append({'signed_group':group['label'],**entry})
  mapped.append({'label':group['label'],'signed_total_a':group['signed_total_a'],'actual_distinct_physical_pad_UUIDs':sorted(set(ids)),'unrooted_candidates':bad,'within_group_distribution':group['within_group_distribution'],'no_equal_sharing_or_unrooted_candidate_exclusion':True})
 put(O/'signed-group-actual-UUID-simplex-mapping.json',mapped);put(O/'unrooted-signed-physical-endpoints.json',unrooted);put(O/'missing-signed-logical-selectors.json',missing);put(O/'all-actual-distinct-signed-pad-ports.json',list(unique.values()));faces={};facerows=[];barrels=[]
 for l in K.LAYERS:
  shape=unary_union([r['shape']for r in lg if r['layer']==l]);f=O/(l+'-actual-rooted-drilled-sheet.wkb');f.write_bytes(shape.wkb);parts=RF.parts(shape);faces[l]=parts;tree=STRtree(parts);facerows.append({'layer':l,'exact_drilled_union_sha256':sha(f),'area_mm2':shape.area,'actual_face_count':len(parts),'total_boundary_vertices':sum(len(p.exterior.coords)+sum(len(r.coords)for r in p.interiors)for p in parts),'largest_face_mm2':max((p.area for p in parts),default=0)});print('R269_SHEET',l,facerows[-1]['area_mm2'],len(parts),facerows[-1]['total_boundary_vertices'],flush=True)
 viaoriginal={v['uuid']:v for v in g['vias']};padroot={p['uuid']:p for p in h['pads']if p['net']=='/LOGIC_GND'and p.get('hole')}
 for v in h['vias']:
  if v['net']!='/LOGIC_GND':continue
  layers=[l for l in v['flashed']if('via',v['uuid'],l)in rootkeys]
  if not layers:continue
  native=viaoriginal.get(v['uuid']);barrels.append({'kind':'via','UUID':v['uuid'],'at':[v['x'],v['y']],'diameter_mm':v['d'],'drill_mm':v['drill'],'literal_flashed_layers':v['flashed'],'rooted_contact_layers':layers,'native_original_record':native,'prospective_NOT_native':native is None or native.get('flashed')!=v['flashed']})
 for uid,p in padroot.items():
  layers=[l for l in p['layers']if('pad',uid,l)in rootkeys]
  if layers:barrels.append({'kind':'plated_pad','UUID':uid,'ref':p['ref'],'pin':p['num'],'at':[p['x'],p['y']],'literal_pad_hole':p['hole'],'rooted_contact_layers':layers,'native_actual_pad_record':p})
 put(O/'all-actual-or-explicit-prospective-rooted-ground-barrels.json',barrels);put(O/'actual-drilled-sheet-size-rows.json',facerows);put(O/'native-provisional-stackup.json',h['stackup']);fg=[p for p in h['pads']if p['ref']=='U1001'and p['net']=='/LOGIC_GND'];result={'verdict':'SIGNED_MULTIPATH_PHYSICAL_INVENTORY_FULL_SOLVER_OPEN','exact_R265_diagnostic_model_sha256':sha(mp),'actual_drilled_groups_sha256':sha(gp),'signed_source_ledger_sha256':sha(pfile),'signed_source_export_sha256':sha(actualsource),'signed_group_count':len(mapped),'signed_sum_a':sum(r['signed_total_a']for r in mapped),'fixed_actual_J11001_2_source_sink_a':-3.9931149887647366,'unique_actual_signed_pad_UUID_count':len(unique),'missing_logical_selector_count':len(missing),'unrooted_group_endpoint_count':len(unrooted),'full_shared_signed_LG_mesh_bound_requires_every_candidate_or_explicit_missing_path_fail':True,'all31_package_ground_pads_rooted':all(all(('pad',p['uuid'],l)in rootkeys for l in p['layers'])for p in fg),'FPGA_ground_pad_count':len(fg),'actual_or_explicit_prospective_ground_barrel_count':len(barrels),'actual_flashed_masks_only_no_all6_assumption':True,'sheet_rows':facerows,'thin_sheet_barrel_plating_mesh_refinement_terminals_solver_current_allocation_convergence':'OPEN','no_face_zero_ohm_or_equal_sharing_capacity_claim':True,'full_CORE_0p8_IO3_2A_sharedLG3p993_not_reduced':True,'native_jobs':0,'board_written':False,'adopted':False};put(O/'receipt.json',result);print('R269_COMPLETE',sha(O/'receipt.json'),len(unique),len(unrooted),len(missing),len(barrels),flush=True)
if __name__=='__main__':main()
