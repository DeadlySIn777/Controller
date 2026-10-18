"""Freeze the actual source22 candidate, primary inputs and bounded proposals."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
from hardware_validate_motherboard_diagnostics import native,validate


def main():
 source=ROOT/'hardware/motherboard_diagnostics';archive=HERE/'source'
 if archive.exists():raise ValueError('Immutable source22 archive already exists')
 shutil.copytree(source,archive)
 primary=HERE/'primary-inputs';primary.mkdir()
 copies={
  'iso7720.pdf':ROOT/'reports/motherboard-compute-20260930/wide-input-independent-review-r01/sources/iso7720.pdf',
  'iso7720.txt':ROOT/'reports/motherboard-compute-20260930/wide-input-independent-review-r01/sources/iso7720.txt',
  'tps3700.pdf':ROOT/'reports/motherboard-analog-input-20260930/sources/tps3700.pdf',
  'tps3700.txt':ROOT/'reports/motherboard-analog-input-20260930/sources/tps3700.txt',
  'tps2663.pdf':ROOT/'reports/motherboard-power-entry-20260930/sources/tps2663.pdf',
  'tps2663.txt':ROOT/'reports/motherboard-power-entry-20260930/sources/tps2663.txt',
  'parent-r20b-netlist.xml':ROOT/'reports/motherboard-audit-20260930/2663-source-r20b-review/inputs/source/netlist.xml',
  'hardware_build_motherboard_diagnostics.py':ROOT/'tools/hardware_build_motherboard_diagnostics.py',
  'hardware_validate_motherboard_diagnostics.py':ROOT/'tools/hardware_validate_motherboard_diagnostics.py',
  'test_motherboard_diagnostics.py':ROOT/'tests/test_motherboard_diagnostics.py',
  'M3-NPTH-official.kicad_mod':Path('C:/Program Files/KiCad/10.0/share/kicad/footprints/MountingHole.pretty/MountingHole_3.2mm_M3.kicad_mod'),
  'TPS3700-DDC-standard-land.kicad_mod':Path('C:/Program Files/KiCad/10.0/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23-6.kicad_mod'),
 }
 for name,path in copies.items():shutil.copy2(path,primary/name)
 d=json.loads((archive/'design.json').read_text(encoding='utf-8'));check=validate(d,native(archive/'netlist.xml'),native(primary/'parent-r20b-netlist.xml'))
 assert check['passed'],check
 (HERE/'parent-domain-validation.json').write_text(json.dumps(check,indent=2)+'\n',encoding='utf-8')
 erc=json.loads((archive/'erc.json').read_text(encoding='utf-8'));viol=[v for s in erc['sheets'] for v in s['violations']]
 assert not erc['ignored_checks'] and all(v['severity']=='warning' and v['type']=='ground_pin_not_ground' for v in viol)
 drc=json.loads((HERE/'fixture-drc.json').read_text(encoding='utf-8'));assert not drc['violations'] and not drc['ignored_checks']
 # Exact proposals only; actual child/parent source is not silently rewritten.
 prior=ROOT/'reports/motherboard-audit-20260930/2663-source-r20b-review'
 semantic=json.loads((prior/'single-pad-semantic-classification.json').read_text(encoding='utf-8'))
 categories={'obsolete_dedicated_machine_status_input','optional_unimplemented_PCIE_compute_endpoint','unused_regulator_builtin_power_good_output','unused_eFuse_FLT_open_drain_output'}
 rows=[{**r,'new_native_disposition':'NC graphical marker on real manufacturer function; preserve pin name and electrical type, remove obsolete labels/page exports','new_physical_net':None} for r in semantic['rows'] if r['category'] in categories]
 assert len(rows)==20
 xml=native(primary/'parent-r20b-netlist.xml')
 for row in rows:assert xml[row['ref']]['pins'][row['pin']]==row['net'].removeprefix('/')
 # The seven machine-status nonphysical boundary pins must also stop exporting
 # obsolete named nets. They are not physical components or deletion savings.
 names={r['net'].removeprefix('/') for r in rows if r['category']=='obsolete_dedicated_machine_status_input'}
 boundary=[]
 for ref,c in xml.items():
  if c['footprint']:continue
  for pin,net in c['pins'].items():
   if net in names:boundary.append({'ref':ref,'pin':pin,'old_native_net':'/'+net,'new_disposition':'NC nonphysical boundary pin; no physical header exists'})
 proposal={'schema_version':1,'exact_parent_input_sha256':hashlib.sha256((primary/'parent-r20b-netlist.xml').read_bytes()).hexdigest(),
  'native_physical_NC_proposals':rows,'obsolete_nonphysical_machine_status_boundary_pins':boundary,
  'proposal_count':20,'source_mutated':False,'actual_parent_change_authorized_by_root_only':True,
  'not_manufacturer_NC_pins':'Builtin PG/FLT and allGPIO retain their real manufacturer functions/types; unused is a circuit disposition, not a different package-pin assignment.',
  'must_preserve':['All66 original promotions plus21 prior deallocations ledger separately','All24DI/IOL1 and actualG12/G15/G16 probe/toolsetter/permit functions','Four liveFPGA fault outputs now exposed by actualsource22 bareTPs','AllSD/eMMC and actualEthernet/HDMI/USB source','FA_PGOOD existing analog divider and distinctA/B/logic returns'],
  'manufacturing_ready':False}
 (HERE/'bounded-NC-proposals.json').write_text(json.dumps(proposal,indent=2)+'\n',encoding='utf-8')
 aliases={'parent_reference_index':22,'required_aliases':{
  'IO_3V3':'/IO_3V3','LOGIC_GND':'/LOGIC_GND','DOA_FIELD_3V3':'/motherboard_do/DOA_FIELD_3V3','FIELD_GND':'/motherboard_motors/FIELD_GND',
  'DOB_FIELD_3V3':'/motherboard_do/DOB_FIELD_3V3','FIELD_B_0V':'/motherboard_do/FIELD_B_0V','FA_PGOOD':'/motherboard_power_entry/FA_PGOOD','FB_PGOOD':'/motherboard_power_entry/FB_PGOOD',
  'DOA_FIELD_POWER_GOOD':'/motherboard_io_control/DOA_FIELD_POWER_GOOD','DOB_FIELD_POWER_GOOD':'/motherboard_io_control/DOB_FIELD_POWER_GOOD',
  **{n:'/fpga_core/'+n for n in ['FPGA_LINK_FAULT','FPGA_WATCHDOG_FAULT','FPGA_INHIBIT_FAULT','FPGA_TIMING_FAULT']}},
  'existing_internal_FA_PGOOD_requires_real_parent_export':True,'preserve_existing_native_netnames':True,'existing_low_biases_not_duplicated':['R13027','R13045']}
 (HERE/'parent-alias-requirements.json').write_text(json.dumps(aliases,indent=2)+'\n',encoding='utf-8')
 receipt={'schema_version':1,'revision':'source22-r01','physical_footprints':20,'purchased_components':10,'bare_fault_testpads':4,'bare_NPTH_M3_mounts':6,'numbered_electrical_pads':56,
  'native_ERC_errors':0,'native_ERC_unsuppressed_warnings':len(viol),'native_ERC_ignored_checks':[],
  'ERC_warning_disposition':'Two manufacturer GND1 pins are on real FIELD_B_0V, which the KiCad net-name heuristic does not call GND; actual domains independently checked, no suppression.',
  'independent_native_source_and_parent_domain_checks':check['checks'],'independent_checks_pass':True,'mutation_tests_passed':19,
  'native_isolated_geometry_fixture_DRC_regular_violations':0,'native_fixture_DRC_ignored_checks':[],
  'fixture_unconnected_items':len(drc['unconnected_items']),'fixture_is_not_routed_motherboard':True,
  'parent_integration_pending':True,'target_GPIO_review':'Motor firmware owner confirms actual readonly PB1 sampled with actual driver diagnostic validity; fixture responses not hardware evidence',
  'independent_topology_review':'docs_sync independently checked exactTPS3700 pins/thresholds/supply and own-return ISO7720F topology; no source mutation',
  'existing_FA_divider_unchanged':True,'existing_field_domains_distinct':True,'new_MCU_GPIO':False,'new_permission_authority':False,
  'source_NC_proposals_applied':False,'physical_partial_power_transient_thermal_EMC_validation':False,'manufacturing_ready':False,
  'source_sha256':{str(p.relative_to(archive)):hashlib.sha256(p.read_bytes()).hexdigest() for p in archive.rglob('*') if p.is_file()},
  'primary_and_tools_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in primary.iterdir() if p.is_file()}}
 (HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:receipt[k] for k in ['physical_footprints','purchased_components','native_ERC_errors','native_ERC_unsuppressed_warnings','independent_checks_pass','mutation_tests_passed']}))


if __name__=='__main__':main()
