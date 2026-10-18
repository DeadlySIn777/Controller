"""One ordinary via + one B stub, exact native dependencies, no staging."""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,re,time
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in (ROOT,ROOT/'sbc-power',ROOT/'coupled-recovery'):sys.path.insert(0,str(d))
import ordinary_routes as O
from verify_source import parse,children,child,atom
OUT=H/'R715-one-barrel-one-B-stub-exact-native-dependency-and-conditional-comparison-r731'
P=H/'R157-high-current-FBG-actual-source-parallel-stitch-nomination-r715'
R727=H/'R715-round-stub-exhaustive-byte-bindings-and-returned-tree-consistency-r727'
R729=H/'R715-one-prospective-barrel-full-signed-explicit-numeric-subset-redistribution-r729'
R697=H/'R157-actual-FBG-explicit-stable-numerical-subset-full-signed-current-r697'
SOURCE=ROOT/'R155-known-reference-native-diagnostic-r157/measure/copy/board.kicad_pcb'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def artifact(p):return {'file':str(p.resolve()),'SHA256':sha(p)}
def main():
    assert not OUT.exists();OUT.mkdir();start=time.monotonic()
    assert sha(SOURCE)=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'
    assert sha(R727/'receipt.json')=='b793ef3a1b887f27fb0fc013954a247c2564fee827679e9fa08a5408b4d564b8'
    assert sha(R729/'receipt.json')=='d5b71e6669362b4558eafea7508744292cda6dbac2333ec87db3e5b4084b2d6e'
    assert sha(R697/'receipt.json')=='286df7e59b8172661e4d8a4f24b18f6f5abaf340a6c073a32379142eebd1c0af'
    packet=P/'only-one-new-parallel-FBG-barrel-and-B-source-stub-NOMINEE.pkl';assert sha(packet)=='de776f9dc5f95bc937d88e90d89039c8337641f9f4be5dac52284fddafe811c0'
    item,=pickle.loads(packet.read_bytes());v=item['via'];t,=item['tracks'];raw=SOURCE.read_bytes()
    head,chunks,tail=O.C.pcbtext.split(raw);assert head+b''.join(chunks)+tail==raw
    inventory={O.C.pcbtext.chunk_uuid(ch):ch for ch in chunks if O.C.pcbtext.chunk_uuid(ch)}
    olduid='7a9206b1-d64b-4ebf-9424-6c4d6d434176';old=inventory[olduid]
    ast=parse(old.decode());assert ast[0]=='via' and atom(ast,'net')==v['net']
    assert v['uuid'] not in inventory and t['uuid'] not in inventory
    assert raw.count(('(net '+json.dumps(v['net'])+')').encode())>0
    oldfile=OUT/(olduid+'.template-original-native-via-chunk');oldfile.write_bytes(old)
    new=old.replace(b'(at 47.748 206.5)',b'(at 47.948 204.2)').replace(b'(size 0.5)',b'(size 0.8)').replace(b'(drill 0.2)',b'(drill 0.4)').replace(olduid.encode(),v['uuid'].encode())
    newast=parse(new.decode());keys={'at','size','drill','uuid'}
    assert [row for row in ast[1:] if row[0] not in keys]==[row for row in newast[1:] if row[0] not in keys]
    assert child(newast,'at')[1:]==['47.948','204.2'] and atom(newast,'size')=='0.8' and atom(newast,'drill')=='0.4'
    assert atom(newast,'uuid')==v['uuid'] and atom(newast,'net')==v['net']
    viafile=OUT/(v['uuid']+'.via-chunk');viafile.write_bytes(new)
    text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.6f)\n\t\t(layer %s)\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(*t['a'],*t['b'],t['w'],json.dumps(t['layer']),json.dumps(t['net']),json.dumps(t['uuid']))
    segmentfile=OUT/(t['uuid']+'.segment-chunk');segmentfile.write_text(text,encoding='utf-8',newline='')
    ta=parse(text);assert atom(ta,'net')==v['net'] and atom(ta,'uuid')==t['uuid'] and float(atom(ta,'width'))==t['w']
    for path,kind,uid in [(viafile,'via',v['uuid']),(segmentfile,'segment',t['uuid'])]:
        assert O.C.pcbtext.chunk_kind(path.read_bytes())==kind and O.C.pcbtext.chunk_uuid(path.read_bytes())==uid
    before=json.loads((R697/'receipt.json').read_bytes());after=json.loads((R729/'receipt.json').read_bytes())
    assert before['conditional_material_inputs']==after['conditional_material_inputs']
    assert [before[k] for k in ('full_FB_terms','full_exact_physical_endpoint_choices','normal_J11005_2_sink_A')]==[after[k] for k in ('full_FB_terms','full_exact_physical_endpoint_choices','normal_J11005_2_sink_A')]
    oldbars=json.loads((R697/'all-actual-real-barrel-full-signed-simplex-current-bounds.json').read_bytes());newbars=json.loads((R729/'all-actual-real-barrel-full-signed-simplex-current-bounds.json').read_bytes())
    maximum=lambda rs,uid:max(r['maximum_absolute_A'] for r in rs if r['UUID']==uid)
    ordinary=[r for r in newbars if r['kind']=='via'];worst=max(ordinary,key=lambda r:r['maximum_absolute_A'])
    compare={'full_signed_terms':75,'physical_endpoint_choices':152,'source_return_A':after['normal_J11005_2_sink_A'],
        'same_conditional_material_inputs':after['conditional_material_inputs'],
        'before_numeric_subset_return_voltage_V':before['maximum_conditional_absolute_voltage_V'],
        'after_numeric_subset_return_voltage_V':after['maximum_conditional_absolute_voltage_V'],
        'old_7a9206_maximum_before_A':maximum(oldbars,olduid),'old_7a9206_maximum_after_A':maximum(newbars,olduid),
        'new_a7c42_maximum_after_A':maximum(newbars,v['uuid']),
        'largest_remaining_ordinary_after':{k:worst[k] for k in ('UUID','layer_a','layer_b','maximum_absolute_A')},
        'after_maximum_unit_KCL_residual_A':after['maximum_unit_equation_KCL_residual_A'],
        'no_equal_sharing':True,'individual_interval_maxima_NOT_simultaneous_independent_currents':True,
        'same_numeric_omission_criteria_NOT_identical_mesh_or_convergence_proof':True,
        'numeric_subset_does_NOT_automatically_upperbound_physical_voltage_or_barrel_current':True,
        'saved_total_positive_plus_return_policy_V':.48,'return_only_no_total_loop_PASS':True,
        'material_plating_current_density_temperature_rise_transient_NATIVE_actual_contact_ratings':'OPEN'}
    put(OUT/'complete-conditional-signed-current-comparison.json',compare)
    rows=[{'action':'add','kind':kind,'uuid':uid,'raw_net':v['net'],'chunk_file':str(path.resolve()),'chunk_SHA256':sha(path)} for path,kind,uid in [(viafile,'via',v['uuid']),(segmentfile,'segment',t['uuid'])]]
    manifest={'status':'EXACT_MINIMAL_ONE_VIA_ONE_STUB_DEPENDENCY_FOR_ROOT_REVIEW_NO_NATIVE_LAUNCH',
        'exact_native_parent':artifact(SOURCE),'template_original_via':artifact(oldfile),'original_template_NOT_removed_or_replaced':True,
        'add_rows':rows,'delete_rows':[],'zone_changes':[],'native_rule_source_FP_hole_or_original_mask_changes':[],
        'only_new_via_declared_at_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],
        'B_stub_width_length_mm':[t['w'],item['row']['B_stub_length_mm']],
        'source_J11005_2_no_shutdown_connector_substitution':True,
        'required_actual_native_finite_contact_layers':['B.Cu','In1.Cu','In2.Cu','In4.Cu'],
        'new_ordinary_all6_mask_PROSPECTIVE_NOT_FORCED_old_flags_exact':True,
        'foreign_fills_hard_no_filled_polygon_edits_or_new_antipads':True,
        'source_old_contact_and_ref_binding':artifact(R727/'receipt.json'),
        'all_pad_hole_and_actual_foreign_fill_binding':artifact(H/'R715-all-native-pad-holes-foreign-fill-and-new-DC-body-supplement-r721/receipt.json'),
        'R721_cap_schema_FAIL_and_new_stub_raw_In4_gap_preserved_not_fast_signal_shadow_PASS':True,
        'numeric_comparison':artifact(OUT/'complete-conditional-signed-current-comparison.json'),
        'R729_numerical_subset_full_signed_receipt':artifact(R729/'receipt.json'),
        'actual_full_candidate_fill_all_retained_native_masks_source_contact_reference_DRC_current_loop_thermal':'OPEN',
        'native_jobs':0,'board_written':False,'adopted':False}
    put(OUT/'minimal-native-addition-recipe.json',manifest)
    put(OUT/'receipt.json',{'status':manifest['status'],'recipe_SHA256':sha(OUT/'minimal-native-addition-recipe.json'),
        'comparison_SHA256':sha(OUT/'complete-conditional-signed-current-comparison.json'),
        'add_vias':1,'add_segments':1,'delete_items':0,'native_definition_edits':0,
        'full_fill_native_current_thermal_limits_preserved':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start})
    print('R731_COMPLETE',sha(OUT/'receipt.json'),'recipe',sha(OUT/'minimal-native-addition-recipe.json'),flush=True)
if __name__=='__main__':main()
