"""Nominate bounded short surface connections using exact current discrete Cu.

Actual full-BEFORE fills remain hard. Full-AFTER source/reference/current and
native checks are required before any adoption. No existing copper is edited.
"""
import sys,json,pickle,hashlib,time,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely import STRtree
from shapely.affinity import translate
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import guarded_power_projection_r44 as Z
K=N.K;L=N.L;sha=N.sha
OUT=H/'current-R753-short-logic-no-hole-surface-construction-r305'
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();started=time.monotonic();N.assert_R157_actual_before()
 base=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
 assert sha(base)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 _,h,_,_,_=pickle.loads(base.read_bytes())
 ep=H/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json'
 assert sha(ep)=='13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3';e=json.loads(ep.read_bytes())
 pp=H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json';poses=json.loads(pp.read_bytes())['pads']
 census=H/'R157-actual-native-remaining-pad-joins-same-surface-census-r282/actual-short-common-surface-pad-group-pairs-not-routes.json'
 pairs=[r for r in json.loads(census.read_bytes()) if r['native_domain']=='DOM_LOGIC' and r['centre_span_mm']<=5 and not any(v.startswith(('J15001.','J15002.')) for v in (r['native_left_pad'],r['native_right_pad']))][:100]
 # Controlled differential interfaces require a coupled pair design.
 pairs=[r for r in pairs if '/USB_' not in r['normalized_net'] and '/HDMI_' not in r['normalized_net'] and '/MIPI_' not in r['normalized_net']]
 native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());padnames={};seen={}
 for p in native['pads']:
  key=p['ref'],str(p['num']);i=seen.get(key,0);seen[key]=i+1;padnames[p['ref']+'.'+str(p['num'])+'#'+str(i)]=p
 roi=unary_union([box(min(r['left_actual_at_mm'][0],r['right_actual_at_mm'][0])-2,min(r['left_actual_at_mm'][1],r['right_actual_at_mm'][1])-2,max(r['left_actual_at_mm'][0],r['right_actual_at_mm'][0])+2,max(r['left_actual_at_mm'][1],r['right_actual_at_mm'][1])+2) for r in pairs])
 records={ly:[] for ly in ('F.Cu','B.Cu')};holes=[]
 def add(ly,uid,net,kind,s,extra=0.,local=0.):
  if s.intersects(roi):records[ly].append({'UUID':uid,'raw_net':net,'kind':kind,'shape':s,'extra':extra,'local':local})
 for uid,t in e['copper'].items():
  if t['kind']=='via':
   x,y=[z/1e6 for z in t['at_IU']];pt=Point(x,y)
   if not pt.buffer(1.5).intersects(roi):continue
   for ly in records:add(ly,uid,t['raw_net'],'current_integer_via',Z.bounded_buffer(pt,t['diameters_IU'][ly]/2e6))
   holes.append((uid,t['raw_net'],Z.bounded_buffer(pt,t['drill_IU']/2e6)))
  elif t['layer'] in records:
   assert t['kind']=='segment';aa=[z/1e6 for z in t['start_IU']];bb=[z/1e6 for z in t['end_IU']]
   axis=LineString([aa,bb])
   if axis.buffer(1.5).intersects(roi):add(t['layer'],uid,t['raw_net'],'current_integer_track',Z.bounded_buffer(axis,t['width_IU']/2e6))
 for p in h['pads']:
  obs=poses[p['uuid']];assert obs[1]==p['net'];dx=obs[2]/1e6-p['x'];dy=obs[3]/1e6-p['y']
  if dx or dy:assert p['ref'] in ('R10007','R10016')
  for ly in records:
   if ly not in obs[4]:continue
   for s in L.poly(p['layers'].get(ly,[])):add(ly,p['uuid'],p['net'],'native_pose_pad',translate(box(*s.bounds),dx,dy) if dx or dy else s,.005)
  for s in L.poly(p.get('hole')or[]):
   if s.intersects(roi):holes.append((p['uuid'],p['net'],s))
 for q in native['zones']:
  for ly in records:
   for s in L.poly(N.O.polys(q['fills'].get(ly,[]))):add(ly,q['uuid'],q['net'],'actual_FULL_before_fill',s,0.,float(q['clearance_mm']))
 reserve,exempt=K.A.reservations();rules=[]
 for rs,isreserve in ((h['rule_areas'],False),(reserve['keepouts'],True)):
  for r in rs:
   if not isreserve and not r.get('no_tracks'):continue
   for s in L.poly(r['outline']):
    if s.intersects(roi):rules.append((r,s,isreserve))
 trees={ly:STRtree([r['shape']for r in rows]) for ly,rows in records.items()}
 board=unary_union(L.poly(h['outline'])).buffer(-.525);accepted=[];attempts=[];dom=h['domains_normalized']
 for number,r in enumerate(pairs):
  a=r['left_actual_at_mm'];b=r['right_actual_at_mm'];net=r['normalized_net'];raw=r['raw_net']
  pa=padnames[r['native_left_pad']];pb=padnames[r['native_right_pad']]
  assert pa['net']==pb['net']==raw and pa['at']==a and pb['at']==b
  endpoint_uids=set()
  for np in (pa,pb):
   matches=[p['uuid'] for p in h['pads'] if p['ref']==np['ref'] and str(p['num'])==str(np['num']) and poses[p['uuid']][1]==np['net'] and poses[p['uuid']][2:4]==[int(round(v*1e6)) for v in np['at']]]
   assert len(matches)==1,('exact current native endpoint UUID',np['ref'],np['num'],matches)
   endpoint_uids.add(matches[0])
  options=[[a,b],[a,[a[0],b[1]],b],[a,[b[0],a[1]],b]];chosen=None;trials=[]
  for ly in r['common_native_surfaces']:
   for path in options:
    path=[v for i,v in enumerate(path) if i==0 or v!=path[i-1]];body=Z.bounded_buffer(LineString(path),.1);errors=[]
    if not board.covers(body):errors.append({'kind':'board_edge'})
    for j in trees[ly].query(body.buffer(1.025),predicate='intersects'):
     q=records[ly][int(j)]
     if L.norm(q['raw_net'])==net:continue
     gap=max(.15 if dom.get(L.norm(q['raw_net']))==dom[net] else .6,q['local'])+.025+q['extra'];distance=body.distance(q['shape'])
     if distance<gap:errors.append({'kind':q['kind'],'UUID':q['UUID'],'required_mm':gap,'actual_mm':distance})
    for uid,hn,s in holes:
     # Only the OWN endpoint plated hole can qualify its bounded endpoint;
     # these nominations keep that electrical/reference qualification OPEN.
     if uid in endpoint_uids:continue
     if body.distance(s)<.280:errors.append({'kind':'all_other_drill_guard','UUID':uid,'actual_mm':body.distance(s)})
    for rule,s,isreserve in rules:
     if ly in rule['layers'] and not(isreserve and net in exempt.get(rule['name'],set())) and body.distance(s)<.025:errors.append({'kind':'rule_area','name':rule.get('name')})
    for prior in accepted:
     if prior['layer']==ly and prior['normalized_net']!=net:
      gap=.175 if dom[prior['normalized_net']]==dom[net] else .625
      if body.distance(prior['body'])<gap:errors.append({'kind':'previous_new_nominee','index':prior['index']})
    trials.append({'layer':ly,'path':path,'geometry_errors':errors})
    if not errors:
     tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R305-current/'+str(number)+'/'+ly+'/'+str(i))),'net':raw,'layer':ly,'w':.2,'a':aa,'b':bb,'locked':False} for i,(aa,bb) in enumerate(zip(path,path[1:]))]
     chosen={'index':number,'raw_net':raw,'normalized_net':net,'layer':ly,'tracks':tracks,'body':body,'endpoints':list(endpoint_uids),'basis_pair':r,'source_reference_current_width_native_DRC_SI':'OPEN_MATCHING_FULL_AFTER_REQUIRED'};accepted.append(chosen);break
   if chosen:break
  attempts.append({'index':number,'raw_net':raw,'nominee':bool(chosen),'trials':trials})
  if number%10==0:print('R305_PHYSICAL',number,'nominees',len(accepted),flush=True)
 packet=OUT/'ONLY_NEW-short-surface-physical-nominees-NOT_MODEL.pkl';packet.write_bytes(pickle.dumps(accepted,protocol=5));put('attempts.json',attempts)
 put('receipt.json',{'status':'EXACT_CURRENT_DISCRETE_AND_FULL_BEFORE_FOREIGN_HARD_PHYSICAL_NOMINEES_ONLY','candidate_SHA256':e['board_sha256'],'Cu_ledger_SHA256':sha(ep),'pose_SHA256':sha(pp),'census_SHA256':sha(census),'native_FULL_BEFORE_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'pairs_screened':len(pairs),'nominees':len(accepted),'packet_SHA256':sha(packet),'new_tracks':sum(len(r['tracks'])for r in accepted),'new_vias':0,'existing_Cu_removed':0,'ALL_matching_FULL_AFTER_source_fill_reference_and_power_ground_current_width_native_rules':'OPEN','own_PTH_endpoint_drill_SOURCE_bound':'OPEN_NOT_WAIVED','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R305_COMPLETE',len(accepted),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
