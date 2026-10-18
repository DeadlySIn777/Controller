"""Native, unsuppressed geometry regression of the nine affected power ICs.

Run with KiCad Python. These small boards intentionally have no routing: their
uncapped unconnected counts are reported, never confused with a finished PCB.
No parent board or copper is modified.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).resolve().parent
OUT=REPORT/'native-pad-repair-r03'
STOCK=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
REFS=['U11001','U11003','U11005','U11007','U11008','U11009','U11010','U11011','U11012']

def build_and_check(label,source):
    dest=OUT/label;dest.mkdir(parents=True,exist_ok=True)
    model=json.loads((source/'design.json').read_text())
    board=pcbnew.BOARD();board.SetCopperLayerCount(6);netmap={};records={}
    for i,ref in enumerate(REFS):
        p=model['components'][ref];lib,name=p['footprint'].split(':')
        folder=source/(lib+'.pretty') if lib=='CNC_MB_Entry' else STOCK/(lib+'.pretty')
        fp=pcbnew.FootprintLoad(str(folder),name)
        if fp is None:raise ValueError('Native footprint load failed '+ref)
        fp.SetReference(ref);fp.SetValue(p['mpn']);board.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(15+20*(i%5)),pcbnew.FromMM(15+25*(i//5))))
        for pad in fp.Pads():
            if not pad.GetNumber():continue
            n=p['pins'][pad.GetNumber()] or 'NC_'+ref+'_'+pad.GetNumber()
            if n not in netmap:
                ni=pcbnew.NETINFO_ITEM(board,n,len(netmap)+1);board.Add(ni);netmap[n]=ni
            pad.SetNet(netmap[n])
        records[ref]={'mpn':p['mpn'],'footprint':p['footprint'],'footprint_sha256':hashlib.sha256((folder/(name+'.kicad_mod')).read_bytes()).hexdigest()}
    for a,b in [((0,0),(115,0)),((115,0),(115,60)),((115,60),(0,60)),((0,60),(0,0))]:
        line=pcbnew.PCB_SHAPE(board);line.SetShape(pcbnew.SHAPE_T_SEGMENT);line.SetLayer(pcbnew.Edge_Cuts)
        line.SetStart(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in a)));line.SetEnd(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in b)));line.SetWidth(pcbnew.FromMM(.05));board.Add(line)
    path=dest/'geometry.kicad_pcb';pcbnew.SaveBoard(str(path),board)
    pro=json.loads((ROOT/'reports/motherboard-pcb-integration-20260930/populated-r07-1585/motherboard-populated-candidate.kicad_pro').read_text())
    pro['meta']['filename']='geometry.kicad_pro'
    pro['board']['design_settings']['rules']['min_clearance']=.15
    for row in pro['net_settings']['classes']:row['clearance']=.15
    path.with_suffix('.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
    path.with_suffix('.kicad_dru').write_text('(version 1)\n# No clearance reductions or suppressions in this source geometry proof.\n')
    command=[str(CLI),'pcb','drc','--format','json','--output',str(dest/'drc.json'),str(path)]
    result=subprocess.run(command,capture_output=True,text=True)
    (dest/'drc-command.txt').write_text(' '.join(command)+'\n'+result.stdout+'\n'+result.stderr)
    drc=json.loads((dest/'drc.json').read_text())
    return {'source_path':str(source.relative_to(ROOT)),'geometry_violations':drc['violations'],
            'geometry_violation_count':len(drc['violations']),'unconnected_items_count':len(drc['unconnected_items']),
            'ignored_checks':drc['ignored_checks'],'records':records,'native_returncode':result.returncode,
            'manufacturing_ready':False,'routing_intentionally_absent_on_this_geometry_fixture':True}

def main():
    old=build_and_check('prior-r02',REPORT/'prior-r02-before-native-pad-repair/hardware/motherboard_power_entry')
    new=build_and_check('corrected-r03',ROOT/'hardware/motherboard_power_entry')
    passed=old['geometry_violation_count']==9 and new['geometry_violation_count']==0 and not old['ignored_checks'] and not new['ignored_checks']
    receipt={'passed':passed,'prior_r02':old,'corrected_r03':new,'no_parent_board_or_copper_changed':True,
             'no_footprint_clearance_exceptions_added':True,'physical_assembly_or_wholeboard_routing_qualified':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'passed':passed,'prior_geometry_violations':old['geometry_violation_count'],'new_geometry_violations':new['geometry_violation_count'],'new_unconnected_geometry_fixture':new['unconnected_items_count']}))
    return not passed

if __name__=='__main__':raise SystemExit(main())
