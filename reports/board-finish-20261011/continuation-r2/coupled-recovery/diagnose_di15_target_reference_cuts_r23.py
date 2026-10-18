"""Exact retained-reference obligations blocking three ordinary DI15 sites."""
import sys,pickle,json,math,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'));sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import guarded_power_projection_r44 as Z
from shapely.geometry import Point,box
from shapely.ops import unary_union
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
NET='/motherboard_di/DI15_LOGIC';GND='/LOGIC_GND'
def main():
 started=time.monotonic();out=HERE/'di15-target-reference-cut-obligations-r23.json';assert not out.exists();A.read(__file__);r18path=HERE/'di15-target-exact-blocker-diagnostic-r18.json';r18=json.loads(A.read(r18path));assert C.sha(A.read(r18path))=='8db0d9bf6e1b54ef2007ecd7f7f60f242b66d6fd0c8b87b4c70ed462b154d645';raw=A.read(HERE/'di15-current-r78-projection-r13.pkl');assert C.sha(raw)=='2b272430cc2d0e2368a23c3d7aad25c3142010fdbec4ef6f2f78ff3239cd82c2';cp=pickle.loads(raw);h=cp['h'];refs=cp['refs'];win=box(129,110,134,116);localrefs={l:ref.intersection(win) for l,ref in refs.items()};domain=h['domains_normalized'];source=A.read(cp['binding']['exact_native_discrete_board_file']);inv=C.inventory(source);rows=[]
 for t in h['tracks']:
  l=t['layer'];net=L.norm(t['net'])
  if l not in refs or net==GND or domain.get(net)!=domain.get(GND):continue
  arc=L.body(t) if t.get('m') is not None else None;bounds=arc.envelope if arc is not None else box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2)
  if not bounds.intersects(win):continue
  body=arc if arc is not None else A.shape({'kind':'segment',**t});covered=body.intersection(localrefs[l])
  if covered.is_empty:continue
  rows.append((t,body,covered))
 results=[]
 for attemp in r18['attempts']:
  at=attemp['ordinary_signal_via_mm'];cut=Z.bounded_disk({'x':at[0],'y':at[1]},.525);losses=[]
  for t,body,covered in rows:
   loss=covered.intersection(cut)
   if loss.area<=1e-9:continue
   old=inv[4].get(t['uuid']);row={'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'a_mm':t['a'],'b_mm':t['b'],'width_mm':t['w'],'actual_prior_source_reference_loss_mm2':loss.area,'actual_Cu_distance_from_new_signal_center_mm':Point(at).distance(body),'loss_bounds_mm':loss.bounds,'loss_WKB_sha256':C.sha(loss.wkb),'exact_untouched_eedf_chunk_sha256':C.sha(old) if old else None,'owned_new_proposal_not_source_byte':old is None}
   if old:row['exact_original_chunk']=old.decode()
   losses.append(row)
  plane=[]
  for l,sh in localrefs.items():
   if l not in('F.Cu','In3.Cu'):continue
   missing=cut.difference(sh);bounds=missing.bounds if not missing.is_empty else None;holes=[{'UUID':v['uuid'],'raw_net':v['net'],'at_mm':[v['x'],v['y']],'d_mm':v['d'],'drill_mm':v['drill'],'actual_flash_layers':v['flashed'],'distance_to_proposed_site_mm':math.dist(at,(v['x'],v['y']))} for v in h['vias'] if math.dist(at,(v['x'],v['y']))<1.2];plane.append({'route_layer':l,'missing_full_owned_projection_disk_mm2':missing.area,'missing_bounds_mm':bounds,'near_actual_existing_vias':holes})
  results.append({'site_mm':at,'physical_F_path':attemp['F_points_mm'],'physical_all6_candidate_from_R18':True,'full_disk_reference_nomination_diagnosis':plane,'retained_current_reference_obligations_cut':losses})
 report={'verdict':'EXACT_DI15_TARGET_REFERENCE_OBLIGATIONS_NOMINATED_NO_RIPUP_OR_WAIVER','source_parent_sha256':C.sha(source),'R18_receipt_sha256':C.sha(A.read(r18path)),'R78_current_DI6_exact_checkpoint_sha256':C.sha(raw),'actual_full_body_prior_reference_candidates_in_local_window':len(rows),'site_diagnostics':results,'all_current_and_proposed_Cu_preserved':True,'constructor_independent_native_current_r06_r07_final_source_SI':'OPEN','native_jobs':0,'board_written':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sites':results,'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
