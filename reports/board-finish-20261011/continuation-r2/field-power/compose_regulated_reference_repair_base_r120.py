"""Remove only two failed new reference walls, retain four constructive feeds."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely.ops import unary_union
from shapely import STRtree
from shapely.geometry import box
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_power_projection_r44 as P
O=H/'regulated-reference-wall-repair-base-r120'
DROP={'c70aed70-d8e0-5712-8468-097b177d3c8a','e7367999-5e27-5c2f-a1c8-628b55d61bcd'}
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'corrected-regulated-native-bound-search-base-r111';g,h,b,z,prior=pickle.loads((base/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z)
 rr=H/'regulated-source-contact-reference-audit-r116';full=pickle.loads((rr/'proposed-zones.pkl').read_bytes());assert {q['uuid'] for q in full if q['uuid'] in DROP}==DROP
 retained=[q for q in full if q['uuid'] not in DROP];d=pickle.loads((H/'regulated-quantized-inner-source-feeds-r114/proposed-discrete.pkl').read_bytes());h['vias']+=d['vias'];h['tracks']+=d['tracks'];z+=retained
 rp=H.parent/'logic-return-r18-snapshot-1';assert sha(rp/'proposed-zones.pkl')=='943d222e160f478d8cc351f63489b5b07a4ef380a326e81b8e6f2a6d13a05a42';lg=pickle.loads((rp/'proposed-zones.pkl').read_bytes());assert len(lg)==7 and not {q['uuid'] for q in lg}&{q['uuid'] for q in z};z+=lg
 oldgroups=pickle.loads((H/'regulated-reference-contact-diagnostic-r119/old-ground-groups.pkl').read_bytes());masks={};rows=[]
 for net,root in [('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/LOGIC_GND','J11001')]:
  gs=oldgroups[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(root,'2') for q in xs));dom=h['domains_normalized'][net]
  for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]:
   ref=unary_union([q['shape'] for q in gs[ri] if q['kind']=='fill' and q['layer']==inner]);pieces=[];count=0
   for t in prior['tracks']:
    if t['layer']!=outer or C.norm(t['net'])==net or prior['domains_normalized'].get(C.norm(t['net']))!=dom:continue
    count+=1
    env=box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2) if not t.get('m') else C.body(t).envelope
    if ref.intersects(env):
     sh=C.body(t).intersection(ref)
     if not sh.is_empty:pieces.append(sh)
   mask=unary_union(pieces);masks[(net,inner)]=mask;(O/(root+'-'+inner+'-full-original-reference-mask.wkb')).write_bytes(mask.wkb);rows.append({'ground':net,'layer':inner,'outer_layer':outer,'eligible_tracks':count,'actual_old_source_reference_area_mm2':mask.area,'WKB_sha256':P.digest(mask)});print('R120 reference mask',root,inner,count,len(pieces),flush=True)
 b['regulated_R114_actual_owned_delta']={'receipt_file':str((H/'regulated-quantized-inner-source-feeds-r114/receipt.json').resolve()),'receipt_sha256':sha(H/'regulated-quantized-inner-source-feeds-r114/receipt.json'),'retained_four_zone_UUIDs':[q['uuid'] for q in retained],'explicitly_withdrawn_only_failed_new_zone_UUIDs':sorted(DROP),'new_via_UUIDs':[q['uuid'] for q in d['vias']],'new_track_UUIDs':[q['uuid'] for q in d['tracks']]}
 b['ROOT_R18_actual_seven_LOGIC_spines']={'receipt_file':str((rp/'receipt.json').resolve()),'receipt_sha256':sha(rp/'receipt.json'),'zones_sha256':sha(rp/'proposed-zones.pkl'),'UUIDs':[q['uuid'] for q in lg],'independent_REG_mutual_receipt_sha256':sha(H/'regulated-root-logic-spine-mutual-r118/receipt.json'),'source_native_current_final_recheck_required':True}
 b['field_regulated_search_hard_nominees']['source_qualified_peer_ROOT_spine_UUIDs_hard']+= [q['uuid'] for q in lg]
 b['regulated_old_source_reference_hard_masks']={'pickle_file':str((O/'reference-masks.pkl').resolve()),'scope':'Every retained same-domain outer track intersection with R111 actual source-rooted In1/In4 fill; original physical mask, no expansion; planner adds declared clearance and guard.'}
 print('R120 fresh full guarded projection',len(z),flush=True);after,cuts=P.projected(g,h,z)
 (O/'reference-masks.pkl').write_bytes(pickle.dumps(masks,protocol=5));write(O/'reference-mask-ledger.json',rows);(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'retained-R114-zones.pkl').write_bytes(pickle.dumps(retained,protocol=5));write(O/'oldfill-retreats.json',cuts)
 write(O/'receipt.json',{'verdict':'CONCRETE_TWO_WALL_WITHDRAWAL_FOR_SOURCE_REFERENCE_REBUILD','model_sha256':sha(O/'model.pkl'),'R111_base_sha256':sha(base/'model.pkl'),'failed_R116_receipt_sha256':sha(rr/'receipt.json'),'retained_R114_four_zone_SHA256':sha(O/'retained-R114-zones.pkl'),'retained_R114_vias':len(d['vias']),'retained_R114_tracks':len(d['tracks']),'withdrawn_only_new_zone_UUIDs':sorted(DROP),'owned_new_return_restored_from_R111':'98928f26-b6d6-5eb4-8ceb-454f2b717b88','ROOT_R18_seven_zones_sha256':sha(rp/'proposed-zones.pkl'),'full_reference_masks_sha256':sha(O/'reference-masks.pkl'),'reference_mask_ledger_sha256':sha(O/'reference-mask-ledger.json'),'oldfill_ledger_sha256':sha(O/'oldfill-retreats.json'),'source_contact_reference_current_native_gates':'OPEN','board_written':False,'native_jobs':0});print('R120 frozen',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
