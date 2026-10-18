"""Add isolated ISO1212 substrate thermal copper to an exact native board.

Each manufacturer's SUB pin gets its own 2 by 2 mm backside island. The
substrates remain distinct from every circuit return and from one another.
Run using the installed KiCad Python; this is native layout work, not a
measurement or a PCB fabrication release.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import pcbnew

from hardware_build_assembly import parse,dump,children,child,value
from hardware_map_motherboard_domains import ROOT,sha,write
from hardware_route_selected_additive import immutable_objects,zone_definitions
from hardware_route_logic_return import identity
from hardware_zone_motherboard_returns import rectangle,add_zone

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')


def mm_point(x,y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))


def substrate_recipe(board,mapping):
    """Strictly match the fitted manufacturer's native SUB12/SUB13 lands."""
    refs={f.GetReference():f for f in board.GetFootprints()}
    pads=[p for p in mapping['pads'] if p['domain'].startswith('SUB:')]
    if len(pads)!=44 or len({p['net'] for p in pads})!=44:
        raise ValueError('Expected exactly44 distinct actual substrate pads')
    rows=[]
    for p in pads:
        f=refs[p['reference']]
        if f.GetValue()!='ISO1212DBQR' or f.GetLayer()!=pcbnew.F_Cu or abs(f.GetOrientationDegrees())>1e-8:
            raise ValueError('Unreviewed ISO1212 package, side or rotation '+p['reference'])
        if p['pin'] not in ['12','13'] or p['native_nc']:
            raise ValueError('SUB identity differs from exact fitted source')
        pad=[q for q in f.Pads() if q.GetNumber()==p['pin']]
        if len(pad)!=1 or pad[0].GetNetname()!=p['net']:
            raise ValueError('Native SUB pad differs from mapped source')
        side=1 if p['pin']=='12' else -1
        local=pad[0].GetFPRelativePosition();size=pad[0].GetSize()
        if tuple(local)!=(2700000,side*317500) or tuple(size)!=(1600000,410000):
            raise ValueError('Unreviewed actual SUB land geometry '+p['reference'])
        origin=f.GetPosition();x,y=pcbnew.ToMM(origin.x),pcbnew.ToMM(origin.y)
        rows.append(dict(reference=p['reference'],pin=p['pin'],net=p['net'],pad_uuid=p['uuid'],
            segment_points_mm=[[x+2.7,y+side*.3175],[x+1.55,y+side*.3175],[x+1.3,y+side*1.25]],
            via_mm=[x+1.3,y+side*1.25],
            zone_bounds_mm=[x+.6,y+( .5 if side>0 else -2.5),x+2.6,y+(2.5 if side>0 else -.5)]))
    return sorted(rows,key=lambda r:(r['reference'],r['pin']))


def apply_substrates(board,rows):
    added_copper=[];added_zones=[]
    for row in rows:
        net=board.FindNet(row['net'])
        if net.GetNetname()!=row['net']:raise ValueError('Exact substrate net missing')
        for a,b in zip(row['segment_points_mm'],row['segment_points_mm'][1:]):
            t=pcbnew.PCB_TRACK(board);t.SetLayer(pcbnew.F_Cu);t.SetNet(net)
            t.SetWidth(pcbnew.FromMM(.20));t.SetStart(mm_point(*a));t.SetEnd(mm_point(*b));board.Add(t)
            added_copper.append(t.m_Uuid.AsString())
        v=pcbnew.PCB_VIA(board);v.SetNet(net);v.SetPosition(mm_point(*row['via_mm']))
        v.SetWidth(pcbnew.FromMM(.6));v.SetDrill(pcbnew.FromMM(.3));v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);board.Add(v);added_copper.append(v.m_Uuid.AsString())
        z=add_zone(board,row['net'],rectangle(row['zone_bounds_mm']),pcbnew.B_Cu,35,
                   'FLOATING_SUB_'+row['reference']+'_'+row['pin'])
        z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(.15))
        row['zone_uuid']=z.m_Uuid.AsString();row['via_uuid']=v.m_Uuid.AsString()
        added_zones.append(row['zone_uuid'])
    return added_copper,added_zones


