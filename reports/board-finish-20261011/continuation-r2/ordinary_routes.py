"""Additive ordinary-digital routing on the freshly filled exact 198b board."""
import ast,collections,hashlib,json,math,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;C06=BASE/'recovery-composite/c06'
sys.path.insert(0,str(C06));sys.path.insert(0,str(BASE))
import screen_c06 as S
import compose_additions as C
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
SOURCE=BASE/'power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb'
OUT=HERE/'ordinary-routes-r1';READS={}
def read(p):
    p=Path(p).resolve();raw=p.read_bytes();READS[str(p)]=hashlib.sha256(raw).hexdigest();return raw
def write(name,data):
    tmp=OUT/(name+'.part');tmp.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8');tmp.replace(OUT/name)
def polys(v):return [[p[0],p[1:]] for p in v]
def exact_model_class():
    tree=ast.parse(read(Path(S.__file__)).decode('utf-8'));node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Model');changed=0
    for outer in ast.walk(node):
        if isinstance(outer,ast.For) and isinstance(outer.target,ast.Name) and outer.target.id=='via':
            inner=next(n for n in outer.body if isinstance(n,ast.For));assert len(inner.body)==4
            # The drill crosses every layer. Copper only exists where native
            # FlashLayer reports an annulus; retain holes outside the condition.
            inner.body=[ast.If(test=ast.Compare(left=ast.Name(id='layer',ctx=ast.Load()),ops=[ast.In()],comparators=[ast.Subscript(value=ast.Name(id='via',ctx=ast.Load()),slice=ast.Constant(value='flashed'),ctx=ast.Load())]),body=inner.body[:3],orelse=[]),inner.body[3]];changed+=1
    if changed!=1:raise ValueError('Native-annulus model derivation did not match exactly')
    namespace=dict(S.__dict__);module=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]));exec(compile(module,'fresh-native-annulus-model','exec'),namespace)
    write('model-derivation.json',{'original_model_sha256':READS[str(Path(S.__file__).resolve())],'constructor_changes':1,'via_copper_uses_native_flashed_layers':True,'via_drills_still_cross_every_copper_layer':True,'derived_model_source':ast.unparse(node)})
    return namespace['Model']
def geometry():
    rec=json.loads(read(HERE/'native-198b-geometry/receipt.json'));native=json.loads(read(HERE/'native-198b-geometry/geometry.json'));flashes=json.loads(read(HERE/'native-198b-geometry/actual-via-flashes.json'))
    if rec['verdict']!='PASS' or not rec['fresh_fill_in_memory'] or rec['board_saved']:raise ValueError('Invalid current native export')
    for p,h in rec['outputs'].items():
        if hashlib.sha256(read(p)).hexdigest()!=h:raise ValueError('Native export output changed')
    raw=read(SOURCE);old=read(S.overlay_tool.base.BASE);before,after=C.inventory(old),C.inventory(raw)
    if hashlib.sha256(raw).hexdigest()!=flashes['board_sha256']:raise ValueError('Native candidate mismatch')
    if before[0]!=after[0] or before[2]!=after[2] or before[5]!=after[5]:raise ValueError('Full inherited pad/graphic/non-copper geometry no longer exact')
    g=json.loads(read(S.overlay_tool.base.GEOM));arcs={t['uuid']:t for t in g['tracks'] if t.get('kind')=='arc'};tracks=[];vias=[]
    for uid,ch in after[4].items():
        kind=C.pcbtext.chunk_kind(ch)
        if kind=='segment':tracks.append({'uuid':uid,'net':S.overlay_tool.netname(ch),'a':S.overlay_tool.numbers(ch,'start'),'b':S.overlay_tool.numbers(ch,'end'),'w':S.overlay_tool.scalar(ch,'width'),'layer':C.pcbtext.chunk_layer(ch)})
        elif kind=='via':
            x,y=S.overlay_tool.numbers(ch,'at');vias.append({'uuid':uid,'net':S.overlay_tool.netname(ch),'x':x,'y':y,'d':S.overlay_tool.scalar(ch,'size'),'drill':S.overlay_tool.scalar(ch,'drill'),'flashed':flashes['vias'][uid]})
        elif uid in arcs and before[4].get(uid)==ch:tracks.append(arcs[uid])
        else:raise ValueError('Unmodeled changed arc')
    if len(tracks)!=len(native['tracks']) or len(vias)!=len(native['vias']):raise ValueError('Native/source copper counts differ')
    nt={t['uuid']:t for t in native['tracks']};nv={v['uuid']:v for v in native['vias']}
    for t in tracks:
        if t.get('kind')!='arc' and any(t[a]!=nt[t['uuid']][b] for a,b in [('a','s'),('b','e'),('w','w'),('net','net'),('layer','layer')]):raise ValueError('Native/source segment mismatch')
    for v in vias:
        n=nv[v['uuid']]
        if [v['x'],v['y']]!=n['at'] or v['d']!=n['w'] or v['drill']!=n['drill'] or v['net']!=n['net']:raise ValueError('Native/source via mismatch')
    g.update(tracks=tracks,vias=vias,board=str(SOURCE),sha256=flashes['board_sha256'],refilled=True)
    oldzones={z['uuid']:z for z in g['zones']}
    if set(oldzones)!={z['uuid'] for z in native['zones']}:raise ValueError('Unmodeled zone set')
    for z in g['zones']:z['fills']={layer:polys(p) for layer,p in next(n for n in native['zones'] if n['uuid']==z['uuid'])['fills'].items()}
    g['domains_normalized']={S.norm(n):v for n,v in g['nets'].items()}
    return g
