"""Add one declared In1 ground bridge to actual old source copper."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_shared_return_actual_source_planes_r240.py';code=source.read_text().replace('nomination-r240','explicit-source-bridge-nomination-r242').replace('R240','R242')
needle="assert seedrows['In1.Cu']['actual_J3_before_fill_annular_overlap_mm2']>0 and seedrows['In1.Cu']['new_shared_via_layer_key_in_actual_source']";assert code.count(needle)==1;code=code.replace(needle,"assert seedrows['In1.Cu']['new_shared_via_layer_key_in_actual_source'] # Real source via exists, but the plane still needs its declared native-source bridge.")
needle="win=desired.envelope.buffer(1);";assert code.count(needle)==1
code=code.replace(needle,"""
 source_bridge_xy=[[216.964196,144.614062],[217.35,143.55],[217.188385086,143.477595190]]
 source_bridge=LineString(source_bridge_xy).buffer(.15,quad_segs=128)
 assert oldref['In1.Cu'].covers(Point(source_bridge_xy[-1])) and source_bridge.intersection(oldref['In1.Cu']).area>0
 desired=desired.union(source_bridge)
 in1_central_rooted=False
 win=desired.envelope.buffer(1);""")
needle="seed=oldref[layer].union(ann(central))";assert code.count(needle)==1
code=code.replace(needle,"seed=oldref[layer]if layer=='In1.Cu'else oldref[layer].union(ann(central))if in1_central_rooted else oldref[layer]")
needle=" if layer=='In1.Cu':in1oldret=physical.intersection(ann(oldret)).area>0";assert code.count(needle)==1
code=code.replace(needle,""" if layer=='In1.Cu':
  in1oldret=physical.intersection(ann(oldret)).area>0
  in1_central_rooted=physical.intersection(ann(central)).area>0 and physical.intersection(oldref[layer]).area>0
  assert in1_central_rooted,'Declared In1 source bridge must connect true old source fill to the actual shared barrel'
""")
code=code.replace("'no_cap_borrow_or_expansion':True","'no_cap_borrow_or_expansion':True,'declared_In1_source_bridge_xy_mm':source_bridge_xy,'declared_source_bridge_width_mm':.30,'In1_keep_seed_is_only_real_old_J3_source_fill':True,'In4_shared_annulus_seed_requires_successful_In1_source_bridge':in1_central_rooted")
compile(code,str(source),'exec');receipt=H/'U10003-source-bridge-r242-derivation.json';assert not receipt.exists();proof=H/'U10003-shared-return-two-source-seeded-new-FG-plane-source-seed-diagnosis-r241/receipt.json';assert hashlib.sha256(proof.read_bytes()).hexdigest()=='bf7ad1e1bdd114adda9b63d209bc20a661195cda4f2bcbd1ab4e8c6923fd9e14'
receipt.write_text(json.dumps({'source_script_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'executed_script_sha256':hashlib.sha256(code.encode()).hexdigest(),'exact_actual_source_diagnosis_sha256':hashlib.sha256(proof.read_bytes()).hexdigest(),'change':'explicit .30mm In1 ground bridge to actual oldJ3 source; In1 seeded only from oldactualfill; In4 requires realvia connection afterIn1','R240_failed_direct_seed_preserved':True,'native_jobs':0,'adopted':False},indent=1)+'\n');exec(compile(code,str(source),'exec'))
