"""Replan the sensor control with its full copper body over rooted In1."""
import json,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
import ordinary_routes as F
S=F.S;C=F.C;OUT=F.HERE/'sensor-full-reference-r1'
from shapely.geometry import LineString
from shapely.ops import unary_union,nearest_points
def main():
    OUT.mkdir(exist_ok=False);F.OUT=OUT;F.read(Path(__file__))
    prior=json.loads(F.read(F.HERE/'ordinary-routes-r1/result.json'));row=next(r for r in prior['results'] if r['paths']);parts=json.loads(F.read(F.BASE/'measure/r07-four-fag-shared/partitions.json'))
    g=F.geometry();reserved=json.loads(F.read(F.C06/'alternate-r07/reserved-r07.json'));ex={}
    for line in F.read(F.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^\"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:ex[m[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    model=F.exact_model_class()(g,reserved,ex);layer='F.Cu';plane='In1.Cu';anchor=model.pads['J11001.2#0']
    fill=unary_union([r['shape'] for r in model.records[plane] if r['kind']=='fill' and r['net']=='/LOGIC_GND']);conductive=unary_union([fill]+[r['shape'] for r in model.records[plane] if r.get('net')=='/LOGIC_GND' and r['kind'] in ('pad','track','via')]);a=unary_union(S.poly(anchor['layers'][plane]));pieces=[conductive] if conductive.geom_type=='Polygon' else list(conductive.geoms);ref=fill.intersection(unary_union([p for p in pieces if p.intersects(a)]));safe=ref.buffer(-.125)
    net=row['net'];target={'net':net,'domain':'DOM_LOGIC','c05_groups':parts['nets'][net],'lost_relationships':[{'r07_connected_pad_ids':sum(row['before_groups'],[])}]};groups=model.contact_groups(target);aa,bb=[unary_union([r['shape'] for r in gr['records'] if r['layer']==layer]) for gr in groups];pa,pb=nearest_points(aa,bb);attempts=[];paths=[]
    for grow in [5,18,30]:
        window=LineString([pa,pb]).envelope.buffer(grow,cap_style=3).envelope;free,_=model.free(target,layer,window);free=free.intersection(safe);seeds=[S.seed_sites(gr,layer,free,window) for gr in groups];path,search=S.astar(free,*seeds,time.monotonic()+15,node_cap=200000) if all(seeds) else (None,{'reason':'no full-reference attachment'})
        attempts.append({'window_margin_mm':grow,'seed_counts':[len(s) for s in seeds],'search':search})
        if path:
            body=LineString(path['points_mm']).buffer(.1,resolution=128)
            if body.difference(ref).area>1e-8:raise ValueError('Body escaped source reference')
            path.update(layer=layer,width_mm=.2,new_vias=[],reference_layer=plane,source_anchor='J11001.2#0',reference_body_uncovered_mm2=body.difference(ref).area);paths.append(path);break
    F.READS.update(S.READS)
    for p,h in F.READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Input changed '+p)
    F.write('result.json',{'verdict':'HOST_PATH_NATIVE_OPEN' if paths else 'FINITE_FULL_BODY_REFERENCE_SEARCH_INCOMPLETE','inputs':F.READS,'board_sha256':g['sha256'],'results':[dict(row,paths=paths,layers=attempts)],'native_drc':False,'adopted':False})
    print(json.dumps({'paths':len(paths),'attempts':attempts}),flush=True)
if __name__=='__main__':main()
