"""Current prototype readiness report, explicitly separating remaining engineering from hardware gates."""
from pathlib import Path
import json,hashlib
root=Path.cwd();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
ad=root/'reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01/adoption.json';a=read(ad)
full=Path(a['full_validation_report']);f=read(full)
pub=root/'hardware/board_review/revisions/20261002-30/publication.json';p=read(pub)
assert a['board_sha256']==p['native_pcb_sha256'] and p['published']
out=root/'reports/motherboard-readiness-20261002/ROOT104';out.mkdir(parents=True,exist_ok=False)
record=dict(status='BLOCKED_ENGINEERING_INCOMPLETE',manufacturing_ready=False,working_revision='ROOT104',source_revision='Source26',published_CAD='20261002-30',board_sha256=a['board_sha256'],input_sha256={str(v.relative_to(root)):sha(v)for v in [ad,full,pub,Path(__file__)]},routing=dict(fully_joined_multi_pad_nets=633,incomplete_multi_pad_nets=1101,total_multi_pad_nets=1734,required_unconnected_joins=3508,native_independent_counts_agree=True,orphan_copper=0,track_via_items=11807),native_checks=dict(ERC_errors=0,ERC_unsuppressed_warnings=70,DRC_regular_errors=0,DRC_regular_warnings=0,ignored_checks=[],unconnected_display_cap=499),mechanical=dict(width_mm=460,height_mm=340,layers=6,thickness_mm=1.6,stackup_vendor_qualified=False),manufacturing_outputs=dict(native_PCB=True,schematic_netlist=True,designator_BOM=True,nonproduction_CAD=True,final_Gerbers=False,final_drill_files=False,production_CPL=False,final_assembly_drawings=False,PCBWay_turnkey_quote=False),cost=dict(currency='USD',known_priced_consumed_parts_per_board={'1':1091.51,'10':877.37,'100':796.51},priced_exact_MPNs=105,unpriced_MPNs=185,unpriced_purchased_fitted_pieces=720,complete_manufactured_board_cost=None,plug_in_modules=None,screens=None,complete_kit_cost=None),validation=dict(full_status_counts=f['status_counts'],host_tests_passed=1895,native_tests_passed=238,Windows_symlink_skips=5,source_hashes_unchanged=4041,actual_SPI_seeded_cases=2048,reset_fault_mechanics_scenarios=18,complete_machine_profiles=0,physical_tests=0,release_guard_tests=37),remaining_engineering=['3508 required joins; all power/return and critical interface routing must be completed.','Source27 reset/health circuit corrections and current-loop/global-reference reconciliation are staged and unadopted. Full20ms inhibit and startup/missing-module behavior are not yet proven across the actual complete circuit.','277 paste-land/drill intersections across274 inherited vias require layout correction or specifically qualified filled/capped fabrication and assembly.','Complete HAL/CNC3/provider integration,ordinary output authority,record identity/provisioning and all9 machine profiles remain unfinished.','FPGA composed implementation exceeds the current coarse resource screen; optimization and exact vendor package fit/timing remain open.','Full analog chain convergence,return-path/power/current/thermal/cable/load qualification,mechanical interference and manufacturing stackup/rules remain incomplete.','Complete quoted costing,production fabrication/drill/CPL/assembly outputs and final independent reviews remain unfinished.'],external_or_physical_gates=['Exact Efinity device/package place-and-route and timing need the vendor toolchain.','PCB fabricator/assembler must qualify exact stackup,via process,assembly limits and complete turnkey quote before release.','Assembled prototype validation is required for20ms inhibit,fault/default-safe behavior,signal integrity,EMI,thermal/current and electrical ratings.'])
(out/'readiness.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
text='''# ROOT104 prototype readiness — 2 October 2026

**Not ready for manufacture.** The working PCB and published CAD30 have identical bytes. This is a verified routing increment, not a completed prototype package.

| Item | Exact current result |
|---|---|
| Routing | 633 fully joined and 1,101 incomplete multi-pad nets; **3,508 required joins remain**. Native and independent counts agree. Zero orphan copper. |
| Native ERC | 0 errors; 70 unsuppressed, individually documented warnings. |
| Native regular DRC | 0 errors, 0 warnings, no ignored checks. Unrouted connectivity remains a separate failing completion gate. |
| Board | 460 × 340 × 1.6 mm; six layers; vendor stackup not qualified. |
| Files | Native PCB/project/rules, source schematic/netlist, designator BOM and current CAD render. **No final Gerbers, drills, production CPL or final assembly package.** |
| Partial consumed BOM at 1 / 10 / 100 | US$1,091.51 / $877.37 / $796.51. 185 exact MPNs and 720 purchased fitted pieces remain unpriced. Modules, screens and manufacturing costs are separate unknowns. |
| Fresh full validation | 25 PASS, 9 BLOCKED, 1 physical NOT_RUN, 0 FAIL; 1,895 host and 238 native cases pass, five Windows symlink skips. All 4,041 tracked inputs unchanged during the run. |
| Additional evidence | 2,048 fresh actual SPI fault trials; 18 reset/fault mechanics scenarios; bounded diagnostic IOL1 and read-only IS2 profile; 37 release-guard tests pass after canonical report serialization was corrected. |

The increment adds 48 controlled copper objects and retains every prior copper object, pad, placement and zone definition. Scoped proofs now cover 120 bypass loops, 245 receiving returns and 188 Source-anchored filled resources. A saved/refilled removal of the additions restores the exact prior copper and Source clusters with 3,521 joins. These checks do not constitute whole-board completion.

The whole-board Freerouting trials did not produce usable routed output within their bounds. A protected local-region trial produced a real session but reported both selected joins still unrouted; native acceptance is tracked in the separate Freerouting evaluation. No Freerouting copper is included in ROOT104.

## Engineering still required

'''+''.join('- '+s+'\n'for s in record['remaining_engineering'])+'''
## External and physical gates

'''+''.join('- '+s+'\n'for s in record['external_or_physical_gates'])+'''
Internal engineering gates remain; the remaining blockers cannot honestly be described as only purchasing or physical prototype tests. The one-custom-board architecture and existing source scope remain in place.
'''
(out/'README.md').write_text(text,encoding='utf8',newline='\n')
print(json.dumps(dict(passed=True,report=str(out/'README.md'),manufacturing_ready=False)))
