from pathlib import Path
H=Path(__file__).resolve().parent;dst=H/'freeze_CM_pin79_wall_source_scope_r324.py';assert not dst.exists();s=(H/'freeze_CM_wall_source_obligations_r314.py').read_text()
start=s.index("prefixes=['57aa8602'");end=s.index("out=H/",start)
s=s[:start]+"selected=[];target=K.Point(117.452,201.175)\nfor t in current['tracks']:\n if t['layer']!='F.Cu'or K.L.norm(t['net'])=='/LOGIC_GND'or t['uuid']=='b7dc346a-8a46-4b4c-ae3d-c5990ddefc96':continue\n a,bb=t['a'],t['b'];pad=t['w']/2+1.5\n if not(min(a[0],bb[0])-pad<=target.x<=max(a[0],bb[0])+pad and min(a[1],bb[1])-pad<=target.y<=max(a[1],bb[1])+pad):continue\n if K.L.body(t).distance(target)<=1.5:assert t['uuid']in iv[3];selected.append(('track',t))\n"+s[end:]
s=s.replace('CM-two-ground-old-wall-source-obligations-r314','CM-J15002-pin79-additional-old-F-walls-r324').replace("'exact_selected_wall_count':5","'exact_selected_wall_count':len(selected),'target_actual_J15002_79_mm':[117.452,201.175],'known_CDONE_b7dc_track_excluded_to_show_additional_walls':True")
needle="'selected_peer_wall_UUIDs_are_currently_untouched':True"
s=s.replace(needle,needle+",'actual_F_full_body_distance_to_target_mm':K.L.body(t).distance(target)")
dst.write_text(s,encoding='utf-8',newline='\n')
