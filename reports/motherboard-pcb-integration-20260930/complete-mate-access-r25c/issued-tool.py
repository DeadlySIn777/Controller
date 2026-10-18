"""Apply the reviewed standard-mate poses to an isolated native board copy.

Power-group poses are checked as future obstacles, never applied here. Exact
lands/source nets and unrelated copper remain unchanged. Native DRC and the
independent full-source inventory are required before root adopts any candidate.
"""
import argparse,collections,json,math,shutil,subprocess,heapq
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy,rect,overlap,grown,body_box,graphic_box,transformed_box
from hardware_apply_motherboard_mechanical_access import moved_point
from hardware_route_logic_return import identity,mm,segment_distance,segment_hits_box
from hardware_populate_motherboard_pcb import pad_template
from hardware_reconcile_motherboard_peripheral_pcb import piece
from hardware_route_local_signals import paths,GeometryIndex

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out',required=True,type=Path)
args=ap.parse_args();out=args.out.resolve()
assert not out.exists() and out.is_relative_to(ROOT/'reports');out.mkdir(parents=True)
source=ROOT/'reports/motherboard-pcb-integration-20260930/current-source-population-r24f/motherboard-current-source-candidate.kicad_pcb'
proposal_path=ROOT/'reports/motherboard-mechanical-20260930/r24f-complete-mate-proposal-r05/review.json'
proposal=json.loads(proposal_path.read_text());assert proposal['pass'] and sha(source)==proposal['input_board_sha256']
before={str(f):sha(f)for f in [source,source.with_suffix('.kicad_pro'),source.with_suffix('.kicad_dru'),proposal_path]}
b=p.LoadBoard(str(source));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
oldtracks={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
oldpieces={(r,z.m_Uuid.AsString()):piece(z)for r,f in fps.items()for z in f.Pads()}
templates={r:collections.Counter(pad_template(z)for z in f.Pads())for r,f in fps.items()}
oldposes={r:[*mm(f.GetPosition()),f.GetOrientationDegrees()]for r,f in fps.items()}
poses=proposal['exact_proposed_poses'];assert len(poses)==15
removed={};modified={};added=[];route_receipts=[]

# These six tracks are complete private connector-local return bridges. Native
# connectivity proves that their only actual endpoint pads belong to one header.
private={}
for ref,pin in [('J19523','9'),('J19532','3')]:
    pad=next(z for z in fps[ref].Pads()if z.GetNumber()==pin)
    cluster=b.GetConnectivity().GetConnectedItems(pad)
    assert all(z.GetParentFootprint().GetReference()==ref for z in cluster if z.Type()==p.PCB_PAD_T)
    ids=[z.m_Uuid.AsString()for z in cluster if z.Type()==p.PCB_TRACE_T]
    assert len(ids)==3,(ref,ids)
    for uid in ids:private[uid]=ref
for uid,ref in private.items():
    t=tracks[uid];t.SetStart(p.VECTOR2I(p.FromMM(moved_point(mm(t.GetStart()),oldposes[ref],poses[ref])[0]),p.FromMM(moved_point(mm(t.GetStart()),oldposes[ref],poses[ref])[1])))
    point=moved_point(mm(t.GetEnd()),oldposes[ref],poses[ref]);t.SetEnd(p.VECTOR2I(p.FromMM(point[0]),p.FromMM(point[1])))
    modified[uid]={'before':oldtracks[uid],'after':identity(t),'reason':'Entire native header-only same-net return bridge follows its reviewed header pose.'}

# Shared return/shield branches have one moved endpoint and a fixed external
# endpoint. Remove only the exact branches, then route real same-net replacements;
# never stretch a long straight segment through unrelated pads/copper.
targets=[]
for ref in ['J11005','J11006','J19531','J19534']:
    rows=proposal['old_actual_attached_copper'][ref];assert len(rows)==1
    uid=next(iter(rows));t=tracks[uid]
    own=[];external=[]
    for pt in [t.GetStart(),t.GetEnd()]:
        ownpads=[z for z in fps[ref].Pads()if z.HitTest(pt)and z.GetNetCode()==t.GetNetCode()]
        if ownpads:own.append(ownpads[0].GetNumber())
        else:external.append(mm(pt))
    assert len(own)==len(external)==1,(ref,own,external)
    targets.append({'reference':ref,'pin':own[0],'external_old_endpoint':external[0],'net':t.GetNetname()})
    removed[uid]={'identity':oldtracks[uid],'reason':'Exact old branch attached to a moved header; native replacement must rejoin its actual same net.'};b.Remove(t)
for ref,(x,y,a)in poses.items():fps[ref].SetOrientationDegrees(a);fps[ref].SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))

