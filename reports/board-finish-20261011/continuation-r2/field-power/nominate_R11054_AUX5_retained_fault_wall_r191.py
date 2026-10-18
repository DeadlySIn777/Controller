"""Two-track AUX5 power detour candidates preserve exact FAULT pin2 contact."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'nominate_R14065_retained_shutdown_CAN_wall_r181.py').read_text(encoding='utf-8')
s=s.replace('R14065','R11054').replace('shutdown','fault').replace('CAN','AUX5').replace('r181','r191').replace('R181','R191')
s=s.replace('B.Cu','F.Cu').replace("courtyard']['B']","courtyard']['F']").replace(".get('B',[])",".get('F',[])")
s=s.replace("uid='e97700e6-80b1-4c0e-a1ed-1be39dede491';wall=next(t for t in h['tracks'] if t['uuid']==uid);assert wall['net']=='/motherboard_comms/AUX5_RXD'", "uid='b81b7cf8-f4fa-48b7-ac89-e03f782cac0a';wall=next(t for t in h['tracks'] if t['uuid']==uid);other=next(t for t in h['tracks'] if t['uuid']=='b16daa8b-7cb9-40bd-b78f-bcd0efb732a0');assert wall['net']==other['net']=='/motherboard_motors{slash}AUX_5V_B';assert wall['b']==other['a']")
s=s.replace("h2['tracks']=[t for t in h2['tracks'] if t['uuid']!=uid]","h2['tracks']=[t for t in h2['tracks'] if t['uuid'] not in {uid,other['uuid']}]")
s=s.replace('oldbody=C.body(wall);outside=[]','oldbody=unary_union([C.body(wall),C.body(other)]);outside=[]')
s=s.replace("F.graph(c,'/LOGIC_GND')","F.graph(c,'/motherboard_motors/FIELD_GND')").replace("==('J11001','2')","==('J11003','2')").replace("q['layer']=='In4.Cu'","q['layer']=='In1.Cu'")
s=s.replace('for offset in (0.,.2,.4,.6,.8,1.):','for offset in (0.,.2,.4,.6,.8,1.,1.2,1.4):')
s=s.replace("pts=[wall['a'],[round(wall['b'][0]+offset,6),wall['a'][1]],[round(wall['b'][0]+offset,6),wall['b'][1]],wall['b']]","pts=[wall['a'],[round(221.8+offset,6),wall['a'][1]],[round(221.8+offset,6),44.7],[other['b'][0],44.7],other['b']]")
s=s.replace("if not checks and not lost and not courtyards and miss<1e-9:","if not checks and not lost and not courtyards:")
s=s.replace("'exact_old_AUX5_track':wall","'exact_old_AUX5_tracks':[wall,other],'new_power_reference_area_is_diagnostic_DC_loop_full_current_gate_remains_OPEN':True")
s=s.replace('new_AUX5_uncovered_actual_J1_In4_reference_mm2','new_AUX5_uncovered_actual_J3_In1_reference_mm2')
exec(compile(s,str(H/'nominate_R14065_retained_shutdown_CAN_wall_r181.py'),'exec'))
