"""Rebase exact R9 additions onto R48; replay owned return cuts outwards.

No stale R9 base model replaces the newer IO3/U15/LOGIC/CORE geometry.
Original native zone definitions remain byte-owned by the eedf parent.
"""
import copy,json,pickle,hashlib
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import core_inner_feed_r18 as I
import guarded_declared_settings_projection_r58 as GP
L=I.L;p=I.p;G=I.G;Q=I.Q
OUT=L.OUT/'core-protected-outward-joint-r59'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def keep(f,shape):f.write_bytes(shape.wkb);return {'file':str(f.resolve()),'sha256':sha(f),'area_mm2':shape.area}
def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'source-used.py').write_bytes(Path(__file__).read_bytes())
    parent=L.OUT/'remaining-core-feeds-r48/model.pkl';assert sha(parent)=='3e4e42806786d7d15f66f8029f674db50c4df235adcea16d2f5d7a19b7757baa'
    g,h,b,zones,prior=pickle.loads(parent.read_bytes());h=copy.deepcopy(h);binding=copy.deepcopy(b)
    rp=L.OUT.parent/'protected24-on-corrected-core-r9';assert sha(rp/'receipt.json')=='c84b6b19dc9a09b83b368a5e1df1c0f597a2a704cec3d13f23798f03603ae2db'
    rr=json.loads((rp/'receipt.json').read_text());df=rp/'proposed-discrete.pkl';zf=rp/'proposed-zones.pkl'
    assert sha(df)==rr['proposed_discrete_sha256'] and sha(zf)==rr['proposed_zones_sha256']
    d=pickle.loads(df.read_bytes());zs=pickle.loads(zf.read_bytes());assert len(d['vias'])==12 and len(d['tracks'])==12 and len(zs)==10
    for kind in ('vias','tracks'):
        assert not {q['uuid'] for q in h[kind]} & {q['uuid'] for q in d[kind]};h[kind]+=d[kind]
    assert not {q['uuid'] for q in zones}&{q['uuid'] for q in zs}
    # Preserve R48 own field-return geometry and all its preceding carves.
    # Recreate only the exact R9 intended ownership policy on CURRENT pieces.
    carves=[];result=[]
    for q in zones:
        cuts=[];objects=[]
        if q['layer'] in ('In1.Cu','In2.Cu','In4.Cu'):
            for bank,ret in [('FIELD_A_24V_PROTECTED','/motherboard_motors/FIELD_GND'),('FIELD_B_24V_PROTECTED','/motherboard_do/FIELD_B_0V')]:
                if p.norm(q['net'])!=ret:continue
                raw=next(v['net'] for v in d['vias'] if p.norm(v['net']).endswith(bank));clear=max(G.gap(h,q['net'],raw),float(q.get('clearance_mm',.15)))+.025
                for v in d['vias']:
                    if v['net']!=raw:continue
                    radius=max(v['drill']/2+.275,v['d']/2+clear);cuts.append(GP.bounded_disk(v,radius));objects.append({'kind':'via','uuid':v['uuid'],'analytic_radius_mm':radius})
                for t in d['tracks']:
                    if t['net']==raw and t['layer']==q['layer']:cuts.append(GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear));objects.append({'kind':'track','uuid':t['uuid'],'clearance_with_guard_mm':clear})
                for a in zs:
                    if a['net']==raw and a['layer']==q['layer']:cuts.append(GP.bounded_buffer(a['shape'],max(clear,float(a.get('clearance_mm',.15))+.025)));objects.append({'kind':'new_zone','uuid':a['uuid'],'clearance_with_guard_mm':clear})
        if not cuts:result.append(q);continue
        cutter=unary_union(cuts);before=q['shape'];outline=q.get('zone_outline_shape',before)
        after=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);oa=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6)
        if before.equals(after) and outline.equals(oa):result.append(q);continue
        files={role:keep(OUT/(q['uuid']+'.protected-'+role+'.wkb'),s) for role,s in [('physical-before',before),('physical-after',after),('outline-before',outline),('outline-after',oa),('cutter',cutter)]}
        carves.append({'zone_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'files':files,'objects':objects,'physical_removed_mm2':before.difference(after).area,'physical_quantization_added_mm2':after.difference(before).area,'outline_removed_mm2':outline.difference(oa).area,'outline_quantization_added_mm2':oa.difference(outline).area,'all_current_R48_contacts_and_prior_carves_remain_obligations':True})
        result.append({**q,'shape':after,'zone_outline_shape':oa})
    zones=result+zs
    # This explicitly carves the intended prospective-CORE-main-In2 for
    # new protected barrels, and preserves its source/retention obligations.
    normalized,via_ledger=GP.normalize_owned_via_guards(h,zones)
    byid={q['uuid']:q for q in zones}
    for row in via_ledger:
        q=byid[row['zone_uuid']];a=next(q for q in normalized if q['uuid']==row['zone_uuid'])
        row['geometry_files']={role:keep(OUT/(q['uuid']+'.foreign-via-'+role+'.wkb'),s) for role,s in [('physical-before',q['shape']),('physical-after',a['shape']),('outline-before',q.get('zone_outline_shape',q['shape'])),('outline-after',a['zone_outline_shape'])]}
    zones=normalized
    cf=OUT/'protected-current-owned-return-cut-ledger.json';write(cf,carves);vf=OUT/'all-owned-foreign-via-outward-cut-ledger.json';write(vf,via_ledger)
    binding.update({'joint_CORE_R48_file':str(parent.resolve()),'joint_CORE_R48_sha256':sha(parent),'joint_protected_R9_receipt_file':str((rp/'receipt.json').resolve()),'joint_protected_R9_receipt_sha256':sha(rp/'receipt.json'),'joint_protected_R9_discrete_sha256':sha(df),'joint_protected_R9_positive_zones_sha256':sha(zf),'protected_return_cut_ledger_file':str(cf.resolve()),'protected_return_cut_ledger_sha256':sha(cf),'all_owned_foreign_via_guard_ledger_file':str(vf.resolve()),'all_owned_foreign_via_guard_ledger_sha256':sha(vf),'guarded_joint_projector_file':str(Path(GP.__file__).resolve()),'guarded_joint_projector_sha256':sha(Path(GP.__file__)),'CORE_main_In2_disposition':'INTENDED_ACTUAL_NEW_SUPPLY_ZONE; retained, explicit foreign-via antipads, later deterministic UUID mapping required','original_native_zone_definitions_unchanged':True,'root_R9_stale_R38_base_not_overlaid':True,'three_CORE_wall_pads_pending':['U9001.10','R17031.1','U11007.6']})
    binding['restored_generated_grid_UUIDs']=sorted(set(binding.get('restored_generated_grid_UUIDs',[]))|{q['zone_uuid'] for q in carves+via_ledger})
    checkpoint=OUT/'owned-composition-checkpoint.pkl';checkpoint.write_bytes(pickle.dumps((g,h,binding,zones,None),protocol=5));write(OUT/'checkpoint-receipt.json',{'verdict':'EXACT_OWNED_REBASE_FROZEN_PROJECTION_ALL_GATES_PENDING','checkpoint_sha256':sha(checkpoint),'binding':binding,'native_jobs':0,'board_written':False})
    print('R59_OWNED_CHECKPOINT',sha(checkpoint),len(zones),len(carves),len(via_ledger),flush=True)
    # Source check uses the actual globally projected model; never a count of
    # accepted proposals or source contacts inherited from the old R9 clone.
    candidate,oldcuts=GP.projected(g,h,zones);Q.NET=I.NET;groups,_,_=Q.groups(candidate,return_details=True);lookup={q['uuid']:i for i,rs in enumerate(groups) for q in rs};sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));root=lookup[sp['uuid']]
    missing=[{'group':i,'pads':[q for q in rs if not q['ref'].startswith('@')]} for i,rs in enumerate(groups) if i!=root and any(not q['ref'].startswith('@') for q in rs)]
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,zones,candidate),protocol=5));write(OUT/'old-fill-outward-projection-ledger.json',oldcuts)
    receipt={'verdict':'EXACT_R48_R9_GUARDED_REBASE_SOURCE_SCOPE_FROZEN_FULL_CONTACT_GEOMETRY_NATIVE_PENDING','model_sha256':sha(model),'binding':binding,'CORE_source':'R11022.2','CORE_remaining':missing,'CORE_only_original_three_wall_pads_still_pending':{(q['ref'],q['pad']) for rs in missing for q in rs['pads']}=={('U9001','10'),('R17031','1'),('U11007','6')},'owned_return_carves':len(carves),'foreign_via_owned_shape_carves':len(via_ledger),'old_fill_projection_ledger_sha256':sha(OUT/'old-fill-outward-projection-ledger.json'),'original_native_zone_definitions_unchanged':True,'all_retained_old_contact_source_return_current_native_DRC_gates':'OPEN','native_jobs':0,'board_written':False}
    write(OUT/'receipt.json',receipt);print('R59_PROJECTED_MODEL',sha(model),len(missing),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
