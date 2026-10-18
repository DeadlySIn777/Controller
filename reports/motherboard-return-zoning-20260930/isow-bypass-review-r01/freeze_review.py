"""Freeze an independent primary-source interpretation, not a PCB adoption."""
from pathlib import Path
import hashlib, json, shutil

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
sources={
 'isow1432':(ROOT/'reports/motherboard-comms-20260930/sources/isow1432.pdf','https://www.ti.com/lit/ds/symlink/isow1432.pdf'),
 'isow1044':(ROOT/'reports/motherboard-comms-20260930/sources/isow1044.pdf','https://www.ti.com/lit/ds/symlink/isow1044.pdf'),
 'sllu337':(OUT/'sllu337.pdf','https://www.ti.com/lit/ug/sllu337/sllu337.pdf'),
 'grm155':(OUT/'murata-grm155.pdf','https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM155R71H103KA88-01A.pdf'),
}
local={}
for key,(p,url) in sources.items():
 target=OUT/(key+'.pdf')
 if p!=target: shutil.copy2(p,target)
 local[key]=dict(url=url,file=target.name,sha256=sha(target))

# Dimensions refer to each side's nominal package origin; positive absolute X.
tip_min,tip_max=9.97/2,10.63/2
body_w_min,body_w_max=.45,.55
def body_gap(x): return [round(x-body_w_max/2-tip_max,6),round(x-body_w_min/2-tip_min,6)]
recipe_gap=body_gap(6.10)
review=dict(
 schema_version=1,review_type='independent primary-source interpretation and bounded dimensional proposal',
 no_source_or_pcb_mutation=True,manufacturing_ready=False,physical_qualification=False,
 sources=local,
 evidence=[
  dict(source='isow1432',page=41,figure='9-7',fact='Figure arrow is terminal-edge to capacitor terminal-edge; text says less than1mm from device pins without defining an exact PCB-land/body datum.'),
  dict(source='isow1044',page=37,figure='9-7',fact='Equivalent close HF-cap guidance and matching layout arrangement.'),
  dict(source='sllu337',page=8,figure='4-2',fact='C20 HF-cap lands visibly overlap corresponding same-net extended ISOW IC lands; this is a drawing observation, not an extracted numeric placement coordinate.'),
  dict(source='sllu337',page=10,table='5-1',fact='C6/C20 are10nF0402; this EVM uses a different capacitor manufacturer than the selected motherboard MPN.'),
  dict(source='isow1432',page=51,drawing='DFM0020A',fact='Manufacturer lead-tip overall span9.97..10.63mm.'),
  dict(source='grm155',page=2,fact='Selected GRM155R71H103KA88 package body1.0±.05 by.5±.05mm.'),
 ],
 rejected_inference='A1.48mm minimum centre-spacing bound is not universal: it assumes copper clearance between matching-net IC and capacitor lands, which the EVM deliberately overlaps.',
 distance_interpretation='Record shortest actual routed matching-land-edge gap/length and physical lead-tip-to-cap-body bounds independently. Do not convert either into an unqualified centre-distance threshold.',
 proposed_recipe=dict(
  hf_cap_local_center_abs_x_mm=6.10,hf_cap_local_center_y_mm=5.080,orientation='0402 vertical between converter power/return pins',
  ic_recommended_land_outer_abs_x_mm=5.90,cap_matching_land_inner_abs_x_mm=5.79,same_net_land_overlap_x_mm=.11,
  manufacturer_ic_tip_radius_mm=[tip_min,tip_max],manufacturer_cap_body_width_mm=[body_w_min,body_w_max],
  nominal_tip_to_body_gap_mm=recipe_gap,total_relative_x_placement_bound_mm=.10,
  bounded_tip_to_body_gap_mm=[round(recipe_gap[0]-.10,6),round(recipe_gap[1]+.10,6)],
  relative_bound_is_process_qualification_not_manufacturer_guarantee=True,
  using_point1_mm_per_component_would_make_gap_upper_mm=round(recipe_gap[1]+.20,6),
  proposed_courtyard_indentation_abs_x_mm=5.55,nominal_max_lead_tip_to_courtyard_margin_mm=round(5.55-tip_max,6),
  courtyard_changes_must_preserve_all_native_copper_paste_mask_lands=True,
 ),
 rejected_farther_recipe=dict(abs_x_mm=6.91,nominal_tip_to_body_gap_mm=body_gap(6.91),reason='May have0.70mm PCB-land-edge path but cannot be called literal less-than1mm device-tip-to-body compliance.'),
 additional_actual_layout_requirements=[
  'Symmetric close power/return trace paths until the HF bypass; exact local loop and actual native return proof remain required.',
  'Maintain manufacturer4mm raw secondary EMI exclusion from unrelated traces/pours near VISOOUT/GND2. Required local raw HF/bulk/ferrite paths shown in the example remain intentional; filtered return planes must not bypass the real ferrite.',
  'Native DRC plus exact IC/cap/body/courtyard pose proof, package and capacitor dimension tolerances, and actual assembler relative placement capability before adopting the bounded courtyard recipe.',
 ],
 source_geometry_proposal_review='coherent as bounded proposal; no native candidate reviewed or adopted by this receipt',
)
assert review['proposed_recipe']['bounded_tip_to_body_gap_mm']==[.410,.990]
assert review['proposed_recipe']['using_point1_mm_per_component_would_make_gap_upper_mm']==1.09
(OUT/'review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(review_sha256=sha(OUT/'review.json'),tip_to_body_gap_mm=review['proposed_recipe']['bounded_tip_to_body_gap_mm'],no_source_or_pcb_mutation=True)))
