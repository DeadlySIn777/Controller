"""No-hole IO3 bridge; only literal native foreign fills may retreat normally.

All original outlines, discrete Cu/annuli, and generated owned peers remain
hard. Exact per-record negative operations and fresh source/contact/reference
checks accompany any sparse nomination; no whole model is emitted.
"""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_FIELD5_IO3_local_reference_existing_source_bridge_r295.py').read_text()
# Expand the already frozen R295 wrapper before adding a separately frozen
# native-fill scope; the original failed fixed-fill recipe remains untouched.
ns={'__file__':str(P/'nominate_FIELD5_IO3_local_reference_existing_source_bridge_r295.py')}
base=(P/'nominate_FIELD5_IO3_no_hole_existing_source_bridge_r293.py').read_text()
base=base.replace('FIELD5-R393-IO3-no-hole-actual-source-strict-reference-bridge-r293','FIELD5-R393-IO3-no-hole-normal-native-fill-source-bridge-r296')
base=base.replace("rawfree=free(layer,width,clip);f=rawfree.intersection(refs[layer].buffer(-width/2-.000004,quad_segs=128));faces=[]", "print('R296_ATTEMPT',radius,width,layer,flush=True);rawfree=free(layer,width,clip);localref=refs[layer].intersection(clip.buffer(1));f=rawfree.intersection(localref.buffer(-width/2-.000004,quad_segs=128));faces=[]")
base=base.replace('import tri_route as TR','import tri_route as TR\nimport immutable_local_fill_subtraction_r254 as IM\nimport copy')
base=base.replace(';del allgroups','')
base=base.replace("rec,trees=F.build(hard);", "source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';nativeids=set(A.C.inventory(source.read_bytes())[3]);rec,trees=F.build(hard);")
base=base.replace("if L.norm(rr['net'])==NET:continue", "if L.norm(rr['net'])==NET:continue\n   if rr['kind']=='fill'and rr['uuid']in nativeids:continue",1)
needle=' attempts=[];winner=None'
replacement=''' def project_native(nt,key):
  zones=[];ledger=[];affected={NET}
  for oldz in c['zones']:
   z={**oldz,'fills':{}};native=oldz['uuid']in nativeids
   for ly,rr in oldz['fills'].items():
    cuts=[];cutrows=[]
    if native and L.norm(oldz['net'])!=NET:
     for t in nt:
      if t['layer']!=ly:continue
      radius=t['w']/2+max(float(oldz['clearance_mm']),gap(NET,oldz['net']))+.025
      cut=buf(LineString([t['a'],t['b']]),radius)
      if any(cut.intersects(p)for p in L.poly(rr)):
       cuts.append(cut);cutrows.append({'new_UUID':t['uuid'],'normal_only_native_foreign_fill_cutter_radius_mm':radius,'cutter_WKB_sha256':digest(cut)});(O/(key+'-'+oldz['uuid']+'-'+ly+'-'+t['uuid']+'-normal-cutter.wkb')).write_bytes(cut.wkb)
    if cuts:
     newrs,lr=IM.subtract(rr,cuts,O,key+'-'+oldz['uuid']+'-'+ly);z['fills'][ly]=newrs;affected.add(L.norm(oldz['net']));ledger.append({'native_UUID':oldz['uuid'],'raw_net':oldz['net'],'layer':ly,'original_definition_settings_retained':True,'exact_array_before_sha256':hashlib.sha256(pickle.dumps(rr,protocol=5)).hexdigest(),'exact_array_after_sha256':hashlib.sha256(pickle.dumps(newrs,protocol=5)).hexdigest(),'cuts':cutrows,**lr})
    else:z['fills'][ly]=copy.deepcopy(rr)
   zones.append(z)
  trial={**c,'tracks':c['tracks']+nt,'zones':zones}
  return trial,ledger,affected
 attempts=[];winner=None'''
