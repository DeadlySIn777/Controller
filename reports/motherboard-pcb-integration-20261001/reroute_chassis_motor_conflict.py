"""Reroute one newly added chassis trunk around two exact field-return vias.

No footprint, source net, plane or unrelated copper may change. All actual
CHASSIS pad clusters must remain identical after native refill.
"""
import sys,json,shutil,collections
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_route_logic_return import identity,mm,xy
from hardware_route_owned_bypass_loops import Geometry,drc
from hardware_apply_probe_pin_delta import clusters
from hardware_populate_motherboard_pcb import sha,write,pad_template
source=ROOT/'reports/motherboard-pcb-integration-20261001/motor-source24-merge-r38/motherboard-bounded-merged-candidate.kicad_pcb'
out=ROOT/'reports/motherboard-pcb-integration-20261001/chassis-motor-conflict-r39d';out.mkdir()
dest=out/'motherboard-chassis-detour-candidate.kicad_pcb'
for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(source.with_suffix(suffix),dest.with_suffix(suffix))
for r in source.parent.iterdir():
 if r.is_dir()and(r.suffix=='.pretty'or r.name=='3dmodels'):shutil.copytree(r,out/r.name)
 elif r.name=='fp-lib-table':shutil.copy2(r,out/r.name)
b=pcbnew.LoadBoard(str(source));uid='0af7fc0e-6027-4760-bb45-60e9771bcd1c'
original={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
old=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==uid)
assert old.GetNetname()=='/CHASSIS'and old.GetLayer()==pcbnew.B_Cu
first,last=mm(old.GetStart()),mm(old.GetEnd());width=pcbnew.ToMM(old.GetWidth())
assert {first,last}=={(431.,41.5),(431.,100.5)}
before_clusters=clusters(b,set(),{'/CHASSIS'})
native_pads={p.m_Uuid.AsString():(p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in b.GetPads()}
geometry=Geometry(b);path=None
for x in(429.,428.,427.,426.,432.,432.25,432.5,433.):
 trial=[(431.,41.5),(431.,49.),(x,49.+abs(x-431.)),(x,64.),(431.,64.+abs(x-431.)),(431.,100.5)]
 if geometry.clear(trial,'/CHASSIS',pcbnew.B_Cu,width):path=trial;break
if path is None:
 # The coarse obstacle index can reject a legal route between through-hole
 # connector lands. This exact1mm detour is judged by native DRC below;
 # no violation may be suppressed or waived by the geometric pre-screen.
 raise ValueError('No legal bounded same-layer chassis detour')
b.Remove(old);added=[]
for start,end in zip(path,path[1:]):
 t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet('/CHASSIS'));t.SetLayer(pcbnew.B_Cu);t.SetWidth(pcbnew.FromMM(width));t.SetStart(xy(start));t.SetEnd(xy(end));b.Add(t);added.append(t)
expected={t.m_Uuid.AsString():identity(t)for t in added}
pcbnew.SaveBoard(str(dest),b);report=drc(dest,out,'drc')
errors=[v for v in report['violations']if v['severity']=='error']
if errors:raise ValueError('Actual chassis detour has native errors '+json.dumps(errors))
if any(v['type']!='via_dangling'or v['items'][0]['description'].split('[')[1].split(']')[0]!='/IO_3V3'for v in report['violations']):raise ValueError('Unexpected retained native warning')
fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity()
actual={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
assert set(actual)==(set(original)-{uid})|set(expected)
assert all(actual[k]==v for k,v in original.items()if k!=uid)and all(actual[k]==v for k,v in expected.items())
assert before_clusters==clusters(fresh,set(),{'/CHASSIS'})
assert native_pads=={p.m_Uuid.AsString():(p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in fresh.GetPads()}
write(out/'receipt.json',dict(source_sha256=sha(source),board_sha256=sha(dest),removed_native_copper={uid:original[uid]},added_native_copper=expected,path_mm=path,width_mm=width,all_native_pad_lands_nets_poses_unchanged=True,all_actual_chassis_pad_clusters_retained=True,all_unrelated_copper_unchanged=True,native_errors=0,remaining_actual_IO3_feed_via_warnings=len(report['violations']),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False))
print(dict(path=path,width_mm=width,native_errors=0,remaining_IO3_feed_vias=len(report['violations']),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),board_sha256=sha(dest)))
