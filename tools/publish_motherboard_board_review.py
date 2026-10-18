"""Publish verified additive motherboard geometry without replacing prior CAD.

Run with KiCad Python. Requires a frozen population receipt and independently
checks all source pads and copper clusters. This never exports fabrication.
"""
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
KICAD=Path('C:/Program Files/KiCad/10.0/share/kicad')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def mm(v):return round(pcbnew.ToMM(v),6)

def run(args,log):
    result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
    log.write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise ValueError('Native command failed; see '+str(log))

def component(fp,c,folder):
    pads=[]
    for p in fp.Pads():
        if not p.GetNumber() or not p.IsOnCopperLayer():continue
        pos,size=p.GetPosition(),p.GetSize()
        shape={pcbnew.PAD_SHAPE_RECT:'rect',pcbnew.PAD_SHAPE_ROUNDRECT:'roundrect',
               pcbnew.PAD_SHAPE_CIRCLE:'circle',pcbnew.PAD_SHAPE_OVAL:'oval'}.get(p.GetShape(),'rect')
        pads.append(dict(number=p.GetNumber(),net=p.GetNetname(),x=mm(pos.x),y=mm(pos.y),
                         width=mm(size.x),height=mm(size.y),shape=shape,angle=p.GetOrientation().AsDegrees()))
    graphics=[]
    for item in fp.GraphicalItems():
        if not isinstance(item,pcbnew.PCB_SHAPE) or item.GetLayer() not in (pcbnew.F_Fab,pcbnew.F_CrtYd,pcbnew.F_SilkS):continue
        kind={pcbnew.SHAPE_T_SEGMENT:'line',pcbnew.SHAPE_T_RECT:'rect',pcbnew.SHAPE_T_CIRCLE:'circle'}.get(item.GetShape())
        if kind:
            p,q=item.GetStart(),item.GetEnd()
            graphics.append(dict(kind=kind,x1=mm(p.x),y1=mm(p.y),x2=mm(q.x),y2=mm(q.y),layer=fp.GetBoard().GetLayerName(item.GetLayer())))
    models=[]
    for model in fp.Models():
        p=Path(model.m_Filename.replace('${KICAD10_3DMODEL_DIR}',str(KICAD/'3dmodels')).replace('${KIPRJMOD}',str(folder)))
        models.append(dict(path=model.m_Filename,available=p.is_file()))
    b=fp.GetBoundingBox(False,False);pos=fp.GetPosition()
    fpid=fp.GetFPID()
    return dict(reference=fp.GetReference(),value=c['value'],mpn=c['mpn'],footprint=str(fpid.GetLibNickname())+':'+str(fpid.GetLibItemName()),
        x_mm=mm(pos.x),y_mm=mm(pos.y),rotation_deg=fp.GetOrientationDegrees(),placement_only_candidate=False,
        highlight=False,bbox=dict(x=mm(b.GetX()),y=mm(b.GetY()),width=mm(b.GetWidth()),height=mm(b.GetHeight())),
        pads=pads,graphics=graphics,models=models,source='Frozen motherboard native/source population receipt',
        source_block=c.get('source_block'),status='Actual source footprint; circuit and routing qualification incomplete',dnp=c.get('dnp',False))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--population',type=Path,required=True);p.add_argument('--revision',required=True)
    p.add_argument('--base',required=True);a=p.parse_args()
    if not all(re.fullmatch(r'[A-Za-z0-9_-]+',v) for v in (a.base,a.revision)):raise ValueError('Invalid revision')
    current=read(REVIEW/'board-view.json')
    if current['current_revision']!=a.base:raise ValueError('Latest revision changed')
    source=a.population.resolve();receipt=read(source/'report.json')
    boardfile=source/'motherboard-populated-candidate.kicad_pcb'
    if not receipt['population']['ok'] or not receipt['population']['source_inputs_unchanged']:raise ValueError('Population review failed')
    if receipt['candidate_board_sha256']!=sha(boardfile):raise ValueError('Reviewed board changed')
    if not receipt['watchdog_clear_source_check']['ok']:raise ValueError('Incorrect watchdog-clear command topology')
    snap=source/'source-inputs';model=read(snap/'motherboard-design.json')
    for name in ('design.json','netlist.xml','assembly-map.json'):
        target=snap/('motherboard-'+name)
        matches=[h for path,h in receipt['source_inputs_sha256'].items() if Path(path).parent.name=='motherboard' and Path(path).name==name]
        if len(matches)!=1 or sha(target)!=matches[0]:raise ValueError('Frozen source snapshot changed '+name)
    folder=REVIEW/'revisions'/a.revision
    if folder.exists():raise ValueError('Never replace a published or attempted revision')
    shutil.copytree(source,folder)
    dest=folder/boardfile.name
    run([str(CLI),'pcb','drc','--format','json','--output',str(folder/'publication-drc.json'),str(dest)],folder/'publication-drc.txt')
    drc=read(folder/'publication-drc.json')
    if drc['violations'] or drc.get('ignored_checks'):raise ValueError('Unresolved native geometry checks')
    inventory=folder/'publication-connectivity'
    run([__import__('sys').executable,str(ROOT/'tools/motion_card_routing_inventory.py'),'--board',str(dest),
         '--netlist',str(folder/'source-inputs/motherboard-netlist.xml'),'--source-design',str(folder/'source-inputs/motherboard-design.json'),
         '--out',str(inventory)],folder/'publication-connectivity.txt')
    connected=read(inventory/'review.json')
    board=pcbnew.LoadBoard(str(dest));board.BuildConnectivity()
    parts={f.GetReference():f for f in board.GetFootprints()}
    if set(parts)!=set(model['components']):raise ValueError('Exact source population mismatch')
    components=[component(f,model['components'][r],folder) for r,f in sorted(parts.items())]
    tracks=[]
    for t in board.GetTracks():
        if isinstance(t,pcbnew.PCB_VIA):
            tracks.append(dict(kind='via',net=t.GetNetname(),x=mm(t.GetPosition().x),y=mm(t.GetPosition().y),
                diameter_mm=mm(t.GetWidth(pcbnew.F_Cu)),drill_mm=mm(t.GetDrillValue()),layer=board.GetLayerName(t.TopLayer())+'/'+board.GetLayerName(t.BottomLayer())))
        else:
            tracks.append(dict(kind='segment',net=t.GetNetname(),layer=board.GetLayerName(t.GetLayer()),
                x1=mm(t.GetStart().x),y1=mm(t.GetStart().y),x2=mm(t.GetEnd().x),y2=mm(t.GetEnd().y),width_mm=mm(t.GetWidth())))
    image=folder/'motherboard-3d.png'
    run([str(CLI),'pcb','render','--output',str(image),'--width','1600','--height','1000','--background','opaque',
         '--rotate','-25,0,0','--zoom','1.0','--quality','basic',str(dest)],folder/'publication-render.txt')
    zones=[dict(net=z.GetNetname(),layer=board.GetLayerName(z.GetLayer()),filled=z.IsFilled(),
                filled_area_mm2=z.GetFilledArea()/1e12,local_clearance_mm=mm(z.GetLocalClearance())) for z in board.Zones()]
    reservations=[dict(x=r['rectangle_mm'][0],y=r['rectangle_mm'][1],width=r['rectangle_mm'][2],
        height=r['rectangle_mm'][3],label=r['name']+' — reservation only') for r in receipt['mechanical_reservations']]
    relative='revisions/'+a.revision+'/'
    missing=connected['uncapped_unconnected_ratsnest_edges']
    blocks={c.get('source_block') for c in model['components'].values()}
    module_scope=('Actual purchased-compute/ESP sockets and SD slot are fitted in CAD; SoMs, firmware, raw peripheral completion and mechanical/thermal/RF qualification remain open.'
        if {'motherboard_compute','motherboard_esp_socket'}<=blocks else 'Compute/ESP/storage sockets are not fitted; module boxes are reservations only.')
    unfinished=[label for block,label in (
        ('motherboard_power_entry','protected power entry'),('motherboard_io_control','I/O-control endpoints'),
        ('motherboard_operator','probe/pendant supplies'),('motherboard_process','process control'),
        ('motherboard_analog_output','analog outputs'),('motherboard_analog_input','analog inputs'),
        ('motherboard_comms','field communications'),('motherboard_status','status indicators'),
        ('motherboard_terminals','field terminals'),('motherboard_field_safety','field supply/permit frontends')) if block not in blocks]
    limitations=[f'{missing} independently counted missing copper joins; routing and full-board/field planes remain incomplete.',
        module_scope,
        'Required source still absent: '+', '.join(unfinished)+'.' if unfinished else 'Fitted circuits still require their declared electrical/firmware/physical validation.',
        'The enlarged outline, stackup, module mating and mechanical clearances are provisional; no manufacture approval.',
        'FPGA vendor fit, loaded timing, 20 ms fault response, electrical/EMC/thermal and prototype bring-up remain unqualified.']
    spec=dict(id='motion-card',title='One motherboard — actual integrated source',source_block='motherboard',
        summary=f'{len(parts)} physical source footprints ({model["assembly_fitted_parts"]} fitted), {len(tracks)} track/via items and {len(zones)} real filled planes. {missing} copper joins remain. '+module_scope,
        status='Partially routed circuit candidate',width_mm=receipt['dimensions_mm'][0],height_mm=receipt['dimensions_mm'][1],
        thickness_mm=receipt['thickness_mm'],copper_layers=receipt['layers'],outline_status='Provisional expanded outline; final mechanics unfinished',
        assembly_reference_layer='F.Fab',zones=reservations,components=components,tracks=tracks,copper_zones=zones,
        board_file=relative+dest.name,image_3d=relative+image.name,open_work=limitations,unresolved=[],
        mechanical_reservations=receipt['mechanical_reservations'],source_hashes=receipt['source_inputs_sha256'],
        footprint_hashes=receipt['exact_footprint_inputs_sha256'],stats=dict(footprints=len(parts),components=len(parts),source_footprint_assignments=len(parts),source_fitted_footprints=len(parts),placement_only_candidates=0,
            placement_only_assignments=0,assembly_fitted_parts=model['assembly_fitted_parts'],models_available=sum(any(m['available'] for m in c['models']) for c in components),
            available_3d_models=sum(any(m['available'] for m in c['models']) for c in components),fitted_pads=connected['fitted_pads'],represented_nets=len(board.GetNetsByName())-1,routed_tracks=len(tracks),
            routed_segments=sum(t['kind']=='segment' for t in tracks),routed_vias=sum(t['kind']=='via' for t in tracks),
            copper_zones=len(zones),filled_copper_zones=sum(z['filled'] for z in zones),reported_unconnected_items=len(drc['unconnected_items']),
            uncapped_unconnected_ratsnest_edges=missing,native_unconnected_report_limit=499),
        evidence=dict(source_backed=True,native_board=True,routing=True,native_geometry_violations=0,
            independent_source_population_and_connectivity=True,drc_pass=False,physical_measurement=False,manufacturing_ready=False))
    doc=dict(schema_version=1,current_revision=a.revision,revision_label=f'Integrated {len(parts)}-part motherboard; {missing} joins remain',
        scope='Actual source population on preserved copper; full controller and manufacturing package unfinished.',boards=[spec],
        revisions=current['revisions']+[dict(id=a.revision,label=f'Integrated {len(parts)}-part motherboard',path=relative+'board-view.json')])
    write(folder/'board-view.json',doc)
    publication=dict(revision=a.revision,native_pcb_sha256=sha(dest),source_population_verified=True,
        source_population=len(parts),native_regular_drc_violations=0,ignored_checks=drc.get('ignored_checks',[]),
        uncapped_missing_joins=missing,reported_unconnected_items=len(drc['unconnected_items']),manufacturing_ready=False)
    write(folder/'publication.json',publication)
    temp=REVIEW/'board-view.next.json';write(temp,doc);temp.replace(REVIEW/'board-view.json')
    print(json.dumps(publication))

if __name__=='__main__':main()
