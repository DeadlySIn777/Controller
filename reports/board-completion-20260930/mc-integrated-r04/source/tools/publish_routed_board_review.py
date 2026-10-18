"""Publish actual partial native copper while preserving historical revisions."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import pcbnew

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'hardware/board_review'
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def mm(x):return round(pcbnew.ToMM(x),6)
def pads(b):return {(f.GetReference(),p.GetNumber()):(p.GetNetname(),tuple(p.GetPosition()),tuple(p.GetSize())) for f in b.GetFootprints() for p in f.Pads()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',required=True);p.add_argument('--revision',required=True)
    p.add_argument('--label',default='MC actual partial copper; native DRC geometry check')
    p.add_argument('--placement-revision', help='Use a staged new-part inventory while preserving published history')
    p.add_argument('--routed',required=True,type=Path);p.add_argument('--power-bundle',type=Path)
    a=p.parse_args()
    if not all(re.fullmatch(r'[A-Za-z0-9_-]+',v) for v in (a.base,a.revision,a.placement_revision or a.base)):raise ValueError('Unsafe revision id')
    current=json.loads((REVIEW/'board-view.json').read_text(encoding='utf-8'))
    if current['current_revision']!=a.base:raise ValueError('Base revision is no longer latest')
    source=REVIEW/'revisions'/(a.placement_revision or a.base);folder=REVIEW/'revisions'/a.revision
    doc=json.loads((source/'board-view.json').read_text(encoding='utf-8'));spec=doc['boards'][0]
    base=REVIEW/spec['board_file'];base_board=pcbnew.LoadBoard(str(base))
    board=pcbnew.LoadBoard(str(a.routed.resolve()))
    if pads(base_board)!=pads(board):raise ValueError('Routed board changes source footprint/pads/nets')
    original_pad_map=pads(base_board);routed_before=len(board.GetTracks())
    if a.power_bundle:
        bundle=json.loads(a.power_bundle.read_text(encoding='utf-8'))
        if bundle['base_board_sha256']!=sha(base):raise ValueError('Power routes use different base placement')
        for conn in bundle['selected_connections']:
            for s in conn['segments']:
                net=board.FindNet(s['net'])
                if net is None:raise ValueError('Power route net absent: '+s['net'])
                t=pcbnew.PCB_TRACK(board);t.SetNet(net);t.SetLayer(pcbnew.F_Cu)
                t.SetStart(pcbnew.VECTOR2I(*[pcbnew.FromMM(v) for v in s['start_mm']]))
                t.SetEnd(pcbnew.VECTOR2I(*[pcbnew.FromMM(v) for v in s['end_mm']]))
                t.SetWidth(pcbnew.FromMM(s['width_mm']));board.Add(t)
    # Preserve all source-model/footprint files and native rule profile locally.
    shutil.copytree(source,folder)
    dest=folder/'motion-card-route-candidate.kicad_pcb'
    for item in board.Drawings():
        if isinstance(item,pcbnew.PCB_TEXT) and 'PLACEMENT STUDY' in item.GetText():
            item.SetText('PARTIAL ROUTING CANDIDATE - NOT FOR MANUFACTURE')
    pcbnew.SaveBoard(str(dest),board)
    pro=base.with_suffix('.kicad_pro')
    if pro.exists():dest.with_suffix('.kicad_pro').write_bytes(pro.read_bytes())
    reopened=pcbnew.LoadBoard(str(dest))
    if pads(reopened)!=original_pad_map:raise ValueError('Saved candidate changes fitted geometry/nets')
    drc=folder/'native-drc.json'
    result=subprocess.run([str(CLI),'pcb','drc','--format','json','-o',str(drc),str(dest)],capture_output=True,text=True)
    (folder/'native-drc.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise ValueError('Native DRC command failed')
    report=json.loads(drc.read_text(encoding='utf-8'))
    if report['violations']:raise ValueError('Routed candidate has DRC geometry/library violations; preserve for repair')
    tracks=[]
    for t in reopened.GetTracks():
        if isinstance(t,pcbnew.PCB_VIA):
            tracks.append({'kind':'via','net':t.GetNetname(),'x':mm(t.GetPosition().x),'y':mm(t.GetPosition().y),
                           'diameter_mm':mm(t.GetWidth(pcbnew.F_Cu)),'drill_mm':mm(t.GetDrillValue()),
                           'layer':reopened.GetLayerName(t.TopLayer())+'/'+reopened.GetLayerName(t.BottomLayer())})
        else:
            tracks.append({'kind':'segment','net':t.GetNetname(),'layer':reopened.GetLayerName(t.GetLayer()),
              'x1':mm(t.GetStart().x),'y1':mm(t.GetStart().y),'x2':mm(t.GetEnd().x),'y2':mm(t.GetEnd().y),'width_mm':mm(t.GetWidth())})
    render=subprocess.run([str(CLI),'pcb','render','--output',str(folder/'motion-card-3d.png'),
        '--width','1600','--height','900','--background','opaque','--rotate','-35,0,0','--zoom','1.5','--quality','basic',str(dest)],capture_output=True,text=True)
    (folder/'render.txt').write_text(render.stdout+render.stderr,encoding='utf-8')
    if render.returncode:raise ValueError('Native render failed; candidate not published')
    spec['tracks']=tracks;spec['stats']['routed_tracks']=len(tracks)
    spec['stats']['routed_segments']=sum(t['kind']=='segment' for t in tracks)
    spec['stats']['routed_vias']=sum(t['kind']=='via' for t in tracks)
    spec['stats']['reported_unconnected_items']=len(report['unconnected_items'])
    reopened.BuildConnectivity()
    unconnected=reopened.GetConnectivity().GetUnconnectedCount(False)
    spec['stats']['uncapped_unconnected_ratsnest_edges']=unconnected
    spec['stats']['native_unconnected_report_limit']=499
    spec['status']='Partially routed circuit candidate'
    spec['summary']=f'{len(spec["components"])} physical source parts with actual partial copper. Remaining card interfaces, GPIO, connectors, planes and full routing are unfinished.'
    relative='revisions/'+a.revision+'/'
    spec['board_file']=relative+dest.name;spec['image_3d']=relative+'motion-card-3d.png'
    spec['evidence'].update({'routing':True,'routing_scope':'Selected supervision, motor-local paths and ten converter paths; other nets remain partial/unrouted',
        'native_geometry_violations':0,'unconnected_items_remain':unconnected>0,'drc_pass':False,
        'physical_measurement':False,'manufacturing_ready':False})
    spec['routing_inputs']={'routed_native_board':str(a.routed),'sha256':sha(a.routed),
        'base_sha256':sha(base),'power_bundle':str(a.power_bundle) if a.power_bundle else None,
        'power_bundle_sha256':sha(a.power_bundle) if a.power_bundle else None,
        'input_native_track_items':routed_before,'additional_power_track_items':len(tracks)-routed_before,
        'placement_revision':a.placement_revision or a.base}
    doc.update({'current_revision':a.revision,'revision_label':a.label,
        'scope':'Source-backed partial motion-card layout. Manufacturing remains blocked.'})
    doc['revisions']=current['revisions']+[{'id':a.revision,'label':doc['revision_label'],'path':relative+'board-view.json'}]
    write(folder/'board-view.json',doc)
    receipt={'base_revision':a.base,'revision':a.revision,'native_pcb_sha256':sha(dest),
        'native_drc_sha256':sha(drc),'parts':len(spec['components']),'tracks':len(tracks),
        'fitted_pad_geometry_and_nets_preserved':True,'native_geometry_violations':0,
        'reported_unconnected_items':len(report['unconnected_items']),
        'uncapped_unconnected_ratsnest_edges':unconnected,'manufacturing_ready':False}
    write(folder/'publication.json',receipt)
    temporary=REVIEW/'board-view.next.json';write(temporary,doc);temporary.replace(REVIEW/'board-view.json')
    print(json.dumps(receipt))


if __name__=='__main__':main()
