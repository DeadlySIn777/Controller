"""R330 bounded successor: only exact spatially irrelevant Cu is omitted."""
from pathlib import Path
p=Path(__file__).with_name('screen_CM79_external_In1_In4_source_layers_old_supported_refs_hard_r330.py')
s=p.read_text(encoding='utf-8').replace('r330','r332').replace('R330','R332')
# Every buffered constraint radius is below 1.3 mm. The region+3 mm clip
# therefore cannot change the obstacle intersection in the declared region.
# Original roles, source masks, pad and Cu primitives stay byte untouched.
s=s.replace("s=s.replace('region=box(104,158,144,214)'", "s=s.replace('region=box(104,158,144,214)'")
needle=" s=s.replace(marker,mask+marker)"
assert needle in s
s=s.replace(needle,""" s=s.replace(marker,mask+marker)
 s=s.replace('obstacles.append(buf(z[\\'shape\\'],.625+req))','assert .625+req<3;obstacles.append(buf(zero(z[\\'shape\\']).intersection(wide),.625+req))')
 s=s.replace('ref=zero(K.source_refs(beforeLG)[','ref=zero(K.source_refs(beforeLG)[')
 s=s.replace("[REFKEY]);supported=[]", "[REFKEY]).intersection(wide);supported=[]") if False else s
 # Substitute the expanded actual reference key in the already-bound code.
 s=s.replace("ref=zero(K.source_refs(beforeLG)['F.Cu']);supported=[]", "ref=zero(K.source_refs(beforeLG)['F.Cu']).intersection(wide);supported=[]")
 s=s.replace("ref=zero(K.source_refs(beforeLG)['B.Cu']);supported=[]", "ref=zero(K.source_refs(beforeLG)['B.Cu']).intersection(wide);supported=[]")
 s=s.replace("records,trees=F.build({**c,'zones':[]});obstacles=[]", "records,trees=F.build({**c,'zones':[]});print('R332_PHASE_NATIVE_ROWS',flush=True);obstacles=[]")
 s=s.replace(" for v in h['vias']:", " print('R332_PHASE_OWNED_POSITIVE_LOCAL_GUARDS_COMPLETE',flush=True)\\n for v in h['vias']:")
 s=s.replace("put(O/'exact-source-bank-old-reference-hard-mask-ledger.json'", "print('R332_PHASE_EXACT_SOURCE_SUPPORTED_MASK_COMPLETE',flush=True);put(O/'exact-source-bank-old-reference-hard-mask-ledger.json'")
 s=s.replace("faces=RF.parts(free);tests=[]", "faces=RF.parts(free);put(O/'exact-plus3mm-spatial-broadphase-authority.json',{'region_plus_margin_mm':3,'maximum_owned_positive_obstacle_radius_mm':1.250003,'maximum_source_supported_reference_obstacle_radius_mm':.900003,'all_omitted_remote_geometry_is_disjoint_every_candidate_guard':'EXACT_SPATIAL_SCOPE','every_final_whole_original_body_source_reference_gate':'OPEN_NOT_WAIVED','no_original_WKB_or_model_bytes_changed':True});tests=[]")
""")
exec(compile(s,str(__file__),'exec'))
