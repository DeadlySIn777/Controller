"""Report-only exact ESP module/profile proposal screen; no PCB saves."""
import json
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT, sha, xy, rect, copper_hits, graphic_box, body_box, overlap, grown, transformed_box

board_path=ROOT/'reports/motherboard-pcb-integration-20260930/full-local-signal-route-r20/local-signal-routes-candidate.kicad_pcb'
out=ROOT/'reports/motherboard-mechanical-20260930/r20-rf-notch-r01'
if (out/'review.json').exists():
    raise SystemExit('Use new immutable report directory')
out.mkdir(parents=True,exist_ok=True)
before=sha(board_path)
b=p.LoadBoard(str(board_path))
fps={x.GetReference():x for x in b.GetFootprints()}
for ref,pose in {'J16001':(446,338.6,180),'J16002':(423.14,338.6,180),'J19528':(387,333,0)}.items():
    f=fps[ref]; f.SetOrientationDegrees(pose[2]);f.SetPosition(p.VECTOR2I(p.FromMM(pose[0]),p.FromMM(pose[1])))
notch=[424.8,338.8,444.3,340]
# Bounding rectangle includes rounded-corner material retained by the proposed
# 0.5 mm router profile, so zero-hit results are conservative for actual milling.
screens={name:copper_hits(b,grown(notch,margin)) for name,margin in [('removed_material',0),('native_p50_copper_edge_guard',.5)]}
antenna=transformed_box(fps['J16001'],[2.48,-7.85,20.48,-1.54])
body=transformed_box(fps['J16001'],[-1.27,-1.565,24.13,61.3])
component=[]
for f in fps.values():
    box=body_box(f)[0]
    if overlap(box,notch):component.append({'ref':f.GetReference(),'body_proxy':box})
rowpads={r:[{'pad':z.GetNumber(),'bbox_mm':rect(z.GetBoundingBox()),'drill_mm':xy(z.GetDrillSize())}for z in fps[r].Pads() if overlap(grown(notch,2),rect(z.GetBoundingBox()))]for r in ['J16001','J16002']}
courtyards={r:graphic_box(fps[r],p.F_CrtYd)for r in ['J16001','J16002']}
drills=[{'ref':f.GetReference(),'pad':z.GetNumber(),'center_mm':xy(z.GetPosition()),'drill_mm':xy(z.GetDrillSize())}for f in fps.values()for z in f.Pads()if z.GetDrillSize().x>0 and overlap(rect(z.GetBoundingBox()),grown(notch,.5))]
profile=[{'type':'line','start':[424.8,340],'end':[424.8,339.3]},
         {'type':'arc','start':[424.8,339.3],'mid':[424.946446609,338.946446609],'end':[425.3,338.8],'center':[425.3,339.3],'radius_mm':.5},
         {'type':'line','start':[425.3,338.8],'end':[443.8,338.8]},
         {'type':'arc','start':[443.8,338.8],'mid':[444.153553391,338.946446609],'end':[444.3,339.3],'center':[443.8,339.3],'radius_mm':.5},
         {'type':'line','start':[444.3,339.3],'end':[444.3,340]}]
report={'input_board':str(board_path),'input_sha256':before,'input_unchanged':sha(board_path)==before,
        'native_footprints':len(fps),'native_tracks_vias':len(list(b.GetTracks())),
        'read_only_RAM_moves':{'J16001':[446,338.6,180],'J16002':[423.14,338.6,180],'J19528':[387,333,0]},
        'notch_bounding_rectangle_mm':notch,'proposed_edge_profile':profile,
        'antenna_world_mm':antenna,'module_PCB_world_mm':body,
        'nominal_antenna_gap_to_notch_floor_mm':round(antenna[1]-338.8,6),
        'antenna_straight_floor_horizontal_margins_mm':[round(antenna[0]-425.3,6),round(443.8-antenna[2],6)],
        'all_enabled_copper_layer_screens':screens,'module_socket_courtyards_mm':courtyards,
        'nearest_socket_pads':rowpads,'removed_material_component_proxy_hits':component,'nearby_drills':drills,
        'mill_corner_radius_mm':.5,'native_copper_to_edge_rule_mm':.5,
        'primary_module_DXF':{'path':'reports/motherboard-esp-socket-20260930/espressif-s3-devkit-dimensions.dxf','sha256':sha(ROOT/'reports/motherboard-esp-socket-20260930/espressif-s3-devkit-dimensions.dxf')},
        'limitations':['The 0.5 mm expanded bounding rectangle is a conservative copper screen, not native DRC of an adopted outline.',
                       'Header plastics/courtyards may overhang; actual plated copper and drills must pass the unchanged 0.5 mm edge rule.',
                       'Manufacturer dimensional/assembly tolerances and PCBWay profile tolerance require actual fit qualification; nominal clearance is not a worst-case guarantee.',
                       '15 mm recommended final-housing RF clearance and actual range/throughput remain qualification gates; own module feed/header geometry is distinguished from extrinsic metal.',
                       'Final outline/native zone refill/DRC and module assembly must be checked after root adopts geometry; this tool never saves a candidate PCB.']}
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(out/'issued-tool.py').write_bytes(Path(__file__).read_bytes())
assert report['input_unchanged']
print(json.dumps({'copper_screens':{k:v['counts']for k,v in screens.items()},'component_hits':component,'near_drills':drills,'antenna':antenna,'nominal_floor_gap':report['nominal_antenna_gap_to_notch_floor_mm']}))
