"""Use qualified, already-flashed retained vias to access spare routing layers."""
import ast,hashlib,json,math,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import ordinary_routes as F
S=F.S;C=F.C;HERE=F.HERE;BASE=F.BASE;C06=F.C06
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
OUT=HERE/'retained-via-routes-r1'
def main():
    OUT.mkdir(exist_ok=False);F.OUT=OUT;F.read(Path(__file__));started=time.time()
    for p in [Path(F.__file__),Path(C.__file__),Path(C.pcbtext.__file__),Path(S.overlay_tool.__file__),Path(S.overlay_tool.base.__file__),S.CONTROLLED]:F.read(p)
    prior=json.loads(F.read(HERE/'ordinary-routes-r1/result.json'));parts=json.loads(F.read(BASE/'measure/r07-four-fag-shared/partitions.json'));g=F.geometry()
    reserved=json.loads(F.read(C06/'alternate-r07/reserved-r07.json'));dru=F.read(C06/'alternate-r07/reserve/board.kicad_dru').decode();exemptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exemptions[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    prior_paths=[r for r in prior['results'] if r['paths']]
    for row in prior_paths:
        for path in row['paths']:
            for i,(a,b) in enumerate(zip(path['points_mm'],path['points_mm'][1:])):g['tracks'].append({'uuid':'FIRST_'+row['net']+'_'+str(i),'net':row['net'],'a':a,'b':b,'w':.2,'layer':path['layer']})
    Exact=F.exact_model_class();tree=ast.parse(F.read(Path(S.__file__)).decode('utf-8'));node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Model');method=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='contact_groups');count=0
    for n in ast.walk(method):
        if isinstance(n,ast.Tuple) and [x.value for x in n.elts if isinstance(x,ast.Constant)]==['track','pad']:
            n.elts.append(ast.Constant(value='via'));count+=1
    if count!=1:raise ValueError('Retained-layer access derivation mismatch')
    namespace=dict(S.__dict__);exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'retained-layer-access','exec'),namespace)
    class Access(Exact):pass
    Access.contact_groups=namespace['contact_groups'];model=Access(g,reserved,exemptions)
    F.write('retained-access-derivation.json',{'changed_conditions':1,'only_actual_flashed_annuli_available':True,'drills_added':0,'contact_method_source':ast.unparse(method)})
    refs={};source=model.pads['J11001.2#0']
    for layer in ['In1.Cu','In4.Cu']:
        fill=unary_union([r['shape'] for r in model.records[layer] if r['kind']=='fill' and r['net']=='/LOGIC_GND']);own=[r['shape'] for r in model.records[layer] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','track','via')];conductive=unary_union([fill]+own);anchor=unary_union(S.poly(source['layers'][layer]));pieces=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms);refs[layer]=fill.intersection(unary_union([p for p in pieces if p.intersects(anchor)]))
    ground=[v for v in g['vias'] if S.norm(v['net'])=='/LOGIC_GND' and {'In1.Cu','In4.Cu'}<=set(v['flashed']) and all(refs[l].intersects(Point(v['x'],v['y']).buffer(v['d']/2)) for l in refs)];gt=STRtree([Point(v['x'],v['y']) for v in ground]);vm={v['uuid']:v for v in g['vias']};buddy={}
    smd=[r['shape'] for p in g['pads'] if p['smd'] for l,poly in p['layers'].items() if l in ['F.Cu','B.Cu'] for r in [{'shape':unary_union(S.poly(poly))}]];st=STRtree(smd)
    for v in g['vias']:
        if S.norm(v['net'])=='/LOGIC_GND':continue
        p=Point(v['x'],v['y']);drill=p.buffer(v['drill']/2+.025)
        if len(st.query(drill,predicate='intersects')):continue
        options=[(p.distance(Point(ground[i]['x'],ground[i]['y'])),ground[i]) for i in gt.query(p.buffer(1),predicate='intersects')]
        if options:
            dist,rv=min(options,key=lambda x:x[0]);buddy[v['uuid']]={'uuid':rv['uuid'],'at':[rv['x'],rv['y']],'distance_mm':dist,'source_anchor':'J11001.2#0','actual_reference_flashes':rv['flashed']}
    print('Qualified retained signal vias',len(buddy),flush=True);results=[];accepted=[]
    for old in prior['results']:
        if old['paths'] or old['verdict']=='WITHHELD_GRAPH_MISMATCH':continue
        net=old['net'];gr=old['before_groups'];groups=parts['nets'][net];target={'net':net,'domain':'DOM_LOGIC','c05_groups':groups,'lost_relationships':[{'r07_connected_pad_ids':gr[0]+gr[1]}]};record={'net':net,'before_groups':gr,'layers':[],'paths':[]}
        contacts=model.contact_groups(target)
        for layer in ['F.Cu','B.Cu','In3.Cu']:
            if any(layer not in cg['layers'] for cg in contacts):continue
            allowed=[r for cg in contacts for r in cg['records'] if r['layer']==layer and r['kind']=='via' and r['uuid'] in buddy];allowance=unary_union([Point(vm[r['uuid']]['x'],vm[r['uuid']]['y']).buffer(vm[r['uuid']]['d']/2+.15+.025) for r in allowed]);ref=refs[S.REF_LAYER[layer]].union(allowance)
            aa,bb=[unary_union([r['shape'] for r in cg['records'] if r['layer']==layer and (r['kind']!='via' or r['uuid'] in buddy)]) for cg in contacts]
            if aa.is_empty or bb.is_empty:continue
            pa,pb=nearest_points(aa,bb)
            for margin in [5,18]:
                window=LineString([pa,pb]).envelope.buffer(margin,cap_style=3).envelope;free,_=model.free(target,layer,window);free=free.intersection(ref);filtered=[dict(cg,records=[r for r in cg['records'] if r['kind']!='via' or r['uuid'] in buddy]) for cg in contacts];seeds=[S.seed_sites(cg,layer,free,window) for cg in filtered]
                path,search=S.astar(free,seeds[0],seeds[1],time.monotonic()+7,node_cap=100000) if all(seeds) else (None,{'reason':'no qualified attachment','nodes':0});record['layers'].append({'layer':layer,'window_margin_mm':margin,'seed_counts':[len(x) for x in seeds],'search':search})
                if not path:continue
                if not free.covers(LineString(path['points_mm'])):raise ValueError('Serialized retained-via route escaped free geometry')
                endpoint_vias=[u for u,k in [(path['source_uuid'],path['source_kind']),(path['target_uuid'],path['target_kind'])] if k=='via']
                if any(u not in buddy or layer not in vm[u]['flashed'] for u in endpoint_vias):raise ValueError('Retained endpoint lacks actual flash/qualified return')
                path.update(layer=layer,width_mm=.2,new_vias=[],retained_endpoint_returns={u:buddy[u] for u in endpoint_vias},reference_layer=S.REF_LAYER[layer],reference_antipad_allowances=[{'uuid':r['uuid'],'radius_mm':vm[r['uuid']]['d']/2+.15+.025,'return':buddy[r['uuid']]} for r in allowed],source_anchor='J11001.2#0');record['paths'].append(path)
                for i,(a,b) in enumerate(zip(path['points_mm'],path['points_mm'][1:])):model.records[layer].append({'uuid':'ACCESS_'+net+'_'+str(i),'net':S.norm(net),'domain':'DOM_LOGIC','kind':'track','shape':LineString([a,b]).buffer(.1),'layer':layer,'key':('t','ACCESS_'+net+'_'+str(i)),'sites':[a,b]})
                model.trees[layer]=STRtree([r['shape'] for r in model.records[layer]]);accepted.append(record);break
            if record['paths']:break
        record['verdict']='HOST_PATH_NATIVE_OPEN' if record['paths'] else 'NO_PATH_WITH_QUALIFIED_RETAINED_VIA_ACCESS';results.append(record);F.write('progress.json',{'phase':'RUNNING','examined':len(results),'accepted':len(accepted),'last_net':net,'last_verdict':record['verdict'],'elapsed_seconds':time.time()-started});F.write('routes-checkpoint.json',{'board_sha256':g['sha256'],'results':results,'native_drc':False,'adopted':False});print(net,record['verdict'],flush=True)
    F.READS.update(S.READS)
    for p,h in F.READS.items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:raise ValueError('Input changed '+p)
    F.write('result.json',{'board_sha256':g['sha256'],'inputs':F.READS,'prior_paths_obstructing_later_nets':len(prior_paths),'results':results,'accepted_count':len(accepted),'qualified_existing_signal_vias':len(buddy),'new_holes':0,'new_vias':0,'new_plane_cutters':0,'retained_via_antipads_used_only_with_source_connected_return_within_mm':1,'board_emitted':False,'native_drc':False,'adopted':False,'limits':['Finite windows; failures are not global impossibility.','Only ordinary catalog class NONE nets previously selected.','In3 reference/SI remains a native and electrical review obligation.','Existing via-drill/solder-land overlaps were excluded geometrically; full assembly rules remain separate.','Native refill/continuity/DRC still mandatory.']});F.write('progress.json',{'phase':'COMPLETE','examined':len(results),'accepted':len(accepted),'elapsed_seconds':time.time()-started})
if __name__=='__main__':main()
