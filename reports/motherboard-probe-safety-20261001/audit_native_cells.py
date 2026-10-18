"""Read-only exact eight ISO1212 cells; device-role spacing precedes routing."""
from pathlib import Path
import hashlib,json,sys
import pcbnew
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'native-layout-r32-r02'
OUT.mkdir(exist_ok=True)
BOARD=ROOT/'reports/motherboard-pcb-integration-20261001/shared-power-isow-merge-r32/motherboard-bounded-merged-candidate.kicad_pcb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=pcbnew.LoadBoard(str(BOARD));fps={f.GetReference():f for f in b.GetFootprints()}
def pads(ref,pin=None):return [p for p in fps[ref].Pads() if p.GetNumber() and (pin is None or p.GetNumber()==str(pin))]
def bounds(p):
    q=p.GetBoundingBox();return [pcbnew.ToMM(q.GetLeft()),pcbnew.ToMM(q.GetTop()),pcbnew.ToMM(q.GetRight()),pcbnew.ToMM(q.GetBottom())]
def gap(a,c):
    x=bounds(a);y=bounds(c);return (max(x[0]-y[2],y[0]-x[2],0)**2+max(x[1]-y[3],y[1]-x[3],0)**2)**.5
def nearest(ref,pin,targets):
    a=pads(ref,pin)[0];candidates=[(gap(a,p),r,p.GetNumber()) for r,ps in targets for p in pads(r) if ps is None or p.GetNumber() in ps]
    d,r,p=min(candidates);return dict(gap_mm=d,nearest_reference=r,nearest_pin=p)
rows=[]
channels=[('U14031','R14069','R14070',None,'PRB0',16,15),('U14031','R14072','R14073',None,'PRB1',11,10),
 ('U19001','R19001','R19002','C19001','EXT_PERMIT',16,15),('U19001','R19004','R19005','C19002','PROCESS_PERMIT',11,10),
 ('U19002','R19007','R19008','C19004','SAFETY_STATUS',16,15),('U19002','R19010','R19011','C19005','RESET_ARM',11,10),
 ('U19003','R19013','R19014','C19007','CONTACTOR_FB',16,15),('U19003','R19016','R19017','C19008','STO_FB',11,10)]
for u,rt,rs,ci,name,sense,inp in channels:
    protected=[(u,None),(rs,None)]+([(ci,None)] if ci else [])
    pos=fps[u].GetPosition();ext=pads(rt,'1')[0]
    expected=pads(u,sense)[0].GetNetname()
    rows.append(dict(channel=name,IC=u,IC_position_mm=[pcbnew.ToMM(pos.x),pcbnew.ToMM(pos.y)],
        IC_angle_deg=fps[u].GetOrientationDegrees(),RTHR=rt,RSENSE=rs,CIN=ci,
        RTHR_external_pad_to_nearest_protected=nearest(rt,'1',protected),
        RTHR_external_net=ext.GetNetname(),RTHR_internal_pad_net=pads(rt,'2')[0].GetNetname(),
        required_RTHR_internal_pad_net=expected,
        RTHR_source_net_correction_pending=rt in ('R14069','R14072'),
        SENSE_native_pin=str(sense),IN_native_pin=str(inp),
        field_GND=pads(u,'14' if sense==16 else '9')[0].GetNetname(),
        SUB_native_net=pads(u,'13' if sense==16 else '12')[0].GetNetname()))
bypass=[]
operator=json.loads((ROOT/'hardware/motherboard_operator/design.json').read_text())
probe_bypass=[r for r,c in operator['components'].items() if c.get('role')=='U14031 bypass']
assert probe_bypass==['C14058']
for u,cap in [('U14031',probe_bypass[0]),('U19001','C19003'),('U19002','C19006'),('U19003','C19009')]:
    a=pads(u,'2')[0];c=pads(cap,'1')[0]
    assert a.GetNetname()==c.GetNetname()=='/IO_3V3'
    dist=(a.GetPosition()-c.GetPosition()).EuclideanNorm()/1e6
    bypass.append(dict(IC=u,capacitor=cap,positive_terminal_to_VCC2_mm=dist,
        edge_gap_mm=gap(a,c),positive_net=c.GetNetname(),return_net=pads(cap,'2')[0].GetNetname(),
        manufacturer_2mm_geometry_pass=dist<=2))
review=dict(board=str(BOARD.relative_to(ROOT)),board_SHA256=sha(BOARD),
    source_scope='PCB still paired with source23 before the bounded two probe-pad source24 transaction.',
    field_channels=rows,logic_bypasses=bypass,
    external_RTHR_geometric_4mm_failures=[r['RTHR'] for r in rows if r['RTHR_external_pad_to_nearest_protected']['gap_mm']<4],
    logic_2mm_failures=[r['capacitor'] for r in bypass if not r['manufacturer_2mm_geometry_pass']],
    board_modified=False,manufacturing_ready=False,
    scope='Read-only actual native pad-edge and bypass-terminal inspection; routing,return continuity and physicalEMC are not proved.')
(OUT/'review.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps(dict(RTHR_spacing_failures=review['external_RTHR_geometric_4mm_failures'],
    logic_bypass_2mm_failures=review['logic_2mm_failures'],board_SHA256=review['board_SHA256'])))
