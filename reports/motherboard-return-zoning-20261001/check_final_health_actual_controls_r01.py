"""Exact immutable actual U20/U26 control/reference checks, no provider claim."""
from pathlib import Path
import argparse,sys,json
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew as p
from hardware_map_motherboard_domains import write,sha
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();inputs={str(q):sha(q)for q in(a.board,Path(__file__),Path(__file__).with_name('check_exact_endpoint_antipad_union_r01.py'))}
b=p.LoadBoard(str(a.board));b.BuildConnectivity();pads={(f.GetReference(),q.GetNumber()):q for f in b.GetFootprints()for q in f.Pads()if q.GetNumber()};decls={}
for owner in('U11020','U11026'):
 d=dict(return_net=pads[owner,'2'].GetNetname(),reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4);decls.update({pads[owner,q].GetNetname():d for q in('1','3')})
c=ExactEndpointUnionCheck(b,decls);rows=[]
for t in b.GetTracks():
 if t.GetNetname()not in decls:continue
 try:r=c.via(t,decls[t.GetNetname()])if t.Type()==p.PCB_VIA_T else c.segment(t,decls[t.GetNetname()]);rows.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),passed=True,review=r))
 except ValueError as e:rows.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),passed=False,error=str(e)))
assert all(sha(Path(q))==h for q,h in inputs.items());write(a.out,dict(passed=bool(rows)and all(r['passed']for r in rows),board_sha256=sha(a.board),input_sha256=inputs,margin_mm=.4,rows=rows,provider_loaded_timing_or_all_temperature_qualification=False,manufacturing_ready=False));print(json.dumps(dict(passed=all(r['passed']for r in rows),actual_controls_checked=len(rows),errors=[r for r in rows if not r['passed']])))
if any(not r['passed']for r in rows):sys.exit(1)
