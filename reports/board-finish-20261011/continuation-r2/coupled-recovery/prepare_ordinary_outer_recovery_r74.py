"""Freeze a separate outer-layer constructor with explicit empty-layer handling."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
src=H/'construct_ordinary_q0_pen_F_r70.py'; b=src.read_bytes();s=b.decode()
s=s.replace('Additive ordinary F-only recovery nominees for DOA Q0 and PEN enable.', 'Additive ordinary F or B recovery nominees for DOA Q0 and PEN enable.')
s=s.replace("REQUESTS=[('/motherboard_do/DOA_Q0_READY_N','/motherboard_motors/FIELD_GND',('J11003','2')),('/motherboard_process/PEN_ENABLE_LOGIC','/LOGIC_GND',('J11001','2'))]", "BASE_REQUESTS=[('/motherboard_do/DOA_Q0_READY_N','/motherboard_motors/FIELD_GND',('J11003','2')),('/motherboard_process/PEN_ENABLE_LOGIC','/LOGIC_GND',('J11001','2'))]\nREQUESTS=[(*q,layer) for q in BASE_REQUESTS for layer in ('F.Cu','B.Cu')]")
s=s.replace('r70','r74').replace('F-only','outer-only').replace('F_ONLY','OUTER_ONLY')
s=s.replace('for net,ground,sourcepad in REQUESTS:', 'for net,ground,sourcepad,layer in REQUESTS:')
s=s.replace("row={'net':net", "row={'selected_outer_layer':layer,'selected_adjacent_reference_layer':'In1.Cu' if layer=='F.Cu' else 'In4.Cu','net':net")
s=s.replace("reference=unary_union([q['shape'] for q in groot if q['kind']=='fill' and q['layer']=='In1.Cu']);term=[unary_union([q['shape'] for q in xs if q['layer']=='F.Cu']) for _,xs in needed];pair=nearest_points(*term);", "reference_layer='In1.Cu' if layer=='F.Cu' else 'In4.Cu';reference=unary_union([q['shape'] for q in groot if q['kind']=='fill' and q['layer']==reference_layer]);term=[unary_union([q['shape'] for q in xs if q['layer']==layer]) for _,xs in needed]\n  row['current_required_groups_layer_Cu_areas_mm2']=[q.area for q in term]\n  if any(q.is_empty for q in term):row['not_constructed_reason']='Required current group has no copper on this selected layer';print('ORDINARY_LAYER_INELIGIBLE',net,layer,flush=True);continue\n  pair=nearest_points(*term);")
s=s.replace("trees['F.Cu']",'trees[layer]').replace("rec['F.Cu']",'rec[layer]')
s=s.replace("z['layer']!='F.Cu'", "z['layer']!=layer")
s=s.replace("z['fills'].get('F.Cu',[])","z['fills'].get(layer,[])")
s=s.replace("if 'F.Cu' in q['layers']", "if layer in q['layers']")
s=s.replace("identity.serial_segment(net,'F.Cu',a,b,.2)","identity.serial_segment(net,layer,a,b,.2)")
s=s.replace("'layer':'F.Cu'", "'layer':layer")
s=s.replace("'source_connected_ref_plane':'actual '+sourcepad[0]+'.'+sourcepad[1]+' In1'", "'source_connected_ref_plane':'actual '+sourcepad[0]+'.'+sourcepad[1]+' '+reference_layer")
s=s.replace("print('ORDINARY_OUTER_ONLY_RESULT',net,bool", "print('ORDINARY_OUTER_ONLY_RESULT',net,layer,bool")
dst=H/'construct_ordinary_q0_pen_outer_r74.py'; assert not dst.exists();dst.write_text(s)
out=H/'prepare-ordinary-outer-r74.json';assert not out.exists();out.write_text(json.dumps({'source':str(src),'source_sha256':hashlib.sha256(b).hexdigest(),'derived':str(dst),'derived_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'delta':'Attempt F and B independently; reject explicitly absent layer Cu rather than nearest_points(empty); actual own-domain adjacent rooted In1/In4, same physical and source authority. No new holes or withdrawals.'},indent=1)+'\n');compile(s,str(dst),'exec');print(dst)
