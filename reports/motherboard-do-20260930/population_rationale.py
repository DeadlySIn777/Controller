"""Read-only DI/DO footprint sanity audit for the root880-part audit."""
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
rows=[]
for region in ['motherboard_di','motherboard_do']:
 path=ROOT/'hardware'/region/'design.json';d=json.loads(path.read_text());parts=d['components']
 rows.append({'region':region,'design_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'physical_footprints':len(parts),
  'numbered_electrical_pads':sum(len(p['pins']) for p in parts.values()),
  'MPN_population':dict(collections.Counter(p['mpn'] for p in parts.values())),
  'no_fitted_boundary_connectors':all(not b.get('physical',b.get('fitted',False)) and not b['footprint'] and not b['mpn'] for b in d['boundaries'].values()),
  'custom_card_connectors':0,'compute_or_ESP_sockets':0,'storage_sockets':0,'MCUs_currently_fitted':0,
  'permission_or_health_constant_healthy_sources':0})
rationale={
 '24_DI':{'total':120,'ISO1212_dual_receivers':12,'channel_threshold_resistors':24,'channel_current_set_resistors':24,
  'channel_filter_capacitors':24,'channel_logic_bias_resistors':24,'per_device_logic_decouplers':12,
  'reason':'Twelve independent dual receivers preserve24general DI. Per-channel field thresholds/current/filter/bias differ from twelve motor alarms and two fast probes. Local bypass capacitors are not rack-power duplicates.',
  'open_gaps':'Sensor-power limiters/monitoring and real acquisition MCU remain outside this120-part frontend. No inherited rack identity or connector is fitted.'},
 '16_DO':{'total':110,'quad_smart_switches':4,'output_reverse_blocking_FETs':16,'six_channel_domain_isolators':2,
  'rearm_latches':2,'quad_AND_packages':2,'resistors':40,'capacitors':44,
  'reason':'Four quadTPS devices are the minimum for16outputs. Two isolators preserve separateFIELD_A/B power-return domains. Two rearm latches record independent permission drops/reset; merging them couples domains. Each channel has a source-backed external reverse-blocking FET and output capacitor. Current measurement uses the existingTPS internalADC, with no separate fake ADC/MCU perquad.',
  'capacitor_breakdown':{'logic_gate_and_latch_bypass':4,'isolator_domain_bypass':4,'TPS_VDD_HF_and_stabilizer':8,'TPS_VS_HF_and_local_MLCC':8,'ISNS_filter':4,'per_output_filter':16},
  'resistor_breakdown':{'logic_fail_off':14,'host_CS_idle':2,'field_DOEN_pull_off':2,'field_CLK_and_SDI_bias':4,'field_CS_bias':2,'field_SDO_bias':2,'field_wired_OR_FLT_bias':2,'address_straps':4,'READY_ground':4,'ISNS_current_to_voltage':4},
  'native_NC_pads':28,'unnumbered_paste_only_objects_not_parts_or_electrical_pads':228,
  'open_gaps':'No fitted field connectors, field supply converters/entry/bulk, MCU, identity chip or status LED. Current POR1.25A must not be described as an implemented0.72A setting.'}}
review={'scope':'DI+DO source rationale supporting root880-footprint audit; does not replace root full-board inventory',
 'read_only':True,'rows':rows,'rationale':rationale,
 'current_frontend_totals':{'physical_footprints':230,'numbered_electrical_pads':960,'rack_connectors':0,'compute_sockets':0,'ESP_sockets':0,'storage_sockets':0,'MCUs':0},
 'DO_consolidation_candidates_not_applied':[
  {'candidate':'One logic8-gate AND package instead of two4-gate packages','reason_not_removed':'Current two packages use3gates each. A reviewed8-gate part with independently allocated inputs and safe partial-power behavior could reduce1IC, but changes source/package/pin mapping and all bypass/layout tests. No exact replacement is selected.'},
  {'candidate':'One dualDFF instead of two singleDFF packages','reason_not_removed':'Separate clear/Q functions must remain. Requires an exact true dualDFF with verified pinmap/reset/power and package; SN74LVC2G74 is a SINGLE8-pinDFF and is not this optimization.'},
  {'candidate':'Delete resistor biases on actively driven nodes','reason_not_removed':'Only acceptable after complete driver leakage, partial-power/reset/high-Z review. Inputs such as fieldDOEN and MCU-controlled enables must defaultOFF. No bias is waived by a future firmware claim.'},
  {'candidate':'Combine per-IC decoupling into one global capacitor','reason_not_removed':'Not a valid source-count optimization; local return inductance and TI VDD stabilization requirements survive one-board consolidation.'},
  {'candidate':'MergeFIELD_A/B ground/power or share one isolator/latch','reason_not_removed':'Would eliminate the inherited two independent field/isolation/permission domains; not a like-for-like cost reduction.'},
  {'candidate':'Omit16reverse-blockingFETs oroutputfilters','reason_not_removed':'Removes protected output electrical functions and changes cable/load qualification. No approved omission.'}],
 'IOL1_three_MCU_rationale':{'not_part_of_current_880':True,'standalone_source_candidate_footprints':104,'purchased_parts':86,'factory_copper_test_pads':18,
 'three_nodes':'L0DIC24DI class0x11, L1DOA8DO class0x21, L2DOB8DO class0x21; three soldered functional regions, no cards.',
 'reason':'Retains three independent point-to-point IOL1 SPI slaves with100us periods and parallel59.6us processing windows, plus two independently isolated TPS SPI masters. One STM32G031 has only twoSPI peripherals; it cannot provide3host slaves+2driver masters. Sharing links or one larger MCU changes protocol/peripheral allocation/processing and common-failure domains; it is not a harmless rack-remnant deletion.',
 'candidates_not_applied':['Four extra CARD_EN/STROBE pull-downs in the unintegrated13xxx source duplicate four already-fitted10xxx biases on the final same nets; one reviewed physical10k per net is sufficient. Remove the duplicate source owners only during integration/review, not from either frozenfrontend now.','Three separate rail supervisors keep MCU IWDG/NRST resets local. A common rail supervisor plus properly isolated open-drain fanout may consolidate supply monitoring while preserving local resets; direct tying of allNRST pins is not equivalent.','Four slot bits per node inherit IOL1 electrical straps. Restricting current0–2 IDs to two physical bits can remove6resistors/free6GPIO but requires an explicit revised pin/identity contract. No fake card presence or always-healthy straps are permitted.'],
 'evidence':'Source only; no target firmware, programmed option bytes, factory identity or physical timing proof.'},
 'manufacturing_ready':False}
(OUT/'population-rationale.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'DI_parts':120,'DO_parts':110,'total':230,'rack_connectors':0,'MCUs_currently_fitted':0,'no_source_mutations':True}))
