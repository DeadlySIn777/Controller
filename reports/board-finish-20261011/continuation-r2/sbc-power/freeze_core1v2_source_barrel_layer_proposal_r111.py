"""Explicit extra-In4 source-barrel hypothesis; no native flash is inferred."""
import copy,json,pickle,hashlib,sys
from pathlib import Path
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'))
import contact_layout as C
from verify_source import parse,atom
O=H/'sbc-power/core1v2-source-barrel-extra-In4-proposal-r111'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def write(f,d):Path(f).write_text(json.dumps(d,indent=1)+'\n')
def main():
    assert not O.exists();O.mkdir()
    mp=H/'field-power/corrected-regulated-native-bound-search-base-r111/model.pkl'
    assert sha(mp)=='722fae195cecfcfa07729dd243c2d74a0a0088e672582363265a2c15553db4d8'
    g,h,b,z,c=pickle.loads(mp.read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);c=copy.deepcopy(c)
    bf=H/'field-power/native-bound-field-base-r5/model.pkl';base=pickle.loads(bf.read_bytes())['discrete']
    uid='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92';old=next(q for q in base['vias'] if q['uuid']==uid);now=next(q for q in h['vias'] if q['uuid']==uid)
    assert now==old and set(old['flashed'])=={'F.Cu','In3.Cu'}
    marker=next(q for q in h['pads'] if (q['ref'],q['num'])==('L2001','2'));assert marker['net']==old['net']
    native=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    _,chunks,_=C.O.C.pcbtext.split(native.read_bytes());hits=[q for q in chunks if ('(uuid "'+uid+'")').encode() in q]
    assert len(hits)==1 and atom(parse(hits[0].decode()),'uuid')==uid
    cf=O/(uid+'.unchanged-existing-native-via-chunk');cf.write_bytes(hits[0])
    proposal={**copy.deepcopy(old),'flashed':old['flashed']+['In4.Cu'],'prospective_new_flash_requires_native_refill':'In4.Cu'}
    ledger={'verdict':'EXPLICIT_EXTRA_LAYER_HOST_HYPOTHESIS_NATIVE_FILL_REQUIRED_NO_SERIALIZED_VIA_CHANGE',
            'parent_native_board_file':str(native.resolve()),'parent_native_board_sha256':sha(native),
            'baseline_host_model_sha256':sha(mp),'via_uuid':uid,'net_raw':old['net'],
            'actual_source_marker':{'ref':'L2001','pin':'2','physical_pad_UUID':marker['uuid'],'raw_net':marker['net']},
            'expected_original_host_geometry':old,'expected_prospective_host_geometry':proposal,
            'original_actual_native_flash_mask':old['flashed'],'prospective_additional_flash_layer':'In4.Cu',
            'required_native_postfill_flash_mask':proposal['flashed'],'original_native_via_chunk_file':str(cf.resolve()),
            'original_native_via_chunk_sha256':sha(cf),'same_serialized_existing_via_UUID_net_position_diameter_drill':True,
            'no_new_drill_and_no_native_layer_span_change':True,'only_declared_host_changes':['flashed','prospective_new_flash_requires_native_refill'],
            'all_unknown_host_or_native_changes_rejected':True,'full_fitted_CORE1V2_load_A':.8,
            'single_barrel_current_drop_thermal_and_all_original_foreign_contacts':'OPEN','native_jobs':0,'board_written':False}
    lf=O/'extra-flash-obligation.json';write(lf,ledger)
    for model in (h,c):
        model['vias']=[copy.deepcopy(proposal) if q['uuid']==uid else q for q in model['vias']]
    b.setdefault('existing_native_owned_additional_flash_recipes',[]).append({'file':str(lf.resolve()),'sha256':sha(lf)})
    jf=H/'sbc-power/core1v2-local-outer-join-nominees-r106/proposed-tracks.pkl';assert sha(jf)=='ebce5be3f82d0c2de9bf6ee303d287efa78a9f85bc19358ee5249f01152b3073'
    jr=H/'sbc-power/core1v2-j7-independent-local-audit-r110/receipt.json';assert sha(jr)=='bbe71ab1846ce9b8a00b58b27b72e31e3c97cc9420014283d5201e13d005a659'
    tracks=pickle.loads(jf.read_bytes());assert len(tracks)==1
    for model in (h,c):
        assert not {q['uuid'] for q in tracks}&{q['uuid'] for q in model['tracks']};model['tracks']+=copy.deepcopy(tracks)
    b['CORE1V2_J7_explicit_local_nominee']={'tracks_sha256':sha(jf),'analytic_audit_sha256':sha(jr),'source_original_foreign_contact_current_native_gates':'OPEN'}
    model=O/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,z,c),protocol=5))
    write(O/'receipt.json',{'verdict':'PROSPECTIVE_SOURCE_EXTRA_IN4_AND_EXACT_J7_ROUTE_INPUT_FOREIGN_FILL_REPROJECTION_REQUIRED',
          'model_sha256':sha(model),'parent_model_sha256':sha(mp),'extra_flash_obligation_sha256':sha(lf),
          'existing_via_host_flash_hypotheses':1,'added_exact_scoped_tracks':1,'new_holes':0,'old_Cu_deletions':0,
          'all_original_NATIVE_via_fields_and_old_zone_definitions_unchanged':True,
          'original_foreign_fills_currently_parent_cache_and_must_be_reprojected_before_acceptance':True,
          'no_actual_native_extra_flash_claim':True,'full_source_contacts_current_and_native':'OPEN','native_jobs':0,'board_written':False})
    print('CORE1V2_EXTRA_IN4_ROUTE_INPUT',sha(model),sha(lf),sha(O/'receipt.json'),old,flush=True)
if __name__=='__main__':main()
