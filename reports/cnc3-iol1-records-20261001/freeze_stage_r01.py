from pathlib import Path
import hashlib,json,shutil
P=Path(__file__).resolve().parent;S=P/'stage-r01';ROOT=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):(S/name).write_text(json.dumps(obj,indent=2)+'\n')
model=json.loads((ROOT/'hardware/motherboard/design.json').read_text());components=model['components']; mcus={r:c for r,c in components.items() if 'STM32G031' in str(c)}
write('primary-flash-observations.json',{
 'status':'SOURCE_INSPECTED','date':'2026-10-01','exact_fitted_MCUs':{r:{'mpn':c.get('mpn'),'footprint':c.get('footprint')} for r,c in mcus.items()},
 'electrical_source_design_sha256':sha(ROOT/'hardware/motherboard/design.json'),
 'facts':[
 {'primary':'https://www.st.com/resource/en/datasheet/stm32g031g4.pdf','document':'DS12992 Rev4 June2025','pages':[1,13,66,67,122],'fitted_x8_memory':{'flash_bytes':65536,'SRAM_bytes':8192},'flash64bit_program_typ_max_us':[85,125],'page_erase_typ_max_ms':[22,40],'endurance_cycles':10000,'endurance_TA_C':[-40,105],'retention_after10000cycles_at55C_years':30,'characterization_not_production_test':True},
 {'primary':'https://www.st.com/resource/en/reference_manual/rm0444-stm32g0x1-advanced-armbased-32bit-mcus-stmicroelectronics.pdf','document':'RM0444 Rev6','sections':['3.3.1/Table9','3.3.8','3.5.3','41.1'],'pages':[71,72,79,90,1368],'page_bytes':2048,'aligned_program_doubleword_bytes':8,'programmed_word_requires_erase_before_nonzero_reprogram':True,'ECC_bits_per64bitword':8,'UID_readonly_base':'0x1fff7590','UID_bytes':12,'WRP_granularity_bytes':2048}
 ],
 'primary_retrieval':'Manufacturer web extraction independently read; direct binary downloads timed out, preserved sources-r01/receipt.json. No invented retained PDF hash.',
 'partition':{'application':'0x08000000..0x0800EFFF','application_bytes':61440,'factory_slot0':'0x0800F000..0x0800F7FF','factory_slot1':'0x0800F800..0x0800FFFF','independent_erase_pages':[30,31],'record_bytes':512,'commit_doubleword_offset':504},
 'runtime_flash_erase_or_program_implemented':False,'factory_SWD_provisioning_executed':False,'WRP_or_RDP_or_BOR_or_IWDG_options_provisioned':False,'firmware_update_loader_implemented':False,
 'factory_plan':'Program only inactive independent erased page, 63 content doublewords, read/validate content, then finalCRC+commit doubleword504, read/verify full record; preserve old committed page. Factory only, outputs withheld. Protect/read back pages30/31 with actual WRP configuration after provisioning; option provisioning and power interruption remain hardware gates.',
 'torn_flash_model':'Prefix and final doubleword byte interruptions in software; no claim of atomic flash writes/ECC brownout or full bootloader proof.'})