def check_substrates(board,rows):
    zones={z.m_Uuid.AsString():z for z in board.Zones()};tracks={t.m_Uuid.AsString():t for t in board.GetTracks()}
    pads={p.m_Uuid.AsString():p for f in board.GetFootprints() for p in f.Pads()}
    board.BuildConnectivity();cn=board.GetConnectivity();receipt=[];errors=[]
    for row in rows:
        z=zones[row['zone_uuid']];v=tracks[row['via_uuid']];p=pads[row['pad_uuid']]
        fill=z.GetFilledPolysList(pcbnew.B_Cu)
        attached=cn.GetConnectedItems(p)
        connected=any(t.m_Uuid.AsString()==row['via_uuid'] for t in attached)
        point=mm_point(*row['via_mm'])
        own_fill=fill.Contains(point)
        actual_area=fill.Area()/1e12
        # Full outline area is4 mm²; native min-thickness rounding can vary by
        # the integer polygon arc tolerance. Demand the actual minimum4 mm².
        ok=connected and own_fill and actual_area>=3.999 and fill.OutlineCount()==1
        item=dict(reference=row['reference'],pin=row['pin'],net=row['net'],
                  actual_filled_area_mm2=actual_area,filled_outlines=fill.OutlineCount(),
                  own_pad_to_via_connected=connected,own_via_in_filled_SUB_island=own_fill,
                  floating_distinct_source_net=True,passed=ok)
        receipt.append(item)
        if not ok:errors.append(item)
    return dict(passed=not errors,rows=receipt,errors=errors)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',type=Path,required=True);p.add_argument('--map',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    base=a.board.resolve();out=a.out.resolve();mapping=json.loads(a.map.read_text(encoding='utf-8'))
    if out.exists() or not out.is_relative_to(ROOT/'reports'):raise ValueError('New report directory required')
    if mapping['input_sha256'].get(str(base))!=sha(base):raise ValueError('Map does not match exact PCB')
    out.mkdir(parents=True);(out/'inputs').mkdir()
    for f in [base,a.map.resolve(),Path(__file__)]:shutil.copy2(f,out/'inputs'/f.name)
    candidate=out/'motherboard-floating-substrates-candidate.kicad_pcb'
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(base.with_suffix(suffix),candidate.with_suffix(suffix))
    for f in base.parent.iterdir():
        if f.is_dir() and (f.name.endswith('.pretty') or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
    if (base.parent/'fp-lib-table').exists():shutil.copy2(base.parent/'fp-lib-table',out/'fp-lib-table')
    before_tree=parse(base.read_text(encoding='utf-8'));before=immutable_objects(before_tree)
    board=pcbnew.LoadBoard(str(base));old={t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}
    oldzones={z.m_Uuid.AsString() for z in board.Zones()}
    rows=substrate_recipe(board,mapping);cu,zones=apply_substrates(board,rows)
    donor=out/'native-donor.kicad_pcb';pcbnew.SaveBoard(str(donor),board)
    donor_tree=parse(donor.read_text(encoding='utf-8'));tree=copy.deepcopy(before_tree)
    tree.extend(copy.deepcopy(n) for n in donor_tree[1:] if isinstance(n,list) and n and n[0] in ['segment','via','zone']
                and value(child(n,'uuid')[1]) in set(cu+zones))
    candidate.write_text(dump(tree)+'\n',encoding='utf-8');write(out/'substrate-rows.json',rows)
    cmd=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(candidate)]
    r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (out/'drc-command.txt').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8');write(out/'drc-command.json',cmd)
    fresh=pcbnew.LoadBoard(str(candidate));fresh.BuildConnectivity();actual={t.m_Uuid.AsString():identity(t) for t in fresh.GetTracks()}
    if any(actual.get(k)!=v for k,v in old.items()):raise ValueError('Old copper changed')
    after=immutable_objects(parse(candidate.read_text(encoding='utf-8')))
    if after[0]!=before[0] or after[2]!=before[2]:raise ValueError('Old pads or noncopper native object changed')
    if any(after[1].get(k)!=v for k,v in before[1].items()):raise ValueError('Old zone definition changed')
    validation=check_substrates(fresh,rows);write(out/'substrate-validation.json',validation)
    drc=json.loads((out/'drc.json').read_text(encoding='utf-8'))
    receipt=dict(board_sha256=sha(candidate),input_board_sha256=sha(base),map_sha256=sha(a.map),
        old_copper_and_pad_pieces_preserved=True,old_zone_definitions_preserved=True,
        native_DRC_regular=len(drc.get('violations',[])),native_DRC_ignored=drc.get('ignored_checks',[]),
        substrate_validation=validation['passed'],new_copper_UUIDs=cu,new_zone_UUIDs=zones,
        old_zone_count=len(oldzones),substrate_count=len(rows),uncapped_unconnected=fresh.GetConnectivity().GetUnconnectedCount(False),
        physical_qualification=False,manufacturing_ready=False)
    write(out/'receipt.json',receipt);print(json.dumps(receipt,indent=2));raise SystemExit(not validation['passed'] or bool(drc.get('violations')))


if __name__=='__main__':main()
