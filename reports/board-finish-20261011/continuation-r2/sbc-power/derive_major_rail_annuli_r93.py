"""Freeze an explicit derivative of root's guarded regional annulus router."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent.parent
source=H/'repair_protected_field_returns_r4.py'
s=source.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
replace("OUT=H/'protected-field-return-restoration-r4';LAYERS=('In4.Cu','In2.Cu','In3.Cu','In1.Cu')", "OUT=H/'sbc-power/major-rail-existing-annulus-feeds-r93';LAYERS=('In4.Cu','In2.Cu','In3.Cu','In1.Cu')")
replace("mp=Path(sys.argv[1]).resolve();pins={'48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff':'5ab7626ced2d869dca30bbeba34687942c6c713ec3f4edda6f762b26b91fa09b'}\n mr=mp.with_name('receipt.json');assert sha(mp) in pins and sha(mr)==pins[sha(mp)]", "mp=Path(sys.argv[1]).resolve();mr=mp.with_name('receipt.json');pinned=json.loads(mr.read_text());assert sha(mp)==pinned['model_sha256'];assert pinned['parent_model_sha256']=='128a21a83ccc8e1029f4b97e27930f82de743e00ef45fb1fc2041f0967b8a821';assert pinned['removed_new_components']==11")
replace("rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)", """fieldbase=H/'field-power/regulated-final-power-search-base-r70';fp=fieldbase/'model.pkl';assert sha(fp)=='1368cee2cc2e18bc670a2875f31c4148b6d8792bbc67e89e65289107d923b73d'
 fold,fh,fb,fz,fc=pickle.loads(fp.read_bytes());ids={kind:{q['uuid'] for q in h[kind]} for kind in ('vias','tracks')}
 hard_ds={kind:[q for q in fh[kind] if q['uuid'] not in ids[kind]] for kind in ('vias','tracks')}
 regz=pickle.loads((fieldbase/'proposed-zones.pkl').read_bytes());assert sha(fieldbase/'proposed-zones.pkl')=='54c5d76895736c683210179965fc97d07038ca3436c863215f28eb49169d864f'
 rootp=H/'protected-field-return-r4-snapshot-4/proposed-zones.pkl';assert sha(rootp)=='213182e7ec8439cccb0087bf99b362e6e149a3f21843d103b7b50ddceb428239'
 hard_zones=regz+pickle.loads(rootp.read_bytes())
 hard_h={**h,'vias':h['vias']+hard_ds['vias'],'tracks':h['tracks']+hard_ds['tracks']}
 binding['major_rail_hard_only_later_foreign_proposals']={'field_R70_model_sha256':sha(fp),'root_snapshot4_sha256':sha(rootp),'hard_vias':len(hard_ds['vias']),'hard_tracks':len(hard_ds['tracks']),'hard_zone_count':len(hard_zones),'no_source_contact_credit_from_hard_only_objects':True}
 rec,trees=F.build({**hard_h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)""")
replace("all_holes += [(v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64)) for v in h['vias']]", "all_holes += [(v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64)) for v in hard_h['vias']]")
replace("for net,ref in [('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:", "for net,ref in [('/CORE_1V2','L2001'),('/IO_3V3','R18001')]:")
replace("for q in zones+adds:", "for q in zones+adds+hard_zones:")
replace("for width in (1.,.5,.35,.25):", "for width in (1.25,1.,.8,.5,.35,.25,.20):")
replace("controller-protected-ground-r4/", "controller-major-rail-existing-annuli-r93/")
replace("'label':'Protected supply return restoration R4'", "'label':'Major rail existing-annulus feed R93'")
replace("zz,guard=N.normalize_owned_via_guards(h,[z]);z=zz[0]", """zz,guard=N.normalize_owned_via_guards(hard_h,[z]);z=zz[0]
     import owned_analytic_track_guards_r75 as AT
     zz,track_guard,_=AT.normalize_owned_track_guards(hard_h,[z]);z=zz[0]
     # Pad shapes are exact native rectangles/ovals from the pinned geometry;
     # the same outward buffer closes the complete planning guard.
     pad_cuts=[]
     for pi in trees[layer].query(z['shape'].buffer(1.5),predicate='intersects'):
      pp=rec[layer][int(pi)]
      if pp['kind']=='pad' and pp['net']!=raw:pad_cuts.append(N.bounded_buffer(pp['shape'],gap(pp['net'])+.025))
     if pad_cuts:
      cutter=unary_union(pad_cuts);z['shape']=set_precision(z['shape'].difference(cutter),1e-6);z['zone_outline_shape']=set_precision(z['zone_outline_shape'].difference(cutter),1e-6)""")
replace("'outward_via_guards':guard", "'outward_via_guards':guard,'outward_track_guards':track_guard,'outward_pad_cutter_count':len(pad_cuts)")
replace("'new_holes':0,'old_Cu_deleted':0", "'full_fitted_CORE1V2_load_A':.8,'IO3_full_fitted_output_envelope_A':2.,'route_width_is_geometry_only_current_drop_thermal_open':True,'new_holes':0,'old_Cu_deleted':0")
replace("'EXISTING_ANNULUS_RETURN_RESTORATION_SOURCE_PROJECTION_MATCHED_MUTUAL_NATIVE_CURRENT_PENDING'", "'MAJOR_RAIL_EXISTING_ANNULUS_FEEDS_SOURCE_PROJECTION_MATCHED_MUTUAL_NATIVE_CURRENT_PENDING'")
replace("RETURN_R4_FROZEN", "MAJOR_RAIL_R93_FROZEN")
# The root file resolves H from its own directory. This derivative is below sbc-power.
replace("H=Path(__file__).resolve().parent;", "H=Path(__file__).resolve().parent.parent;")
out=H/'sbc-power/construct_major_rail_annuli_r93.py';assert not out.exists();out.write_text(s)
compile(s,str(out),'exec')
print('MAJOR_RAIL_ROUTER_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
