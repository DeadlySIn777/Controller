"""Explicit conventional RAW power transitions, with real TVS source paths.

15 x 0.50/0.20 vias per transition; plating/current sharing/thermal require
factory and prototype qualification. No assumed current rating per via.
"""
from pathlib import Path
import pcbnew,argparse,json,shutil,subprocess,collections,math
from hardware_route_current_delivery_native import Geometry,sha
from hardware_route_logic_return import mm,xy,identity,pad_identity
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);b=pcbnew.LoadBoard(str(a.board.resolve()));g=Geometry(b);fps={f.GetReference():f for f in b.GetFootprints()};old={v.m_Uuid.AsString():identity(v)for v in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};add=[];zones=[];rows=[]
 for d,pt in [('D11001',(321.4,174.5)),('D11002',(324.4,159.5)),('D11003',(329.4,224.5))]:
  p=next(v for v in fps[d].Pads()if v.GetNumber()=='1');n=p.GetNetname();s=mm(p.GetPosition());assert math.dist(s,pt)<=6
  points=[(pt[0]+.8*x,pt[1]+.8*y)for x in [-2,-1,0,1,2]for y in [-1,0,1]]
  assert g.clear([s,pt],n,pcbnew.F_Cu,2),d
  for q in points:
   assert all(g.clear([q,q],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]),(d,q)
   for f in fps.values():
    for pp in f.Pads():
     if pp.GetAttribute()in [pcbnew.PAD_ATTRIB_NPTH,pcbnew.PAD_ATTRIB_PTH]:assert math.dist(q,mm(pp.GetPosition()))>.25+.1+pcbnew.ToMM(max(pp.GetDrillSize()))/2,(d,q,f.GetReference())
   v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(q));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);add.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role='RAW_15_via_power_array'))
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetStart(xy(s));t.SetEnd(xy(pt));t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(2));b.Add(t);g.add(t);add.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role='RAW_short_2mm_pad_neck'))
  for layer in [pcbnew.F_Cu,pcbnew.B_Cu]:
   z=pcbnew.ZONE(b);z.SetNet(b.FindNet(n));z.SetLayer(layer);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(.15));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetAssignedPriority(100);z.Outline().NewOutline()
   ps=[(pt[0]-1.9,pt[1]-1.1),(pt[0]+1.9,pt[1]-1.1),(pt[0]+1.9,pt[1]+1.1),(pt[0]-1.9,pt[1]+1.1)]
   for x,y in ps:z.Outline().Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
   b.Add(z);zones.append(dict(uuid=z.m_Uuid.AsString(),net=n,layer=b.GetLayerName(layer),polygon_mm=ps))
  rows.append(dict(ref=d,pin='1',net=n,power_anchor_mm=pt,via_count=15,pad_neck_length_mm=math.dist(s,pt),pad_neck_width_mm=2))
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'raw-power-transitions-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();now={v.m_Uuid.AsString():identity(v)for v in q.GetTracks()};assert all(now[k]==v for k,v in old.items());assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()};assert all(now[v['uuid']]==v['identity']for v in add)
 for row in rows:
  p=next(v for f in q.GetFootprints()if f.GetReference()==row['ref']for v in f.Pads()if v.GetNumber()==row['pin']);reach={v.m_Uuid.AsString()for v in q.GetConnectivity().GetConnectedItems(p)};assert all(v['uuid']in reach for v in add if v['identity'][1]==row['net'])
 run=subprocess.run([CLI,'pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;dd=json.loads((a.out/'drc.json').read_text());result=dict(source_board=str(a.board),source_sha256=sha(a.board),candidate_sha256=sha(dest),exact_added_copper=add,exact_added_zones=zones,power_anchors=rows,all_old_pad_and_copper_identities_preserved=True,native_drc_types=dict(collections.Counter(v['type']for v in dd['violations'])),native_errors=[v for v in dd['violations']if v['severity']=='error'],via_plating_thermal_current_sharing_qualified=False,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['exact_added_copper','exact_added_zones','native_errors']}))
if __name__=='__main__':main()
