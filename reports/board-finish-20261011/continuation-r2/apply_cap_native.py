"""Native C11068 flip/pose attestation; emit only that footprint's native chunk.

An isolated full temporary serialization provides the native chunk. No original
source/project/settings file is saved, no zones are refilled and no DRC is run.
"""
import datetime,hashlib,importlib.util,json,sys
from pathlib import Path
import pcbnew
HERE=Path(__file__).resolve().parent;OUT=HERE/'cap-native-r1';SOURCE=OUT/'project/board.kicad_pcb'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def chain(ch):return [[int(ch.CPoint(i).x)/1e6,int(ch.CPoint(i).y)/1e6] for i in range(ch.PointCount())]
def polygons(ps):return [[chain(ps.COutline(i))]+[chain(ps.CHole(i,j)) for j in range(ps.HoleCount(i))] for i in range(ps.OutlineCount())]
def main():
    inputs=json.loads((OUT/'inputs.json').read_bytes())
    for p,h in inputs['files'].items():
        if sha(p)!=h:raise ValueError('Frozen input changed '+p)
    recipe=json.loads((HERE/'coupled-recovery/aux-cap-bside-r3.json').read_bytes())['proposal'];manager=pcbnew.GetSettingsManager();project_path=SOURCE.with_suffix('.kicad_pro')
    if not manager.LoadProject(str(project_path)):raise ValueError('Frozen project load failed')
    project=manager.GetProject(str(project_path));board=None
    try:
        board=pcbnew.LoadBoard(str(SOURCE));board.SetProject(project);fp=board.FindFootprintByReference('C11068')
        if fp is None or fp.m_Uuid.AsString()!=recipe['footprint_uuid'] or fp.GetValue()!=recipe['value'] or fp.GetLayer()!=pcbnew.F_Cu:raise ValueError('Owned native footprint identity differs')
        prior={str(p.m_Uuid.AsString()):{'num':str(p.GetNumber()),'net':str(p.GetNetname()).replace('{slash}','/'),'size_nm':[p.GetSize().x,p.GetSize().y],'shape':int(p.GetShape()),'attr':int(p.GetAttribute()),'drill_nm':[p.GetDrillSize().x,p.GetDrillSize().y],'rr':p.GetRoundRectRadiusRatio()} for p in fp.Pads()}
        oldpos=fp.GetPosition();fp.Flip(oldpos,False);xy=recipe['target_pose']['xy_mm'];fp.SetPosition(pcbnew.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6)));fp.SetOrientationDegrees(recipe['target_pose']['angle_degrees'])
        expected={p['uuid']:p for p in recipe['expected_pads']};rows=[]
        for p in fp.Pads():
            uid=str(p.m_Uuid.AsString());before=prior[uid];position=p.GetPosition();at=[int(position.x)/1e6,int(position.y)/1e6];observed={'num':str(p.GetNumber()),'net':str(p.GetNetname()).replace('{slash}','/'),'size_nm':[p.GetSize().x,p.GetSize().y],'shape':int(p.GetShape()),'attr':int(p.GetAttribute()),'drill_nm':[p.GetDrillSize().x,p.GetDrillSize().y],'rr':p.GetRoundRectRadiusRatio()}
            if observed!=before or at!=expected[uid]['at_mm'] or p.GetLayer()!=pcbnew.B_Cu:raise ValueError('Native transformed pad differs '+uid+' '+repr(at))
            ps=pcbnew.SHAPE_POLY_SET();p.TransformShapeToPolygon(ps,pcbnew.B_Cu,0,pcbnew.FromMM(.005),pcbnew.ERROR_INSIDE);rows.append({'uuid':uid,**observed,'at_mm':at,'actual_layer':'B.Cu','polygon_rings':polygons(ps)})
        if {r['uuid'] for r in rows}!=set(expected):raise ValueError('Pad set changed')
        temp=OUT/'native-temporary.kicad_pcb';pcbnew.SaveBoard(str(temp),board)
        tool=Path('Z:/pcb-runs/claude-finish/tools/integrate/pcbtext.py');spec=importlib.util.spec_from_file_location('frozen_cap_pcbtext',tool);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);head,chunks,tail=module.split(temp.read_bytes());owned=[c for c in chunks if module.chunk_kind(c)=='footprint' and module.chunk_uuid(c)==recipe['footprint_uuid']]
        if len(owned)!=1:raise ValueError('Native owned footprint serialization unavailable')
        chunk_path=OUT/'C11068-native-flipped.chunk';chunk_path.write_bytes(owned[0])
        for p,h in inputs['files'].items():
            if sha(p)!=h:raise ValueError('Frozen input changed '+p)
        write(OUT/'native-attestation.json',{'verdict':'NATIVE_FLIP_POSE_PAD_ATTESTATION_PASS','finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_files':inputs['files'],'owned_footprint_uuid':recipe['footprint_uuid'],'actual_reference':fp.GetReference(),'actual_value':fp.GetValue(),'actual_layer':str(board.GetLayerName(fp.GetLayer())),'actual_angle_degrees':fp.GetOrientationDegrees(),'actual_centre_mm':xy,'pads':rows,'output_chunk':str(chunk_path),'output_chunk_sha256':sha(chunk_path),'temporary_serialization_sha256':sha(temp),'source_board_saved':False,'settings_saved':False,'zone_refill':False,'drc':False,'adopted':False})
        print('Native C11068 flip and exact physical pad attestation PASS',flush=True)
    finally:
        if board is not None:board.ClearProject()
        manager.UnloadProject(project,False)
if __name__=='__main__':main()
