"""Reuse the exact-current physical constructor on unchanged old In3 ports."""
import json,hashlib,runpy,time
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'nominate_current_DOA_SDO_B_surface_transport_r302.py'
pf=H/'actual-native-existing-In3-ports-across-current-logic-groups-r311/actual-unchanged-In3-port-pairs-not-routes.json'
rows=json.loads(pf.read_bytes());selected=[];seen=set()
for r in rows:
 key=r['normalized_net'],r['left_before_group'],r['right_before_group']
 if key not in seen:seen.add(key);selected.append(r)
selected=selected[:6]
OUT=H/'six-existing-old-port-In3-physical-batch-r313';assert not OUT.exists();OUT.mkdir()
results=[];started=time.monotonic()
for number,r in enumerate(selected):
 code=source.read_text();name='existing-old-In3-port-current-physical-r313-pair'+str(number)
 code=code.replace("OUT=H/'current-R753-DOA-SDO-field-no-hole-B-transport-nomination-r302'","OUT=H/"+repr(name))
 old="NET='/motherboard_do/DOA_SDO_FIELD';LY='B.Cu'"
 assert code.count(old)==1;code=code.replace(old,'NET='+repr(r['normalized_net'])+";LY='In3.Cu'")
 begin=code.index(" left=next(x for x in pads")
 end=code.index(" dom=h['domains_normalized']",begin)
 replacement=""" endpoint_uids="""+repr({r['left_port']['UUID'],r['right_port']['UUID']})+"""
 va=e['copper']["""+repr(r['left_port']['UUID'])+"""];vb=e['copper']["""+repr(r['right_port']['UUID'])+"""]
 assert va['kind']==vb['kind']=='via' and L.norm(va['raw_net'])==L.norm(vb['raw_net'])==NET
 assert va['chunk_sha256']=="""+repr(r['left_port']['unchanged_current_native_chunk_SHA256'])+""" and vb['chunk_sha256']=="""+repr(r['right_port']['unchanged_current_native_chunk_SHA256'])+"""
 a=[v/1e6 for v in va['at_IU']];end=[v/1e6 for v in vb['at_IU']]
 assert a=="""+repr(r['left_port']['at_mm'])+""" and end=="""+repr(r['right_port']['at_mm'])+"""
 left=({'net':va['raw_net']},None,None)
 roi=box(min(a[0],end[0])-12,min(a[1],end[1])-12,max(a[0],end[0])+12,max(a[1],end[1])+12)
"""
 code=code[:begin]+replacement+code[end:]
 old="if L.norm(t['raw_net'])!=NET:holes.append((uid,Point(x,y).buffer(t['drill_IU']/2e6,quad_segs=128)))"
 assert code.count(old)==1;code=code.replace(old,"holes.append((uid,Point(x,y).buffer(t['drill_IU']/2e6,quad_segs=128)))")
 old="if L.norm(p['net'])!=NET:holes.append((p['uuid'],s))"
 assert code.count(old)==1;code=code.replace(old,"holes.append((p['uuid'],s))")
 old="if s.intersects(roi):cuts.append(Z.bounded_buffer(s,.1+.275+.005))"
 assert code.count(old)==1;code=code.replace(old,"if uid not in endpoint_uids and s.intersects(roi):cuts.append(Z.bounded_buffer(s,.1+.275+.005))")
 old="if body.distance(s)<.280:errors.append({'kind':'all_foreign_drill_guard'"
 assert code.count(old)==1;code=code.replace(old,"if uid not in endpoint_uids and body.distance(s)<.280:errors.append({'kind':'all_foreign_drill_guard'")
 code=code.replace('R302-SDO-current-B/','R313-existing-In3/'+str(number)+'/').replace('R302_DONE','R313_PAIR_DONE')
 code=code.replace('actual J11003.2 SOURCE In4 full native R299 AFTER','actual J11001.2 LG SOURCE In4; exact own two OLD terminal cap and finite transfer plus existing return gates OPEN')
 code=code.replace('actual J3_In4','actual J1_In4')
 target=H/('nominate_existing_old_In3_port_r313_pair'+str(number)+'.py');assert not target.exists();compile(code,str(target),'exec');target.write_text(code)
 print('R313_START',number,r['normalized_net'],r['span_mm'],flush=True)
 runpy.run_path(str(target),run_name='__main__')
 receipt=H/name/'receipt.json';rr=json.loads(receipt.read_bytes());results.append({'pair':r,'script_file':str(target.resolve()),'script_SHA256':sha(target),'receipt_file':str(receipt.resolve()),'receipt_SHA256':sha(receipt),'physical_nominee_count':rr['nominee_count'],'source_owned_terminal_caps_existing_returns_CURRENT_FULL_AFTER_native':'OPEN'})
 (OUT/'progress.json').write_text(json.dumps(results,indent=1)+'\n')
(OUT/'receipt.json').write_text(json.dumps({'status':'SIX_CURRENT_UNCHANGED_OBSERVED_In3_PORT_PHYSICAL_SCREENS_SOURCE_REFERENCE_RETURN_NATIVE_OPEN','source_constructor_SHA256':sha(source),'source_port_census_SHA256':sha(pf),'pairs':results,'native_jobs':0,'no_new_vias_no_old_Cu_or_board_edit':True,'adopted':False,'elapsed_seconds':time.monotonic()-started},indent=1)+'\n')
print('R313_BATCH_COMPLETE',sha(OUT/'receipt.json'),flush=True)
