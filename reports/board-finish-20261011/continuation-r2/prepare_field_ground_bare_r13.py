"""Allow explicit old-fill retreat nominees while retaining all real blockers."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'nominate_field_ground_bare_dogbones_r8.py';o=H/'nominate_field_ground_bare_dogbones_r13.py';assert not o.exists()
s=p.read_text();a=s.index(" mp=H/'sbc-power/r17031");e=s.index(" raw=next",a)
s=s[:a]+''' mp=Path(sys.argv[2]).resolve();mr=mp.with_name('receipt.json');r=json.loads(mr.read_bytes());assert sha(mp)==r['model_sha256'] and r['actual_C_R102_R10_composed']
 assert r['R106_model_sha256']=='3f9086799fb85283714126d51b1e7cc8dc477ffe8a3ed0b1c06edd91071dcf39'
 old,h,b,zones,current=pickle.loads(mp.read_bytes());h=copy.deepcopy(h);out.mkdir()
''' +s[e:]
a=s.index('   # Explicit different-domain stored original fills');e=s.index('   region=set_precision',a)
s=s[:a]+'''   # Original filled polygons may retreat around prospective ordinary Cu.
   # No original native outline is edited. These are only nominations until
   # the full independent all-net reference/contact/source gates prove every
   # old obligation retained on the complete guarded projection.
''' +s[e:]
a="   startparts=[p for p in polys(routefree)if p.intersects(padshape.buffer(-.000020))];options=[]"
b=a+"\n   print('FAG_BARE_R13_FACE',pad['ref'],radius,'legal_site_area',region.area,'outer_start_parts',len(startparts),'source_distances',{l:point.distance(source[l])for l in('In1.Cu','In2.Cu','In3.Cu','In4.Cu')},flush=True)"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('controller-ground-bare-r7/','controller-ground-bare-r13/')
s=s.replace("'fixed_R78_plus_FAG_snapshot4_context_unqualified':True","'actual_corrected_R106_C_CORE91_ROOT4_R10_context_unqualified':True,'original_fill_retreat_nomination_requires_explicit_full_all_net_retained_contact_reference_source_gate':True")
s=s.replace('mp,mr,cp,Path(N.__file__)','mp,mr,Path(N.__file__)')
compile(s,str(o),'exec');o.write_text(s)
(H/'field-ground-bare-r13-derivation.json').write_text(json.dumps({'source_file':str(p),'source_sha256':sha(p),'derived_file':str(o),'derived_sha256':sha(o),'actual_corrected_coupled_source_context':True,'only_original_stored_fills_allowed_to_retreat_in_nomination':True,'all_actual_tracks_pads_vias_holes_SMD_native_areas_source_reservations_barriers_and_foreign_NEWplanes_hard':True,'ordinary_0p5_0p2_all6_0p2_stub_only':True,'no_original_native_outline_modified_or_existing_Cu_removed':'PRESERVED','full_mutual_retained_contacts_reference_current_native_gates':'OPEN','native_jobs':0,'board_written':False},indent=1)+'\n')
print(json.dumps({'script':str(o),'sha256':sha(o)}))
