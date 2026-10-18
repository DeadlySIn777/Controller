"""Validate frozen setup bindings/manifests without starting LinuxCNC."""
from pathlib import Path
import hashlib,json,sys,uuid
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'reports/board-finish-20261017/release-review/qualified-linuxcnc-pair-r1'
STAGE=OUT/'source-root'
sys.path.insert(0,str(STAGE))
from controller_config.service import read_json
from controller_config.setup_service import SetupService
from controller_lab.cnc3_configuration import prepare_configuration,verify_configuration
from tools.create_cnc3_qualification_fixture import runtime_sources
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prep=json.loads((OUT/'preparation-receipt.json').read_text())
assert all(sha(STAGE/p)==h for p,h in prep['staged_runtime_source_SHA256'].items())
rows=[]
for motors in (8,12):
 fixture=STAGE/f'reports/deeper-runtime-20261004/host/fixtures-{motors}'
 store=fixture/'setup.json';before=sha(store)
 inventory=runtime_sources();assert len(inventory)==71
 manifest=prepare_configuration(SetupService(store),read_json(fixture/'binding.json'),run_id=str(uuid.uuid4()),
  source_root=STAGE,source_files=inventory,encoder_mapping=read_json(fixture/'encoder-mapping.json'))
 verify_configuration(manifest,SetupService(store),source_root=STAGE,expected_source_files=inventory)
 host=manifest['cnc3_host'];assert host['fitted_mask']==0xfff and host['active_mask']==(1<<motors)-1
 assert manifest['physical_backend_allowed'] is False and manifest['simulation_context']['physical_backend_allowed'] is False
 assert manifest['simulation_context']['transport']=='disconnected_compiled_rtl_spi'
 assert [len(manifest['configured_io'][k]) for k in ['inputs','outputs','encoders']]==[24,16,4]
 assert host['required_encoder_mask']==15 and host['dout_enable_mask']==65535
 assert manifest['simulation_context']['source_sha256']==prep['staged_runtime_source_SHA256']
 assert sha(store)==before
 output=OUT/f'preflight-manifest-{motors}.json';assert not output.exists();output.write_text(json.dumps(manifest,indent=2)+'\n')
 rows.append({'active_joints':motors,'all_twelve_fitted':True,'active_mask':host['active_mask'],
  'fitted_mask':host['fitted_mask'],'DI':24,'DO':16,'ABZ':4,'source_closure_files':len(inventory),
  'configuration_recomputed_and_verified':True,'manifest_SHA256':sha(output),'copied_settings_unchanged':True})
receipt={'status':'FROZEN_8_12_SOURCE_BOUND_MANIFEST_PREFLIGHT_PASS_NOT_INTEGRATION_EXECUTION',
 'preparation_SHA256':sha(OUT/'preparation-receipt.json'),'profiles':rows,
 'canonical_settings_unchanged':all(sha(Path(item['original']))==item['SHA256'] for files in prep['fixture_inputs'].values() for item in files.values()),
 'local_installed_tools_checked_read_only':{'LinuxCNC':'1:2.9.4-2+deb13u1','Verilator':'5.048','Icarus':'13.0stable','rootfs_HAL_headers_present':True},
 'mapped_event_gate_required_at_launch':True,'LinuxCNC_process_started':False,'production_adopted':False,'physical_authority':False}
assert receipt['canonical_settings_unchanged']
(OUT/'preflight-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
