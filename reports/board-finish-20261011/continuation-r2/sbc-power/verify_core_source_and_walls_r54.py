"""Frozen R48 actual source scope, R9 second snapshot, and three wall census."""
import json,pickle,hashlib
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely import STRtree
import core_inner_feed_r18 as I
L=I.L;p=I.p;Q=I.Q;G=I.G
OUT=L.OUT/'core-source-walls-and-protected-second-r54'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    f=L.OUT/'remaining-core-feeds-r48/model.pkl';assert sha(f)=='3e4e42806786d7d15f66f8029f674db50c4df235adcea16d2f5d7a19b7757baa'
    g,h,b,z,c=pickle.loads(f.read_bytes());r=json.loads((f.parent/'receipt.json').read_text())
    Q.NET=I.NET;groups,parts,assign=Q.groups(c,return_details=True);lookup={q['uuid']:i for i,rs in enumerate(groups) for q in rs}
    sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));root=lookup[sp['uuid']]
    source_checks=[]
    for name,rf in [('earlier_five',L.OUT/'actual-core-cross-layer-source-bridge-r38/receipt.json'),('new_ten',f.parent/'receipt.json')]:
        rr=json.loads(rf.read_text())
        # Earlier receipt uses a different detail format; every original R47 target
        # absent from this final exact source component is separately enumerated.
        if name=='new_ten':
            for row in rr['rows']:
                pads=[q for q in row['physical_contacts'] if not q['ref'].startswith('@')]
                checks=[{'uuid':q['uuid'],'ref':q['ref'],'pad':q['pad'],'actual_source_rooted':lookup[q['uuid']]==root} for q in pads]
                assert all(q['actual_source_rooted'] for q in checks)
                source_checks.append({'scope':name,'constructor_group':row['group'],'pads':checks})
    missing=[{'group':i,'pads':[q for q in rs if not q['ref'].startswith('@')]} for i,rs in enumerate(groups) if i!=root and any(not q['ref'].startswith('@') for q in rs)]
    expected={('U9001','10'),('R17031','1'),('U11007','6')};actual={(q['ref'],q['pad']) for rs in missing for q in rs['pads']};assert actual==expected
    earlier=json.loads((L.OUT/'remaining-core-feeds-r48/initial-islands.json').read_text())
    initial_uuids={q['uuid'] for row in earlier['targets'] for q in row['pads']};assert len(initial_uuids)==21
    for q in h['pads']:
        if p.norm(q['net'])==I.NET and q['uuid'] not in initial_uuids:assert lookup[q['uuid']]==root,('earlier_CORE_pad_lost_source',q['ref'],q['num'],q['uuid'])
    rd=L.OUT.parent/'protected24-r9-accepted-positive-snapshot-r2';pz=pickle.loads((rd/'proposed-zones.pkl').read_bytes());assert sha(rd/'proposed-zones.pkl')=='7a96e527601456bb579fc6a899c47c7846556520505882616bb972826b066878'
    d=pickle.loads((f.parent/'proposed-discrete.pkl').read_bytes());zs=pickle.loads((f.parent/'new-CORE-zones.pkl').read_bytes());pairs=[];errors=[]
    for q in pz:
        for a in zs:
            if a['layer']!=q['layer']:continue
            dist=a['shape'].distance(q['shape']);req=max(G.gap(h,a['net'],q['net']),float(a.get('clearance_mm',.15)),float(q.get('clearance_mm',.15)))+.025
            row={'kind':'zone','CORE_uuid':a['uuid'],'protected_uuid':q['uuid'],'gap_mm':dist,'required_mm':req};pairs.append(row)
            if dist<req:errors.append(row)
        for v in d['vias']:
            dist=Point(v['x'],v['y']).distance(q['shape']);req=max(v['drill']/2+.275,v['d']/2+max(G.gap(h,v['net'],q['net']),float(q.get('clearance_mm',.15)))+.025)
            row={'kind':'via','CORE_uuid':v['uuid'],'protected_uuid':q['uuid'],'center_gap_mm':dist,'required_mm':req};pairs.append(row)
            if dist<req:errors.append(row)
        for t in d['tracks']:
            if t['layer']!=q['layer']:continue
            dist=LineString([t['a'],t['b']]).distance(q['shape'])-t['w']/2;req=max(G.gap(h,t['net'],q['net']),float(q.get('clearance_mm',.15)))+.025
            row={'kind':'track','CORE_uuid':t['uuid'],'protected_uuid':q['uuid'],'gap_mm':dist,'required_mm':req};pairs.append(row)
            if dist<req:errors.append(row)
    walls=[];records={l:[] for l in I.LAYERS}
    for a in h['pads']:
        for l,rs in a['layers'].items():
            for s in p.base.polygons(rs):records[l].append({'kind':'pad','uuid':a['uuid'],'net':a['net'],'shape':s,'ref':a['ref'],'pin':a['num'],'source':'native_discrete'})
    for a in h['tracks']:records[a['layer']].append({'kind':'track','uuid':a['uuid'],'net':a['net'],'shape':p.base.body(a),'source':'native_or_owned_discrete','geometry':a})
    for a in h['vias']:
        for l in a['flashed']:records[l].append({'kind':'via','uuid':a['uuid'],'net':a['net'],'shape':Point(a['x'],a['y']).buffer(a['d']/2),'source':'native_or_owned_discrete'})
    for a in z:records[a['layer']].append({'kind':'new_zone','uuid':a['uuid'],'net':a['net'],'shape':a['shape'],'source':'owned_new_plane'})
    trees={l:STRtree([a['shape'] for a in rs]) for l,rs in records.items()}
    for row in missing:
        for q in row['pads']:
            pad=next(a for a in h['pads'] if a['uuid']==q['uuid']);near=[]
            for l,rs in pad['layers'].items():
                padshape=p.base.polygons(rs)[0];win=Point(q['at']).buffer(3)
                for ii in trees[l].query(win,predicate='intersects'):
                    a=records[l][int(ii)]
                    if p.norm(a['net'])==I.NET:continue
                    distance=padshape.distance(a['shape']);req=G.gap(h,pad['net'],a['net'])+.025
                    near.append({**{k:v for k,v in a.items() if k!='shape'},'layer':l,'pad_Cu_distance_mm':distance,'ordinary_Cu_guard_mm':req,'bounds':a['shape'].bounds})
            walls.append({'pad':q,'nearby_foreign_bodies':sorted(near,key=lambda a:a['pad_Cu_distance_mm'])})
    (OUT/'walls.json').write_text(json.dumps(walls,indent=2)+'\n')
    receipt={'verdict':'PASS_ACTUAL_CORE_SOURCE_SCOPE_AND_PROTECTED_SECOND' if not errors else 'FAIL_PROTECTED_SECOND','model_sha256':sha(f),'receipt_sha256':sha(f.parent/'receipt.json'),'source':'R11022.2','source_checks':source_checks,'earlier_non_target_CORE_pads_all_still_source_rooted':True,'remaining':missing,'protected_snapshot_sha256':sha(rd/'proposed-zones.pkl'),'pair_errors':errors,'pairs':pairs,'full_current_native_and_retained_foreign_contacts':'OPEN','native_jobs':0,'board_written':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('CORE_SOURCE_WALLS_R54',len(source_checks),len(missing),len(errors),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
