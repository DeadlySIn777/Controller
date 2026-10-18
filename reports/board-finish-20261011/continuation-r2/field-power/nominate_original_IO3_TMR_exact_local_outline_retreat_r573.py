"""Declared negative-only original outline repair; no cached Cu or rule edit."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,re,copy,time
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import contact_layout as L
import ordinary_routes as O
from verify_source import P as SP
from inventory import sha
OUT=H/'original-IO3-TMR-exact-local-two-notch-negative-outline-nominee-r573'
BASE=H/'original-IO3-native-TMR-boundary-outline-cache-fill-provenance-r565'
N=ROOT/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218'
UID='54921f4b-0308-4821-9549-ff9360bf05ca'
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return dict(empty=s.is_empty,type=s.geom_type,area_mm2=s.area,length_mm=s.length,bounds_mm=None if s.is_empty else list(s.bounds),WKB_SHA256=hashlib.sha256(s.wkb).hexdigest())
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic();assert sha(BASE/'receipt.json')=='01f7cfd6331055e4a78fb7f61965d699bd3c313e40bbd0dcfa09ee2a2808ff11'
 oldchunk=(BASE/'R218_selected_input-original-zone.chunk').read_bytes();assert hashlib.sha256(oldchunk).hexdigest()=='11aab152bdc7623a733ed7afa5cd7bbbbbd6c7310a9774907968b7b6a92041d3'
 oldrings=json.loads((BASE/'exact-original-native-outline-area-source-controls.json').read_bytes())['raw_outline_integer_rings']['R218_selected_input'];rings=copy.deepcopy(oldrings)
 old=[ [323998000,130301999],[323998000,130350000],[339800000,130350000] ];inds=[i for i in range(len(rings[0])-2)if rings[0][i:i+3]==old];assert inds==[3160];idx=inds[0]
 # Keep every pre-existing edge/vertex except this explicitly declared
 # two-notch notch. Both new vertices are exact native integer points;
 # no global quantization, GEOS union or remote construction is used.
 new=[[323972900,130375100],[339800000,130375100]];rings[0][idx:idx+3]=new
 upper_old=[[334400000,123679066],[325246423,119253576]];upper_new=[[334400000,123651178],[325265219,119234781]];assert rings[0][3013:3015]==upper_old;rings[0][3013:3015]=upper_new
 oldshape=Polygon([(x/1e6,y/1e6)for x,y in oldrings[0]],[[(x/1e6,y/1e6)for x,y in rr]for rr in oldrings[1:]])
 newshape=Polygon([(x/1e6,y/1e6)for x,y in rings[0]],[[(x/1e6,y/1e6)for x,y in rr]for rr in rings[1:]])
 assert oldshape.is_valid and newshape.is_valid;gain=newshape.difference(oldshape);loss=oldshape.difference(newshape);assert gain.is_empty and not loss.is_empty
 area=Polygon([(348.198,130.35),(323.998,130.35),(323.998,118.65)]);hit=newshape.intersection(area);assert hit.is_empty;gap=newshape.distance(area);assert gap>=.025
 locality=Polygon([(323.5,130.8),(323.998,130.301999),(323.998,130.35),(339.8,130.35),(339.8,130.3751),(323.9729,130.3751)])
 upper_local=Polygon([(x/1e6,y/1e6)for x,y in upper_old+upper_new+[[334400000,122500000],[325400000,119100000]]]).convex_hull;locality=unary_union([locality,upper_local]);assert locality.is_valid;outside=loss.difference(locality);assert outside.is_empty
 oldtext=oldchunk.decode();pattern=r'(?P<indent>[ \t]+)\(xy 323\.998 130\.301999\)\s+\(xy 323\.998 130\.35\)\s+\(xy 339\.8 130\.35\)'
 matches=list(re.finditer(pattern,oldtext));assert len(matches)==1;mat=matches[0];nl='\r\n'if '\r\n'in oldtext else'\n';indent=mat.group('indent');replacement=indent+'(xy 323.9729 130.3751)'+nl+indent+'(xy 339.8 130.3751)'
 newtext=oldtext[:mat.start()]+replacement+oldtext[mat.end():];upperpattern=r'(?P<indent>[ \t]+)\(xy 334\.4 123\.679066\)\s+\(xy 325\.246423 119\.253576\)';um=list(re.finditer(upperpattern,newtext));assert len(um)==1;um=um[0];ui=um.group('indent');ur=ui+'(xy 334.4 123.651178)'+nl+ui+'(xy 325.265219 119.234781)';newchunk=(newtext[:um.start()]+ur+newtext[um.end():]).encode();olda=SP['sexpr_parse'](oldtext);newa=SP['sexpr_parse'](newchunk.decode());oldpolys=SP['children'](olda,'polygon');newpolys=SP['children'](newa,'polygon');assert len(oldpolys)==len(newpolys)==55
 assert oldpolys[1:]==newpolys[1:];assert [x for x in olda if not(isinstance(x,list)and x[0]=='polygon')]==[x for x in newa if not(isinstance(x,list)and x[0]=='polygon')]
 oldpts=SP['child'](oldpolys[0],'pts');newpts=SP['child'](newpolys[0],'pts');assert oldpts[1:3014]==newpts[1:3014]and oldpts[3016:1+idx]==newpts[3016:1+idx]and oldpts[1+idx+3:]==newpts[1+idx+2:]
 data=json.loads((N/'scoped-fill/geometry.json').read_bytes());z=next(x for x in data['zones']if x['uuid']==UID);nativeoutline=unary_union(L.poly(O.polys(z['outline'])));assert nativeoutline.normalize().wkb==oldshape.normalize().wkb
 actual=unary_union(L.poly(O.polys(z['fills']['In2.Cu'])));prospective_removed=actual.intersection(loss)
 groups=pickle.loads((H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r563/fresh-native-selected-all-drilled-groups.pkl').read_bytes())['/IO_3V3'];metal=[]
 for xs in groups:
  for r in xs:
   if r['layer']=='In2.Cu'and r['kind']!='fill':
    overlap=r['shape'].intersection(prospective_removed)
    if not overlap.is_empty:metal.append({'kind':r['kind'],'UUID':r['uuid'],'layer':r['layer'],'intersection':ds(overlap)})
 for name,s in [('before-original-outline',oldshape),('after-local-negative-outline',newshape),('exact-declared-local-boundary-redesign-mask',locality),('actual-outline-negative-removal',loss),('new-gain-control-empty',gain),('outside-declared-local-mask-control-empty',outside),('R218-actual-filled-Cu-intersect-proposed-outline-loss',prospective_removed)]: (OUT/(name+'.wkb')).write_bytes(s.wkb)
 (OUT/'exact-original-zone-before.chunk').write_bytes(oldchunk);(OUT/'exact-original-zone-after-outline-only.chunk').write_bytes(newchunk)
 packet={'original_zone_UUID':UID,'layer':'In2.Cu','raw_net':'/IO_3V3','before_original_native_zone_chunk_SHA256':hashlib.sha256(oldchunk).hexdigest(),'after_original_native_zone_chunk_SHA256':hashlib.sha256(newchunk).hexdigest(),'before_full_original_zone_chunk':oldchunk,'after_full_outline_only_original_zone_chunk':newchunk,'before_integer_polygon_rings':oldrings,'after_integer_polygon_rings':rings,'all_other_AST_nodes_including_any_original_cache_exact':True,'old_vertex_start_index':idx,'declared_old_vertices_IU':old,'declared_new_vertices_IU':new,'second_declared_old_vertices_IU':upper_old,'second_declared_new_vertices_IU':upper_new,'local_negative_redesign_mask':locality,'before_outline_shape':oldshape,'after_outline_shape':newshape,'physical_fill_operation':'NONE: native fresh fill required; this packet only replaces original native outline pts','all_rules_settings_source_FP_discrete_original_other_zones':'UNCHANGED','R218_candidate_SHA256':'6befbca6dcac6bfe812dc8be04069701338f8ef95159faf9a5cb4a114395d55e'}
 (OUT/'only-one-original-IO3-zone-outline-negative-replacement.pkl').write_bytes(pickle.dumps(packet,protocol=5))
 put(OUT/'native-physical-metal-near-proposed-negative-strip.json',metal)
 put(OUT/'receipt.json',{'status':'EXPLICIT_ORIGINAL_NATIVE_OUTLINE_NEGATIVE_REPAIR_NOMINATION_FULL_NATIVE_SOURCE_REFILL_CONTACT_CURRENT_OPEN','input_R565_SHA256':sha(BASE/'receipt.json'),'packet_SHA256':sha(OUT/'only-one-original-IO3-zone-outline-negative-replacement.pkl'),'original_zone_UUID':UID,'original_and_after_chunk_SHA256':[hashlib.sha256(oldchunk).hexdigest(),hashlib.sha256(newchunk).hexdigest()],'before_raw_outline_vertices':sum(map(len,oldrings)),'after_raw_outline_vertices':sum(map(len,rings)),'all_old_outer_vertices_exact_except_only_indices3013_3014_3160_3161_3162':True,'all_54_original_hole_ring_AST_bytes_and_all_other_zone_AST_nodes_exact':True,'changed_original_vertices_IU':old,'new_original_vertices_IU':new,'second_changed_original_vertices_IU':upper_old,'second_new_original_vertices_IU':upper_new,'strict_literal_zero_grid_gained_outline':ds(gain),'strict_removed_outside_exact_declared_local_mask':ds(outside),'exact_negative_outline_removal':ds(loss),'actual_native_TMR_closed_set_after_outline_hit':ds(hit),'actual_native_TMR_after_outline_distance_mm':gap,'declared_planner_margin_mm':.025,'construction_axis_reserve_mm':.0001,'R218_fresh_actual_fill_in_proposed_negative_strip':ds(prospective_removed),'In2_physical_metal_intersections_with_proposed_removed_current_fill':metal,'actual_R218_605direct_contact_and_sourcegroup_after_fresh_NATIVE_FILL':'OPEN','no_manual_original_cachedfill_edit':True,'no_board_native_or_project_written':True,'native_jobs':0,'old_raw_R563_closed_boundary_FAIL_preserved':True,'unmodified_R157_measurement_bound_inherited_FAILs':True,'full_signed_sheet_barrel_loop_thermal_capacity':'OPEN','adopted':False,'elapsed_seconds':time.monotonic()-st})
 print('R569',sha(OUT/'receipt.json'),'outline loss',loss.area,'actual Cu strip',prospective_removed.area,'metal overlaps',len(metal),flush=True)
if __name__=='__main__':main()
