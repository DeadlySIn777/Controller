from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;p=H/'audit_AO1_ground_exact_R753_conductors_and_R310_peers_r666.py';s=p.read_text()
(H/'AO1-seven-ground-exact-R753-conductor-and-R310-peer-guard-r666/failure.json').write_text(json.dumps({'verdict':'READER_SCHEMA_FAILURE_RETAINED','error':'Peer d350 packet explicitly uses deleted_original_chunks; reader requested original_deletes','source_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'native_jobs':0,'material_changes':0},indent=1)+'\n')
assert s.count("peer['original_deletes']")==2;s=s.replace("peer['original_deletes']","peer['deleted_original_chunks']")
assert s.count('peer-guard-r666')==1;s=s.replace('peer-guard-r666','peer-guard-r668').replace('R666_COMPLETE','R668_COMPLETE')
out=H/'audit_AO1_ground_exact_R753_conductors_and_R310_peers_r668.generated.py';assert not out.exists();out.write_text(s)
