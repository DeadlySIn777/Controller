"""Bound PG fine pitch neck and route the rest at effective .20 minimum."""
import json,hashlib,math
from shapely.geometry import Point,LineString
from shapely.ops import nearest_points
import joint_model_r2 as J
import continuous_path_r2 as CP
L=J.L;p=J.p;R=J.R;C=J.C
def main():
    g,h,_=J.model();pg=json.loads((L.OUT/'PG-pullup-local-move-r3.json').read_text());net='/motherboard_power_entry/SBC_SWITCH_PG';pad=C.pad(h,'U11012','7');source=(pad['x'],pad['y']);pad=C.pad(h,'R11049','2');end=(pad['x'],pad['y']);window=__import__('shapely').geometry.box(108,156,124,172);p.WINDOW=window
    free=R.free_layer(h,net,'F.Cu',window,('/LOGIC_GND','/IO_3V3',L.stage.caps.CORE,p.NET),reference_guard=None,allow_own_via_connection=True)
    narrow=next(q for q in p.hubs.components(free.buffer(-.0625)) if q.covers(Point(source)));wide=next(q for q in p.hubs.components(free.buffer(-.1)) if q.covers(Point(end)));landing=narrow.intersection(wide.buffer(-.025));join=nearest_points(Point(source),landing)[1].coords[0];fine=CP.path(narrow,source,join);bulk=CP.path(wide,join,end)
    assert fine['verdict']==bulk['verdict']=='HOST_PATH';assert fine['length_mm']<=1.2
    tracks=[]
    for label,w,r in [('neck',.125,fine),('bulk',.2,bulk)]:tracks += [C.track('PG-r4-'+label+'-'+str(i),net,'F.Cu',[round(x,6) for x in a],[round(x,6) for x in b],w) for i,(a,b) in enumerate(zip(r['points'],r['points'][1:])) if math.dist(a,b)>1e-8]
    area=LineString([[round(x,6) for x in q] for q in fine['points']]).buffer(.09);file=L.OUT/'U11012_LITERAL_PG_NECK-r4.wkb';file.write_bytes(area.wkb)
    dru=L.live.COMBINED.with_suffix('.kicad_dru');existing=dru.read_text();assert 'U11012' not in existing
    rule='(rule "U11012 exact PG fine-pitch neck only" (layer "F.Cu")\n (condition "A.Type == \'Track\' && A.Width < 0.20mm && A.NetName == \'/motherboard_power_entry/SBC_SWITCH_PG\' && A.enclosedByArea(\'U11012_LITERAL_PG_NECK\')")\n (constraint track_width (min 0.125mm) (max 0.125mm))\n (constraint track_segment_length (max 1.2mm)))\n'
    (L.OUT/'PG-exact-neck-rule-proposal-r4.kicad_dru').write_text(rule)
    result={'exact_board':L.live.SHA,'effective_existing_general_minimum_mm':.2,'existing_exact_U11012_neck_rule':False,'new_tracks':tracks,'superseded_PG_track_uuids':[q['uuid'] for q in pg['new_tracks'] if p.norm(q['net'])==net],'fine_neck_length_mm':fine['length_mm'],'fine_neck_route':fine,'bulk_width_mm':.2,'bulk_route':bulk,'named_area':{'name':'U11012_LITERAL_PG_NECK','file':str(file.resolve()),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'bounds':area.bounds,'area_mm2':area.area},'native_rule_text_proposal':rule,'existing_dru_sha256':hashlib.sha256(dru.read_bytes()).hexdigest(),'native_rule_acceptance_effective_constraint_and_full_DRU_DRC_gates_open':True,'native_jobs':0,'board_written':False}
    (L.OUT/'PG-exact-neck-r4.json').write_text(json.dumps(result,indent=2)+'\n');print('PG_NECK',fine['length_mm'],bulk['length_mm'],len(tracks),flush=True)
if __name__=='__main__':main()
