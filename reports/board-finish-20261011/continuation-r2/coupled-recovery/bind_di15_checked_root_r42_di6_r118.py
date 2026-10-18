"""Bind exact checked ROOT R42 and project only native-bound DI6 items.

All prior LOGIC_GND source keys must survive their exact body/hole cuts.
No board, source, rule or native mutations; only one current model is used.
"""
import sys,json,pickle,copy,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE.parent/'sbc-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_di6_direct_latest_power_r8 as D
import audit_c10036_r24_full_independent_r30 as Q
import guarded_power_projection_r44 as Z
import complete_geometry_r2 as GE
from shapely.geometry import LineString
from shapely.ops import unary_union
C=A.C
def main():
 started=time.monotonic();out=HERE/'di15-safe-root-r42-DI6-bind-r118.json';cache=HERE/'di15-current-safe-root-r42-DI6-r118.pkl';assert not out.exists() and not cache.exists();A.read(__file__)
 path=HERE.parent/'logic-two-reference-safe-return-restoration-r42/model.pkl';raw=A.read(path);assert C.sha(raw)=='a4baedbfbccc92930a22c946b1e4e5262287d59b60b2a1e529bfddfa75c398ba';old,h,binding,zones,before=pickle.loads(raw);h=copy.deepcopy(h);zones=copy.deepcopy(zones);assert before is not None
 receiptpath=path.with_name('receipt.json');receipt=json.loads(A.read(receiptpath));assert C.sha(A.read(receiptpath))=='c3662517d5484fd59d111be0e65881564de9700a64c80419ce0e55a9235b4e28';assert receipt['model_sha256']==C.sha(raw) and receipt['new_zone_shapes']==2 and receipt['new_holes']==0 and receipt['old_Cu_deleted']==0 and receipt['old_native_zone_outlines_changed']==0
 snap=path.with_name('proposed-zones.pkl');assert C.sha(A.read(snap))==receipt['proposed_zones_sha256']=='6dade25d3aced12036dcd56ef8bbec590f5bd721ec47bd83435cd3ad2186b114'
 independentpath=HERE.parent/'logic-two-independent-full-r43/receipt.json';independent=json.loads(A.read(independentpath));assert C.sha(A.read(independentpath))=='c0688d943d936947bb21ce60b7afc57574e5c4220db00ff7349b6b4821a0f0b3';assert independent['model_sha256']==C.sha(raw) and independent['added_zones_sha256']==receipt['proposed_zones_sha256'] and independent['all_original_Cu_holes_source_poses_native_outlines_unchanged_to_parent'];assert independent['verdict']=='PASS_TWO_NEW_LOGIC_PIECES_FULL_OLD_ZONE_NET_CONTACT_SOURCE_REFERENCE_HOST_GEOMETRY_NATIVE_CURRENT_OPEN'
 assert all(not q['old_discrete_contact_losses'] for q in independent['affected_net_contacts']);assert all(independent[k]==0 for k in ('physical_error_count','foreign_new_zone_error_count','foreign_hole_error_count','native_no_zone_area_error_count'));assert independent['all_old_zone_bearing_net_count']==76
 A.read(independentpath.with_name('reference-checkpoint.json'));A.read(independentpath.with_name('contact-checkpoint.json'))
 rp=HERE/'di6-reference-corrected-full-audit-r11.json';r11=json.loads(A.read(rp));assert C.sha(A.read(rp))=='d6468fbf689a15f94e157318067358eec8c323eda202355194f9cde41879a8cb';cpp=HERE/'di6-reference-r11-physical-checkpoint.pkl';cpraw=A.read(cpp);assert C.sha(cpraw)==r11['immutable_physical_checkpoint_sha256']=='d2eada8116e69f25e1cc8631e95f3c81de4d87a255b5098eed1b28c0e2a27570';cp=pickle.loads(cpraw);nt=cp['nt'];nv=cp['nv'];assert len(nt)==9 and len(nv)==2
 assert binding['exact_native_discrete_board_sha256']==r11['source_parent_sha256'];assert C.sha(A.read(binding['exact_native_discrete_board_file']))==r11['source_parent_sha256']
 print('DI15_R118_SAFE_ROOT_BEFORE_EXACT_PHYSICAL_SOURCE_BEGIN',flush=True);oldrefs,oldUF,oldgroups,oldroot=D.root_reference(before)
 for k,added in(('tracks',nt),('vias',nv)):
  ids={q['uuid'] for q in h[k]};assert not ids&{q['uuid'] for q in added};h[k]+=copy.deepcopy(added)
 fillrows=[];afterzones=[]
 for z in before['zones']:
  nz={**z,'fills':{}};local=float(z.get('clearance_mm',.15));net=L.norm(z['net'])
  for l,rs in z['fills'].items():
   original=unary_union(L.poly(rs));cutters=[];cutrows=[]
   for t in nt:
    n=L.norm(t['net'])
    if t['layer']!=l or n==net:continue
    domain=.15 if h['domains_normalized'].get(net)==h['domains_normalized'].get(n) else .6;radius=t['w']/2+max(domain,local)+.025;cut=Z.bounded_buffer(LineString([t['a'],t['b']]),radius)
    if cut.intersects(original):cutters.append(cut);cutrows.append({'uuid':t['uuid'],'kind':'track','radius_mm':radius,'WKB_sha256':C.sha(cut.wkb)})
   for v in nv:
    n=L.norm(v['net'])
    if n==net:radius=v['drill']/2
    else:domain=.15 if h['domains_normalized'].get(net)==h['domains_normalized'].get(n) else .6;radius=max(v['drill']/2+.275,v['d']/2+max(domain,local)+.025)
    cut=Z.bounded_disk(v,radius)
    if cut.intersects(original):cutters.append(cut);cutrows.append({'uuid':v['uuid'],'kind':'via','radius_mm':radius,'WKB_sha256':C.sha(cut.wkb)})
   rem=original.difference(unary_union(cutters));nz['fills'][l]=GE.records(rem)
   if cutters:fillrows.append({'zone_UUID':z['uuid'],'layer':l,'net':z['net'],'native_or_proposed_local_mm':local,'before_WKB_sha256':C.sha(original.wkb),'after_WKB_sha256':C.sha(rem.wkb),'removed_mm2':original.difference(rem).area,'cutters':cutrows})
  afterzones.append(nz)
 after={**before,'tracks':h['tracks'],'vias':h['vias'],'zones':afterzones};print('DI15_R118_ONLY_DI6_PROJECTED_AFTER_DRILLED_SOURCE_BEGIN',flush=True);refs,uf,groups,root=D.root_reference(after);lost=sorted(Q.discrete_keys(oldroot)-Q.discrete_keys(root));planes={l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==l]) for l in Q.LAYERS};result={'h':h,'old':old,'binding':binding,'before':before,'after':after,'zones':zones,'refs':refs,'source_planes':planes,'groups':groups,'root':root,'ROOT_checked_R42_model_sha256':C.sha(raw),'ROOT_checked_R42_receipt_sha256':C.sha(A.read(receiptpath)),'DI6_owned_checkpoint_sha256':C.sha(cpraw),'exact_DI6_incremental_projection_ledger':fillrows,'only_LOGIC_GND_source_recomputed_after_drills':True};cache.write_bytes(pickle.dumps(result,protocol=5));report={'verdict':'CHECKED_ROOT_R42_EXACT_OWN_DI6_DRILLED_SOURCE_BOUND_NOMINATION_ONLY' if not lost else'CHECKED_ROOT_R42_DI6_SOURCE_LOSS_INCOMPLETE','model_path':str(cache),'model_sha256':C.sha(cache.read_bytes()),'ROOT_checked_R42_model_sha256':C.sha(raw),'ROOT_checked_R42_receipt_sha256':C.sha(A.read(receiptpath)),'source_parent_sha256':r11['source_parent_sha256'],'DI6_owned_checkpoint_sha256':C.sha(cpraw),'added_tracks':9,'added_vias':2,'other_items_changed':0,'LOGIC_GND_J11001_2_prior_source_keys_lost':lost,'actual_rooted_unique_pad_count':len({q['uuid'] for q in root if q['kind']=='pad'}),'projection_ledger':fillrows,'DI6_matched_native_remote_three_reference_slivers':'OPEN','joint_all_reference_contacts_signed_supply_current_native_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'model_sha256':report['model_sha256'],'source_losses':lost,'rooted_pads':report['actual_rooted_unique_pad_count']}),flush=True)
if __name__=='__main__':main()
