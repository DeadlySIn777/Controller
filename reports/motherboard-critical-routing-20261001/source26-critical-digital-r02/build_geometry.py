"""Frozen-source, explicitly conditional prototype geometry; no source/CAD edits.

Qucs project documentation equations 11.4--6, 11.15--18, 11.22--25:
Hammerstad/Jensen quasi-static, finite-copper, uncovered isolated microstrip.
Soldermask, adjacent conductors, actual manufacturing tolerances and dispersion
are deliberately not replaced with invented corrections or guaranteed bounds.
"""
from pathlib import Path
import copy,hashlib,json,math
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def model(w,h,t,er):
 u=w/h;th=t/h
 du1=th/math.pi*math.log(1+4*math.e/(th/math.tanh(math.sqrt(6.517*u))**2))
 dur=du1/2*(1+1/math.cosh(math.sqrt(er-1)))
 def air(ur):
  f=6+(2*math.pi-6)*math.exp(-(30.666/ur)**.7528)
  return 376.730313668/(2*math.pi)*math.log(f/ur+math.sqrt(1+(2/ur)**2))
 ur=u+dur
 a=1+math.log((ur**4+(ur/52)**2)/(ur**4+.432))/49+math.log(1+(ur/18.1)**3)/18.7
 b=.564*((er-.9)/(er+3))**.053
 ee=(er+1)/2+(er-1)/2*(1+10/ur)**(-a*b)
 z=air(ur)/math.sqrt(ee)
 ee_corrected=ee*(air(u+du1)/air(ur))**2
 delay=math.sqrt(ee_corrected)/.299792458 # ps/mm, light velocity .299792458 mm/ps
 return dict(characteristic_impedance_ohm=z,effective_permittivity=ee_corrected,
  propagation_ps_per_mm=delay,distributed_capacitance_pf_per_mm=delay/z,
  not_a_lumped_GPIO_load=True)
def main():
 r=json.loads((OUT/'critical-digital-source-review.json').read_text())
 f=json.loads((OUT/'primary-timing-facts.json').read_text())
 independent=json.loads((OUT/'independent-review.json').read_text())
 assert r['passed']and independent['passed']and f['STM32G031']['actual_target']['GPIO_OSPEEDR_write_present']
 ordinary=ROOT/'reports/motherboard-ordinary-routing-20261001/source26-review-r08/ordinary-source-review.json'
 excluded=set(json.loads(ordinary.read_text())['nets'])
 x=model(.35,.22,.07,4.45)
 assert 45<x['characteristic_impedance_ohm']<55
 rows={}
 for name,source in r['nets'].items():
  if name in excluded:continue
  row=copy.deepcopy(source)
  row.update(layers=['F.Cu','B.Cu'],width_mm=.35,clearance_mm=.20,
   prototype_geometry_authorized=True,operating_profile_qualified=False,
   impedance_factory_qualified=False,allow_unreferenced_escape=False,
   allow_isolation_barrier_crossing=False,geometry_authority='bounded prototype engineering selection',
   engineering_single_ended_target_ohm=50,engineering_impedance_tolerance_percent=10,
   nominal_uncovered_microstrip_model=x,
   factory_stackup_field_solver_and_loaded_waveform_qualification_required=True,
   actual_path_flight_and_receiver_load_proof_required=True,
   source_resistor_and_clocktap_topology_immutable=True,
   existing_source_stub_distance_screen_is_not_manufacturer_limit=True,
   retained_copper_widths_are_immutable_and_discontinuities_need_actual_model=True)
  rows[name]=row
 prototype=dict(schema_version=1,kind='exact_critical_digital_prototype_geometry',passed=True,
  prototype_geometry_authorized=True,route_execution_requires_exact_passed_same_board_plane_binding=True,
  operating_profile_qualified=False,impedance_factory_qualified=False,manufacturing_ready=False,
  source_review_sha256=sha(OUT/'critical-digital-source-review.json'),
  source_design_sha256=r['source_design_sha256'],source_netlist_sha256=r['source_netlist_sha256'],
  ordinary112_sha256=sha(ordinary),ordinary112_net_names_unchanged=True,
  exact_nets=len(rows),ordinary_already_owned_names_excluded=sorted(set(r['nets'])&excluded),
  numeric_geometry=dict(signal_width_mm=.35,clearance_mm=.20,through_via_diameter_mm=.60,
   drill_mm=.30,own_return_stitch_max_distance_mm=1.0,corridor_margin_mm=.40),
  nominal_stackup_metadata=dict(outer_copper_mm=.070,outer_to_reference_dielectric_mm=.220,
   relative_permittivity=4.45,soldermask_mm=.010,factory_qualified=False),
  nominal_approximation=x,
  model_limitations=['no soldermask correction','no nearby-conductor/coupled-line model',
   'no vendor production thickness or dielectric tolerance','no dispersion or actual driver IBIS',
   'no pad/package discontinuity model','no assertion distributed trace C is lumped CL',
   'no guarantee of datasheet maximum receiver/input capacitance'],
  primary_microstrip_source=json.loads((OUT/'primary/microstrip-source.json').read_text()),
  supporting_independent_review_sha256=sha(OUT/'independent-review.json'),
  primary_timing_sha256=sha(OUT/'primary-timing-facts.json'),
  target_speed_correction_receipt_sha256=sha(ROOT/'reports/motherboard-iol1-firmware-20261001/ospeed-r01/receipt.json'),
  nets=rows)
 (OUT/'prototype-route-geometry-review.json').write_text(json.dumps(prototype,indent=2)+'\n')
 proposal=copy.deepcopy(prototype);proposal.update(kind='critical_digital_exact_net_proposal',
  source_revision=26,board_binding_required=True,plane_geometry_qualified=False,route_execution=False)
 (OUT/'route-configuration-proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
 print(json.dumps(dict(exact_prototype_nets=len(rows),nominal_model=x)))
if __name__=='__main__':main()
