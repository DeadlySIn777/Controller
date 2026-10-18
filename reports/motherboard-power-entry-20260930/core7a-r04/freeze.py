"""Freeze the exact bounded CORE-only correction and disconnected proofs."""
from pathlib import Path
import hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SRC=ROOT/'hardware/motherboard_power_entry'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=HERE/'receipt-r04.json'
 if out.exists():raise SystemExit('Immutable r04 receipt exists')
 prior=HERE/'prior-r03';old=json.loads((prior/'hardware/motherboard_power_entry/design.json').read_text());new=json.loads((SRC/'design.json').read_text());delta={}
 if set(new['components'])-set(old['components'])!={'C11088'} or set(old['components'])-set(new['components']):raise ValueError('Unreviewed component population delta')
 for ref,p in old['components'].items():
  q=new['components'][ref]
  if p['pins']!=q['pins']:raise ValueError('Existing native pin/net changed '+ref)
  diff={k:{'old':p.get(k),'new':q.get(k)} for k in set(p)|set(q) if p.get(k)!=q.get(k)}
  if diff:delta[ref]=diff
 if set(delta)!={'U11007','R11022','L11001'}:raise ValueError('Unexpected source component delta')
 for p in (prior/'hardware/motherboard_power_entry/CNC_MB_Entry.pretty').glob('*.kicad_mod'):
  if sha(p)!=sha(SRC/'CNC_MB_Entry.pretty'/p.name):raise ValueError('Unreviewed existing land change '+p.name)
 reviewroot=ROOT/'reports/motherboard-compute-20260930/power-closure-r01'
 independent=json.loads((reviewroot/'CORE7-review-receipt.json').read_text())
 for p,h in independent['hashes'].items():
  if sha(reviewroot/p)!=h:raise ValueError('Independent calculation evidence changed '+p)
 geom=json.loads((HERE/'native-geometry-r02/receipt.json').read_text());validation=json.loads((HERE/'validation.json').read_text());erc=json.loads((SRC/'erc.json').read_text())
 ercv=[v for s in erc['sheets'] for v in s['violations']]
 if not geom['passed'] or not validation['passed'] or ercv:raise ValueError('Native geometry/continuity/ERC not clean')
 targets=['motors','motor_power','power_entry','io3_upgrade','io3_window','safety_sensor','probe_limit_upgrade','status','watchdogs']
 cmd=[sys.executable,'-X','utf8','-m','pytest','-q']+[str(ROOT/'tests'/('test_motherboard_'+n+'.py')) for n in targets]
 sources=[p for p in SRC.rglob('*') if p.is_file()]+[ROOT/'tools/hardware_build_motherboard_power_entry.py',ROOT/'tools/hardware_validate_motherboard_power_entry.py',ROOT/'tests/test_motherboard_power_entry.py']
 before={str(p):sha(p) for p in sources}
 run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8');(HERE/'regression.log').write_text(run.stdout+'\n'+run.stderr)
 if run.returncode or any(sha(Path(p))!=h for p,h in before.items()):raise ValueError('Regression failure or source changed during checks')
 add=new['components']['C11088'];files=sources+[HERE/'archive_prior.py',HERE/'native_geometry.py',HERE/'freeze.py',HERE/'validation.json',HERE/'regression.log',HERE/'native-geometry-r02/receipt.json',reviewroot/'CORE7-source-delta.json',reviewroot/'CORE7-review-receipt.json',reviewroot/'power-capacity-review.json',reviewroot/'audit.py',reviewroot/'sources/xal1010.pdf',reviewroot/'sources/susumu-5m-detail.html']
 receipt={'revision':'motherboard-power-entry-r0.4-CORE-only7A','source_frozen_for_parent_integration':True,'prior_r03_files_archived_and_hash_verified':37,
  'pcb_components':221,'purchased_nonPCB_fuses':3,'numbered_pads_native':geom['numbered_pads'],'native_pin_assignments':validation['native_pins'],'native_nc_pins':validation['native_nc_pins'],
  'native_ERC':{'errors':0,'warnings':0,'ignored':0},'native_geometry_DRC':{'violations':0,'ignored_checks':[],'fixture_unconnected_display_count':geom['unconnected_items_count'],'fixture_is_unrouted_not_actual_motherboard':True},
  'exact_component_field_delta':delta,'added_component':{'C11088':add},'every_existing_pin_net_preserved':True,'all_other_existing_components_exactly_preserved':True,'all_original_manufacturer_lands_hash_preserved':True,
  'MOTION_6A_and_field_domains_unchanged':True,'boundary_power':new['boundary_power'],'boundary_inputs':new['boundary_inputs'],'boundary_outputs':new['boundary_outputs'],
  'CORE_board_envelope_a':7,'CORE_silicon_rating_a':10,'CORE_board_7A_physically_qualified':False,'ordinary_normal_load_screen_a':6.63708429339838,
  'load_screen_efficiency_and_unsourced_reservations_are_assumptions':True,'whole_board_stability_thermal_inrush_or_transient_qualified':False,
  'regression_returncode':run.returncode,'regression_stdout':run.stdout.strip(),'source_changed_during_tests':False,
  'parent_adoption_requirements':['Adopt only U11007 same-pad MPN/library identity, R11022 same-land5mohm and L11001 exactlarger Coilcraft land; add C11088 positivepin1CORE5/negativepin2LOGIC_GND.',
   'Preserve all existing electrical pins/nets, MOTION6A, source/FINAL gate interposition and all domain returns.',
   'Review newcoil mechanics/pad1 shortlead orientation, originalpowerhotloops/Kelvin shunt sense and fourthbulk localrouting; run whole-board nativeERC/DRC/connectivity afterward.',
   'Keep7A as unqualified bounded design envelope; no8A/10A promise, no simultaneousall-short continuous-run requirement, no automaticmoduleaux/USB allocation claim.'],
  'parent_or_PCB_files_changed_by_this_task':False,'manufacturing_ready':False,
  'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files))}}
 out.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['revision','source_frozen_for_parent_integration','pcb_components','numbered_pads_native','native_ERC','regression_stdout']}))
if __name__=='__main__':main()
