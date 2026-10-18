"""Bind completed exact LG R18 and incrementally project only owned DI6.

Rebuild the actual drilled LOGIC_GND source group, including adjacent In3
reference for ordinary In2 nomination. No native, board or live mutation.
"""
import sys,json,pickle,copy,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE.parent/'sbc-power'));sys.path.insert(0,str(HERE))
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
 started=time.monotonic();out=HERE/'di15-root-LG-r18-DI6-bind-r50.json';cache=HERE/'di15-current-root-LG-r18-DI6-r50.pkl';assert not out.exists() and not cache.exists();A.read(__file__)
 path=HERE.parent/'logic-source-union-reuse-return-restoration-r18/model.pkl';raw=A.read(path);assert C.sha(raw)=='20ae7a0558877ba76300f2163b920c77fe96c5861a930fb7b22570f665ad37b8';old,h,binding,zones,before=pickle.loads(raw);h=copy.deepcopy(h);zones=copy.deepcopy(zones);assert before is not None
 receiptpath=path.with_name('receipt.json');receipt=json.loads(A.read(receiptpath));assert receipt['model_sha256']==C.sha(raw) and receipt['new_holes']==0 and receipt['old_Cu_deleted']==0 and receipt['old_native_zone_outlines_changed']==0
 assert receipt['new_zone_shapes']==7 and receipt['baseline_model_sha256']=='24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8'
 proofs=json.loads(A.read(path.with_name('bank-proofs.json')));snap=path.with_name('proposed-zones.pkl');assert C.sha(A.read(snap))==receipt['proposed_zones_sha256']=='943d222e160f478d8cc351f63489b5b07a4ef380a326e81b8e6f2a6d13a05a42'
 for r in receipt['bank_source_proofs']:
  assert r['same_original_source_and_owned_source_zone_fills_in_wholeboard_projection'] and r['all_accepted_target_and_prior_root_pad_source_contacts_retained']
 rp=HERE/'di6-reference-corrected-full-audit-r11.json';r11=json.loads(A.read(rp));assert C.sha(A.read(rp))=='d6468fbf689a15f94e157318067358eec8c323eda202355194f9cde41879a8cb'
 cpp=HERE/'di6-reference-r11-physical-checkpoint.pkl';cpraw=A.read(cpp);assert C.sha(cpraw)==r11['immutable_physical_checkpoint_sha256']=='d2eada8116e69f25e1cc8631e95f3c81de4d87a255b5098eed1b28c0e2a27570';cp=pickle.loads(cpraw)
 assert binding['exact_native_discrete_board_sha256']==r11['source_parent_sha256'];assert C.sha(A.read(binding['exact_native_discrete_board_file']))==r11['source_parent_sha256'];nt=cp['nt'];nv=cp['nv'];assert len(nt)==9 and len(nv)==2
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
    if cut.intersects(original):cutters.append(cut);cutrows.append({'uuid':t['uuid'],'layer':l,'kind':'track','radius_mm':radius,'WKB_sha256':C.sha(cut.wkb)})
   for v in nv:
    n=L.norm(v['net'])
    if n==net:radius=v['drill']/2
    else:domain=.15 if h['domains_normalized'].get(net)==h['domains_normalized'].get(n) else .6;radius=max(v['drill']/2+.275,v['d']/2+max(domain,local)+.025)
    cut=Z.bounded_disk(v,radius)
    if cut.intersects(original):cutters.append(cut);cutrows.append({'uuid':v['uuid'],'layer':l,'kind':'via','radius_mm':radius,'WKB_sha256':C.sha(cut.wkb)})
   rem=original.difference(unary_union(cutters));nz['fills'][l]=GE.records(rem)
   if cutters:fillrows.append({'zone_UUID':z['uuid'],'layer':l,'net':z['net'],'native_or_proposed_local_mm':local,'before_WKB_sha256':C.sha(original.wkb),'after_WKB_sha256':C.sha(rem.wkb),'removed_mm2':original.difference(rem).area,'cutters':cutrows})
  afterzones.append(nz)
 after={**before,'tracks':h['tracks'],'vias':h['vias'],'zones':afterzones}
 print('DI15_EXACT_R18_ONLY_DI6_DRILLED_SOURCE_BEGIN',flush=True);refs,uf,groups,root=D.root_reference(after)
 planes={l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==l]) for l in Q.LAYERS}
 refs['In2_from_In1.Cu']=planes['In1.Cu'];refs['In2_from_In3.Cu']=planes['In3.Cu']
 result={'h':h,'old':old,'binding':binding,'before':before,'after':after,'zones':zones,'refs':refs,'source_planes':planes,'groups':groups,'root':root,'ROOT_LG_R18_model_sha256':C.sha(raw),'ROOT_LG_R18_receipt_sha256':C.sha(A.read(receiptpath)),'R18_seven_shapes_sha256':C.sha(A.read(snap)),'DI6_owned_physical_checkpoint_sha256':C.sha(cpraw),'exact_DI6_incremental_projection_ledger':fillrows,'LOGIC_GND_root_only_recomputed_after_actual_drills':True,'new_power_ground_planes_native_current_qualification':False}
 cache.write_bytes(pickle.dumps(result,protocol=5));rpads=sorted(q['uuid'] for q in root if q['kind']=='pad')
 report={'verdict':'ROOT_LG_R18_EXACT_OWN_DI6_DRILLED_SOURCE_BOUND_NOMINATION_ONLY','model_sha256':C.sha(cache.read_bytes()),'model_path':str(cache),'ROOT_LG_R18_model_sha256':C.sha(raw),'ROOT_LG_R18_receipt_sha256':C.sha(A.read(receiptpath)),'ROOT_LG_R18_bank_proofs_sha256':C.sha(A.read(path.with_name('bank-proofs.json'))),'R18_seven_shapes_sha256':C.sha(A.read(snap)),'source_parent_sha256':r11['source_parent_sha256'],'DI6_owned_checkpoint_sha256':C.sha(cpraw),'added_tracks':9,'added_vias':2,'other_items_changed':0,'LOGIC_GND_source_pad':'J11001.2','rooted_pad_UUIDs':rpads,'rooted_pad_count':len(set(rpads)),'rooted_plane_WKB_sha256':{l:C.sha(s.wkb) for l,s in planes.items()},'projection_ledger':fillrows,'proposed_planes_native_full_contact_all_other_domains_current_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started}
 out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'verdict':report['verdict'],'sha256':C.sha(out.read_bytes()),'rooted_pad_count':report['rooted_pad_count'],'model_sha256':report['model_sha256']}),flush=True)
if __name__=='__main__':main()
