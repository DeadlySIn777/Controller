"""Source-network In1/In4 IO3 DC plane, no invented routed-body MAP gate.

The exact existing schema authorizes these supply layers. Actual old source,
direct contacts, absolute retained reference and every hard peer still gate
the sparse nomination. Full signed return/current loop remains OPEN.
"""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_FIELD5_IO3_normal_native_fill_source_bridge_r296.py').read_text()
needle="exec(compile(base,str(__file__),'exec'))"
transform=r'''
base=base.replace('FIELD5-R393-IO3-no-hole-normal-native-fill-source-bridge-r296','FIELD5-R393-IO3-In1-In4-existing-annulus-DC-plane-r298')
base=base.replace("('In2.Cu','In3.Cu','F.Cu','B.Cu')", "('In1.Cu','In4.Cu')")
base=base.replace("localref=refs[layer].intersection(clip.buffer(1));f=rawfree.intersection(localref.buffer(-width/2-.000004,quad_segs=128));faces=[]", "f=rawfree;faces=[]")
base=base.replace("missing=actual.difference(refs[layer]);row['fresh_drilled_actual_fullbody_ref_gap_mm2']=missing.area\n     if not missing.is_empty:continue", "row['DC_In1_In4_new_plane_routed_MAP_predicate']='NOT_DEFINED_NOT_ASSERTED';row['whole_signed_current_return_loop']='OPEN'\n     if actual.intersection(a).area<=0 or actual.intersection(bb).area<=0:continue")
# Produce only a positive plane and its immutable primitive construction
# recipe. These virtual segments are never added to the discrete model.
base=base.replace("trial={**c,'tracks':c['tracks']+nt,'zones':zones}", "axisbody=unary_union([buf(LineString([t['a'],t['b']]),t['w']/2)for t in nt]);ownholes=unary_union([sh for u,n,sh in holes if sh.intersects(axisbody)]);physical=axisbody.difference(ownholes);zid=str(uuid.uuid5(uuid.NAMESPACE_URL,'FIELD5-IO3-R298-DC:'+nt[0]['layer']+':'+str(nt[0]['w'])));newplane={'uuid':zid,'net':NET,'layer':nt[0]['layer'],'layers':[nt[0]['layer']],'fills':{nt[0]['layer']:IM.records(physical)},'clearance_mm':.15,'prospective_not_native':True};trial={**c,'zones':zones+[newplane]}")
base=base.replace("'fullbody_drill_subtracted_fill_reference_gap_empty':True", "'DC_In1_In4_new_plane_routed_MAP_predicate':'NOT_DEFINED_NOT_ASSERTED','local_and_whole_signed_return_current_thermal_loop':'OPEN'")
base=base.replace("'tracks':nt,'vias':[],'removed_original_UUIDs':[]", "'construction_recipe_tracks_only':nt,'vias':[],'removed_original_UUIDs':[]")
base=base.replace("if winner:(O/'only-new-IO3-tracks-no-holes-no-deletes.pkl').write_bytes(pickle.dumps({k:winner[k]for k in('tracks','vias','removed_original_UUIDs')},protocol=5))", "if winner:\n  virtual=winner['construction_recipe_tracks_only'];intended=unary_union([buf(LineString([t['a'],t['b']]),t['w']/2)for t in virtual]);physical=intended.difference(unary_union([sh for u,n,sh in holes if sh.intersects(intended)]));zid=str(uuid.uuid5(uuid.NAMESPACE_URL,'FIELD5-IO3-R298-DC:'+winner['layer']+':'+str(winner['width_mm'])));positive={'uuid':zid,'net':NET,'layer':winner['layer'],'shape':physical,'zone_outline_shape':intended,'clearance_mm':.15,'core_width_mm':winner['width_mm'],'priority':124,'physical_Cu_drill_subtracted':True};(O/'only-new-positive-IO3-DC-plane-no-hole.pkl').write_bytes(pickle.dumps([positive],protocol=5));(O/'only-immutable-virtual-plane-construction-recipe.pkl').write_bytes(pickle.dumps({'construction_recipe_tracks_only':virtual,'vias':[],'removed_original_UUIDs':[]},protocol=5));winner['positive_plane_UUID']=zid;winner['positive_physical_WKB_sha256']=digest(physical);winner['positive_intended_WKB_sha256']=digest(intended);winner['positive_physical_literal_subset_intended']=physical.difference(intended).is_empty;winner['actual_source_port_overlap_mm2']=physical.intersection(bb).area;winner['actual_detached_port_overlap_mm2']=physical.intersection(a).area")
base=base.replace("sha(O/'only-new-IO3-tracks-no-holes-no-deletes.pkl')if winner else None", "sha(O/'only-new-positive-IO3-DC-plane-no-hole.pkl')if winner else None")
base=base.replace("'NO_HOLE_EXISTING_SOURCE_IO3_BRIDGE_NOMINATION_PENDING_INDEPENDENT_FULL_CURRENT_AUDIT'", "'NO_HOLE_EXISTING_SOURCE_IO3_IN1_IN4_DC_PLANE_NOMINATION_PENDING_INDEPENDENT_FULL_CURRENT_AUDIT'")
base=base.replace("'NO_NORMAL_NATIVE_FILL_NO_HOLE_STRICT_REFERENCE_IO3_BRIDGE_IN_DECLARED_WINDOWS'", "'NO_NO_HOLE_IN1_IN4_DC_IO3_PLANE_RETAINING_ALL_OLD_CONTACT_SOURCE_REFERENCES_IN_DECLARED_WINDOWS'")
base=base.replace('R296','R298')
'''
assert s.count(needle)==1
s=s.replace(needle,transform+'\n'+needle)
exec(compile(s,str(__file__),'exec'))
