"""Reuse pinned R693 equations/input schema with one explicit R715 barrel.

All old native contacts/masks remain actual R157. New contacts are the
prospective R723 source graph, never observed native flags or capacity proof.
"""
import os, psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='2'
p=psutil.Process(); p.cpu_affinity(list(range(16,28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import hashlib, json
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'prepare_R157_actual_FBG_full_signed_3D_mesh_r693.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source)=='d6db43c6290d34b702c0830cf8ab6e1acc0f6042b2835adea08602370cb24bd5'
s=source.read_text(encoding='utf-8')
def replace(old,new):
    global s
    assert s.count(old)==1, (old,s.count(old))
    s=s.replace(old,new)
replace("OUT = H / 'R157-actual-FBG-complete-signed-real-barrel-mesh-input-r693'", "OUT = H / 'R715-one-prospective-barrel-complete-signed-native-baseline-mesh-input-r725'")
replace("groups, missing = N.bound_R663_before_groups({NET})\n    assert not missing", """proof = H/'R715-new-stub-explicit-round-cap-direct-source-supplement-r723'
    assert sha(proof/'receipt.json')=='950a0ed4b559739cf508f27843573a4fc9ea531f51c60d308787d71677ce5a6b'
    graphfile=proof/'prospective-round-cap-FBG-all-drilled-groups.pkl'
    assert sha(graphfile)=='7f5c26c3c60c1b513c5bcab7f00f29814e8d952b2b617fe53301a05965b4af5f'
    groups={NET:pickle.loads(graphfile.read_bytes())}
    packet=H/'R157-high-current-FBG-actual-source-parallel-stitch-nomination-r715/only-one-new-parallel-FBG-barrel-and-B-source-stub-NOMINEE.pkl'
    assert sha(packet)=='de776f9dc5f95bc937d88e90d89039c8337641f9f4be5dac52284fddafe811c0'
    newitem,=pickle.loads(packet.read_bytes()); newvia=newitem['via']; newtrack,=newitem['tracks']
    assert newvia['uuid']=='a7c42fee-df2d-533b-a806-0d6b7bcdf738'
    assert newvia['required_native_actual_flash_layers']==['B.Cu','In1.Cu','In2.Cu','In4.Cu']""")
replace("vias = {v['uuid']: v for v in h['vias']}", """vias = {v['uuid']: v for v in h['vias']}
    assert newvia['uuid'] not in vias
    vias[newvia['uuid']]=newvia""")
replace("assert set(contacts) <= set(observed[uid])", """if uid==newvia['uuid']:
                    assert set(contacts)<=set(newvia['flashed'])
                else:
                    assert set(contacts) <= set(observed[uid])""")
replace("'observed_native_flash_layers': observed[uid] if kind == 'via' else None", """'observed_native_flash_layers': observed.get(uid) if kind == 'via' else None,
                          'new_barrel_contact_layers_PROSPECTIVE_NOT_native': uid==newvia['uuid'],
                          'required_new_actual_native_contact_layers': newvia['required_native_actual_flash_layers'] if uid==newvia['uuid'] else None""")
replace("'all_contact_shapes_are_actual_native_all_drill_subtracted_R663_root_group': True", """'old_contact_shapes_actual_native_all_drill_subtracted_R157_new_drill_added': uid!=newvia['uuid'],
                          'new_port_contact_shapes_are_prospective_R723_only': uid==newvia['uuid']""")
replace("'status': 'ACTUAL_R157_FULL_FBG_SIGNED_PORTS_AND_REAL_BARREL_NUMERICAL_INPUT_FROZEN_NOT_CAPACITY_QUALIFIED'", """'status': 'R715_ONE_PROSPECTIVE_BARREL_FULL_SIGNED_NUMERICAL_INPUT_NOT_CAPACITY_QUALIFIED',
               'R723_prospective_graph_receipt_SHA256':sha(proof/'receipt.json'),
               'R723_prospective_graph_SHA256':sha(graphfile), 'R715_sparse_packet_SHA256':sha(packet),
               'all_original_observed_native_layers_retained_new_mask_contacts_prospective_only':True,
               'new_prospective_barrel_UUID':newvia['uuid'],
               'new_B_stub_raw_R721_reference_gap_and_failed_inscribed_cap_comparison_preserved':True""")
replace("'actual_source_discrete_layer_keys': len(rootkeys)", "'prospective_after_source_discrete_layer_keys': len(rootkeys)")
replace("'actual_rooted_contact_ports': len(ports)", "'actual_old_plus_one_prospective_rooted_contact_ports': len(ports)")
replace("'actual_rooted_plated_ports': sum(p['barrel_is_plated'] for p in ports)", "'actual_old_plus_one_prospective_rooted_plated_ports': sum(p['barrel_is_plated'] for p in ports)")
replace("'no_native_flash_substitution_or_phantom_annuli': True", "'no_old_native_flash_substitution_new_one_barrel_contacts_explicitly_prospective': True")
replace("print('R693_COMPLETE'", "print('R725_COMPLETE'")
generated=H/'prepare_R715_one_barrel_full_signed_prospective_mesh_r725.generated.py'
assert not generated.exists(); generated.write_text(s,encoding='utf-8')
exec(compile(s,str(generated),'exec'))
