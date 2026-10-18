"""Prepare only local motor-buffer signal routes for the offline router.

The unchanged native board retains all electrical nets. BGA-facing signals,
power, ground, BOE qualification and physical receiver connectors are excluded.
"""
import argparse
import json
from pathlib import Path
import pcbnew
import motion_card_selected_routes as routing
from hardware_build_assembly import parse,dump,child,children,value,q

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/board-completion-20260930/motor-local-routing'
routing.OUT=OUT


def prepare(path):
    OUT.mkdir(parents=True,exist_ok=True)
    board=pcbnew.LoadBoard(str(path))
    if board.GetTracks():raise ValueError('Use source placement for bounded motor-local routing')
    nets={}
    for fp in board.GetFootprints():
        for pad in fp.Pads():nets.setdefault(pad.GetNetname(),[]).append((fp.GetReference(),pad.GetNumber()))
    selected=sorted(n for n,pads in nets.items() if n.startswith('/mc_motor_buffers/') and len(pads)>=2
        and all(int(''.join(filter(str.isdigit,r)))//1000==5 for r,p in pads))
    if len(selected)!=64:raise ValueError('Expected38 raw-output and26 outgoing-default nets')
    raw=OUT/'motion-card-native.dsn'
    if not pcbnew.ExportSpecctraDSN(board,str(raw)):raise ValueError('Native DSN export failed')
    tree=parse(raw.read_text());network=child(tree,'network');classes=children(network,'class')
    via=next(child(child(c,'circuit'),'use_via') for c in classes if child(c,'circuit') is not None and child(child(c,'circuit'),'use_via') is not None)
    for item in classes:network.remove(item)
    all_names={value(n[1]) for n in children(network,'net')}
    if not set(selected)<=all_names:raise ValueError('Local motor net omitted by native export')
    for item in list(children(network,'net')):
        if value(item[1]) not in selected:network.remove(item)
    network.append(['class',q('Local_motor_signals')]+[q(n) for n in selected]+[
        ['circuit',via],['rule',['width','200'],['clearance','150']]])
    dest=OUT/'motion-card-selected.dsn';dest.write_text(dump(tree)+'\n')
    meta={'base_board':str(path),'base_sha256':routing.sha(path),'native_dsn_sha256':routing.sha(raw),
        'selected_dsn_sha256':routing.sha(dest),'selected_nets':selected,'selected_net_count':len(selected),
        'excluded_net_count':len(all_names-set(selected)),
        'scope':'64 local motor raw-output/default nets only; no BGA inputs, rails, qualifiedOE or completeMC approval',
        'rules':{'signal_width_mm':.2,'clearance_mm':.15,'routable_layers':['F.Cu','B.Cu']},
        'manufacturing_ready':False}
    (OUT/'prepare.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'selected_nets':len(selected),'dsn':str(dest)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',type=Path);group.add_argument('--import-session',type=Path)
    parser.add_argument('--out',type=Path,default=OUT);a=parser.parse_args()
    OUT=a.out.resolve();routing.OUT=OUT
    if a.prepare:prepare(a.prepare.resolve())
    else:routing.import_session(a.import_session.resolve())