# Pair each moved AI/safety shield port with its existing AC-only Y2 capacitor.
# The capacitor's pin1 domain and pin2 CHASSIS assignment stay exactly unchanged.
# Existing central private CHASSIS tails are removed to their true first junction.
cap_ports={'C19507':('J19531','11','12'),'C19504':('J19534','9','12')}
same_tracks=[t for t in b.GetTracks()if t.GetNetname()=='/CHASSIS'and not isinstance(t,p.PCB_VIA)]
cap_remove=set()
for ref in cap_ports:
    pad=next(z for z in fps[ref].Pads()if z.GetNumber()=='2');point=tuple(pad.GetPosition());last=None
    while True:
        candidates=[t for t in same_tracks if t.m_Uuid.AsString()not in cap_remove and t.m_Uuid.AsString()!=last and point in [tuple(t.GetStart()),tuple(t.GetEnd())]]
        if len(candidates)!=1:break
        t=candidates[0];uid=t.m_Uuid.AsString();other=tuple(t.GetEnd())if tuple(t.GetStart())==point else tuple(t.GetStart())
        removed[uid]={'identity':oldtracks[uid],'reason':'Exact old private Y2 CHASSIS tail removed only to its existing junction/pad before local port co-move.'};cap_remove.add(uid)
        if any(z.GetParentFootprint().GetReference()!=ref and z.GetNetname()=='/CHASSIS'and z.HitTest(p.VECTOR2I(*other))for z in b.GetPads()):break
        point=other;last=uid

for t in same_tracks:
    if t.m_Uuid.AsString()in cap_remove:b.Remove(t)

recipe_path=Path(next(k for k in proposal['input_hashes']if k.endswith('power-groups-geometry-candidate.kicad_pcb')))
recipe_receipt=recipe_path.with_name('placement-receipt.json');recipe=p.LoadBoard(str(recipe_path));rf={f.GetReference():f for f in recipe.GetFootprints()}
virtual={r:(graphic_box(f,p.F_CrtYd)or body_box(f)[0])for r,f in fps.items()}
for group in json.loads(recipe_receipt.read_text())['groups']:
    for ref in group['refs']:virtual[ref]=graphic_box(rf[ref],p.F_CrtYd)or body_box(rf[ref])[0]
for ref,row in proposal['actual40_ports_mutually_checked'].items():
    for kind,box in row['envelopes_mm'].items():virtual[ref+'_'+kind]=box
virtual.update({'CM_MODULE':transformed_box(fps['J15001'],[-3,-30,37,25]),'ESP_MODULE':transformed_box(fps['J16001'],[-1.27,-1.565,24.13,61.3]),'ESP_RF15':grown(transformed_box(fps['J16001'],[2.48,-7.85,20.48,-1.54]),15)})
for ref in ['H22001','H22002','H22003','H22004','H22005','H22006']:
    x,y=mm(fps[ref].GetPosition());virtual[ref+'_WASHER']=[x-4.25,y-4.25,x+4.25,y+4.25]
cap_poses={}
for ref,(port,p1,p2)in cap_ports.items():
    f=fps[ref];pp={z.GetNumber():mm(z.GetPosition())for z in fps[port].Pads()};center=((pp[p1][0]+pp[p2][0])/2,(pp[p1][1]+pp[p2][1])/2)
    candidates=[]
    for x in range(int(center[0])-22,int(center[0])+23):
        for y in range(int(center[1])-22,int(center[1])+23):
            for angle in [0,90,180,270]:
                f.SetOrientationDegrees(angle);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
                pads={z.GetNumber():mm(z.GetPosition())for z in f.Pads()};score=math.dist(pads['1'],pp[p1])+math.dist(pads['2'],pp[p2]);candidates.append((score,x,y,angle))
    for score,x,y,angle in sorted(candidates):
        f.SetOrientationDegrees(angle);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));box=graphic_box(f,p.F_CrtYd)or body_box(f)[0]
        if any(overlap(grown(box,.25),other)for name,other in virtual.items()if name!=ref):continue
        bad=False
        for pad in f.Pads():
            for t in b.GetTracks():
                if pad.GetNetCode()==t.GetNetCode()or not overlap(grown(rect(pad.GetBoundingBox()),.15),rect(t.GetBoundingBox())):continue
                layer=p.F_Cu if isinstance(t,p.PCB_VIA)else t.GetLayer()
                if pad.IsOnLayer(layer)and pad.GetEffectiveShape(layer).Collide(t.GetEffectiveShape(layer),p.FromMM(.15)):bad=True;break
            if bad:break
        if bad:continue
        cap_poses[ref]={'before':oldposes[ref],'after':[x,y,angle],'actual_port':port,'own_return_pin':p1,'CHASSIS_pin':p2,'total_terminal_to_cap_span_mm':score};virtual[ref]=box;break
    assert ref in cap_poses,'No honest local Y2 clearance '+ref