write('record-and-wire-proposal.json',{
 'status':'PROPOSED_IS2_NOT_ADOPTED','version':'MBR2','base_IOL1_wire_frame_bytes':40,'CNC3_command_feedback_bytes':[96,176],'soldered_regions':{'0':'DIC11','1':'DOA21','2':'DOB21','3':'ACC31'},
 'one_motherboard_serial_shared_by_all_regions':True,'actual_unique_MCU_UID_per_region':True,'no_removable_card_identity_or_custom_board':True,
 'record_layout':[
 [0,4,'MBR2 magic'],[4,1,'record format2'],[5,1,'IOL1 functional class'],[6,1,'actual fitted lane/slot'],[7,1,'hardware major0..15'],[8,1,'hardware minor'],[9,1,'IS2 integrated topology1'],[10,2,'512byte length BE'],[12,4,'nonzero generation BE, no wrap allocation'],[16,16,'common board serial printableASCII zero padded'],[32,12,'actual STM32 UID bytes atUID_BASE in address order'],[44,2,'layout revision BE'],[46,2,'minimum/max CNC3ABI bytes'],[48,4,'minimum/max firmware u16BE'],[52,4,'minimum/max gateware u16BE'],[56,10,'source population12motors/4ABZ/24DI/16DO/2probe/2freq/2PWM/2AO/4AI/0Flanes, no qualification'],[66,2,'zero reserved'],[68,32,'electrical source manifest SHA256'],[100,32,'own board-region calibration record SHA256, actual method/range/units/provenance in separately bound record'],[132,32,'actual factory test record SHA256'],[164,32,'firmware image SHA256'],[196,16,'SHA256 public key fingerprint prefix'],[212,228,'FF reserved'],[440,64,'Ed25519 signature over0..439'],[504,4,'CRC32C over0..503'],[508,4,'CMT2 commit tag']
 ],
 'IDENT_READ_supplement':{'control':8,'telemetry_request':255,'command_payload10':'chunk0..63','command_payload11_35':'zero','response_telemetry_page':'0x80|chunk','response26_27':'chunk index u16BE','response28_35':'actual8B record slice orFF when unprovisioned','response_realtime10_25':'ordinary actual realtime preserved','response_header3':'actual integrity-validated observed HWmajor inuppernibble, actualfittedslot inlower','latency':'prepared after preceding CSrelease, chunk selection only after full acceptedCRC/epoch/sequence command','authority':'none'},
 'DIC_CONFIG_frozen_bytes':{'control':16,'telemetry_request':255,'payload10':'blob0','payload11':'format1','payload12_14':'3 group debounce100us units0..255','payload15_34':'zero','payload35':'zero','actual_applied_CRC':'page1 telemetry32..35 over exact24B config','config_storage':'volatile only, cleared onnewactualepoch; noflashwrites'},
 'trust':{'CRC':'integrity only','target_UID':'mix-up check, not secure remote attestation','host_signature':'real Ed25519 under explicit supplied registry','production_trust':'notimplemented, cannot be granted by renamedfixturemetadata','ACTIVE_outputs_ARM':'notimplemented and remainsLOW','calibration_accuracy':'notinferred from hash/signature'},
 'backwards_safe':'Unprovisionedflash yields nofactoryrecord, major0, noACTIVE; original polls/SYNC unchanged. NewIDENT supplement/version requires coordinated host/master review beforeadoption. Diagnostic major0 reader cannot silently accept provisionedmajor1.',
 'machine_license':'independent machine-bound entitlement; board serial replacement doesnotrequire software repurchase; licensingnotimplementedbyrecord'})
readme='''# Staged one-motherboard record and DIC configuration

This is a proposed IS2 supplement and actual report-local C implementation. Four fitted STM32G031 controllers belong to one motherboard. They share its board serial, with each region record bound to its real MCU UID. No EEPROM, removable card or custom daughterboard was added.

The target executes a flash-record integrity reader and read-only IDENT telemetry chunking. A separate host verifier checks actual Ed25519 signatures under explicitly supplied keys. CRC is not authentication; a UID check in ordinary firmware is not secure attestation. No manufacturer trust root is provisioned, and developer-key metadata can never produce production trust. The signature does not prove fitted parts, factory measurements, calibration accuracy or wiring.

The frozen DIC CONFIG_WRITE payload is validated before sequence, accepted time and configuration change. The three group values drive elapsed-time debounce at 100us units. Configuration invalidation/replacement restarts the candidate stability timer. Rejected frames retain the prior configuration and never reload accepted progress. A new accepted epoch clears configuration qualification; nothing becomes ACTIVE. Runtime flash erase/program and an update bootloader remain absent.

The linker reserves independent final2KiB pages, leaving60KiB for application. No WRP/RDP/BOR/IWDG option bytes have been provisioned or measured. The two-page prefix/commit tests are software fault models. Actual flash ECC/torn-write behavior, factory programming/write protection and power loss require hardware qualification.

The IDENT chunk supplement is explicit and unadopted:40B IOL1 and96/176B CNC3 lengths stay unchanged,16B realtime stays intact, and8B record chunks use selected telemetry. Existing diagnostic acquisition still expects major0; coordinated host/master firmware work is required for provisioned revisions. Calibration and factory-test hashes bind separately retained records; missing records remain unqualified. Offline machine entitlement stays separate from board identity.

Evidence categories: Python cryptographic/record execution; the same C validators/filter with sanitizers; actual simulated SPI into that C; four ARM target compilations. These are not execution of DMA/IRQ/MMIO or physical flash/IO measurements.
'''
(S/'README.md').write_text(readme,newline='\n')
for run in ['compiled-record-config-r05','actual-SPI-record-config-r01','compiled-mutations-r01']:
 r=json.loads((P/run/'receipt.json').read_text());assert r['status']=='PASS'
O=P/'record-config-replay-candidate-r01'
if O.exists():raise RuntimeError('fresh frozen bundle required')
shutil.copytree(S,O,ignore=shutil.ignore_patterns('__pycache__'))
files={str(p.relative_to(O)):sha(p) for p in O.rglob('*') if p.is_file()}
(O/'bundle-manifest.json').write_text(json.dumps({'files':files,'frozen':True,'proposal_not_live_adoption':True},indent=2)+'\n')
print(json.dumps({'bundle':str(O),'manifest_sha256':sha(O/'bundle-manifest.json'),'file_count':len(files)}))
