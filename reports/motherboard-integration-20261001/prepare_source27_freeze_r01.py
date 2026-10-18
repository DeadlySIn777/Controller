"""Freeze a report-only exact parent health correction and future hook.
No shared source/tools/test file is written.
"""
from pathlib import Path
import json,hashlib,copy,shutil
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashes(d):return {p.relative_to(d).as_posix():sha(p)for p in d.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
initial=json.loads((OUT/'initial-stage-receipt.json').read_text())
if hashes(ROOT/'hardware/motherboard')!=initial['before_source_sha256']:raise ValueError('Live Source26 changed')
for path in('independent-health-validation-r02.json','future-generator-reproduction-r01.json'):
    if json.loads((OUT/path).read_text()).get('passed')is not True:raise ValueError('Missing completed proof '+path)
FINAL=OUT/'final-source27-candidate/motherboard';shutil.copytree(OUT/'candidate/motherboard',FINAL)
dep=ROOT/'tools/hardware_apply_motherboard_health_source.py'
for file,field in(('design.json','source_sha256'),('assembly-map.json','input_sha256')):
    m=json.loads((FINAL/file).read_text());m[field][dep.relative_to(ROOT).as_posix()]=sha(dep)
    (FINAL/file).write_text(json.dumps(m,indent=2)+'\n')
before=json.loads((OUT/'before/motherboard/design.json').read_text());after=json.loads((FINAL/'design.json').read_text())
changed=[r for r in before['components']if before['components'][r]!=after['components'][r]]
if set(changed)!={'R2106','U11019','U11025'}:raise ValueError('Unexpected components')
if any(before['components'][r]['pins']!=after['components'][r]['pins']or before['components'][r]['footprint']!=after['components'][r]['footprint']for r in before['components']):raise ValueError('Pins/lands changed')
ordinary=ROOT/'reports/motherboard-ordinary-routing-20261001/source26-review-r08/ordinary-source-review.json'
owners=ROOT/'reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json'
ow=json.loads(owners.read_text());affected=[c['ref']for c in ow['capacitors']if c.get('owner')in('U11019','U11025')]
plan={
 'adopted':False,'live_source26_unchanged':True,'source27_rebinding_required':True,
 'frozen_source26_artifacts_remain_immutable':True,
 'before_source26_design_sha256':sha(ROOT/'hardware/motherboard/design.json'),
 'before_source26_netlist_sha256':sha(ROOT/'hardware/motherboard/netlist.xml'),
 'proposed_source27_design_sha256':sha(FINAL/'design.json'),
 'proposed_source27_native_netlist_sha256':sha(FINAL/'netlist.xml'),
 'ordinary112':{
   'before_review':ordinary.relative_to(ROOT).as_posix(),'before_review_sha256':sha(ordinary),
   'eligible_net_count_must_remain':112,
   'action':'Issue a new Source27 reviewed artifact with exact112 names/endpoints, voltage/classes/denials unchanged. Re-evaluate actual source-part provenance and health corners; bind exact adopted Source27 model/XML/adoption hashes. Do not substitute a new hash into the frozen Source26 artifact or bypass its checker.'},
 'capacitor723':{
   'before_manifest':owners.relative_to(ROOT).as_posix(),'before_manifest_sha256':sha(owners),
   'exact_affected_owner_bypasses':affected,
   'action':'Issue new723 manifest retaining every source-owned pin/role/return and all precision/converter exclusions. Replace the two actual owner MPNs with14, preserving native pin/land identity, and independently verify all723 against exact adopted XML/model. Source27 map and geometric measurement report must be fresh.'},
 'critical_digital':{
   'action':'Issue new exact Source27 critical declaration and recipe versions; preserve literal nets, endpoint pins, .40 returns, widths, neck rules and timing qualification boundaries. Recheck full native SOURCE clusters and actual reference resources against the reconciled board/map. Preserve frozen Source26 tools/reviews and use explicit new dependency hashes instead of disabling source binding.'},
 'retained_completed_routes':{
   'action':'After parent property-only reconciliation of the three fitted identities, run new Source27-bound combined checkers for101HF/207returns, ordinary9, critical2, AO1 SDO, full FLASH MISO and52 SOURCE bridge groups. Bind all exact retained UUID/geometry and endpoint witnesses. Repeat appropriate native cut negatives on changed health/default circuits and preserve all original donor negative receipts.'},
 'FPGA_and_source_history':{
   'action':'Retain original327/1229 retained pin-net ledger and135assigned48free FPGA metadata. Generate fresh real native netlist/ERC and independent actual source identity proof. No frame/gateware/pin-map changes.'},
 'cost':{
   'before':'reports/motherboard-cost-20260930/source-r26-2688-complete-cost-v11',
   'action':'Issue Source27 cost snapshot from exact adopted BOM. Only R2106 and two14 MPN purchases change; keep unknowns NULL, provenance/date/quantity/packaging and all existing dated price receipts immutable. No whole-cost claim.'},
 'manufacturing_ready':False,'physical_ramp_and_loading_qualified':False}
(OUT/'source27-rebinding-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
record={
 'passed':True,'adopted':False,'live_source26_unchanged':True,
 'scope':'Report-only exact three parent procurement/default corrections, no child/originalMC changes; no live adoption authorized',
 'before_source_sha256':initial['before_source_sha256'],'candidate_source_sha256':hashes(FINAL),
 'candidate_tools_sha256':hashes(OUT/'candidate-tools'),'candidate_tests_sha256':hashes(OUT/'candidate-tests'),
 'actual_exact_three_part_ledger':after['health_source_correction']['exact_three_part_ledger'],
 'changed_refs':sorted(changed),'all_native_pin_nets_and_manufacturer_lands_unchanged':True,
 'physical_parts':2688,'retained_MC_parts':327,'retained_MC_pin_nets':1229,'FPGA_assigned':135,'FPGA_free':48,
 'native_ERC_errors':0,'native_ERC_warnings':70,'ignored_checks':[],
 'retained_focused_tests_passed':301,'focused_subtests':16,'independent_health_tests_passed':33,
 'additional_actual_native_mutation_controls':28,'future_generator_all2688_component_dictionaries_and_native_pin_nets_identical':True,
 'evidence_sha256':{p.relative_to(ROOT).as_posix():sha(p)for p in[
 OUT/'initial-stage-receipt.json',OUT/'independent-health-validation-r02.json',OUT/'future-generator-reproduction-r01.json',
 OUT/'focused-source-tests-r01.log',OUT/'health-pytest-r01.log',OUT/'source27-rebinding-plan.json',OUT/'erc.json',OUT/'future-generated-r03-native-erc.json',dep]},
 'live_promotion_must_wait_for_root_release':True,'physical_qualification':False,'manufacturing_ready':False}
(OUT/'freeze-receipt-r01.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(passed=True,adopted=False,source=FINAL.as_posix(),changed_refs=changed,owner_bypasses=affected)))
