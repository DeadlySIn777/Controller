"""Read-only exact normal-source-hole witness; no route or mask is applied."""
from pathlib import Path
import sys,json,pickle,hashlib,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from shapely.geometry import Point
from shapely.ops import unary_union
OUT=H/'AO1-CS-physical-SG-patch-normal-COM-native-hole-retained-SCLK-source-witness-r698';COM='/motherboard_analog_output/AO1_COM'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def vertices(s):
 if s.geom_type=='Polygon':return list(s.exterior.coords)
 return[x for g in getattr(s,'geoms',[])for x in vertices(g)]
def main():
 assert not OUT.exists();OUT.mkdir();rp=H/'AO1-only-old-COM-barrel-own-B-stub-exact-profile-controlled-detour-actual-annular-source-return-r696/receipt.json';assert sha(rp)=='d55f45be7073a57a3f281f89b20724ebb36eae1280c2baa0c1ae51fa96040ddc';cp=rp.parent/'bounded-source-COM-SG-stub-axis-regions.pkl';data=pickle.loads(cp.read_bytes());sg=data['SGsites'];mp=H/'AO1-R656-seven-GROUND-additions-joint-R20-independent-source-geometry-r658/R20-plus-only-seven-ground-tracks-prospective-source-audit-context.pkl';assert sha(mp)=='94ea2f68b967fac5c78a8085291b1f46de54b2f5b29a33de12253fe8119f7c23';h=pickle.loads(mp.read_bytes());gp=mp.parent/'actual-before-R20-and-prospective-ground-added-COM-groups.pkl';assert sha(gp)=='d26f50bfa4047a6e29e572eb3daf3a7fdf72c323ee3adeabeb9567198c53c3f9';root=K.root(pickle.loads(gp.read_bytes())['after'],'U14619','7');ref=K.source_refs(root)['F.Cu'];pad=next(p for p in h['pads']if p['uuid']=='9e930fee-0c61-4e83-afa1-6c4c050a9696');body=unary_union(K.L.poly(pad['layers']['F.Cu']));oldSupported=body.intersection(ref);w=Point(376.23,127.59);assert body.contains(w)and ref.contains(w),'bound source witness not inside both material sets';maxdist=max(w.distance(Point(xy))for xy in vertices(sg));minNormal=0.5;covering=[]
 for z in h['zones']:
  if K.L.norm(z['net'])!=COM:continue
  if any(sh.covers(w)for sh in K.L.poly(z['fills'].get('In1.Cu',[]))):covering.append({'native_zone_UUID':z['uuid'],'native_zone_local_clearance_mm':float(z['clearance_mm']),'nominal_NEW_SIGNAL_via_r_plus_native_zone_clearance_mm':.25+float(z['clearance_mm'])})
 assert covering;minNormal=min(r['nominal_NEW_SIGNAL_via_r_plus_native_zone_clearance_mm']for r in covering);ret=data['RETsource'];ring=Point(sg.representative_point()).buffer(.999,quad_segs=128).difference(Point(sg.representative_point()).buffer(.901,quad_segs=128));pair=ret.intersection(ring)
 r={'verdict':'EVERY_BOUNDED_LEGAL_CS_SIGNAL_SITE_NORMAL_NATIVE_HOLE_ERASES_RETAINED_OLD_SCLK_SOURCE_WITNESS'if maxdist<minNormal-.005 else'NORMAL_SOURCE_WITNESS_NOT_UNIVERSALLY_ERASED','input_SHA256':{str(p.resolve()):sha(p)for p in(rp,cp,mp,gp)},'bounded_SG_region_area_mm2':sg.area,'bounded_SG_region_bounds_mm':list(sg.bounds),'retained_foreign_pad':{'UUID':pad['uuid'],'ref':pad['ref'],'pin':str(pad['num']),'net':pad['net'],'signal_layer':'F.Cu','mapped_real_SOURCE_plane':'In1.Cu'},'actual_old_pad_body_and_SOURCE_strict_interior_witness_mm':[w.x,w.y],'farthest_any_legal_bounded_SG_point_from_witness_mm':maxdist,'covering_actual_same_COM_zone_native_profiles':covering,'smallest_nominal_native_new_SIGNAL_hole_radius_mm':minNormal,'native_inside_5um_reserved_witness_margin_mm':minNormal-.005-maxdist,'unrelated_old_SOURCE_witness_cannot_use_NEW_CS_cap':True,'same_COM_moved_GROUND_barrel_uses_no_SIGNAL_antipad':True,'representative_SG_actual_annular_ordinary_return_ring_intersection_area_mm2':pair.area,'changed_native_geometry_or_filled_arrays':0,'native_jobs':0,'adopted':False,'controlled_SCLK_body_mask_or_profile_exception':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('R698_COMPLETE',sha(OUT/'receipt.json'),r['verdict'],'maxdist',maxdist,'normal',minNormal,'returnringarea',pair.area,flush=True)
if __name__=='__main__':main()
