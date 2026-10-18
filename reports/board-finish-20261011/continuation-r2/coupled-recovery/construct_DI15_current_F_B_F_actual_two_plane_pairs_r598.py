"""A different three-leg DI15 transport using actual shared J1 source planes.

Uses cached physical legality, exact bare endpoints and continuous site
regions. No old copper or power reference is withdrawn by this constructor.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,math
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_ao1_positive_operation_r4 as SERIAL
import construct_DI15_current_ordinary_F_In2_F_pairs_r592 as R
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI15-current-F-B-F-actual-two-plane-ordinary-pairs-r598';NET=R.NET;LG=R.LG
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,v=None):
  p=Path(p);s=sha(p);assert v is None or s==v;pins[str(p.resolve())]=s;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes())
 ca=pickle.loads(pin(H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592/bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl').read_bytes())
 banks=pickle.loads(pin(H/'DI6-current-independent-all-contacts-source-reference-r580/actual-before-and-after-ten-source-bank-primitives.pkl').read_bytes());old=banks['after'][LG]
 cp=pin(H/'DI15-actual-R157-current-native-port-return-census-r590/exact-current-DI15-physical-groups-and-actual_NATIVE-J1-reference-primitives-NOMINATION_ONLY.pkl','85ec65a59757706be27b5a329d27f4c4a56f9dc337b77d55c2130dc58f320f93');census=pickle.loads(cp.read_bytes())
 refs={ly:unary_union([r['shape']for r in old if r['kind']=='fill'and r['layer']==ly]).intersection(census['native_refs'][ly])for ly in('In1.Cu','In4.Cu')}
 win=box(115,86,136,118);bf=ca['free'][NET,'B.Cu'].intersection(refs['In4.Cu'].intersection(win.buffer(1)).buffer(-.105));ff=ca['ff'];returns=ca['via'][LG].intersection(refs['In1.Cu']).intersection(refs['In4.Cu']);options={};start=[119.136,89.0495];end=[132.115,114.375]
 for role,region,desired in(('source',ca['sourceSites'],[119.835668,88.351965]),('target',ca['targetSites'],[131.25,112.35])):
  opts=[]
  for at in R.sites(region.intersection(bf),desired,60):
   ring=Point(at).buffer(.999,quad_segs=128).difference(Point(at).buffer(.901,quad_segs=128));rs=R.sites(returns.intersection(ring),[at[0]+.925,at[1]],8);rs=[x for x in rs if .9<=math.dist(x,at)<=1]
   if rs:opts.append({'signal':at,'returns':rs})
  options[role]=opts
 put(OUT/'continuous-actual-source-two-plane-pair-options.json',options);attempts=[];selected=None
 for a in options['source'][:15]:
  for z in options['target'][:15]:
   for ar in a['returns'][:3]:
    for zr in z['returns'][:3]:
     cut=unary_union([K.Z.bounded_buffer(Point(x),.630)for x in(ar,zr)]);paths=[];row={'source_signal':a['signal'],'source_return':ar,'target_signal':z['signal'],'target_return':zr,'paths':paths};attempts.append(row)
     for ly,p1,p2,free in(('F.Cu',start,a['signal'],ff),('B.Cu',a['signal'],z['signal'],bf),('F.Cu',z['signal'],end,ff)):
      parts=[s for s in R.pieces(free.difference(cut))if s.covers(Point(p1))and s.covers(Point(p2))]
      if not parts:break
      pts,search=T.route(parts[0],tuple(p1),tuple(p2));pts=[[round(x,6),round(y,6)]for x,y in pts]
      if len(pts)<2 or not parts[0].covers(LineString(pts)):break
      paths.append({'layer':ly,'points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length,'search':search})
     if len(paths)==3:selected=row;break
    if selected:break
   if selected:break
  if selected:break
 original=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');identity=K.A.N.SourceNets(original.read_bytes());inv=K.C.inventory(original.read_bytes())[3];nt=[];nv=[];chunks={}
 if selected:
  for path in selected['paths']:
   for a,z in zip(path['points_mm'],path['points_mm'][1:]):
    uid,ch=identity.serial_segment(NET,path['layer'],a,z,.2);nt.append({'uuid':uid,'net':identity.raw(NET),'layer':path['layer'],'w':.2,'a':a,'b':z});chunks[uid]=ch
  for net,at in((NET,selected['source_signal']),(NET,selected['target_signal']),(LG,selected['source_return']),(LG,selected['target_return'])):
   uid,ch=SERIAL.serial_via(identity,net,at);chunks[uid]=ch;nv.append({'uuid':uid,'net':identity.raw(net),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
  identity.assert_chunks(chunks);assert set(chunks).isdisjoint(inv)
 put(OUT/'finite-three-leg-paired-path-attempts.json',attempts);packet=OUT/'only-NEW-DI15-F-B-F-sparse-nomination.pkl';packet.write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'exact_new_chunks':chunks,'original_deletes':{},'selected':selected,'actual_before_refs':refs,'used_layer_legs':['F.Cu','B.Cu','F.Cu']},protocol=5));put(OUT/'receipt.json',{'verdict':'DI15_F_B_F_CURRENT_PAIRED_POSITIVE_INDEPENDENT_OPEN'if selected else'DI15_F_B_F_CURRENT_PAIRED_TRANSPORT_BOUNDED_INCOMPLETE','selected':selected,'source_options':len(options['source']),'target_options':len(options['target']),'B_source_plane_components':len(R.pieces(bf)),'pair_window_mm':[.9,1.0],'input_SHA256':pins,'sparse_nomination_file':str(packet.resolve()),'sparse_nomination_SHA256':sha(packet),'all_original_and_current_power_Cu_held':True,'complete_all_drill_source_full_body_native_oldcontact_zero_oldref_current_SI':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R598_COMPLETE',sha(OUT/'receipt.json'),'options',len(options['source']),len(options['target']),'selected',bool(selected),flush=True)
if __name__=='__main__':main()
