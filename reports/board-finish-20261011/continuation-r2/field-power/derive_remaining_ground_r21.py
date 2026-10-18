from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'remaining_field_ground_feeds_r20.py').read_text(encoding='utf-8')
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change("OUT=HERE/'remaining-field-ground-feeds-r20'","OUT=HERE/'remaining-field-ground-feeds-r21'")
change('controller-field-remaining-r20/','controller-field-remaining-r21/')
change("aa=part.buffer(-.00002).intersection(src);bb=part.buffer(-.00002).intersection(dst)","aa=part.buffer(-.00002).intersection(src.buffer(width/2-.025));bb=part.buffer(-.00002).intersection(dst.buffer(width/2-.025))")
change("body.intersection(src).area<1e-8 or body.intersection(dst).area<1e-8","body.intersection(src).area<.001 or body.intersection(dst).area<.001")
change("'no_new_planes':True","'no_new_planes':True,'endpoint_centers_may_be_outside_source_only_with_checked_physical_Cu_overlap_mm2':.001,'minimum_endpoint_penetration_mm':.025")
out=HERE/'remaining_field_ground_feeds_r21.py';assert not out.exists();out.write_text(s,encoding='utf-8')
