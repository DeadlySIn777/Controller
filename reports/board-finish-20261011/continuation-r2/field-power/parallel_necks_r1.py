"""Actual parallel source-PTH escapes then wider copper, host-only current proposal."""
import json,pickle,hashlib,re,time,math
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from contact_layout import HERE,BASE,load,build,norm,poly,S,identity,contacts
from power_groups import N,ROOTS
from inventory import sha
OUT=HERE/'parallel-source-necks-r1';LAYERS=['In1.Cu','In4.Cu','In2.Cu','In3.Cu']
def seeds(xs,layer,fr,other):
 out=[];target=unary_union([x['shape'] for x in other if x['layer']==layer])
 for x in xs:
  if x['layer']!=layer:continue
  av=x['shape'].intersection(fr).buffer(-.015)
  if av.is_empty:continue
  if not target.is_empty:
   p,_=nearest_points(av,target);out.append((tuple(p.coords[0]),x))
  p=av.representative_point();out.append((tuple(p.coords[0]),x))
 out.sort(key=lambda x:Point(x[0]).distance(target));return out[:80]
def main():
 if OUT.exists():raise ValueError('Refuse frozen proposal')
 OUT.mkdir();g,b=load();grp=pickle.loads((HERE/'power-groups-r1.pkl').read_bytes());gr=json.loads((HERE/'power-groups-r1.json').read_text(encoding='utf-8'));rec,trees=build(g,layers=set(LAYERS));res=json.loads((BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));dru=(BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text(encoding='utf-8');ex={}
 for ln in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',ln.strip())
  if m:ex[m[1]]={norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 outline=unary_union(poly(g['outline']));rows=[];adds=[];oldstep=S.STEP;S.STEP=.25
 try:
  for bank,goalid,win in [('FBG',0,box(60,150,255,238)),('FAG',0,box(250,150,455,238))]:
   net=N[bank];domain=g['domains_normalized'][net];rootpad=next(p for p in g['pads'] if (p['ref'],p['num'])==ROOTS[bank]);goal=grp[bank][goalid]
   for layer in LAYERS:
    obs=[];rpart=rec[layer]
    for i in trees[layer].query(win.buffer(10),predicate='intersects'):
     r=rpart[i]
     if norm(r['net'])==net or r['kind']=='fill':continue
     obs.append(r['shape'].buffer((.15 if r['domain']==domain else .6)+.03))
    for p in g['pads']:
     if norm(p['net'])!=net:obs.extend(q.buffer(.275) for q in poly(p.get('hole') or []) if q.intersects(win.buffer(10)))
    for v in g['vias']:
     if norm(v['net'])!=net and win.buffer(10).covers(Point(v['x'],v['y'])):obs.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275))
    for a in g['rule_areas']:
     if (a.get('no_tracks') or a.get('no_zones')) and layer in a['layers']:obs.extend(q.buffer(.025) for q in poly(a['outline']) if q.intersects(win))
    for a in res['keepouts']:
     if net not in ex.get(a['name'],set()) and layer in a['layers']:obs.extend(q.buffer(.025) for q in poly(a['outline']) if q.intersects(win))
    blocked=unary_union(obs);small=win.intersection(outline.buffer(-.526-1)).difference(blocked.buffer(1.001));wide=win.intersection(outline.buffer(-.526-3.6)).difference(blocked.buffer(3.601));gs=unary_union([r['shape'] for r in goal if r['layer']==layer]);pieces=[wide] if wide.geom_type=='Polygon' else list(wide.geoms);pieces=[q for q in pieces if q.intersection(gs).area>1e-8]
    row={'bank':bank,'source_PTH':list(ROOTS[bank]),'layer':layer,'source_annulus_native_flashed':layer in rootpad['layers'],'target_original_group':goalid,'window_mm':win.bounds,'neck_width_mm':2.,'wide_width_mm':7.2,'wide_goal_body_count':len(pieces),'sourcepad_start_mm':[rootpad['x'],rootpad['y']],'raw_native_net':rootpad['net'],'attempts':[]}
    startshape=unary_union(poly(rootpad['layers'][layer]));start=startshape.intersection(small).buffer(-.01)
    if start.is_empty or not pieces:row['verdict']='NO_SOURCE_NECK_OR_WIDE_DESTINATION_BODY';rows.append(row);print(bank,layer,row['verdict'],flush=True);continue
    # Select shortest neck into a wide legal body that already reaches the
    # actual old destination. Include extra seeds along wide/body boundary.
    target=unary_union(pieces);a,bb=nearest_points(start,target);ss=[(tuple(a.coords[0]),{'uuid':rootpad['uuid'],'kind':'pad'})];tt=[]
    for n,q in enumerate(pieces):
     _,p=nearest_points(start,q.buffer(-.01));tt.append((tuple(p.coords[0]),{'uuid':'WIDE_BODY_'+str(n),'kind':'proposed_wide_body'}))
     for p in list(q.exterior.coords)[::max(1,len(q.exterior.coords)//35)]:
      pt=Point(p);pt=q.buffer(-.015).intersection(pt.buffer(.1)).representative_point()
      if not pt.is_empty:tt.append((tuple(pt.coords[0]),{'uuid':'WIDE_BODY_'+str(n),'kind':'proposed_wide_body'}))
    path,search=S.astar(small.buffer(-.00001),ss,tt,time.monotonic()+15,node_cap=260000);row['attempts'].append({'stage':'2mm_source_neck','search':search})
    if not path or not small.covers(LineString(path['points_mm'])):row['verdict']='NO_SHORT_NECK_FOUND';rows.append(row);print(bank,layer,row['verdict'],flush=True);continue
    landing=path['points_mm'][-1];q=next(x for x in pieces if x.buffer(.0001).covers(Point(landing)));ends=seeds(goal,layer,q,[{'shape':Point(landing).buffer(.01),'layer':layer}]);spine,search2=S.astar(q.buffer(-.00001),[(landing,{'uuid':'WIDE_LANDING','kind':'proposed_wide_body'})],ends,time.monotonic()+20,node_cap=420000) if ends else (None,{'reason':'No exact wide native destination attachment'});row['attempts'].append({'stage':'7p2mm_destination_body','search':search2})
    if not spine or not q.covers(LineString(spine['points_mm'])):row['verdict']='SHORT_NECK_FOUND_WIDE_PATH_PENDING';row['neck']=path;rows.append(row);print(bank,layer,row['verdict'],flush=True);continue
    lines=[LineString(path['points_mm']),LineString(spine['points_mm'])];cu=unary_union([lines[0].buffer(1.,quad_segs=32),lines[1].buffer(3.6,quad_segs=32)]);hits=contacts(rec,trees,cu,layer);own=[r for r in hits if norm(r['net'])==net];foreign=[r for r in hits if norm(r['net'])!=net and r['kind']!='fill'];assert not foreign
    retreats=[]
    for i in trees[layer].query(cu.buffer(.65),predicate='intersects'):
     r=rec[layer][i]
     if r['kind']=='fill' and norm(r['net'])!=net:
      gap=.15 if r['domain']==domain else .6;area=cu.buffer(gap+.025).intersection(r['shape']).area
      if area>1e-8:retreats.append(identity(r)|{'required_retreat_area_mm2':area,'clearance_mm':gap})
    row.update(verdict='HOST_EXACT_SOURCE_PTH_NECK_AND_WIDE_NATIVE_DESTINATION',neck=path,wide_path=spine,neck_length_mm=lines[0].length,wide_length_mm=lines[1].length,own_contacts=own,mandatory_fill_retreat=retreats,each_branch_resistance60C_mohm=.57003672*(lines[0].length/2+lines[1].length/7.2),barrel_native_hole_diameter_mm=1.4)
    adds.append({'shape':cu,'layer':layer,'net':rootpad['net'],'kind':'prospective_copper','domain':domain,'uuid':'NEW_RETURN_'+bank+'_'+layer});(OUT/(bank+'-'+layer+'.wkb')).write_bytes(cu.wkb);rows.append(row);print(bank,layer,row['verdict'],row['neck_length_mm'],row['wide_length_mm'],flush=True)
    (OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
 finally:S.STEP=oldstep
 result={'board_sha256':g['sha256'],'rows':rows,'current_sharing_not_assumed':True,'full_signed_sheet_barrel_and_thermal_solve_pending':True,'no_new_return_holes':True,'all_original_copper_static_contacts_preserved':True,'native_jobs':0,'board_written':False,'native_fill_and_foreign_contact_retreat_not_yet_validated':True,'all_normal_power_roots_joined':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');data=pickle.dumps(adds,protocol=5);(OUT/'prospective-copper.pkl').write_bytes(data);(OUT/'binding.json').write_text(json.dumps({'cache_sha256':hashlib.sha256(data).hexdigest(),'receipt_sha256':sha(OUT/'receipt.json'),'original_board_sha256':g['sha256']},indent=1)+'\n',encoding='utf-8')
if __name__=='__main__':main()
