"""Classify all reference islands for coordinated plane/pad-access redesign."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict,Counter
import hashlib,json,pickle
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;OUT=HERE/'coordinated-power-reference-plane-plan-r1';PLAN=OUT/'plan.json';ACT=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';PADS=ROOT/'reports/board-finish-20261017/join-throughput-r1/native-pad-inventory.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();norm=lambda n:n.replace('{slash}','/')
def main():
 target=OUT/'bulk-batches-r2.json';assert not target.exists();plan=json.loads(PLAN.read_text());cache=ACT/'actual-combined-full-after-all-net-groups.pkl';graphs=pickle.loads(cache.read_bytes());pads=json.loads(PADS.read_text())['pads'];counts=Counter();rows=[]
 for r in plan['references']:
  net=r['net'];actual=graphs.get(net,[]);roots=[tuple(p)for p in r['source_ports']];primary=roots[:1];sourceids={i for i,xs in enumerate(actual)if any(q['kind']=='pad'and(q['ref'],str(q['pin']))in primary for q in xs)};uuidgroups=defaultdict(set)
  for i,xs in enumerate(actual):
   for q in xs:
    if q['kind']=='pad':uuidgroups[q['uuid']].add(i)
  sr=[q for i in sourceids for q in actual[i]];source_by_layer={l:[q for q in sr if q['layer']==l]for l in('F.Cu','B.Cu')};trees={l:STRtree([q['shape']for q in qs])for l,qs in source_by_layer.items()};floors={l:[q for q in sr if q['kind']=='fill'and q['layer']==l]for l in('In1.Cu','In4.Cu')};ft={l:STRtree([q['shape']for q in qs])for l,qs in floors.items()}
  for group in r['group_rows']:
   if any(k.startswith(ref+'.'+pin+'#')for k in group['physical_pad_keys']for ref,pin in primary):continue
   keys=group['physical_pad_keys'];uu={pads[k]['UUID']for k in keys};ids=set().union(*(uuidgroups[u]for u in uu));pr=[q for i in ids for q in actual[i]];via={q['uuid']for q in pr if q['kind']=='via'};pth={q['uuid']for q in pr if q['kind']=='pad'and sum(1 for z in pr if z['kind']=='pad'and z['uuid']==q['uuid'])>1};padrows=[q for q in pr if q['kind']=='pad'and q['uuid']in uu];floor_hits=[];surface=[]
   for q in padrows:
    ly=q['layer']
    if ly not in('F.Cu','B.Cu'):continue
    floor='In1.Cu'if ly=='F.Cu'else'In4.Cu';hits=ft[floor].query(q['shape'],predicate='intersects');area=sum(q['shape'].intersection(floors[floor][int(i)]['shape']).area for i in hits)
    if area>0:floor_hits.append({'pad_UUID':q['uuid'],'pad_layer':ly,'actual_root_floor':floor,'finite_projection_overlap_mm2':area})
    if source_by_layer[ly]:
     i=int(trees[ly].nearest(q['shape']));a=source_by_layer[ly][i];surface.append({'pad_UUID':q['uuid'],'layer':ly,'source_electrode_kind':a['kind'],'source_electrode_UUID':a['uuid'],'edge_gap_mm':q['shape'].distance(a['shape'])})
   if not roots:kind='chassis_bond_and_shield_network_requires_designated_mechanical_root'
   elif ids&sourceids:kind='native_pad_group_vs_drilled_R299_graph_disagreement_hold_for_native_rebuild'
   elif not ids:kind='native_pad_keys_missing_from_R299_graph_hold_source_binding'
   elif via or pth:kind='existing_layer_entry_reconstruct_wide_plane_to_plane_or_plane_to_port_corridor'
   elif floor_hits:kind='surface_only_pad_access_above_real_source_floor_needs_bank_ground_access_pattern'
   else:kind='surface_only_pad_access_and_no_real_source_floor_extend_domain_region_or_reposition_bank'
   counts[kind]+=1;rows.append({'domain':r['domain'],'net':net,'native_group':group['native_group'],'pad_count':group['pad_count'],'pad_keys':keys,'bounds_mm':group['bounds_mm'],'classification':kind,'retained_actual_via_UUIDs':sorted(via),'retained_PTH_pad_UUIDs':sorted(pth),'source_floor_projection_hits':floor_hits,'nearest_actual_same_layer_source_Cu':sorted(surface,key=lambda x:x['edge_gap_mm'])[:1],'no_route_clearance_capacity_or_source_closure_claimed':True})
 result={'utc':datetime.now(timezone.utc).isoformat(),'status':'ALL_MAJOR_REFERENCE_GROUPS_CLASSIFIED_FOR_COORDINATED_BANK_PLANES_AND_ACCESS_NO_ROUTING','input_sha256':{str(p):sha(p)for p in(PLAN,cache,PADS,Path(__file__))},'classification_counts':dict(counts),'reference_groups_reviewed':len(rows),'primary_source_policy':'Only first declared source pad is an established root. Other same-net producer/filter-return ports must be physically joined before their floor can be used; no virtual union across source components.','groups':rows,'interpretation':'Existing entries support plane-first connection; surface-only pads require a current/return-qualified bank access pattern or surface resource. A plane drawn underneath is not an electrical join. Projection/nearest distances are diagnosis only, not route approval.','PTH_detection':'Retained same pad UUID occurring on multiple copper layers in actual drilled graph; no new drill or flash layer assumed.','native_jobs':0,'board_changed':False,'adopted':False};target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'counts':result['classification_counts'],'groups':len(rows)}))
if __name__=='__main__':main()
