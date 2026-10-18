"""Reuse exact saved DI6 signal route and nominate compliant source return.

No original geometry is restored or ripped up. Native R157 masks bind any
existing return nomination. All current Cu/filled records/owned roles stay
hard for this initial screen. A positive nomination is not final source,
neighbor-reference, native or current acceptance.
"""
from pathlib import Path
import sys,json,pickle,hashlib,math,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_ao1_positive_operation_r4 as SERIAL
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI6-saved-route-current-policy-return-nomination-r568'
LG='/LOGIC_GND';NET='/motherboard_di/DI6_LOGIC'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return{'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':list(s.bounds)if not s.is_empty else None,'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or s==v;pins[str(p.resolve())]=v;return p
 mp=pin(H/'DIC-retired-cutter-policy-coupled-current-r556/model.pkl','95d1636e90b8d11530cbc6ba461c60f7e68272e08d1e7cd4b5863bf0a43b46d5');g,h,b,q,cur=pickle.loads(mp.read_bytes());gp=pin(H/'DIC-policy-coupled-actual-current-independent-r562/actual-new-all-drilled-groups.pkl','2c1e577fdad9358b88578a6338f934924e6ced9186ca8dc06a37e652bba9ec8c');groups=pickle.loads(gp.read_bytes());root=K.root(groups[LG],'J11001','2');refs={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')}
 rp=pin(H/'di6-native-owned-ledger-r14/receipt.json','6d7dcdc50a10393138761a0067fb73325eace8307800358d72723adcbb1afd79');rr=json.loads(rp.read_bytes());sp=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');source=sp.read_bytes();native=K.C.inventory(source)[3];ident=K.A.N.SourceNets(source);tracks=[];vias=[];chunks={}
 for r in rr['exact_new_chunk_files']:
  cp=pin(r['chunk_file'],r['chunk_sha256']);ch=cp.read_bytes();uid=r['UUID'];assert uid not in native and uid not in{x['uuid']for x in h['tracks']+h['vias']};p=K.A.G.parse(uid,ch,{});chunks[uid]=ch
  if p['kind']=='segment':tracks.append({'uuid':uid,'net':ident.raw(p['net']),'layer':p['layer'],'w':p['w'],'a':p['a'],'b':p['b']})
  else:vias.append({'uuid':uid,'net':ident.raw(p['net']),'x':p['at'][0],'y':p['at'][1],'d':p['d'],'drill':p['drill'],'flashed':list(K.LAYERS)})
 assert len(tracks)==9 and len(vias)==2;signal=next(v for v in vias if K.L.norm(v['net'])==NET);oldreturn=next(v for v in vias if K.L.norm(v['net'])==LG)
 maskfile=pin(P/'R155-known-reference-native-diagnostic-r157/measure/actual-full-refill-via-flashes.json');masks=json.loads(maskfile.read_bytes())['vias'];assert signal['uuid']not in masks
 allg={**h,'tracks':h['tracks']+tracks,'vias':h['vias']+[signal],'zones':[]};rec,trees=K.F.build(allg);holes,holetree=K.hole_context(allg);smd=[(p,s)for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for s in K.L.poly(rs)];smdtree=STRtree([s for p,s in smd]);viapoints=[Point(v['x'],v['y'])for v in allg['vias']];vtree=STRtree(viapoints);fill={ly:[]for ly in K.LAYERS}
 for z in cur['zones']:
  for ly,rs in z['fills'].items():fill[ly].extend((z,s)for s in K.L.poly(rs))
 ft={ly:STRtree([s for z,s in rs])for ly,rs in fill.items()};domain=h['domains_normalized'];req=lambda n,n2:.15 if domain[K.L.norm(n)]==domain[K.L.norm(n2)]else .6;reservations,exempt=K.A.reservations()
 def guard(x,own_signal=True):
  via='d'in x;lyrs=K.LAYERS if via else[x['layer']];axis=Point(x['x'],x['y'])if via else LineString([x['a'],x['b']]);r=x['d']/2 if via else x['w']/2;body=axis.buffer(r,quad_segs=128);bad=[]
  for ly in lyrs:
   for j in trees[ly].query(body.buffer(.9),predicate='intersects'):
    row=rec[ly][int(j)];n=K.L.norm(row['net'])
    if row['uuid']==x['uuid']or n==K.L.norm(x['net']):continue
    other=row.get('source')
    if row['kind']=='via':gap=axis.distance(Point(other['x'],other['y']))-r-(other['d']if ly in other['flashed']else other['drill'])/2
    elif row['kind']=='track'and not other.get('m'):gap=axis.distance(LineString([other['a'],other['b']]))-r-other['w']/2
    else:gap=axis.distance(row['shape'])-r
    need=req(n,x['net'])+.025
    if gap<need:bad.append({'kind':'TRUE_'+row['kind'],'layer':ly,'UUID':row['uuid'],'gap_mm':gap,'required_mm':need})
   for j in ft[ly].query(body.buffer(.9),predicate='intersects'):
    z,s=fill[ly][int(j)]
    if K.L.norm(z['net'])==K.L.norm(x['net']):continue
    gap=axis.distance(s)-r;need=max(float(z['clearance_mm']),req(z['net'],x['net']))+.025
    if gap<need:bad.append({'kind':'CURRENT_NATIVE_OR_OWNED_FILL_HARD','layer':ly,'UUID':z['uuid'],'gap_mm':gap,'required_mm':need})
   for z in q:
    if z['layer']!=ly or K.L.norm(z['net'])==K.L.norm(x['net']):continue
    for role in('shape','zone_outline_shape'):
     gap=axis.distance(z[role])-r;need=max(float(z['clearance_mm']),req(z['net'],x['net']))+.025
     if gap<need:bad.append({'kind':'CURRENT_OWNED_'+role,'layer':ly,'UUID':z['uuid'],'gap_mm':gap,'required_mm':need})
   for area in h['rule_areas']:
    if ly in area['layers']and area.get('no_vias'if via else'no_tracks')and any(body.intersects(s)for s in K.L.poly(area['outline'])):bad.append({'kind':'NATIVE_KEEPOUT','layer':ly,'UUID':area['uuid']})
   for area in reservations['keepouts']:
    if ly in area['layers']and K.L.norm(x['net'])not in exempt.get(area['name'],set())and any(body.distance(s)<.025 for s in K.L.poly(area['outline'])):bad.append({'kind':'FROZEN_RESERVE','layer':ly,'name':area['name']})
  if via:
   for j in vtree.query(axis.buffer(.815),predicate='intersects'):
    v=allg['vias'][int(j)]
    if v['uuid']==x['uuid']:continue
    gap=axis.distance(viapoints[int(j)]);edge=gap-(v['drill']+x['drill'])/2
    if gap<.815 or edge<.280:bad.append({'kind':'ORDINARY_PITCH_OR_DRILL_EDGE','UUID':v['uuid'],'pitch_mm':gap,'drill_edge_mm':edge})
   for j in smdtree.query(axis.buffer(x['drill']/2+.28),predicate='intersects'):
    p,s=smd[int(j)];gap=axis.distance(s)-x['drill']/2
    if gap<.28:bad.append({'kind':'ALL_SMD_DRILL_APERTURE','UUID':p['uuid'],'gap_mm':gap,'required_mm':.28})
   for j in holetree.query(axis.buffer(x['drill']/2+.28),predicate='intersects'):
    if axis.distance(holes[int(j)])-x['drill']/2<.28:bad.append({'kind':'EVERY_HOLE_EDGE','hole_index':int(j),'gap_mm':axis.distance(holes[int(j)])-x['drill']/2,'required_mm':.28})
  return bad
 trackchecks=[{'UUID':t['uuid'],'layer':t['layer'],'guard_failures':guard(t)}for t in tracks];signalbad=guard(signal);put(OUT/'exact-saved-nine-track-and-signal-hard-current-screen.json',{'tracks':trackchecks,'signal':signal,'signal_guard_failures':signalbad})
 sigdisk=K.Z.bounded_disk(signal,.525);refsafter={ly:s.difference(sigdisk)for ly,s in refs.items()};source_existing=[]
 for v in h['vias']:
  if K.L.norm(v['net'])!=LG:continue
  d=math.dist([v['x'],v['y']],[signal['x'],signal['y']])
  if not .90<=d<=1.0:continue
  actual=masks.get(v['uuid'],[]);ann=K.Z.bounded_disk(v,v['d']/2).difference(K.Z.bounded_disk(v,v['drill']/2));contact={ly:ann.intersection(refsafter[ly])for ly in refsafter};source_existing.append({'UUID':v['uuid'],'at_mm':[v['x'],v['y']],'distance_mm':d,'actual_R157_flash_layers':actual,'finite_current_host_J1_reference_annuli':{ly:info(s)for ly,s in contact.items()},'existing_compliant_native_mask_and_host_source_nominee':all(ly in actual and not contact[ly].is_empty and contact[ly].area>0 for ly in refsafter),'native_fresh_final_source_after_all_new_cuts':'OPEN'})
 put(OUT/'all-existing-.90-to-1.0-source-return-census.json',source_existing);selected=None;attempts=[]
 if not any(z['existing_compliant_native_mask_and_host_source_nominee']for z in source_existing):
  base=math.atan2(oldreturn['y']-signal['y'],oldreturn['x']-signal['x']);points=[]
  for rad in(.925,.95,.975,.901,.999):
   for k in range(180):
    angle=base+2*math.pi*k/180;x=round(signal['x']+rad*math.cos(angle),6);y=round(signal['y']+rad*math.sin(angle),6);points.append((math.dist([x,y],[oldreturn['x'],oldreturn['y']]),x,y))
  for _,x,y in sorted(set(points)):
   v={**oldreturn,'x':x,'y':y};d=math.dist([x,y],[signal['x'],signal['y']]);assert .90<=d<=1.0;bad=guard(v);ann=K.Z.bounded_disk(v,.25).difference(K.Z.bounded_disk(v,.1));contacts={ly:ann.intersection(refsafter[ly])for ly in refsafter};rooted=all(not z.is_empty and z.area>0 for z in contacts.values());row={'at_mm':[x,y],'distance_mm':d,'guard_failures':bad,'finite_current_host_J1_source_annuli':{ly:info(s)for ly,s in contacts.items()},'both_used_reference_planes_finite':rooted};attempts.append(row)
   if bad or not rooted:continue
   selected=v;gen,ch=SERIAL.serial_via(ident,LG,[x,y]);ch=ch.replace(gen.encode(),v['uuid'].encode());chunks[v['uuid']]=ch;print('R568_POSITIVE_RETURN',x,y,d,flush=True);break
 else:selected={'existing_return_UUIDs':[z['UUID']for z in source_existing if z['existing_compliant_native_mask_and_host_source_nominee']]}
 put(OUT/'finite-NEW-source-return-attempts.json',attempts);packet=OUT/'only-saved-nine-tracks-one-signal-and-policy-return-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':tracks,'signal_via':signal,'selected_return':selected,'exact_new_chunks':chunks if selected else{},'no_original_deletes':True,'saved_R14_oldreturn_policy_failed_mm':math.dist([signal['x'],signal['y']],[oldreturn['x'],oldreturn['y']])},protocol=5))
 allerrors=sum(len(r['guard_failures'])for r in trackchecks)+len(signalbad);verdict='SAVED_DI6_SIGNAL_ROUTE_AND_COMPLIANT_SOURCE_RETURN_INITIAL_HARD_GEOMETRY_NOMINEE'if selected and not allerrors else'SAVED_DI6_FRESH_CURRENT_HARD_GEOMETRY_REQUIRES_SCOPED_REPAIR'
 result={'verdict':verdict,'exact_current_model_SHA256':sha(mp),'source_original_eedf_SHA256':sha(sp),'saved_R14_recipe_SHA256':sha(rp),'original_R06_DI6_target_relationship':'U13001.12 versus R8207.1/U17003.1/U8004.4','ordinary_source_window_mm':[.9,1.0],'existing_return_census':source_existing,'selected_return':selected,'saved_signal_path_hard_failure_count':allerrors,'actual_target_existing_pair_R22_distance_mm':.9708243919473877,'exact_original583bf_conflicting_via_remains_withheld':True,'all_original_fault_current_Cu_preserved':True,'signal_layer_legs':2,'all_saved_new_and_old_matched_native_reference_failures_preserved':True,'old_MOTION237_remote210nm_source_delta_from_old_scopednative_not_waived':True,'full_fresh_drilled_all_relationship_source_oldref_newbody_native_SI_current_minfeature':'OPEN','sparse_nominee_file':str(packet.resolve()),'sparse_nominee_SHA256':sha(packet),'input_SHA256':pins,'native_jobs':0,'board_source_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-st};put(OUT/'receipt.json',result);print('R568_COMPLETE',sha(OUT/'receipt.json'),verdict,'signal_route_errors',allerrors,'return',bool(selected),flush=True)
if __name__=='__main__':main()
