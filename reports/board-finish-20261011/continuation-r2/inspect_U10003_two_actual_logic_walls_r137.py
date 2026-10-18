"""Read exact wall geometry and local source geometry; no geometry mutations."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
OUT=H/'U10003-two-actual-logic-wall-coupled-geometry-r137'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl'
    assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
    g,h,b,z,full=pickle.loads(mp.read_bytes());groups=pickle.loads(mp.with_name('groups.pkl').read_bytes())
    uuids=('eeb33c09-9494-4734-b174-e3c3ceffd73b','8f7ea41c-9cfd-4c25-a376-00657f6105ed')
    rows=[];win=box(210,136,221,148)
    for uid in uuids:
        target=next(t for t in h['tracks'] if t['uuid']==uid);net=C.norm(target['net'])
        ts=[t for t in h['tracks'] if C.norm(t['net'])==net and C.track(t).intersects(win)]
        vs=[v for v in h['vias'] if C.norm(v['net'])==net and win.covers(Point(v['x'],v['y']))]
        ps=[{k:p[k] for k in ('uuid','ref','num','x','y','layers','smd')} for p in h['pads'] if C.norm(p['net'])==net and win.covers(Point(p['x'],p['y']))]
        rows.append({'target_track':target,'domain':h['domains_normalized'][net],'nearby_same_net_tracks':ts,'nearby_same_net_vias':vs,'nearby_same_net_pads':ps,'old_discrete_group_count':len(F.graph(full,net))})
    sources={}
    for net,ref,pin in (('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_power/LOGIC_GND','J1','2')):
        if net not in groups:net=next(n for n in groups if n.endswith('/LOGIC_GND'))
        roots=[xs for xs in groups[net] if any(q['kind']=='pad' and q.get('ref')==ref and q.get('pin')==pin for q in xs)]
        if not roots:roots=[max(groups[net],key=len)]
        root=roots[0];sources[net]={}
        for l in h['copper_layers']:
            shape=unary_union([q['shape'] for q in root if q['layer']==l]).intersection(win)
            p=OUT/(net.rsplit('/',1)[-1]+'-'+l+'.wkb');p.write_bytes(shape.wkb)
            sources[net][l]={'path':str(p),'sha256':sha(p),'area_mm2':shape.area}
    receipt={'verdict':'EXACT_WALL_GEOMETRY_READ_ONLY','model_sha256':sha(mp),'rows':rows,'source_regions':sources,'native_jobs':0,'board_written':False,'adopted':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n')
    print('R137',sha(OUT/'receipt.json'),flush=True)
    for row in rows:print(json.dumps({k:row[k] for k in ('target_track','domain','nearby_same_net_tracks','nearby_same_net_vias','nearby_same_net_pads','old_discrete_group_count')}),flush=True)
if __name__=='__main__':main()
