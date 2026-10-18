"""Disjoint host/native cases, unchanged actual sources, fresh unsuppressed ERC."""
import json,re,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
h=OUT/'source26-root78-host-r01';n=OUT/'source26-root78-native-r01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
host=read(h/'receipt.json');native=read(n/'receipt.json')
assert host['all_commands_passed']and host['source_hashes_unchanged']and native['passed']and native['source_hashes_unchanged']
maps=[read(p)for p in [h/'source-before.json',h/'source-after.json',n/'source-before.json',n/'source-after.json']]
assert all(v==maps[0]for v in maps)
skips=host['runs'][-1]['skip_cases']
expected={v['case']for v in skips if 'KiCad'in v['reason']}
actual=set(re.findall(r'^(.+?) \.\.\. ok$',(n/'native-tests.log').read_text(),re.MULTILINE))
assert actual==expected and len(actual)==native['reported_tests']==235
left=[v for v in skips if v['case']not in actual];assert len(left)==5
erc=read(h/'native-erc.json');priorpath=ROOT/'reports/motherboard-integration-20261001/source26-reference-fuse-adopted-r04/erc.json';prior=read(priorpath)
rows=lambda r:collections.Counter(json.dumps(dict(sheet=s['path'],uuid_path=s['uuid_path'],violation=v),sort_keys=True)for s in r['sheets']for v in s['violations'])
assert rows(erc)==rows(prior) and not erc['ignored_checks']
violations=[v for s in erc['sheets']for v in s['violations']]
assert len(violations)==70 and all(v['severity']=='warning'for v in violations)
evidence=[h/'receipt.json',n/'receipt.json',h/'native-erc.json',priorpath,Path(__file__)]
result=dict(passed=True,host_reported_tests=host['runs'][-1]['reported_tests'],host_passed=host['runs'][-1]['passed_tests'],host_skipped=host['runs'][-1]['skipped_tests'],
            actual_KiCad_cases_passed=len(actual),native_cases_exactly_match_all_host_KiCad_skips=True,remaining_skips=left,
            scoped_source_files=len(maps[0]),all_scoped_source_hashes_unchanged=True,
            native_ERC=dict(errors=0,warnings=70,ignored_checks=[],exact_prior_source26_warning_dispositions_preserved=True,
                            types=dict(collections.Counter(v['type']for v in violations))),
            evidence={str(p):sha(p)for p in evidence},physical_measurements=False,target_compilation=False,HDL_simulation=False,FPGA_vendor_fit=False,manufacturing_ready=False)
dest=OUT/'source26-root78-combined-validation.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n')
print(dict(passed=True,host=2087,host_passed=1847,actual_native_passed=235,remaining_environment_skips=5,source_files=len(maps[0]),ERC_errors=0,ERC_warnings=70))
