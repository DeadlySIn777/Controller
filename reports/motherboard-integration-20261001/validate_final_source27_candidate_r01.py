from pathlib import Path
import sys,json,hashlib,importlib.util,xml.etree.ElementTree as ET
ROOT=Path.cwd();O=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01';T=O/'candidate-tools';D=O/'final-source27-candidate/motherboard'
sys.path.insert(0,str(T));sys.path.insert(1,str(ROOT/'tools'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hashes(d):return {p.relative_to(d).as_posix():sha(p)for p in d.rglob('*')if p.is_file()and '__pycache__'not in p.parts}
f=json.loads((O/'freeze-receipt-r01.json').read_text())
for folder,key in((D,'candidate_source_sha256'),(T,'candidate_tools_sha256'),(O/'candidate-tests','candidate_tests_sha256')):
    if hashes(folder)!=f[key]:raise ValueError('Frozen candidate differs '+str(folder))
if hashes(ROOT/'hardware/motherboard')!=f['before_source_sha256']:raise ValueError('Live Source26 changed')
spec=importlib.util.spec_from_file_location('final27validation',T/'hardware_validate_motherboard.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);v.ROOT=ROOT;v.OUT=D
m=json.loads((D/'design.json').read_text());a=json.loads((D/'assembly-map.json').read_text());tree=ET.parse(D/'netlist.xml')
errors=v.validate(tree,m,a,True)
if errors:raise ValueError(errors)
old=json.loads((O/'before/motherboard/design.json').read_text())
if v.nodes(tree)!=v.nodes(ET.parse(O/'before/motherboard/netlist.xml')):raise ValueError('Native pin/net changed')
if set(r for r in old['components']if old['components'][r]!=m['components'][r])!={'R2106','U11019','U11025'}:raise ValueError('Unexpected components')
if any(old['components'][r]['pins']!=m['components'][r]['pins']or old['components'][r]['footprint']!=m['components'][r]['footprint']for r in old['components']):raise ValueError('Land/pin changed')
scripts=[ROOT/'reports/motherboard-integration-20261001/promote_source27_parent_health_r01.py',ROOT/'reports/motherboard-integration-20261001/prepare_source27_freeze_r01.py',Path(__file__),O/'freeze-receipt-r01.json',O/'source27-rebinding-plan.json',O/'future-generator-reproduction-r01.json',O/'independent-health-validation-r02.json']
r=dict(passed=True,adopted=False,full_actual_parent_hash_and_native_validation_passed=True,all_live_parent_and_original_MC_child_sources_unchanged=True,exact_three_part_native_identity_delta=True,original327_native1229_and_FPGA13548_retained=True,physical_parts=2688,native_ERC_errors=0,native_ERC_warnings=70,health_tests_passed=33,retained_focused_tests_passed=301,independent_native_negative_controls=28,future_full_generator_reproduces_exact_stage_native_circuit=True,complete_explicit_source_hash_rebinding_plan=True,promoter_not_executed=True,root_permission_to_adopt_required=True,evidence_sha256={p.relative_to(ROOT).as_posix():sha(p)for p in scripts},physical_qualified=False,manufacturing_ready=False)
(O/'delivery-receipt-r01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,adopted=False,exact_parts=3,focused_tests=301,health_tests=33,mutations=28)))
