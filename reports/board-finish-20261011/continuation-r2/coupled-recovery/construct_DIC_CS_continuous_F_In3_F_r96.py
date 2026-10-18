"""DIC-CS recovery from actual current copper, using one transport layer.

Existing In3 annuli are preferred. At most two new F/In3 transitions are
nominated with real finite In1/In4 returns and exact source raw net chunks.
No rip-up, native launch, parent model mutation or acceptance.
"""
import sys,json,pickle,time,math,itertools
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import audit_c10036_r24_full_independent_r30 as Q
import construct_di6_direct_source_escape_r5 as K
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
C=A.C;NET='/motherboard_io_control/DIC_IOL1_CS_BUFFER';GND='/LOGIC_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def main():
 started=time.monotonic();out=HERE/'DIC-CS-existing-In3-or-B-dive-nomination-r96.json';assert not out.exists();A.read(__file__);rp=HERE/'di15-safe-root-r22-DI6-bind-r62.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='a8234fa46de66b43eeefcf2bfbdb3d8563bf862a2ce60c46212b17e77ea314be';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h=cur['h'];g=cur['after'];domains=h['domains_normalized'];source=A.read(cur['binding']['exact_native_discrete_board_file']);identity=A.N.SourceNets(source);policy={L.norm(n):v for n,v in json.loads(A.read(A.S.CONTROLLED))['nets'].items()}.get(NET);assert policy is None or policy.get('class') in(None,'NONE');assert domains[NET]==domains[GND]
 graph=json.loads(A.read(HERE/'conflict-graph.json'));loss=next(q for q in graph['lost_route_rows'] if q['net']==NET);labels=loss['native_lost_relationships'][0]['r06_pad_relationship'];desired=set()
 for label in labels:
  pref,ordinal=label.rsplit('#',1);ref,pin=pref.rsplit('.',1);assert ordinal=='0';pp=[p for p in h['pads'] if L.norm(p['net'])==NET and(p['ref'],str(p['num']))==(ref,pin)];assert len(pp)==1;desired.add(pp[0]['uuid'])
 _,groups=Q.physical(g,NET);wanted=[xs for xs in groups if {q['uuid'] for q in xs if q['kind']=='pad'}&desired];assert len(wanted)==2;term={layer:[unary_union([q['shape'] for q in xs if q['layer']==layer]) for xs in wanted] for layer in('F.Cu','In3.Cu')};root=cur['root'];planes={l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==l]) for l in('In1.Cu','In4.Cu')};ref=planes['In4.Cu'];allterm=unary_union(term['F.Cu']);xmin,ymin,xmax,ymax=allterm.bounds;win=box(xmin-8,ymin-8,xmax+8,ymax+8);rec,trees=F.build({**h,'zones':[]});reserve,exempt=A.reservations();records={l:[rec[l][int(i)] for i in trees[l].query(win.buffer(2),predicate='intersects')] for l in LAYERS};holes=[];smd=[]
 for v in h['vias']:
  if Point(v['x'],v['y']).distance(win)<2:holes.append((v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)))
 for p in h['pads']:
  holes.extend((p['uuid'],L.norm(p['net']),q) for q in L.poly(p.get('hole') or []) if q.distance(win)<2)
  if p['smd']:smd.extend(q for layer,ps in p['layers'].items() if layer in('F.Cu','B.Cu') for q in L.poly(ps) if q.distance(win)<2)
 hard=[]
 for q in h['rule_areas']:
  if q.get('no_tracks') or q.get('no_vias'):
   hard.extend({'shape':sh,'layers':q['layers'],'no_tracks':q.get('no_tracks'),'no_vias':q.get('no_vias'),'exempt':set()} for sh in L.poly(q['outline']) if sh.distance(win)<2)
 for q in reserve['keepouts']:hard.extend({'shape':sh,'layers':q['layers'],'no_tracks':True,'no_vias':True,'exempt':exempt.get(q['name'],set())} for sh in L.poly(q['outline']) if sh.distance(win)<2)
 def obstacle(net,layer,via=False):
  obs=[];radius=.25 if via else 0
  for q in records[layer]:
   n=L.norm(q['net'])
   if n!=net:obs.append(q['shape'].buffer(radius+(.15 if domains.get(n)==domains.get(net) else .6)+.030,quad_segs=128))
  for z in cur['zones']:
   n=L.norm(z['net'])
   if z['layer']!=layer or n==net or z['shape'].distance(win)>2:continue
   obs.append(z['shape'].buffer(radius+max(.15 if domains.get(n)==domains.get(net) else .6,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
  for z in g['zones']:
   n=L.norm(z['net'])
   if n==net or domains.get(n)==domains.get(net):continue
   for sh in L.poly(z['fills'].get(layer,[])):
    if sh.distance(win)<2:obs.append(sh.buffer(radius+max(.6,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
  obs.extend(sh.buffer(.280 if not via else .380,quad_segs=128) for u,n,sh in holes if via or n!=net)
  obs.extend(q['shape'].buffer(.275 if via else .025,quad_segs=128) for q in hard if q['no_vias' if via else 'no_tracks'] and layer in q['layers'] and net not in q['exempt'])
  return unary_union(obs)
 free={l:win.difference(obstacle(NET,l)).buffer(-.105,quad_segs=128).intersection(planes['In1.Cu' if l=='F.Cu' else 'In4.Cu'].intersection(win.buffer(1)).buffer(-.105,quad_segs=128)) for l in('F.Cu','In3.Cu')}
 via={}
 for net in(NET,GND):
  reg=win
  for layer in LAYERS:reg=reg.difference(obstacle(net,layer,True))
  reg=reg.difference(unary_union([q.buffer(.380,quad_segs=128) for q in smd])).difference(unary_union([Point(v['x'],v['y']).buffer(.815,quad_segs=128) for v in h['vias'] if Point(v['x'],v['y']).distance(win)<2]));via[net]=reg
 # Real existing return annuli are useful only on both planes and at J1.
 roots_by_id={}
 for q in root:
  if q['kind']=='via' and q['layer'] in planes:roots_by_id.setdefault(q['uuid'],{})[q['layer']]=q['shape']
 oldreturns=[]
 for v in h['vias']:
  if L.norm(v['net'])!=GND or v['uuid'] not in roots_by_id or Point(v['x'],v['y']).distance(win)>2:continue
  pp=roots_by_id[v['uuid']];areas={l:pp[l].intersection(planes[l]).area if l in pp else 0 for l in planes}
  if all(x>.004 for x in areas.values()):oldreturns.append({'uuid':v['uuid'],'at_mm':[v['x'],v['y']],'diameter_mm':v['d'],'drill_mm':v['drill'],'finite_actual_rooted_annular_contact_mm2':areas})
 def return_options(signal_region):
  result=[]
  for ret in oldreturns:
   p=Point(ret['at_mm']);lower=.25+ret['diameter_mm']/2+.15+.030;region=signal_region.intersection(p.buffer(1,quad_segs=128).difference(p.buffer(max(.815,lower),quad_segs=128)))
   for s in K.sites(region,[p.x-.9,p.y],2):result.append({'signal':s['at_mm'],'return':ret['at_mm'],'return_new':False,'old_return_uuid':ret['uuid'],'finite_return_contact':ret['finite_actual_rooted_annular_contact_mm2']})
  for s in K.sites(signal_region,list(signal_region.centroid.coords)[0],6):
   p=Point(s['at_mm']);rgn=via[GND].intersection(p.buffer(1,quad_segs=128).difference(p.buffer(.825,quad_segs=128)))
   for ret in K.sites(rgn,[p.x-.9,p.y],2):
    rp=Point(ret['at_mm']);ann=rp.buffer(.25,quad_segs=128).difference(rp.buffer(.1,quad_segs=128));area={l:ann.intersection(planes[l]).area for l in planes}
    if all(x>.004 for x in area.values()):result.append({'signal':s['at_mm'],'return':ret['at_mm'],'return_new':True,'old_return_uuid':None,'finite_return_contact':area})
  return result[:16]
 endpoint_options=[];elig=[];nominees=[]
 for transport_index,transport in enumerate(K.pieces(free['In3.Cu'])):
  sideopts=[]
  for side in range(2):
   direct=term['In3.Cu'][side].buffer(-.05,quad_segs=128).intersection(transport);preferred=list(term['F.Cu'][side].centroid.coords)[0];opts=[{'at_mm':q['at_mm'],'new_signal':False,'F_attachment':None,'pair':None} for q in K.sites(direct,preferred,2)];bc=[]
   fa=term['F.Cu'][side].buffer(-.05,quad_segs=128).intersection(free['F.Cu'])
   for part in K.pieces(free['F.Cu']):
    att=fa.intersection(part)
    if att.is_empty:continue
    v=via[NET].intersection(part).intersection(transport).intersection(Point(term['F.Cu'][side].centroid).buffer(5,quad_segs=128))
    if v.is_empty:continue
    pairs=return_options(v);bc.append({'attachment_mm2':att.area,'via_region_mm2':v.area,'paired_options':len(pairs)})
    for pair in pairs[:6]:
     pa=nearest_points(att,Point(pair['signal']))[0];opts.append({'at_mm':pair['signal'],'new_signal':True,'F_attachment':[round(pa.x,6),round(pa.y,6)],'pair':pair})
   sideopts.append(opts)
   if opts or bc or not direct.is_empty:elig.append({'transport_component':transport_index,'side':side,'direct_actual_In3_attach_mm2':direct.area,'F_components':bc,'options_count':len(opts)})
  endpoint_options.append({'transport_component':transport_index,'side_options':sideopts})
  if any(not opts for opts in sideopts):continue
  for a,b in itertools.product(*sideopts):
   new=[o['at_mm'] for o in(a,b) if o['new_signal']]+[o['pair']['return'] for o in(a,b) if o['new_signal'] and o['pair']['return_new']]
   if any(math.dist(x,y)<.81 for x,y in itertools.combinations(new,2)):continue
   nominees.append({'transport_component':transport_index,'endpoints':[a,b],'score':sum(o['new_signal'] for o in(a,b))*100+math.dist(a['at_mm'],b['at_mm'])})
 print('DIC-CS_IN3_ELIGIBILITY',json.dumps(elig),'NOMINEES',len(nominees),flush=True);attempts=[];selected=None
 for nom in sorted(nominees,key=lambda q:q['score'])[:8]:
  row={**nom,'paths':[]};attempts.append(row);returns=[o['pair']['return'] for o in nom['endpoints'] if o['new_signal'] and o['pair']['return_new']];cut=unary_union([Point(p).buffer(.535,quad_segs=128) for p in returns]);pairs=[('In3.Cu',nom['endpoints'][0]['at_mm'],nom['endpoints'][1]['at_mm'])]+[('F.Cu',o['F_attachment'],o['at_mm']) for o in nom['endpoints'] if o['new_signal']]
  for layer,a,b in pairs:
   parts=[p for p in K.pieces(free[layer].difference(cut)) if p.covers(Point(a)) and p.covers(Point(b))]
   if not parts:row['failed_layer']=layer;break
   pts,search=T.route(parts[0],tuple(a),tuple(b));pts=[[round(x,6),round(y,6)] for x,y in pts]
   if len(pts)<2:row['failed_layer']=layer;break
   body=unary_union([A.shape({'kind':'segment','a':x,'b':y,'w':.2}) for x,y in zip(pts,pts[1:])]);selected_reference_layer='In1.Cu' if layer=='F.Cu' else 'In4.Cu';gap=body.difference(planes[selected_reference_layer]);row['paths'].append({'source_reference_layer':selected_reference_layer,'layer':layer,'points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length,'full_body_actual_adjacent_source_reference_gap_mm2':gap.area,'search':search})
   if not gap.is_empty:row['failed_reference']=layer;break
  if len(row['paths'])==len(pairs) and not row.get('failed_reference'):selected=row;break
 cache=HERE/'DIC-CS-existing-In3-or-B-dive-r96-model.pkl';assert not cache.exists();cache.write_bytes(pickle.dumps({'current':cur,'free':free,'via':via,'refs':planes,'terms':term,'endpoint_options':endpoint_options,'existing_returns':oldreturns,'root':root},protocol=5));report={'verdict':'DIC-CS_CONCRETE_CURRENT_CONTACT_DIVE_NOMINATED_UNQUALIFIED' if selected else 'DIC-CS_CURRENT_CONTACT_DIVE_BOUNDED_INCOMPLETE','R62_receipt_sha256':C.sha(A.read(rp)),'current_model_sha256':r['model_sha256'],'source_parent_sha256':C.sha(source),'raw_net':identity.raw(NET),'policy':policy,'original_r06_relationship':labels,'exact_current_pad_UUIDs':sorted(desired),'eligibility':elig,'nominees_count':len(nominees),'attempts':attempts,'selected':selected,'oldCu_deletes':0,'max_layer_segments':3,'new_signal_vias_at_most':2,'new_paired_return_native_flash_current_full_contacts_source_groups_all_reference_SI_DRC':'ODIC-CS','saved_model':str(cache),'saved_model_sha256':C.sha(cache.read_bytes()),'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'eligibility':elig,'selected':selected}),flush=True)
if __name__=='__main__':main()
