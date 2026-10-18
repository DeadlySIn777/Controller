"""Parallel PTH-rooted variable-width return bridges, exact geometry contacts."""
import json,pickle,hashlib,time,math,re
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from contact_layout import HERE,BASE,load,build,norm,poly,S,identity,contacts
from power_groups import N,ROOTS
from parallel_necks_r1 import seeds
from inventory import sha
OUT=HERE/'variable-return-r2';LAYERS=['In1.Cu','In4.Cu','In2.Cu','In3.Cu']
def main():
 if OUT.exists():raise ValueError('Frozen proposal exists')
 OUT.mkdir();g,b=load();grp=pickle.loads((HERE/'power-groups-r1.pkl').read_bytes());gr=json.loads((HERE/'power-groups-r1.json').read_text(encoding='utf-8'));rec,trees=build(g,layers=set(LAYERS));res=json.loads((BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));dru=(BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text(encoding='utf-8');ex={}
 for ln in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',ln.strip())
  if m:ex[m[1]]={norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 outline=unary_union(poly(g['outline']));rows=[];adds=[];oldstep=S.STEP;S.STEP=.3
 try:
  for bank,goalid,win in [('FBG',0,box(0,120,255,239)),('FAG',0,box(180,120,455,239))]:
   net=N[bank];dom=g['domains_normalized'][net];pad=next(p for p in g['pads'] if (p['ref'],p['num'])==ROOTS[bank]);goal=grp[bank][goalid]
   for layer in LAYERS:
    obs=[]
    for i in trees[layer].query(win.buffer(5),predicate='intersects'):
     r=rec[layer][i]
     if norm(r['net'])==net or r['kind']=='fill':continue
     obs.append(r['shape'].buffer((.15 if r['domain']==dom else .6)+.03))
    for p in g['pads']:
     if norm(p['net'])!=net:obs.extend(q.buffer(.275) for q in poly(p.get('hole') or []) if q.intersects(win.buffer(5)))
    for v in g['vias']:
     if norm(v['net'])!=net and win.buffer(5).covers(Point(v['x'],v['y'])):obs.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275))
    for a in g['rule_areas']:
     if (a.get('no_tracks') or a.get('no_zones')) and layer in a['layers']:obs.extend(q.buffer(.025) for q in poly(a['outline']) if q.intersects(win))
    for a in res['keepouts']:
     if net not in ex.get(a['name'],set()) and layer in a['layers']:obs.extend(q.buffer(.025) for q in poly(a['outline']) if q.intersects(win))
    blocked=unary_union(obs);legal=win.intersection(outline.buffer(-.526)).difference(blocked);free=win.intersection(outline.buffer(-1.526)).difference(blocked.buffer(1.001));source=unary_union(poly(pad['layers'][layer])).intersection(free).buffer(-.01);tt=seeds(goal,layer,free,[{'shape':Point(pad['x'],pad['y']),'layer':layer}]);row={'bank':bank,'source_PTH':list(ROOTS[bank]),'raw_native_net':pad['net'],'layer':layer,'window_mm':win.bounds,'source_annulus_actual_native_flash':layer in pad['layers'],'target_original_group':goalid,'minimum_centerline_core_width_mm':2.,'maximum_expansion_width_mm':7.2,'goal_seed_count':len(tt),'source_seed_area_mm2':source.area}
    if source.is_empty or not tt:row['verdict']='NO_EXACT_SOURCE_OR_TARGET_ATTACHMENT';rows.append(row);print(bank,layer,row['verdict'],flush=True);continue
    a,_=nearest_points(source,unary_union([Point(q[0]) for q in tt]));ss=[(tuple(a.coords[0]),{'uuid':pad['uuid'],'kind':'pad'})];path,search=S.astar(free.buffer(-.00001),ss,tt,time.monotonic()+35,node_cap=650000);row['search']=search
    if not path or not free.covers(LineString(path['points_mm'])):row['verdict']='NO_2MM_ROOT_TO_EXACT_TARGET_PATH';rows.append(row);print(bank,layer,row['verdict'],flush=True);continue
    ln=LineString(path['points_mm']);core=ln.buffer(1.,quad_segs=32);cu=ln.buffer(3.6,quad_segs=32).intersection(legal);parts=[cu] if cu.geom_type=='Polygon' else list(cu.geoms);cu=unary_union([x for x in parts if x.intersection(core).area>1e-8]);assert cu.buffer(.00001).covers(core)
    hits=contacts(rec,trees,cu,layer);own=[r for r in hits if norm(r['net'])==net];foreign=[r for r in hits if norm(r['net'])!=net and r['kind']!='fill'];assert not foreign
    retreats=[]
    for i in trees[layer].query(cu.buffer(.65),predicate='intersects'):
     r=rec[layer][i]
     if r['kind']=='fill' and norm(r['net'])!=net:
      gap=.15 if r['domain']==dom else .6;area=cu.buffer(gap+.025).intersection(r['shape']).area
      if area>1e-8:retreats.append(identity(r)|{'required_retreat_area_mm2':area,'clearance_mm':gap})
    samples=[]
    for s in range(1,math.ceil(ln.length)):
     t=ln.interpolate(s);a=ln.interpolate(max(0,s-.05));bb=ln.interpolate(min(ln.length,s+.05));dx,dy=bb.x-a.x,bb.y-a.y;n=math.hypot(dx,dy)
     if n==0:continue
     seg=LineString([(t.x-5*dy/n,t.y+5*dx/n),(t.x+5*dy/n,t.y-5*dx/n)]);cut=seg.intersection(cu);vals=[cut] if cut.geom_type=='LineString' else list(cut.geoms);w=max((v.length for v in vals if v.distance(t)<.0001),default=0);samples.append({'arc_length_mm':s,'at_mm':[t.x,t.y],'local_cross_section_mm':w})
    row.update(verdict='HOST_SOURCE_PTH_ROOTED_VARIABLE_RETURN_BRIDGE',path=path,length_mm=ln.length,area_mm2=cu.area,min_sampled_width_mm=min((x['local_cross_section_mm'] for x in samples),default=2),width_samples=samples,own_contacts=own,mandatory_fill_retreat=retreats,uniform_2mm_only_resistance60C_upper_bound_mohm=.57003672*ln.length/2.,uniform_2mm_resistance_not_actual_sheet_solve=True,geometric_core_proved_2mm=True,new_return_holes=0)
    p=OUT/(bank+'-'+layer+'.wkb');p.write_bytes(cu.wkb);row['copper_file']=str(p.resolve());row['copper_sha256']=sha(p);adds.append({'shape':cu,'layer':layer,'net':pad['net'],'kind':'prospective_copper','domain':dom,'uuid':'NEW_RETURN_'+bank+'_'+layer});rows.append(row);print(bank,layer,row['verdict'],row['length_mm'],row['min_sampled_width_mm'],flush=True)
    (OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
 finally:S.STEP=oldstep
 result={'board_sha256':g['sha256'],'rows':rows,'no_new_return_holes':True,'all_original_static_Cu_preserved':True,'native_jobs':0,'board_written':False,'source_current_sharing_and_full_sheet_barrel_thermal_solve':'PENDING; no 6.5A rating granted by summed widths','existing_fill_voids_and_contacts_gate_open':True,'all_power_return_groups_joined':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');data=pickle.dumps(adds,protocol=5);(OUT/'prospective-copper.pkl').write_bytes(data);(OUT/'binding.json').write_text(json.dumps({'cache_sha256':hashlib.sha256(data).hexdigest(),'receipt_sha256':sha(OUT/'receipt.json'),'original_board_sha256':g['sha256']},indent=1)+'\n',encoding='utf-8')
if __name__=='__main__':main()
