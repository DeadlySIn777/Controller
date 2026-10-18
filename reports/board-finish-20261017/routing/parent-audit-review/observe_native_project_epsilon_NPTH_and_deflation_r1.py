"""Bounded read-only actual project epsilon, cloned keepouts and NPTH probe.

No fill, board save, project save, source polygon or setting mutation occurs.
Only cloned rule outlines receive provider-identical Fracture/Deflate calls.
"""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import pcbnew,json,hashlib,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2'
SOURCE=OLD/'combined-R753-one-full-native-fill-cached-DRC-r299/filled-copy/board.kicad_pcb'
OUT=HERE/'actual-project-epsilon-NPTH-cloned-deflation-r1'
RAW=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763/actual-native-no-fill-area-closed-set-both-role-intersections.json'
OFFICIAL=HERE/'official-kicad-10.0.4-disallow-source-r2'
NATIVE_RULES=HERE/'read-only-native-R299-rule-areas-r2/exact-native-rule-areas.json'
TARGETS={'5a0230b2-991d-45c1-b5f0-31bd8f82bf7b','ac23de70-6546-466a-9b98-858c566d444e'}
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,r):(OUT/n).write_text(json.dumps(r,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def chain(c):return [[c.CPoint(i).x,c.CPoint(i).y]for i in range(c.PointCount())]
def rings(poly):return [{'outer_IU':chain(poly.COutline(i)),'holes_IU':[chain(poly.CHole(i,j))for j in range(poly.HoleCount(i))]}for i in range(poly.OutlineCount())]
def main():
    st=time.monotonic();assert not OUT.exists();OUT.mkdir()
    files=[SOURCE,SOURCE.with_suffix('.kicad_pro'),SOURCE.with_suffix('.kicad_dru')]
    if SOURCE.with_suffix('.kicad_prl').exists():files.append(SOURCE.with_suffix('.kicad_prl'))
    pins={str(f):sha(f)for f in(files+[Path(__file__),RAW,NATIVE_RULES,OFFICIAL/'receipt.json',OFFICIAL/'drc_test_provider_disallow.cpp',OFFICIAL/'board_design_settings.cpp',OFFICIAL/'base_units.h'])}
    assert pins[str(SOURCE)]=='6d7719335455a1941c28de1ebd750e862915d483049dd90226e054bd559e1632'
    manager=pcbnew.GetSettingsManager();projectfile=SOURCE.with_suffix('.kicad_pro')
    assert manager.LoadProject(str(projectfile));project=manager.GetProject(str(projectfile));assert project is not None
    b=pcbnew.LoadBoard(str(SOURCE));b.SetProject(project);settings=b.GetDesignSettings()
    epsilon=settings.GetDRCEpsilon();arc=pcbnew.FromMM(pcbnew.ARC_LOW_DEF_MM);version=pcbnew.GetBuildVersion()
    put('epsilon-observation.json',{'native_build_version':version,'project_file':str(projectfile),'native_board':str(SOURCE),'LoadProject_true':True,'SetProject_used':True,'GetDRCEpsilon_IU':epsilon,'GetDRCEpsilon_mm':epsilon/1e6,'ARC_LOW_DEF_MM':pcbnew.ARC_LOW_DEF_MM,'ARC_LOW_DEF_IU':arc,'corner_strategy':'CORNER_STRATEGY_ALLOW_ACUTE_CORNERS','no_settings_changed':True,'input_SHA256':pins})
    allzones=[(z,{'kind':'board'})for z in b.Zones()]
    for fp in b.GetFootprints():allzones.extend((z,{'kind':'footprint','UUID':fp.m_Uuid.AsString(),'ref':fp.GetReference()})for z in fp.Zones())
    zones={z.m_Uuid.AsString():z for z,owner in allzones};deflated={};rules=[]
    for z,owner in allzones:
        if not z.GetIsRuleArea()or not z.GetDoNotAllowZoneFills():continue
        original=rings(z.Outline());clone=z.Outline().CloneDropTriangulation();clone.Fracture();clone.Deflate(epsilon,pcbnew.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS,arc)
        uid=z.m_Uuid.AsString();deflated[uid]=clone;rules.append({'UUID':uid,'name':z.GetZoneName(),'owner':owner,'layers':[b.GetLayerName(l)for l in b.GetEnabledLayers().CuStack()if z.GetLayerSet().Contains(l)],'GetDoNotAllowZoneFills':True,'original_native_outlines':original,'provider_deflated_clone_outlines':rings(clone),'GetDRCEpsilon_IU':epsilon,'native_original_unchanged':rings(z.Outline())==original})
    put('actual-native-provider-deflated-no-fill-rule-clones.json',rules)
    raw=json.loads(RAW.read_bytes());checks=[]
    for index,row in enumerate(raw):
        if row['role']!='ACTUAL_CPP_FILL':continue
        area=zones[row['area_UUID']];zone=zones[row['zone_UUID']];assert area.GetIsRuleArea()and area.GetDoNotAllowZoneFills()
        layerrows=[]
        for name in row['layers']:
            layer=b.GetLayerID(name);assert area.GetLayerSet().Contains(layer)and zone.GetLayerSet().Contains(layer)
            filled=zone.GetFilledPolysList(layer);hit=bool(deflated[row['area_UUID']].Collide(filled,0))
            layerrows.append({'layer':name,'native_cached_filled_polygon_collision_with_provider_deflated_rule':hit})
        checks.append({'raw_index':index,'area_UUID':row['area_UUID'],'zone_UUID':row['zone_UUID'],'raw_role':row['role'],'raw_overlap':row['overlap'],'raw_witness_preserved':True,'actual_zone_IsFilled':bool(zone.IsFilled()),'provider_deflated_clone_native_Collide_checks':layerrows})
        if len(checks)%25==0:put('native-collision-progress.json',checks)
    put('all-actual-raw-pairs-native-provider-deflated-collision.json',checks)
    npth=[];target=[]
    for fp in b.GetFootprints():
        for p in fp.Pads():
            uid=p.m_Uuid.AsString()
            if p.GetAttribute()!=pcbnew.PAD_ATTRIB_NPTH and uid not in TARGETS:continue
            pos=p.GetPosition();drill=p.GetDrillSize();layerrows=[]
            for layer in b.GetEnabledLayers().CuStack():
                size=p.GetSize(layer);row={'layer':b.GetLayerName(layer),'IsOnLayer':bool(p.IsOnLayer(layer)),'CanFlashLayer':bool(p.CanFlashLayer(layer)),'FlashLayer':bool(p.FlashLayer(layer)),'pad_shape_enum':int(p.GetShape(layer)),'pad_size_IU':[size.x,size.y]}
                if uid in TARGETS:
                    poly=pcbnew.SHAPE_POLY_SET();p.TransformShapeToPolygon(poly,layer,0,pcbnew.FromMM(.005),pcbnew.ERROR_INSIDE);row['native_TransformShapeToPolygon_mechanical_or_Cu_proxy_IU']=rings(poly)
                layerrows.append(row)
            row={'UUID':uid,'ref':fp.GetReference(),'pin':p.GetNumber(),'raw_net':p.GetNetname(),'position_IU':[pos.x,pos.y],'GetAttribute_enum':int(p.GetAttribute()),'PAD_ATTRIB_NPTH_enum':int(pcbnew.PAD_ATTRIB_NPTH),'IsNPTHWithNoCopper':bool(p.IsNPTHWithNoCopper()),'drill_size_IU':[drill.x,drill.y],'drill_shape_enum':int(p.GetDrillShape()),'orientation_degrees':p.GetOrientationDegrees(),'layer_observations':layerrows}
            npth.append(row)
            if uid in TARGETS:target.append(row)
    assert {p['UUID']for p in target}==TARGETS
    put('all-actual-native-NPTH-conductor-and-layer-observations.json',npth);put('two-exact-R767-empty-net-pad-native-observations.json',target)
    changed={str(f):{'before':pins[str(f)],'after':sha(f)}for f in files if sha(f)!=pins[str(f)]};assert not changed,changed
    hits=sum(c['native_cached_filled_polygon_collision_with_provider_deflated_rule']for r in checks for c in r['provider_deflated_clone_native_Collide_checks'])
    put('receipt.json',{'status':'ACTUAL_PROJECT_NATIVE_EPSILON_AND_CLONE_COLLISION_NPTH_READ_ONLY_OBSERVATIONS_BOUND','native_build_version':version,'release10_0_4_source_matches_build':version.startswith('10.0.4'),'GetDRCEpsilon_IU':epsilon,'actual_no_fill_clone_count':len(rules),'actual_raw_no_fill_pair_checks':len(checks),'native_provider_deflated_actual_fill_collisions':hits,'native_native_Collide_is_direct_polygon_query_not_entire_DRC_engine':True,'npth_pad_count':len(npth),'two_target_NPTHWithNoCopper':[{'UUID':p['UUID'],'IsNPTHWithNoCopper':p['IsNPTHWithNoCopper']}for p in target],'all_raw_witnesses_preserved':True,'physical_keepout_hole_washer_current_and_reference_scopes_not_waived':True,'clones_only_no_source_geometry_or_rules_changed':True,'native_Fill_calls':0,'native_SaveBoard_calls':0,'native_SaveProject_calls':0,'source_inputs_after_hashes_identical':True,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st})
    print('ACTUAL_NATIVE_EPSILON_NPTH_COMPLETE',epsilon,'native_collisions',hits,'npth',len(npth),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
