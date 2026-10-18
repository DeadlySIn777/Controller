import sys,json,shutil,math,subprocess,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,xy,identity
from hardware_route_local_signals import paths
from hardware_route_current_delivery_native import sha
B=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-cell-r202/motor-health-U20-cell-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-offland-return-r214');O.mkdir(exist_ok=False)
r=json.loads((B.parent/'receipt.json').read_text());ret={v['uuid']for v in r['exact_added_copper']if v['role']=='U11020_own_bypass_return'};vu=next(v['uuid']for v in r['exact_added_copper']if v['role']=='U11020_local_Source_return_stitch')
t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-return-retired.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));v=next(v for v in b.GetTracks()if v.m_Uuid.AsString()==vu);v.SetPosition(xy((337.15,175.85)));g=FastGeometry(b);n=v.GetNetname();p=next(p for p in b.GetPads()if p.GetParentFootprint().GetReference()=='C11079'and p.GetNumber()=='2');a=mm(p.GetPosition());z=mm(v.GetPosition());pts=next((p for p in paths(a,z)if g.clear(p,n,pcbnew.B_Cu,.25)),None)
if pts is None:pts=g.grid(a,z,n,pcbnew.B_Cu,.25,step=.1,padding=5,max_nodes=45000)
assert pts,('RETURN',a,z);new=[]
for s,e in zip(pts,pts[1:]):
 tr=pcbnew.PCB_TRACK(b);tr.SetNet(b.FindNet(n));tr.SetStart(xy(s));tr.SetEnd(xy(e));tr.SetWidth(pcbnew.FromMM(.25));tr.SetLayer(pcbnew.B_Cu);b.Add(tr);g.add(tr);new.append(dict(uuid=tr.m_Uuid.AsString(),identity=identity(tr),role='U11020_own_bypass_return'))
r['exact_added_copper']=[v for v in r['exact_added_copper']if v['uuid']not in ret]
for q in r['exact_added_copper']:
 if q['uuid']==vu:q['identity']=identity(v)
r['exact_added_copper']+=new
r['routes']=[q for q in r['routes']if q['role']!='U11020_own_bypass_return'];r['routes'].append(dict(role='U11020_own_bypass_return',net=n,layer='B.Cu',width_mm=.25,points_mm=pts,uuids=[v['uuid']for v in new],length_mm=sum(math.dist(a,z)for a,z in zip(pts,pts[1:]))))
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();D=O/'motor-health-U20-cell-candidate.kicad_pcb';pcbnew.SaveBoard(str(D),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(D)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());err=[v for v in d['violations']if v['severity']=='error'];assert not err,err
r.update(candidate_sha256=sha(D),native_errors=err,native_types=dict(collections.Counter(v['type']for v in d['violations'])),receiving_return_offland_correction=dict(via_uuid=vu,old_point_mm=[336.8,175.6],new_point_mm=[337.15,175.85],reason='Actual drilled barrel intersected the fitted C11004.2 SMD land; preserve conventional open via outside fitted SMD lands.'))
(O/'receipt.json').write_text(json.dumps(r,indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary actual health receiving circuit and off-land conventional receiving-return barrel, preserving all Source endpoints and independent final inhibits.',reviewed_footprint_references=list(r['old_poses']),reviewed_copper_delta_UUIDs=sorted(q['uuid']for q in r['exact_retired_copper'])+sorted(q['uuid']for q in r['exact_added_copper']),reviewed_added_zone_UUIDs=[]),indent=2));print('DONE',sha(D),len(r['exact_added_copper']),len(r['exact_retired_copper']),flush=True)
