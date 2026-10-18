"""A source-backed own-power-distribution proposal; preserve the strict checker FAIL."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'restore_old_ground_reference_masks_r62.py';dst=H/'restore_old_ground_reference_masks_r70.py';assert not dst.exists();s=src.read_text().replace('SAFE-old-source-ground-reference-remove-only-masks-r62','SAFE-old-source-ground-reference-power-scope-proposal-r70').replace('R62_','R70_')
contract=H/'sbc-power/CORE1V2-own-rail-shadow-classification-proposal-r191/receipt.json';assert sha(contract)=='bd84507d3c6321e21abeb40c1dd0ee9c847a5f7ae97d799795e05d12131fba4a'
a="assert sum(map(len,lostby.values()))==303"
b="""assert sum(map(len,lostby.values()))==303
 proposalfile=H/'sbc-power/CORE1V2-own-rail-shadow-classification-proposal-r191/receipt.json';assert sha(proposalfile)=='bd84507d3c6321e21abeb40c1dd0ee9c847a5f7ae97d799795e05d12131fba4a';proposal=json.loads(proposalfile.read_bytes());assert proposal['verdict']=='SOURCE_BACKED_SCOPED_POWER_VS_SIGNAL_CLASSIFICATION_PROPOSAL_ONLY'and not proposal['original_strict_checker_modified']and not proposal['physical_PDN_qualified']
 candidates=proposal['literal_same_raw_CORE1V2_B_power_candidate_rows'];power_UIDs={q['uuid']for q in candidates};assert len(power_UIDs)==20 and power_UIDs<=lostby['/LOGIC_GND']
 bytrack={t['uuid']:t for t in h['tracks']};assert all(bytrack[uid]['net']=='/CORE_1V2'and bytrack[uid]['layer']=='B.Cu'for uid in power_UIDs)
 lostby['/LOGIC_GND']-=power_UIDs;assert sum(map(len,lostby.values()))==283
 put(out/'own-power-candidate-proposal.json',{'proposal_sha256':sha(proposalfile),'exact20_own_rail_track_UUIDs':sorted(power_UIDs),'geometry_masks_omit_only_these_candidates':True,'strict_original_checker_still_FAIL_unchanged':True,'PDN_loop_decoupling_source_current_return_stability_transient_qualification':'OPEN','adoption_and_host_retention_flags':False})"""
assert a in s;s=s.replace(a,b)
a="'full76_contact_reference_geometry_native_current_thermal':'OPEN'"
b="'full76_contact_reference_geometry_native_current_thermal':'OPEN','own_rail_classification_proposal_sha256':sha(proposalfile),'strict_original_reference_checker_preserved_FAIL':True,'PDN_replacement_obligations':proposal['mandatory_replacement_PDN_obligations'],'host_retained_relationships_pass':False"
assert a in s;s=s.replace(a,b)
compile(s,str(dst),'exec');dst.write_text(s)
(H/'ground-mask-power-scope-r70-derivation.json').write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'source_backed_contract_sha256':sha(contract),'scope':'Construction omits only20 literal own CORE1V2 B rail shadows; all283 other actual lost ground-body shadows remain protected. This is a PDN classification proposal, not a reference waiver or checker mutation. Source25pads/f6annulus/allotherrails remain mandatory.','host_retained_relationships_pass':False,'physical_PDN_qualified':False,'native_jobs':0,'adopted':False},indent=1)+'\n');print(dst)
