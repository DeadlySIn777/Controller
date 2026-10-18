"""Read actual retained PCB against the frozen current physical source.

This produces a review inventory, never approves or applies its own changes.
Run with KiCad Python; full pad pieces are counted, not collapsed by pin name.
"""
import argparse, collections, json
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import native_parts_and_nets, footprint_name, sha

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',required=True,type=Path)
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Review must use a fresh output')
    model=json.loads((a.source/'design.json').read_text());parts=model['components']
    _,nodes=native_parts_and_nets(a.source/'netlist.xml',parts)
    b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity()
    tracks=collections.Counter(str(t.GetNetname()) for t in b.GetTracks())
    zones=collections.Counter(str(z.GetNetname()) for z in b.Zones())
    retained={f.GetReference():f for f in b.GetFootprints()}
    changes={};replacements=[];missing=[]
    for ref,fp in retained.items():
        if ref not in parts:missing.append(ref);continue
        target=parts[ref]
        if footprint_name(fp)!=target['footprint']:
            replacements.append(dict(reference=ref,old_footprint=footprint_name(fp),new_footprint=target['footprint'],
                position_mm=[pcbnew.ToMM(v) for v in fp.GetPosition()],rotation=fp.GetOrientationDegrees(),
                reason='Manufacturer-reviewed bounded source footprint correction; not approved by this review'))
        for pad in fp.Pads():
            if not pad.GetNumber() or not pad.IsOnCopperLayer():continue
            key=(ref,pad.GetNumber());before=str(pad.GetNetname());after=nodes.get(key)
            if before==after:continue
            row=changes.setdefault(key,dict(reference=ref,pin=key[1],old_native_net=before,new_native_net=after,
                old_net_copper_items=tracks[before],old_net_zones=zones[before],physical_pad_pieces=0))
            row['physical_pad_pieces']+=1
    result=dict(base_sha256=sha(a.board),source_design_sha256=sha(a.source/'design.json'),
        source_netlist_sha256=sha(a.source/'netlist.xml'),physical_parts=len(parts),retained_parts=len(retained),
        added_references=sorted(set(parts)-set(retained)),removed_references=missing,
        footprint_replacements=replacements,changes=list(changes.values()),
        approved=False,manufacturing_ready=False)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(retained=len(retained),added=len(result['added_references']),removed=missing,
        footprint_replacements=replacements,changed_native_pins=len(changes),
        changed_nets_with_copper=[r for r in changes.values() if r['old_net_copper_items'] or r['old_net_zones']])))
if __name__=='__main__':main()
