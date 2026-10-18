"""Transfer existing native copper into a larger source-backed MC candidate.

Only explicitly reviewed sheet-to-public motor/OE renames are permitted. Every
old pad retains its physical geometry and every old track/via retains geometry.
Run with KiCad Python. No release/fabrication output is produced.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import pcbnew


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pad_map(board):
    return {(f.GetReference(),p.GetNumber()):
        {'net':p.GetNetname(),'position':tuple(p.GetPosition()),'size':tuple(p.GetSize()),
         'orientation':p.GetOrientationDegrees(),'layers':p.GetLayerSet().FmtBin(),
         'shape':p.GetShape(),'attribute':p.GetAttribute()}
        for f in board.GetFootprints() for p in f.Pads()}
def trace(t):
    return {'kind':'via' if isinstance(t,pcbnew.PCB_VIA) else 'segment','net':t.GetNetname(),
        'start':tuple(t.GetStart()),'end':tuple(t.GetEnd()),'layer':t.GetLayer(),
        'width':t.GetWidth(pcbnew.F_Cu) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth(),
        'drill':t.GetDrillValue() if isinstance(t,pcbnew.PCB_VIA) else None,
        'top':t.TopLayer() if isinstance(t,pcbnew.PCB_VIA) else None,
        'bottom':t.BottomLayer() if isinstance(t,pcbnew.PCB_VIA) else None}
def approved_rename(old,new):
    if old==new:return True
    if re.fullmatch(r'/fpga_core/(STEP|DIR)\d+_FPGA',old):return new=='/'+old.split('/')[-1]
    match=re.fullmatch(r'/fpga_core/DRIVE_ENABLE(\d+)_FPGA_RESERVED',old)
    if match:return new==f'/EN{match[1]}_N_FPGA'
    return old=='/mc_permission/BANK_B_BUFFER_ENABLE_QUALIFIED' and new=='/BANK_B_BUFFER_ENABLE_QUALIFIED'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path);parser.add_argument('--staged',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);a=parser.parse_args()
    a.source=a.source.resolve();a.staged=a.staged.resolve();a.output=a.output.resolve()
    if a.output.exists():raise ValueError('Output is immutable; choose a new candidate')
    hashes={str(p):sha(p) for p in (a.source,a.staged)}
    old=pcbnew.LoadBoard(str(a.source));board=pcbnew.LoadBoard(str(a.staged))
    # A staged source board may already contain independently checked local
    # motor routes; retain those items as well as the earlier circuit copper.
    target_tracks=[trace(t) for t in board.GetTracks()]
    source_pads=pad_map(old);target_pads=pad_map(board);net_map={}
    for key,source in source_pads.items():
        target=target_pads.get(key)
        if target is None:raise ValueError('Retained pad absent: '+repr(key))
        if any(target[k]!=v for k,v in source.items() if k!='net'):raise ValueError('Retained pad moved/changed: '+repr(key))
        if not approved_rename(source['net'],target['net']):raise ValueError('Unreviewed electrical rename: '+repr((key,source['net'],target['net'])))
        net_map.setdefault(source['net'],set()).add(target['net'])
    if any(len(v)!=1 for v in net_map.values()):raise ValueError('Source copper net was split')
    net_map={k:next(iter(v)) for k,v in net_map.items()}
    expected=list(target_tracks)
    for item in old.GetTracks():
        before=trace(item);destination=net_map[before['net']]
        net=board.FindNet(destination)
        if net is None:raise ValueError('Target copper net missing: '+destination)
        duplicate=item.Duplicate();board.Add(duplicate);duplicate.SetNet(net)
        wanted={**before,'net':destination}
        if trace(duplicate)!=wanted:raise ValueError('Copper transfer changed geometry')
        expected.append(wanted)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    pcbnew.SaveBoard(str(a.output),board)
    a.output.with_suffix('.kicad_pro').write_bytes(a.staged.with_suffix('.kicad_pro').read_bytes())
    for path in a.staged.parent.glob('*.pretty'):
        shutil.copytree(path,a.output.parent/path.name,dirs_exist_ok=True)
    for name in ('fp-lib-table','3dmodels'):
        path=a.staged.parent/name
        if path.is_dir():shutil.copytree(path,a.output.parent/name,dirs_exist_ok=True)
        elif path.is_file():shutil.copyfile(path,a.output.parent/name)
    reloaded=pcbnew.LoadBoard(str(a.output))
    if pad_map(reloaded)!=target_pads:raise ValueError('Saved candidate changed pad inventory')
    sort=lambda values:sorted(json.dumps(v,sort_keys=True) for v in values)
    if sort(trace(t) for t in reloaded.GetTracks())!=sort(expected):raise ValueError('Saved copper inventory changed')
    reloaded.BuildConnectivity()
    if any(sha(Path(p))!=h for p,h in hashes.items()):raise ValueError('Input changed during transfer')
    receipt={'source_sha256':hashes,'output_sha256':sha(a.output),'existing_pads_preserved':len(source_pads),
        'new_source_pads':len(target_pads)-len(source_pads),'source_copper_items_preserved':len(old.GetTracks()),
        'staged_copper_items_preserved':len(target_tracks),'total_copper_items':len(expected),
        'net_renames':{k:v for k,v in net_map.items() if k!=v},
        'uncapped_unconnected_ratsnest_edges':reloaded.GetConnectivity().GetUnconnectedCount(False),
        'geometry_preserved':True,'manufacturing_ready':False,'physical_qualification':False}
    a.output.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
