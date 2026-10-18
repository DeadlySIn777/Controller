"""Route the actual nine AC-only couplings and common shield/bond on a PCB copy.

No functional return is DC bonded to CHASSIS. Existing private central shield
tails are replaced only after proving their entire actual pad population. This
does not qualify protective-earth fault current or the complete EMC assembly.
"""
import argparse, collections, heapq, json, math, shutil, subprocess
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT, sha, xy, rect, transformed_box
from hardware_route_logic_return import identity, distance, segment_hits_box
from hardware_route_local_signals import GeometryIndex, paths
from hardware_isow_layout_recipe import lands, vec
from hardware_build_assembly import parse, dump, child, value

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--proposal',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--local-only',action='store_true')
    args=ap.parse_args();out=args.out.resolve();assert not out.exists();out.mkdir(parents=True)
    proposal=json.loads(args.proposal.read_text());assert proposal['all_finite_body_copper_mate_pose_screens_pass']
    base=Path(next(q for q in proposal['input_hashes']if q.endswith('motherboard-bounded-merged-candidate.kicad_pcb')))
    manifest=ROOT/'reports/motherboard-bypass-owners-20260930/complete723-source-r06/capacitor-owners.json'
    inputs={str(q):sha(q)for q in[base,base.with_suffix('.kicad_pro'),base.with_suffix('.kicad_dru'),base.parent/'drc.json',args.proposal.resolve(),manifest,Path(__file__)]}
    assert all(sha(Path(q))==h for q,h in proposal['input_hashes'].items())
    b=p.LoadBoard(str(base));b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()}
    rows=[z for z in json.loads(manifest.read_text())['capacitors']if z['ref'].startswith('C195')];assert len(rows)==9
    oldlands={r:lands(f)for r,f in fs.items()};oldposes={r:[*xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayerName()]for r,f in fs.items()}
    oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
    def pad(ref,pin):return next(z for z in fs[ref].Pads()if z.GetNumber()==str(pin))
    moving={z['ref']for z in proposal['proposal']if z['old_pose']!=z['new_pose']}
    central={'H19501'}|moving
    cluster=b.GetConnectivity().GetConnectedItems(pad('H19501','1'))
    actual={z.GetParentFootprint().GetReference()for z in cluster if z.Type()==p.PCB_PAD_T}
    assert actual==central,(actual,central)
    doomed={z.m_Uuid.AsString()for z in cluster if z.Type()in[p.PCB_TRACE_T,p.PCB_VIA_T]}
    assert doomed and all(oldcu[z][1].endswith('/CHASSIS')for z in doomed)
    removed={u:dict(before=oldcu[u],reason='Entire old central shield-only cluster has exactly the seven relocated Y2 CHASSIS pads and the existing M4 bond; no other physical terminal.')for u in doomed}
    tree=parse(base.read_text())
    for q in list(tree):
        if isinstance(q,list)and q[0]in['segment','arc','via']and value(child(q,'uuid')[1])in doomed:tree.remove(q)
    filtered=out/'filtered-old-native.kicad_pcb';filtered.write_text(dump(tree)+'\n');b=p.LoadBoard(str(filtered));fs={f.GetReference():f for f in b.GetFootprints()}
    for row in proposal['proposal']:
        f=fs[row['ref']];x,y,angle=row['new_pose'];f.SetOrientationDegrees(angle);f.SetPosition(vec((x,y)))
    pi={p.F_Cu:GeometryIndex(),p.B_Cu:GeometryIndex()};ti={p.F_Cu:GeometryIndex(),p.B_Cu:GeometryIndex()};holes=GeometryIndex();barriers=[]
    for z in b.GetPads():
        for layer in pi:
            if z.IsOnLayer(layer):pi[layer].add((z.GetNetname(),z),rect(z.GetBoundingBox()))
        drill=p.ToMM(z.GetDrillSize().x)
        if drill:holes.add((z.GetNetname(),xy(z.GetPosition()),drill/2,z.GetAttribute()==p.PAD_ATTRIB_NPTH),rect(z.GetBoundingBox()))
    for f in fs.values():
        name=str(f.GetFPID().GetLibItemName()).upper()
        if any(s in name for s in['ISO1212','ISO772','ISO774','ISO776','TLP3640','TLP4176','TMR4WI']):
            points=[xy(z.GetPosition())for z in f.Pads()if z.IsOnCopperLayer()];x,y=xy(f.GetPosition())
            box=(x-.6,min(z[1]for z in points)-.8,x+.6,max(z[1]for z in points)+.8)if f.GetOrientationDegrees()%180==0 else(min(z[0]for z in points)-.8,y-.6,max(z[0]for z in points)+.8,y+.6)
            barriers.append((f.GetReference(),box))
    # Do not route even common shield metal through either reviewed raw output
    # corridor, across their isolation barrier, or beneath the ESP antenna.
    barriers.extend([('ISOW_RS485',[377.2,92.55,387.5,102.2]),('ISOW_CAN',[329.2,60.55,339.5,70.2]),('ISOW_RS485_ISO',[373.4,85,374.6,99]),('ISOW_CAN_ISO',[325.4,53,326.6,67]),('ESP_RF',transformed_box(fs['J16001'],[2.48,-7.85,20.48,-1.54]))])
    def index(t):
        for layer in ti:
            if t.IsOnLayer(layer):ti[layer].add((t.GetNetname(),t),rect(t.GetBoundingBox()))
    for t in b.GetTracks():index(t)
    def clear(points,net,layer,width):
        for s,e in zip(points,points[1:]):
            if any(segment_hits_box(s,e,box,width/2)for _,box in barriers):return False
            if min(*s,*e)<.8 or max(s[0],e[0])>459.2 or max(s[1],e[1])>339.2:return False
            t=p.PCB_TRACK(b);t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetStart(vec(s));t.SetEnd(vec(e));shape=t.GetEffectiveShape(layer)
            for name,z in pi[layer].candidates(s,e,width/2+.3):
                if name!=net and shape.Collide(z.GetEffectiveShape(layer),p.FromMM(.151)):return False
            for name,z in ti[layer].candidates(s,e,width/2+.3):
                if name!=net and shape.Collide(z.GetEffectiveShape(layer),p.FromMM(.151)):return False
            for name,pt,r,nonplated in holes.candidates(s,e,width/2+1):
                if (nonplated or name!=net)and distance(pt,s,e)<r+width/2+.251:return False
        return True
    def find_route(s,e,net,layer,width):
        for v in paths(s,e):
            if clear(v,net,layer,width):return v
        for x in range(max(1,int(min(s[0],e[0]))-25),min(459,int(max(s[0],e[0]))+25)+1):
            v=[s,(x,s[1]),(x,e[1]),e]
            if clear(v,net,layer,width):return v
        for y in range(max(1,int(min(s[1],e[1]))-25),min(339,int(max(s[1],e[1]))+25)+1):
            v=[s,(s[0],y),(e[0],y),e]
            if clear(v,net,layer,width):return v
        xmin=max(1,int(min(s[0],e[0]))-35);xmax=min(459,int(max(s[0],e[0]))+35);ymin=max(1,int(min(s[1],e[1]))-35);ymax=min(339,int(max(s[1],e[1]))+35)
        starts=[(x,y)for x in range(math.floor(s[0])-1,math.ceil(s[0])+2)for y in range(math.floor(s[1])-1,math.ceil(s[1])+2)if clear([s,(x,y)],net,layer,width)]
        goals={(x,y)for x in range(math.floor(e[0])-1,math.ceil(e[0])+2)for y in range(math.floor(e[1])-1,math.ceil(e[1])+2)if clear([(x,y),e],net,layer,width)}
        queue=[];cost={};previous={};visited=set();end=None
        for point in starts:
            g=math.dist(s,point);cost[point]=g;previous[point]=None;heapq.heappush(queue,(g+math.dist(point,e),g,point))
        while queue and len(visited)<100000:
            _,g,point=heapq.heappop(queue)
            if point in visited:continue
            visited.add(point)
            if point in goals:end=point;break
            for dx,dy in[(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                other=(point[0]+dx,point[1]+dy)
                if other in visited or not(xmin<=other[0]<=xmax and ymin<=other[1]<=ymax):continue
                gg=g+math.hypot(dx,dy)
                if gg>=cost.get(other,float('inf'))or not clear([point,other],net,layer,width):continue
                cost[other]=gg;previous[other]=point;heapq.heappush(queue,(gg+math.dist(other,e),gg,other))
        if end is None:return None
        points=[]
        while end is not None:points.append(end);end=previous[end]
        raw=[s]+list(reversed(points))+[e];result=[]
        for point in raw:
            if result and math.dist(point,result[-1])<1e-8:continue
            while len(result)>1 and abs((result[-1][0]-result[-2][0])*(point[1]-result[-1][1])-(result[-1][1]-result[-2][1])*(point[0]-result[-1][0]))<1e-8:result.pop()
            result.append(point)
        return result
    added={};routes=[]
    def route(q,z,description,width=.5):
        assert q.GetNetCode()==z.GetNetCode()
        b.BuildConnectivity();cluster={a.m_Uuid.AsString()for a in b.GetConnectivity().GetConnectedItems(q)if a.Type()==p.PCB_PAD_T}
        if z.m_Uuid.AsString()in cluster:
            routes.append(dict(a=[q.GetParentFootprint().GetReference(),q.GetNumber()],z=[z.GetParentFootprint().GetReference(),z.GetNumber()],already_connected=True,reason=description));return True
        s,e=xy(q.GetPosition()),xy(z.GetPosition());net=q.GetNetname();choice=None
        for layer in[p.B_Cu,p.F_Cu]:
            if not q.IsOnLayer(layer)or not z.IsOnLayer(layer):continue
            points=find_route(s,e,net,layer,width)
            if points is not None:choice=(layer,points);break
        if choice is None:return False
        layer,points=choice;ids=[]
        for start,end in zip(points,points[1:]):
            if math.dist(start,end)<1e-8:continue
            t=p.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetStart(vec(start));t.SetEnd(vec(end));b.Add(t);index(t);ids.append(t.m_Uuid.AsString());added[t.m_Uuid.AsString()]=identity(t)
        routes.append(dict(a=[q.GetParentFootprint().GetReference(),q.GetNumber()],z=[z.GetParentFootprint().GetReference(),z.GetNumber()],already_connected=False,layer=b.GetLayerName(layer),width_mm=width,points_mm=points,path_length_mm=sum(math.dist(s,e)for s,e in zip(points,points[1:])),added_UUIDs=ids,reason=description));print('ROUTED',description,len(ids),flush=True);return True
    # Actual domain returns and shield terminals, not nearest arbitrary ground.
    for row in rows:
        for cp,key in[('1','power_nodes'),('2','return_nodes')]:
            q=pad(row['ref'],cp);dest=sorted([pad(z['ref'],z['pin'])for z in row[key]],key=lambda z:math.dist(xy(q.GetPosition()),xy(z.GetPosition())))
            good=next((z for z in dest if route(q,z,'Exact '+row['ref']+'.'+cp+' AC-only own connector endpoint',.2 if row['ref']=='C19501'and cp=='1'else .5)),None)
            assert good is not None,(row['ref'],cp)
    if not args.local_only:
        # Join all actual shield/bond pads as a CHASSIS-only native spanning
        # network. This signal/shield conductor is not a rated external PE path.
        shields=[z for z in b.GetPads()if z.GetNetname().endswith('/CHASSIS')];assert len(shields)==51
        failed=set()
        while True:
            b.BuildConnectivity();groups={}
            for z in shields:
                c=frozenset(a.m_Uuid.AsString()for a in b.GetConnectivity().GetConnectedItems(z)if a.Type()==p.PCB_PAD_T);groups.setdefault(c,[]).append(z)
            if len(groups)==1:break
            pairs=[];values=list(groups.values())
            for i,one in enumerate(values):
                for two in values[i+1:]:
                    for q in one:
                        for z in two:
                            key=tuple(sorted((q.m_Uuid.AsString(),z.m_Uuid.AsString())))
                            if key not in failed:pairs.append((math.dist(xy(q.GetPosition()),xy(z.GetPosition())),q,z,key))
            joined=False
            for _,q,z,key in sorted(pairs,key=lambda v:v[0]):
                if route(q,z,'Common CHASSIS shield-to-bond network; no functional-return DC tie',1.):joined=True;break
                failed.add(key)
            if not joined:raise AssertionError(('Unrouted shield clusters',len(groups)))
    for f in base.parent.iterdir():
        if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,out/f.name)
    shutil.copyfile(base.parent/'fp-lib-table',out/'fp-lib-table')
    p.ZONE_FILLER(b).Fill(b.Zones());dest=out/'motherboard-y2-chassis-candidate.kicad_pcb';p.SaveBoard(str(dest),b)
    for suffix in['.kicad_pro','.kicad_dru']:shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
    run=subprocess.run([str(CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'drc.txt').write_text(run.stdout+run.stderr)
    fresh=p.LoadBoard(str(dest));fresh.BuildConnectivity();nf={f.GetReference():f for f in fresh.GetFootprints()};cu={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
    assert oldlands=={r:lands(f)for r,f in nf.items()}
    assert all(oldposes[r]==[*xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayerName()]for r,f in nf.items()if r not in moving)
    assert all(cu.get(u)==v for u,v in oldcu.items()if u not in doomed)
    assert set(cu)==(set(oldcu)-doomed)|set(added)
    checks=[]
    for row in routes:
        q=next(z for z in nf[row['a'][0]].Pads()if z.GetNumber()==row['a'][1]);z=next(z for z in nf[row['z'][0]].Pads()if z.GetNumber()==row['z'][1]);cluster={a.m_Uuid.AsString()for a in fresh.GetConnectivity().GetConnectedItems(q)if a.Type()==p.PCB_PAD_T};checks.append(dict(a=row['a'],z=row['z'],actual_connected=z.m_Uuid.AsString()in cluster))
    assert all(z['actual_connected']for z in checks)
    chassis=next(z for z in nf['H19501'].Pads());cs={z.m_Uuid.AsString()for z in fresh.GetConnectivity().GetConnectedItems(chassis)if z.Type()==p.PCB_PAD_T};chassis_count=sum(z.m_Uuid.AsString()in cs for z in fresh.GetPads()if z.GetNetname().endswith('/CHASSIS'))
    baseline=json.loads((base.parent/'drc.json').read_text());drc=json.loads((out/'drc.json').read_text());before_violations={json.dumps(z,sort_keys=True)for z in baseline['violations']};after_violations={json.dumps(z,sort_keys=True)for z in drc['violations']}
    assert inputs=={q:sha(Path(q))for q in inputs}
    result=dict(input_hashes=inputs,board_sha256=sha(dest),physical_parts=len(nf),native_Cu_count=len(cu),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),moved_Y2_poses={r:dict(before=oldposes[r],after=[*xy(nf[r].GetPosition()),nf[r].GetOrientationDegrees(),nf[r].GetLayerName()])for r in moving},removed_old_private_copper=removed,added_native_copper=added,routes=routes,independent_native_route_checks=checks,native_CHASSIS_pads=51,native_CHASSIS_pads_connected_to_bond=chassis_count,all_unrelated_lands_pin_nets_poses_and_Cu_unchanged=True,native_DRC_regular=len(drc['violations']),native_DRC_types=dict(collections.Counter(v['type']for v in drc['violations'])),native_DRC_new_exact_violations=[json.loads(z)for z in after_violations-before_violations],native_DRC_ignored=drc.get('ignored_checks',[]),baseline_native_DRC_regular=len(baseline['violations']),source_modified=False,PCB_parent_modified=False,physical_qualification=False,protective_earth_fault_capacity_qualified=False,manufacturing_ready=False)
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copyfile(__file__,out/'issued-tool.py');print(json.dumps({k:v for k,v in result.items()if k not in['input_hashes','moved_Y2_poses','removed_old_private_copper','added_native_copper','routes','independent_native_route_checks','native_DRC_new_exact_violations']}))
    assert not result['native_DRC_new_exact_violations']and not result['native_DRC_ignored']
    assert args.local_only or chassis_count==51

if __name__=='__main__':main()
