from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 bundle=HERE/'serial-replay-candidate-r02';replay=HERE/'serial-replay-full-r02';out=HERE/'serial-admission-handoff-r01'
 if out.exists():raise RuntimeError('Fresh handoff receipt required')
 report=read(replay/'report.json')
 assert report['status']=='PASS' and report['counts']=={'PASS':11,'FAIL':0,'BLOCKED':0,'NOT_RUN':0}
 assert report['input_integrity'] and report['inputs_unchanged'] and report['scope_flags']['actual_simulated_SPI_edges_and_CRC']
 manifest=read(bundle/'bundle-manifest.json');assert report['exact_inputs']==manifest['files']
 for p,h in manifest['files'].items():assert sha(bundle/p)==h,(p,'bundle drift')
 peerpath=HERE/'peer-serial-admission-authority-review-r01/receipt.json';peer=read(peerpath);assert peer['passed']
 plantpath=ROOT/'reports/controller-plant-20261001/actual-spi-edge-plant-r03/receipt.json';plant=read(plantpath);assert plant['status']=='PASS' and plant['source_unchanged']
 rtl={p.name:sha(p) for p in bundle.glob('cnc3_*.v')};assert len(rtl)==7
 for p,h in peer['input_sha256'].items():assert sha(ROOT/p)==h and rtl[Path(p).name]==h
 matched=[]
 for p,h in plant['input_sha256'].items():
  if Path(p).name in rtl:assert rtl[Path(p).name]==h;matched.append(Path(p).name)
 assert set(matched)==set(rtl)
 prior=[]
 for row in read(bundle/'inputs.json'):
  assert sha(bundle/row['snapshot'])==row['sha256'] and sha(Path(row['source']))==row['sha256']
  prior.append({'source':row['source'],'sha256':row['sha256'],'unchanged':True})
 original_codec=ROOT/'gateware/v3/frozen/protocol_v3.py';original_spec=ROOT/'gateware/v3/frozen/spec/protocol.json'
 for p in (original_codec,original_spec):assert sha(p)==sha(bundle/'inputs/workspace'/p.relative_to(ROOT))
 stats=read(replay/'family_synthesis_lint/mapped-stat.json')['modules']['\\cnc3_motion_spi']['num_cells_by_type']
 diagnostic=read(HERE/'family-proof-r06/mapped-stat.json')['modules']['\\cnc3_motion_spi']['num_cells_by_type']
 out.mkdir()
 references=[peerpath,plantpath,HERE/'serial-replay-entrypoint-controls-r01/receipt.json',HERE/'serial-SPI-frame-binding-r05/receipt.json',HERE/'frozen-C-rate-boundary-r02/receipt.json']
 for p in references:
  j=read(p);assert j.get('status')=='PASS' or j.get('passed') is True
 receipt={'status':'PASS','scope':'report-local bounded stateful motion implementation and fresh replay; incomplete full CNC3/controller','bundle_path':str(bundle),'bundle_manifest_sha256':sha(bundle/'bundle-manifest.json'),'bundle_files':manifest['files'],'fresh_replay_report':str(replay/'report.json'),'fresh_replay_report_sha256':sha(replay/'report.json'),'all11_fresh_stages_pass':True,'exact_RTL':rtl,'preserved_original_sources':prior,'additional_exact_codec_spec':{str(p):sha(p) for p in (original_codec,original_spec)},'scope_review_and_independent_evidence':{str(p):sha(p) for p in references},'fresh_stage_receipts':{r['name']:{'path':r['receipt'],'sha256':r['receipt_sha256']} for r in report['stages']},'family_mapped_cells':stats,'parallel_diagnostic_cells':diagnostic,'LUT4_reduction':diagnostic['EFX_LUT4']-stats['EFX_LUT4'],'vendor_T20_fit_timing_bitstream':False,'protocol_rate_MAX':16777216,'protocol_max_pps_assuming_50MHz':195312.5,'actual_runtime_timing_admission':'overflow-safe unsigned abs32 and shared36bit shift/add against configured high+low+1 before atomic completed-frame commit','drive_machine_cap_duty_remains_host':True,'physical_providers':'explicit external inputs; current behavioral fixtures and plant use ideal providers','request_consumer':'real one-cycle accept/reject; no backpressure queue integrated; public structural endpoint queue remains separate','complete_CNC3_CAP3_HAL_machine':False,'manufacturing_ready':False,'open_implementation_boundaries':['actual IOL1 acquisition and board-region/factory qualification','physical safety RESET_ARM/contactor/STO/provider qualifier','I/O configuration/epochs/rearm and real DO/PWM/AO authority','CAP3/fault/identity pages and event/index/MPG transport','real LinuxCNC/HAL commissioning/service commands with deliberate continuity witness','vendor package fit, constrained50MHz timing and board/cable/power/thermal/watchdog qualification'],'shared_or_external_source_modified':False,'replay_command':['C:/Python314/python.exe','-X','utf8',str(bundle/'replay_motion.py'),'--out','<fresh-output>','--wsl-distro','GarciaMechBuilder']}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
 # This is explicitly excluded from the executable bundle manifest; every
 # executable/input byte remains identical to the completed fresh replay.
 (bundle/'freeze-receipt.json').write_text(json.dumps({'status':'PASS','handoff_receipt':str(out/'receipt.json'),'handoff_receipt_sha256':sha(out/'receipt.json'),'bundle_manifest_sha256':sha(bundle/'bundle-manifest.json')},indent=2)+'\n',encoding='utf8',newline='\n')
 (out/'README.md').write_text('''# Bounded CNC3 motion implementation

All eleven fresh disconnected stages pass on the exact frozen seven-module
resource-shared successor. The original CNC1, shared structural CNC3 and external
specification bytes remain unchanged. Command/feedback sizes remain96/176bytes;
the frozen cap remains195,312.5steps/s/channel assuming50MHz. Independent exact
parallel comparison, overflow/rate/timing boundaries, actualSPI/CRC/rejection,
fault priority, clean drain and compiled mutations are included. An independent
nine-scenario actualSPI→emittedSTEP12→mechanics→ABZ4 run uses the identical RTL.

The shared incoming-rate checker performs11 sequential additions per word.
It rejects invalid rates before sequence,progress or any of12rates commit. A
currentCS/CRC-valid completed frame owns its admission result; reset/abort/newCS
cannot reuse an earlier accepted result. GPIO/wire/clock/provider behavior is
simulated. The mapped family result is not vendor device fit or physical timing.

This scope does not implement full IOL1/config/output authority,factory identity,
CAP3/pages,events/MPG,physical safety qualification or the realHAL machine chain.
The four real base encoder algorithms do not imply twelve physical receivers.
The standalone exploratory2MHz sweep does not raise the frozenCNC3rate.

Use the receipt's replay_command with a fresh output directory. The replay runs
actual compilers/simulations/family mapping, not cachedPASS aggregation. Failed
earlier fixture receipts remain immutable. See receipt.json for exact input,
proof,peer,plant and resource hashes and remaining implementation boundaries.
''',encoding='utf8',newline='\n')
 print(json.dumps({'status':'PASS','handoff':str(out/'receipt.json'),'sha256':sha(out/'receipt.json'),'bundle_manifest_sha256':sha(bundle/'bundle-manifest.json'),'mapped_cells':stats}))
if __name__=='__main__':main()
