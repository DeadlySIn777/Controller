"""Attribute empty SG sites to physical Cu versus reference coverage exactly."""
from pathlib import Path
import sys,json,pickle,hashlib,time
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point
from shapely.ops import unary_union
OUT=H/'AO1-CS-F-escape-physical-face-vs-SOURCE-qualified-face-exact-blockers-r684';NET='/motherboard_analog_output/AO1_DAC_CS_N';COM='/motherboard_analog_output/AO1_COM'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for x in getattr(s,'geoms',[])for p in parts(x)]
def info(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 rp=pin(H/'AO1-DAC-CS-real-rooted-ground-bridges-exact-b177-detour-paired-constructor-r676/receipt.json','bea5b9618a8573024723a229728303d75f3fafab9a2b414529ff861b90ae7631');cp=pin(rp.parent/'bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl');cache=pickle.loads(cp.read_bytes());mp=pin(H/'AO1-R656-seven-GROUND-additions-joint-R20-independent-source-geometry-r658/R20-plus-only-seven-ground-tracks-prospective-source-audit-context.pkl','94ea2f68b967fac5c78a8085291b1f46de54b2f5b29a33de12253fe8119f7c23');model=pickle.loads(mp.read_bytes());p=next(p for p in model['pads']if p['uuid']=='5bd36a6a-0ece-4d8a-bb54-e362786d2249');origin=Point(p['x'],p['y']);physical=unary_union([s for s in parts(cache['free'][NET,'F.Cu'])if s.covers(origin)]);qualified=unary_union([s for s in parts(cache['ff'])if s.covers(origin)]);physicalSG=physical.intersection(cache['via'][NET]);qualifiedSG=qualified.intersection(cache['via'][NET]);rec,trees=K.F.build({**model,'zones':[]});dom=model['domains_normalized'];rows=[]
 peerp=pin(H/'AO1-MON3-VREF-and-only-b177-5V-native-width-endpoint-source-detour-r19/MON3-VREF-plus-exact-b177-5V-controlled-detour-NOMINEE.pkl','d35097754a50017d6d4b17d4388dbced44c63547b39fbddbcda31b8a78cf4181');new=set(pickle.loads(peerp.read_bytes())['exact_new_chunks'])
 for i in trees['F.Cu'].query(physical.buffer(1),predicate='intersects'):
  r=rec['F.Cu'][int(i)];n=K.L.norm(r['net'])
  if n==NET:continue
  req=(.15 if dom[n]==dom[NET]else .6)+.025+.105;sh=r['shape'];gap=sh.distance(physical);mask=K.Z.bounded_buffer(sh,req);row={'UUID':r['uuid'],'kind':r['kind'],'net':r['net'],'ref':r.get('ref'),'pin':r.get('pin'),'exact_AO1_controlled_NEW_peer':r['uuid']in new,'shape_bounds_mm':list(sh.bounds),'distance_to_physical_face_mm':gap,'axis_guard_radius_mm':req,'blocker_mask_intersection_with_face_boundary_length_mm':mask.intersection(physical.boundary).length,'near_face_axis_guard':gap<=req+.000020};rows.append(row)
 r={'verdict':'EXACT_CS_PIN7_F_ESCAPE_ATTRIBUTION_NO_ROUTING_OR_CU_CHANGE','input_SHA256':pins,'source_pad':{'ref':p['ref'],'pin':str(p['num']),'UUID':p['uuid'],'at_mm':[p['x'],p['y']]},'physical_trace_axis_source_face':info(physical),'SOURCE_qualified_trace_axis_source_face':info(qualified),'legal_ordinary_SG_sites_on_physical_source_face':info(physicalSG),'legal_ordinary_SG_sites_on_qualified_source_face':info(qualifiedSG),'all_near_current_F_Cu_rows':rows,'physical_or_reference_attribution':'PHYSICAL_CONNECTED_FACE_HAS_NO_ORDINARY_VIA_SITE'if physicalSG.is_empty else'PHYSICAL_ESCAPE_HAS_SG_SITES_BUT_SOURCE_SHADOW_CONSTRAINS_THEM','native_SOURCE_after_closed_loop_SI':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n')
 for p,s in pins.items():assert sha(p)==s,p
 print('R684_COMPLETE',sha(OUT/'receipt.json'),r['physical_or_reference_attribution'],'physical',physical.area,'qualified',qualified.area,'near',[(r['UUID'][:8],r['net'])for r in rows if r['near_face_axis_guard']],flush=True)
if __name__=='__main__':main()
