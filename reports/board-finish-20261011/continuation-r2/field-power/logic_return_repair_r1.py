"""Construct LOGIC_GND repairs in exact coupled r7 legal polygon space."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,uuid,sys,time
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import set_precision,get_num_coordinates
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'logic-return-repair-r1';NET='/LOGIC_GND'
def polys(sh):return [sh] if sh.geom_type=='Polygon' else [p for p in getattr(sh,'geoms',[]) if p.geom_type=='Polygon']
def main():
    assert not OUT.exists();OUT.mkdir();base=HERE/'coupled-logic-base-r1';br=json.loads((base/'receipt.json').read_text());assert sha(base/'model.pkl')==br['model_sha256'];model=pickle.loads((base/'model.pkl').read_bytes());h=model['projected'];discrete=model['discrete'];zones=model['new_zones'];assert sha(base/'groups.pkl')==br['groups_sha256'];groups=pickle.loads((base/'groups.pkl').read_bytes())['new_groups'];gaps=json.loads((HERE/'logic-group-gaps-r1/receipt.json').read_text());outline=unary_union(C.poly(h['outline'])).buffer(-.526);dom=h['domains_normalized'][NET];rows=[];adds=[];obs={};trees={};source_group=next(i for i,g in enumerate(groups) if any(q['kind']=='pad' and q['ref']=='J11001' and q['pin']=='2' for q in g));main_group=0
    for layer in h['copper_layers']:
        dd=[]
        for t in h['tracks']:
            if t['layer']==layer and C.norm(t['net'])!=NET:dd.append((t['uuid'],'track',C.body(t).buffer((.15 if h['domains_normalized'].get(C.norm(t['net']))==dom else .6)+.025)))
        for v in h['vias']:
            if C.norm(v['net'])==NET:continue
            rr=v['drill']/2+.275
            if layer in v['flashed']:rr=max(rr,v['d']/2+(.15 if h['domains_normalized'].get(C.norm(v['net']))==dom else .6)+.025)
            dd.append((v['uuid'],'via-drill-or-annulus',Point(v['x'],v['y']).buffer(rr,quad_segs=32)))
        for p in h['pads']:
            if C.norm(p['net'])!=NET:
                for sh in C.poly(p['layers'].get(layer,[])):dd.append((p['uuid'],'pad',sh.buffer((.15 if h['domains_normalized'].get(C.norm(p['net']))==dom else .6)+.025)))
                for sh in C.poly(p.get('hole') or []):dd.append((p['uuid'],'pad-drill',sh.buffer(.275)))
        for z in zones:
            if z['layer']==layer and C.norm(z['net'])!=NET:dd.append((z['uuid'],'frozen-proposed-power-plane',z['shape'].buffer((.15 if h['domains_normalized'].get(C.norm(z['net']))==dom else .6)+.025)))
        for a in h['rule_areas']:
            if a.get('no_zones') and layer in a['layers']:
                for sh in C.poly(a['outline']):dd.append((a.get('uuid',a.get('name')),'native-functional-no-zones',sh.buffer(.025)))
        obs[layer]=dd;trees[layer]=STRtree([q[2] for q in dd]);print('obstacles',layer,len(dd),flush=True)
    # First restoration is the actual external input/return source group.
    selected=[q for q in gaps['rows'] if q['group']==source_group]
    if '--all' in sys.argv:selected+= [q for q in gaps['rows'] if q['group']!=source_group]
    for gaprow in selected:
        gi=gaprow['group'];sourcecase=gi==source_group;result=None;attempts=[]
        widths=[2.,1.5,1.] if sourcecase else [.5,.35,.25]
        layergaps=gaprow['layer_gaps']
        if sourcecase:layergaps=sorted(layergaps,key=lambda q:(q['layer']!='In3.Cu',q['gap_mm']))
        for q in layergaps:
            layer=q['layer'];src=unary_union([r['shape'] for r in groups[gi] if r['layer']==layer]);target=unary_union([r['shape'] for r in groups[main_group] if r['layer']==layer]);a,b=q['from_mm'],q['to_mm']
            for margin in [8.,20.,45.]:
                win=box(min(a[0],b[0])-margin,min(a[1],b[1])-margin,max(a[0],b[0])+margin,max(a[1],b[1])+margin).intersection(outline);idx=trees[layer].query(win,predicate='intersects');blocked=unary_union([obs[layer][int(i)][2] for i in idx]);legal=win.difference(blocked)
                for w in widths:
                    center=legal.buffer(-w/2-.005);candidates=[]
                    for part in polys(center):
                        sa=part.intersection(src);tb=part.intersection(target)
                        if not sa.is_empty and not tb.is_empty:candidates.append((sa.distance(tb),part,sa,tb))
                    if not candidates:attempts.append({'layer':layer,'window_margin_mm':margin,'width_mm':w,'verdict':'NO_SHARED_LEGAL_CENTERLINE_COMPONENT'});continue
                    _,part,sa,tb=min(candidates,key=lambda q:q[0]);start,end=nearest_points(sa,tb)
                    if get_num_coordinates(part)>180000:
                        # Conservative inward simplification; final centerline and Cu
                        # are re-tested against the unsimplified exact legal region.
                        simple=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part)
                        pp=[p for p in polys(simple) if p.intersects(sa) and p.intersects(tb)]
                        if not pp:attempts.append({'layer':layer,'window_margin_mm':margin,'width_mm':w,'verdict':'CONSERVATIVE_SIMPLIFICATION_LOST_ATTACHMENT'});continue
                        part=max(pp,key=lambda p:p.area);start,end=nearest_points(part.intersection(sa),part.intersection(tb))
                    points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]));line=LineString(points);core=line.buffer(w/2,quad_segs=32);assert legal.buffer(.000001).covers(core)
                    maxwidth=5. if sourcecase else 1.2;body=line.buffer(maxwidth/2,quad_segs=32).intersection(legal);body=unary_union([p for p in polys(body) if p.intersection(core).area>1e-9]);body=set_precision(body,1e-6);assert legal.buffer(.000002).covers(body) and body.buffer(.000002).covers(core)
                    hits=[]
                    for j,gg in enumerate(groups):
                        contacts=[r for r in gg if r['layer']==layer and r['shape'].intersects(body)]
                        if contacts:hits.append({'group':j,'objects':[C.identity(r) for r in contacts]})
                    assert gi in {r['group'] for r in hits} and main_group in {r['group'] for r in hits}
                    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-field-logic-return-r1-'+str(gi)+'-'+layer));file=OUT/(uid+'.wkb');file.write_bytes(body.wkb);result={'uuid':uid,'net_raw':NET,'group':gi,'layer':layer,'source_external_return_repair':sourcecase,'minimum_centerline_width_mm':w,'max_body_width_mm':maxwidth,'length_mm':line.length,'area_mm2':body.area,'path_mm':points,'source_pad_triplets':gaprow['pads'],'contacted_groups':hits,'geometry_file':str(file.resolve()),'sha256':sha(file),'search':search,'static_Cu_drill_frozen_new_plane_and_no_zones_screen':'PASS','new_holes':0,'legacy_uniform_core_sheet_R60C_upper_bound_ohm':.00057003672*line.length/w,'current_allocation_status':'SOURCE_BOUND_PENDING_SIGNED_INPUT_RETURN_LEDGER' if sourcecase else 'LOCAL_LOAD_BOUND_PENDING_PIN_ALLOCATION','native_jobs':0};adds.append({'uuid':uid,'layer':layer,'net':NET,'shape':body});print('accepted',gi,layer,w,line.length,'joins',[r['group'] for r in hits],flush=True);break
                if result:break
            if result:break
        rows.append({'group':gi,'verdict':'CONSTRUCTED_LEGAL_REPAIR_CURRENT_AND_NATIVE_PENDING' if result else 'NO_REPAIR_WITH_FROZEN_POWER_SHAPES','repair':result,'attempts':attempts});(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n')
    raw=pickle.dumps(adds,protocol=5);(OUT/'proposed-zones.pkl').write_bytes(raw);receipt={'verdict':'CONSTRUCTED_REPAIRS_REQUIRE_FULL_CONTACT_CURRENT_NATIVE_AUDIT','base_receipt_sha256':sha(base/'receipt.json'),'gap_receipt_sha256':sha(HERE/'logic-group-gaps-r1/receipt.json'),'rows':rows,'proposal_sha256':sha(OUT/'proposed-zones.pkl'),'exact_existing_raw_token':NET,'frozen_r7_field_and_CORE_shapes_unchanged':True,'native_jobs':0,'board_written':False,'board_adopted':False,'source_current_sheet_barrel_thermal_qualification':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('receipt',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
