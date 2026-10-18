"""Prepare a nearest-port-first continuation on exact CORE91/C24/root4 context."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'repair_protected_field_returns_r4.py';out=H/'repair_fbg_lazy_existing_returns_r10.py';r=H/'fbg-lazy-existing-returns-r10-derivation.json'
assert not out.exists()and not r.exists();s=p.read_text()
start=s.index(" mp=Path(sys.argv[1]).resolve();pins=");end=s.index(" assert not OUT.exists();",start)
s=s[:start]+""" mp=Path(sys.argv[1]).resolve();mr=mp.with_name('receipt.json');r=json.loads(mr.read_bytes())
 assert sha(mp)==r['model_sha256'] and r['CORE_r91_explicit_option'] is True
 assert r['base_CORE_model_sha256']=='1bb0d52095c4f2ad003d0c5934d8e7fca7174c8936af19ae0bbed66021003e09'
 assert r['root_four_spines_sha256']=='213182e7ec8439cccb0087bf99b362e6e149a3f21843d103b7b50ddceb428239'
 assert r['exact_C_native_owned_ledger_sha256']=='017fb0ae11976a79059349bcc0364b8ce6cb0547b01ba542fb6a2a681bd76efb'
 assert r['C10036_pad_source_rooted'] and r['both_new_C_return_vias_source_rooted']
 assert r['U19008_delta_included'] is False and r['REG_delta_included'] is False
"""+s[end:]
s=s.replace("OUT=H/'protected-field-return-restoration-r4'","OUT=H/'fbg-lazy-existing-return-restoration-r10'")
needle="[('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]";assert s.count(needle)==1;s=s.replace(needle,"[('/motherboard_do/FIELD_B_0V','J11005')]")
s=s.replace('controller-protected-ground-r4/','controller-fbg-existing-return-r10/').replace('Protected supply return restoration R4','Field B existing-annulus return continuation R10').replace('RETURN_R4_FROZEN','FBG_RETURN_R10_FROZEN')
start=s.index("   for radius in (5.,15.,35.,75.,800.):");end=s.index("     width=-negative_width",start)
block="""   # Enumerate candidates lazily so the closest usable source port can be
   # routed before hundreds of unrelated legal faces are constructed.
   def choices_for_radius(radius):
    ranked=sorted(ports,key=lambda pair:(source[pair[1]].distance(Point(via_by_id[pair[0]]['x'],via_by_id[pair[0]]['y'])),pair[1],pair[0]))
    for vid,layer in ranked:
     v=via_by_id[vid];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=64).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
     if not box(v['x']-radius,v['y']-radius,v['x']+radius,v['y']+radius).intersects(source[layer]):continue
     region=legal(layer,vid,radius)
     if not region.intersects(ann) or not region.intersects(source[layer]):continue
     for width in (1.,.5,.35,.25):
      for part in polys(region.buffer(-width/2-.005)):
       if not part.intersects(ann) or not part.intersects(source[layer]):continue
       inner=part.buffer(-.00002);aa=inner.intersection(ann);bb=inner.intersection(source[layer])
       if aa.area>1e-8 and bb.area>1e-8:yield aa.distance(bb),-width,vid,layer,part,aa,bb,region,ann
   for radius in (5.,15.,35.,75.,800.):
    for distance,negative_width,vid,layer,part,aa,bb,region,ann in choices_for_radius(radius):
"""
s=s[:start]+block+s[end:]
s=s.replace('get_num_coordinates(part)>160000','get_num_coordinates(part)>5000').replace('part.buffer(-.015).simplify(.005,preserve_topology=True)','part.buffer(-.002).simplify(.0005,preserve_topology=True)')
s=s.replace("gap(q['net'])+.025","gap(q['net'])+.025+.000020").replace("float(q.get('clearance_mm',.15)))+.025)","float(q.get('clearance_mm',.15)))+.025+.000020)").replace('gap(craw)+.025)','gap(craw)+.025+.000020)').replace('N.bounded_buffer(s,.025)','N.bounded_buffer(s,.025+.000020)')
s=s.replace("     a,b=nearest_points(aa,bb);chord=LineString([a,b])","     print('FBG_LAZY_PATH',vid,layer,radius,width,get_num_coordinates(part),flush=True)\n     a,b=nearest_points(aa,bb);chord=LineString([a,b])")
compile(s,str(out),'exec');out.write_text(s)
r.write_text(json.dumps({'parent_constructor_sha256':sha(p),'derived_constructor_sha256':sha(out),'requires_exact_frozen_CORE91_C24_and_root4_context_without_U19008_or_REG_failed_nominees':True,'new_port_order':'lazy increasing actual same-layer source distance before legal-mask construction; same actual annulus/source containment predicates','complex_face_threshold_vertices':5000,'conservative_simplification':'erode2um/simplify0.5um/intersect exact original legal face, then actual rounded-width core containment and source projection gates','explicit_extra_legal_outward_mm':.000020,'all_prior_actual_source_contacts_retained_and_exact_source_only_fullbank_fill_equality_required':True,'finite_failure_is_not_proof_of_no_path':True,'new_Cu_or_holes':0,'original_zone_outlines_untouched':True,'all_mutual_analytic_margin_current_reference_native_refill_DRC':'OPEN','native_jobs':0},indent=1)+'\n');print(json.dumps({'script':str(out),'sha256':sha(out)}))
