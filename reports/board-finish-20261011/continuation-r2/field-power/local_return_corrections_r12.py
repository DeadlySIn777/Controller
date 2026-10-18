"""Repair exact three-item LOGIC island and rejected0.15mm C14049 stub.

Preserve every old/native copper item and all proposed return polygons. Only
the explicitly rejected new stub is replaced; all new tracks are>=0.20mm.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,uuid,re
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'local-return-corrections-r12'
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
    assert not OUT.exists();OUT.mkdir();bp=HERE/'complete-local-field-return-contact-audit-r10';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());gg=pickle.loads((bp/'groups.pkl').read_bytes());rp=HERE.parent/'sbc-power/io3-field-crossings-r15';planes=pickle.loads((rp/'model.pkl').read_bytes())[3]+pickle.loads((HERE/'source-rooted-local-field-returns-r6/proposed-zones.pkl').read_bytes())+pickle.loads((HERE/'bridged-field-ground-dogbones-r8/proposed-zones.pkl').read_bytes());ownedids={q['uuid'] for q in planes};badid='ad24a90e-2565-5700-b98a-173c8744c1ca';oldbad=next(q for q in g['tracks'] if q['uuid']==badid);assert oldbad['w']==.15;h={**g,'tracks':[q for q in g['tracks'] if q['uuid']!=badid]};records,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526);res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    adds=[];rows=[]
    for name,net,targetref,targetpin,rootref in [('LOGIC_R5051_restore','/LOGIC_GND','R5051','2','J11001'),('C14049_minimum_width','/motherboard_motors/FIELD_GND','C14049','2','J11003')]:
        groups=gg[net];ri=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));targetpad=next(q for q in g['pads'] if (q['ref'],q['num'])==(targetref,targetpin));raw=targetpad['net'];domain=g['domains_normalized'][net];found=None;attempts=[]
        def gap(other):return .15 if g['domains_normalized'].get(C.norm(other))==domain else .6
        candidates=[]
        for layer in ('F.Cu','B.Cu','In1.Cu','In4.Cu'):
            if name=='C14049_minimum_width':src=unary_union(C.poly(targetpad['layers'].get(layer,[])))
            else:
                ti=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(targetref,targetpin) for q in xs));src=unary_union([q['shape'] for q in groups[ti] if q['layer']==layer and q['kind']!='fill'])
            dst=unary_union([q['shape'] for q in groups[ri] if q['layer']==layer and q['uuid']!=badid and (q['kind']!='fill' or q['uuid'] in ownedids) and not(q['kind']=='pad' and q['uuid']==targetpad['uuid'])])
            if src.is_empty or dst.is_empty:continue
            a,b=nearest_points(src,dst);candidates.append((a.distance(b),layer,src,dst,a,b))
        for distance,layer,src,dst,a,b in sorted(candidates,key=lambda q:q[0]):
            if name=='C14049_minimum_width' and layer not in ('F.Cu','B.Cu'):continue
            obstacles=[q['shape'].buffer(gap(q['net'])+.025) for q in records[layer] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in planes if q['layer']==layer and C.norm(q['net'])!=net]
            for v in g['vias']:
                if C.norm(v['net'])!=net:obstacles.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=32))
            for pad in g['pads']:
                if C.norm(pad['net'])!=net:obstacles.extend([q.buffer(.275) for q in C.poly(pad.get('hole') or [])])
            outer=layer in ('F.Cu','B.Cu')
            for rule in g['rule_areas']:
                if (rule.get('no_tracks') if outer else rule.get('no_zones')) and layer in rule['layers']:obstacles.extend([q.buffer(.025) for q in C.poly(rule['outline'])])
            if outer:
                for rule in res['keepouts']:
                    if net not in exceptions.get(rule['name'],set()) and layer in rule['layers']:obstacles.extend([q.buffer(.025) for q in C.poly(rule['outline'])])
            tree=STRtree(obstacles)
            for margin in (3.,10.,25.):
                win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ids=tree.query(win,predicate='intersects');legal=win.difference(unary_union([obstacles[int(j)] for j in ids]))
                for width in ((.5,.35,.25,.20) if outer else (.5,.35)):
                    options=[]
                    for part in polys(legal.buffer(-width/2-.005)):
                        sa=part.buffer(-.00002).intersection(src);tb=part.buffer(-.00002).intersection(dst)
                        if not sa.is_empty and not tb.is_empty:options.append((sa.distance(tb),part,sa,tb))
                    if not options:attempts.append({'layer':layer,'width_mm':width,'margin_mm':margin,'verdict':'NO_LEGAL_SHARED_PHYSICAL_ATTACHMENT_COMPONENT'});continue
                    _,part,sa,tb=min(options,key=lambda q:q[0]);start,end=nearest_points(sa,tb)
                    try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                    except (AssertionError,ValueError):continue
                    points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points);core=line.buffer(width/2,quad_segs=32)
                    if not legal.buffer(.000001).covers(core) or core.intersection(src).area<1e-8 or core.intersection(dst).area<1e-8:continue
                    if not outer:continue
                    uids=[]
                    for j,(aa,bb) in enumerate(zip(points,points[1:])):
                        if aa==bb:continue
                        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-local-return-correction-r12/{name}/{j}'));t={'uuid':uid,'net':raw,'layer':layer,'a':aa,'b':bb,'w':width,'prospective_not_native':True};adds.append(t);uids.append(uid);path=OUT/(uid+'.segment-chunk');path.write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*aa,*bb,width,layer,raw,uid),encoding='utf-8',newline='')
                    found={'name':name,'raw_net':raw,'layer':layer,'width_mm':width,'length_mm':line.length,'points_mm':points,'new_segment_UUIDs':uids,'native_target_pad_UUID':targetpad['uuid'],'source_root':rootref+'.2','sheet_only_R35um60C_ohm':.00057003672*line.length/width,'search':search,'native_retained_contacts_and_signed_current_gates':'OPEN'};print(name,layer,width,line.length,flush=True);break
                if found:break
            if found:break
        rows.append({'name':name,'verdict':'CONSTRUCTED' if found else 'NO_FIXED_ATTACHMENT_REPAIR','repair':found,'attempts':attempts});(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n')
    (OUT/'proposed-tracks.pkl').write_bytes(pickle.dumps(adds,protocol=5));receipt={'verdict':'CONSTRUCTIVE_SCOPED_LOCAL_RETURN_CORRECTIONS' if all(q['repair'] for q in rows) else 'REPAIR_INCOMPLETE','rows':rows,'new_segments':len(adds),'proposal_sha256':sha(OUT/'proposed-tracks.pkl'),'remove_rejected_new_stub_UUID':badid,'remove_rejected_new_stub_geometry':oldbad,'parent_contact_receipt_sha256':sha(bp/'receipt.json'),'all_original_native_discrete_and_owned_return_shapes_unchanged':True,'native_minimum_track_width_mm':.20,'new_holes':0,'native_jobs':0,'board_written':False,'full_retained_contact_and_native_current_gates':'OPEN'};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