# Route only the bounded replacement shield/return resources. These existing
# 0.2mm auxiliary return links do not qualify whole-board high-current paths.
pad_index={p.F_Cu:GeometryIndex(),p.B_Cu:GeometryIndex()};track_index={p.F_Cu:GeometryIndex(),p.B_Cu:GeometryIndex()};barriers=[]
for q in b.GetPads():
    for layer in pad_index:
        if q.IsOnLayer(layer):pad_index[layer].add((q.GetNetname(),q),rect(q.GetBoundingBox()))
for f in b.GetFootprints():
    name=str(f.GetFPID().GetLibItemName()).upper()
    if any(s in name for s in ['ISO1212','ISO772','ISO774','ISO776','TLP3640','TLP4176','TMR4WI']):
        q=[mm(z.GetPosition())for z in f.Pads()if z.IsOnCopperLayer()];x,y=mm(f.GetPosition())
        if f.GetOrientationDegrees()%180==0:barriers.append((x-.5,min(v[1]for v in q)-.8,x+.5,max(v[1]for v in q)+.8))
        else:barriers.append((min(v[0]for v in q)-.8,y-.5,max(v[0]for v in q)+.8,y+.5))
def index_track(t):
    for layer in track_index:
        if t.IsOnLayer(layer):track_index[layer].add((t.GetNetname(),t),rect(t.GetBoundingBox()))
for t in b.GetTracks():index_track(t)
def clear(points,net,layer,width=.2):
    for s,e in zip(points,points[1:]):
        if any(segment_hits_box(s,e,box,width/2)for box in barriers):return False
        t=p.PCB_TRACK(b);t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetStart(p.VECTOR2I(p.FromMM(s[0]),p.FromMM(s[1])));t.SetEnd(p.VECTOR2I(p.FromMM(e[0]),p.FromMM(e[1])))
        shape=t.GetEffectiveShape(layer)
        for name,q in pad_index[layer].candidates(s,e,.6):
            if name!=net and shape.Collide(q.GetEffectiveShape(layer),p.FromMM(.151)):return False
        for name,z in track_index[layer].candidates(s,e,.6):
            if name!=net and shape.Collide(z.GetEffectiveShape(layer),p.FromMM(.151)):return False
    return True
def route(net,s,e,layer,description):
    pts=next((v for v in paths(s,e)if clear(v,net,layer)),None)
    if pts is None:
        for x in range(max(1,int(min(s[0],e[0]))-25),min(459,int(max(s[0],e[0]))+25)+1):
            v=[s,(x,s[1]),(x,e[1]),e]
            if clear(v,net,layer):pts=v;break
    if pts is None:
        for y in range(max(1,int(min(s[1],e[1]))-25),min(339,int(max(s[1],e[1]))+25)+1):
            v=[s,(s[0],y),(e[0],y),e]
            if clear(v,net,layer):pts=v;break
    if pts is None:
        # Finite native-collision-screened 1mm grid search. This changes only
        # the explicitly owned replacement branch, never old foreign copper.
        xmin=max(1,int(min(s[0],e[0]))-25);xmax=min(459,int(max(s[0],e[0]))+25)
        ymin=max(1,int(min(s[1],e[1]))-25);ymax=min(339,int(max(s[1],e[1]))+25)
        starts=[(x,y)for x in range(math.floor(s[0])-1,math.ceil(s[0])+2)for y in range(math.floor(s[1])-1,math.ceil(s[1])+2)if clear([s,(x,y)],net,layer)]
        goal=[(x,y)for x in range(math.floor(e[0])-1,math.ceil(e[0])+2)for y in range(math.floor(e[1])-1,math.ceil(e[1])+2)if clear([(x,y),e],net,layer)]
        queue=[];cost={};previous={};visited=set();end=None
        for point in starts:
            g=math.dist(s,point);cost[point]=g;previous[point]=None;heapq.heappush(queue,(g+math.dist(point,e),g,point))
        while queue and len(visited)<60000:
            _,g,point=heapq.heappop(queue)
            if point in visited:continue
            visited.add(point)
            if point in goal:end=point;break
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                other=(point[0]+dx,point[1]+dy)
                if other in visited or not(xmin<=other[0]<=xmax and ymin<=other[1]<=ymax):continue
                gg=g+math.hypot(dx,dy)
                if gg>=cost.get(other,float('inf'))or not clear([point,other],net,layer):continue
                cost[other]=gg;previous[other]=point;heapq.heappush(queue,(gg+math.dist(other,e),gg,other))
        if end is not None:
            grid=[]
            while end is not None:grid.append(end);end=previous[end]
            grid.reverse();raw=[s]+grid+[e];pts=[]
            for point in raw:
                if pts and math.dist(point,pts[-1])<1e-8:continue
                while len(pts)>=2 and abs((pts[-1][0]-pts[-2][0])*(point[1]-pts[-1][1])-(pts[-1][1]-pts[-2][1])*(point[0]-pts[-1][0]))<1e-8:pts.pop()
                pts.append(point)
    assert pts is not None,(description,s,e)
    ids=[]
    for start,end in zip(pts,pts[1:]):
        if math.dist(start,end)<1e-6:continue
        t=p.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(p.FromMM(.2));t.SetStart(p.VECTOR2I(p.FromMM(start[0]),p.FromMM(start[1])));t.SetEnd(p.VECTOR2I(p.FromMM(end[0]),p.FromMM(end[1])));b.Add(t);index_track(t);added.append(t.m_Uuid.AsString());ids.append(t.m_Uuid.AsString())
    route_receipts.append({'net':net,'layer':b.GetLayerName(layer),'points_mm':pts,'added_UUIDs':ids,'reason':description})
