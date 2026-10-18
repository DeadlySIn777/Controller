"""Derive a source-filtered major-rail search without changing root evidence."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent.parent
source=H/'repair_fbg_lazy_existing_returns_r10.py'
s=source.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
replace("H=Path(__file__).resolve().parent;", "H=Path(__file__).resolve().parent.parent;")
replace("OUT=H/'fbg-lazy-existing-return-restoration-r10';", "OUT=H/'sbc-power/major-rail-lazy-existing-annulus-feeds-r108';")
start=s.index(" mp=Path(sys.argv[1]).resolve();")
end=s.index(" assert not OUT.exists();",start)
s=s[:start]+''' specfile=Path(sys.argv[1]).resolve();spec=json.loads(specfile.read_bytes())
 mp=Path(spec['model_file']).resolve();mr=Path(spec['receipt_file']).resolve()
 assert sha(mp)==spec['model_sha256'] and sha(mr)==spec['receipt_sha256']
 r=json.loads(mr.read_bytes());assert r['model_sha256']==sha(mp)
 assert spec['all_later_actual_model_geometry_is_hard'] is True
 assert spec['no_native_or_source_adoption'] is True
'''+s[end:]
replace(" # R69 already contains the full outward guarded projection, pinned above.", " # The exact frozen input supplies all actual later discrete and new-plane geometry.")
replace(" for net,ref in [('/motherboard_do/FIELD_B_0V','J11005')]:", " for net,ref in [('/CORE_1V2','L2001'),('/IO_3V3','R18001')]:")
replace("     v=via_by_id[vid];ann=", "     if source[layer].is_empty:continue\n     v=via_by_id[vid];ann=")
replace("     region=legal(layer,vid,radius)", "     print('MAJOR_RAIL_LAZY_LEGAL',net,vid,layer,radius,flush=True)\n     region=legal(layer,vid,radius)")
replace("     for width in (1.,.5,.35,.25):", "     for width in (1.25,1.,.8,.5,.35,.25,.20):")
replace("     print('FBG_LAZY_PATH',vid,layer,radius,width,get_num_coordinates(part),flush=True)", "     print('MAJOR_RAIL_LAZY_PATH',net,vid,layer,radius,width,get_num_coordinates(part),flush=True)")
replace("controller-fbg-existing-return-r10/", "controller-major-rail-lazy-existing-annuli-r108/")
replace("'label':'Field B existing-annulus return continuation R10'", "'label':'Major rail lazy existing-annulus feed R108'")
replace("     zz,guard=N.normalize_owned_via_guards(h,[z]);z=zz[0]", """     zz,guard=N.normalize_owned_via_guards(h,[z]);z=zz[0]
     import owned_analytic_track_guards_r75 as AT
     import owned_native_pad_guards_r98 as AP
     zz,track_guard,_=AT.normalize_owned_track_guards(h,[z]);z=zz[0]
     zz,pad_guard,_=AP.normalize_owned_pad_guards(h,[z]);z=zz[0]""")
replace("'outward_via_guards':guard", "'outward_via_guards':guard,'outward_track_guards':track_guard,'outward_pad_guards_with_explicit_20nm_construction_reserve':pad_guard")
replace("'EXISTING_ANNULUS_RETURN_RESTORATION_SOURCE_PROJECTION_MATCHED_MUTUAL_NATIVE_CURRENT_PENDING'", "'MAJOR_RAIL_LAZY_EXISTING_ANNULUS_FEEDS_SOURCE_PROJECTION_MATCHED_MUTUAL_EXACT_CONTACT_NATIVE_CURRENT_PENDING'")
replace("'new_holes':0,'old_Cu_deleted':0", "'input_binding_file':str(specfile),'input_binding_sha256':sha(specfile),'full_fitted_CORE1V2_load_A':.8,'IO3_full_fitted_output_envelope_A':2.,'geometry_width_does_not_grant_current_or_sharing':True,'fast_graph_2nm_intersection_tolerance_requires_independent_exact_integer_contact_gate':True,'new_holes':0,'old_Cu_deleted':0")
replace("print('FBG_RETURN_R10_FROZEN'", "print('MAJOR_RAIL_LAZY_R108_FROZEN'")
out=H/'sbc-power/construct_major_rail_lazy_annuli_r108.py';assert not out.exists();out.write_text(s)
compile(s,str(out),'exec')
print('MAJOR_RAIL_LAZY_ROUTER_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest(),'SOURCE',hashlib.sha256(source.read_bytes()).hexdigest())
