"""Exact ordinary-site counterfactual for one native IO3 plane's new antipads."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=H/'diagnose_CORE_external_port_blockers_r92.py';s=p.read_text();changes=[]
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append({'old':a,'new':b})
replace("CORE-ordinary-external-fill-port-blocker-diagnosis-r92';assert", "CORE-native-IO3-antipad-external-port-nominees-r93';assert")
replace("  print('R92_BLOCKERS'", "  self.propose_IO3_antipad_ports(candidate,out,side)\n  print('R93_BLOCKERS'")
extra='''
 def propose_IO3_antipad_ports(self,candidate,out,side):
  allowed_UUID='54921f4b-0308-4821-9549-ff9360bf05ca'
  eligible=[r for r in self.rows if r['family']=='native_foreign_power_filled_Cu'and r.get('UUID')==allowed_UUID]
  assert eligible and all(r['raw_net']=='/IO_3V3'and r['layer']=='In2.Cu'for r in eligible)
  retained=[r['shape']for r in self.rows if r not in eligible]
  region=set_precision(candidate.difference(unary_union(retained)),1e-6)
  (out/(side+'-new-native-IO3-antipad-prospective-port-region.wkb')).write_bytes(region.wkb)
  proposals=[]
  for face in sorted(parts(region),key=lambda q:-q.area)[:6]:
   point=face.representative_point();xy=[round(point.x,6),round(point.y,6)]
   if not region.covers(Point(xy)):continue
   uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-CORE-native-IO3-antipad-r93/'+side+'/'+repr(xy)))
   proposals.append({'side':side,'via':{'uuid':uid,'net':'/CORE_1V2','x':xy[0],'y':xy[1],'d':.5,'drill':.2,'flashed':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],'prospective_not_native':True},'ordinary_site_face_area_mm2':face.area,'one_native_IO3_plane_exact_new_hole_and_annulus_antipad_required':allowed_UUID})
  (out/(side+'-prospective-new-ordinary-ports.pkl')).write_bytes(pickle.dumps(proposals,protocol=5))
  put(out/(side+'-antipad-site-proposal.json'),{'side':side,'prospective_new_ordinary_port_region_area_mm2':region.area,'proposals':proposals,'all_original_R90_guards_except_one_literal_IO3_native_filled_plane_remain_hard':True,'native_zone_original_outline_and_settings_unchanged':True,'required_new_antipad_predicate':'new CORE ordinary .5/.2 via, .15 same-domain Cu+.025 planning margin and >=.275 foreign-hole clearance; ALL old IO3 source/direct-layer-contact/shape/no-loss checks required','ordinary_native_flashes_all6': 'UNPROVEN','actual_CORE_In3_finite_annular_overlap':'REQUIRES_EXACT_MODEL_CHECK','all77_contacts_all_original_discrete_IO3_fill_contacts_full_2A_IO3_and_0_8A_CORE_current_return_drop_thermal_native_DRC':'OPEN','no_native_or_board_written':True,'adopted':False})
  print('R93_IO3_ANTIPAD_ORDINARY_PORT_NOMINEES',side,region.area,len(proposals),flush=True)
'''
replace('\ndef main():',extra+'\ndef main():')
replace("'verdict':'EXACT_R90_ORDINARY_SITE_BLOCKER_ATTRIBUTION_ONLY'", "'verdict':'LITERAL_NATIVE_IO3_NEW_ANTIPAD_ORDINARY_PORT_PROPOSALS_ONLY'")
replace("'R92_EXACT_BLOCKER_ATTRIBUTION_FROZEN'", "'R93_LITERAL_IO3_ANTIPAD_PORT_PROPOSALS_FROZEN'")
compile(s,'nominate_CORE_native_IO3_antipad_ports_r93.py','exec');out=H/'nominate_CORE_native_IO3_antipad_ports_r93.py';assert not out.exists();out.write_text(s)
(H/'CORE-native-IO3-antipad-port-nominees-r93-derivation.json').write_text(json.dumps({'prior_attribution_receipt_sha256':sha(H/'CORE-ordinary-external-fill-port-blocker-diagnosis-r92/receipt.json'),'base_script_sha256':sha(p),'derived_script_sha256':sha(out),'changes':changes,'ordinary_site_counterfactual_only':True,'prior_R90_full_guard_zero_region_WKB_must_still_equal':True,'only_literal_native_IO3_54921f4b_plane_antipad_proposed':True,'all_old_source_direct_filled_contact_and_current_native_checks_open':True},indent=1)+'\n')
print('R93_DERIVED',sha(out),flush=True)
