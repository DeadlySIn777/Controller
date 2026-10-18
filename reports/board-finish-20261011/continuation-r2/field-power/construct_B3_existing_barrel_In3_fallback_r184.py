"""Explicit additional inner flash hypothesis on two unchanged native barrels."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_B3_preserving_exact_old_IO3_r177.py').read_text(encoding='utf-8')
s=s.replace('r177','r184').replace('R177','R184')
anchor="hard={'planes':[],'discrete':{'vias':[],'tracks':[]}}"
insertion="""actual=json.loads((C.BASE/'continuation-r2/native-198b-geometry/actual-via-flashes.json').read_text(encoding='utf-8'))['vias'];flashrows=[]
for prefix,role in [('049e91c3','target_native_B3_barrel'),('12d237e3','source_native_B3_barrel')]:
 prior=next(v for v in h['vias'] if v['uuid'].startswith(prefix));assert C.norm(prior['net'])=='/motherboard_do/DOB_FIELD_3V3';original=copy.deepcopy(prior);mask=list(prior.get('flashed',actual[prior['uuid']]));assert 'In3.Cu' not in mask
 for model in (h,c):
  v=next(v for v in model['vias'] if v['uuid']==prior['uuid']);v['flashed']=list(dict.fromkeys(mask+['In3.Cu']));v['prospective_extra_native_flash_layers']=['In3.Cu'];v['required_retained_native_flash_layers']=mask
 flashrows.append({'existing_native_UUID':prior['uuid'],'raw_net':prior['net'],'original_record':original,'old_actual_required_flash_layers':mask,'new_proposed_extra_flash_layers':['In3.Cu'],'native_serialized_geometry_and_padstack_unchanged':True,'layer_center_must_be_inside_intended_new_outline':True,'physical_Cu_retains_drill_void':True,'selected_native_refill_then_exact_source_annulus_proof_required':True,'role':role})
b['field_existing_barrel_flash_obligations_r184']=flashrows
(B/'existing-barrel-extra-In3-flash-hypothesis.json').write_text(json.dumps(flashrows,indent=1)+'\\n',encoding='utf-8')
hard={'planes':[],'discrete':{'vias':[],'tracks':[]}}"""
assert anchor in s;s=s.replace(anchor,insertion)
s=s.replace("original-IO3-r172-positive-snapshot-4/proposed-zones.pkl','9fbe57d1d4a5d6999e4500ab091480ad7e34afe47a1fa9b35d457c2f165937fd'","original-IO3-r172-positive-snapshot-8/proposed-zones.pkl','d576613bad70e94d04e47822b0b7c42f30e7f1a72e91d4a4a9cf1f8335eac16c'")
s=s.replace("INNER=['In2.Cu','In1.Cu','In4.Cu','In3.Cu']","INNER=['In3.Cu']")
# The inherited wrapper edits the original source string. Override its exact
# replacement target as well, rather than assuming the already edited text.
s=s.replace('s=s.replace("INNER=[\'In1.Cu\',\'In4.Cu\',\'In3.Cu\',\'In2.Cu\']","INNER=[\'In3.Cu\']")','s=s.replace("INNER=[\'In1.Cu\',\'In4.Cu\',\'In3.Cu\',\'In2.Cu\']","INNER=[\'In3.Cu\']")')
exec(compile(s,str(H/'construct_B3_preserving_exact_old_IO3_r177.py'),'exec'))
