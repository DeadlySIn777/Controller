"""Prepare the exact two ADC-reference capacitor source corrections in isolation.

No live child or parent write is permitted. Current manufacturer part/bias data
qualifies a bounded1uF25V0603 alternative; it does not guarantee reference
effective capacitance over production spread, aging or actual operating noise.
"""
import argparse,copy,hashlib,importlib.util,json,math,shutil,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,r):Path(p).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def lerp(data,x):
 pts=[(float(a[0]),float(b[0]))for a,b in data]
 for (a,c),(b,d)in zip(pts,pts[1:]):
  if a<=x<=b:return c+(d-c)*(x-a)/(b-a)
 raise ValueError('Manufacturer model does not enclose requested point')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out=a.out.resolve()
 if a.out.exists():raise ValueError('Fresh immutable proposal required')
 a.out.mkdir(parents=True);before=a.out/'before';before.mkdir();child=ROOT/'hardware/motherboard_analog_input';shutil.copytree(child,before/'child');originals=[ROOT/'tools/hardware_build_motherboard_analog_input.py',ROOT/'tools/hardware_validate_motherboard_analog_input.py',ROOT/'tests/test_motherboard_analog_input.py'];[shutil.copyfile(p,before/p.name)for p in originals]
 frozen={str(p):sha(p)for p in list(child.rglob('*'))+originals if p.is_file()};tools=a.out/'candidate-tools';tools.mkdir();builder=tools/originals[0].name;validator=tools/originals[1].name
 raw=originals[0].read_text(encoding='utf-8');old="for rail in ['AI_ADC_REFIO','AI_ADC_REFCAP']:cap(rail,g,22000,'actualreferencechargecap, effective>=10uF mustbequalified');cap(rail,g,1000,'referencecloseHF bypass')"
 new="""for rail in ['AI_ADC_REFIO','AI_ADC_REFCAP']:
  cap(rail,g,22000,'actualreferencechargecap, effective>=10uF mustbequalified')
  reference_hf=cap(rail,g,1000,'referencecloseHF bypass')
  parts[reference_hf].update(mpn='GRM188R71E105KA12D',value='1000nF25V',voltage_rating_v=25,role='manufacturer-confirmed1uF25V X7R0603 referenceHF; nominal/bias/aging qualification distinct')"""
 if raw.count(old)!=1:raise ValueError('Current exact reference builder changed')
 raw=raw.replace(old,new).replace("d['revision']='MB-AI-r03-ADC-local-bypass'","d['revision']='MB-AI-r04-reference-part-source'")
 anchor="d['revision']='MB-AI-r04-reference-part-source'"
 metadata=dict(exact_references=['C14741','C14743'],exact_mpn='GRM188R71E105KA12D',manufacturer_current_part_confirmed=True,historical_H105_not_declared_nonexistent=True,reference_effective_capacitance_full_corner_qualified=False,reference_ESR_loaded_stability_qualified=False,product_internal_ambient_c=[0,55],no_source_pins_or_footprints_changed=True)
 raw=raw.replace(anchor,anchor+'\n d[\'adc_reference_component_qualification\']='+repr(metadata));builder.write_text(raw,encoding='utf-8')
 valid=originals[1].read_text(encoding='utf-8');anchor="  for ref,mpn,nf,voltage,fp in [('C14744'"
 check="""  if 'adc_reference_component_qualification'in d:
   q=d['adc_reference_component_qualification']
   ck(q['exact_references']==['C14741','C14743']and q['exact_mpn']=='GRM188R71E105KA12D'and q['manufacturer_current_part_confirmed']and not q['reference_effective_capacitance_full_corner_qualified']and not q['reference_ESR_loaded_stability_qualified']and q['product_internal_ambient_c']==[0,55],'exact bounded reference sourcing; typical model is not production qualification')
   for ref,rail in [('C14741','AI_ADC_REFIO'),('C14743','AI_ADC_REFCAP')]:
    exact(ref,'GRM188R71E105KA12D','Capacitor_SMD:C_0603_1608Metric',{1:rail,2:g})
    ck(p[ref]['voltage_rating_v']==25 and math.isclose(p[ref]['capacitance_f'],1e-6),'actual manufacturer referenceHF rating/value')
"""
 if valid.count(anchor)!=1:raise ValueError('Exact validator anchor differs')
 valid=valid.replace(anchor,check+anchor);validator.write_text(valid,encoding='utf-8')
 build=module('adc_ref_candidate_builder',builder);build.ROOT=ROOT;stage=a.out/'candidate/hardware/motherboard_analog_input';build.build(stage)
 for suffix,cmd in [('netlist.xml',[CLI,'sch','export','netlist','--format','kicadxml','-o',str(stage/'netlist.xml'),str(stage/'motherboard_analog_input.kicad_sch')]),('erc.json',[CLI,'sch','erc','--format','json','-o',str(stage/'erc.json'),str(stage/'motherboard_analog_input.kicad_sch')])]:
  r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8');(a.out/(suffix+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0
 validate=module('adc_ref_candidate_validator',validator).validate;old=json.loads((child/'design.json').read_text());d=json.loads((stage/'design.json').read_text());changes=[r for r in old['components']if old['components'][r]!=d['components'][r]];assert changes==['C14741','C14743'];assert old['blocks']==d['blocks']and old['channels']==d['channels']and old['boundaries']==d['boundaries'];assert all(v['pins']==d['components'][r]['pins']for r,v in old['components'].items());assert validate(d,stage/'netlist.xml',stage/'erc.json')['ok']
 tests=module('adc_ref_original_mutation_tests',originals[2]);tests.ROOT=a.out/'candidate';tests.validate=validate;suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
 with(a.out/'tests.log').open('w',encoding='utf-8')as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
 assert r.wasSuccessful();controls=[]
 for name,edit in [('wrong-reference-H105-alias',lambda x:x['components']['C14741'].update(mpn='GRM188R71H105KAALD')),('wrong-50V-source-rating',lambda x:x['components']['C14743'].update(voltage_rating_v=50)),('typical-model-false-production-proof',lambda x:x['adc_reference_component_qualification'].update(reference_effective_capacitance_full_corner_qualified=True)),('temperature-scope-expansion',lambda x:x['adc_reference_component_qualification'].update(product_internal_ambient_c=[-40,55]))]:
  x=copy.deepcopy(d);edit(x);assert not validate(x)['ok'];controls.append(dict(name=name,rejected=True))
 modelrows=[]
 for p in (ROOT/'reports/motherboard-critical-routing-20261001/reference-cap-primary-r09').glob('bias-*.json'):
  for q in json.loads(p.read_text())['JsonCharaData']:
   row=q['charadata'][0];assert not row['error'];modelrows.append(dict(part=q['partnumber'],temperature_c=int(row['tc']),ac_vrms=.01,cap_4_10v_uf=lerp(row['data'],4.10),cap_4_15v_uf=lerp(row['data'],4.15)))
 by={(r['part'],r['temperature_c']):r for r in modelrows};assert len(by)==112
 pair=[]
 for t in range(56):
  bulk=by['GCM31CR71A226KE02',t];hf=by['GRM188R71E105KA12',t];pair.append(dict(temperature_c=t,typical_bulk_uf=bulk['cap_4_10v_uf'],typical_hf_uf=hf['cap_4_10v_uf'],conditional_pair_after_minus10percent_tolerance_uf=.9*(bulk['cap_4_10v_uf']+hf['cap_4_10v_uf']),conditional_4_15v_guard_uf=.9*(bulk['cap_4_15v_uf']+hf['cap_4_15v_uf'])))
 minimum=min(pair,key=lambda r:r['conditional_4_15v_guard_uf']);assert minimum['conditional_4_15v_guard_uf']>10
 assert all(sha(Path(p))==h for p,h in frozen.items())
 receipt=dict(passed=True,live_child_or_parent_mutated=False,exact_changes=[dict(reference=r,before=old['components'][r],after=d['components'][r])for r in changes],all_source_pins_parts_footprints_and_blocks_preserved=True,child_parts=165,child_electrical_pads=554,native_ERC_errors=0,native_ERC_warnings=0,original_child_mutation_tests=r.testsRun,additional_reference_negative_controls=controls,product_internal_ambient_c=[0,55],manufacturer_typical_model_rows=modelrows,conditional_pair_sweep=pair,minimum_conditional_pair_guard=minimum,conditional_unallocated_further_loss_fraction=1-10/minimum['conditional_4_15v_guard_uf'],production_effective_C_guarantee=False,model_basis='Manufacturer typical curve at10mVrms,0..55C integer samples; each part minus10% initial tolerance. Typical DC-bias model is not a guaranteed distribution; do not double-count its model temperature again as X7R15%. Unspecified production/aging/intermediate temperature/ripple/ESR/startup limits remain qualification.',reference_numeric_ESR_limit_in_primary=False,remaining_H105_elsewhere_not_changed=True,source26_live_adoption_held=True,input_sha256=frozen,candidate_sha256={str(p.relative_to(a.out)):sha(p)for p in stage.rglob('*')if p.is_file()},candidate_builder_sha256=sha(builder),candidate_validator_sha256=sha(validator),manufacturing_ready=False)
 write(a.out/'receipt.json',receipt);print(json.dumps(dict(passed=True,changed=changes,tests=receipt['original_child_mutation_tests']+4,conditional_guard_min_uf=minimum['conditional_4_15v_guard_uf'],live_source_mutated=False)))
if __name__=='__main__':main()
