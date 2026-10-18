from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
src=P/'construct_IO3_safe_existing_via_reroute_r162.py';s=src.read_text()
s=s.replace('IO3-safe-existing-via-reroute-r162','IO3-bounded-owned-CORE-notch-reroute-r164').replace('controller/IO3-SAFE-owned-replacement-r162/','controller/IO3-SAFE-owned-replacement-r164/').replace('IO3_SAFE_R162_FROZEN','IO3_SAFE_R164_FROZEN')
s=s.replace(" refs={};refrows=[];oldfills=", " original_track_ids={t['uuid'] for t in g['tracks']}\n refs={};refrows=[];oldfills=")
s=s.replace("if r['kind']!='track' or r['net']=='/LOGIC_GND'", "if r['kind']!='track' or r['uuid'] not in original_track_ids or r['net']=='/LOGIC_GND'")
s=s.replace(" for radius in (5.,15.,35.,75.,125.):", " notch_scope=set_precision(box(v['x']-10,v['y']-10,v['x']+10,v['y']+10),1e-6);notch_uid='prospective-CORE-main-In2';core_raw='/mc_local_power{slash}CORE_5V'\n core_key_file=H/'sbc-power/frozen-regional-source-exit-replay-r129/CORE-source-scope-checkpoint.json';core_keys=set(json.loads(core_key_file.read_bytes())['prior_exact_CORE_keys']);assert len(core_keys)==8303\n for radius in (5.,15.,35.,75.):")
needle="    if q['layer']==layer and q['net']!=RAW and query.intersects(q['shape']):obs.append(GP.bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020))"
repl="""    if q['layer']==layer and q['net']!=RAW and query.intersects(q['shape']):
     obstruction=q['shape'].difference(notch_scope) if q['uuid']==notch_uid and layer=='In2.Cu' else q['shape']
     obs.append(GP.bounded_buffer(obstruction.intersection(query),max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025+.000020))"""
assert needle in s;s=s.replace(needle,repl)
s=s.replace("GP.bounded_buffer(s,max(.6,float(q['clearance_mm']))+.025+.000020)","GP.bounded_buffer(s.intersection(query),max(.6,float(q['clearance_mm']))+.025+.000020)")
s=s.replace("   free=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6)","   free=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6);print('IO3_SAFE_FREE_PORT',layer,radius,'annulus_mm2',free.intersection(ann).area,'source_mm2',free.intersection(source[layer]).area,flush=True)")
needle="     hs={**h,'zones':[q for q in h['zones'] if q['net']==RAW]};trial,cuts=GP.projected(g,hs,remain+[nq]);Q.NET=RAW;"
repl="""     trial_zones=list(remain);carve=None
     if layer=='In2.Cu':
      coreq=next(q for q in trial_zones if q['uuid']==notch_uid);cut=GP.bounded_buffer(nq['shape'],.175+.000020);before=coreq['shape'];outline_before=coreq.get('zone_outline_shape',before)
      ca=set_precision(set_precision(before,1e-6).difference(cut),1e-6);coa=set_precision(set_precision(outline_before,1e-6).difference(cut),1e-6)
      removed=before.difference(ca);assert notch_scope.buffer(.000050).covers(removed),'CORE change leaves authorized bounded notch scope'
      trial_zones=[({**q,'shape':ca,'zone_outline_shape':coa} if q['uuid']==notch_uid else q) for q in trial_zones]
      carve={'owned_NEW_CORE_UUID':notch_uid,'raw_net':core_raw,'layer':'In2.Cu','scope_bounds_mm':notch_scope.bounds,'scope_WKB_SHA256':digest(notch_scope),'physical_before_WKB_SHA256':digest(before),'physical_after_WKB_SHA256':digest(ca),'outline_before_WKB_SHA256':digest(outline_before),'outline_after_WKB_SHA256':digest(coa),'physical_removed_mm2':removed.area,'physical_quantization_added_mm2':ca.difference(before).area,'outline_removed_mm2':outline_before.difference(coa).area,'outline_quantization_added_mm2':coa.difference(outline_before).area,'cut_WKB_SHA256':digest(cut),'full_CORE_current_A':7.882034293398381,'minimum_CORE_neck_sheet_barrel_current_thermal_drop_remain_unqualified':True,'no_original_native_zone_outline_change':True}
     hs={**h,'zones':[q for q in h['zones'] if q['net']==RAW]};trial,cuts=GP.projected(g,hs,trial_zones+[nq]);Q.NET=RAW;"""
assert needle in s;s=s.replace(needle,repl)
needle="     answer=row;chosen=nq;print('IO3_SAFE_SOURCE_ACCEPT',layer,line.length,width,len(joined),flush=True);break"
repl="""     core_selected={**h,'zones':[q for q in h['zones'] if q['net']==core_raw]};core_trial,_=GP.projected(g,core_selected,trial_zones+[nq]);Q.NET=C.norm(core_raw);cgs,cparts,cassignment=Q.groups(core_trial,return_details=True);cri=next(i for i,xs in enumerate(cgs) if any((r['ref'],r['pad'])==('R11022','2') for r in xs));ckeys={r['uuid'] for r in cgs[cri]};lost_core=sorted(core_keys-ckeys);floating=[]
     for cq in trial_zones:
      if cq['net']!=core_raw:continue
      for piece in polys(cq['shape']):
       hits={a for cp,a in zip(cparts[cq['layer']],cassignment[cq['layer']]) if cp.intersection(piece).area>0}
       if hits!={cri}:floating.append({'UUID':cq['uuid'],'piece_mm2':piece.area,'groups':sorted(map(str,hits))})
     row['lost_CORE_source_keys']=lost_core;row['detached_retained_CORE_components']=floating;row['bounded_owned_CORE_notch']=carve;write(O/'attempts.json',attempts)
     if lost_core or floating:continue
     if carve:
      for name,shape in [('CORE-before',before),('CORE-after',ca),('CORE-outline-before',outline_before),('CORE-outline-after',coa),('CORE-cut',cut),('CORE-notch-scope',notch_scope)]:
       (O/(name+'.wkb')).write_bytes(shape.wkb)
      write(O/'CORE-owned-notch-ledger.json',carve)
     remain=trial_zones;answer=row;chosen=nq;print('IO3_SAFE_SOURCE_ACCEPT',layer,line.length,width,len(joined),'CORE',len(ckeys),flush=True);break"""
assert needle in s;s=s.replace(needle,repl)
s=s.replace("'lost_prior_source_keys':missing", "'lost_prior_source_keys':missing,'CORE_original_source_key_file':str(core_key_file),'CORE_original_source_key_file_sha256':sha(core_key_file)")
out=P/'construct_IO3_bounded_CORE_notch_reroute_r164.py';assert not out.exists();out.write_text(s)
receipt={'verdict':'R162_DELIBERATELY_STOPPED_WITH_NO_ATTEMPTED_OR_ACCEPTED_GEOMETRY_BOUNDED_OWNED_CORE_SUCCESSOR','stopped_exact_PID':70252,'script_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'attempts_file_absent':not(P/'IO3-safe-existing-via-reroute-r162/attempts.json').exists(),'successor_script_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'owned_new_CORE_notch_source_contacts_components_current_gates':True,'native_jobs':0,'board_written':False}
(P/'IO3-safe-existing-via-reroute-r162/deliberate-stop-receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(receipt)
