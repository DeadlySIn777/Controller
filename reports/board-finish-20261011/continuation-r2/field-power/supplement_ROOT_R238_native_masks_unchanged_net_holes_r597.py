"""Bind native pad authority and exact new-drill disjoint unchanged-net proof."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
OUT=H/'ROOT-R238-HOST-native-mask-and-exact-unchanged-net-new-drill-supplement-r597'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();audit=H/'ROOT-R238-HOST-independent-actual-drilled-old-contact-return-reference-r593/receipt.json';assert sha(audit)=='ae201321e911af3ebb93ce32b34ea7a3ff9814fc9820b575b724d3670808b3cb';rp=ROOT/'R10007-exact-native-B-pose-and-pad-mask-attestation-r237/receipt.json';assert sha(rp)=='07e29a3b923c4c8a0a73a2704d32939a5bcd10d7b712cba589639ec34b914a7d'
 ar=json.loads(audit.read_bytes());mp=ROOT/'R10007-HOST-current-fresh-native-pad-authority-r238/model.pkl';bp=ROOT/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl';assert sha(mp)==ar['after_model_SHA256']and sha(bp)==ar['before_model_SHA256'];_,h,_,q,c=pickle.loads(mp.read_bytes());_,h0,_,_,before=pickle.loads(bp.read_bytes());r=json.loads(rp.read_bytes());assert r['exit_code']==0;native={x['UUID']:x for x in r['native_attestation']['native_pads']};pads=[]
 for x in h['pads']:
  if x['ref']!='R10007':continue
  n=native[x['uuid']];assert (x['num'],x['net'],x['x'],x['y'],x['smd'],x['hole'])==(n['num'],n['net'],n['x'],n['y'],n['smd'],n['hole']);assert x['layers']==n['layers'];assert next(y for y in c['pads']if y['uuid']==x['uuid'])==x
  pads.append({'UUID':x['uuid'],'pin':x['num'],'raw_net':x['net'],'native_at_mm':[x['x'],x['y']],'actual_native_layers_WKB_SHA256':{l:hashlib.sha256(unary_union(K.L.poly(rs)).wkb).hexdigest()for l,rs in n['layers'].items()},'every_literal_native_polygon_record_and_hole_exact_in_h_and_candidate':True})
 assert len(pads)==2
 pp=ROOT/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r235/exact-discrete-and-rigid-pose-packet.pkl';d=pickle.loads(pp.read_bytes());new=d['vias'][0];hole=Point(new['x'],new['y']).buffer(new['drill']/2,quad_segs=128);ctx=K.hole_context(before);records,trees=K.F.build(before);selected={'/LOGIC_GND','/IO_3V3','/motherboard_do/DOA_SDI_HOST'};hits=[];checked=[]
 for ly in K.LAYERS:
  for j in trees[ly].query(hole,predicate='intersects'):
   x=records[ly][int(j)];net=K.L.norm(x['net'])
   if net in selected:continue
   actual=x['shape'].difference(unary_union([ctx[0][int(k)]for k in ctx[1].query(x['shape'],predicate='intersects')]));hit=actual.intersection(hole);checked.append({'raw_net':x['net'],'kind':x['kind'],'UUID':x['uuid'],'layer':ly,'actual_before_drilled_Cu_hit_empty':hit.is_empty})
   if not hit.is_empty:
    path=OUT/(x['uuid']+'-'+ly+'-actual-new-hole-hit.wkb');path.write_bytes(hit.wkb);hits.append({'raw_net':x['net'],'kind':x['kind'],'UUID':x['uuid'],'layer':ly,'hit_type':hit.geom_type,'hit_area_mm2':hit.area,'hit_length_mm':hit.length,'hit_WKB_SHA256':hashlib.sha256(hit.wkb).hexdigest(),'file':str(path)})
 fgfb={'/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V'};same=[]
 oldz={z['uuid']:z for z in before['zones']}
 for z in c['zones']:
  if K.L.norm(z['net'])in fgfb:assert z==oldz[z['uuid']];same.append(z['uuid'])
 put(OUT/'native-R10007-pad-literal-mask-authority-bindings.json',pads);put(OUT/'actual-new-hole-unchanged-net-broadphase-candidates.json',checked);put(OUT/'actual-new-hole-unchanged-net-intersections.json',hits)
 put(OUT/'receipt.json',{'status':'NATIVE_MASK_AUTHORITY_AND_UNCHANGED_NET_DRILL_DISJOINT_PASS'if not hits else'UNCHANGED_NET_DRILL_INTERSECTION_REPAIR_REQUIRED','independent_R593_source_contact_receipt_SHA256':sha(audit),'native_R237_attestation_SHA256':sha(rp),'actual_R238_model_SHA256':sha(mp),'native_R10007_two_pad_records_holes_positions_RAWnets_exact':True,'new_drill_UUID':new['uuid'],'drill_before_all_holes_operator':'Exact same K.hole_context/K.physical polygon operator as independently recomputed R593; no source-hole filling or field exemption.','unchanged_net_new_drill_hit_count':len(hits),'all_native_FG_FB_current_zone_arrays_metadata_exact':True,'FG_FB_unchanged_zone_count':len(same),'all_unselected_new_drill_disjoint_does_not_waive_foreign_cap_clearance_failures':True,'R593_raw_three_cap_reference_deficits_and_original575_authority_OPEN':True,'R196_FG_CLK_FLT_nine_body_nomination_FAILs_retained':True,'native_fresh_all6_NEWHOST_and_complete_DRC_current':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R595',sha(OUT/'receipt.json'),'unchanged drillhits',len(hits),flush=True)
if __name__=='__main__':main()
