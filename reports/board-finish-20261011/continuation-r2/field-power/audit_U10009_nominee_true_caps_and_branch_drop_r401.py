"""Independent exact caps/ordinary holes for the coupled lower VS nominee."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_U11025_new_true_caps_ordinary_holes_local_current_r348.py').read_text(encoding='utf-8')
s=s.replace("R=H/'U11025-joint-health-return-legal-face-construction-r344';O=H/'U11025-independent-full-caps-aperture-current-r348'","R=H/'U10009-retained-lower-VS-ordinary-barrel-coupled-nomination-r397';O=H/'U10009-nominee-independent-true-caps-ordinary-and-conditional-branch-r401';M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'")
old="_,h,_,_,_=pickle.loads((R/'model.pkl').read_bytes());d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());"
new="""g,h,b,q,actual=pickle.loads(M.read_bytes());assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';d=pickle.loads((R/'only-coupled-ordinary-and-inner-plane-nominee.pkl').read_bytes());h={**h,'tracks':[t for t in h['tracks']if t['uuid']not in d['removed']]+d['tracks'],'vias':h['vias']+d['vias']};"""
assert s.count(old)==1;s=s.replace(old,new)
start=s.index(" length=sum(");end=s.index(" errors=[q for q in checks",start)
replace="""
 plane=d['planes'][0];ps=plane['shape'];layer=plane['layer']
 for i in trees[layer].query(ps.buffer(.627),predicate='intersects'):
  row=rec[layer][int(i)]
  if row['net']==plane['net']:continue
  gap=ps.distance(row['shape']);req=max(G.gap(h,plane['net'],row['net']),plane.get('clearance_mm',.15))+.025
  if row['kind']=='track'and not tm[row['uuid']].get('m'):ot=tm[row['uuid']];gap=ps.distance(LineString([ot['a'],ot['b']]))-ot['w']/2
  elif row['kind']=='via':ov=vm[row['uuid']];gap=ps.distance(Point(ov['x'],ov['y']))-ov['d']/2
  checks.append({'new_UUID':plane['uuid'],'foreign_UUID':row['uuid'],'kind':'new_inner_plane_true_'+row['kind'],'layer':layer,'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
 length=sum(LineString([t['a'],t['b']]).length for t in d['tracks']if t['net']==v['net']);rho=1.724e-8*(1+.00393*(125-20));track_R=rho*(length*.001)/(.3e-3*25e-6);barrel_area=math.pi*((.15e-3+20e-6)**2-(.15e-3)**2);barrel_R=rho*1.6e-3/barrel_area
 # This is an intentionally explicit worst eligible lower-VS current
 # reservation, not an assumption of equal sharing among eight VS pins.
 current=2.008
 local={'scope':'U10009_lower_four_VS_and_C10017_conditional_only','all_four_output_limits_A':.5,'eligible_lower_VS_reservation_A':current,'reservation_derivation':'2 A outputs plus3 mA IQ planning and5 mA cap feed margin; final exact57term allocation still required','no_equal_VS_sharing':True,'new_B_protected_length_mm':length,'new_B_width_mm':.3,'new_barrel_drill_mm':.3,'screen_outer_Cu_um':25,'screen_barrel_plating_um':20,'screen_whole_barrel_length_mm':1.6,'screen_Cu_temperature_C':125,'rho_ohm_m':rho,'B_track_R_ohm':track_R,'new_whole_barrel_R_ohm':barrel_R,'conditional_B_track_plus_barrel_drop_V':current*(track_R+barrel_R),'conditional_B_track_plus_barrel_loss_W':current**2*(track_R+barrel_R),'inner_sheet_source_old_barrel_package_spreading_actual_temperature_and_transient_drop_NOT_INCLUDED':True,'barrel_and_sheet_temperature_rise_and_guaranteed_physical_rating':'OPEN; resistance is not a thermal capacity proof','native_source_and_all_eight_VS_retention':'OPEN'}
"""
s=s[:start]+replace+s[end:]
s=s.replace("'R344_receipt_SHA256'","'R397_receipt_SHA256'").replace("'R344_model_SHA256':sha(R/'model.pkl')","'parent_R155_model_SHA256':sha(M),'nominee_packet_SHA256':sha(R/'only-coupled-ordinary-and-inner-plane-nominee.pkl')")
s=s.replace('INDEPENDENT_NEW_CU_AND_ORDINARY_APERTURE_PASS_CONDITIONAL_LOCAL_CURRENT_SCREEN_NATIVE_OPEN','INDEPENDENT_U10009_NOMINEE_DISCRETE_PLANE_AND_ORDINARY_GUARD_PASS_FULL_CAPACITY_SOURCE_NATIVE_OPEN').replace('INDEPENDENT_NEW_U11025_CU_APERTURE_REJECTED','INDEPENDENT_U10009_NOMINEE_TRUE_GUARD_REJECTED')
s=s.replace("'local_conditional_drop_V':local['conditional_local_track_plus_full_barrel_drop_V']","'conditional_partial_drop_V':local['conditional_B_track_plus_barrel_drop_V']")
exec(compile(s,str(H/'audit_U11025_new_true_caps_ordinary_holes_local_current_r348.py'),'exec'))
