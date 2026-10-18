"""Preserve all12 protected dogbones; replace only mutually invalid new planes.

No original copper or plane outline changes. Every chosen-layer source goal is
bound locally and every accepted route is checked in a full projected graph.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision,get_num_coordinates
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import zone_projection_r1 as N
import tri_route as T
OUT=H/'protected24-on-corrected-core-r8';LAYERS=('In1.Cu','In4.Cu','In2.Cu','In3.Cu')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
    mp=H/'sbc-power/actual-core-cross-layer-source-bridge-r38/model.pkl';assert sha(mp)=='91710ee78e3b35c7903bc590292af2fd3eccbb514589fd9a7553a76772f6f4db'
    rp=H/'protected24-dogbones-r7';rr=json.loads((rp/'receipt.json').read_bytes());assert sha(rp/'receipt.json')=='46a6530da775692bee83f19404711cd280f9d87d8662c589a21e20e6c6c8a226'
    old,base,binding,bz,prior=pickle.loads(mp.read_bytes());new=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());protected=pickle.loads((rp/'proposed-zones.pkl').read_bytes())
    assert sha(rp/'proposed-discrete.pkl')==rr['proposed_discrete_sha256'] and sha(rp/'proposed-zones.pkl')==rr['proposed_zones_sha256']
    h={**base,'vias':base['vias']+new['vias'],'tracks':base['tracks']+new['tracks']}
    precise={q['uuid'] for q in bz if q.get('label')=='CORE-main-In2' or q.get('label','').startswith('IO3-r15-field-crossing-') or q.get('field_return_proposal') and q['layer']=='In2.Cu'};assert len(precise)==9
    bz=[{**q,'shape':set_precision(q['shape'],1e-6)} if q['uuid'] in precise else q for q in bz]
    rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)
    def gap(raw,other):return .15 if h['domains_normalized'][C.norm(raw)]==h['domains_normalized'][C.norm(other)] else .6
    def may_carve(q,raw):return q['layer'] in ('In1.Cu','In2.Cu','In4.Cu') and C.norm(q['net'])==('/motherboard_motors/FIELD_GND' if C.norm(raw).endswith('FIELD_A_24V_PROTECTED') else '/motherboard_do/FIELD_B_0V')
    invalid=[];held=[]
    for z in protected:
        bad=any(q['net']!=z['net'] and z['shape'].distance(q['shape'])<gap(z['net'],q['net'])+.024 for q in rec[z['layer']])
        bad=bad or any(q['layer']==z['layer'] and q['net']!=z['net'] and not may_carve(q,z['net']) and z['shape'].distance(q['shape'])<gap(z['net'],q['net'])+.024 for q in bz)
        (invalid if bad else held).append(z)
    assert not OUT.exists();OUT.mkdir();rows=[];adds=list(held);carves=[]
    def project(zs):
        result=[];ledger=[]
        for q in bz:
            bodies=[]
            for bank in ('FIELD_A_24V_PROTECTED','FIELD_B_24V_PROTECTED'):
                raw=next(v['net'] for v in new['vias'] if C.norm(v['net']).endswith(bank))
                if not may_carve(q,raw):continue
                bodies += [Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32) for v in new['vias'] if v['net']==raw]
                bodies += [C.body(t) for t in new['tracks'] if t['net']==raw and t['layer']==q['layer']]
                bodies += [z['shape'] for z in zs if z['net']==raw and z['layer']==q['layer']]
            if bodies:
                cutter=unary_union(bodies).buffer(.175);shape=set_precision(q['shape'].difference(cutter),1e-6);native=set_precision(q.get('zone_outline_shape',q['shape']).difference(cutter),1e-6)
                if not shape.equals(q['shape']):ledger.append({'uuid':q['uuid'],'old_shape_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'new_shape_sha256':hashlib.sha256(shape.wkb).hexdigest(),'removed_area_mm2':q['shape'].difference(shape).area,'quantization_added_area_mm2':shape.difference(q['shape']).area,'cutter_wkb_sha256':hashlib.sha256(cutter.wkb).hexdigest()})
                result.append({**q,'shape':shape,'zone_outline_shape':native})
            else:result.append(q)
        candidate,cuts=N.projected(old,h,result+zs);return candidate,result+zs,ledger,cuts
    current,allzones,carves,cuts=project(adds)
    print('INVALID_NEW_PROTECTED_PLANES',len(invalid),[q['uuid'] for q in invalid],flush=True)
    for bank,net,rootref in [('FB','/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006'),('FA','/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004')]:
        raw=next(v['net'] for v in new['vias'] if C.norm(v['net'])==net)
        ownholes=unary_union([s for p in h['pads'] if p['net']==raw for s in C.poly(p.get('hole') or [])]+[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64) for v in h['vias'] if v['net']==raw])
        legal={};cached={}
        for layer in LAYERS:
            obs=[q['shape'].buffer(gap(raw,q['net'])+.025) for q in rec[layer] if q['net']!=raw]
            obs += [q['shape'].buffer(gap(raw,q['net'])+.025) for q in bz+adds if q['layer']==layer and q['net']!=raw and not may_carve(q,raw)]
            obs += [s.buffer(.275) for p in h['pads'] if p['net']!=raw for s in C.poly(p.get('hole') or [])]+[Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=32) for v in h['vias'] if v['net']!=raw]
            obs += [s.buffer(.025) for rule in h['rule_areas'] if rule.get('no_zones') and layer in rule['layers'] for s in C.poly(rule['outline'])]
            legal[layer]=set_precision(outline.difference(unary_union(obs)),1e-6)
            for width in (2.,1.,.5,.35,.25):cached[layer,width]=polys(legal[layer].buffer(-width/2-.005))
            print('PROTECTED_R8_LEGAL',bank,layer,get_num_coordinates(legal[layer]),flush=True)
        for v in [v for v in new['vias'] if v['net']==raw]:
            groups=F.graph(current,net);root=next(xs for xs in groups if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'17') for q in xs))
            if any(q['kind']=='via' and q['uuid']==v['uuid'] for q in root):continue
            source={l:unary_union([q['shape'] for q in root if q['layer']==l]).difference(ownholes) for l in LAYERS};ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64));options=[]
            for layer in LAYERS:
                for width in (2.,1.,.5,.35,.25):
                    for part in cached[layer,width]:
                        inner=part.buffer(-.00002);aa=inner.intersection(ann);bb=inner.intersection(source[layer])
                        if aa.area>1e-8 and bb.area>1e-8:options.append((aa.distance(bb),layer,width,part,aa,bb))
            answer=None
            for distance,layer,width,part,aa,bb in sorted(options,key=lambda q:(-q[2],q[0])):
                if get_num_coordinates(part)>160000:
                    simple=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);ps=[p for p in polys(simple) if p.intersects(aa) and p.intersects(bb)]
                    if not ps:continue
                    part=max(ps,key=lambda p:p.area);aa=part.buffer(-.00002).intersection(aa);bb=part.buffer(-.00002).intersection(bb)
                    if aa.area<=1e-8 or bb.area<=1e-8:continue
                start,end=nearest_points(aa,bb)
                try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                except (AssertionError,ValueError):continue
                points=[[round(x,6),round(y,6)] for x,y in points]
                if len(set(map(tuple,points)))<2:continue
                line=LineString(points);core=line.buffer(width/2,quad_segs=32)
                if not legal[layer].buffer(.000001).covers(core):continue
                native=set_precision(unary_union([p for p in polys(line.buffer(max(2.,width),quad_segs=32).intersection(legal[layer])) if p.intersection(core).area>1e-9]),1e-6);physical=set_precision(native.difference(ownholes),1e-6)
                if physical.intersection(ann).area<.01 or physical.intersection(source[layer]).area<1e-8:continue
                zid=str(uuid.uuid5(uuid.UUID(v['uuid']),'corrected-core-r8/'+layer));z={'uuid':zid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':native,'clearance_mm':.15,'physical_Cu_drill_subtracted':True,'label':'Protected feed on corrected CORE'}
                trial,tzones,tcarves,tcuts=project(adds+[z]);tr=next(xs for xs in F.graph(trial,net) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'17') for q in xs))
                if not any(q['kind']=='via' and q['uuid']==v['uuid'] for q in tr):continue
                if not {q['uuid'] for q in root if q['kind'] in ('pad','via','track')}<={q['uuid'] for q in tr if q['kind'] in ('pad','via','track')}:continue
                adds.append(z);current,allzones,carves,cuts=trial,tzones,tcarves,tcuts;answer={'via_uuid':v['uuid'],'new_zone_uuid':zid,'layer':layer,'points_mm':points,'length_mm':line.length,'minimum_core_width_mm':width,'native_required_flash':[layer],'actual_full_projected_source_join':True,'search':search};print('PROTECTED_R8_ROOTED',bank,v['uuid'],layer,line.length,width,flush=True);break
            rows.append({'bank':bank,'via_uuid':v['uuid'],'eligible_same_layer_routes':len(options),'repair':answer});write(OUT/'checkpoint.json',rows);(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((old,h,binding,allzones,current),protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5));(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps(new,protocol=5))
    write(OUT/'receipt.json',{'verdict':'PROTECTED_ON_CORRECTED_CORE_CONSTRUCTED_MUTUAL_RETURNS_CURRENT_NATIVE_PENDING','parent_CORE_model_sha256':sha(mp),'R7_exact_recipe_sha256':sha(rp/'receipt.json'),'model_sha256':sha(model),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'all12_vias12stubs_preserved_exact':True,'invalid_owned_new_planes_replaced':[q['uuid'] for q in invalid],'preserved_owned_positive_planes':[q['uuid'] for q in held],'rows':rows,'owned_new_field_return_carves':carves,'original_fill_projection_ledger':cuts,'original_source_Cu_zone_outlines_changed':False,'full_mutual_old_source_return_current_native_refill_flashes_and_DRC':'OPEN','board_written':False,'native_jobs':0,'adopted':False});print('PROTECTED_R8_FROZEN',sha(model),flush=True)
if __name__=='__main__':main()
