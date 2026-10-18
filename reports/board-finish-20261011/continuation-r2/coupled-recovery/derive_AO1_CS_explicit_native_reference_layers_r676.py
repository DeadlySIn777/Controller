from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;p=H/'construct_AO1_CS_real_ground_bridges_exact_b177_detour_r674.generated.py';s=p.read_text()
(H/'AO1-DAC-CS-real-rooted-ground-bridges-exact-b177-detour-paired-constructor-r674/failure.json').write_text(json.dumps({'verdict':'REFERENCE_READER_LAYER_SCHEMA_FAILURE_RETAINED','error':'K.source_refs returns signal-layer mapped references, not physical In1/In4 keys; r676 forms physical fill unions explicitly','source_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'native_jobs':0,'material_changes':0},indent=1)+'\n')
old="refs=K.source_refs(root);reference=refs['In1.Cu'];reference4=refs['In4.Cu'];before_root=K.root(groups['before'],'U14619','7');native=K.source_refs(before_root)['In1.Cu']"
new="reference=unary_union([z['shape']for z in root if z['kind']=='fill'and z['layer']=='In1.Cu']);reference4=unary_union([z['shape']for z in root if z['kind']=='fill'and z['layer']=='In4.Cu']);before_root=K.root(groups['before'],'U14619','7');native=unary_union([z['shape']for z in before_root if z['kind']=='fill'and z['layer']=='In1.Cu'])"
assert s.count(old)==1;s=s.replace(old,new).replace('constructor-r674','constructor-r676').replace('R674_','R676_');out=H/'construct_AO1_CS_explicit_ground_root_reference_layers_r676.generated.py';assert not out.exists();out.write_text(s)
