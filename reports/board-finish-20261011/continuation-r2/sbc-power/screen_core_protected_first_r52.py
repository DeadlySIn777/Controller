"""Read-only pair screen of immutable CORE3 against first protected R9 body."""
import json,pickle,hashlib
from pathlib import Path
from shapely.geometry import Point,LineString
import core_inner_feed_r18 as I
L=I.L;G=I.G;OUT=L.OUT/'core-ten-vs-protected-first-r52'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();stage=L.OUT/'remaining-core-accepted-checkpoints-r50/stage-10';g,h,b,z,c=pickle.loads((stage/'accepted-checkpoint-model.pkl').read_bytes())
    assert sha(stage/'accepted-checkpoint-model.pkl')=='a1d9cc1c180c827f2a3c9582b218d8856b9cf9dc672cb97a6d5e3bbf81348bb3'
    d=pickle.loads((stage/'proposed-discrete.pkl').read_bytes());zs=pickle.loads((stage/'new-CORE-zones.pkl').read_bytes())
    prior=L.OUT.parent/'protected24-r9-accepted-positive-snapshot-r1';pz=pickle.loads((prior/'proposed-zones.pkl').read_bytes());assert sha(prior/'proposed-zones.pkl')=='d50421ed63da1222774430814cbd78eb1e0b321a02b187afc493ef44ba7c634c'
    pairs=[];errors=[]
    for q in pz:
        for z in zs:
            if z['layer']!=q['layer']:continue
            actual=z['shape'].distance(q['shape']);gap=max(G.gap(h,z['net'],q['net']),float(q.get('clearance_mm',.15)),float(z.get('clearance_mm',.15)))+.025
            pair={'CORE_uuid':z['uuid'],'protected_uuid':q['uuid'],'kind':'plane_vs_plane','actual_gap_mm':actual,'required_gap_mm':gap};pairs.append(pair)
            if actual<gap:errors.append(pair)
        for v in d['vias']:
            actual=Point(v['x'],v['y']).distance(q['shape']);required=max(v['drill']/2+.275,v['d']/2+G.gap(h,v['net'],q['net'])+.025)
            pair={'CORE_uuid':v['uuid'],'protected_uuid':q['uuid'],'kind':'via_vs_plane','actual_center_distance_mm':actual,'required_center_distance_mm':required};pairs.append(pair)
            if actual<required:errors.append(pair)
        for t in d['tracks']:
            if t['layer']!=q['layer']:continue
            actual=LineString([t['a'],t['b']]).distance(q['shape'])-t['w']/2;required=G.gap(h,t['net'],q['net'])+.025
            pair={'CORE_uuid':t['uuid'],'protected_uuid':q['uuid'],'kind':'segment_vs_plane','actual_gap_mm':actual,'required_gap_mm':required};pairs.append(pair)
            if actual<required:errors.append(pair)
    (OUT/'receipt.json').write_text(json.dumps({'verdict':'PASS_SCOPED_ANALYTIC_PAIRS' if not errors else 'FAIL_SCOPED_ANALYTIC_PAIRS','CORE_stage10_model_sha256':sha(stage/'accepted-checkpoint-model.pkl'),'protected_snapshot_zone_sha256':sha(prior/'proposed-zones.pkl'),'all_seven_snapshot_planes_checked':True,'errors':errors,'pairs':pairs,'later_CORE_and_protected_shapes_not_screened':True,'projected_source_contact_current_native':'OPEN','native_jobs':0,'board_written':False},indent=2)+'\n');print('CORE10_PROTECTED_R9_FIRST',len(errors),sha(OUT/'receipt.json'),errors,flush=True)
if __name__=='__main__':main()
