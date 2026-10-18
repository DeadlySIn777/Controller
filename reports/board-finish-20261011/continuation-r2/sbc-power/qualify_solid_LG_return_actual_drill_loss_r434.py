"""Keep raw R433 signal-cap failures; use actual solid LG drill operation."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-active-R300-CDONE-CM79-ground-r433.py').read_text(encoding='utf-8')
s=s.replace('CM79-active-R300-minimal-CDONE-one-new-ordinary-ground-return-r433','CM79-active-R300-minimal-CDONE-one-new-ordinary-ground-return-r434')
needle=' groundBad=[];groundOps=[];groundRawRefs=[]'
replacement=''' from bind_R300_all_native_intents_CM_context_r431 import fields
 inv=A.C.inventory(Path(packet['active_board']).read_bytes());solidProfiles=[]
 for zuid in ('58c55cd5-98e6-4467-88e3-146ceeee361a','c1d27fa1-452b-4e27-985d-5ad23644d800'):
  f=fields(inv[3][zuid]);cp=next(x for x in f if x.startswith('(connect_pads'));assert cp.startswith('(connect_pads yes');solidProfiles.append({'UUID':zuid,'exact_current_native_fields':[x for x in f if not x.startswith('(polygon')],'LOGIC_GND_via_connection':'FULL_SOLID','own_plane_prospective_subtraction':'actual .10 mm physical drill only; no foreign signal antipad or thermal gap authority'})
 put('exact-current-original-LG-solid-connection-profile-and-drill-authority.json',solidProfiles)
 groundBad=[];groundOps=[];groundRawRefs=[]'''
assert needle in s;s=s.replace(needle,replacement)
assert s.count('rp.buffer(.525,quad_segs=128)')==2
s=s.replace('rp.buffer(.525,quad_segs=128)','rp.buffer(.1,quad_segs=128)')
s=s.replace("'one_new_ground_return_deficit_count':len(groundBad)","'one_new_ground_return_deficit_count':len(groundBad),'new_LG_same_plane_physical_drill_radius_mm':.1,'R433_signal_style_525_cap_raw_reference_FAIL_preserved':True,'actual_current_original_LG_full_solid_profile_file':'exact-current-original-LG-solid-connection-profile-and-drill-authority.json'")
s=s.replace("'CM79-R433-","'CM79-R434-").replace("print('R433_COMPLETE'","print('R434_COMPLETE'")
E=P/'exact-expanded-active-R300-solid-LG-drill-CM79-ground-r434.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
