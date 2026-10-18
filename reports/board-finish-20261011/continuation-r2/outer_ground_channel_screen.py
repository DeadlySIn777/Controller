"""Plan ordinary copper channels through same-domain outer ground pours.

In1/In4 reference copper and all retained tracks/pads/drills remain fixed. Only
prospective F/B LOGIC_GND fill cuts are modeled, and every cut is ledgered.
Native refill, retained plane contacts and power/return review remain mandatory.
"""
import ast,json,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import ordinary_routes as F
S=F.S;C=F.C;HERE=F.HERE;OUT=HERE/'outer-ground-channel-r1'
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
def main():
    OUT.mkdir(exist_ok=False);F.OUT=OUT;F.read(Path(__file__));start=time.time()
    prior=json.loads(F.read(HERE/'ordinary-routes-r1/result.json'));parts=json.loads(F.read(F.BASE/'measure/r07-four-fag-shared/partitions.json'));g=F.geometry();reserved=json.loads(F.read(F.C06/'alternate-r07/reserved-r07.json'));ex={}
    for line in F.read(F.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^\"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:ex[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    Base=F.exact_model_class();tree=ast.parse(F.read(Path(S.__file__)).decode());node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Model');method=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='free');outer=next(n for n in method.body if isinstance(n,ast.For));outer.body.insert(1,ast.parse("if layer in ('F.Cu','B.Cu') and r['kind']=='fill' and r.get('net')=='/LOGIC_GND' and r.get('domain')==domain: continue").body[0]);ns=dict(S.__dict__);exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'outer-ground-only-free','exec'),ns)
    class Model(Base):pass
    Model.free=ns['free'];model=Model(g,reserved,ex);F.write('ground-channel-derivation.json',{'exact_derived_free_source':ast.unparse(method),'only_changed_obstacle':'same-domain LOGIC_GND fills on F.Cu/B.Cu','reference_planes_changed':False,'retained_tracks_pads_holes_changed':False});refs={}
    for plane in ['In1.Cu','In4.Cu']:
        fill=unary_union([r['shape'] for r in model.records[plane] if r['kind']=='fill' and r['net']=='/LOGIC_GND']);conductive=unary_union([fill]+[r['shape'] for r in model.records[plane] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','track','via')]);anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][plane]));pieces=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms);refs[plane]=fill.intersection(unary_union([p for p in pieces if p.intersects(anchor)])).buffer(-.125)
    results=[];accepted=[];cumulative_cuts={'F.Cu':[],'B.Cu':[]}
    for old in prior['results']:
        if old['verdict']=='WITHHELD_GRAPH_MISMATCH':continue
        net=old['net'];target={'net':net,'domain':'DOM_LOGIC','c05_groups':parts['nets'][net],'lost_relationships':[{'r07_connected_pad_ids':sum(old['before_groups'],[])}]};groups=model.contact_groups(target);row={'net':net,'before_groups':old['before_groups'],'attempts':[],'paths':[]}
        for layer in ['F.Cu','B.Cu']:
            if any(layer not in group['layers'] for group in groups):continue
            aa,bb=[unary_union([r['shape'] for r in group['records'] if r['layer']==layer]) for group in groups];pa,pb=nearest_points(aa,bb)
            for margin in [5,20]:
                window=LineString([pa,pb]).envelope.buffer(margin,cap_style=3).envelope;free,_=model.free(target,layer,window);free=free.intersection(refs[S.REF_LAYER[layer]]);seeds=[S.seed_sites(group,layer,free,window) for group in groups];path,search=S.astar(free,*seeds,time.monotonic()+8,node_cap=140000) if all(seeds) else (None,{'reason':'no full-body-reference attachment','nodes':0});attempt={'layer':layer,'margin_mm':margin,'search':search};row['attempts'].append(attempt)
                if not path:continue
                cutter=LineString(path['points_mm']).buffer(.1+.15+.025,resolution=128);cuts=[];split=[]
                for r in model.records[layer]:
                    if r['kind']!='fill' or r['net']!='/LOGIC_GND' or not cutter.intersects(r['shape']):continue
                    cut=r['shape'].intersection(cutter);remaining=r['shape'].difference(unary_union(cumulative_cuts[layer]+[cutter]));pieces=[remaining] if remaining.geom_type=='Polygon' else [p for p in remaining.geoms if p.geom_type=='Polygon' and p.area>1e-10];cuts.append({'zone_uuid':r['uuid'],'layer':layer,'before_fill_piece_area_mm2':r['shape'].area,'cut_area_mm2':cut.area,'conservative_after_pieces':len(pieces),'cutter_wkt':cut.wkt})
                    if len(pieces)!=1:split.append({'zone_uuid':r['uuid'],'after_pieces':len(pieces)})
                attempt['prospective_ground_cuts']=cuts
                if split:attempt['withheld_plane_split']=split;continue
                path.update(layer=layer,width_mm=.2,new_vias=[],reference_layer=S.REF_LAYER[layer],reference_body_guard_mm=.025,prospective_outer_ground_cuts=cuts,source_anchor='J11001.2#0');row['paths'].append(path);cumulative_cuts[layer].append(cutter)
                for i,(a,b) in enumerate(zip(path['points_mm'],path['points_mm'][1:])):model.records[layer].append({'uuid':'GROUND_CHANNEL_'+net+'_'+str(i),'net':S.norm(net),'domain':'DOM_LOGIC','kind':'track','shape':LineString([a,b]).buffer(.1),'layer':layer,'key':('t','GROUND_CHANNEL_'+net+'_'+str(i)),'sites':[a,b]})
                model.trees[layer]=STRtree([r['shape'] for r in model.records[layer]]);accepted.append(row);break
            if row['paths']:break
        row['verdict']='HOST_PATH_PLANE_CONTACT_AUDIT_NATIVE_OPEN' if row['paths'] else 'FINITE_GROUND_CHANNEL_SEARCH_INCOMPLETE';results.append(row);F.write('progress.json',{'phase':'RUNNING','examined':len(results),'accepted':len(accepted),'last_net':net,'elapsed_seconds':time.time()-start});F.write('routes-checkpoint.json',{'results':results,'adopted':False});print(net,row['verdict'],flush=True)
    F.READS.update(S.READS)
    for p,h in F.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Input changed '+p)
    F.write('result.json',{'inputs':F.READS,'board_sha256':g['sha256'],'results':results,'accepted_count':len(accepted),'new_holes':0,'native_jobs':0,'adopted':False,'manufacturing_ready':False,'limits':['Bounded searches; no global impossibility claim','Every new outer-pour cut needs independent surviving-contact/return/current audit','Native refill/uncapped connectivity/DRC mandatory','In1/In4 geometry remains fixed']});F.write('progress.json',{'phase':'COMPLETE','examined':len(results),'accepted':len(accepted),'elapsed_seconds':time.time()-start})
if __name__=='__main__':main()
