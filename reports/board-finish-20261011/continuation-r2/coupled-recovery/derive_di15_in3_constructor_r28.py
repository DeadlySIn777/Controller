"""Create a separate In3 continuous nominee with exact failure counters."""
from pathlib import Path
import hashlib
HERE=Path(__file__).resolve().parent
p=HERE/'construct_di15_reference_escape_r25.py';raw=p.read_bytes()
s=raw.decode();s=s.replace('Latest frozen R59 power/protected model','Frozen R78 power/protected model; newer reservations are hard only')
s=s.replace("out=HERE/'di15-partial-annulus-reference-B-nomination-r25.json'","out=HERE/'di15-partial-annulus-reference-In3-nomination-r28.json'")
s=s.replace("'B.Cu'","'In3.Cu'")
s=s.replace("'B_source_reachable_component_count'","'In3_source_reachable_component_count'").replace("'B_total_reference_free_mm2'","'In3_total_reference_free_mm2'")
s=s.replace('ins=K.pieces(free[NET,\'In3.Cu\']);pairs=[];attempts=[]','ins=K.pieces(free[NET,\'In3.Cu\']);pairs=[];attempts=[];component_diagnosis=[]')
s=s.replace('for part in ins:\n    a=sr.intersection(part);b=dr.intersection(part)\n    if a.is_empty or b.is_empty:continue',"for part_index,part in enumerate(ins):\n    a=sr.intersection(part);b=dr.intersection(part)\n    diagnosis={'source_attachment_index':si,'target_attachment_index':di,'transport_component':part_index,'component_area_mm2':part.area,'source_signal_site_area_mm2':a.area,'target_signal_site_area_mm2':b.area,'both_terminal_regions_present':not a.is_empty and not b.is_empty,'source_nominees':0,'source_nominees_with_new_return':0,'target_nominees':0,'target_nominees_with_new_return':0};component_diagnosis.append(diagnosis)\n    if a.is_empty or b.is_empty:continue")
s=s.replace("for sa in K.sites(a,[118.45,90.75],8):\n     pa", "for sa in K.sites(a,[118.45,90.75],8):\n     diagnosis['source_nominees']+=1\n     pa")
s=s.replace('if not ra:continue\n     for sb',"if not ra:continue\n     diagnosis['source_nominees_with_new_return']+=1\n     for sb")
s=s.replace("for sb in K.sites(b,[131.25,112.35],8):\n      pb", "for sb in K.sites(b,[131.25,112.35],8):\n      diagnosis['target_nominees']+=1\n      pb")
s=s.replace('if not rb:continue\n      pairs.append',"if not rb:continue\n      diagnosis['target_nominees_with_new_return']+=1\n      pairs.append")
s=s.replace("'continuous_exact_component_diagnosis':site_diagnosis,", "'continuous_exact_component_diagnosis':site_diagnosis,'every_terminal_transport_component_diagnosis':component_diagnosis,")
s=s.replace("A.read(BIND.__file__);A.read(HERE/'di15-target-reference-cut-obligations-r23.json')", "A.read(BIND.__file__);A.read(HERE/'di15-target-reference-cut-obligations-r23.json');A.read(HERE/'construct_di15_reference_escape_r25.py')")
s=s.replace("h=current['h'];zones=current['zones'];before=current['after'];refs=current['refs'];", "h=current['h'];zones=current['zones'];before=current['after'];refs=current['refs'];")
target=HERE/'construct_di15_reference_escape_r28.py';assert not target.exists();target.write_text(s)
print(hashlib.sha256(target.read_bytes()).hexdigest())
