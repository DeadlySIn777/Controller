from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_c10036_paired_return_r4.py').read_text()
s=s.replace('paired-return-recipe-r4','paired-return-recipe-r5').replace('inherited-transition-r4','inherited-transition-r5')
a="assert abs(gap.area-audit['new_reference_errors'][0]['full_body_uncovered_mm2'])<1e-8,(gap.area,audit['new_reference_errors'][0]);assert maximum<=radius,(maximum,radius)"
b="source_kernel_gap=L.body(t).difference(planes['In1.Cu']);assert abs(source_kernel_gap.area-audit['new_reference_errors'][0]['full_body_uncovered_mm2'])<1e-8,(source_kernel_gap.area,audit['new_reference_errors'][0]);assert maximum<=radius,(maximum,radius)"
assert s.count(a)==1;s=s.replace(a,b)
a="'gap_area_mm2':gap.area"
b="'source_r3_kernel_gap_area_mm2':source_kernel_gap.area,'full_128_arc_segments_per_quadrant_gap_area_mm2':gap.area,'gap_area_mm2':gap.area"
assert s.count(a)==1;s=s.replace(a,b)
q=HERE/'construct_c10036_paired_return_r5.py';assert not q.exists();q.write_text(s)