assert base.count(needle)==1;base=base.replace(needle,replacement)
base=base.replace("trial={**c,'tracks':c['tracks']+nt};_,new=K.physical(trial,NET,K.hole_context(trial));rows,loss=K.contact_losses(groups,new);", "trial,fillledger,affected=project_native(nt,str(len(attempts)));newgroups={};contactbad=[];directbad=[];sourcebad=[];ctx=K.hole_context(trial)\n     for nn in sorted(affected):\n      oldgroups=groups if nn==NET else allgroups[nn];_,ng=K.physical(trial,nn,ctx);newgroups[nn]=ng;cr,cl=K.contact_losses(oldgroups,ng);contactbad.extend({'net':nn,**x}for x in cl)\n      # Retain every old direct actual filled-to-discrete contact, not merely a group shortcut.\n      cutkeys={(x['native_UUID'],x['layer'])for x in fillledger if L.norm(x['raw_net'])==nn};nfill={}\n      for xs in ng:\n       for r0 in xs:\n        if r0['kind']=='fill':nfill.setdefault((r0['uuid'],r0['layer']),[]).append(r0['shape'])\n      for ly in K.LAYERS:\n       metal=[r0 for xs in oldgroups for r0 in xs if r0['layer']==ly and r0['kind']!='fill'];mt=STRtree([r0['shape']for r0 in metal])\n       for f0 in(r0 for xs in oldgroups for r0 in xs if r0['kind']=='fill'and r0['layer']==ly and(r0['uuid'],ly)in cutkeys):\n        for j in mt.query(f0['shape'].buffer(.000002),predicate='intersects'):\n         m0=metal[int(j)]\n         if f0['shape'].distance(m0['shape'])<=.000002 and not any(ss.distance(m0['shape'])<=.000002 for ss in nfill.get((f0['uuid'],ly),[])):directbad.append({'net':nn,'native_fill_UUID':f0['uuid'],'layer':ly,'old_direct_contact':[m0['kind'],m0['uuid']]})\n      for rn,rf,rp in K.ROOTS:\n       if rn!=nn:continue\n       oldroot=K.root(oldgroups,rf,rp);newroot=K.root(ng,rf,rp);sk=sorted(K.keys(oldroot)-K.keys(newroot));sourcebad.extend({'net':nn,'source':rf+'.'+rp,'missing_key':list(k)}for k in sk)\n     new=newgroups[NET];rows,loss=K.contact_losses(groups,new);")
base=base.replace("if loss or lost:continue", "row['native_fill_retreat_old_contacts_lost']=len(contactbad);row['native_fill_retreat_old_direct_contacts_lost']=len(directbad);row['native_fill_retreat_prior_root_keys_lost']=len(sourcebad)\n     if loss or lost or contactbad or directbad or sourcebad:continue\n     refbad=[]\n     for nn,rf,rp in(('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2')):\n      oldroot=K.root(allgroups[nn],rf,rp);ng=newgroups.get(nn,allgroups[nn]);newroot=K.root(ng,rf,rp);errors0,proof0=RF.audit(c,K.source_refs(oldroot),K.source_refs(newroot),nn);refbad.extend({'bank':nn,**v}for v in errors0)\n     row['strict_three_bank_old_reference_losses']=len(refbad)\n     if refbad:continue")
# Actual geometric checks use freshly projected native fills. Owned peers and
# every original discrete/annulus remain the same hard objects.
base=base.replace('checks=[];errors=[]', 'freshrec,freshtrees=F.build(trial,layers={layer});checks=[];errors=[]')
base=base.replace("for j in trees[layer].query(bod.buffer(.8),predicate='intersects'):\n       rr=rec[layer][int(j)]", "for j in freshtrees[layer].query(bod.buffer(.8),predicate='intersects'):\n       rr=freshrec[layer][int(j)]")
base=base.replace("if L.norm(rr['net'])==NET:continue\n       req=", "if L.norm(rr['net'])==NET:continue\n       req=")
base=base.replace("'all_foreign_current_fill_Cu_preserved':True", "'only_original_native_foreign_fills_retreated':True,'exact_native_fill_negative_ledger':fillledger,'affected_current_nets':sorted(affected),'strict_three_bank_old_reference_losses':0,'all_native_fill_direct_old_contact_losses':0,'all_prior_affected_source_key_losses':0")
base=base.replace("'every_other_current_native_owned_body_fill_hole_exact':True", "'every_other_original_body_hole_native_definition_and_owned_generated_peer_exact':True")
base=base.replace("'new_generated_or_native_fill_role_operations':0", "'new_generated_role_operations':0,'native_fill_negative_scopes':len(winner['exact_native_fill_negative_ledger'])if winner else 0")
base=base.replace("'NO_NO_HOLE_STRICT_CURRENT_REFERENCE_IO3_BRIDGE_IN_DECLARED_WINDOWS'", "'NO_NORMAL_NATIVE_FILL_NO_HOLE_STRICT_REFERENCE_IO3_BRIDGE_IN_DECLARED_WINDOWS'")
base=base.replace('R293','R296')
exec(compile(base,str(__file__),'exec'))
