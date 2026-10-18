"""Triage the three physical old-port paths using real native BEFORE source.

Only their own two existing terminals can explain raw reference holes. These
are preliminary source/transfer and existing-return checks, not native AFTER.
"""
import sys,json,pickle,hashlib,time,math
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;sha=N.sha
OUT=H/'R313-existing-port-In3-source-own-caps-return-and-newnew-triage-r314'
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir()
 batch=H/'six-existing-old-port-In3-physical-batch-r313/receipt.json';assert sha(batch)=='ec835ba5aa774b735cb559fd899ca3fb1fadfc414e72c0f70d3313612a9b3347';br=json.loads(batch.read_bytes())
 gp=H/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-all-net-groups.pkl';assert sha(gp)=='d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a';gg=pickle.loads(gp.read_bytes());lg=[n for n in gg if L.norm(n)=='/LOGIC_GND'];assert len(lg)==1;src=K.root(gg[lg[0]],'J11001','2')
 ep=H/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json';assert sha(ep)=='13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3';e=json.loads(ep.read_bytes())
 fills={ly:[r for r in src if r['kind']=='fill'and r['layer']==ly]for ly in ('In1.Cu','In4.Cu')};trees={ly:STRtree([r['shape']for r in rr])for ly,rr in fills.items()}
 def support(body,ly):return unary_union([body.intersection(fills[ly][int(i)]['shape'])for i in trees[ly].query(body,predicate='intersects')])
 returns={}
 for r in src:
  if r['kind']=='via'and r['layer']in fills:returns.setdefault(r['uuid'],{}).setdefault(r['layer'],[]).append(r['shape'])
 rows=[];packets=[]
 for bi,b in enumerate(br['pairs']):
  if not b['physical_nominee_count']:continue
  folder=Path(b['receipt_file']).parent;pf=folder/'only-new-SDO-B-tracks-physical-nominee-NOT_MODEL.pkl';nominees=pickle.loads(pf.read_bytes());assert len(nominees)==1;n=nominees[0];body=__import__('shapely').from_wkb(n['whole_body_WKB']);pair=b['pair'];ports=[pair['left_port'],pair['right_port']];caps=[];terminal=[]
  for p in ports:
   t=e['copper'][p['UUID']];assert t['chunk_sha256']==p['unchanged_current_native_chunk_SHA256'];at=[v/1e6 for v in t['at_IU']];radius=t['diameters_IU']['In3.Cu']/2e6+.275
   # This inscribed polygon is contained by the EXACT declared circle;
   # no enlarged boundary tolerance or neighboring cap is admitted.
   cap=Point(at).buffer(radius,quad_segs=256);caps.append(cap)
   ann=Point(at).buffer(t['diameters_IU']['In3.Cu']/2e6,quad_segs=256).difference(Point(at).buffer(t['drill_IU']/2e6,quad_segs=256));join=body.intersection(ann);transfer=support(body.intersection(cap),'In4.Cu');near=[]
   for uid,layers in returns.items():
    gt=e['copper'].get(uid)
    if not gt or gt['kind']!='via' or L.norm(gt['raw_net'])!='/LOGIC_GND' or set(layers)!={'In1.Cu','In4.Cu'}:continue
    pos=[v/1e6 for v in gt['at_IU']];distance=math.dist(at,pos)
    if not .90<=distance<=1.0:continue
    contacts={ly:support(unary_union(ss),ly)for ly,ss in layers.items()}
    if all(not s.is_empty and s.area>0 for s in contacts.values()):near.append({'UUID':uid,'distance_mm':distance,'finite_actual_BEFORE_SOURCE_annular_contacts':{ly:ds(s)for ly,s in contacts.items()}})
   terminal.append({'signal_UUID':p['UUID'],'exact_current_native_at_IU':t['at_IU'],'declared_own_terminal_circle_radius_mm':radius,'cap_inscribed_WKB_SHA256':sha_bytes(cap.wkb),'physical_SG_annular_newbody_join':ds(join),'finite_SOURCE_In4_newbody_transfer_inside_owncap':ds(transfer),'ordinary_existing_before_SOURCE_returns':near,'D4_private_samepart_ownership_if_no_ordinary_return':'OPEN_NOT_INFERRED_FROM_COURTYARD_OR_NET_GROUP'})
  raw=body.difference(support(body,'In4.Cu'));gap=raw.difference(unary_union(caps));(OUT/('pair-'+str(bi)+'-raw-reference-gap.wkb')).write_bytes(raw.wkb);(OUT/('pair-'+str(bi)+'-gap-outside-two-inscribed-own-caps.wkb')).write_bytes(gap.wkb)
  row={'batch_pair_index':bi,'normalized_net':pair['normalized_net'],'path_packet_SHA256':sha(pf),'raw_fullbody_actual_SOURCE_In4_gap':ds(raw),'gap_outside_only_two_exact_owned_terminal_circles':ds(gap),'terminals':terminal,'inherited_FG_template_labels':'corrected_by_this_LOGIC_J11001_LG_scope_record_ONLY_no_result_or_geometry_rewrite','matching_current_FULL_NATIVE_AFTER_allgraphs_source_mask_caps_clearance_current_and_SI':'OPEN'};rows.append(row);packets.append((row,n,body))
 newnew=[]
 for i,(a,na,ba)in enumerate(packets):
  for b,nb,bb in packets[i+1:]:
   if a['normalized_net']!=b['normalized_net']:newnew.append({'left':a['batch_pair_index'],'right':b['batch_pair_index'],'actual_body_gap_mm':ba.distance(bb),'same_domain_planning_required_mm':.175,'error':ba.distance(bb)<.175})
 put('source-own-cap-transfer-and-existing-return-triage.json',rows);put('new-new.json',newnew)
 put('receipt.json',{'status':'ACTUAL_FULL_BEFORE_OWN_TERMINAL_SOURCE_AND_EXISTING_RETURN_TRIAGE_NATIVE_AFTER_OPEN','batch_SHA256':sha(batch),'actual_source_groups_SHA256':sha(gp),'current_native_Cu_SHA256':sha(ep),'nominees':len(rows),'outside_own_cap_reference_failures':sum(not r['gap_outside_only_two_exact_owned_terminal_circles']['EMPTY']for r in rows),'ordinary_return_missing_terminals':sum(not t['ordinary_existing_before_SOURCE_returns']for r in rows for t in r['terminals']),'annular_join_or_source_transfer_missing_terminals':sum(t['physical_SG_annular_newbody_join']['EMPTY']or t['finite_SOURCE_In4_newbody_transfer_inside_owncap']['EMPTY']for r in rows for t in r['terminals']),'new_new_geometry_errors':sum(r['error']for r in newnew),'no_new_vias_no_other_cap_or_hole_borrowed_no_geometry_tolerance':True,'current_NATIVE_AFTER_D4_ifneeded_all_source_oldreference_directtouch_mask_power_fault_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R314_TRIAGE',sha(OUT/'receipt.json'),flush=True)
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
if __name__=='__main__':main()
