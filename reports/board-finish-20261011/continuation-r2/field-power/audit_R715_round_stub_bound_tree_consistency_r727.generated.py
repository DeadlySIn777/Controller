"""Explicit new-stub cap representation and direct drilled source proof.

The R721 graph-body mismatch is retained. Only the declared NEW .5 B stub
gets a 128-quadrant cap representation; every old graph row is byte exact.
Native Cu remains nominal width .5 and is not rewritten by this host proof.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '2'
p = psutil.Process(); p.cpu_affinity(list(range(16, 28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys, pickle, json, hashlib, time
from pathlib import Path
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent; ROOT=H.parent
for d in (ROOT,ROOT/'sbc-power',ROOT/'coupled-recovery'): sys.path.insert(0,str(d))
import contact_layout as L
import fast_contacts as F
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import R157_native_selected_actual_conversion_r673 as N
import audit_R667_actual_three_ground_landing_native_source_contacts_r669 as T
OUT=H/'R715-round-stub-exhaustive-byte-bindings-and-returned-tree-consistency-r727'
P=H/'R157-high-current-FBG-actual-source-parallel-stitch-nomination-r715'
R719=H/'R715-FBG-parallel-stitch-actual-baseline-source-reference-independent-r719'
R721=H/'R715-all-native-pad-holes-foreign-fill-and-new-DC-body-supplement-r721'
M=ROOT/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
NET='/motherboard_do/FIELD_B_0V'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v): p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def info(s): return {'EMPTY':s.is_empty,'geom_type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
    assert not OUT.exists(); OUT.mkdir(); start=time.monotonic(); T.OUT=OUT
    assert sha(R719/'receipt.json')=='55abb18b9fad6affedaf2c16f3299296bac619553086b97fd0032df17a13f62b'
    assert sha(R721/'receipt.json')=='048a0751eca9fed42b7e3253fe29f47413b4429b03d4d29ed58e5725a9a173d0'
    prior=json.loads((R721/'receipt.json').read_bytes()); assert prior['status']=='R715_SUPPLEMENT_REPAIR_REQUIRED'
    assert prior['all_hole_or_actual_foreign_fill_guard_error_count']==0
    packet=P/'only-one-new-parallel-FBG-barrel-and-B-source-stub-NOMINEE.pkl'
    assert sha(packet)=='de776f9dc5f95bc937d88e90d89039c8337641f9f4be5dac52284fddafe811c0'
    item,=pickle.loads(packet.read_bytes()); via=item['via']; track,=item['tracks']
    N.assert_R157_actual_before(); assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
    g,h,b,q,c=pickle.loads(M.read_bytes())
    ng=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes())
    masks=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias']
    before,context,padledger=N.convert_selected_actual(h,c,ng,masks,{NET},N.R157/'copy/board.kicad_pcb')
    baseline,missing=N.bound_R663_before_groups({NET}); assert not missing
    candidate={**before,'vias':before['vias']+[via],'tracks':before['tracks']+[track]}
    raw=LineString([track['a'],track['b']]).buffer(track['w']/2,quad_segs=128)
    standard=F.build
    changed=[]
    def declared_new_only_build(model,*args,**kwargs):
        rows,trees=standard(model,*args,**kwargs)
        for layer,records in rows.items():
            for row in records:
                if row['kind']=='track' and row['uuid']==track['uuid']:
                    assert layer=='B.Cu' and row['source']==track
                    old=row['shape']; assert old.difference(raw).is_empty
                    changed.append({'UUID':track['uuid'],'layer':layer,'old_inscribed_cap_shape':info(old),
                                    'explicit_new_128_cap_shape':info(raw),'nominal_width_and_centerline_unchanged':True})
                    row['shape']=raw
        trees['B.Cu']=STRtree([row['shape'] for row in rows['B.Cu']])
        return rows,trees
    F.build=declared_new_only_build
    try: _,groups=K.physical(candidate,NET,K.hole_context(candidate))
    finally: F.build=standard
    assert len(changed)==1
    old=baseline[NET]; br=K.root(old,'J11005','2'); ar=K.root(groups,'J11005','2')
    relations,bad=K.contact_losses(old,groups); lost=sorted(K.keys(br)-K.keys(ar))
    rootbody=unary_union([r['shape'] for r in ar if r['kind']=='track' and r['uuid']==track['uuid'] and r['layer']=='B.Cu'])
    holes,tree=K.hole_context(candidate)
    physical=raw.difference(unary_union([holes[int(i)] for i in tree.query(raw,predicate='intersects')]))
    missingbody=physical.difference(rootbody); excess=rootbody.difference(physical)
    direct=[]
    source_B=unary_union([r['shape'] for r in br if r['layer']=='B.Cu'])
    parts=list(physical.geoms) if physical.geom_type=='MultiPolygon' else [physical]
    for i,piece in enumerate(parts):
        overlap=piece.intersection(source_B)
        direct.append({'new_drilled_body_component':i,'component':info(piece),'actual_BEFORE_J5_rooted_B_attachment':info(overlap),'PASS':not overlap.is_empty and overlap.area>0})
    refs,proof=T.exact_reference_delta(before,K.source_refs(br),K.source_refs(ar),NET)
    groupfile=OUT/'prospective-round-cap-FBG-all-drilled-groups.pkl'; groupfile.write_bytes(pickle.dumps(groups,protocol=5))
    for name,shape in [('new-drilled-body',physical),('source-rooted-new-body',rootbody),('new-body-missing',missingbody),('new-body-excess',excess)]: (OUT/(name+'.wkb')).write_bytes(shape.wkb)
    put(OUT/'only-NEW-track-cap-model-representation.json',changed)
    put(OUT/'all-old-FBG-relationships.json',{'rows':relations,'losses':bad})
    put(OUT/'direct-each-new-body-component-actual-before-source-contacts.json',direct)
    put(OUT/'strict-old-FBG-routed-reference-delta.json',{'losses':refs,'proof':proof})
    failed=bool(bad or lost or refs or not missingbody.is_empty or not excess.is_empty or any(not r['PASS'] for r in direct))
    priorgraph=H/'R715-new-stub-explicit-round-cap-direct-source-supplement-r723/prospective-round-cap-FBG-all-drilled-groups.pkl'
    assert sha(priorgraph)=='7f5c26c3c60c1b513c5bcab7f00f29814e8d952b2b617fe53301a05965b4af5f'
    assert sha(groupfile)==sha(priorgraph), 'fresh K.physical graph differs after unused returned-tree correction'
    put(OUT/'receipt.json',{'returned_B_broadphase_tree_rebuilt_after_exact_NEW_row_override':True,
        'R723_returned_tree_defect_preserved_but_K_physical_ignored_it_and_rebuilt_all_layer_trees':True,
        'R723_receipt_SHA256':sha(H/'R715-new-stub-explicit-round-cap-direct-source-supplement-r723/receipt.json'),
        'fresh_groups_equal_R723_bytes':True,'R155_model_SHA256':sha(M),'status':'PROSPECTIVE_NEW_ROUND_CAP_DRILLED_DC_BODY_SOURCE_PASS_NATIVE_CURRENT_OPEN' if not failed else 'PROSPECTIVE_NEW_ROUND_CAP_SOURCE_REPAIR_REQUIRED',
        'R721_raw_failed_receipt_SHA256':sha(R721/'receipt.json'),'R721_old_inscribed_graph_body_difference_preserved':True,
        'R719_old_three_ground_all_mask_direct_reference_proof_SHA256':sha(R719/'receipt.json'),
        'R715_packet_SHA256':sha(packet),'explicit_only_NEW_round_cap_representation_file_SHA256':sha(OUT/'only-NEW-track-cap-model-representation.json'),
        'all_original_rows_and_nominal_new_width_centerline_unchanged':True,'all_original_native_masks_unchanged_new_masks_prospective':True,
        'all_old_FBG_relationship_losses':len(bad),'prior_J5_source_key_losses':len(lost),'strict_old_FBG_routed_reference_losses':len(refs),
        'every_drilled_new_body_component_finite_actual_BEFORE_J5_attachment':all(r['PASS'] for r in direct),
        'exact_new_drilled_body_missing_from_source_component':info(missingbody),'source_body_excess':info(excess),
        'prospective_source_pad_count':T.countpad(ar),'prospective_source_key_count':len(K.keys(ar)),
        'groups_SHA256':sha(groupfile),'R721_all_holes_and_actual_foreign_fill_zero_error_scope_reused_exact_geometry':True,
        'new_fullbody_actual_In4_reference_gap_remains_R721_raw_evidence':True,
        'signed_distribution_native_actual_contact_voltage_plating_current_loop_thermal': 'OPEN',
        'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start})
    print('R727_COMPLETE',sha(OUT/'receipt.json'),'FAIL',failed,flush=True)
if __name__=='__main__':main()
