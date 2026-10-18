"""Prepare final independent exact manifest binding; do not run without manifest."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
p=HERE/'audit_ao1_positive_operation_r3.py';t=p.read_text()
t=t.replace("out=HERE/'ao1-positive-independent-operation-r3.json'","out=HERE/'ao1-positive-independent-operation-r4.json'")
t=t.replace("'schema':'ao1-independent-positive-operation-r3'","'schema':'ao1-independent-positive-operation-r4'")
needle='    chunks={u:ch for u,ch in now[4].items() if u not in removed};chunks.update({u:old[4][u] for u in restored});chunks.update(new)'
replacement="""    if manifest is None:raise ValueError('Frozen root exact AO1 return manifest required')
    if manifest['local_native_source_sha256']!=C.sha(raw):raise ValueError('Manifest native baseline differs')
    if {u:ch.encode() for u,ch in manifest['exact_new_chunks'].items()}!=new:raise ValueError('Manifest new exact UUID/chunk serialization differs')
    if {u:ch.encode() for u,ch in manifest['exact_restored_chunks'].items()}!={u:old[4][u] for u in restored}:raise ValueError('Manifest exact original restores differ')
    if {u:ch.encode() for u,ch in manifest['exact_removed_chunks'].items()}!={u:now[4][u] for u in removed}:raise ValueError('Manifest exact owned removals differ')
    staged_parent=HERE.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb'
    staged_raw=A.read(staged_parent);staged=C.inventory(staged_raw)
    if C.sha(staged_raw)!=manifest['exact_staged_parent_sha256']:raise ValueError('Manifest latest parent differs')
    if any(staged[4].get(u)!=now[4][u] for u in removed) or restored&set(staged[4]) or set(new)&set(staged[3]):raise ValueError('Latest-parent exact owned operation collision/change')
    parent_identity=N.SourceNets(staged_raw)
    if any(parent_identity.raw(n)!=identity.raw(n) for n in (VREF,SDI,COM)):raise ValueError('Latest-parent raw native net identity differs')
    parent_owned_exact={'path':str(staged_parent.resolve()),'sha256':C.sha(staged_raw),'removed_chunks_unchanged':True,'restored_uuids_absent':True,'new_uuids_absent':True,'raw_net_tokens_exact':True,'whole_parent_geometry_and_global_reference_qualification':'OPEN under root native combined guards'}
"""+needle
assert needle in t;t=t.replace(needle,replacement)
needle='    referrors=[r for r in refchecks if r[\'uncovered_full_copper_mm2\']>1e-9]'
replacement="""    def ledger_identity(rows):
        return sorted((r['zone_uuid'],r['net'],r['layer'],r['exact_original_fill_wkb_sha256'],r['exact_serialized_local_zone_clearance_mm'],tuple(sorted((q['uuid'],q['net'],q['required_zone_domain_clearance_mm']) for q in r['cut_items'])),r['candidate_component_count'],tuple(sorted((tuple(q['key']),tuple(q['candidate_piece_indices'])) for q in r['old_existing_physical_contacts']))) for r in rows)
    if ledger_identity(fillledger)!=ledger_identity(manifest['prospective_fill_ledger']):raise ValueError('Independent final exact fill/contact ledger differs from root constructor')
"""+needle
assert needle in t;t=t.replace(needle,replacement)
t=t.replace("if not .8<=distance<=1.:continue","if not .8<=distance<=1.+1e-9:continue")
t=t.replace("'native_geometry_proof':proof", "'native_geometry_proof':proof,'exact_root_manifest_serialization_binding':True,'independent_constructor_exact_fill_contact_ledger_match':True,'latest_parent_owned_operation_binding':parent_owned_exact")
q=HERE/'audit_ao1_positive_operation_r4.py'
if q.exists():raise ValueError('Fresh r4 required')
q.write_text(t);compile(t,str(q),'exec')
(HERE/'ao1-positive-operation-r3-interrupted-diagnostic.json').write_text(json.dumps({'verdict':'DELIBERATELY_STOPPED_BEFORE_UNBOUND_AUDIT_COMPLETION','script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pid':72600,'reason':'Root requested waiting for exact return manifest; own process command verified before stop','board_emitted':False,'result_credit':False,'fresh_final_audit':str(q.resolve())},indent=1)+'\n')
print('r4 syntax PASS; waiting for exact root manifest')
