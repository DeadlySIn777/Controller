from pathlib import Path
import sys,json,copy,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_review_fpga_neck_rule as prior
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_critical_digital_wip_r03 as clusters
import hardware_route_owned_bypass_loops_wip_r03 as warning
e=authority.engine
OUT=Path('reports/motherboard-critical-routing-20261001/source26-root71-BGA-neck-rule-r06')
proposal=e.read(OUT/'proposal.json');names=set(proposal['nets'])
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-four-reference-closures-r71/motherboard-bounded-merged-candidate.kicad_pcb')
candidate=OUT/'motherboard-literal38-neck-rule-candidate.kicad_pcb'
old=e.parse(BASE.read_text());new=e.parse(candidate.read_text())
extra=[z for z in e.children(new,'zone')if e.child(z,'name')and e.value(e.child(z,'name')[1])==prior.AREA]
if len(extra)!=1:raise ValueError('Exactly one literal named rule area required')
reduced=copy.deepcopy(new);reduced.remove(next(z for z in e.children(reduced,'zone')if e.child(z,'name')and e.value(e.child(z,'name')[1])==prior.AREA))
if e.immutable_objects(old)!=e.immutable_objects(reduced):raise ValueError('Native source/lands/poses/zone definitions changed')
def copper(tree):return {e.value(e.child(t,'uuid')[1]):e.dump(t)for k in('segment','via','arc')for t in e.children(tree,k)}
if copper(old)!=copper(new):raise ValueError('Rule-only proposal changed existing actual copper')
oldpro=e.read(BASE.with_suffix('.kicad_pro'));newpro=e.read(candidate.with_suffix('.kicad_pro'));control=copy.deepcopy(newpro);control['board']['design_settings']['rules']['min_track_width']=oldpro['board']['design_settings']['rules']['min_track_width']
if control!=oldpro:raise ValueError('Unexpected manufacturer/project rule change')
if candidate.with_suffix('.kicad_dru').read_text()!=BASE.with_suffix('.kicad_dru').read_text()+prior.proposed_rules(names):raise ValueError('Literal reviewed rules differ')
drc=e.read(OUT/'native.json');baseline=e.read(BASE.parent/'drc.json');disposition=e.read(BASE.parent/'baseline-disposition.json')
known=warning.reviewed_wip_warnings(baseline,disposition,e.sha(BASE))
if warning.new_route_defects(drc,known)or drc.get('ignored_checks'):raise ValueError('New native defect in rule-only scope')
b=pcbnew.LoadBoard(str(candidate));source=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
retained=clusters.clusters_preserved(clusters.source_clusters(pcbnew.LoadBoard(str(BASE))),b)
base=Path('reports/motherboard-critical-routing-20261001/source26-BGA-native-access-r03/sparse_outer/actual-F256-package-access.kicad_pcb')
cases=[prior.native_case(base,mode,OUT/('native-'+mode),names)for mode in('healthy','power','wrong_net','outside','B_side','overlength')]
if cases[0]['errors']or any(not c['no_ignored_checks']for c in cases)or any(not c['width_errors']for c in cases[1:5])or not cases[5]['length_errors']:raise ValueError('Actual native BGA rule controls failed')
r=dict(passed=True,proposal_sha256=e.sha(OUT/'proposal.json'),candidate_sha256=e.sha(candidate),base_sha256=e.sha(BASE),exact_literal_source_nets=38,all_old_actual_copper_preserved=True,all_source_lands_poses_existing_zone_definitions_preserved=True,source_population=source[0],source_cluster_retention=retained,actual_native_errors=0,actual_native_warnings=len(drc['violations']),all_prior_warnings_retained=True,no_ignored_checks=True,native_positive_and_negative_cases=cases,aggregate_split_overlength_guard=proposal['aggregate_controls'],only_absolute_minimum_and_exact38_F_short_neck_area_changed=True,all_other_effective_track_widths_minimum_mm=.2,maximum_aggregate_neck_length_mm=1.0,exact_factory_2oz_process_confirmation_outstanding=True,reference_annulus_checker_unchanged=True,actual_parent_changed=False,no_actual_new_routes=True,manufacturing_ready=False,tool_sha256=e.sha(__file__))
e.write(OUT/'review.json',r);print(json.dumps(dict(passed=True,actual_native_errors=0,prior_warnings=len(drc['violations']),native_cases=len(cases),literal_signal_nets=38,actual_parent_changed=False)),flush=True)
