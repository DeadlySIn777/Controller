"""Only actual old CM wall reroutes, exact contacts/full .20 Cu, no new via."""
import hashlib,json,pickle,sys,itertools,uuid,traceback,math
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import physical_reference_losses_r3_zero_r208 as RF
import audit_aux_exact_raw as A
import tri_route as TR
O=H/'sbc-power/CM-final-two-coupled-actual-old-wall-fullwidth-nominations-r285'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def buf(s,r):n=Z.bounded_buffer(s,r);z=set_precision(n,0);assert z.wkb==n.wkb;return z
def main():
 assert not O.exists();O.mkdir();base=H/'sbc-power/CM-sparse-exact-current-R364-only-new-role-withdrawal-inherited-fills-FAIL-r283';mp=base/'model.pkl';assert sha(mp)=='592ca2e2137c1e38e91eb1c9fe6a8ca29fdc549cbf27b209ea2518ad8e952151';g,h,b,q,c=pickle.loads(mp.read_bytes());proof=H/'sbc-power/CM-R283-current-independent-all-contact-source-native-rule-r284';assert sha(proof/'receipt.json')=='877050f6d37de31e39381d08a08c39f8acf789da412853b3ae65aa607af7fa62';gp=proof/'actual-drilled-current-groups.pkl';assert sha(gp)=='4ab9643d092b7e4b50e46f9fd2fef362389277d97bc41d0059353338c847f555';groups=pickle.loads(gp.read_bytes());lg=K.root(groups['/LOGIC_GND'],'J11001','2');goal=unary_union([r['shape']for r in lg if r['layer']=='F.Cu']);source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';raw=source.read_bytes();iv=A.C.inventory(raw);identity=A.N.SourceNets(raw);peer=H/'coupled-recovery/CM-two-ground-old-wall-source-obligations-r314/receipt.json';assert sha(peer)=='49794db907702d03286d1c93b609556cbb4dcfb269ee72ee5eabda7463894ab6';rec,trees=F.build({**c,'zones':[]},layers={'F.Cu'});dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree([s for u,n,s in holes]);reserve,exempt=A.reservations();outline=unary_union(L.poly(h['outline'])).buffer(-.525);trackby={t['uuid']:t for t in h['tracks']};cases=[('J15001','1','/motherboard_compute/CM_HOST_SPI_CS_CMD_N'),('J15002','79','/fpga_core{slash}FPGA_CDONE')];results=[];won=[];cache={}
 def free(net,clip,removed,extra=(),anchors=()):
  key=(net,tuple(clip.bounds));cachekey=key
  if cachekey not in cache:
   cuts=[]
   for j in trees['F.Cu'].query(clip.buffer(1.5),predicate='intersects'):
    rr=rec['F.Cu'][int(j)]
    if L.norm(rr['net'])==L.norm(net):continue
    req=gap(net,rr['net'])+.025+.000003
    if rr['kind']=='track'and not rr['source'].get('m'):t=rr['source'];cut=buf(LineString([t['a'],t['b']]),t['w']/2+.1+req)
    elif rr['kind']=='via':v=rr['source'];cut=buf(Point(v['x'],v['y']),v['d']/2+.1+req)
    else:cut=buf(rr['shape'],.1+req)
    cuts.append((rr['uuid'],cut))
   for j in ht.query(clip.buffer(1.5),predicate='intersects'):
    uid,n,sh=holes[int(j)]
    if L.norm(n)!=L.norm(net):cuts.append((None,buf(sh,.380003)))
   for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
    for rule in rules:
     if ex and L.norm(net)in exempt.get(rule['name'],set()):continue
     if'F.Cu'in rule['layers']and(ex or rule.get('no_tracks')):
      for s in L.poly(rule['outline']):
       if s.intersects(clip):cuts.append((None,buf(s,.125003)))
   cache[cachekey]=cuts
  cuts=[s for uid,s in cache[cachekey]if uid not in removed]+[buf(sh,.275003)for sh in extra]+[buf(Point(pt),rad+.275003)for pt,rad in anchors];return clip.intersection(outline.buffer(-.100003)).difference(unary_union(cuts))
 for ref,pin,net in cases:
  p=next(p for p in h['pads']if(p['ref'],p['num'])==(ref,pin));ps=Point(p['x'],p['y']);nativewalls=[t for t in h['tracks']if t['layer']=='F.Cu'and t['net']==net and LineString([t['a'],t['b']]).distance(ps)<3.0 and t['uuid']in iv[3]];nativewalls=sorted(nativewalls,key=lambda t:LineString([t['a'],t['b']]).distance(ps))[:8];assert nativewalls;put(O/(ref+'-'+pin+'-exact-native-wall-candidates.json'),nativewalls);attempts=[];winner=None
  for n in range(1,min(4,len(nativewalls))+1):
   for walls in itertools.combinations(nativewalls,n):
    rm={t['uuid']for t in walls};anchors=[(pt,max(t['w'],.2)/2)for t in walls for pt in(t['a'],t['b'])];candidate={'removed_exact_old_wall_UUIDs':sorted(rm),'coupled_actual_old_wall_widths_mm':[t['w']for t in walls],'routes':[]};attempts.append(candidate)
    if any(t['w']!=.2 for t in walls):candidate['failure']='Not exact full .20 old wall; no invented neck or width exception';continue
    for radius in(2.,4.,8.):
     clip=box(ps.x-radius,ps.y-radius,ps.x+radius,ps.y+radius);gf=free('/LOGIC_GND',clip,rm,anchors=anchors);localgoal=goal.intersection(clip).buffer(-.00001)
     for dy in(-.3,.3,-.4,.4):
      start=[p['x'],round(p['y']+dy,6)];sp=Point(start);faces=[f for f in RF.parts(gf)if f.covers(sp)]
      for face in faces:
       target=face.buffer(-.000005).intersection(localgoal)
       if target.is_empty:continue
       ep=nearest_points(sp,target)[1];end=[round(ep.x,6),round(ep.y,6)]
       if not target.covers(Point(end)):continue
       path,method=TR.route(face,start,end);path=[[round(x,6),round(y,6)]for x,y in path]
       if not face.covers(LineString(path)):continue
       gnt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM-R285:'+p['uuid']+':'+','.join(sorted(rm))+':GND:'+str(i))),'net':'/LOGIC_GND','layer':'F.Cu','w':.2,'a':a,'b':bb}for i,(a,bb)in enumerate(zip(path,path[1:]))];newgbody=unary_union([buf(LineString([t['a'],t['b']]),.1)for t in gnt]);extras=[newgbody];sf=free(net,clip,rm,extra=extras);replacements=[];errors=[]
       for old in walls:
        aa=Point(old['a']);bb=Point(old['b']);ff=[f for f in RF.parts(sf)if f.covers(aa)and f.covers(bb)]
        if not ff:errors.append({'old_UUID':old['uuid'],'failure':'No full .20 paired wall route preserving both actual old endpoints'});break
        rp,rmeth=TR.route(ff[0],old['a'],old['b']);rp=[[round(x,6),round(y,6)]for x,y in rp]
        if not ff[0].covers(LineString(rp)):errors.append({'old_UUID':old['uuid'],'failure':'Rounded wall route leaves exact free polygon'});break
        replacements.extend({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM-R285:'+old['uuid']+':'+','.join(sorted(rm))+':wall:'+str(i))),'net':old['net'],'layer':'F.Cu','w':.2,'a':a,'b':bb}for i,(a,bb)in enumerate(zip(rp,rp[1:])));candidate['routes'].append({'old_UUID':old['uuid'],'path':rp,'method':rmeth})
       if errors:candidate['paired_route_errors']=errors;continue
       beforeuf,oldgroups=K.physical(c,L.norm(net),K.hole_context(c));trial={**c,'tracks':[t for t in c['tracks']if t['uuid']not in rm]+gnt+replacements};_,newgroups=K.physical(trial,L.norm(net),K.hole_context(trial));cr,loss=K.contact_losses(oldgroups,newgroups,rm)
       if loss:candidate['actual_retained_old_signal_contact_losses']=loss;continue
       nativechunks=[]
       for old in walls:
        ch=iv[3][old['uuid']];parsed=A.G.parse(old['uuid'],ch,{});assert(parsed['net'],parsed['layer'],parsed['w'],parsed['a'],parsed['b'])==(L.norm(old['net']),old['layer'],old['w'],old['a'],old['b']);file=O/(old['uuid']+'.exact-source-wall-delete-chunk');file.write_bytes(ch);nativechunks.append({'UUID':old['uuid'],'raw_net':identity.raw(L.norm(old['net'])),'exact_old_chunk_file':str(file.resolve()),'exact_old_chunk_sha256':sha(file)})
       contact=buf(Point(start),.1).intersection(unary_union(L.poly(p['layers']['F.Cu']))).area;assert contact>0;winner={'ref':ref,'pin':pin,'actual_pad_UUID':p['uuid'],'actual_start_native_pad_contact_mm2':contact,'removed_original_track_UUIDs':sorted(rm),'exact_original_wall_delete_authority':nativechunks,'tracks':gnt+replacements,'vias':[],'new_ground_track_count':len(gnt),'new_paired_fullwidth_wall_track_count':len(replacements),'all_retained_old_signal_physical_layer_contacts_loss_count':len(loss),'actual_source_F_Cu_end_positive_contact':True,'ground_path':path,'ground_method':method,'coupled_native_discrete_fullwidth_margin_only':'NOMINATION_PENDING_ALL_CURRENT_FILLED_SOURCE_REFERENCE_NATIVE_PROOF','field_successor_minimal_rebind_required':True};won.append(winner);break
      if winner:break
     if winner:break
    if winner:break
   if winner:break
  results.append({'ref':ref,'pin':pin,'exact_raw_signal_wall_net':net,'winner':winner,'actual_old_wall_restore_matrix':attempts});put(O/'finite-coupled-source-wall-matrix.json',results);print('R285_CASE',ref,pin,len(attempts),winner is not None,flush=True)
 tracks=[t for w in won for t in w['tracks']];removed=[u for w in won for u in w['removed_original_track_UUIDs']];(O/'only-coupled-new-discrete-and-exact-old-wall-deletes.pkl').write_bytes(pickle.dumps({'tracks':tracks,'vias':[],'removed_original_track_UUIDs':removed},protocol=5));put(O/'receipt.json',{'verdict':'COUPLED_ACTUAL_OLD_WALL_FULLWIDTH_NOMINATION_PENDING_CURRENT_FIELD_REBASE_AND_ALL_GATES'if len(won)==2 else'PARTIAL_FINITE_COUPLED_OLD_WALL_DIAGNOSTIC_NO_CM51_CURRENT_CREDIT','exact_diagnostic_model_sha256':sha(mp),'exact_actual_source_groups_sha256':sha(gp),'independent_exact_wall_source_contact_authority_sha256':sha(peer),'case_count':2,'nominated_case_count':len(won),'new_track_count':len(tracks),'exact_old_wall_delete_count':len(removed),'new_vias':0,'all_actual_old_source_via_definitions_annuli_pads_rules_untouched':True,'ordinary_new_and_old_wall_width_mm':.2,'new_same_domain_clearance_plus_planner_mm':.175,'foreign_domain_plus_planner_mm':.625,'all_electrical_source_reference_current_native_fault_and_two_case_mutual_geometry':'OPEN','inherited_failed_field28_CORE93_CM85_outsideq_current':'FAIL_OR_OPEN_RETAINED','full_current_mesh_not_run':True,'board_written':False,'native_jobs':0,'adopted':False,'script_sha256':sha(__file__)});print('R285_COMPLETE',len(won),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
