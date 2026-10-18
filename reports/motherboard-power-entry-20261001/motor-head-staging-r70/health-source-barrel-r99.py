import sys,json,math,shutil,subprocess,collections
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_current_delivery_native import sha
from hardware_route_local_signals import paths
BASE=Path('reports/motherboard-power-entry-20261001/health-supply-r95/motor-health-supply-candidate.kicad_pcb');OUT=Path('reports/motherboard-power-entry-20261001/health-supply-r99');OUT.mkdir(exist_ok=False);rec=json.loads((BASE.parent/'receipt.json').read_text());b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();g=FastGeometry(b);old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};p=next(p for p in b.GetPads()if p.GetParentFootprint().GetReference()=='C11055'and p.GetNumber()=='1');pt=mm(p.GetPosition());net=p.GetNetname();added=[];chosen=None
for d in[.75,1.,1.25,1.5,2.]:
 for dx,dy in[(1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(-.707107,.707107)]:
  z=(pt[0]+d*dx,pt[1]+d*dy)
  if all(g.clear([z,z],net,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu])and all(g.clear([pt,z],net,l,.25)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):chosen=z;break
 if chosen:break
assert chosen,(pt,net)
v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(chosen));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role='FIELD5_actual_source_cap_barrel'))
for l in[pcbnew.F_Cu,pcbnew.B_Cu]:
 t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetStart(xy(pt));t.SetEnd(xy(chosen));t.SetWidth(pcbnew.FromMM(.25));t.SetLayer(l);b.Add(t);added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role='FIELD5_actual_source_cap_'+b.GetLayerName(l)))
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();assert b.GetConnectivity().IsConnectedOnLayer(v,pcbnew.B_Cu)and v.FlashLayer(pcbnew.B_Cu)
dest=OUT/BASE.name;pcbnew.SaveBoard(str(dest),b)
for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(BASE.with_suffix(ext),dest.with_suffix(ext))
for f in BASE.parent.iterdir():
 if f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
 elif f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(OUT/'drc.json'),str(dest)],capture_output=True,text=True);assert r.returncode==0;d=json.loads((OUT/'drc.json').read_text());err=[v for v in d['violations']if v['severity']=='error'];assert not err,err
assert not any(v['type']=='track_dangling'and any(i['uuid']=='c507d769-eedf-4881-94a9-9d0456bc2681'for i in v['items'])for v in d['violations']);rec['board_sha256']=sha(dest);rec['exact_added_copper']+=added;rec['actual_field5_source_barrel']=dict(source=['C11055','1'],point_mm=chosen,uuid=v.m_Uuid.AsString(),actual_B_annulus_flashed_and_connected=True);rec['native_types']=dict(collections.Counter(v['type']for v in d['violations']));rec['corrected_prior_candidate']=str(BASE);rec['native_errors']=err;(OUT/'receipt.json').write_text(json.dumps(rec,indent=2));(OUT/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[v['uuid']for v in rec['exact_added_copper']],reviewed_added_zone_UUIDs=[]),indent=2));print('SOURCE_BARREL',chosen,sha(dest),len(rec['exact_added_copper']),flush=True)
