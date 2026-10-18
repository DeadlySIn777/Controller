"""Add reviewed conventional through-via LOGIC_GND escapes to the retained BGA.

The 0.8mm-pitch / 0.35mm NSMD land pattern is retained exactly. A 0.50mm
capture diameter / 0.20mm drill has a nominal 0.15mm annular ring. At the
interstitial location, pad/via nominal clearance is 0.140685mm. A narrowly
scoped 0.125mm pad-to-via rule is above PCBWay's published 0.10mm floor;
it is an actual dimensional constraint, not a DRC exclusion. Process,
drill compensation, tenting, stackup and assembly still require review.
No source changes, signal allocation changes or fabrication files occur.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import pcbnew
from hardware_route_logic_return import identity, pad_identity, distance, segment_distance, segment_hits_box, xy, mm

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
RULES='''(version 1)
# Nominal 0.8mm-pitch diagonal pad/via clearance = 0.140685mm.
# Only FPGA pad / conventional via pairs use this dimensional rule.
(rule "T20 conventional BGA pad-via clearance"
  (condition "(A.memberOfFootprint('U1001') && B.Type == 'Via') || (B.memberOfFootprint('U1001') && A.Type == 'Via')")
  (constraint clearance (min 0.125mm)))
(rule "BGA conventional via dimensions"
  (condition "A.Type == 'Via'")
  (constraint hole_size (min 0.20mm))
  (constraint annular_width (min 0.15mm)))
'''

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();source=a.board.resolve();out=a.out.resolve()
    if out.exists() or out.is_relative_to(ROOT/'hardware'):raise ValueError('Use a new immutable report directory')
    if source.with_suffix('.kicad_dru').exists():raise ValueError('Merge pre-existing design rules explicitly')
    inputs={str(s):sha(s) for s in (source,source.with_suffix('.kicad_pro'),ROOT/'hardware/motion_card/mechanical.json')}
    b=pcbnew.LoadBoard(str(source));b.BuildConnectivity()
    if b.GetCopperLayerCount()!=6 or len(b.Zones())!=1:raise ValueError('Expected retained six-layer board with one logic return fill')
    old={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    pads={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in b.GetPads()}
    u=next(f for f in b.GetFootprints() if f.GetReference()=='U1001')
    if len(u.Pads())!=256:raise ValueError('Exact T20F256 package required')
    net=b.FindNet('/LOGIC_GND');groups=[];mapping={};skips=[]
    foreign=[q for q in b.GetPads() if q.GetNetname()!='/LOGIC_GND']
    via_positions=[mm(t.GetPosition()) for t in b.GetTracks() if isinstance(t,pcbnew.PCB_VIA)]
    for q in u.Pads():
        if q.GetNetname()!='/LOGIC_GND':continue
        start=mm(q.GetPosition());end=None
        if abs(pcbnew.ToMM(q.GetSize().x)-.35)>1e-6:raise ValueError('Changed NSMD land')
        for dx,dy in ((-.4,-.4),(.4,-.4),(.4,.4),(-.4,.4)):
            e=(round(start[0]+dx,6),round(start[1]+dy,6))
            if any(math.dist(e,v)<.7 for v in via_positions):continue
            blocked=False
            for other in foreign:
                op=mm(other.GetPosition());size=other.GetSize()
                if other.GetParentFootprint().GetReference()=='U1001':
                    if math.dist(e,op)<.175+.25+.125-1e-6 or distance(op,start,e)<.175+.10+.15-1e-6:blocked=True;break
                else:
                    bb=other.GetBoundingBox();box=(pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))
                    if segment_hits_box(e,e,box,.401) or other.IsOnLayer(pcbnew.F_Cu) and segment_hits_box(start,e,box,.251):blocked=True;break
            if blocked:continue
            for t in b.GetTracks():
                if t.GetNetname()=='/LOGIC_GND':continue
                ta,tb=mm(t.GetStart()),mm(t.GetEnd());width=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth())
                if distance(e,ta,tb)<.401+width/2 or t.IsOnLayer(pcbnew.F_Cu) and segment_distance(start,e,ta,tb)<.251+width/2:blocked=True;break
            if not blocked:end=e;break
        key='U1001.'+q.GetNumber()
        if end is None:skips.append({'pad':key,'reason':'No clear conventional through-via candidate in retained geometry'});continue
        t=pcbnew.PCB_TRACK(b);t.SetNet(net);t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(start));t.SetEnd(xy(end));t.SetWidth(pcbnew.FromMM(.2));b.Add(t)
        v=pcbnew.PCB_VIA(b);v.SetNet(net);v.SetPosition(xy(end));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
        ids=[t.m_Uuid.AsString(),v.m_Uuid.AsString()];index=len(groups)
        groups.append({'pad':key,'start_mm':start,'via_mm':end,'ids':ids,'retained':True})
        mapping.update({i:index for i in ids});via_positions.append(end)
    out.mkdir(parents=True);dest=out/'bga-return-route-candidate.kicad_pcb'
    dest.with_suffix('.kicad_pro').write_bytes(source.with_suffix('.kicad_pro').read_bytes())
    dest.with_suffix('.kicad_dru').write_text(RULES,encoding='utf-8')
    for path in source.parent.glob('*.pretty'):shutil.copytree(path,out/path.name)
    for name in ('3dmodels','fp-lib-table'):
        path=source.parent/name
        if path.is_dir():shutil.copytree(path,out/name)
        elif path.is_file():shutil.copyfile(path,out/name)
    repairs=[]
    for attempt in range(10):
        pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(dest),b)
        report=out/f'drc-{attempt:02}.json'
        command=[str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(report),str(dest)]
        r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/f'drc-{attempt:02}.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
        if r.returncode:raise RuntimeError('Native DRC did not run successfully')
        data=json.loads(report.read_text(encoding='utf-8'))
        if data.get('ignored_checks'):raise ValueError('Ignored checks are not permitted')
        violations=data['violations']
        if not violations:break
        remove=set()
        for issue in violations:
            ids={item.get('uuid') for item in issue.get('items',[])}
            found={mapping[i] for i in ids if i in mapping}
            if not found:raise ValueError('Native violation affects retained geometry or dimensional rules: '+json.dumps(issue))
            remove.update(found)
        for idx in remove:
            group=groups[idx]
            for t in list(b.GetTracks()):
                if t.m_Uuid.AsString() in group['ids']:b.Remove(t)
            group['retained']=False;repairs.append({'pad':group['pad'],'native_drc_rejected':True})
    else:raise ValueError('Native DRC repair bound reached')
    reopened=pcbnew.LoadBoard(str(dest));reopened.BuildConnectivity()
    if pads!={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in reopened.GetPads()}:raise ValueError('Retained source pad geometry or nets changed')
    new={t.m_Uuid.AsString():identity(t) for t in reopened.GetTracks()}
    if any(new.get(i)!=value for i,value in old.items()):raise ValueError('Retained copper identity changed')
    if any(sha(Path(s))!=value for s,value in inputs.items()):raise ValueError('Input changed during routing')
    receipt={'source_hashes':inputs,'board_sha256':sha(dest),'rule_sha256':sha(dest.with_suffix('.kicad_dru')),
      'retained_copper_items':len(old),'total_track_via_items':len(new),'ground_bga_escape_groups':sum(g['retained'] for g in groups),
      'ground_bga_skipped':skips,'escape_groups':groups,'native_rejected_groups':repairs,
      'native_regular_drc_violations':len(data['violations']),'native_drc_ignored_checks':data.get('ignored_checks',[]),
      'capped_unconnected_items':len(data['unconnected_items']),'uncapped_unconnected_edges':reopened.GetConnectivity().GetUnconnectedCount(False),
      'dimensions_mm':{'pad':.35,'via':.5,'drill':.2,'nominal_annular_width':.15,'bga_pad_to_via_rule':.125,
                        'nearest_nominal_bga_pad_via_clearance':math.sqrt(.4*.4*2)-.175-.25},
      'retained_pad_net_geometry_and_copper_identity_unchanged':True,'manufacturing_ready':False,
      'sources':[{'url':'https://www.pcbway.com/capabilities.html','retrieved_date':'2026-09-30','basis':'0.10mm spacing floor; nominal 0.15mm annular ring; 0.20mm hole maximum thickness1.6mm / aspect8'},
                 {'path':'hardware/motion_card/mechanical.json','basis':'Efinix exact0.35mm NSMD land /0.8mm pitch retained; suggested0.4/0.25via is not PCBWay standard annular rule'}],
      'remaining':['Conventional drill compensation/tolerance, tenting, stackup and assembly qualification',
                   'Whole motherboard population/routing, power planes, all isolated field returns and interface circuits']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_hashes','escape_groups','sources')}))

if __name__=='__main__':main()
