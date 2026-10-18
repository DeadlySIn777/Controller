from pathlib import Path
H=Path(__file__).resolve().parent;dst=H/'nominate_Q0_R10016_true_source_pose_r334.py';assert not dst.exists();s=(H/'nominate_Q0_R10016_source_pose_r332.py').read_text().replace('nomination-r332','nomination-r334')
needle="groundF=unary_union([r['shape']for r in root if r['layer']=='F.Cu']);"
replacement="""retained=[r for r in root if r['uuid']not in padids];sourceUF=K.A.S.UF()
for r in retained:sourceUF.find(r['key'])
for layer in K.LAYERS:
 layerrows=[r for r in retained if r['layer']==layer];tree=STRtree([r['shape']for r in layerrows])
 for i,r in enumerate(layerrows):
  for j in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
   j=int(j)
   if i<j and r['shape'].distance(layerrows[j]['shape'])<=.000002:sourceUF.join(r['key'],layerrows[j]['key'])
rootkey=next(r['key']for r in retained if r['kind']=='pad'and(r['ref'],str(r['pin']))==('J11003','2'));trueRoot=[r for r in retained if sourceUF.find(r['key'])==sourceUF.find(rootkey)]
withdrawal_missing=K.keys(retained)-K.keys(trueRoot);assert not withdrawal_missing,('Old ground pad withdrawal disconnects prior source objects',withdrawal_missing)
groundF=unary_union([r['shape']for r in trueRoot if r['layer']=='F.Cu']);"""
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace('def obstacles(net,newsh):','def obstacles(net,newsh,peer_tracks=()):')
needle="obs=[]\n for j in trees['F.Cu']"
replacement="obs=[]\n for t in peer_tracks:\n  if K.L.norm(t['net'])!=net:obs.append(K.A.shape({'kind':'segment',**t}).buffer(req(net,t['net'])+.030,quad_segs=128))\n for j in trees['F.Cu']"
assert s.count(needle)==1;s=s.replace(needle,replacement)
needle="if bad or not all(r['new_F_pad_actual_source_reference_gap_empty']for r in contact)or contact[1]['new_F_ground_pad_actual_rooted_F_Cu_overlap_mm2']<=.004:continue\n free=obstacles(NET,newsh);"
replacement="""if bad:continue
 groundtracks=[];groundchunks={};ground_body=unary_union([]);ground_witness={'direct_existing_root_overlap_mm2':newsh['2'].intersection(groundF).area,'exact_old_R10016_pad_absent_from_source_graph':True}
 if ground_witness['direct_existing_root_overlap_mm2']<=.004:
  groundfree=obstacles(GND,newsh);ga=[newsh['2'].buffer(-.04,quad_segs=128).intersection(groundfree),groundF.buffer(-.02,quad_segs=128).intersection(groundfree)];row['ground_attachment_areas_mm2']=[x.area for x in ga]
  for part in parts(groundfree):
   aa=[x.intersection(part)for x in ga]
   if any(x.is_empty for x in aa):continue
   p0,p1=nearest_points(*aa);ends=[[round(p.x,6),round(p.y,6)]for p in(p0,p1)]
   if not all(part.covers(Point(p))for p in ends):continue
   path0,search0=T.route(part,tuple(ends[0]),tuple(ends[1]));path0=[[round(x,6),round(y,6)]for x,y in path0]
   if len(path0)<2:continue
   gb=unary_union([K.A.shape({'kind':'segment','a':a,'b':bb,'w':.2})for a,bb in zip(path0,path0[1:])])
   if not gb.difference(ref).is_empty or min(gb.intersection(newsh['2']).area,gb.intersection(groundF).area)<=.004:continue
   for a,bb in zip(path0,path0[1:]):
    uid,ch=identity.serial_segment(GND,'F.Cu',a,bb,.2);assert uid not in iv[3];groundchunks[uid]=ch;groundtracks.append({'uuid':uid,'net':identity.raw(GND),'a':a,'b':bb,'w':.2,'layer':'F.Cu'})
   ground_body=gb;ground_witness.update(new_F_ground_path_mm=path0,strict_ground_route_actual_In1_source_gap_empty=True,ground_new_pad_and_real_retained_root_overlaps_mm2=[gb.intersection(newsh['2']).area,gb.intersection(groundF).area],search=search0);break
  if not groundtracks:continue
 free=obstacles(NET,newsh,groundtracks);"""
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace("'new_tracks':tracks,'exact_add_chunks':{u:c.decode()for u,c in chunks.items()}","'new_tracks':groundtracks+tracks,'exact_add_chunks':{u:c.decode()for u,c in {**groundchunks,**chunks}.items()},'actual_withdrawn_old_pad_source_ground_witness':ground_witness,'new_pad_whole_body_reference_rows_preserved_OPEN_not_waived':contact")
s=s.replace("'actual_ground_pin_root_contact_mm2':newsh['2'].intersection(groundF).area","'actual_ground_pin_root_contact_mm2':newsh['2'].intersection(groundF.union(ground_body)).area")
s=s.replace("for uid,ch in chunks.items():(out/(uid+'.segment-chunk')).write_bytes(ch)","for uid,ch in {**groundchunks,**chunks}.items():(out/(uid+'.segment-chunk')).write_bytes(ch)")
s=s.replace("'every_current_protected_power_role_hard':True","'every_current_protected_power_role_hard':True,'actual_old_ground_pad_removed_before_source_witness':True,'all_prior_ground_source_keys_retained_after_old_pad_withdrawal':True,'source_union_excludes_own_phantom_old_pad_geometry':True,'new_SMD_whole_pad_reference_DC_loop_and_SI_qualification':'OPEN; raw exact gaps preserved; every new routed full body strictly reference covered'")
dst.write_text(s,encoding='utf-8',newline='\n')
