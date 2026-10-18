from pathlib import Path
import json,hashlib,math
R=Path(__file__).resolve().parent
geo=json.loads((R/'placement-geometry.json').read_text())
native=json.loads((R/'packing60-native-geometry.json').read_text())
drc=json.loads((R/'packing60-validation/placement-drc.json').read_text())
top=sum(v['area_mm2'] for n,v in geo.items() if n not in ('J1','J2'))
strip_area=(2.37-.25)*(20.15-.25)+(14.99-12.87)*(20.15-2.71)
scenarios=[]
for height in (50,60):
 layout=json.loads((R/f'placement-packing-{height}mm.json').read_text())
 usable=(15.24-.5)*(height-.5)-strip_area
 scenarios.append({'height_mm':height,'extension_beyond_20_32mm_body':height-20.32,
 'top_area_after_0_25mm_edge_and_header_service_strips_mm2':usable,
 'required_courtyard_envelope_area_mm2':top,'spare_area_mm2':usable-top,
 'spare_percent':100*(usable-top)/usable,'attempts':layout['attempts'],
 'unplaced_references':layout['unplaced'],'placement_sha256':hashlib.sha256((R/f'placement-packing-{height}mm.json').read_bytes()).hexdigest()})
lay=json.loads((R/'placement-packing-60mm.json').read_text())['parts']
distances={a+'--'+b:round(math.dist(lay[a][:2],lay[b][:2]),3) for a,b in [('U20','C21'),('U20','D23'),('U20','C22'),('U50','C50'),('Q1','R4')]}
report={'status':'60MM GEOMETRIC PACKING PASS; FUNCTIONAL PLACEMENT AND HOST FIT OPEN',
 'scope':'Actual55nativefootprints;47SMTtop,3THTconnectors top,2THTheaders underside,3testpadstop. Courtyards unchanged. No Gerbers or fabrication release.',
 'width_mm':15.24,'header_row_spacing_mm':12.7,'header_pitch_mm':2.54,
 'header_top_keepout_basis':'1.70mm solder-pad envelope expanded0.25mm, then continuous strips to avoid placing parts between solder tails; clipped atboard0.25mm margin.',
 'header_service_strip_area_inside_margin_mm2':strip_area,
 'top_courtyard_area_mm2':top,'scenarios':scenarios,
 'native_60mm_geometry_issues':native['issues'],
 'native_drc_violation_count':len(drc['violations']),
 'native_drc_violation_types':sorted(set(v['type'] for v in drc['violations'])),
 'native_drc_unconnected_count':len(drc.get('unconnected_items',[])),
 'distance_evidence_not_engineered_routing':distances,
 'remaining_work':['Confirm exacthost and39.68mm provisionalextension clearance before freezing60mm outline.',
 'Replace geometricbinpacking with functionalbuck/MCU/gateclusters; presentplacementmustnotberouted as-is.',
 'Recheck connector mating/latch/fingeraccess,wireexit and maximumtopcomponentheight onactualhost.',
 'Correct5unsuppressedsilkviolations;completeelectricalrouting/ERC/DRC afterward.'],
 'manufacturing_ready':False}
(R/'mechanical-feasibility.json').write_text(json.dumps(report,indent=2)+'\n')
text='''OEA r0.3 mechanical feasibility — bounded packing study,6October2026

The60mm candidate geometrically fits all55actual footprints with all47SMT on
top. This is NOT an engineered placement: power-loop, decoupling and gate
components are too far apart in the automatic packing. Do not route or order
this candidate as-is. It preserves exactlibrarycourtyards; no footprints were
shrunk. The parent r0.3 PCB and placement were not modified.

Actual topcourtyard area:645.605mm². Headerpitch2.54mm;rowspacing12.70mm;
J1=(1.27,1.27) andJ2=(13.97,3.81) onunderside;VM absent. Topheader service
strips use1.70mm solderpad envelopes plus0.25mm clearance, with no components
between soldertails. Both board candidates retain0.25mm courtyard-edge margin.

50x15.24mm:650.4692mm² available after those margins/strips;4.8642mm² spare,
only0.748% of usable area.100bounded packing attempts left12parts unplaced.
This is evidence of a poor target, not a proof no possible arrangement exists.

60x15.24mm:797.8692mm² available;152.2642mm² spare,19.083%. The first bounded
packing attempt placed everyfootprint. Native transformedcourtyard/service-
strip checks found zero overlaps. NativeKiCadDRC found zero courtyard or
copper-clearance violations, but5unsuppressed silkscreen violations and92
unconnected items remain. This is not a clean complete-board DRC result.

The60mm outline extends39.68mm beyond the20.32mm referencebody. Exact host
model and adjacentobstructions remain unknown. The screwterminal faces the
end,with selector inward; actualmating/latchaccess and topheight remain open.
The4mm-inductor height and connector bodies require actualhost/enclosurefit.
A100x50mm hotplate can cover this length along its longaxis; that does not
qualify the solderprofile. SingleSMTface permitsreflowbeforeTHTconnectors.

Saved placement-packing-50mm.json is incomplete. placement-packing-60mm.json
is a full geometriccandidate only. packing60-validation contains a native
mechanicaltestfixtureboard and unsuppressed DRC output; no fabricationfiles
were generated. Repack functionalclusters after hostclearance is known.
The exact sourcehashes, nativeboxes, area arithmetic and diagnosticdistances
are preserved in placement-geometry.json, packing60-native-geometry.json and
mechanical-feasibility.json. No finaloutline or procurement is authorized by
these checks.
'''
(R/'mechanical-feasibility.txt').write_text(text,encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k in ('status','scenarios','native_drc_violation_count','native_drc_unconnected_count','distance_evidence_not_engineered_routing')}))