def main():
    OUT.mkdir(exist_ok=False);started=time.time();read(Path(__file__))
    for p in [Path(C.__file__),Path(C.pcbtext.__file__),Path(S.overlay_tool.__file__),Path(S.overlay_tool.base.__file__),S.CONTROLLED]:read(p)
    census=json.loads(read(HERE/'remaining-net-census-r2.json'));parts=json.loads(read(BASE/'measure/r07-four-fag-shared/partitions.json'))
    g=geometry();reserved=json.loads(read(C06/'alternate-r07/reserved-r07.json'));dru=read(C06/'alternate-r07/reserve/board.kicad_dru').decode();exemptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exemptions[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    print('Building fresh exact-annulus geometry model',flush=True);Model=exact_model_class();model=Model(g,reserved,exemptions)
    # Fresh fill contours, real flashed annuli and exact inherited copper form
    # the reference network on each adjacent plane, anchored at the input return.
    refs={};anchor=model.pads['J11001.2#0'];refstats={}
    for layer in ['In1.Cu','In4.Cu']:
        fill=unary_union([r['shape'] for r in model.records[layer] if r['kind']=='fill' and r['net']=='/LOGIC_GND'])
        own=[r['shape'] for r in model.records[layer] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','track','via')]
        conductive=unary_union([fill]+own);a=unary_union(S.poly(anchor['layers'][layer]));pieces=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms)
        anchored=unary_union([p for p in pieces if p.intersects(a)]);refs[layer]=fill.intersection(anchored);refstats[layer]={'source_pad':'J11001.2#0','source_uuid':anchor['uuid'],'source_connected_fill_area_mm2':refs[layer].area}
    print('Fresh source references ready',flush=True);candidates=[];excluded=[]
    clock=re.compile(r'(CLK|SCLK|SCK|XTAL|OSC|USB|HDMI|MDI|_SW$|PHASE|BOOT|VREF|DVDT|ILIM|AGND|_COM$)',re.I)
    for row in census['rows']:
        net=row['net'];n=S.norm(net)
        if row['category']!='ordinary_digital_catalog' or g['domains_normalized'].get(n)!='DOM_LOGIC' or clock.search(n):continue
        groups=parts['nets'][net];shapes=[unary_union([p for pid in gr for layer in ['F.Cu','B.Cu'] for p in S.poly(model.pads[pid]['layers'].get(layer,[]))]) for gr in groups]
        best=min((a.distance(b),i,j) for i,a in enumerate(shapes) for j,b in enumerate(shapes) if i<j)
        candidates.append((best[0],net,best[1],best[2]))
    results=[];accepted=[]
    for distance,net,gi,gj in sorted(candidates):
        groups=parts['nets'][net];target={'net':net,'domain':'DOM_LOGIC','c05_groups':groups,'lost_relationships':[{'r07_connected_pad_ids':groups[gi]+groups[gj]}]}
        record={'net':net,'before_groups':[groups[gi],groups[gj]],'nearest_pad_body_gap_mm':distance,'layers':[],'paths':[]}
        try:contacts=model.contact_groups(target)
        except ValueError as exc:record.update(verdict='WITHHELD_GRAPH_MISMATCH',reason=str(exc));results.append(record);continue
        for layer in ['F.Cu','B.Cu']:
            if any(layer not in gr['layers'] for gr in contacts):continue
            a,b=[unary_union([r['shape'] for r in gr['records'] if r['layer']==layer]) for gr in contacts];pa,pb=nearest_points(a,b)
            for margin in [4,14]:
                window=LineString([pa,pb]).envelope.buffer(margin,cap_style=3).envelope;free,blockers=model.free(target,layer,window);ref_layer=S.REF_LAYER[layer];free=free.intersection(refs[ref_layer]);seeds=[S.seed_sites(gr,layer,free,window) for gr in contacts]
                path,search=S.astar(free,seeds[0],seeds[1],time.monotonic()+5,node_cap=80000) if all(seeds) else (None,{'reason':'no source-reference-covered attachment','nodes':0})
                record['layers'].append({'layer':layer,'margin_mm':margin,'seed_counts':[len(v) for v in seeds],'search':search})
                if not path:continue
                if not free.covers(LineString(path['points_mm'])):raise ValueError('Rounded emitted path escaped exact free geometry')
                path.update(layer=layer,width_mm=.2,new_vias=[],reference_layer=ref_layer,source_anchor='J11001.2#0');record['paths'].append(path)
                for i,(a,b) in enumerate(zip(path['points_mm'],path['points_mm'][1:])):
                    r={'uuid':'ORDINARY_NEW_'+net+'_'+str(i),'net':S.norm(net),'domain':'DOM_LOGIC','kind':'track','shape':LineString([a,b]).buffer(.1),'layer':layer,'key':('t','ORDINARY_NEW_'+net+'_'+str(i)),'sites':[a,b]};model.records[layer].append(r)
                model.trees[layer]=STRtree([r['shape'] for r in model.records[layer]]);accepted.append(record);break
            if record['paths']:break
        record['verdict']='HOST_PATH_NATIVE_OPEN' if record['paths'] else 'NO_PATH_IN_CURRENT_TWO_WINDOWS';results.append(record)
        write('progress.json',{'phase':'RUNNING','examined':len(results),'total_candidates':len(candidates),'accepted':len(accepted),'last_net':net,'last_verdict':record['verdict'],'elapsed_seconds':time.time()-started})
        write('routes-checkpoint.json',{'board_sha256':g['sha256'],'results':results,'native_jobs':0,'adopted':False});print(net,record['verdict'],flush=True)
    READS.update(S.READS)
    for p,h in READS.items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:raise ValueError('Routing input changed '+p)
    report={'board_sha256':g['sha256'],'source_files_sha256':READS,'results':results,'candidate_count':len(candidates),'accepted_count':len(accepted),'reference_witnesses':refstats,'geometry_fresh_native':True,'actual_via_annuli_used':True,'track_clearance_mm':.15,'cross_domain_clearance_mm':.6,'hole_clearance_mm':.25,'planning_margin_mm':.025,'no_existing_copper_changes':True,'new_vias':0,'native_drc_run':False,'board_emitted':False,'adopted':False,'limits':['One shortest relationship per eligible DOM_LOGIC ordinary catalog net in this pass; all enumerated candidates attempted.','Two finite windows per layer; failed searches are not global impossibility claims.','Frozen router reservations retained.','Routes need independent vector/native checks and both-baseline continuity before integration.']}
    write('result.json',report);write('progress.json',{'phase':'COMPLETE','accepted':len(accepted),'examined':len(results),'elapsed_seconds':time.time()-started});print(json.dumps({'accepted':len(accepted),'examined':len(results),'result':str(OUT/'result.json')}),flush=True)
if __name__=='__main__':main()
