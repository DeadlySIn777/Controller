"""Inspect exact existing Source-connected barrels for a future In3 connection.

Existing .50/.20 geometry is explicitly declared per UUID, never permission to
change the frozen .60/.30 geometry for a new ordinary via. No copper is added.
"""
from pathlib import Path
import sys,json,copy
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as ordinary
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import identity,mm
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/motherboard-bounded-merged-candidate.kicad_pcb')
M=Path('reports/motherboard-domains-20261001/source26-r101-r01/domain-map.json')
R=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root101-In3-r47/manifest.json')
O=Path('reports/motherboard-ordinary-routing-20261001/ROOT101-existing-status-vias-r49');assert not O.exists();O.mkdir()
ordinary.MAPPING=json.loads(M.read_text());manifest=json.loads(R.read_text())
names={'/mc_permission/OUT_PERMIT','/mc_permission/PROC_PERMIT','/motherboard_status/STATUS_HW_GOOD','/motherboard_status/STATUS_MOTION_RGB_ENABLE','/motherboard_io_control/DI_SENSOR_G2_FAULT'}
rows={k:v for k,v in manifest['nets'].items()if k in names}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();exact={t.m_Uuid.AsString():t for t in b.GetTracks()}
declared={u:dict(net=t.GetNetname(),position=list(mm(t.GetPosition())),diameter_mm=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)),drill_mm=pcbnew.ToMM(t.GetDrill()),identity=identity(t))for u,t in exact.items()if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()in rows}
class ExactRetainedVia(ordinary.LiteralPieces):
 def via(self,v,row):
  u=v.m_Uuid.AsString()
  if u not in declared or identity(v)!=declared[u]['identity']:raise ValueError('Undeclared or changed existing native barrel')
  d=declared[u]
  if (d['diameter_mm'],d['drill_mm'])not in[(.5,.2),(.6,.3)]:raise ValueError('Outside exact existing prototype via geometry')
  exactrow=copy.deepcopy(row);exactrow.update(via_diameter_mm=d['diameter_mm'],via_drill_mm=d['drill_mm'])
  return super().via(v,exactrow)
checker=ExactRetainedVia(b,rows);results=[]
for u,d in declared.items():
 v=exact[u];probe=pcbnew.PCB_TRACK(b);probe.SetNet(v.GetNet());probe.SetLayer(pcbnew.In3_Cu);probe.SetStart(v.GetPosition());probe.SetEnd(v.GetPosition()+pcbnew.VECTOR2I(10000,0));probe.SetWidth(pcbnew.FromMM(.2))
 checker.tracks.append(probe)
 try:
  review=checker.via(v,rows[d['net']]);row=dict(uuid=u,passed=True,proof=review)
 except ValueError as ex:row=dict(uuid=u,passed=False,reason=str(ex))
 finally:checker.tracks.pop()
 peers=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber()for p in b.GetConnectivity().GetConnectedItems(v)if isinstance(p,pcbnew.PAD)]
 row.update(net=d['net'],mm=d['position'],diameter_mm=d['diameter_mm'],drill_mm=d['drill_mm'],actual_Source_pads=sorted(peers));results.append(row)
write(O/'review.json',dict(input_sha256={str(p):sha(p)for p in[B,M,R,Path(__file__)]},board_sha256=sha(B),inspection_only=True,literal_existing_vias=declared,results=results,future_In3_probe_is_not_routed_copper=True,no_new_or_existing_copper_modified=True,original_Source_stitch_annulus_and_margin_checks_retained=True,manufacturing_ready=False))
print(json.dumps(dict(passes=[{k:v for k,v in r.items()if k!='proof'}for r in results if r['passed']],failures=[{k:v for k,v in r.items()if k not in['proof','actual_Source_pads']}for r in results if not r['passed']])),flush=True)
