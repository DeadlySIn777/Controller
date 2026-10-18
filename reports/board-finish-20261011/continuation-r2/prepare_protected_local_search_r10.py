"""Derive regional searches with global fallback, retaining every hard guard."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=H/'reroute_protected_on_latest_core_r9.py';dst=H/'reroute_protected_on_latest_core_r10.py';assert not dst.exists()
s=src.read_text(encoding='utf-8').replace("OUT=H/'protected24-on-corrected-core-r9'","OUT=H/'protected24-on-corrected-core-r10'")
s=s.replace('from shapely.geometry import Point,LineString','from shapely.geometry import Point,LineString,box')
s=s.replace('import tri_route as T','import tri_route as T\nfrom guarded_power_projection_r44 import bounded_buffer,bounded_disk')
start=s.index('        legal={};cached={};cachedtrees={}')
end=s.index("        for v in [v for v in new['vias']",start)
s=s[:start]+'''        padholes=[sh for p in h['pads'] if p['net']!=raw for sh in C.poly(p.get('hole') or [])]
        holetree=STRtree(padholes);foreignvias=[v for v in h['vias'] if v['net']!=raw]
        viatree=STRtree([Point(v['x'],v['y']) for v in foreignvias]);local_cache={}
        def local_options(ann,source):
            for width in (2.,1.,.5,.35,.25):
                for layer in LAYERS:
                    if source[layer].is_empty:continue
                    a,b=nearest_points(ann,source[layer]);ax,ay=a.coords[0];bx,by=b.coords[0]
                    for margin in (5.,15.,35.,75.,800.):
                        window=box(min(ax,bx)-margin,min(ay,by)-margin,max(ax,bx)+margin,max(ay,by)+margin)
                        scope=outline.intersection(window);obs=[]
                        for j in trees[layer].query(window.buffer(1.5),predicate='intersects'):
                            q=rec[layer][int(j)]
                            if q['net']==raw:continue
                            clearance=gap(raw,q['net'])+.025
                            if q['kind']=='via':obs.append(bounded_disk(q['source'],q['source']['d']/2+clearance))
                            elif q['kind']=='track':obs.append(bounded_buffer(LineString([q['source']['a'],q['source']['b']]),q['source']['w']/2+clearance))
                            else:obs.append(bounded_buffer(q['shape'],clearance))
                        obs += [bounded_buffer(q['shape'],gap(raw,q['net'])+.025) for q in bz+adds if q['layer']==layer and q['net']!=raw and not may_carve(q,raw) and q['shape'].intersects(window.buffer(1.5))]
                        obs += [bounded_buffer(padholes[int(j)],.275) for j in holetree.query(window.buffer(.3),predicate='intersects')]
                        obs += [bounded_disk(foreignvias[int(j)],foreignvias[int(j)]['drill']/2+.275) for j in viatree.query(window.buffer(2.),predicate='intersects')]
                        obs += [bounded_buffer(sh,.025) for rule in h['rule_areas'] if rule.get('no_zones') and layer in rule['layers'] for sh in C.poly(rule['outline']) if sh.intersects(window.buffer(.1))]
                        legalshape=set_precision(scope.difference(unary_union(obs)),1e-6)
                        parts=polys(legalshape.buffer(-width/2-.005));tree=STRtree(parts)
                        print('PROTECTED_R10_REGIONAL',bank,layer,width,margin,get_num_coordinates(legalshape),flush=True)
                        for j in tree.query(ann,predicate='intersects'):
                            part=parts[int(j)];inner=part.buffer(-.00002);aa=inner.intersection(ann);bb=inner.intersection(source[layer])
                            if aa.area>1e-8 and bb.area>1e-8:yield (aa.distance(bb),layer,width,part,aa,bb,legalshape,margin)
''' + s[end:]
start=s.index('            for layer in LAYERS:',s.index("        for v in [v for v in new['vias']"))
end=s.index('                if get_num_coordinates(part)>160000:',start)
s=s[:start]+'''            answer=None;option_count=0
            for distance,layer,width,part,aa,bb,legalshape,margin in local_options(ann,source):
                option_count+=1
''' + s[end:]
s=s.replace("if not legal[layer].buffer(.000001).covers(core)","if not legalshape.buffer(.000001).covers(core)")
s=s.replace(".intersection(legal[layer]))", ".intersection(legalshape))")
s=s.replace("'corrected-core-r8/'+layer", "'corrected-core-r10-local/'+layer")
s=s.replace("'search':search};print('PROTECTED_R8_ROOTED'", "'search':search,'regional_margin_mm':margin};print('PROTECTED_R10_ROOTED'")
s=s.replace("'eligible_same_layer_routes':len(options)", "'tested_eligible_same_layer_routes':option_count")
s=s.replace("print('PROTECTED_R8_FROZEN'", "print('PROTECTED_R10_FROZEN'")
# The bounded local constructors do not alter original definitions; their
# cut ledger still identifies every proposed return outline changed by replay.
s=s.replace("cutter=unary_union(bodies).buffer(.175)","cutter=bounded_buffer(unary_union(bodies),.175)")
dst.write_text(s,encoding='utf-8');compile(s,str(dst),'exec')
(H/'protected-local-search-r10-derivation.json').write_text(json.dumps({'source':str(src.resolve()),'source_sha256':sha(src),'derived':str(dst.resolve()),'derived_sha256':sha(dst),'changes':['Lazy regional5/15/35/75mm windows with whole-board800mm fallback','Spatially query all native/proposed Cu, drilled apertures and zone keepouts in each exact window','Use circumscribed256-edge plus2nm outward hard guards','Keep all12 dogbones/six nonconflicting bridges and replace only four invalid owned planes','Require actual full projected source join and all prior rooted contacts for each acceptance'],'no_new_resource_slot':True,'native_jobs':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
print(sha(dst))
