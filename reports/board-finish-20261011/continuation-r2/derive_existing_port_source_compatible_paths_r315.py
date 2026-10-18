"""Route only within actual BEFORE LG source plus two owned old terminals."""
import json,hashlib,runpy,time
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
batch=H/'six-existing-old-port-In3-physical-batch-r313/receipt.json';assert sha(batch)=='ec835ba5aa774b735cb559fd899ca3fb1fadfc414e72c0f70d3313612a9b3347';br=json.loads(batch.read_bytes())
OUT=H/'three-existing-old-port-In3-BEFORE-source-compatible-paths-r315';assert not OUT.exists();OUT.mkdir();results=[];started=time.monotonic()
for index,b in enumerate(br['pairs']):
 if not b['physical_nominee_count']:continue
 source=Path(b['script_file']);assert sha(source)==b['script_SHA256'];target=H/('nominate_existing_old_In3_port_source_r315_pair'+str(index)+'.py');assert not target.exists();code=source.read_text()
 old="forbidden=unary_union(cuts);board=unary_union(L.poly(h['outline'])).buffer(-.625);attempts=[];accepted=[]"
 new="""forbidden=unary_union(cuts);board=unary_union(L.poly(h['outline'])).buffer(-.625);attempts=[];accepted=[]
 gp=H/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-all-net-groups.pkl'
 assert sha(gp)=='d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a'
 groups=pickle.loads(gp.read_bytes());lg=[n for n in groups if L.norm(n)=='/LOGIC_GND'];assert len(lg)==1;ground=K.root(groups[lg[0]],'J11001','2')
 ref=unary_union([q['shape'].intersection(roi)for q in ground if q['kind']=='fill'and q['layer']=='In4.Cu'and q['shape'].intersects(roi)])
 caps=[]
 for uid in endpoint_uids:
  v=e['copper'][uid];radius=v['diameters_IU'][LY]/2e6+.275;caps.append(Point([z/1e6 for z in v['at_IU']]).buffer(radius,quad_segs=256))
 reference_with_ONLY_TWO_inscribed_owncaps=unary_union([ref,*caps]);reference_axis=reference_with_ONLY_TWO_inscribed_owncaps.buffer(-.10002)
"""
 assert code.count(old)==1;code=code.replace(old,new)
 old='free=window.intersection(board).difference(forbidden);path=None;search=None'
 new='free=window.intersection(board).difference(forbidden).intersection(reference_axis);path=None;search=None'
 assert code.count(old)==1;code=code.replace(old,new)
 old="path=[[round(x,6),round(y,6)]for x,y in path];body=Z.bounded_buffer(LineString(path),.1);errors=[]"
 new="""path=[[round(x,6),round(y,6)]for x,y in path];body=Z.bounded_buffer(LineString(path),.1);errors=[]
  outside=body.difference(reference_with_ONLY_TWO_inscribed_owncaps)
  if not outside.is_empty:errors.append({'kind':'literal_full_BEFORE_SOURCE_plus_ONLY_TWO_owned_terminal_caps','gap':ds(outside)})
"""
 assert code.count(old)==1;code=code.replace(old,new)
 code=code.replace('r313','r315').replace('R313','R315').replace('physical_current_no_path_in_this_window','physical_AND_actual_BEFORE_source_compatible_no_path_in_this_window')
 code=code.replace('current_FG_union_and_original_plane_profile_interactions','current_LG_and_original_plane_profile_interactions').replace('future_full_native_FG_In4_SOURCE_fullbody_reference_not_credited','future_full_native_LG_In4_SOURCE_fullbody_reference_not_credited')
 compile(code,str(target),'exec');target.write_text(code);print('R315_SOURCE_START',index,b['pair']['normalized_net'],flush=True);runpy.run_path(str(target),run_name='__main__')
 folder=H/('existing-old-In3-port-current-physical-r315-pair'+str(index));receipt=folder/'receipt.json';r=json.loads(receipt.read_bytes());results.append({'pair':b['pair'],'script_file':str(target.resolve()),'script_SHA256':sha(target),'receipt_file':str(receipt.resolve()),'receipt_SHA256':sha(receipt),'nominee_count':r['nominee_count'],'only_exact_two_terminal_caps_used':'inscribed polygons inside declared circles, finite annular transfer/ordinary return/current nativeAfter still REQUIRED'});(OUT/'progress.json').write_text(json.dumps(results,indent=1)+'\n')
(OUT/'receipt.json').write_text(json.dumps({'status':'THREE_EXISTING_PORT_PATHS_CONSTRAINED_TO_ACTUAL_BEFORE_SOURCE_AND_ONLY_TWO_OWNED_CAPS_NATIVE_AFTER_OPEN','physical_batch_SHA256':sha(batch),'results':results,'new_vias':0,'oldCu_deletes':0,'existing_ordinary_returns_or_explicit_private_D4_owned_returns':'OPEN_REQUIRED','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started},indent=1)+'\n');print('R315_SOURCE_BATCH_COMPLETE',sha(OUT/'receipt.json'),flush=True)
