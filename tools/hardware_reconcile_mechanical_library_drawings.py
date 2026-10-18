"""Bounded project-copy housing-outline layer reconciliation; source libs read-only."""
import hashlib,json,shutil,subprocess
from pathlib import Path
import pcbnew as p
from hardware_route_logic_return import identity

ROOT=Path(__file__).resolve().parents[1];CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
source=ROOT/'reports/motherboard-pcb-integration-20260930/mechanical-access-r22'
out=ROOT/'reports/motherboard-pcb-integration-20260930/mechanical-library-r23-r03'
if out.exists():raise SystemExit('Use a fresh immutable candidate directory')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,d):f.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def pad_records(f):
    return sorted([(v.GetNumber(),tuple(v.GetPosition()),tuple(v.GetSize()),tuple(v.GetDrillSize()),v.GetDrillShape(),v.GetShape(),tuple(v.GetOffset()),v.GetLayerSet().FmtBin(),v.GetAttribute(),v.GetRoundRectRadiusRatio(),v.GetChamferPositions(),v.GetChamferRectRatio(),v.GetOrientationDegrees(),v.GetNetname())for v in f.Pads()],key=repr)
def glyph(g):
    return (int(g.GetShape()),tuple(g.GetStart()),tuple(g.GetEnd()),g.GetWidth())
def local(f):
    z=p.FOOTPRINT(f);z.SetOrientationDegrees(0);z.SetPosition(p.VECTOR2I(0,0));return z
