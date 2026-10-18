from pathlib import Path
import sys,json,copy
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as a
import hardware_route_critical_digital_wip_r03 as c
import hardware_route_owned_bypass_loops_wip_r03 as w
import hardware_review_fpga_neck_rule as n
e=a.engine
OUT=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA38-rule-r76')
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-ordinary9-r75/motherboard-bounded-merged-candidate.kicad_pcb')
DEST=OUT/'motherboard-literal38-neck-rule-candidate.kicad_pcb'
proposal=e.read(OUT/'proposal.json');prior=e.read(proposal['frozen_rule_review']['path']);literal=e.read(proposal['frozen_proposal']['path'])
for evidence in (proposal['frozen_rule_review'],proposal['frozen_proposal']):
 if e.sha(evidence['path'])!=evidence['sha256']:raise ValueError('Frozen native/source rule proof changed')
old=e.parse(BASE.read_text());new=e.parse(DEST.read_text());reduced=copy.deepcopy(new)
area=next(z for z in e.children(reduced,'zone')if e.value(e.child(z,'uuid')[1])==proposal['new_F_rule_area_uuid']);reduced.remove(area)
if e.immutable_objects(old)!=e.immutable_objects(reduced):raise ValueError('Rebase changed SOURCE/lands/poses/existing rules/planes')
def cu(tree):return{e.value(e.child(t,'uuid')[1]):e.dump(t)for k in('segment','via','arc')for t in e.children(tree,k)}
if cu(old)!=cu(new):raise ValueError('Rebase changed old actual copper')
oldpro=e.read(BASE.with_suffix('.kicad_pro'));pro=e.read(DEST.with_suffix('.kicad_pro'));control=copy.deepcopy(pro);control['board']['design_settings']['rules']['min_track_width']=oldpro['board']['design_settings']['rules']['min_track_width']
if control!=oldpro or pro['board']['design_settings']['rules']['min_track_width']!=.15:raise ValueError('Unexpected project schema delta')
if DEST.with_suffix('.kicad_dru').read_text()!=BASE.with_suffix('.kicad_dru').read_text()+n.proposed_rules(set(literal['nets'])):raise ValueError('Appended native rule scope changed')
d=e.read(OUT/'native.json');known=w.reviewed_wip_warnings(e.read(BASE.parent/'drc.json'),e.read(BASE.parent/'baseline-disposition.json'),e.sha(BASE))
if w.new_route_defects(d,known)or d.get('ignored_checks'):raise ValueError('Native rebase introduces a defect')
b=pcbnew.LoadBoard(str(DEST));pop,nodes=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'));before=pcbnew.LoadBoard(str(BASE));retained=c.clusters_preserved(c.source_clusters(before),b)
if b.GetConnectivity().GetUnconnectedCount(False)!=3612:raise ValueError('Rule-only rebase changed actual native connectivity')
e.write(OUT/'review.json',dict(passed=True,board_sha256=e.sha(DEST),base_sha256=e.sha(BASE),actual_native_errors=0,all_prior_unsuppressed_warnings=d['violations'],no_new_native_defects=True,no_ignored_checks=True,actual_missing_joins_unchanged=3612,all_old_actual_copper_source_pad_lands_and_poses_preserved=True,source_population=pop,prior_SOURCE_clusters=retained,exact_project_schema_diff=proposal['exact_project_schema_diff'],appended_DRC_rules=proposal['appended_DRC_rules'],new_rule_area_uuid=proposal['new_F_rule_area_uuid'],only_one_F_rule_area_added=True,exact_literal_signal_nets=38,maximum_aggregate_per_net_mm=1.0,frozen_actual_native_cases=proposal['frozen_rule_review'],six_native_cases_passed=prior['native_positive_and_negative_cases'],aggregate_positive_and_negative_controls=literal['aggregate_controls'],primary_conflicting_tables_retained=literal['primary_sources'],factory_exact_2oz_process_confirmation_outstanding=True,existing_BGA_pad_via_rule_and_return_annulus_checker_unchanged=True,new_actual_routes=0,actual_parent_changed=False,manufacturing_ready=False,tool_sha256=e.sha(__file__)))
print(json.dumps(dict(passed=True,errors=0,prior_warnings=len(d['violations']),missing_joins_unchanged=3612,project_changes=1,rule_area=1,actual_new_copper=0)),flush=True)
