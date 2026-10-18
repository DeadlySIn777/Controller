"""Isolated native motor-alarm geometry fixture; no source board mutation."""
from pathlib import Path
import argparse,json,hashlib,shutil,subprocess,collections
import pcbnew
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def xy(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--recipes',type=Path,required=True);ap.add_argument('--group',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);digest=sha(a.board);old=pcbnew.LoadBoard(str(a.board.resolve()));fs={f.GetReference():f for f in old.GetFootprints()};group=json.loads(a.recipes.read_text())['groups'][a.group];b=pcbnew.BOARD();nets={}
    b.SetCopperLayerCount(old.GetCopperLayerCount())
    for n in sorted({p.GetNetname()for r in group for p in fs[r].Pads()if p.GetNetname()}):v=pcbnew.NETINFO_ITEM(b,n);b.Add(v);nets[n]=v
    for r,(x,y,ang)in group.items():
        f=pcbnew.FOOTPRINT(fs[r]);f.SetPosition(xy(x+30,y+30));f.SetOrientationDegrees(ang)
        for p in f.Pads():
            n=p.GetNetname()
            if n:p.SetNet(nets[n])
        b.Add(f)
    for x,y,s,t in [(10,10,70,10),(70,10,70,50),(70,50,10,50),(10,50,10,10)]:l=pcbnew.PCB_SHAPE();l.SetShape(pcbnew.SHAPE_T_SEGMENT);l.SetLayer(pcbnew.Edge_Cuts);l.SetStart(xy(x,y));l.SetEnd(xy(s,t));l.SetWidth(pcbnew.FromMM(.05));b.Add(l)
    dest=a.out/'motor-alarm-cell-fixture.kicad_pcb';pcbnew.SaveBoard(str(dest),b);shutil.copyfile(a.board.with_suffix('.kicad_pro'),dest.with_suffix('.kicad_pro'))
    if a.board.with_suffix('.kicad_dru').exists():shutil.copyfile(a.board.with_suffix('.kicad_dru'),dest.with_suffix('.kicad_dru'))
    (a.out/'fp-lib-table').write_text((a.board.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
    run=subprocess.run([CLI,'pcb','drc','--format','json','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0;j=json.loads((a.out/'drc.json').read_text());assert sha(a.board)==digest
    result=dict(source_sha256=digest,source_unchanged=True,fixture_only=True,parts=len(group),native_drc_types=dict(collections.Counter(r['type']for r in j['violations'])),unconnected_native_items=len(j['unconnected_items']),actual_routing_completed=False,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
