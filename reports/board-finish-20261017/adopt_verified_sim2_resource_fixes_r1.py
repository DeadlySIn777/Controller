"""Apply three proven fixes only to the disconnected SIM2 runtime, with rollback."""
from pathlib import Path
import datetime as dt,hashlib,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parent.parent;RUN=H/'event-producer-fifo-r1';OUT=RUN/'canonical-adoption-r1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 required={
  RUN/'behavior-receipt.json':'PRODUCER_FIFO_DIFFERENTIAL_PASS',
  RUN/'native-full-map/receipt.json':'NATIVE_PRODUCER_FIFO_FULL_SIM2_MAP_PASS_FIT_AND_TIMING_SEPARATE',
  RUN/'full-runtime-independent-r1/receipt.json':'PASS',
  RUN/'postmap-behavior-r3/receipt.json':'MAPPED_FULL_EVENT_ENGINE_VENDOR_PRIMITIVE_FUNCTIONAL_PASS',
  RUN/'linuxcnc-pair-r1/receipt.json':'PASS',
  H/'release-review/producer-full-native-map-independent-r1/receipt.json':'INDEPENDENT_EXACT_NATIVE_FULL_SIM2_MAP_RESOURCE_SCOPE_PASS',
 }
 for p,status in required.items():assert json.loads(p.read_bytes())['status']==status,(p,status)
 independent=H/'release-review/producer-fifo-independent-supplement-r1/independent-reviewed-overlay-packet.json'
 reviewed=json.loads(independent.read_bytes())
 assert reviewed['status']=='INDEPENDENT_FUNCTIONAL_REVIEW_PASS_FOR_DISCONNECTED_SIM2_ONLY'
 assert all(sha(r['path'])==r['SHA256'] for r in reviewed['qualification_receipts'].values())
 native=json.loads((RUN/'native-full-map/receipt.json').read_bytes())
 assert native['resources']['EFX_LUT4']+native['resources']['EFX_ADD']==17912
 assert native['resources']['EFX_RAM_5K']==63
 entries=native['source_inventory']
 assert all(sha(r['canonical'])==r['canonical_SHA256'] and sha(r['copy'])==r['copy_SHA256'] for r in entries)
 selected=[r for r in entries if r['canonical_SHA256']!=r['copy_SHA256']]
 assert {Path(r['canonical']).name for r in selected}=={'cnc3_event_bank.v','cnc3_runtime_events.v','cnc3_spi_transport_stateful.v'}
 for row in selected:
  assert sha(row['selected_source'])==row['copy_SHA256']
  assert reviewed['selected_sources'][Path(row['canonical']).name]['SHA256']==row['copy_SHA256']
 suite=json.loads((RUN/'full-runtime-independent-r1/receipt.json').read_bytes())
 assert all(suite['copied_input_sha256'][Path(row['canonical']).name]==row['copy_SHA256'] for row in entries)
 runtime=ROOT/'gateware/v3/runtime';prov=runtime/'source-provenance.json'
 old_prov=prov.read_bytes();old_data=json.loads(old_prov);assert old_data['production_adopted'] is False
 assert 'implementation_updates' not in old_data
 all_before={str(p):sha(p) for p in runtime.rglob('*') if p.is_file()}
 assert not OUT.exists();(OUT/'backup').mkdir(parents=True)
 for row in selected:shutil.copyfile(row['canonical'],OUT/'backup'/Path(row['canonical']).name)
 (OUT/'backup/source-provenance.json').write_bytes(old_prov)
 update={'id':'2026-10-18-verified-sim2-resource-corrections','utc':dt.datetime.now(dt.timezone.utc).isoformat(),
  'scope':'disconnected_SIM2_functional_implementation_only','production_adopted':False,
  'behavior':'unchanged256event_capacity_all7producers_protocol_buffers_ACK_reset_capture_and_public_limits',
  'physical_authority':False,'physical_wrapper_fit_timing':'OPEN',
  'native_map':{'LUT4':15805,'ADD':2107,'FF':10441,'RAM5K':63,'MULT':1,'coarse_LUT_ADD_total':17912,'T20_coarse_limit':19728,'coarse_headroom':1816},
  'files':[{'copy':Path(r['canonical']).name,'before_sha256':r['canonical_SHA256'],'sha256':r['copy_SHA256'],'verified_source':str(Path(r['selected_source']).relative_to(ROOT)).replace('\\','/')} for r in selected],
  'evidence':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)} for p in [*required,independent]],
  'postmap_scope':'actual vendor primitive models inVerilog2005; initialized binary functional execution, not postroute timing; failedSystemVerilogmode startup runs retained'}
 # Preserve all original provenance bytes up to its final root brace. Original
 # ancestry records remain historical; the appended update binds current files.
 end=old_prov.rstrip();assert end.endswith(b'}');prefix=end[:-1].rstrip()
 newline=b'\r\n' if b'\r\n' in old_prov else b'\n'
 addition=json.dumps([update],indent=2).splitlines()
 addition='\n'.join('  '+line for line in addition)
 new_prov=prefix+b','+newline+b'  "implementation_updates": '+addition.lstrip().encode().replace(b'\n',newline)+newline+b'}'+newline
 assert json.loads(new_prov)['implementation_updates'][0]==update
 for row in selected:
  target=Path(row['canonical']);assert sha(target)==row['canonical_SHA256'];target.write_bytes(Path(row['copy']).read_bytes());assert sha(target)==row['copy_SHA256']
 prov.write_bytes(new_prov)
 changed={str(Path(r['canonical'])) for r in selected}|{str(prov)}
 assert all(sha(p)==h for p,h in all_before.items() if p not in changed)
 assert all(sha(r['canonical'])==r['copy_SHA256'] for r in entries)
 files=[{'path':str(Path(r['canonical'])),'backup':str(OUT/'backup'/Path(r['canonical']).name),'before_SHA256':r['canonical_SHA256'],'after_SHA256':r['copy_SHA256']} for r in selected]
 files.append({'path':str(prov),'backup':str(OUT/'backup/source-provenance.json'),'before_SHA256':hashlib.sha256(old_prov).hexdigest(),'after_SHA256':sha(prov)})
 rec={'status':'THREE_VERIFIED_DISCONNECTED_SIM2_FIXES_APPLIED_REVERSIBLY','applied_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'files':files,
  'all_other_runtime_files_unchanged':True,'canonical_RTL_exactly_matches_verified_native_and_full_runtime_inputs':True,
  'production_adopted':False,'board_or_machine_configuration_changed':False,'manufacturing_ready':False,
  'full_native_map_coarse_headroom':1816,'physical_wrapper_place_route_timing':'OPEN','input_evidence_SHA256':{str(p):sha(p) for p in [Path(__file__),*required,independent]}}
 (OUT/'receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
 rollback='''from pathlib import Path\nimport hashlib,json\nhere=Path(__file__).resolve().parent\nr=json.loads((here/'receipt.json').read_bytes())\nsha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()\nfor x in r['files']:\n assert sha(x['path'])==x['after_SHA256'], 'Current file changed; refusing to overwrite later work'\n assert sha(x['backup'])==x['before_SHA256']\nfor x in r['files']:\n Path(x['path']).write_bytes(Path(x['backup']).read_bytes())\nprint('Restored the exact four pre-adoption files; frozen evidence retained.')\n'''
 (OUT/'rollback.py').write_text(rollback)
 print(json.dumps({'status':rec['status'],'files':[Path(r['path']).name for r in files],'coarse_headroom':1816,'production_adopted':False},indent=2))
if __name__=='__main__':main()
