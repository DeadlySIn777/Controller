"""Isolated source/native fuse-land proof; never writes frozen source11/root."""
import argparse,json,shutil,subprocess,hashlib,collections
from pathlib import Path
import pcbnew
from hardware_apply_fuse_geometry_upgrade import ROOT,REFS,NEW,PRIMARY,apply_fuse_geometry,patch_native_tree,parse,dump,sha
from hardware_route_logic_return import pad_identity,identity,mm
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);src=ROOT/'hardware/motherboard_power_entry';sch=src/'motherboard_power_entry.kicad_sch';model=src/'design.json';frozen={str(p):sha(p)for p in [sch,model,a.board,PRIMARY]};t,m,rr=apply_fuse_geometry(parse(sch.read_text()),json.loads(model.read_text()));sout=a.out/'motherboard_fuse_geometry.kicad_sch';sout.write_text(dump(t)+'\n');(a.out/'design.json').write_text(json.dumps(m,indent=2)+'\n')
 for ext in ['.kicad_pro']:
  shutil.copyfile(sch.with_suffix(ext),sout.with_suffix(ext))
 (a.out/'sym-lib-table').write_text((src/'sym-lib-table').read_text().replace('${KIPRJMOD}',src.as_posix()));shutil.copytree(ROOT/'hardware/motherboard_fuse_geometry/CNC_MB_Fuse.pretty',a.out/'CNC_MB_Fuse.pretty');lib=(a.board.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()).rstrip();(a.out/'fp-lib-table').write_text(lib[:-1]+' (lib (name "CNC_MB_Fuse") (type "KiCad") (uri "${KIPRJMOD}/CNC_MB_Fuse.pretty") (options "") (descr "Keystone primary mounting drawing")))\n')
 run=subprocess.run([CLI,'sch','erc','--format','json','--severity-all','-o',str(a.out/'erc.json'),str(sout)],capture_output=True,text=True);assert run.returncode==0;e=json.loads((a.out/'erc.json').read_text());assert not e.get('ignored_checks');vi=[v for s in e['sheets']for v in s.get('violations',[])];assert not vi
 fp=pcbnew.FootprintLoad(str((a.out/'CNC_MB_Fuse.pretty').resolve()),'Keystone_3568_M55');assert fp is not None;lands=[dict(pin=p.GetNumber(),position_mm=mm(p.GetPosition()),hole_mm=pcbnew.ToMM(p.GetDrillSize().x),size_mm=mm(p.GetSize()))for p in fp.Pads()];assert len(lands)==4
 b=pcbnew.LoadBoard(str(a.board.resolve()));old={v.m_Uuid.AsString():identity(v)for v in b.GetTracks()};oldp={p.m_Uuid.AsString():p for p in b.GetPads()};dest=a.out/'fuse-land-corrected-candidate.kicad_pcb';dest.write_text(dump(patch_native_tree(parse(a.board.read_text())))+'\n')
 for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name,dirs_exist_ok=True)
 q=pcbnew.LoadBoard(str(dest.resolve()));q.BuildConnectivity();pcbnew.ZONE_FILLER(q).Fill(q.Zones());pcbnew.SaveBoard(str(dest),q);q=pcbnew.LoadBoard(str(dest.resolve()));q.BuildConnectivity();now={v.m_Uuid.AsString():identity(v)for v in q.GetTracks()};assert now==old;changes=[]
 for p in q.GetPads():
  r=p.GetParentFootprint().GetReference();oldpad=oldp[p.m_Uuid.AsString()];assert p.GetNetname()==oldpad.GetNetname()and p.GetNumber()==oldpad.GetNumber()and p.GetSize()==oldpad.GetSize()
  if r not in REFS:assert pad_identity(p)==pad_identity(oldpad)
  else:changes.append(dict(ref=r,pin=p.GetNumber(),uuid=p.m_Uuid.AsString(),old_position_mm=mm(oldpad.GetPosition()),new_position_mm=mm(p.GetPosition()),old_hole_mm=pcbnew.ToMM(oldpad.GetDrillSize().x),new_hole_mm=pcbnew.ToMM(p.GetDrillSize().x)))
 run=subprocess.run([CLI,'pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());assert not any(v['severity']=='error'for v in d['violations']);assert all(sha(Path(p))==h for p,h in frozen.items())
 rr.update(source_hashes=frozen,native_ERC_errors=0,native_ERC_warnings=0,native_DRC_types=dict(collections.Counter(v['type']for v in d['violations'])),native_land_rows=lands,exact_native_pad_changes=changes,all_other_pad_and_copper_identities_preserved=True,source_and_parent_unchanged=True,source_candidate_sha256=sha(sout),native_candidate_sha256=sha(dest),manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(rr,indent=2)+'\n');print(json.dumps({k:v for k,v in rr.items()if k not in ['source_hashes','exact_native_pad_changes','native_land_rows']}))
if __name__=='__main__':main()