def fpid(f):return str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())
before={str(f.relative_to(ROOT)):sha(f)for f in source.rglob('*')if f.is_file()}
shutil.copytree(source,out)
inputboard=source/'motherboard-mechanical-candidate.kicad_pcb';b=p.LoadBoard(str(inputboard))
oldpads={f.GetReference():pad_records(f)for f in b.GetFootprints()};oldpose={f.GetReference():[tuple(f.GetPosition()),f.GetOrientationDegrees(),fpid(f)]for f in b.GetFootprints()};oldcopper={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
changes=json.loads((source/'receipt.json').read_text())['exact_silkscreen_body_outline_layer_changes']
fps={f.GetReference():f for f in b.GetFootprints()};wanted={}
for record in changes:
    f=local(fps[record['reference']]);shapes=[g for g in f.GraphicalItems()if isinstance(g,p.PCB_SHAPE)and g.m_Uuid.AsString()==record['uuid']]
    assert len(shapes)==1 and shapes[0].GetLayer()==p.F_Fab
    wanted.setdefault(fpid(f),set()).add(glyph(shapes[0]))
ledger=[];applied=[];stock=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
for fid,keys in wanted.items():
    nickname,name=fid.split(':');lib=out/(nickname+'.pretty');src=(source/(nickname+'.pretty')/(name+'.kicad_mod'))
    if not src.exists():src=stock/(nickname+'.pretty')/(name+'.kicad_mod')
    assert src.is_file(),fid
    lib.mkdir(exist_ok=True);dest=lib/(name+'.kicad_mod');f=p.FootprintLoad(str(src.parent),name);oldland=pad_records(f);oldsha=sha(src);n=0
    for g in f.GraphicalItems():
        if isinstance(g,p.PCB_SHAPE)and glyph(g)in keys:
            assert g.GetLayer()==p.F_SilkS,(fid,glyph(g),g.GetLayer());g.SetLayer(p.F_Fab);n+=1
    assert n==len(keys),(fid,n,keys)
    p.PCB_IO_KICAD_SEXPR().FootprintSave(str(lib),f)
    fresh=p.FootprintLoad(str(lib),name);assert oldland==pad_records(fresh)
    ledger.append({'FPID':fid,'original_path':str(src),'original_sha256':oldsha,'project_copy_path':str(dest),'project_copy_sha256':sha(dest),'layer_only_shape_count':n,'native_pad_piece_records_before':oldland,'native_pad_piece_records_after':pad_records(fresh),'identical_land_pass':True})
    for target in b.GetFootprints():
        if fpid(target)!=fid:continue
        normalized=local(target);mapped={g.m_Uuid.AsString():glyph(g)for g in normalized.GraphicalItems()if isinstance(g,p.PCB_SHAPE)};count=0
        for g in target.GraphicalItems():
            if isinstance(g,p.PCB_SHAPE)and mapped[g.m_Uuid.AsString()]in keys:
                assert g.GetLayer()in (p.F_SilkS,p.F_Fab);g.SetLayer(p.F_Fab);count+=1
        assert count==len(keys),(target.GetReference(),count)
        applied.append({'reference':target.GetReference(),'FPID':fid,'housing_shapes_on_Fab':count,'land_pose_and_pin1_rect_pad_preserved':True})
# A project-local alias replaces lookup for the whole library nickname, so
# carry every other Phoenix footprint actually used by this board verbatim.
# This avoids changing source geometry or creating unresolved library checks.
unchanged_library_copies=[]
for fid in sorted({fpid(f)for f in b.GetFootprints()}):
    nickname,name=fid.split(':')
    if nickname!='Connector_Phoenix_MC':continue
    dest=out/(nickname+'.pretty')/(name+'.kicad_mod')
    if dest.exists():continue
    src=stock/(nickname+'.pretty')/(name+'.kicad_mod');assert src.is_file()
    shutil.copyfile(src,dest);assert sha(src)==sha(dest)
    unchanged_library_copies.append({'FPID':fid,'original_path':str(src),'copy_path':str(dest),'sha256':sha(src)})
# The two stock Phoenix families get a project-local alias; global/system and
# electrical source library files remain unchanged. Existing custom aliases
# already resolve to copied directories in this exact project.
table=(out/'fp-lib-table').read_text()
if '(name "Connector_Phoenix_MC")'not in table:
    i=table.rfind(')');table=table[:i]+'  (lib (name "Connector_Phoenix_MC") (type "KiCad") (uri "${KIPRJMOD}/Connector_Phoenix_MC.pretty") (options "") (descr "Bounded housing outline silk-to-Fab project copy; exact lands unchanged"))\n'+table[i:]
(out/'fp-lib-table').write_text(table,encoding='utf-8')
dest=out/'motherboard-mechanical-candidate.kicad_pcb';p.SaveBoard(str(dest),b);fresh=p.LoadBoard(str(dest))
assert oldpads=={f.GetReference():pad_records(f)for f in fresh.GetFootprints()}
assert oldpose=={f.GetReference():[tuple(f.GetPosition()),f.GetOrientationDegrees(),fpid(f)]for f in fresh.GetFootprints()}
assert oldcopper=={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
assert len(fresh.GetFootprints())==2663 and len(list(fresh.GetTracks()))==8048
assert before=={str(f.relative_to(ROOT)):sha(f)for f in source.rglob('*')if f.is_file()}
cmd=[str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(out/'drc-r23.json'),str(dest)]
r=subprocess.run(cmd,capture_output=True,text=True);(out/'drc-r23-command.txt').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0
drc=json.loads((out/'drc-r23.json').read_text());report={'input_board_sha256':sha(inputboard),'candidate_board_sha256':sha(dest),'source_directory_inputs_sha256':before,'source_unchanged':True,'physical_parts':len(fresh.GetFootprints()),'track_via_items':len(list(fresh.GetTracks())),
 'all_native_pad_geometry_pin_nets_piece_counts_and_poses_unchanged':True,'all_native_copper_UUID_geometry_and_nets_unchanged':True,'project_copied_library_overrides':ledger,'unchanged_other_library_members_copied':unchanged_library_copies,'all_instances_of_modified_family_consistent':applied,
 'native_DRC_regular_violations':len(drc['violations']),'native_DRC_ignored_checks':drc.get('ignored_checks',[]),'uncapped_missing_joins':fresh.GetConnectivity().GetUnconnectedCount(False),
 'technically_justified_scope':'Exact existing project-copy FPID/MPN/land pattern retained. Only declared overhanging housing outline shapes move from clipped silk to full Fab on all family instances. Rectangular pin1 lands and retained on-substrate pin1 glyphs remain. No DRC suppression or source electrical-library mutation.',
 'manufacturing_ready':False}
write(out/'graphic-layer-reconciliation-receipt.json',report);shutil.copyfile(__file__,out/'issued-reconcile-tool.py')
print(json.dumps({'library_families':len(ledger),'instances':len(applied),'native_DRC':len(drc['violations']),'ignored':drc.get('ignored_checks',[]),'parts':len(fresh.GetFootprints()),'copper':len(list(fresh.GetTracks()))}))
assert not drc['violations'] and not drc.get('ignored_checks')
