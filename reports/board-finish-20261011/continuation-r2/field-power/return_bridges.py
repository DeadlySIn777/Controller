"""Concrete source-rooted field return bridges with current sizing and contacts."""
import copy,json,pickle,hashlib,re,time,math
from collections import defaultdict
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import affinity
from contact_layout import HERE,BASE,load,build,norm,poly,S,identity,contacts
from power_groups import key,N,ROOTS
from inventory import sha
OUT=HERE/'return-bridges-r1.json'
def main():
 if OUT.exists():raise ValueError('Refuse prior bridge proposal')
 g,b=load();bd=json.loads((HERE/'power-groups-r1-binding.json').read_text(encoding='utf-8'));raw=(HERE/'power-groups-r1.pkl').read_bytes();assert hashlib.sha256(raw).hexdigest()==bd['cache_sha256'];groups=pickle.loads(raw);gr=json.loads((HERE/'power-groups-r1.json').read_text(encoding='utf-8'))
 static,trees=build(g);layers=['In1.Cu','In4.Cu','In2.Cu','In3.Cu'];hard=defaultdict(list);reserv=json.loads((BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));dru=(BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text(encoding='utf-8');ex={}
 for ln in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',ln.strip())
  if m:ex[m[1]]={norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 for a in g['rule_areas']:
  if a.get('no_tracks') or a.get('no_zones'):
   for l in a['layers']:hard[l].extend((q,a.get('name','native'),set()) for q in poly(a['outline']))
 for a in reserv['keepouts']:
  for l in a['layers']:hard[l].extend((q,a['name'],ex.get(a['name'],set())) for q in poly(a['outline']))
 outline=unary_union(poly(g['outline']));adds=[];result={'board_sha256':g['sha256'],'source_roots':ROOTS,'net_raw_names':{},'rows':[],'native_jobs':0,'board_written':False,'fixed_native_static_copper_changed':False,'new_vias':0,'retained_keepouts_with_exact_existing_net_exemptions':True,'plane_refill_pending':True,'native_or_physical_current_qualification':False}
 def free(net,layer,w,win):
  obs=[]
  for i in trees[layer].query(win.buffer(w+1),predicate='intersects'):
   r=static[layer][i]
   if norm(r['net'])==net or r['kind']=='fill':continue
   obs.append(r['shape'].buffer((.15 if r['domain']==g['domains_normalized'].get(net) else .6)+w/2+.03))
  for p in g['pads']:
   if norm(p['net'])==net:continue
   for q in poly(p.get('hole') or []):
    if q.intersects(win):obs.append(q.buffer(.25+w/2+.025))
  for v in g['vias']:
   if norm(v['net'])!=net and win.covers(Point(v['x'],v['y'])):obs.append(Point(v['x'],v['y']).buffer(v['drill']/2+.25+w/2+.025))
  for r in adds:
   if r['layer']==layer and norm(r['net'])!=net:obs.append(r['shape'].buffer(.6+w/2+.025))
  obs.extend(sh.buffer(w/2+.025) for sh,name,allowed in hard[layer] if net not in allowed and sh.intersects(win))
  return win.intersection(outline.buffer(-.5-w/2-.025)).difference(unary_union(obs))
 def seeds(xs,layer,fr,other):
  out=[];shape=unary_union([x['shape'] for x in other if x['layer']==layer]);
  for x in xs:
   if x['layer']!=layer:continue
   av=x['shape'].intersection(fr).buffer(-.015)
   if av.is_empty:continue
   if not shape.is_empty:
    p,_=nearest_points(av,shape);out.append((tuple(p.coords[0]),x))
   p=av.representative_point();out.append((tuple(p.coords[0]),x))
  if not shape.is_empty:out.sort(key=lambda p:Point(p[0]).distance(shape))
  return out[:80]
 oldstep=S.STEP;S.STEP=.5
 try:
  for bank in ['FBG','FAG']:
   net=N[bank];allg=groups[bank];rootid=gr['nets'][bank]['source_root_group'];joined={rootid};rootrows=list(allg[rootid]);pending=[i for i,xs in enumerate(allg) if i!=rootid and any(x['kind']=='pad' for x in xs) and sum(x['shape'].area for x in xs if x['kind']=='fill')>50]
   result['net_raw_names'][bank]=sorted({r['net'] for r in rootrows});assert len(result['net_raw_names'][bank])==1
   # Merge the principal source-isolated plane groups before small-pad fanout.
   for batch in range(min(12,len(pending))):
    goalid=min(pending,key=lambda i:min((unary_union([r['shape'] for r in rootrows if r['layer']==l]).distance(unary_union([r['shape'] for r in allg[i] if r['layer']==l])) for l in layers if any(r['layer']==l for r in rootrows) and any(r['layer']==l for r in allg[i])),default=1e9));goal=allg[goalid];row={'bank':bank,'canonical_net':net,'raw_native_net':result['net_raw_names'][bank][0],'from_source_root':list(ROOTS[bank]),'joined_ancestor_groups':sorted(joined),'to_group':goalid,'to_pads':sorted({(r['ref'],r['pin']) for r in goal if r['kind']=='pad'}),'copper_capacity_policy_a':6.5,'width_mm':7.2,'current_basis':'7.18938mm raw minimum old35um/10C width fit, rounded upward7.2mm. Conservative full-bank6.5A corridor target, not a device rating or equal current-sharing claim.','attempts':[]}
    for layer in layers:
     if not any(r['layer']==layer for r in rootrows) or not any(r['layer']==layer for r in goal):continue
     rs=unary_union([r['shape'] for r in rootrows if r['layer']==layer]);gs=unary_union([r['shape'] for r in goal if r['layer']==layer]);aa,bb=nearest_points(rs,gs)
     # A materially broader current-carrying plane search, not a repeated
     # failed13 narrow outer-window spine screen.
     for margin in [30,80]:
      win=LineString([aa,bb]).envelope.buffer(margin,cap_style=3).envelope;fr=free(net,layer,7.2,win);ss,tt=seeds(rootrows,layer,fr,goal),seeds(goal,layer,fr,rootrows)
      path,search=S.astar(fr.buffer(-.00001),ss,tt,time.monotonic()+8,node_cap=180000) if ss and tt else (None,{'reason':'No exact wide-copper attachment','nodes':0})
      row['attempts'].append({'layer':layer,'margin_mm':margin,'seeds':[len(ss),len(tt)],'search':search})
      if not path or not fr.covers(LineString(path['points_mm'])):continue
      ln=LineString(path['points_mm']);copper=ln.buffer(3.6,quad_segs=32);retreat=[]
      for i in trees[layer].query(copper.buffer(.65),predicate='intersects'):
       r=static[layer][i]
       if r['kind']=='fill' and norm(r['net'])!=net:
        gap=.15 if r['domain']==g['domains_normalized'].get(net) else .6;void=copper.buffer(gap+.025);area=void.intersection(r['shape']).area
        if area>1e-9:retreat.append(identity(r)|{'required_retreat_area_mm2':area,'clearance_mm':gap,'exact_fill_contact_is_prospective_void_only':True})
      hit=contacts(static,trees,copper,layer);own=[r for r in hit if norm(r['net'])==net];foreign=[r for r in hit if norm(r['net'])!=net and r['kind']!='fill'];assert not foreign
      added={'shape':copper,'layer':layer,'net':result['net_raw_names'][bank][0],'kind':'track','domain':g['domains_normalized'][net],'uuid':'PROPOSED-'+bank+'-'+str(batch)};adds.append(added);rootrows+=goal+[added];joined.add(goalid)
      row.update(verdict='HOST_SOURCE_ROOTED_PLANE_BRIDGE',layer=layer,path=path,length_mm=ln.length,resistance60C_mohm=.57003672*ln.length/7.2,drop_at_capacity_target_v=.00057003672*ln.length/7.2*6.5,exact_own_copper_contacts=own,mandatory_foreign_and_same_domain_fill_retreat=retreat,reference_and_old_foreign_rail_qualification='OPEN; subtract these exact prospective voids and replay old named-pad relationships/rail capacity before native refill adoption.');break
     if 'verdict' in row:break
    if 'verdict' not in row:row['verdict']='NO_WIDE_PATH_IN_FOUR_LAYERS_TWO_BROAD_WINDOWS'
    pending.remove(goalid);result['rows'].append(row);(HERE/'return-bridges-checkpoint.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(bank,goalid,row['verdict'],flush=True)
   result.setdefault('joined_source_root_groups',{})[bank]=sorted(joined)
 finally:S.STEP=oldstep
 result['all_normal_return_pad_groups_connected']=False;result['remaining_small_and_failed_groups']='Each remaining pad component must receive source-rooted current-sized fanout or qualified plane join; this macro pass does not credit proximity.'
 OUT.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');data=pickle.dumps({'adds':adds,'joined':result['joined_source_root_groups']},protocol=5);(HERE/'return-bridges-r1.pkl').write_bytes(data);(HERE/'return-bridges-r1-binding.json').write_text(json.dumps({'cache_sha256':hashlib.sha256(data).hexdigest(),'receipt_sha256':sha(OUT),'board_sha256':g['sha256']},indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'bridges':sum(r['verdict']=='HOST_SOURCE_ROOTED_PLANE_BRIDGE' for r in result['rows']),'groups_attempted':len(result['rows']),'native_jobs':0}))
if __name__=='__main__':main()
