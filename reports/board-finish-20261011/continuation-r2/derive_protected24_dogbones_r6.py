"""Rebind protected fanouts to corrected returns and cache exact free components."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=H/'construct_protected24_dogbones_r5.py';dst=H/'construct_protected24_dogbones_r6.py';assert not dst.exists()
    code=src.read_text(encoding='utf-8')
    replacements={"OUT=ROOT/'protected24-dogbones-r5'":"OUT=ROOT/'protected24-dogbones-r6'","controller-protected24-dogbone-r5/":"controller-protected24-dogbone-r6/",
      "g={**g,'vias':g['vias']+r8discrete['vias'],'tracks':g['tracks']+r8discrete['tracks']+r9tracks};planes=baseplanes+r6adds+r8zones;":"audit19=HERE/'repaired-local-return-audit-r19';a19=json.loads((audit19/'receipt.json').read_bytes());assert a19['verdict'].startswith('PASS_');assert sha(audit19/'geometry.pkl')=='38882eeb997cfe1836314af74532bc497704548af8c8e9b1851607c2a92fff1c' and sha(audit19/'proposed-zones.pkl')=='5a7f01028ab438998bf15955ec0903a5a6a4bee280de954a0216e427004d0dae';g=pickle.loads((audit19/'geometry.pkl').read_bytes());planes=pickle.loads((audit19/'proposed-zones.pkl').read_bytes());baseplanes=planes;",
      "r9p/'receipt.json',r9p/'proposed-tracks.pkl')":"r9p/'receipt.json',r9p/'proposed-tracks.pkl',audit19/'receipt.json',audit19/'geometry.pkl',audit19/'proposed-zones.pkl')",
      "currentgroups=F.graph(g,net);currentroot=":"currentgroups=F.graph(g,net);currentroot=",
    }
    for old,new in replacements.items():
        assert code.count(old)==1,(old,code.count(old));code=code.replace(old,new)
    old="source={l:unary_union([q['shape'] for q in currentroot if q['layer']==l and (q['kind']!='fill' or q['uuid'] in sameids)]) for l in INNER};"
    new="ownholes={q['uuid']:q['shape'] for q in drills if q['net']==raw};source={l:unary_union([q['shape'].difference(ownholes.get(q['uuid'],Point().buffer(0))) for q in currentroot if q['layer']==l and (q['kind']!='fill' or q['uuid'] in sameids)]) for l in INNER};"
    assert code.count(old)==1;code=code.replace(old,new)
    begin=code.index('        def bridge(point,disk,hole):');end=code.index('        wanted=',begin)
    bridge='''        cached=[]
        for l in INNER:
            if source[l].is_empty:continue
            cuts=[q[1] for q in obstacles[l]]+[q['shape'].buffer(gap(q['net'])+.025) for q in adds if q['layer']==l and C.norm(q['net'])!=net]
            legal=set_precision(outline.difference(unary_union(cuts)),1e-6)
            for width in (2.,1.,.5):
                count=0
                for part in polys(legal.buffer(-width/2-.005)):
                    goal=part.buffer(-.00002).intersection(source[l])
                    if goal.is_empty or goal.area<1e-8:continue
                    cached.append({'layer':l,'width':width,'legal':legal,'part':part,'goal':goal});count+=1
                print(bank,l,'SOURCE_COMPONENTS',width,count,flush=True)
        def bridge(point,disk,hole):
            annulus=disk.difference(hole)
            for l,goal in source.items():
                if not goal.is_empty and annulus.intersection(goal).area>.025:return l,None,None
            candidates=[]
            for q in cached:
                startshape=q['part'].buffer(-.00002).intersection(annulus)
                if startshape.is_empty or startshape.area<1e-8:continue
                candidates.append((startshape.distance(q['goal']),q,startshape))
            for distance,q,startshape in sorted(candidates,key=lambda x:(-x[1]['width'],x[0])):
                l,width,legal,part,goal=q['layer'],q['width'],q['legal'],q['part'],q['goal']
                start,end=nearest_points(startshape,goal)
                if get_num_coordinates(part)>160000:
                    simple=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part)
                    possible=[p for p in polys(simple) if p.intersects(startshape) and p.intersects(goal)]
                    if not possible:continue
                    part=max(possible,key=lambda p:p.area)
                    start,end=nearest_points(part.buffer(-.00002).intersection(startshape),part.buffer(-.00002).intersection(goal))
                try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                except (AssertionError,ValueError):continue
                line=LineString(points);core=line.buffer(width/2,quad_segs=32)
                if not legal.buffer(.000001).covers(core):continue
                body=set_precision(unary_union([p for p in polys(line.buffer(max(2.,width),quad_segs=32).intersection(legal)) if p.intersection(core).area>1e-9]),1e-6)
                if not legal.buffer(.000002).covers(body) or not body.buffer(.000002).covers(core):continue
                if body.intersection(annulus).area<.01 or body.intersection(source[l]).area<1e-8:continue
                return l,body,{'minimum_core_width_mm':width,'length_mm':line.length,'points_mm':points,'sheet_only_R35um60C_ohm':.00057003672*line.length/width,'search':search,'source_positive_annular_overlap_mm2':body.intersection(source[l]).area,'annulus_overlap_mm2':body.intersection(annulus).area,'source_component_cache':'Exact complete outline free component, each width eroded before matching; no false150mm endpoint cap'}
            return None,None,None
'''
    code=code[:begin]+bridge+code[end:]
    compile(code,str(dst),'exec');dst.write_text(code,encoding='utf-8')
    (H/'protected24-dogbones-r6-derivation.json').write_text(json.dumps({'prior_helper_sha256':sha(src),'derived_helper_sha256':sha(dst),'corrected_field_r19_receipt_sha256':sha(H/'field-power/repaired-local-return-audit-r19/receipt.json'),'exact_source_positive_annulus_not_drill_disk':True,'exact_global_source_free_component_cache':True,'every_SMD_and_all_native_new_hole_guard_mm':.275,'old_cached_fill_only_endpoints':False,'all_combined_contacts_source_current_native_gates':'OPEN','native_jobs':0,'board_written':False},indent=1)+'\n',encoding='utf-8')
    print(sha(dst))
if __name__=='__main__':main()
