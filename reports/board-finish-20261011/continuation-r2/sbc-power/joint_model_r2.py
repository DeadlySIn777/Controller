"""Complete local controls/support/added bulk, quantized to native nanometres."""
import copy,json
from shapely import set_precision
from shapely.affinity import translate
import local_copper_r3 as T
import pg_pullup_move_r2 as PG
L=T.L;p=T.p;R=T.R;V=T.V;C=T.T
def records(sh):return [[list(q.exterior.coords),[list(x.coords) for x in q.interiors]] for q in p.hubs.components(sh)]
def model(include_pg_dive=True):
    g,h,tail=T.model();en=json.loads((L.OUT/'switch-control-coplan-r5.json').read_text());pg=json.loads((L.OUT/'PG-pullup-local-move-r3.json').read_text());assert pg['verdict']=='HOST_COMPLETE_PG_PULLUP_MOVE'
    h=PG.move(h,pg['R11049_target_pose'][:2],pg['R11049_target_pose'][2]);h={**h,'tracks':h['tracks']+en['new_tracks']+pg['new_tracks'],'vias':h['vias']+en['new_vias']+pg['new_vias']}
    if include_pg_dive:
        dive=json.loads((L.OUT/'PG-local-dive-r5.json').read_text());h={**h,'tracks':[t for t in h['tracks'] if p.norm(t['net'])!='/motherboard_power_entry/SBC_SWITCH_PG']+dive['new_tracks'],'vias':h['vias']+dive['new_vias']}
    frozen=json.loads((L.OUT/'source-native-frozen-r2/receipt.json').read_text())['new_C11094'];uu=frozen['private_uuid_ledger'];dx,dy=27.875,-5.15
    cap=[]
    for old in g['pads']:
        if old['ref']!='C11088':continue
        q=copy.deepcopy(old);q['ref']='C11094';q['uuid']=uu[old['uuid']];q['x']+=dx;q['y']+=dy;q['layers']={lay:[row for sh in p.base.polygons(rs) for row in records(translate(sh,dx,dy))] for lay,rs in q['layers'].items()};cap.append(q)
    f=copy.deepcopy(next(x for x in g['footprints'] if x['ref']=='C11088'));f.update(ref='C11094',x=249.5,y=102);f['courtyard']={lay:[row for sh in p.base.polygons(rs) for row in records(translate(sh,dx,dy))] for lay,rs in f['courtyard'].items()}
    h['pads']=h['pads']+cap;h['footprints']=h['footprints']+[f]
    oldtracks={x['uuid'] for x in g['tracks']};oldvias={x['uuid'] for x in g['vias']}
    h['tracks']=[{**x,'a':[round(q,6) for q in x['a']],'b':[round(q,6) for q in x['b']],'w':round(x['w'],6)} if x['uuid'] not in oldtracks else x for x in h['tracks']]
    h['vias']=[{**x,'x':round(x['x'],6),'y':round(x['y'],6),'d':round(x['d'],6),'drill':round(x['drill'],6)} if x['uuid'] not in oldvias else x for x in h['vias']]
    changed={'U11012','C11061','C11062','C11063','C15001','C15002','R11049','C11094'}
    for i,q in enumerate(h['pads']):
        if q['ref'] not in changed:continue
        q=copy.deepcopy(q);q['x']=round(q['x'],6);q['y']=round(q['y'],6);q['layers']={lay:[row for sh in p.base.polygons(rs) for row in records(set_precision(sh,1e-6))] for lay,rs in q['layers'].items()};h['pads'][i]=q
    return g,h,tail
if __name__=='__main__':
    g,h,tail=model();oldv={x['uuid'] for x in g['vias']};oldt={x['uuid'] for x in g['tracks']};r={'exact_board':L.live.SHA,'native_coordinate_grid_nm':1,'new_vias':[x for x in h['vias'] if x['uuid'] not in oldv],'new_tracks':[x for x in h['tracks'] if x['uuid'] not in oldt],'moved_R11049_pose':json.loads((L.OUT/'PG-pullup-local-move-r3.json').read_text())['R11049_target_pose'],'native_jobs':0,'board_written':False}
    (L.OUT/'joint-local-quantized-r2.json').write_text(json.dumps(r,indent=2)+'\n');print('JOINT_QUANTIZED',len(r['new_vias']),len(r['new_tracks']))
