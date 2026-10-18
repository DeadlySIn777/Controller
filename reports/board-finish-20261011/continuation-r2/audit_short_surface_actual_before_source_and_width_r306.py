"""Independent actual source/width triage for the R305 physical nominees.

No connection is credited on the board and no nominal current is replaced by
a guessed load. Full-AFTER native state remains a separate necessary gate.
"""
import sys,json,pickle,time,hashlib
from pathlib import Path
from shapely.geometry import GeometryCollection
from shapely.ops import unary_union
from shapely import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;sha=N.sha
OUT=H/'R305-short-surface-actual-native-BEFORE-source-and-width-triage-r306'
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def summary(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir()
 packet=H/'current-R753-short-logic-no-hole-surface-construction-r305/ONLY_NEW-short-surface-physical-nominees-NOT_MODEL.pkl'
 assert sha(packet)=='1deac7f8a6ff3ed96c78ecfa6b8e30d26e381a306f84066b3facc64e97e5eb48'
 nominees=pickle.loads(packet.read_bytes())
 gp=H/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-all-net-groups.pkl'
 assert sha(gp)=='d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a';groups=pickle.loads(gp.read_bytes())
 lgkeys=[key for key in groups if L.norm(key)=='/LOGIC_GND'];assert len(lgkeys)==1
 source=K.root(groups[lgkeys[0]],'J11001','2')
 refindex={};contactindex={}
 for ly in ('F.Cu','B.Cu','In1.Cu','In4.Cu'):
  rr=[r for r in source if r['layer']==ly];contactindex[ly]=(rr,STRtree([r['shape']for r in rr]))
  ff=[r for r in rr if r['kind']=='fill'];refindex[ly]=(ff,STRtree([r['shape']for r in ff]))
 widthsfile=Path('Z:/pcb-runs/claude-finish/tools/power_widths.json');widths=json.loads(widthsfile.read_bytes())
 rows=[]
 for r in nominees:
  body=r['body'];net=r['normalized_net'];ly=r['layer'];inner=K.MAP[ly]
  rr,tree=refindex[inner];support=unary_union([body.intersection(rr[int(i)]['shape']) for i in tree.query(body,predicate='intersects')]);gap=body.difference(support)
  rr,tree=contactindex[ly];contact=unary_union([body.intersection(rr[int(i)]['shape']) for i in tree.query(body,predicate='intersects')])
  key=[n for n in groups if L.norm(n)==net];assert len(key)==1
  touched=[]
  for index,old in enumerate(groups[key[0]]):
   if any(q['kind']=='pad' and q['uuid'] in r['endpoints'] for q in old):touched.append(index)
  table=widths.get(net);width=min(t['w']for t in r['tracks']);width_failure=bool(table and width<table['width'])
  row={'index':r['index'],'normalized_net':net,'layer':ly,'actual_BEFORE_endpoint_group_indices':touched,'raw_source_LG_full_body_reference_gap':summary(gap),'real_BEFORE_J1_same_surface_contact':summary(contact),'GROUND_reference_shadow_is_not_a_SIGNAL_test':net=='/LOGIC_GND','nominee_width_mm':width,'historical_IS1_table_width_mm':None if not table else table['width'],'historical_table_width_deficit_requires_rejection_or_new_authoritative_local_load_IR_proof':width_failure,'historical_table_is_not_current_motherboard_electrical_qualification':True,'actual_matching_FULL_AFTER_current_source_keys_alloldgroups_fill_masks_reference_foreign_Cu_and_current':'OPEN'}
  (OUT/('index-'+str(r['index'])+'-raw-BEFORE-LG-reference-gap.wkb')).write_bytes(gap.wkb);rows.append(row)
 put('triage.json',rows)
 put('receipt.json',{'status':'ACTUAL_FULL_BEFORE_SOURCE_WIDTH_TRIAGE_NO_ADOPTION','nominee_packet_SHA256':sha(packet),'actual_all_net_groups_SHA256':sha(gp),'historical_power_widths_SHA256':sha(widthsfile),'count':len(rows),'raw_non_ground_reference_gap_count':sum(not r['raw_source_LG_full_body_reference_gap']['EMPTY'] and r['normalized_net']!='/LOGIC_GND' for r in rows),'historical_width_deficits':sum(r['historical_table_width_deficit_requires_rejection_or_new_authoritative_local_load_IR_proof']for r in rows),'GROUND_real_BEFORE_source_contact_missing':sum(r['real_BEFORE_J1_same_surface_contact']['EMPTY']for r in rows if r['normalized_net']=='/LOGIC_GND'),'matching_FULL_AFTER_native_source_reference_current':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started})
 print('R306_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
