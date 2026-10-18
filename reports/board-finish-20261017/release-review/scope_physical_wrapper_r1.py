"""Source-only, exact-135-pin physical wrapper ownership and gap inventory."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv
import hashlib
import io
import json
import re

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'reports/board-finish-20261017'
OUT = BASE/'release-review/physical-wrapper-scope-r1'
assert not OUT.exists()
OUT.mkdir()

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

csv_source = BASE/'release-review/R299-actual-256-ball-source-pinmap.csv'
rows = [r for r in csv.DictReader(csv_source.open(newline='',encoding='utf-8-sig'))
        if r['assigned_user_ball'].lower() == 'true']
assert len(rows)==135 and len({r['logical_signal'] for r in rows})==135

def owner(s):
    if re.fullmatch(r'(STEP|DIR)\d+_FPGA|EN\d+_N_FPGA',s):
        return ('motion36','implemented runtime leaf; physical adapter required',
                'cnc3_runtime_sim step_out/dir_out/enable_n[11:0]; cnc3_runtime_state; cnc3_stepgen_runtime',
                'Bind exact channel/polarity. Preserve asynchronous raw-inhibit cut and deliberate restart. SIM2 does not establish physical authority.')
    if re.fullmatch(r'ALM\d+_FPGA',s):
        return ('alarms12','implemented synchronization/filter leaf; physical adapter required',
                'cnc3_alarm_filter raw[11:0]',
                'Actual current-flow polarity, configurable alarm interpretation, all12 independent; filter valid is not board qualification.')
    if re.fullmatch(r'ENC\d+_[ABZ]_FPGA',s):
        return ('encoder12','implemented counter/filter leaf; physical validity missing',
                'cnc3_encoder_runtime; runtime encoder_a/b/z[3:0]',
                'Three-stage synchronization exists. Validity must include actual supply/region health; a static differential receiver output is not cable identity or health.')
    if s.startswith('HOST_SPI_'):
        return ('host_spi5','implemented protocol leaf; physical pad wrapper missing',
                'cnc3_spi_transport_stateful',
                'Bind both CS, SCLK/MOSI and MISO output-enable; exact96/176-byte protocol retained. Add actual clock/IO timing constraints, not parallel SIM2 ports.')
    if re.fullmatch(r'IOL1_L[0-3]_(CS_N|SCLK|MOSI|MISO)',s):
        return ('iol1_16','implemented read-only physical bitstream acquisition; production authority missing',
                'prefix-record-full-r01/composed_family_mapping/{cnc_iol1_record_acquisition,cnc_iol1_record_master,cnc_mbr2_stream_checker}.v',
                'Four actual serial lane masters validate complete CRC/identity/epoch/sequence/age. Diagnostic observations cannot become SIM2 provider_ready or authenticated/ACTIVE authority.')
    if s in ('PRB0_FPGA','PRB1_FPGA'):
        return ('probe2','implemented event/filter leaf; physical validity missing',
                'cnc3_runtime_events probe_raw[1:0]',
                'Retain actual polarity/filter/capture selection and one-shot arm. Require fresh actual frontend power/fault observations.')
    if s.startswith('FAST_SR_'):
        return ('fast_sr3','missing RTL acquisition/qualification in canonical runtime',
                'motherboard_operator design sr_serialized_bits; no canonical FAST_SR consumer found',
                '24 bits, H-first nearest bit0, marker1010 bits20..23;6250000Hz,100us polling,double-read agreement,three bad markers latch. Reports actual port faults/MPG selectors; do not fabricate healthy.')
    if s in ('FREQ0_FPGA','FREQ1_FPGA','MPG_A_FPGA','MPG_B_FPGA'):
        return ('frequency_mpg4','missing current runtime function',
                'physical fast-input receiver source only; SIM2 feature bits exclude MPG',
                'Need synchronized capture/count, validity/age and exact protocol integration before advertising. Do not trade off four ABZ or twelve motors.')
    if s in ('PWM0_FPGA','PWM1_FPGA','PEN0_CMD','PEN1_CMD'):
        return ('pwm_process4','unsupported by current SIM2; production logic missing',
                'cnc3_runtime_state rejects nonzero unsupported process/PWM/AO payloads',
                'Diagnostic-only idle LOW is truthful inhibited behavior, not an implemented product function. Physical permission/slew/inhibit limits and provider chain need implementation.')
    if s in ('FAST_PORTS_ENABLE','XF_POWER_ENABLE'):
        return ('port_power2','physical power policy missing',
                'motherboard_operator source power switches and FAST_SR fault observations',
                'Implement requested enable policy, real observation qualification, interruption and deliberate restart; no constant healthy flags or automatic recovery.')
    if s in ('FPGA_CLK_50M','FPGA_USER_RESET_N','RAILS_OK_FPGA'):
        return ('clock_reset3','physical reset/CDC wrapper missing',
                '50MHz board source; historical asynchronous reset assertion/synchronous release pattern',
                'RAILS_OK_FPGA actually binds /FPGA_CRESET_N. Review this source meaning separately from the user reset; do not infer all field rails healthy.')
    if s in ('RAW_INHIBIT_N','WD_M_OK','WD_O_OK','WATCHDOG_TRIP_M','WATCHDOG_TRIP_O','TAMPER_CLEAR_N',
             'EXT_PERMIT_FPGA','PROCESS_PERMIT_FPGA','SAFETY_STATUS_FPGA','RESET_ARM_FPGA',
             'CONTACTOR_FB_FPGA','STO_FB_FPGA'):
        return ('safety_observation12','pins present; physical qualification adapter missing',
                'runtime state input contract; motherboard_safety_sensor; mc_permission; watchdog_conditioning',
                'Synchronize/report real observations with raw-inhibit asynchronous capture. RESET_ARM readiness/held/consumed needs edge policy, not direct constant. WATCHDOG_TRIP_M/O source nets are active-low WD_M_TRIP_N/O_TRIP_N.')
    if s in ('TX_PERMIT','OUT_PERMIT','PROC_PERMIT','MOTION_A_PGOOD','MOTION_B_PGOOD',
             'OPI_OK_TX','OPI_OK_A','OPI_OK_B','OPI_OK_BOE','OPI_OK_OUT'):
        return ('permission_health10','physical observations present; exact runtime handshake mapping missing',
                'runtime gate_high/opi_ok/output_gate_high/output_opi_ok; motherboard motors and mc_permission',
                'PGOOD is local power; actual MOTOR_TX_GATE_A/B ANDs filtered permission with power. PGOOD alone cannot stand for gate-high. Preserve separate OUT and BOE latches.')
    if s in ('FPGA_MOTION_REQUEST','FPGA_OUTPUT_REQUEST','PERMIT_OUT_REQ','FPGA_PROGRESS_M','FPGA_PROGRESS_O',
             'OPI_REARM_M','OPI_REARM_O','WATCHDOG_TRIP_CLEAR','ARM_LAMP_FPGA'):
        return ('permission_drive9','runtime requests partly implemented; physical sequencer missing',
                'runtime state motion/output request, permit/progress and OPI strobes; actual common motor rearm stem',
                'One physical OPI_REARM_M fans to TX/A/B/BOE; OUT has separate rearm. Do not OR virtual rearm bits without proving shared-domain startup/disarm/fault behavior. Watchdog trip clear/recovery and ARM lamp require actual policy.')
    if s in ('FPGA_ENDPOINT_READY','FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_INHIBIT_FAULT','FPGA_TIMING_FAULT'):
        return ('status5','missing physical status adapter',
                'runtime fault_word/config/qualification; historical diagnostic status pins',
                'Derive from actual physical qualification and sticky fault semantics. Do not make endpoint_ready a clock-alive or diagnostic-sample-valid alias.')
    raise AssertionError('Unclassified physical pin '+s)

inventory=[]
for row in rows:
    group,state,reuse,gap=owner(row['logical_signal'])
    inventory.append({**{k:row[k] for k in ['ball','logical_signal','direction','bank','io_standard','source_net','board_raw_net']},
        'group':group,'source_state':state,'reusable_source':reuse,'required_physical_work':gap})
with (OUT/'actual135-pin-ownership.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=inventory[0].keys());writer.writeheader();writer.writerows(inventory)

relative_inputs=[
    'docs/MOTHERBOARD_IS2.md','gateware/v3/runtime/ABI.md',
    *['gateware/v3/runtime/'+s+'.v' for s in ['cnc3_runtime','cnc3_runtime_sim','cnc3_runtime_provider','cnc3_runtime_cap3','cnc3_runtime_state','cnc3_alarm_filter','cnc3_encoder_runtime']],
    'gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v',
    'gateware/motherboard_bringup/cnc_motherboard_watchdog_bringup.v',
    'gateware/motherboard_iol1_target_bringup/cnc_motherboard_iol1_target_bringup.v',
    *['hardware/'+d+'/design.json' for d in ['motherboard_operator','motherboard_fast_inputs','motherboard_motors','motherboard_control_bridges','motherboard_safety_sensor','mc_permission']],
    'hardware/motherboard/assembly-map.json',
    'firmware/motherboard_iol1_readonly/README.md','firmware/motherboard_iol1_readonly/iol1.h','firmware/motherboard_iol1_readonly/iol1.c','firmware/motherboard_iol1_readonly/target.c',
    *['reports/cnc3-iol1-integrated-records-20261002/prefix-record-full-r01/composed_family_mapping/'+n for n in ['cnc_iol1_record_acquisition.v','cnc_iol1_record_master.v','cnc_mbr2_stream_checker.v','cnc3_motion_acquisition_composition.v','receipt.json']],
    *['reports/cnc3-iol1-integrated-records-20261002/prefix-record-candidate-r01/record_bundle/'+n for n in ['board_record.h','board_record.c','iol1.c','iol1.h','dic_filter.c','dic_filter.h','target.c']],
    'reports/cnc3-iol1-integrated-records-20261002/arithmetic-sharing-handoff-r01/receipt.json',
]
bindings={p:sha(ROOT/p) for p in relative_inputs}
bindings[str(csv_source.relative_to(ROOT)).replace('\\','/')]=sha(csv_source)
report = r'''# Source scope of the physical T20 wrapper

The actual135-pin contract is usable pin evidence. It is not a physical runtime top. The selected resource optimization remains disconnected SIM2, with external parallel model observations and `physical_authority=0`. Every one of the135 assigned source pins is classified in `actual135-pin-ownership.csv`; no extra pins or model provider buses are assumed.

## Smallest honest next wrapper

A report-local inhibited diagnostic top can bind the135 exact physical ports, actual clock/reset, host SPI leaf, all12 alarm receivers, all4 ABZ leaves and four real read-only IOL1 lane masters. Keep every motor enable inactive, STEP/DIR and permission/progress/rearm/clear requests inactive, process/PWM inactive, and mark all unsupported or unqualified observations unavailable. Such safe output levels are the declared purpose of an inhibited diagnostic profile; they cannot be used as proof that the complete production runtime works. Distinct diagnostic capability/provenance is required, not SIM2 identity with manufactured provider inputs. This is a source proposal only; no new top was compiled, mapped, placed, routed or programmed in this audit.

Do not instantiate `cnc3_runtime_sim` and tie model session/hash/tag/valid buses to invented values. `cnc3_runtime` itself hard-ties simulation context low and remains intentionally denied. For a later functional physical runtime, factor shared motion/transport/event leaves from the SIM2 provider boundary, add a real qualified provider and bind that provider to actual acquisition/configuration/health state. The SIM2 guard remains unchanged and must continue to reject physical operation.

## Reusable implemented source

* Current runtime leaves implement twelve STEP/DIR/individual-enable channels, twelve separately filtered alarms, four ABZ counters/index captures, two probe captures, exact96/176-byte transport,256events, motion/output watchdog state, sequence/configuration and disarm/continuity policy. Their physical observations currently come from the explicitly disconnected model.
* `reports/cnc3-iol1-integrated-records-20261002/prefix-record-full-r01/composed_family_mapping/` provides `cnc_iol1_record_acquisition.v`, `cnc_iol1_record_master.v` and `cnc_mbr2_stream_checker.v`. These are actual four-lane serial CRC/class/slot/epoch/sequence/age and streamed MBR2 shape/CRC observation logic. Read-only `commercial_active`, `factory_identity_verified` and `signature_authenticated` remain false. The composed motion/acquisition top deliberately leaves qualified provider inputs external and does not make diagnostic data authorize motion.
* Matching report-local target sources exist in `prefix-record-candidate-r01/record_bundle/{target.c,iol1.c,iol1.h,board_record.c,board_record.h,dic_filter.c,dic_filter.h}`. `target.c` reads the actual hardware UID and both factory Flash slots. `mb_record_integrity` checks class/slot/UID, descriptor shape, generation, commit and CRC; it explicitly cannot authenticate a signature. This is stronger than a fabricated UID, but is not authenticated factory provenance.
* The canonical `firmware/motherboard_iol1_readonly` has actual GPIO sampling, exact physical SPI/DMA/clock-count admission and accepted-frame-only IWDG refresh. It never implements ACTIVE/output application. DIC/DO/ACC are diagnostic; ACC reports ADC/DAC unavailable while its real permission chain holds converters in reset.
* Historical `cnc_motherboard_motion_bringup` has a useful asynchronous raw-inhibit capture, synchronous reset release and pad gate pattern. It is six-axis/two-encoder CNC1 evidence. Both motherboard diagnostic wrappers extend the arrays with six inhibited channels; they cannot be substituted for the twelve-channel current runtime.

## Concrete physical gaps

1. **Provenance and qualified provider:** existing sources can acquire real record/UID/CRC/configuration observations, but no complete production verifier/trust/provisioning/provider composition was found. The checked streamer and C descriptor parser explicitly reject any inference of authenticated factory trust. `diagnostic_sample_valid` cannot become runtime readiness. A non-cryptographic input-integrity profile can truthfully report those observations with authority denied. Complete physical provenance/authority needs real trust provisioning/verification and the exact hardware/source/config lineage binding; a true constant cannot supply it. No new cryptographic product requirement is invented here: this is the existing source's explicitly unfinished trust boundary.
2. **Physical safety adapter and common motor rearm:** current runtime models four motion gate levels and four rearm bits, plus separate output gate/rearm. The actual135 pins expose TX/OUT/PROC permissions, A/B PGOOD and five OPI observations, but only one motor rearm stem and one independent output rearm. Assembly source ties OPI_REARM_A/B to `/fpga_core/OPI_REARM_M`; R12001/R12002 fan that same stem to TX/BOE. This coupling requires an explicit physical handshake policy; blindly OR-ing four model strobes is not a proof. A/B PGOOD is not MOTOR_TX_GATE_A/B: the actual gate also includes filtered received permission, and the gate is not a separate assigned FPGA input. Preserve the independent latch observations and evaluate real shared-strobe startup/disarm/fault behavior. WATCHDOG_TRIP_M/O logical names bind active-low WD_M_TRIP_N/O_TRIP_N; RAW_INHIBIT needs asynchronous cut/capture, reset release synchronization, sticky interruption and deliberate rearm. The model's separate RESET_ARM ready/held/consumed and contactor/STO booleans need real pin polarity/filter/edge/state derivation.
3. **Actual serial output application:** read-only IOL1 target/master code deliberately rejects output-authority commands and keeps enables low. Sixteen DO application, per-driver configuration/CRC, neutral feedback, real fault/readback/age, new-epoch recovery and accepted-frame-only progress need complete FPGA and MCU implementation. SW_STATE is command readback, not measured terminal voltage. Preserve local1ms accept timers/IWDG and hardwired permission cuts. The current runtime's DO mismatch/provider logic can be reused after a real provider exists.
4. **Input/source ownership:** no canonical FAST_SR acquisition consumer was found. Actual operator source has24bits: H-first bit0; marker1010 in bits20..23;6.25MHz read clock;100us polling; two agreeing reads; three bad markers latch. These include actual six frontend supply faults, MPG selectors and actual accessory observations. They cannot become all-healthy defaults. Four ABZ valid bits require physical supply/region validity. Home/limit semantic arrays are machine mappings of actual DI, not36 additional physical pins. FREQ0/1 and MPG A/B currently lack their complete runtime functions and valid/age integration.
5. **Remaining fitted interfaces:** process/PWM/AO are deliberately rejected/unavailable by SIM2. Physical process permission, live converter/driver acquisition, protected port enable/restart, telemetry and complete CAP3 profile remain missing. Keep the required interfaces and truthful capability flags; do not silently remove product functions to fit. Safe idle in a diagnostic top is not production completion.
6. **Package implementation:**135-pin naming/voltage checks and core resource mapping are separate. A physical top still needs exact IO primitive/OE behavior, 50MHz/host/IOL1 timing constraints, CDC/reset analysis, vendor package placement/routing/timing and later loaded hardware measurements. SIM2 parallel top resource reports cannot qualify these gates.

## Minimal implementation order

First build a distinct inhibited135-pin diagnostic adapter with real read-only serial acquisition and direct alarm/encoder/probe observation; its raw fault/age/provenance output must be inspectable and every unsafe request must remain inhibited. Add the exact24-bit FAST_SR reader/marker/age/fault policy from actual source. Then implement the shared physical safety/rearm adapter with stateful fault/reset tests and use exact physical pin names in vendor compilation. Only after those inputs are real should a separate physical provider and matched MCU output application be composed with the qualified shared runtime leaves. Frozen SIM2 tests remain a regression baseline and cannot serve as acceptance of the new physical trust/authority chain.

The earlier19477 LUT4+ADD arithmetic-sharing result is historical report-local motion plus diagnostic record acquisition. It explicitly omits CAP3/full provider/output/event logic, and is not a current full-system resource budget. No resource estimate in this audit adds that entire historical composition to the new runtime; that would double-count motion/transport leaves.
'''
(OUT/'scope.md').write_text(report,encoding='utf-8')
receipt={
    'status':'SOURCE_ONLY_PHYSICAL135_OWNERSHIP_AND_EXPLICIT_GAPS',
    'created_utc':datetime.now(timezone.utc).isoformat(),
    'assigned_source_pins':135,
    'all_pins_classified_exactly_once':True,
    'group_counts':dict(sorted(Counter(r['group'] for r in inventory).items())),
    'input_SHA256':bindings,
    'outputs':{p.name:sha(p) for p in OUT.iterdir() if p.is_file()},
    'implemented_from_existing_sources':{'read_only_actual_acquisition_and_descriptor_integrity':True,
        'complete_authenticated_physical_provider_and_production_outputs':False},
    'new_HDL_tests_vendor_compile_PNR_or_physical_execution':False,
    'source_inspection_only':True,
    'canonical_RTL_firmware_CAD_modified':False,
    'production_adopted':False,
}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':receipt['status'],'groups':receipt['group_counts'],'receipt_SHA256':sha(OUT/'receipt.json')}))
