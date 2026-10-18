"""Finite two-via ordinary-signal screen with actual holes and rooted returns.

No native board is emitted. Every path has at most one dive and one return.
Prospective plane antipads and complete native continuity remain open gates.
"""
import json,math,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import ordinary_routes as F
S=F.S;C=F.C;HERE=F.HERE;OUT=HERE/'new-via-escape-r1'
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
def main():
    OUT.mkdir(exist_ok=False);F.OUT=OUT;F.read(Path(__file__));start=time.time()
    old=json.loads(F.read(HERE/'ordinary-routes-r1/result.json'));parts=json.loads(F.read(F.BASE/'measure/r07-four-fag-shared/partitions.json'));g=F.geometry();reserved=json.loads(F.read(F.C06/'alternate-r07/reserved-r07.json'));ex={}
    for line in F.read(F.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^\"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:ex[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    model=F.exact_model_class()(g,reserved,ex);refs={}
    for plane in ['In1.Cu','In4.Cu']:
        fill=unary_union([r['shape'] for r in model.records[plane] if r['kind']=='fill' and r['net']=='/LOGIC_GND']);conductive=unary_union([fill]+[r['shape'] for r in model.records[plane] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','track','via')]);anchor=unary_union(S.poly(model.pads['J11001.2#0']['layers'][plane]));pieces=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms);refs[plane]=fill.intersection(unary_union([p for p in pieces if p.intersects(anchor)]))
    safe={l:refs[S.REF_LAYER[l]].buffer(-.125) for l in S.LAYERS}
    returns=[v for v in g['vias'] if S.norm(v['net'])=='/LOGIC_GND' and {'In1.Cu','In4.Cu'}<=set(v['flashed']) and all(refs[p].intersects(Point(v['x'],v['y']).buffer(v['d']/2)) for p in refs)];rt=STRtree([Point(v['x'],v['y']) for v in returns]);allvt=STRtree([Point(v['x'],v['y']) for v in g['vias']]);smd=STRtree([p for pad in g['pads'] if pad['smd'] for layer,polys in pad['layers'].items() if layer in ['F.Cu','B.Cu'] for p in S.poly(polys)])
    no_vias=[unary_union(S.poly(a['outline'])) for a in g['rule_areas'] if a.get('no_vias')];nv=STRtree(no_vias);pitch_exempt=unary_union([p for fp in g['footprints'] if fp['ref'] in ['U1001','J15001','J15002'] for polys in fp['courtyard'].values() for p in S.poly(polys)])
    def via_site(at,net):
        point=Point(at);body=point.buffer(.25,resolution=64);hole=point.buffer(.1,resolution=64)
        if not model.outline.buffer(-.775).covers(point):return None
        if len(smd.query(hole.buffer(.125),predicate='intersects')) or len(nv.query(body.buffer(.025),predicate='intersects')):return None
        if not pitch_exempt.covers(point) and len(allvt.query(point.buffer(.8-1e-8),predicate='intersects')):return None
        options=[(point.distance(Point(returns[i]['x'],returns[i]['y'])),returns[i]) for i in rt.query(point.buffer(1),predicate='intersects')]
        if not options:return None
        distance,return_via=min(options,key=lambda x:x[0]);cuts=[]
        for layer in g['copper_layers']:
            for i in model.trees[layer].query(body.buffer(.65),predicate='intersects'):
                r=model.records[layer][i]
                if r['kind']=='hole':
                    if hole.distance(r['shape'])<.25+.025:return None
                elif r.get('net')==S.norm(net):continue
                elif r['kind']=='fill' and r.get('domain')=='DOM_LOGIC':
                    if body.buffer(.175).intersects(r['shape']):cuts.append({'zone_uuid':r['uuid'],'layer':layer,'net':r['net'],'antipad_radius_mm':.425})
                else:
                    required=.15 if r.get('domain')=='DOM_LOGIC' else .6
                    if body.distance(r['shape'])<required+.025:return None
            for r in model.hard[layer]:
                if S.norm(net) not in r['exempt'] and body.buffer(.025).intersects(r['shape']):return None
        if not all(refs[p].buffer(-.125).covers(point) for p in refs):return None
        return {'at':list(at),'diameter_mm':.5,'drill_mm':.2,'return_via_uuid':return_via['uuid'],'return_at':[return_via['x'],return_via['y']],'return_distance_mm':distance,'return_reference_planes':['In1.Cu','In4.Cu'],'source_anchor':'J11001.2#0','prospective_antipads':cuts,'D4_pitch_exception':pitch_exempt.covers(point)}
    results=[];accepted=[]
    for row in old['results']:
        if row['paths'] or row['nearest_pad_body_gap_mm']>90:continue
        net=row['net'];target={'net':net,'domain':'DOM_LOGIC','c05_groups':parts['nets'][net],'lost_relationships':[{'r07_connected_pad_ids':sum(row['before_groups'],[])}]};groups=model.contact_groups(target);record={'net':net,'before_groups':row['before_groups'],'sides':[],'paths':[]};sides=[]
        for group in groups:
            options=[];stats=[]
            for layer in ['F.Cu','B.Cu']:
                if layer not in group['layers']:continue
                own=unary_union([r['shape'] for r in group['records'] if r['layer']==layer]);other=unary_union([r['shape'] for gr in groups if gr is not group for r in gr['records'] if r['layer'] in ['F.Cu','B.Cu']]);pa,pb=nearest_points(own,other);window=own.envelope.intersection(Point(pa).buffer(10).envelope).buffer(3,cap_style=3).envelope;free,_=model.free(target,layer,window);free=free.intersection(safe[layer]);seeds=S.seed_sites(group,layer,free,window);polys=[free] if free.geom_type=='Polygon' else [p for p in free.geoms if p.geom_type=='Polygon'];reachable=unary_union([p for p in polys if any(p.covers(Point(at)) for at,_ in seeds)]);sites=[]
                if reachable.is_empty:stats.append({'layer':layer,'seeds':len(seeds),'legal_sites':0});continue
                bounds=reachable.bounds;points=[]
                for ix in range(math.ceil(bounds[0]*5),math.floor(bounds[2]*5)+1):
                    for iy in range(math.ceil(bounds[1]*5),math.floor(bounds[3]*5)+1):
                        at=(ix/5,iy/5)
                        if reachable.covers(Point(at)):points.append(at)
                points.sort(key=lambda at:Point(at).distance(other)+Point(at).distance(own)*.25)
                for at in points[:5000]:
                    if len(sites)>=8:break
                    if any(math.dist(at,s['at'])<.6 for s in sites):continue
                    site=via_site(at,net)
                    if site:sites.append(site)
                stats.append({'layer':layer,'seeds':len(seeds),'legal_sites':len(sites),'sampled_nodes':len(points)})
                for site in sites:
                    fake={'uuid':'planned-via-'+repr(site['at']),'kind':'via'};path,search=S.astar(free,seeds,[(site['at'],fake)],time.monotonic()+3,node_cap=40000)
                    if path:options.append({'outer_layer':layer,'via':site,'outer_path':path})
            sides.append(options);record['sides'].append(stats)
        if all(sides):
            pairs=sorted([(math.dist(a['via']['at'],b['via']['at']),a,b) for a in sides[0] for b in sides[1]],key=lambda x:x[0]);a0,b0=pairs[0][1:];window=LineString([a0['via']['at'],b0['via']['at']]).envelope.buffer(20,cap_style=3).envelope;free,_=model.free(target,'In3.Cu',window);free=free.intersection(safe['In3.Cu'])
            starts=[(s['via']['at'],{'uuid':str(i),'kind':'planned_via'}) for i,s in enumerate(sides[0])];goals=[(s['via']['at'],{'uuid':str(i),'kind':'planned_via'}) for i,s in enumerate(sides[1])];inner,search=S.astar(free,starts,goals,time.monotonic()+12,node_cap=180000);record['inner_search']=search
            if inner:
                a=sides[0][int(inner['source_uuid'])];b=sides[1][int(inner['target_uuid'])];record['paths']=[{'source_escape':a,'inner_path':inner,'target_escape':b,'new_signal_vias':[a['via'],b['via']],'segments_of_layers':3,'new_return_vias':0,'inner_reference':'In4.Cu'}];accepted.append(record)
                # Stop after the first path: separate exact audit and native
                # refill are needed before treating its plane cuts as harmless.
        record['verdict']='HOST_PATH_REQUIRES_EXACT_AUDIT_NATIVE_OPEN' if record['paths'] else 'FINITE_TWO_VIA_ESCAPE_INCOMPLETE';results.append(record);F.write('progress.json',{'phase':'RUNNING','examined':len(results),'accepted':len(accepted),'last_net':net,'elapsed_seconds':time.time()-start});F.write('routes-checkpoint.json',{'results':results,'adopted':False});print(net,record['verdict'],flush=True)
        if accepted:break
    F.READS.update(S.READS)
    for p,h in F.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Input changed '+p)
    F.write('result.json',{'inputs':F.READS,'board_sha256':g['sha256'],'results':results,'accepted_count':len(accepted),'native_jobs':0,'board_emitted':False,'adopted':False,'limits':['Bounded .2mm site grid and windows; no impossibility claim','Full actual annuli, all-layer copper/hole/native/reserved keepouts modeled','Native refill and every displaced plane contact remain mandatory','Ordinary class NONE only; In3 electrical return review remains open']});F.write('progress.json',{'phase':'COMPLETE','examined':len(results),'accepted':len(accepted),'elapsed_seconds':time.time()-start})
if __name__=='__main__':main()
