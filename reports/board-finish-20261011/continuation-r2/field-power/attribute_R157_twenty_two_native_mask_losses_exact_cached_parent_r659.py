"""Read-only finite native annulus/fill/owned-peer attribution, no fake flash."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,collections
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
OUT=H/'R157-twenty-two-native-mask-loss-exact-cached-parent-finite-annulus-attribution-r659'
B=H/'eedf-original-parent-exact-cached-native-BEFORE-dump-r648/native-cached'
N=ROOT/'R155-known-reference-native-diagnostic-r157/measure'
M=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r643/model.pkl'
OLD=ROOT/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):
 t=set_precision(s,0);assert t.wkb==s.wkb;return t
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def make_records(dump):
 rows=collections.defaultdict(list)
 for z in dump['zones']:
  for ly,rs in z['fills'].items():
   for i,s in enumerate(L.poly(O.polys(rs))):rows[ly].append({'UUID':z['uuid'],'raw_net':z['net'],'record_index':i,'shape':s,'priority':z['priority'],'local_clearance_mm':z['clearance_mm']})
 trees={ly:STRtree([x['shape']for x in xs])for ly,xs in rows.items()};return rows,trees
def query(rr,tt,ly,window,raw=None):
 if ly not in tt:return[]
 return[rr[ly][int(i)]for i in tt[ly].query(window,predicate='intersects')if raw is None or rr[ly][int(i)]['raw_net']==raw]
def fill_summary(rr,tt,ly,ann,raw):
 hits=query(rr,tt,ly,ann,raw);return[{'UUID':r['UUID'],'raw_net':r['raw_net'],'record_index':r['record_index'],'priority':r['priority'],'local_clearance_mm':r['local_clearance_mm'],'nominal_drill_subtracted_annulus_intersection':ds(ann.intersection(r['shape'])),'gap_mm':ann.distance(r['shape'])}for r in hits]
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic()
 paths=[B/'cached-geometry.json',B/'actual-cached-native-via-geometry-and-flashes.json',N/'actual-full-refill-contract.json',N/'actual-full-refill-geometry.json',N/'actual-full-refill-via-flashes.json',M,OLD]
 pins={str(f.resolve()):sha(f)for f in paths};assert sha(paths[0])=='fb9302a169981fc77fd8493ae80919c7ebe72c561701e7095d3cf377a06814e0';assert sha(paths[3])=='421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b';assert sha(M)=='7141d6d37a909617aa339dadfc3b8a1b539904af1b06b2bf8f00ea2abeee69f9';assert sha(OLD)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 before=json.loads(paths[0].read_bytes());bm=json.loads(paths[1].read_bytes())['vias'];contract=json.loads(paths[2].read_bytes());after=json.loads(paths[3].read_bytes());fm=json.loads(paths[4].read_bytes())['vias'];g,h,b,q,c=pickle.loads(M.read_bytes());og,oh,ob,oq,oc=pickle.loads(OLD.read_bytes());ctx=K.hole_context(c);br,bt=make_records(before);nr,nt=make_records(after);actualv={v['uuid']:v for v in after['vias']};currentv={v['uuid']:v for v in c['vias']};rows=[]
 for e in contract['postfill_Cu_or_flash_errors']:
  uid=e['uuid'];v=actualv[uid];cv=currentv[uid];bvia=bm[uid];assert v['net']==cv['net']==bvia['raw_net']and v['at']==[cv['x'],cv['y']]==[x/1e6 for x in bvia['at_IU']];assert v['drill']==cv['drill']==bvia['drill_IU']/1e6;assert v['w']==cv['d'];assert fm[uid]==e['actual_flashes']
  at=Point(v['at']);disk=at.buffer(v['w']/2,quad_segs=64);ann=disk.difference(at.buffer(v['drill']/2,quad_segs=64));holes=[ctx[0][int(i)]for i in ctx[1].query(disk,predicate='intersects')];ann=ann.difference(unary_union(holes));assert not ann.is_empty
  for ly in e['missing_original_parent_actual_flashes']:
   assert ly in bvia['actual_FlashLayer']and ly not in fm[uid]
   window=at.buffer(1.25,quad_segs=64);oldhits=fill_summary(br,bt,ly,ann,v['net']);newhits=fill_summary(nr,nt,ly,ann,v['net']);newnear=query(nr,nt,ly,window,v['net']);nearest=min((ann.distance(r['shape'])for r in newnear),default=None)
   peers=[]
   for label,zs in [('R155_REFILLED_INPUT_OWNED_ROLES',oq),('R643_LATER_DIRECTION_UNION_PROPOSALS',q)]:
    for z in zs:
     if z['layer']!=ly or z['net']==v['net']:continue
     required=.15 if h['domains_normalized'][L.norm(z['net'])]==h['domains_normalized'][L.norm(v['net'])]else .6
     for role in ('shape','zone_outline_shape'):
      sh=zero(z[role]);gap=sh.distance(ann)
      if gap>required+.15:continue
      peers.append({'head':label,'owner_UUID':z['uuid'],'constituents':z.get('constituent_proposal_UUIDs',[]),'raw_net':z['net'],'role':role,'role_SHA256':hs(sh),'gap_to_nominal_actual_drill_subtracted_annulus_mm':gap,'domain_native_required_mm':required,'native_guard_conflicts_annulus':gap<required,'planner_guard_conflicts_annulus':gap<required+.025,'role_intersection_nominal_annulus':ds(sh.intersection(ann))})
   currenthits=[]
   for z in c['zones']:
    if z['net']!=v['net']or ly not in z['fills']:continue
    for ix,sh in enumerate(L.poly(z['fills'][ly])):
     hit=ann.intersection(sh)
     if not hit.is_empty:currenthits.append({'UUID':z['uuid'],'record':ix,'intersection':ds(hit)})
   layer={'via_UUID':uid,'raw_net':v['net'],'at_mm':v['at'],'diameter_mm':v['w'],'drill_mm':v['drill'],'missing_layer':ly,'cached_parent_actual_mask':bvia['actual_FlashLayer'],'refilled_actual_mask':fm[uid],'original_via_discrete_position_drill_diameter_rawnet_unchanged':True,'nominal_finite_annulus_with_ALL_actual_drills_subtracted':ds(ann),'cached_native_BEFORE_same_net_fill_contacts':oldhits,'FULL_REFILLED_same_net_fill_contacts_at_nominal_annulus':newhits,'nearest_FULL_REFILLED_same_net_fill_gap_within_1p25mm':nearest,'owned_foreign_role_guard_attribution':peers,'later_R643_HOST_actual_current_same_net_fill_contacts_NOT_CPP':currenthits,'native_actual_missing_layer_annular_Cu':False,'source_root_membership_current_capacity_reference':'OPEN_SEPARATE_FROM_NOMINAL_FILL_INTERSECTION'};rows.append(layer);put(OUT/'checkpoint-attributions.json',rows);print('R659',uid[:8],ly,'before',len(oldhits),'after',len(newhits),'later',len(currenthits),'peer',len(peers),flush=True)
 put(OUT/'twenty-two-vias-twenty-three-layer-exact-attribution.json',rows)
 put(OUT/'receipt.json',{'status':'READ_ONLY_NATIVE_22_MASK_FAILURE_FINITE_FILL_AND_CURRENT_OWNED_ROLE_ATTRIBUTION_COMPLETE_NO_REPAIR_OR_FLASH_WAIVER','inputs_SHA256':pins,'attribution_SHA256':sha(OUT/'twenty-two-vias-twenty-three-layer-exact-attribution.json'),'original_parent_lost_via_count':len(contract['postfill_Cu_or_flash_errors']),'lost_layer_count':len(rows),'cached_parent_native_before_not_refilled':True,'native_FULL_REFILLED_after':True,'later_R643_contacts_host_only':True,'all_native_22_failure_flags_and_original_actual_masks_preserved':True,'forced_annuli_remove_unused_layers_source_native_Cu_or_plane_edits':False,'fresh_source_component_current_thermal_reference_qualification':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R659_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