def pad(ref,pin):return next(z for z in fps[ref].Pads()if z.GetNumber()==pin)
for ref,(port,p1,p2)in cap_ports.items():
    for cp,hp in [('1',p1),('2',p2)]:
        q,r=pad(ref,cp),pad(port,hp);assert q.GetNetCode()==r.GetNetCode();route(q.GetNetname(),mm(q.GetPosition()),mm(r.GetPosition()),p.B_Cu,'Local existing Y2 capacitor to its actual shield/own-return terminal; AC-only domain boundary unchanged.')
for row in targets:
    q=pad(row['reference'],row['pin'])
    if row['reference']in ['J19531','J19534']:
        # Rejoin the external own-net endpoint on B.Cu, keeping the old shared
        # endpoint fixed. Both ends are manufacturer THT terminal lands.
        route(q.GetNetname(),mm(q.GetPosition()),row['external_old_endpoint'],p.B_Cu,'Rejoin moved shield terminal to its exact fixed CHASSIS endpoint without stretching through top-side foreign copper.')
    else:
        route(q.GetNetname(),mm(q.GetPosition()),row['external_old_endpoint'],p.F_Cu,'Rejoin relocated auxiliary field-return header to its exact fixed own-net endpoint; not a high-current-path qualification.')

dest=out/'motherboard-mate-access-candidate.kicad_pcb'
for f in source.parent.iterdir():
    if f.name.endswith('.pretty')or f.name=='3dmodels':shutil.copytree(f,out/f.name)
    elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
for suffix in ['.kicad_pro','.kicad_dru']:shutil.copyfile(source.with_suffix(suffix),dest.with_suffix(suffix))
p.SaveBoard(str(dest),b)
run=subprocess.run([str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','-o',str(out/'drc.json'),str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'drc.txt').write_text(run.stdout+run.stderr);assert run.returncode==0
fresh=p.LoadBoard(str(dest));fresh.BuildConnectivity();observed={f.GetReference():f for f in fresh.GetFootprints()};finaltracks={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()};allowed=set(poses)|set(cap_poses)
assert len(observed)==2688 and set(observed)==set(fps)
for ref,f in observed.items():
    assert collections.Counter(pad_template(z)for z in f.Pads())==templates[ref],ref
    for z in f.Pads():
        if ref not in allowed:assert piece(z)==oldpieces[ref,z.m_Uuid.AsString()],ref
        else:assert z.GetNetname()==oldpieces[ref,z.m_Uuid.AsString()][2],ref
assert set(finaltracks)==(set(oldtracks)-set(removed))|set(added)
assert all(finaltracks[u]==v for u,v in oldtracks.items()if u not in removed and u not in modified)
assert all(sha(Path(f))==h for f,h in before.items())
drc=json.loads((out/'drc.json').read_text());receipt={'input_hashes':before,'board_sha256':sha(dest),'physical_parts':2688,'track_via_items':len(finaltracks),'exact_header_poses':poses,'exact_Y2_coupling_cap_poses':cap_poses,'modified_copper':modified,'removed_private_copper':removed,'new_route_resources':route_receipts,'all_unrelated_pad_piece_geometry_and_copper_unchanged':True,'all_manufacturer_lands_and_pin_nets_preserved':True,'power_groups_applied':False,'power_group_latest_obstacle_hash':sha(recipe_path),'native_DRC_regular':len(drc['violations']),'native_DRC_types':dict(collections.Counter(v['type']for v in drc['violations'])),'ignored_checks':drc.get('ignored_checks',[]),'uncapped_missing_joins':fresh.GetConnectivity().GetUnconnectedCount(False),'manufacturing_ready':False}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');shutil.copyfile(__file__,out/'issued-tool.py');print(json.dumps({k:receipt[k]for k in ['physical_parts','track_via_items','native_DRC_regular','native_DRC_types','uncapped_missing_joins','exact_Y2_coupling_cap_poses']}));assert not drc['violations']and not drc.get('ignored_checks')
