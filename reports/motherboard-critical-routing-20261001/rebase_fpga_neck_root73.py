from pathlib import Path
import sys,json,copy,shutil
sys.path.insert(0,str(Path('tools').resolve()))
import hardware_route_critical_digital_wip_r05 as a
import hardware_review_fpga_neck_rule as n
e=a.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb')
OLD=Path('reports/motherboard-critical-routing-20261001/source26-root71-BGA-neck-rule-r06')
OUT=Path('reports/motherboard-critical-routing-20261001/source26-root73-BGA-neck-rule-r07');OUT.mkdir(exist_ok=False)
proof=e.read(OLD/'review.json');proposal=e.read(OLD/'proposal.json')
if not proof['passed']or e.sha(OLD/'motherboard-literal38-neck-rule-candidate.kicad_pcb')!=proof['candidate_sha256']:raise ValueError('Frozen rule proof changed')
tree=e.parse(BASE.read_text());old=e.parse((OLD/'motherboard-literal38-neck-rule-candidate.kicad_pcb').read_text())
area=next(z for z in e.children(old,'zone')if e.child(z,'name')and e.value(e.child(z,'name')[1])==n.AREA)
if any(e.value(e.child(z,'uuid')[1])==e.value(e.child(area,'uuid')[1])for z in e.children(tree,'zone')):raise ValueError('Rule-area UUID collides with adopted base')
tree.append(copy.deepcopy(area));dest=OUT/'motherboard-literal38-neck-rule-candidate.kicad_pcb';dest.write_text(a.dump_native_board(tree)+'\n')
project=e.read(BASE.with_suffix('.kicad_pro'));before=project['board']['design_settings']['rules']['min_track_width'];project['board']['design_settings']['rules']['min_track_width']=.15;dest.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2))
newrules=n.proposed_rules(set(proposal['nets']));dest.with_suffix('.kicad_dru').write_text(BASE.with_suffix('.kicad_dru').read_text()+newrules)
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'proposal.json',dict(base_sha256=e.sha(BASE),source_design_sha256=e.sha('hardware/motherboard/design.json'),candidate_sha256=e.sha(dest),frozen_rule_review=dict(path=str(OLD/'review.json'),sha256=e.sha(OLD/'review.json')),frozen_proposal=dict(path=str(OLD/'proposal.json'),sha256=e.sha(OLD/'proposal.json')),exact_project_schema_diff=[dict(path='board.design_settings.rules.min_track_width',before=before,after=.15)],appended_DRC_rules=newrules,new_F_rule_area_uuid=e.value(e.child(area,'uuid')[1]),existing_copper_or_source_or_planes_changed=False,narrow_signal_nets=38,maximum_aggregate_per_net_mm=1.0,all_other_effective_track_minimum_mm=.2,factory_exact_2oz_process_confirmation_outstanding=True,native_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(board=str(dest),project_changes=1,new_rule_area=1,nets=38)),flush=True)
