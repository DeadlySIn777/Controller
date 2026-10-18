"""Offline selected supervision routes; never autoroute BGA/power/connector nets."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import pcbnew
from hardware_build_assembly import parse, dump, child, children, value, q

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/board-completion-20260930/selected-routing'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(board_path):
    OUT.mkdir(parents=True,exist_ok=True)
    board=pcbnew.LoadBoard(str(board_path))
    by_net={}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname():by_net.setdefault(pad.GetNetname(),[]).append((fp.GetReference(),pad.GetNumber()))
    selected=[]
    for name,pads in by_net.items():
        if len(pads)<2 or name.startswith('unconnected-') or name in {'/IO_3V3','/LOGIC_GND'} or name.endswith('_CWD'):continue
        if all(int(''.join(filter(str.isdigit,ref)))//1000 in (3,4) for ref,pin in pads):selected.append(name)
    selected.sort()
    raw=OUT/'motion-card-native.dsn'
    if not pcbnew.ExportSpecctraDSN(board,str(raw)):raise ValueError('Native DSN export failed')
    tree=parse(raw.read_text(encoding='utf-8'))
    network=child(tree,'network')
    old_classes=children(network,'class')
    for item in old_classes:network.remove(item)
    all_names={value(n[1]) for n in children(network,'net')}
    if not set(selected)<=all_names:raise ValueError('Selected nets missing from native DSN')
    # Preserve native physical nets but isolate incomplete/high-current routes.
    rules=[['circuit',['use_via',q('Via[0-1]_600:300_um')]],
           ['rule',['width','200'],['clearance','150']]]
    # Use the native via-padstack name, never guess a fabricated drill geometry.
    old_via=next((child(child(c,'circuit'),'use_via') for c in old_classes if child(c,'circuit') is not None and child(child(c,'circuit'),'use_via') is not None),None)
    if old_via is not None:rules[0][1]=old_via
    # Remove omitted net declarations from this routing-only interchange copy.
    # Their pads remain physical obstacles; the original native PCB retains all
    # electrical assignments and import verifies them unchanged. This also
    # prevents any pre-pass from accidentally fanning out excluded BGA/power nets.
    for net in list(children(network,'net')):
        if value(net[1]) not in selected:network.remove(net)
    network.append(['class',q('Selected_supervision')]+[q(n) for n in selected]+rules)
    path=OUT/'motion-card-selected.dsn';path.write_text(dump(tree)+'\n',encoding='utf-8')
    meta={'base_board':str(board_path),'base_sha256':sha(board_path),'native_dsn_sha256':sha(raw),
          'selected_dsn_sha256':sha(path),'selected_nets':selected,'selected_net_count':len(selected),
          'excluded_net_count':len(all_names-set(selected)),
          'rules':{'signal_width_mm':.2,'clearance_mm':.15,'routable_layers':['F.Cu','B.Cu']},
          'scope':'Partial selected supervision routing; no BGA, clocks, power, field contacts or complete-card routing approval',
          'manufacturing_ready':False}
    (OUT/'prepare.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'selected_nets':len(selected),'excluded_nets':meta['excluded_net_count'],'dsn':str(path)}))


def import_session(session):
    info=json.loads((OUT/'prepare.json').read_text(encoding='utf-8'));base=Path(info['base_board'])
    if sha(base)!=info['base_sha256']:raise ValueError('Base PCB changed')
    board=pcbnew.LoadBoard(str(base));before={(f.GetReference(),p.GetNumber()):(p.GetNetname(),tuple(p.GetPosition())) for f in board.GetFootprints() for p in f.Pads()}
    poses={f.GetReference():(tuple(f.GetPosition()),f.GetOrientationDegrees()) for f in board.GetFootprints()}
    if not pcbnew.ImportSpecctraSES(board,str(session)):raise ValueError('SES import failed')
    selected=set(info['selected_nets'])
    if any(t.GetNetname() not in selected for t in board.GetTracks()):raise ValueError('Router changed excluded net')
    restored=[]
    for fp in board.GetFootprints():
        pos,angle=poses[fp.GetReference()];new=tuple(fp.GetPosition())
        if new==pos and fp.GetOrientationDegrees()==angle:continue
        # Native DSN/SES round-trip can quantize a float-created coordinate by1nm.
        # Restore only tiny shifts on wholly excluded footprints; reject actual
        # placement changes and any shifted selected route endpoints.
        if max(abs(a-b) for a,b in zip(pos,new))>100 or angle!=fp.GetOrientationDegrees() or any(p.GetNetname() in selected for p in fp.Pads()):
            raise ValueError('Router changed physical placement '+fp.GetReference())
        restored.append({'reference':fp.GetReference(),'delta_nm':[b-a for a,b in zip(pos,new)]})
        fp.SetPosition(pcbnew.VECTOR2I(*pos))
    after={(f.GetReference(),p.GetNumber()):(p.GetNetname(),tuple(p.GetPosition())) for f in board.GetFootprints() for p in f.Pads()}
    if before!=after:raise ValueError('Router changed physical pad placement/nets')
    dest=OUT/'motion-card-selected-routed.kicad_pcb';pcbnew.SaveBoard(str(dest),board)
    pro=base.with_suffix('.kicad_pro')
    if pro.exists():dest.with_suffix('.kicad_pro').write_bytes(pro.read_bytes())
    report={**info,'routed_board':str(dest),'routed_board_sha256':sha(dest),'ses_sha256':sha(session),
            'track_items':len(board.GetTracks()),'fitted_pad_geometry_and_nets_preserved':True,
            'excluded_nets_unchanged':True,'excluded_coordinate_quantization_restored':restored,
            'drc_pass':False,'physical_measurement':False}
    (OUT/'import.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'track_items':report['track_items'],'board':str(dest),'pad_geometry_preserved':True}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',type=Path);g.add_argument('--import-session',type=Path);a=p.parse_args()
    if a.prepare:prepare(a.prepare.resolve())
    else:import_session(a.import_session.resolve())
