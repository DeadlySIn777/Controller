from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
B=P/'record-config-replay-candidate-r03'
R=P/'record-config-replay-full-r03'
O=P/'record-config-handoff-r03'
O.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((R/'report.json').read_text())
assert report['status']=='PASS' and report['counts']=={'PASS':3,'FAIL':0,'BLOCKED':0,'NOT_RUN':0}
assert report['bundle_integrity'] and report['inputs_unchanged']
manifest=json.loads((B/'bundle-manifest.json').read_text())
assert all(sha(B/n)==h for n,h in manifest['files'].items())
compiled=json.loads((R/'same_C_signature_record_config_and_ARM/receipt.json').read_text())
wire=json.loads((R/'actual_SPI_record_config/receipt.json').read_text())
mutations=json.loads((R/'compiled_authority_and_integrity_mutations/receipt.json').read_text())
assert compiled['status']==wire['status']==mutations['status']=='PASS'
r={
 'status':'PASS_BOUNDED_PROPOSAL_NOT_ADOPTED',
 'bundle':str(B),'bundle_manifest_sha256':sha(B/'bundle-manifest.json'),
 'fresh_replay_report':str(R/'report.json'),'fresh_replay_report_sha256':sha(R/'report.json'),
 'exact_frozen_inputs':len(manifest['files']),'original_shared_firmware_and_Source26_unchanged':True,
 'host_Python_checks':compiled['host_Python_signature_record_checks'],
 'same_C_record_config_filter_age_checks':compiled['actual_C_record_config_filter_checks'],
 'actual_simulated_SPI_checks':wire['checks'],
 'compiled_runtime_rejected_C_mutants':mutations['actual_compiled_C_mutants'],
 'executed_Python_provenance_mutants':mutations['executed_crypto_provenance_mutants'],
 'ASan_UBSan':compiled['sanitizers'],
 'four_actual_ARM_ELF_bin_compilation':compiled['four_actual_ARM_ELF_bin_compilation'],
 'linker60KiB_overflow_rejected':compiled['actual_linker_partition_overflow_rejected'],
 'target_sizes':compiled['target_sizes'],
 'exact_runtime_files':{n:sha(B/n) for n in ['target.c','iol1.c','iol1.h','board_record.c','board_record.h','dic_filter.c','dic_filter.h','stm32g031.ld','startup.S']},
 'implemented_bounded':[
  'actual fitted four MCU flash/UID integrity-reader and safe unprovisioned/default profile',
  'common motherboard lineage with unique local STM32 UID binding; no invented removable cards',
  'two independent2KiB-page selection and generation2 interrupted-prefix retention software model',
  'actual host Ed25519 verification under explicit supplied registry; no production trust granted',
  'real accepted DIC24B CONFIG with exactCRC and elapsed100us group debounce',
  'explicit unadopted read-only8B IDENT chunk supplement preserving16B realtime and40B wire length',
  'actual shared target age helper/cold unavailable/stale latch and65534/65535/65536/timer-rollover controls',
  'software IWDG starts before factoryflashread; no runtime flash write or erase'
 ],
 'separate_evidence_categories':[
  'exact source/primary manufacturer inspection','host cryptographic and record execution',
  'same compiled C and sanitizers','actual simulated SPI with explicit GPIO fixtures',
  'actual ARM target compilation and linker negative','physical validation notrun'
 ],
 'no_claims':['real flash program/ECC/atomicity/WRP/RDP/BOR hardware execution',
  'authenticated MCU attestation or manufacturer trust provisioning','actual DMA/IRQ/MMIO execution',
  'commercial ACTIVE/output/ARM/CAP3/HAL/vendorfit or new product ratings'],
 'preserved_prior_history':[
  str(P/'record-config-replay-candidate-r01'),str(P/'record-config-replay-candidate-r02'),
  'r02 DIC age wrap rejected by independent peer; r03 corrects it',
  'r02 C torn-prefix fixture used prior generation; r03 uses actualgeneration2 successor',
  'earlier compile/test failures remain in their exact original receipt folders'
 ],
 'future_integration_dependencies':report['open_dependencies'],
 'replay_command':'C:/Python314/python.exe -X utf8 '+str(B/'replay_record_config.py')+' --out <fresh> [--wsl-distro GarciaMechBuilder]'
}
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'receipt':str(O/'receipt.json'),'sha256':sha(O/'receipt.json'),
 'bundle_manifest_sha256':r['bundle_manifest_sha256'],'status':r['status']}))
