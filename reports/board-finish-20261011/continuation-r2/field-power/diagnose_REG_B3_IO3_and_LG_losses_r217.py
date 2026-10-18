"""Exact two-net loss attribution; do not waive tiny reference holes."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
import fast_contacts as F
H=Path(__file__).resolve().parent
for name in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/name))
import regional_guarded_declared_projection_r140 as P
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
import complete_geometry_r2 as G
import physical_reference_losses_r1 as REF
from audit_field_io3_crossings_r15e import losses
O=H/'REG-B3-exact-IO3-and-LG-loss-attribution-r217'
def write(name,d):(O/name).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def restore(b,z):
 assert {q['new_generated_UUID'] for q in b['generated_precision_state_ledger']}=={q['uuid'] for q in z};b['restored_generated_grid_UUIDs']=sorted({q['uuid'] for q in z});restore_bound_generated_precision_states(b,z)
def subset_project(g,h,z,nets):return P.projected(g,{**h,'zones':[q for q in h['zones'] if C.norm(q['net']) in nets]},z)[0]
def main():
 assert not O.exists();O.mkdir();base=H/'U10017-wider-on-exact-IO3-audit-r195';g,bh,bb,bz,_=pickle.loads((base/'model.pkl').read_bytes());bh=copy.deepcopy(bh);bb=copy.deepcopy(bb);bz=copy.deepcopy(bz);restore(bb,bz)
 W=H.parent/'sbc-power/IO3-wider-minimal-validated-integration-packet-r201';wr=json.loads((W/'receipt.json').read_text(encoding='utf-8'));r=wr['only_one_owned_host_group_replacement'][0];old=next(q for q in bz if q['uuid']==r['old_UUID']);assert all(P.digest(old[role])==d['old_sha256'] for role,d in r['roles'].items());new=pickle.loads((W/'exact-owned-IO3-one-In3-group-replacement.pkl').read_bytes());new=new[0] if isinstance(new,list) else new
 for role in ('shape','zone_outline_shape'):new[role]=set_precision(new[role],1e-6,mode='pointwise')
 c554=next(v for v in bh['vias'] if v['uuid']=='c55416b9-e522-5cbf-9523-ddb093be9249');nq,_=P.normalize_owned_via_guards({**bh,'vias':[c554]},[new]);bz=[nq[0] if q['uuid']==old['uuid'] else q for q in bz]
 R=H/'REG-rebuilt-B3-on-wider-IO3-full-audit-r212';assert sha(R/'receipt.json')=='9ae7aaad547c1ada8a6874d4da7f367d1fc20cb5e3215c65e868443c74298128';ag,ah,ab,az,after=pickle.loads((R/'model.pkl').read_bytes());restore(ab,az);newq=pickle.loads((R/'new-owned-zones.pkl').read_bytes());newids={q['uuid'] for q in newq};bg={q['uuid']:q for q in bz};print('R217 two-net baseline',flush=True);before=subset_project(g,bh,bz,{'/IO_3V3','/LOGIC_GND'});oldio=F.graph(before,'/IO_3V3');newio=F.graph(after,'/IO_3V3');io=losses(oldio,newio);summaries=[]
 for row in io:
  groups=[]
  for label,keys in row['new_partitions'].items():
   xs=newio[int(label)];groups.append({'group':label,'retained_old_contact_count':len(keys),'named_pads':[{'UUID':q['uuid'],'ref':q['ref'],'pin':q['pin'],'layer':q['layer']} for q in xs if q['kind']=='pad'],'actual_bounds_mm':list(unary_union([q['shape'] for q in xs]).bounds),'actual_source_rooted':any(q['kind']=='pad' and(q['ref'],q['pin'])==('R18001','2') for q in xs)})
  summaries.append({'old_group':row['old_group'],'old_contact_count':row['old_discrete_count'],'partitions':groups})
 write('IO3-split-exact-physical-groups.json',summaries);withdrawals=[]
 for q in newq:
  trial=subset_project(ag,ah,[z for z in az if z['uuid']!=q['uuid']],{'/IO_3V3'});bad=losses(oldio,F.graph(trial,'/IO_3V3'));withdrawals.append({'withdraw_only_new_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'IO3_relationship_loss_count':len(bad)});print('R217 withdraw',q['uuid'],len(bad),flush=True);write('IO3-one-new-shape-withdrawal-checkpoint.json',withdrawals)
 oldlg=next(xs for xs in F.graph(before,'/LOGIC_GND') if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));newlg=next(xs for xs in F.graph(after,'/LOGIC_GND') if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));oldrefs={out:unary_union([q['shape'] for q in oldlg if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};newrefs={out:unary_union([q['shape'] for q in newlg if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};refrows=json.loads((R/'reference-rows.json').read_text(encoding='utf-8'));bad=next(q['retained_outer_reference_losses'] for q in refrows if q['ground']=='/LOGIC_GND');tm={q['uuid']:q for q in bh['tracks']};attribution=[]
 for row in bad:
  t=tm[row['uuid']];body=REF.A.shape({'kind':'segment',**t});lost=body.intersection(oldrefs[t['layer']]).difference(newrefs[t['layer']]);assert abs(lost.area-row['prior_source_reference_lost_mm2'])<1e-10;inner='In1.Cu' if t['layer']=='F.Cu' else 'In4.Cu';causes=[]
  for q in az:
   if q['layer']!=inner or C.norm(q['net'])=='/LOGIC_GND':continue
   prior=bg.get(q['uuid']);clear=max(G.gap(ah,q['net'],'/LOGIC_GND'),float(q.get('clearance_mm',.15)))+.025
   for local in sorted({float(z['clearance_mm']) for z in ah['zones'] if C.norm(z['net'])=='/LOGIC_GND' and inner in z['fills']}):
    dist=max(clear,local+.025);cut=P.bounded_buffer(q['shape'],dist);affected=lost.intersection(cut)
    if affected.area<1e-12:continue
    priorcut=P.bounded_buffer(prior['shape'],dist) if prior else Point().buffer(0);extra=cut.difference(priorcut);causes.append({'proposal_UUID':q['uuid'],'raw_net':q['net'],'native_old_local_clearance_mm':local,'declared_guarded_buffer_mm':dist,'new_proposal':q['uuid'] in newids,'affected_lost_area_mm2':affected.area,'physical_added_vs_parent_mm2':q['shape'].difference(prior['shape']).area if prior else q['shape'].area,'buffer_added_vs_parent_mm2':extra.area,'lost_area_in_buffer_added_mm2':lost.intersection(extra).area})
  lf=O/(row['uuid']+'.exact-lost-reference.wkb');lf.write_bytes(lost.wkb);attribution.append({**row,'lost_bounds_mm':list(lost.bounds),'exact_lost_shape_file':str(lf.resolve()),'sha256':sha(lf),'proposal_buffer_causes':causes})
 write('LOGIC-reference-loss-exact-proposal-attribution.json',attribution);write('receipt.json',{'verdict':'DIAGNOSTIC_ONLY_NO_CONTACT_OR_REFERENCE_WAIVER','failed_candidate_receipt_sha256':sha(R/'receipt.json'),'all_IO3_new_shape_withdrawals':withdrawals,'exact_IO3_split_groups_sha256':sha(O/'IO3-split-exact-physical-groups.json'),'LOGIC_attribution_sha256':sha(O/'LOGIC-reference-loss-exact-proposal-attribution.json'),'declared_geometry_and_guard_primitives_unchanged':True,'board_written':False,'native_jobs':0});print('R217 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
