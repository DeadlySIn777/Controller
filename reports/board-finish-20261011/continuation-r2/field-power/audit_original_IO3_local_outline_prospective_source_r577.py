"""Read-only clipped-Cu influence screen; actual native refill remains required."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,collections,time
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
from shapely import from_wkb
N=ROOT/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218';T=H/'original-IO3-TMR-exact-local-two-notch-negative-outline-nominee-r573';OLD=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r563';M=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl';OUT=H/'original-IO3-TMR-local-outline-prospective-actual-drill-source-contact-r577';RAW='/IO_3V3';UID='54921f4b-0308-4821-9549-ff9360bf05ca'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(T/'receipt.json')=='eda8658d0265d323ac494b5a293d2f144912f3cd99adc257ede5b8433d1f98eb';assert sha(M)=='4f70c8271d57724e41005d19c178ba597059085e7192955d7605cf20d501f862'
 packet=pickle.loads((T/'only-one-original-IO3-zone-outline-negative-replacement.pkl').read_bytes());loss=from_wkb((T/'actual-outline-negative-removal.wkb').read_bytes());old=pickle.loads((OLD/'fresh-native-selected-all-drilled-groups.pkl').read_bytes());g,h,b,q,c=pickle.loads(M.read_bytes());ng=json.loads((N/'scoped-fill/geometry.json').read_bytes());fl=json.loads((N/'scoped-fill/actual-via-flashes.json').read_bytes())['vias'];raws={'/IO_3V3','/motherboard_power_entry{slash}FIELD_A_24V_PROTECTED'}
 index=collections.defaultdict(list)
 for x in h['pads']:
  if x['net']in raws:index[x['ref'],str(x['num']),x['x'],x['y'],x['net']].append(x)
 rp={}
 for x in ng['pads']:
  if x['net']not in raws:continue
  matches=index[x['ref'],str(x['num']),*x['at'],x['net']];assert len(matches)==1;v=matches[0];rp[v['uuid']]={**v,'layers':{ly:O.polys(x['poly'])for ly in x['layers']}}
 pads=[rp.get(x['uuid'],x)for x in h['pads']];vias=[{**x,'flashed':fl[x['uuid']]}for x in h['vias']];zones=[{**x,'fills':{ly:O.polys(rs)for ly,rs in x['fills'].items()}}for x in ng['zones']if x['net']in raws];candidate={**c,'pads':pads,'vias':vias,'zones':[x for x in c['zones']if x['net']not in raws]+zones}
 beforezone=next(x for x in candidate['zones']if x['uuid']==UID);before_records=L.poly(beforezone['fills']['In2.Cu']);after=[];changes=[]
 for i,r in enumerate(before_records):
  if not r.intersects(loss):after.append(r);continue
  a=r.difference(loss);gain=a.difference(r);outside_removed=r.difference(a).difference(loss);(OUT/('record-'+str(i)+'-raw-gain-control.wkb')).write_bytes(gain.wkb);(OUT/('record-'+str(i)+'-removed-outside-proposed-outline-loss.wkb')).write_bytes(outside_removed.wkb)
  changes.append({'record':i,'before':ds(r),'after':ds(a),'raw_gained':ds(gain),'raw_removed_outside_exact_outline_loss':ds(outside_removed)})
  assert gain.is_empty,changes[-1]
  # Nonempty outside-scope loss remains an explicit FAIL. This separately
  # named read-only topology diagnostic never grants geometric acceptance.
  assert a.is_empty or a.geom_type in ('Polygon','MultiPolygon'),a.geom_type
  if not a.is_empty:after.extend(list(a.geoms)if a.geom_type=='MultiPolygon'else[a])
 # Direct shape-to-record conversion uses the existing exact layer parser;
 # this virtual model is never serialized as native cache or a board model.
 import immutable_local_fill_subtraction_r254 as IM
 virtualzone={**beforezone,'fills':{**beforezone['fills'],'In2.Cu':sum((IM.records(x)for x in after),[])}}
 virtual={**candidate,'zones':[virtualzone if x['uuid']==UID else x for x in candidate['zones']]}
 _,groups=K.physical(virtual,RAW,K.hole_context(virtual));root=K.root(groups,'R18001','2');prior=K.root(old[RAW],'R18001','2');rels,bad=K.contact_losses(old[RAW],groups);lost=sorted(K.keys(prior)-K.keys(root));put(OUT/'all-R218-prior-IO3-physical-relationships.json',rels)
 fills_before=unary_union(L.poly(beforezone['fills']['In2.Cu']));fills_after=unary_union(L.poly(virtualzone['fills']['In2.Cu']));body_loss=fills_before.difference(fills_after);direct=[];oldfill=unary_union([r['shape']for xs in old[RAW]for r in xs if r['kind']=='fill'and r['layer']=='In2.Cu']);newfill=unary_union([r['shape']for xs in groups for r in xs if r['kind']=='fill'and r['layer']=='In2.Cu']);metal={}
 for xs in old[RAW]:
  for r in xs:
   if r['layer']=='In2.Cu'and r['kind']!='fill':metal[r['kind'],r['uuid'],r['layer']]=r['shape']
 for key,shape in metal.items():
  if oldfill.is_empty or shape.distance(oldfill)>.000002:continue
  gap=None if newfill.is_empty else shape.distance(newfill);direct.append({'native_discrete_key':list(key),'same_real_native_drill_subtracted_metal_shape':True,'before_actual_any_native_In2_fill_touch':True,'after_prospective_any_In2_fill_touch':gap is not None and gap<=.000002,'after_gap_mm':gap})
 nozone=fills_after.intersection(Polygon([(348.198,130.35),(323.998,130.35),(323.998,118.65)]));directbad=[r for r in direct if not r['after_prospective_any_In2_fill_touch']];(OUT/'prospective-drilled-IO3-groups-NOT-native-filled.pkl').write_bytes(pickle.dumps({RAW:groups},protocol=5));put(OUT/'local-record-negative-controls.json',changes);put(OUT/'all-actual-R218-before-In2-direct-native-metal-contacts.json',direct)
 raw_clip_fail=[x for x in changes if not x['raw_removed_outside_exact_outline_loss']['empty']];status='FAILED_NEGATIVE_CLIP_BOUND_TO_PROSPECTIVE_SOURCE_TOPOLOGY_DIAGNOSTIC_ACTUAL_CPP_REQUIRED'if raw_clip_fail else'PROSPECTIVE_SOURCE_TOPOLOGY_ONLY_CPP_REQUIRED';source_positive=not lost and not bad and not directbad and nozone.is_empty
 put(OUT/'receipt.json',{'status':status,'input_R573_SHA256':sha(T/'receipt.json'),'input_R563_actual_native_source_SHA256':sha(OLD/'receipt.json'),'all_changed_records':changes,'raw_negative_clip_failures_not_waived':raw_clip_fail,'prospective_source_contact_topology_no_loss_only':source_positive,'actual_R218_prior_named_IO3_sourcepads':len({r['uuid']for r in prior if r['kind']=='pad'and str(r['pin'])}),'prospective_named_IO3_sourcepads':len({r['uuid']for r in root if r['kind']=='pad'and str(r['pin'])}),'source_keys_lost':[list(x)for x in lost],'all_prior_actual_native_IO3_relationships_lost':bad,'prior_actual_In2_direct_touch_count':len(direct),'prospective_direct_touch_losses':directbad,'actual_native_physical_Cu_geometric_strip_loss':ds(body_loss),'prospective_closed_TMR_physical_hit':ds(nozone),'LG_FAG_FBG_native_fill_arrays_and_all_In1_In4_source_reference_primitives':'BYTE_AND_COORDINATE_EXACT_UNCHANGED_BY_IN2_ONLY_DECLARED_SCOPE','all_original_native_outline_settings_other_zone_definitions_native_discrete_sources_rules':'UNCHANGED_EXCEPT_FROZEN_R573_DECLARED_ORIGINAL5492_OUTLINE_DELTA','all_actual_605_direct_contacts_after_fresh_native_fill':'OPEN; this screen checks current actual In2 contacts plus other-layer identity only','actual_native_cpp_refill_source_contact_reference_API_source_current_thermal':'OPEN','virtual_geometric_projection_is_not_actual_CPP_refill_or_native_cache_edit':True,'no_model_board_native_fill_or_input_saved':True,'R563_R569_R571_raw_failures_preserved':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R575',sha(OUT/'receipt.json'),status,'source',len({r['uuid']for r in root if r['kind']=='pad'and str(r['pin'])}),'lost',len(lost),'groups',len(groups),flush=True)
if __name__=='__main__':main()
