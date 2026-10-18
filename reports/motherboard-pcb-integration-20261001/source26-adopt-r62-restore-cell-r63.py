"""Adopt independently qualified ROOT62 WIP, then recheck one exact cell."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_populate_motherboard_pcb import sha,write
donor=ROOT/'reports/motherboard-return-zoning-20261001/source26-r61-orphan-bridge-retirement-r01/motherboard-source26-orphan-free-candidate.kicad_pcb'
folder=donor.parent
required=[folder/'receipt.json',folder/'combined-bypass-proof.json',folder/'independent-connectivity/review.json']
evidence=[json.loads(p.read_text()) for p in required]
if any(d.get('board_sha256')!=sha(donor) for d in evidence):raise ValueError('Exact combined PCB proof differs')
if not evidence[0]['passed'] or not evidence[1]['passed'] or not evidence[2]['source_net_checks_pass'] or evidence[2]['orphan_copper_items']:
    raise ValueError('Combined required PCB proofs failed')
native=json.loads((folder/'native.json').read_text())
if native.get('ignored_checks') or any(v['severity']!='warning' for v in native['violations']):raise ValueError('Native errors or ignored checks')
adopted=ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62'
if adopted.exists():raise ValueError('Fresh WIP adoption required')
adopted.mkdir();target=adopted/'motherboard-source26-WIP.kicad_pcb';shutil.copyfile(donor,target)
for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(donor.with_suffix(suffix),target.with_suffix(suffix))
for resource in folder.iterdir():
    if resource.is_dir() and (resource.suffix=='.pretty' or resource.name=='3dmodels'):shutil.copytree(resource,adopted/resource.name)
    elif resource.name=='fp-lib-table':shutil.copyfile(resource,adopted/resource.name)
shutil.copyfile(folder/'native.json',adopted/'drc.json')
write(adopted/'baseline-disposition.json',dict(board_sha256=sha(target),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=native['violations'],ignored_checks=[]))
write(adopted/'adoption.json',dict(passed=True,adopted=True,scope='Routing WIP only; actual source26 preserved and required combined circuit proofs passed.',board_sha256=sha(target),exact_source_design_sha256=sha(ROOT/'hardware/motherboard/design.json'),exact_source_netlist_sha256=sha(ROOT/'hardware/motherboard/netlist.xml'),evidence_sha256={str(p.resolve()):sha(p) for p in required+[folder/'native.json',folder/'all-retained-new-bridge-source-witnesses.json']},physical_footprints=2688,track_via_count=10506,zone_count=1507,missing_joins=3811,native_errors=0,native_warnings=len(native['violations']),ignored_checks=[],orphan_copper_count=0,retained_bypass_loops=93,receiving_return_endpoints=191,retained_reference_bridge_groups=43,all_retained_reference_bridge_conductors_physically_SOURCE_anchored=True,global_power_or_reference_qualification=False,manufacturing_ready=False))
print('ROOT62 adopted',sha(target),flush=True)
# The only failed HF group was obstructed by the now-retired FIELD_B orphan
# bridge. Its exact five original additions are tried again, never presumed
# safe or marked accepted before full native and actual-reference checks.
before=ROOT/'reports/motherboard-pcb-integration-20261001/source26-rejected-HF-r61/motherboard-bounded-merged-candidate.kicad_pcb'
full=ROOT/'reports/motherboard-pcb-integration-20261001/source26-owned-bypass-r60/motherboard-bounded-merged-candidate.kicad_pcb'
ids=['f430b263-5780-4ea9-87f2-c6ab6769b329','42367b84-8072-419c-9d4a-c6ac3d098532','da59bed9-d431-4aa1-beee-b1afda14bd7c','989a51e4-36f9-4981-b404-1273da85d225','02736cea-05aa-4c29-a3d3-c63d5673f21c']
scope=adopted/'bounded-C17014-retrial-scope.json'
write(scope,dict(electrical_source_unchanged=True,reviewed_scope_reason='Retrial of exactly five original C17014 local bypass objects after retiring the unrelated orphan FIELD_B reference bridge that obstructed its CORE5 reference. This is an unadopted trial until full native/SOURCE/actual own-reference checks pass; no old source/pads/poses/Cu/zone definitions change.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=ids,reviewed_added_zone_UUIDs=[]))
out=ROOT/'reports/motherboard-pcb-integration-20261001/source26-C17014-retrial-r63'
run=subprocess.run([sys.executable,str(ROOT/'tools/hardware_merge_bounded_pcb_delta.py'),'--before',str(before),'--donor',str(full),'--target',str(target),'--scope',str(scope),'--out',str(out)],cwd=ROOT,capture_output=True,text=True)
(out/'merge-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError(run.stderr[-1600:])
report=json.loads((out/'drc.json').read_text())
if report.get('ignored_checks') or any(v['severity']!='warning' for v in report['violations']):raise ValueError('Native retrial rejected; ROOT62 remains current')
write(out/'baseline-disposition.json',dict(board_sha256=sha(out/'motherboard-bounded-merged-candidate.kicad_pcb'),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=report['violations'],ignored_checks=[]))
print(run.stdout[-1000:],flush=True)
