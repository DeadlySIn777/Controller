"""Attach field local return groups only to proven prospective source planes."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,uuid,re
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
from contact_layout import HERE,BASE,build,norm,poly,identity
from power_groups import N,ROOTS
from inventory import sha
OUT=HERE/'ground-dogbones-r1';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];INNER=['In1.Cu','In4.Cu','In2.Cu'];W=.25
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();gp=HERE/'composed-field-geometry-r3/geometry.pkl';cr=json.loads((gp.parent/'receipt.json').read_text(encoding='utf-8'));assert sha(gp)==cr['geometry_sha256'];g=pickle.loads(gp.read_bytes());groups=pickle.loads((gp.parent/'ground-groups.pkl').read_bytes());direct=json.loads((HERE/'direct-ground-joins-r1/receipt.json').read_text(encoding='utf-8'));directcu=pickle.loads((HERE/'direct-ground-joins-r1/prospective-copper.pkl').read_bytes());rec,trees=build(g);outline=unary_union(poly(g['outline']));res=json.loads((BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));dru=(BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text(encoding='utf-8');ex={}
 for ln in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',ln.strip())
  if m:ex[m[1]]={norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 drills=[{'shape':h,'net':norm(q['net']),'uuid':q['uuid']} for q in g['pads'] for h in poly(q.get('hole') or [])]+[{'shape':Point(v['x'],v['y']).buffer(v['drill']/2),'net':norm(v['net']),'uuid':v['uuid']} for v in g['vias']];dt=STRtree([q['shape'] for q in drills]);smd=[{'shape':unary_union(poly(ps)),'uuid':p['uuid']} for p in g['pads'] if p['smd'] for l,ps in p['layers'].items() if l in ['F.Cu','B.Cu']];smt=STRtree([q['shape'] for q in smd]);new=list(directcu);rows=[];remaining=[]
 for bank in ['FAG','FBG']:
  net=N[bank];dom=g['domains_normalized'][net];raw=next(p['net'] for p in g['pads'] if (p['ref'],p['num'])==ROOTS[bank]);gs=groups[bank];ri=next(i for i,xs in enumerate(gs) if any(x['kind']=='pad' and (x['ref'],x['pin'])==ROOTS[bank] for x in xs));connected={ri}|{r['original_composed_group'] for r in direct['rows'] if r['bank']==bank};root=[q for i in connected for q in gs[i]]
  sourceplanes={l:unary_union([r['shape'] for r in root if r['layer']==l]) for l in INNER}
  for gid,xs in enumerate(gs):
   if gid in connected or not any(x['kind']=='pad' for x in xs):continue
   pads=sorted([r for r in xs if r['kind']=='pad' and r['layer'] in ['F.Cu','B.Cu']],key=lambda r:-r['shape'].area);attempts=0;answer=None
   for a in pads[:16]:
    outer=a['layer'];anchor=a['shape'].representative_point()
    for radius in [.6,.9,1.2,1.6,2.2,3.,4.,6.]:
     for step in range(16):
      angle=math.pi*step/8;point=Point(anchor.x+radius*math.cos(angle),anchor.y+radius*math.sin(angle));disk=point.buffer(.3,quad_segs=32);hole=point.buffer(.15,quad_segs=32);plane=next((l for l in INNER if sourceplanes[l].intersection(disk).area>.03),None)
      if plane is None:continue
      attempts+=1;ln=LineString([anchor,point]);stub=ln.buffer(W/2,quad_segs=32);shapes={l:disk for l in LAYERS};shapes[outer]=unary_union([disk,stub]);bad=False;voids=[]
      if not outline.buffer(-.525).covers(unary_union([disk,stub])):continue
      if any(hole.buffer(.05).intersects(smd[int(j)]['shape']) for j in smt.query(hole.buffer(.05),predicate='intersects')):continue
      for j in dt.query(hole.buffer(.275),predicate='intersects'):
       q=drills[int(j)]
       if hole.distance(q['shape'])<.275-1e-7:bad=True;break
      if bad:continue
      for l,cu in shapes.items():
       for j in trees[l].query(cu.buffer(.65),predicate='intersects'):
        q=rec[l][int(j)]
        if norm(q['net'])==net:continue
        gap=.15 if q['domain']==dom else .6
        if q['kind']=='fill':
         ar=cu.buffer(gap+.030).intersection(q['shape']).area
         if ar>1e-8:voids.append(identity(q)|{'clearance_mm':gap,'cut_area_mm2':ar})
        elif cu.distance(q['shape'])<gap+.025-1e-7:bad=True;break
       if bad:break
       for rule in g['rule_areas']:
        if (rule.get('no_vias') or (l==outer and rule.get('no_tracks'))) and l in rule['layers'] and any(cu.intersects(p.buffer(.025)) for p in poly(rule['outline'])):bad=True;break
       if bad:break
       for rule in res['keepouts']:
        if net not in ex.get(rule['name'],set()) and l in rule['layers'] and any(cu.intersects(p.buffer(.025)) for p in poly(rule['outline'])):bad=True;break
       if bad:break
       for q in new:
        if q['layer']==l and norm(q['net'])!=net and cu.distance(q['shape'])<.6+.025-1e-7:bad=True;break
       if bad:break
      if bad:continue
      uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'Controller-field-rooted-ground-dogbone-r1/{bank}/{gid}/{outer}/{point.wkt}'));segid=str(uuid.uuid5(uuid.NAMESPACE_URL,uid+'/stub'));points=[list(anchor.coords[0]),list(point.coords[0])];via='\t(via\n\t\t(at '+format(point.x,'.9f')+' '+format(point.y,'.9f')+')\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "'+raw+'")\n\t\t(uuid "'+uid+'")\n\t)\n';vp=OUT/(uid+'.via-chunk');vp.write_text(via,encoding='utf-8',newline='');seg='\t(segment\n\t\t(start '+format(anchor.x,'.9f')+' '+format(anchor.y,'.9f')+')\n\t\t(end '+format(point.x,'.9f')+' '+format(point.y,'.9f')+')\n\t\t(width 0.25)\n\t\t(layer "'+outer+'")\n\t\t(net "'+raw+'")\n\t\t(uuid "'+segid+'")\n\t)\n';sp=OUT/(segid+'.segment-chunk');sp.write_text(seg,encoding='utf-8',newline='')
      answer={'bank':bank,'original_composed_group':gid,'group_pads':sorted([list(p) for p in {(q['ref'],q['pin']) for q in xs if q['kind']=='pad'}]),'raw_net':raw,'stub_outer_layer':outer,'actual_source_rooted_plane_layer':plane,'source_outer_pad':identity(a),'points_mm':points,'width_mm':W,'via_diameter_drill_mm':[.6,.3],'via_uuid':uid,'segment_uuid':segid,'conservative_proposed_annuli_layers':LAYERS,'required_native_postfill_flashes':[outer,plane],'exact_required_plane_annulus_contact_area_mm2':sourceplanes[plane].intersection(disk.difference(hole)).area,'via_chunk_path':str(vp.resolve()),'via_chunk_sha256':sha(vp),'segment_chunk_path':str(sp.resolve()),'segment_chunk_sha256':sha(sp),'mandatory_foreign_fill_voids':voids,'conditional_20um_barrel_60C_1p6mm_R_mohm':1.99512852e-8*.0016/(math.pi*.0003*.000020)*1000,'local_normal_current_target_a':.5,'current_target_is_capacity_planning_only':True,'actual_local_DC_and_cap_transient_allocation':'PENDING; excludes the already plane-rooted4A connector main return','native_jobs':0}
      for l,cu in shapes.items():new.append({'kind':'prospective_local_return_via_and_stub','uuid':uid+'@'+l,'net':raw,'domain':dom,'layer':l,'shape':cu})
      connected.add(gid);root.extend(xs);break
     if answer:break
    if answer:break
   if answer:rows.append(answer);print(bank,gid,'ROOTED_DOGBONE',len(answer['group_pads']),flush=True)
   else:remaining.append({'bank':bank,'original_composed_group':gid,'pads':sorted([list(p) for p in {(q['ref'],q['pin']) for q in xs if q['kind']=='pad'}]),'via_plane_contact_candidates_checked':attempts});print(bank,gid,'NO_LOCAL_DOGBONE',attempts,flush=True)
   write(OUT/'checkpoint.json',{'rows':rows,'remaining':remaining,'complete':False})
 result={'verdict':'HOST_SOURCE_ROOTED_RETURN_DOGBONE_PROPOSAL','rows':rows,'remaining_groups':remaining,'new_vias':len(rows),'new_stubs':len(rows),'input_geometry_sha256':sha(gp),'source_export_sha256':cr['source_export_sha256'],'direct_ground_receipt_sha256':sha(HERE/'direct-ground-joins-r1/receipt.json'),'native_jobs':0,'board_written':False,'actual_layer_flash_and_foreign_fill_retreat_and_continuity_and_current_gates':'OPEN; all source attachments are concrete source-rooted prospective geometry, never isolated-net proximity.'};write(OUT/'receipt.json',result);(OUT/'prospective-copper.pkl').write_bytes(pickle.dumps(new,protocol=5));print(json.dumps({'new_vias':len(rows),'remaining_groups':len(remaining),'receipt_sha256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
