"""Explicit local Cu nominations on actual rooted barrels; never force flags."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,time,uuid,math,re
from pathlib import Path
from shapely.geometry import Point,Polygon,LineString
from shapely.ops import unary_union
from shapely import set_precision
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import fast_contacts as F
import ordinary_routes as O
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from emit_logic_zones_r1 import render
from verify_source import parse,children,child,atom
OUT=H/'R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665'
M=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r643/model.pkl'
N=ROOT/'R155-known-reference-native-diagnostic-r157/measure'
R=H/'R157-actual-three-ground-native-all-drill-source-groups-r663'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):
 t=set_precision(s,0);assert t.wkb==s.wkb;return t
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(M)=='7141d6d37a909617aa339dadfc3b8a1b539904af1b06b2bf8f00ea2abeee69f9';assert sha(R/'receipt.json')=='33703477904ca3cc046c80e741f59897c68c04d2c6dd13d307792d006b1bb1cd'
 g,h,b,q,c=pickle.loads(M.read_bytes());a=json.loads((R/'twenty-two-old-via-real-barrel-source-membership.json').read_bytes());assert len(a)==22 and all(x['actual_via_barrel_joined_to_external_source_on_an_observed_layer']for x in a);native=json.loads((N/'actual-full-refill-geometry.json').read_bytes());ctx=K.hole_context(c);vby={v['uuid']:v for v in c['vias']};rec,trees=F.build({**c,'zones':[]});fillrows={};filltrees={}
 for z in native['zones']:
  for ly,rs in z['fills'].items():
   for s in L.poly(O.polys(rs)):fillrows.setdefault(ly,[]).append((z,s))
 for ly,rs in fillrows.items():filltrees[ly]=STRtree([r[1]for r in rs])
 dru=N/'copy/board.kicad_dru';rules=[]
 for name,cond,what in re.findall(r'\(rule "([^"\n]*)"\s*\(condition "([^"\n]*)"\)\s*\(constraint disallow ([^)]*)\)\)',dru.read_text(encoding='utf-8')):
  if 'zone'not in what.split():continue
  names=re.findall(r"A.intersectsArea\('([^']+)'\)",cond);assert len(names)==1;area=next(r for r in h['rule_areas']if r.get('name')==names[0]);rules.append((name,area,re.findall(r"A.NetName != '([^']+)'",cond)))
 rules.extend((r.get('name',r['uuid']),r,[])for r in h['rule_areas']if r.get('no_zones'))
 accepted=[];attempts=[];checks=[];bad=[];chunks=[]
 for src in a:
  v=vby[src['via_UUID']];assert v['net']==src['raw_net'];centre=(int(round(v['x']*1e6)),int(round(v['y']*1e6)))
  for ly in src['mask_contract_missing_layers']:
   uid=str(uuid.uuid5(uuid.UUID(v['uuid']),'R157-rooted-native-local-ground-landing-'+ly));ring=[(centre[0]+int(round(250000*math.cos(2*math.pi*i/256))),centre[1]+int(round(250000*math.sin(2*math.pi*i/256))))for i in range(256)];outline=Polygon([(x/1e6,y/1e6)for x,y in ring]);assert outline.is_valid and outline.covers(Point(v['x'],v['y']));outline=set_precision(outline,1e-6,mode='pointwise');ownholes=[ctx[0][int(i)]for i in ctx[1].query(outline,predicate='intersects')];physical=zero(outline).difference(unary_union(ownholes));assert not physical.is_empty;minwidth=max(Point(v['x'],v['y']).distance(Point(x,y))for x,y in outline.exterior.coords)-v['drill']/2
   z={'uuid':uid,'label':'actual-source-rooted-old-barrel-local-ground-landing','net':v['net'],'layer':ly,'shape':physical,'zone_outline_shape':outline,'priority':124,'clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3,'existing_source_via_UUID':v['uuid'],'required_native_new_flash_layer':ly,'actual_source_rooted_other_native_layers':src['actual_native_remaining_source_rooted_layers'],'native_flash_forced':False};errors=[];sameown=[]
   dom=h['domains_normalized'][L.norm(v['net'])];gapfor=lambda raw:.15 if h['domains_normalized'][L.norm(raw)]==dom else .6
   for j in trees[ly].query(outline.buffer(.85),predicate='intersects'):
    r=rec[ly][int(j)]
    if r['net']==v['net']:continue
    if r['kind']=='via':other=r['source'];distance=Point(other['x'],other['y']).distance(physical)-other['d']/2
    elif r['kind']=='track'and not r['source'].get('m'):other=r['source'];distance=LineString([other['a'],other['b']]).distance(physical)-other['w']/2
    else:distance=zero(r['shape']).distance(physical)
    row={'landing_UUID':uid,'kind':'TRUE_'+r['kind'],'foreign_UUID':r['uuid'],'raw_net':r['net'],'gap_mm':distance,'native_required_mm':gapfor(r['net']),'planner_required_mm':gapfor(r['net'])+.025};checks.append(row)
    if distance<row['planner_required_mm']:errors.append(row)
   for j in filltrees[ly].query(outline.buffer(.85),predicate='intersects'):
    other,shape=fillrows[ly][int(j)]
    if other['net']==v['net']:continue
    distance=shape.distance(physical);req=max(gapfor(other['net']),other['clearance_mm'],.15);row={'landing_UUID':uid,'kind':'ACTUAL_FULL_NATIVE_FOREIGN_FILL','foreign_UUID':other['uuid'],'raw_net':other['net'],'gap_mm':distance,'native_required_mm':req,'planner_required_mm':req+.025};checks.append(row)
    if distance<req+.025:errors.append(row)
   for other in q:
    if other['layer']!=ly:continue
    if other['net']==v['net']:
     hit=zero(outline).intersection(zero(other['zone_outline_shape']))
     if not hit.is_empty:sameown.append({'UUID':other['uuid'],'actual_same_raw_intended_intersection':ds(hit),'same_nine_settings':all(other[k]==z[k]for k in ('priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm'))})
     continue
    for role in ('shape','zone_outline_shape'):
     distance=zero(other[role]).distance(physical)
     if distance>.85:continue
     req=max(gapfor(other['net']),float(other['clearance_mm']),.15);row={'landing_UUID':uid,'kind':'LATER_OWNED_FOREIGN_'+role,'foreign_UUID':other['uuid'],'raw_net':other['net'],'gap_mm':distance,'native_required_mm':req,'planner_required_mm':req+.025};checks.append(row)
     if distance<req+.025:errors.append(row)
   for name,area,exempt in rules:
    if ly not in area['layers']or v['net']in exempt:continue
    ash=unary_union(L.poly(area['outline']));hit=zero(outline).intersection(ash)
    if not hit.is_empty:errors.append({'landing_UUID':uid,'kind':'ACTUAL_NATIVE_NO_ZONE','rule':name,'intersection':ds(hit)})
   row={'landing_UUID':uid,'old_via_UUID':v['uuid'],'raw_net':v['net'],'at_mm':[v['x'],v['y']],'layer':ly,'nominal_outer_diameter_mm':.5,'actual_polygon_max_radius_mm':minwidth+v['drill']/2,'nominal_barrel_annular_radial_width_mm':minwidth,'explicit_added_ground_physical_Cu':ds(physical),'intended_no_own_drill_hole_covers_old_barrel_centre':True,'min_thickness_mm':.15,'native_min_feature_AND_flash_survival':'OPEN_ACTUAL_CPP_REQUIRED','actual_other_native_layer_source_proof':src,'same_owned_profile_overlap_obligations':sameown,'guard_errors':errors};attempts.append(row);bad+=errors
   if errors or sameown:continue
   text=render(uid,z['net'],ly,outline).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','Actual source rooted old barrel landing');ast=parse(text);rings=[[(int(round(float(x[1])*1e6)),int(round(float(x[2])*1e6)))for x in child(p,'pts')[1:]]for p in children(ast,'polygon')];assert rings==[ring]and atom(ast,'net')==z['net'];f=OUT/(uid+'.zone-chunk');f.write_text(text,encoding='utf-8',newline='');chunks.append({'uuid':uid,'raw_net':z['net'],'layer':ly,'rings_IU':[ring],'declared_native_settings':{'priority':124,'local_clearance_IU':150000,'minimum_thickness_IU':150000,'thermal_gap_IU':150000,'thermal_spoke_IU':300000,'island_removal_mode':1},'chunk_file':str(f.resolve()),'chunk_SHA256':sha(f)});accepted.append(z)
   print('R665',v['uuid'][:8],ly,'guarderrors',len(errors),'overlaps',len(sameown),flush=True)
 pk=OUT/'only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl';pk.write_bytes(pickle.dumps(accepted,protocol=5));put(OUT/'complete-native-peer-true-copper-guard-checks.json',checks);put(OUT/'all-23-local-landing-attempts-and-raw-failures.json',attempts);put(OUT/'native-exact-local-zone-chunk-rows.json',chunks)
 put(OUT/'receipt.json',{'status':'MINIMAL_ROOTED_OLD_BARREL_LANDING_NOMINEES_GUARDS_PASS_NATIVE_SOURCE_FLASH_PENDING'if len(accepted)==23 else'PARTIAL_LOCAL_LANDING_NOMINATION_REPAIR_REQUIRED','later_peer_head_SHA256':sha(M),'actual_native_source_receipt_SHA256':sha(R/'receipt.json'),'actual_native_geometry_SHA256':sha(N/'actual-full-refill-geometry.json'),'attempted_lost_layer_count':len(attempts),'accepted_nominee_count':len(accepted),'guard_error_count':len(bad),'proposal_packet_SHA256':sha(pk),'chunks_manifest_SHA256':sha(OUT/'native-exact-local-zone-chunk-rows.json'),'all_original_holes_masks_native_Cu_outlines_profiles_untouched':True,'missing_native_flash_layers_NOT_FORCED_OR_HOST_GRAPH_ADDED':True,'new_positive_Cu_explicitly_declared_only_at_actual_rooted_plated_barrels':True,'no_current_barrel_plating_loop_reference_thermal_SI_or_native_FLASH_credit':True,'native_selected_refill_and_all_source_prior_keys_direct_refs':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R665_COMPLETE',sha(OUT/'receipt.json'),'accepted',len(accepted),flush=True)
if __name__=='__main__':main()
