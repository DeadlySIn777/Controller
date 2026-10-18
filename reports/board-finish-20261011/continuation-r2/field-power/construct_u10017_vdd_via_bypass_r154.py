"""Coupled U10017 VDD crossing with a stronger ordinary protected source feed."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_u10017_coupled_vs_wall_r134.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u10017-coupled-vdd-vs-wall-nominee-r134'", "O=H/'u10017-coupled-vdd-strong-source-bypass-base-r154'")
cut=s.index(" a,bb=nearest_points(target['shape'],goal);trials=[];answer=None")
s=s[:cut]+''' a,bb=nearest_points(target['shape'],goal);join=None
 for margin in (3.,8.,18.):
  win=box(min(a.x,bb.x)-margin,min(a.y,bb.y)-margin,max(a.x,bb.x)+margin,max(a.y,bb.y)+margin);join=route(legal(target['net'],win),target['shape'],goal,.2)
  if join:break
 assert join is not None
 points,line,body,search=join;adds=[]
 for j,(pa,pb) in enumerate(zip(points,points[1:])):
  if pa==pb:continue
  adds.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-u10017-vdd-via-bypass-r154/VDD/{j}')),'net':target['net'],'layer':'F.Cu','a':pa,'b':pb,'w':.2,'locked':False,'prospective_not_native':True})
 current=H/'paired-regional-six-regulated-full-contact-audit-r142/REG_R130-regional-model.pkl';g,h,b,z,after=pickle.loads(current.read_bytes());h=copy.deepcopy(h);h['tracks']=[q for q in h['tracks'] if q['uuid']!=old['uuid']]+adds;after=copy.deepcopy(after);after['tracks']=h['tracks'];after['vias']=h['vias'];after['pads']=h['pads'];b=copy.deepcopy(b);b['field_regulated_search_hard_nominees']={'planes':[],'discrete':{'tracks':[],'vias':[]},'source_qualified_peer_ROOT_spine_UUIDs_hard':[q['uuid'] for q in z if q['uuid'].startswith(('f0ef','7b19','d03e','f0b2','5ac5','130e','ffcc','d5e','d62f','d480'))]}
 peer=H.parent/'sbc-power/CORE1V2-source-native-outline-correction-r135/new-feed-zones.pkl';b['field_regulated_search_hard_nominees']['planes']+=pickle.loads(peer.read_bytes());(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'VDD-tracks.pkl').write_bytes(pickle.dumps(adds,protocol=5));(O/'old-owned-wall.pkl').write_bytes(pickle.dumps(old,protocol=5));write(O/'receipt.json',{'model_sha256':sha(O/'model.pkl'),'scope':'CONSTRUCTION_ONLY_VDD_SOURCE_ROUTE_PLUS_UNRESTORED_PROTECTED_WALL_REMOVAL','old_wall_uuid':old['uuid'],'old_wall_original_record_sha256':sha(O/'old-owned-wall.pkl'),'VDD_tracks_sha256':sha(O/'VDD-tracks.pkl'),'VDD_length_mm':line.length,'current_parent_model_sha256':sha(current),'all_original_other_Cu_and_output_limits_preserved':True})
 print('R154 bypass search base',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
'''
s=s.replace('.read_text()', ".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_u10017_coupled_vs_wall_r134.py'),'exec'))
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'", "OUT=HERE/'u10017-protected-source-via-bypass-nominee-r154';BASE=HERE/'u10017-coupled-vdd-strong-source-bypass-base-r154'")
s=s.replace("INNER=['In1.Cu','In4.Cu','In3.Cu','In2.Cu']", "INNER=['In2.Cu','In1.Cu','In3.Cu','In4.Cu']")
s=s.replace("for bank,net,ref,pin,policy in PORTS:", "for bank,net,ref,pin,policy in [('FBVS','/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17',2.003)]:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'", "xs=gs[gi];\n   if not any(q['kind']=='pad' and q.get('ref')=='U10017' for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'", "and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93' and q['uuid'] not in hard.get('source_qualified_peer_ROOT_spine_UUIDs_hard',[])")
s=s.replace("for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):", "for margin in(8.,25.,60.):\n    for width in(1.,.75):")
s=s.replace('for d0,h0 in((.6,.3),(.5,.2)):', 'for d0,h0 in((.8,.4),(.6,.3)):')
s=s.replace('for width in(.25,.2):', 'for width in(.3,.25):')
s=s.replace('controller-regulated-r76/', 'controller-u10017-protected-bypass-r154/')
s=s.replace("native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)", "construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)")
s=s.replace('.read_text()', ".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
