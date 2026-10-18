"""Freeze R42 IO3 plus exact U15/R57 corrections with explicit outward cuts."""
import copy,json,pickle,hashlib,sys
from pathlib import Path
import core_inner_feed_r18 as I
import guarded_power_projection_r44 as P
L=I.L;Q=I.Q;NET=I.NET;OUT=L.OUT/'io3-u15-logic-guarded-model-r47';FIELD=I.FIELD
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();prior=L.OUT/'owned-io3-layer-escape-repair-r42/model.pkl'
    assert sha(prior)=='dc06d1688f700a4c0232ee948ebbdfba6d4af931a9918f5521b1914de194ce68'
    g,h,binding,zones,_=pickle.loads(prior.read_bytes());h=copy.deepcopy(h)
    r44=FIELD/'u11015-reverse-companion-repair-r44';rr=json.loads((r44/'receipt.json').read_text())
    assert sha(r44/'receipt.json')=='590b1d52ff80afbccc311a5e157cade34a917dc59eb646643c9b45185a5e992d'
    d=pickle.loads((r44/'proposed-discrete.pkl').read_bytes());assert sha(r44/'proposed-discrete.pkl')==rr['proposed_discrete_sha256']
    old={q['uuid']:q for q in h['tracks']};removals=rr['owned_original_track_removals'];assert len(removals)==6
    for q in removals:assert old[q['uuid']]==q
    remove={q['uuid'] for q in removals};h['tracks']=[q for q in h['tracks'] if q['uuid'] not in remove]
    for kind in ('tracks','vias'):
        assert not {q['uuid'] for q in h[kind]} & {q['uuid'] for q in d[kind]};h[kind]+=d[kind]
    recipe=FIELD/'u11015-native-recipe-r48/receipt.json';assert sha(recipe)=='4a91742f8d735411d73b23ec5a042879e908685f9bad58328a6f367752863e15'
    binding.setdefault('existing_native_owned_Cu_removal_recipes',[]).append({'file':str(recipe.resolve()),'sha256':sha(recipe),'recipe_type':'delete_rows'})
    r57=FIELD/'logic-outward-guard-repair-r57';r57r=json.loads((r57/'receipt.json').read_text());zf=r57/'proposed-zones.pkl';assert sha(zf)==r57r['proposed_zones_sha256'];adds=pickle.loads(zf.read_bytes());assert len(adds)==2
    assert not {q['uuid'] for q in zones} & {q['uuid'] for q in adds};zones+=adds
    binding['field_U15_R44_and_R48_overlay']={'R44_receipt_sha256':sha(r44/'receipt.json'),'native_recipe_file':str(recipe.resolve()),'native_recipe_sha256':sha(recipe),'vias':3,'tracks':12,'exact_removed_existing_tracks':sorted(remove)}
    binding['field_LOGIC_R57_guarded_two_branch_repairs']={'receipt_file':str((r57/'receipt.json').resolve()),'receipt_sha256':sha(r57/'receipt.json'),'proposed_zones_sha256':sha(zf),'zones':2,'complete_mutual_guarded_projection_after_overlay':'REQUIRED'}
    before={q['uuid']:q for q in zones};zones,guards=P.normalize_owned_via_guards(h,zones)
    for r in guards:
        uid=r['zone_uuid'];b=before[uid];a=next(z for z in zones if z['uuid']==uid)
        for role,shape in [('physical-before',b['shape']),('physical-after',a['shape']),('outline-before',b.get('zone_outline_shape',b['shape'])),('outline-after',a['zone_outline_shape'])]:
            f=OUT/(uid+'.'+role+'.wkb');f.write_bytes(shape.wkb);r[role+'_file']=str(f.resolve());r[role+'_sha256']=sha(f)
    gf=OUT/'owned-new-via-outward-cut-ledger.json';gf.write_text(json.dumps(guards,indent=2)+'\n')
    binding['final_outward_circle_new_owned_zone_cut_ledger']={'file':str(gf.resolve()),'sha256':sha(gf),'changed_zone_count':len(guards),'circle_edges':256,'outward_guard_nm':2,'geometry_grid_nm':1}
    binding['final_outward_projection_helper']={'file':str(Path(P.__file__).resolve()),'sha256':sha(Path(P.__file__)),'changed_old_fill_via_circle_and_track_cap_guards':True,'old_native_zone_definitions_settings_untouched':True}
    binding['restored_generated_grid_UUIDs']=sorted(set(binding.get('restored_generated_grid_UUIDs',[]))|{q['uuid'] for q in adds}|{r['zone_uuid'] for r in guards})
    candidate,cuts=P.projected(g,h,zones);cf=OUT/'old-effective-fill-outward-cut-ledger.json';cf.write_text(json.dumps(cuts,indent=2)+'\n')
    Q.NET=NET;groups,_,_=Q.groups(candidate,return_details=True);ids={q['uuid']:i for i,rr in enumerate(groups) for q in rr};sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));root=ids[sp['uuid']]
    remaining=[{'group':i,'pads':[q for q in rows if not q['ref'].startswith('@')]} for i,rows in enumerate(groups) if i!=root and any(not q['ref'].startswith('@') for q in rows)]
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,zones,candidate),protocol=5))
    receipt={'verdict':'GUARDED_COMPOSED_PROPOSAL_SOURCE_CENSUS_FINAL_MUTUAL_GATES_REQUIRED','model_sha256':sha(model),'parent_R42_model_sha256':sha(prior),'U44_R48_recipe_sha256':sha(recipe),'R57_receipt_sha256':sha(r57/'receipt.json'),'helper_sha256':sha(Path(P.__file__)),'new_owned_zone_cut_ledger_sha256':sha(gf),'old_fill_outward_cut_ledger_sha256':sha(cf),'new_owned_zone_guard_changes':len(guards),'old_fill_retreats':len(cuts),'remaining_CORE_groups':len(remaining),'remaining_CORE_pads':sum(len(r['pads']) for r in remaining),'remaining':remaining,'binding':binding,'all_contact_source_current_native':'OPEN','original_native_zone_definitions_unchanged':True,'native_jobs':0,'board_written':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('GUARDED_R47_FROZEN',sha(model),'remaining',len(remaining),sum(len(r['pads']) for r in remaining),flush=True)
if __name__=='__main__':main()
