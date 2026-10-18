"""Delete only R89-proven unrooted detached NEW CORE-zone components.

Both intended native outlines and physical copper are ledgered. No original
native zone definition, discrete copper, source item or moved pad is edited.
All final geometry/contact/current/native gates remain required.
"""
import copy,json,pickle,hashlib
from pathlib import Path
from shapely.ops import unary_union
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as GP
import io3_contact_restore_r2 as Q
L=G.L;p=G.p;O=L.OUT/'unused-new-core-fragment-removal-r91'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
    assert not O.exists();O.mkdir();(O/'source-used.py').write_bytes(Path(__file__).read_bytes())
    prior=L.OUT/'r17031-translated-source-composition-r78/model.pkl'
    assert sha(prior)=='128a21a83ccc8e1029f4b97e27930f82de743e00ef45fb1fc2041f0967b8a821'
    af=L.OUT/'full-power-source-contact-audit-r89/receipt.json'
    assert sha(af)=='0365dbeb7948c599a0e96996eac020f86bf9b519db656e7aa17a3775c265d957'
    audit=json.loads(af.read_text());g,h,binding,zones,candidate=pickle.loads(prior.read_bytes())
    row=next(r for r in audit['rows'] if r['net_normalized_for_lookup_only']==p.norm(L.stage.caps.CORE))
    old_ids={q['uuid'] for q in g['zones']};rows=[];out=[]
    obligations={r['uuid']:r for r in row['new_zones']}
    for q in zones:
        ar=obligations.get(q['uuid']);bad=[r for r in ar['detached_components'] if not r['source_connected']] if ar else []
        if not bad:out.append(q);continue
        assert q['uuid'] not in old_ids
        physical=p.hubs.components(q['shape']);outline=p.hubs.components(q.get('zone_outline_shape',q['shape']))
        removed_phys=[];removed_outline=[];component_rows=[]
        for r in bad:
            assert r['groups']==[None],('not_unused',q['uuid'],r)
            piece=physical[r['component_index']];assert digest(piece)==r['shape_wkb_sha256']
            ids=[i for i,s in enumerate(outline) if s.intersection(piece).area>0]
            assert len(ids)==1;ii=ids[0];other=outline[ii]
            # Existing own drilled holes may distinguish physical/intended,
            # but no source-connected physical component may share an outline.
            assert all(i==r['component_index'] or other.intersection(s).area==0 for i,s in enumerate(physical))
            removed_phys.append(piece);removed_outline.append(ii)
            component_rows.append({**r,'physical_bounds':list(piece.bounds),'outline_component_index':ii,'outline_removed_WKB_sha256':digest(other),'outline_removed_area_mm2':other.area,'only_new_source_free_Cu_component':True})
        nq=copy.deepcopy(q);nq['shape']=unary_union([s for i,s in enumerate(physical) if i not in {r['component_index'] for r in bad}]);nq['zone_outline_shape']=unary_union([s for i,s in enumerate(outline) if i not in set(removed_outline)])
        assert not nq['shape'].is_empty and not nq['zone_outline_shape'].is_empty
        assert nq['shape'].difference(q['shape']).is_empty
        assert nq['zone_outline_shape'].difference(q.get('zone_outline_shape',q['shape'])).is_empty
        paths={}
        for role,s in [('physical-before',q['shape']),('physical-after',nq['shape']),('outline-before',q.get('zone_outline_shape',q['shape'])),('outline-after',nq['zone_outline_shape'])]:
            f=O/(q['uuid']+'.'+role+'.wkb');f.write_bytes(s.wkb);paths[role]={'file':str(f.resolve()),'sha256':sha(f),'area_mm2':s.area}
        rows.append({'uuid':q['uuid'],'label':q.get('label'),'raw_net':q['net'],'layer':q['layer'],'components':component_rows,'geometry':paths,'no_foreign_original_or_owned_Cu_definition_edited':True});out.append(nq)
    assert sum(len(r['components']) for r in rows)==11
    lf=O/'exact-new-only-fragment-deletion-ledger.json';lf.write_text(json.dumps(rows,indent=2)+'\n')
    binding['explicit_unused_new_CORE_component_removal']={'authorizing_source_audit_file':str(af.resolve()),'sha256':sha(af),'exact_deleted_new_components':11,'ledger_file':str(lf.resolve()),'ledger_sha256':sha(lf),'original_native_zone_and_discrete_definitions_untouched':True}
    checkpoint=O/'checkpoint-model.pkl';checkpoint.write_bytes(pickle.dumps((g,h,binding,out,None),protocol=5))
    print('CORE_NEW_FRAGMENTS_EXPLICITLY_REMOVED',11,'areas',sum(r['area_mm2'] for x in rows for r in x['components']),flush=True)
    candidate,cuts=GP.projected(g,h,out)
    Q.NET=p.norm(L.stage.caps.CORE);groups,parts,assign=Q.groups(candidate,return_details=True);lookup={q['uuid']:i for i,rs in enumerate(groups) for q in rs};sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));root=lookup[sp['uuid']]
    bare=[q for i,rs in enumerate(groups) if i!=root for q in rs if not q['ref'].startswith('@')]
    unrooted=[]
    for q in out:
        if p.norm(q['net'])!=Q.NET:continue
        for i,s in enumerate(p.hubs.components(q['shape'])):
            hits={j for piece,j in zip(parts[q['layer']],assign[q['layer']]) if piece.intersection(s).area>0}
            if hits!={root}:unrooted.append({'uuid':q['uuid'],'component_index':i,'groups':sorted(hits,key=lambda x:(x is None,x or -1)),'area_mm2':s.area})
    assert not bare and not unrooted,(bare,unrooted)
    model=O/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,out,candidate),protocol=5))
    (O/'receipt.json').write_text(json.dumps({'verdict':'UNUSED_NEW_CORE_COMPONENTS_REMOVED_ALL_CORE_NAMED_AND_NEW_COMPONENTS_SOURCE_ROOTED_FINAL_GATES_OPEN','parent_model_sha256':sha(prior),'model_sha256':sha(model),'checkpoint_sha256':sha(checkpoint),'ledger_sha256':sha(lf),'removed_new_components':11,'CORE_bare_named_pads':bare,'CORE_unrooted_new_components':unrooted,'old_fill_retreats':cuts,'original_zone_native_definitions_and_discrete_Cu_unchanged':True,'all_original_power_contacts_current_and_full_native_gates':'OPEN','native_jobs':0,'board_written':False},indent=2)+'\n')
    print('ALL_CORE_COMPONENTS_SOURCE_ROOTED',sha(model),flush=True)
if __name__=='__main__':main()
