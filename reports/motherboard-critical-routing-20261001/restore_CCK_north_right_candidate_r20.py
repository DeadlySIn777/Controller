from pathlib import Path
import sys,copy,json,shutil
sys.path.insert(0,str(Path('tools').resolve()))
import hardware_route_critical_digital_wip_r05 as a
e=a.engine
BASE=Path('reports/motherboard-critical-routing-20261001/CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb')
OLD=Path('reports/motherboard-critical-routing-20261001/actual-source26-root84-CCK-north-right-F-In3-r19')
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False)
old=e.parse(BASE.read_text());donor=e.parse((OLD/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb').read_text());tree=copy.deepcopy(old);plan=e.read(OLD/'proposed-delta.json')
def ref(fp):return next(e.value(p[2])for p in e.children(fp,'property')if e.value(p[1])=='Reference')
old_cap=next(fp for fp in e.children(tree,'footprint')if ref(fp)=='C1022');new_cap=next(fp for fp in e.children(donor,'footprint')if ref(fp)=='C1022');tree[tree.index(old_cap)]=copy.deepcopy(new_cap)
added=set(plan['new_signal_UUIDs']+plan['new_SOURCE_ground_UUIDs']+plan['new_C1022_local_power_UUIDs'])
for kind in ('segment','via','arc'):
 for n in e.children(donor,kind):
  if e.value(e.child(n,'uuid')[1])in added:tree.append(copy.deepcopy(n))
def inventory(t):return{e.value(e.child(n,'uuid')[1]):e.dump(n)for k in('segment','via','arc')for n in e.children(t,k)}
before,after=inventory(old),inventory(tree)
assert all(after.get(u)==v for u,v in before.items()) and set(after)-set(before)==added
immutable_before={ref(fp):e.dump(fp)for fp in e.children(old,'footprint')}
immutable_after={ref(fp):e.dump(fp)for fp in e.children(tree,'footprint')}
assert set(immutable_before)==set(immutable_after) and {r for r in immutable_before if immutable_before[r]!=immutable_after[r]}=={'C1022'}
assert [e.dump(z)for z in e.children(old,'zone')]==[e.dump(z)for z in e.children(tree,'zone')]
dest=OUT/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb';dest.write_text(a.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
shutil.copyfile(OLD/'scoped-F-In3-declaration.json',OUT/'scoped-F-In3-declaration.json')
e.write(OUT/'proposed-delta.json',plan)
e.write(OUT/'authoritative-object-restoration.json',dict(passed=True,base_sha256=e.sha(BASE),draft_sha256=e.sha(OLD/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb'),candidate_sha256=e.sha(dest),all_old_Cu_raw_AST_exact=True,all_unmoved_footprints_raw_AST_exact=True,all_zone_definitions_raw_AST_exact=True,only_native_C1022_pose_changed=True,exact12_new_Cu=sorted(added),native_final_pad_identity_and_DRC_pending=True,relative_CORE_capacity_NOT_qualified=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,actual_new_Cu=len(added),unmoved_native_objects_retained=True)))
