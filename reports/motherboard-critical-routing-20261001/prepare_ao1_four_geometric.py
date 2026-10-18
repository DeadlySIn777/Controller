from pathlib import Path
import sys,json,copy,shutil
sys.path.insert(0,str(Path('tools').resolve()))
import hardware_route_critical_digital_wip_r05 as a
e=a.engine
src=Path('reports/motherboard-critical-routing-20261001/actual-AO1-DAC5-geometric-corridor-proposal-r02');out=Path('reports/motherboard-critical-routing-20261001/actual-AO1-DAC4-geometric-native-r01');out.mkdir(exist_ok=False)
board=src/'motherboard-AO1-five-digital-candidate.kicad_pcb';t=e.parse(board.read_text());r=e.read(src/'search-receipt.json');remove=[]
for s in list(e.children(t,'segment')):
 if e.value(e.child(s,'uuid')[1])in r['added_copper_uuids']and e.value(e.child(s,'net')[1])=='/motherboard_analog_output/AO1_DAC_SCLK':remove.append(e.value(e.child(s,'uuid')[1]));t.remove(s)
dest=out/'motherboard-AO1-four-geometric-candidate.kicad_pcb';dest.write_text(a.dump_native_board(t)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(board.with_suffix(suffix),dest.with_suffix(suffix))
for f in src.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
r.update(removed_only_unfinished_new_SCLK_neck_UUIDs=remove,added_copper_uuids=[v for v in r['added_copper_uuids']if v not in remove],reference_qualification_pending=True,native_DRC_pending=True,source_package_geometry_unchanged=True,manufacturing_ready=False)
e.write(out/'proposal.json',r);print(json.dumps(dict(newCu=len(r['added_copper_uuids']),removedSCLKneck=len(remove))))
