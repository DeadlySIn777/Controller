"""Source-rooted, same-layer local return attachments without new vias."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,uuid,re,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import nearest_points,unary_union
from shapely.strtree import STRtree
from contact_layout import HERE,BASE,build,norm,poly,O,identity,contacts
from power_groups import N,ROOTS,key,graph
from inventory import sha
OUT=HERE/'direct-ground-joins-r1';WIDTH=.35
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();gp=HERE/'composed-field-geometry-r3/geometry.pkl';cr=json.loads((gp.parent/'receipt.json').read_text(encoding='utf-8'));assert sha(gp)==cr['geometry_sha256'];g=pickle.loads(gp.read_bytes());groups=pickle.loads((gp.parent/'ground-groups.pkl').read_bytes());rec,trees=build(g);outline=unary_union(poly(g['outline']));res=json.loads((BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));dru=(BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text(encoding='utf-8');ex={}
 for ln in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',ln.strip())
  if m:ex[m[1]]={norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 drills=[{'shape':h,'net':norm(q['net']),'uuid':q['uuid']} for q in g['pads'] for h in poly(q.get('hole') or [])]+[{'shape':Point(v['x'],v['y']).buffer(v['drill']/2),'net':norm(v['net']),'uuid':v['uuid']} for v in g['vias']];drilltree=STRtree([q['shape'] for q in drills]);rows=[];new=[];blocked=[]
 for bank in ['FAG','FBG']:
  net=N[bank];dom=g['domains_normalized'][net];gs=groups[bank];ri=next(i for i,xs in enumerate(gs) if any(x['kind']=='pad' and (x['ref'],x['pin'])==ROOTS[bank] for x in xs));root=list(gs[ri]);unroot=[(i,xs) for i,xs in enumerate(gs) if i!=ri and any(x['kind']=='pad' for x in xs)];connected={ri};normalraw=next(p['net'] for p in g['pads'] if (p['ref'],p['num'])==ROOTS[bank])
  for iteration in range(4):
   count=0
   bylayer={l:[r for r in root if r['layer']==l] for l in rec};rt={l:STRtree([r['shape'] for r in rs]) for l,rs in bylayer.items() if rs};candidates=[]
   for i,xs in unroot:
    if i in connected:continue
    possible=[]
    for a in xs:
     l=a['layer']
     if l not in rt:continue
     j=int(rt[l].nearest(a['shape']));bb=bylayer[l][j];pt1,pt2=nearest_points(a['shape'],bb['shape']);d=pt1.distance(pt2)
     if d<=40:possible.append((d,l,pt1,pt2,a,bb))
    for x in sorted(possible,key=lambda x:x[0])[:16]:candidates.append((x[0],i,x))
   for _,i,(d,l,pa,pb,a,bb) in sorted(candidates,key=lambda x:x[0]):
    if i in connected:continue
    ln=LineString([tuple(pa.coords[0]),tuple(pb.coords[0])]);cu=ln.buffer(WIDTH/2,quad_segs=32);bad=[];voids=[]
    if not outline.buffer(-.525).covers(cu):bad.append('board_edge')
    for j in trees[l].query(cu.buffer(.65),predicate='intersects'):
     q=rec[l][int(j)]
     if norm(q['net'])==net:continue
     gap=.15 if q['domain']==dom else .6
     if q['kind']=='fill':
      area=cu.buffer(gap+.030).intersection(q['shape']).area
      if area>1e-8:voids.append(identity(q)|{'clearance_mm':gap,'cut_area_mm2':area})
     elif cu.distance(q['shape'])<gap+.025-1e-7:bad.append(identity(q))
    for j in drilltree.query(cu.buffer(.275),predicate='intersects'):
     q=drills[int(j)]
     if q['net']!=net and cu.distance(q['shape'])<.275-1e-7:bad.append({'foreign_drill_uuid':q['uuid']})
    for rule in g['rule_areas']:
     if rule.get('no_tracks') and l in rule['layers'] and any(cu.intersects(x.buffer(.025)) for x in poly(rule['outline'])):bad.append({'functional_no_tracks':rule['uuid']})
    for rule in res['keepouts']:
     if net not in ex.get(rule['name'],set()) and l in rule['layers'] and any(cu.intersects(x.buffer(.025)) for x in poly(rule['outline'])):bad.append({'reserved_no_tracks':rule['name']})
    for q in new:
     if q['layer']==l and norm(q['net'])!=net and cu.distance(q['shape'])<.6+.025-1e-7:bad.append({'new_foreign_return':q['uuid']})
    if bad:
     blocked.append({'bank':bank,'group':i,'length_mm':d,'layer':l,'from':identity(a),'to':identity(bb),'blocking_items':bad[:20]});continue
    assert cu.intersects(a['shape']) and cu.intersects(bb['shape']);uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'Controller-field-local-return-r1/{bank}/{i}/{l}/{pa.wkt}/{pb.wkt}'));row={'bank':bank,'original_composed_group':i,'raw_net':normalraw,'uuid':uid,'layer':l,'width_mm':WIDTH,'points_mm':[list(pa.coords[0]),list(pb.coords[0])],'length_mm':ln.length,'normal35um60C_resistance_mohm':.57003672*ln.length/WIDTH,'source_rooted_target':identity(bb),'source_attachment':identity(a),'all_group_pads':sorted([list(p) for p in {(x['ref'],x['pin']) for x in gs[i] if x['kind']=='pad'}]),'mandatory_foreign_fill_voids':voids,'prospective_source_current_allocation':'PENDING_EXACT_LOCAL_DC_AND_TRANSIENT_LOAD; geometry alone grants no rating','no_new_holes':True};rows.append(row);q={'kind':'prospective_local_return_track','uuid':uid,'net':normalraw,'domain':dom,'layer':l,'shape':cu};new.append(q);root.extend(gs[i]);root.append(q);connected.add(i);count+=1
    chunk='\t(segment\n\t\t(start '+format(pa.x,'.9f')+' '+format(pa.y,'.9f')+')\n\t\t(end '+format(pb.x,'.9f')+' '+format(pb.y,'.9f')+')\n\t\t(width 0.35)\n\t\t(layer "'+l+'")\n\t\t(net "'+normalraw+'")\n\t\t(uuid "'+uid+'")\n\t)\n';path=OUT/(uid+'.segment-chunk');path.write_text(chunk,encoding='utf-8',newline='');row.update(path=str(path.resolve()),chunk_sha256=sha(path))
   print(bank,'iteration',iteration,'new_joins',count,'remaining',len(unroot)-len(connected)+1,flush=True)
   write(OUT/'checkpoint.json',{'rows':rows,'blocked':blocked,'complete':False})
   if not count:break
  for row in rows:
   if row['bank']!=bank:continue
   a,bb=row['points_mm'];g['tracks'].append({'uuid':row['uuid'],'net':row['raw_net'],'layer':row['layer'],'a':a,'b':bb,'w':WIDTH})
 result={'verdict':'HOST_SOURCE_ROOTED_SAME_LAYER_RETURN_PROPOSAL','input_composed_geometry_sha256':sha(gp),'rows':rows,'blocked_direct_candidates':blocked,'new_segments':len(rows),'no_new_holes':True,'native_jobs':0,'board_written':False,'no_current_or_foreign_retained_continuity_qualification_inferred':True,'source_export_sha256':cr['source_export_sha256']};write(OUT/'receipt.json',result);(OUT/'prospective-copper.pkl').write_bytes(pickle.dumps(new,protocol=5));print(json.dumps({'new_segments':len(rows),'receipt_sha256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
