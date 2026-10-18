"""Stage exactly two reference MPNs and three manufacturer fuse footprints.

Live sources stay frozen. Staged child inputs resolve explicitly rather than
blessing stale live hashes. Promotion is a separately requested transaction.
"""
import argparse,copy,csv,json,os,shutil,subprocess,sys
from pathlib import Path
import xml.etree.ElementTree as ET
from hardware_build_assembly import parse,dump,children,value,q,ref_property
from hardware_adopt_adc_bypass_source import ROOT,CLI,sha,load,write,file_hashes
from hardware_apply_fuse_geometry_upgrade import apply_fuse_geometry,make_library,NEW as FUSE_FP
from hardware_validate_motherboard import validate,nodes

CAPS=('C14741','C14743');FUSES=('F11001','F11002','F11003')
def properties(tree,refs,parts):
 result=copy.deepcopy(tree);found=[]
 for s in children(result,'symbol'):
  r=value(ref_property(s)[2])
  if r not in refs:continue
  found.append(r)
  for p in children(s,'property'):
   key={'Value':'value','MPN':'mpn','Footprint':'footprint'}.get(value(p[1]))
   if key:p[2]=q(parts[r][key])
 assert set(found)==set(refs)
 return result
def bom(path,parts,refs):
 with path.open(encoding='utf-8-sig',newline='')as f:reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
 for row in rows:
  if row['Reference']in refs:
   for label,key in [('Value','value'),('MPN','mpn'),('Footprint','footprint')]:row[label]=parts[row['Reference']][key]
 with path.open('w',encoding='utf-8',newline='')as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def add_fuse_library(folder,lib):
 dest=folder/'CNC_MB_Fuse.pretty';dest.mkdir();shutil.copyfile(lib,dest/lib.name)
 p=folder/'fp-lib-table';tree=parse(p.read_text())if p.exists()else['fp_lib_table',['version','7']]
 tree.append(parse('(lib(name "CNC_MB_Fuse")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_Fuse.pretty")(options "")(descr "Exact Keystone M55 manufacturer mounting"))'));p.write_text(dump(tree)+'\n')
def native(folder,basename,out):
 for name,cmd in [('export',[str(CLI),'sch','export','netlist','--format','kicadxml','-o',str(folder/'netlist.xml'),str(folder/(basename+'.kicad_sch'))]),('ERC',[str(CLI),'sch','erc','--format','json','-o',str(out),str(folder/(basename+'.kicad_sch'))])]:
  r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8');out.with_name(out.stem+'-'+name+'.log').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0
 e=load(out);issues=[v for s in e['sheets']for v in s['violations']];assert not e['ignored_checks']and not any(v['severity']=='error'for v in issues)
 return issues
def exact_qualification(tree,model,mapping):
 errors=validate(tree,model,mapping,False);actual=nodes(tree)
 for r,n in [('C14741','AI_ADC_REFIO'),('C14743','AI_ADC_REFCAP')]:
  c=model['components'][r]
  if c['mpn']!='GRM188R71E105KA12D'or c['value']!='1000nF25V'or c['voltage_rating_v']!=25 or c['footprint']!='Capacitor_SMD:C_0603_1608Metric'or abs(c['capacitance_f']-1e-6)>1e-15:errors.append('Exact reference qualification part '+r)
  if actual.get((r,'1'))!='/motherboard_analog_input/'+n or actual.get((r,'2'))!='/motherboard_analog_input/AI_AGND':errors.append('Exact reference native pins '+r)
 for r in FUSES:
  if model['components'][r]['mpn']!='3568'or model['components'][r]['footprint']!=FUSE_FP:errors.append('Exact manufacturer fuse footprint '+r)
 metadata=model.get('adc_reference_component_qualification',{})
 if metadata.get('reference_effective_capacitance_full_corner_qualified')is not False or metadata.get('reference_ESR_loaded_stability_qualified')is not False or metadata.get('product_internal_ambient_c')!=[0,55]:errors.append('Reference typical model cannot promise qualification or expanded temperature')
 if mapping.get('reviewed_source26_qualification_delta',{}).get('references')!=list(CAPS+FUSES):errors.append('Exact five-part source26 ledger')
 return errors
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ('reference-proposal','fuse-receipt','previous-adoption','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args();a.out=a.out.resolve()
 if a.out.exists():raise ValueError('Fresh immutable stage required')
 proposal=load(a.reference_proposal/'receipt.json');fuse=load(a.fuse_receipt);prior=load(a.previous_adoption);live=ROOT/'hardware/motherboard'
 assert proposal['passed']and not proposal['live_child_or_parent_mutated']and fuse['native_ERC_errors']==0
 for name,h in prior['source_hashes'].items():assert sha(live/name)==h,name
 frozen={str(p):sha(p)for p in list(live.rglob('*'))+list((ROOT/'hardware/motherboard_power_entry').rglob('*'))+list((ROOT/'hardware/motherboard_analog_input').rglob('*'))+[a.reference_proposal/'receipt.json',a.fuse_receipt,Path(__file__)]if p.is_file()}
 a.out.mkdir(parents=True);before=a.out/'before';shutil.copytree(live,before/'motherboard');stage=a.out/'candidate/hardware/motherboard';shutil.copytree(live,stage)
 power=a.out/'candidate/hardware/motherboard_power_entry';shutil.copytree(ROOT/'hardware/motherboard_power_entry',power)
 ai=a.out/'candidate/hardware/motherboard_analog_input';shutil.copytree(a.reference_proposal/'candidate/hardware/motherboard_analog_input',ai)
 old=load(stage/'design.json');old_nodes=nodes(ET.parse(stage/'netlist.xml'));model=copy.deepcopy(old);mapping=load(stage/'assembly-map.json');ai_model=load(ai/'design.json')
 # Exact power child tree/model change; no regeneration of the actual circuit.
 pt,pm,fr=apply_fuse_geometry(parse((power/'motherboard_power_entry.kicad_sch').read_text()),load(power/'design.json'));(power/'motherboard_power_entry.kicad_sch').write_text(dump(pt)+'\n');write(power/'design.json',pm);bom(power/'bom.csv',pm['components'],FUSES)
 lib=ROOT/'hardware/motherboard_fuse_geometry/CNC_MB_Fuse.pretty/Keystone_3568_M55.kicad_mod';add_fuse_library(power,lib);native(power,'motherboard_power_entry',power/'erc.json')
 # Only exact native properties change on the two retained parent sheets.
 ft,model,fr=apply_fuse_geometry(parse((stage/'motherboard_power_entry.kicad_sch').read_text()),model);(stage/'motherboard_power_entry.kicad_sch').write_text(dump(ft)+'\n');add_fuse_library(stage,lib)
 for r in CAPS:
  previous={k:v for k,v in old['components'][r].items()if k not in ('source_block','source_reference')};assert previous==next(v['before']for v in proposal['exact_changes']if v['reference']==r)
  model['components'][r]={**ai_model['components'][r],'source_block':'motherboard_analog_input','source_reference':r}
 t=properties(parse((stage/'motherboard_analog_input.kicad_sch').read_text()),CAPS,model['components']);(stage/'motherboard_analog_input.kicad_sch').write_text(dump(t)+'\n')
 model['adc_reference_component_qualification']=copy.deepcopy(ai_model['adc_reference_component_qualification']);mapping['reviewed_source26_qualification_delta']=dict(references=list(CAPS+FUSES),reference_proposal_sha256=sha(a.reference_proposal/'receipt.json'),fuse_receipt_sha256=sha(a.fuse_receipt),native_pin_nets_unchanged=True,parts_count_unchanged=True,physical_qualified=False)
 resolution={}
 for region,folder in [('motherboard_analog_input',ai),('motherboard_power_entry',power)]:
  for name in list(mapping['input_sha256']):
   prefix='hardware/'+region+'/'
   if name.startswith(prefix):resolution[name]=folder/name[len(prefix):]
  for p in folder.glob('CNC_MB_Fuse.pretty/*.kicad_mod'):resolution['hardware/'+region+'/CNC_MB_Fuse.pretty/'+p.name]=p
 for name,p in resolution.items():
  for d in [model['source_sha256'],mapping['input_sha256']]:d[name]=sha(p)
 # Every staged dependency is explicitly resolved; all other dependencies
 # still require the exact existing live hash. No stale child is blessed.
 input_proof=[]
 for name,h in mapping['input_sha256'].items():
  p=resolution.get(name,ROOT/name);assert sha(p)==h,name;input_proof.append(dict(logical_source=name,resolved=str(p.resolve()),sha256=h,staged=name in resolution))
 write(stage/'design.json',model);write(stage/'assembly-map.json',mapping);bom(stage/'bom.csv',model['components'],CAPS+FUSES)
 issues=native(stage,'motherboard',a.out/'erc.json');tree=ET.parse(stage/'netlist.xml');assert nodes(tree)==old_nodes;assert len(model['components'])==2688
 changed=[r for r in model['components']if model['components'][r]!=old['components'][r]];assert set(changed)==set(CAPS+FUSES)
 errors=exact_qualification(tree,model,mapping)
 if errors:write(a.out/'validation-failed.json',errors);raise ValueError('Actual source26 exact native qualification failed')
 env={**os.environ,'CONTROLLER_MOTHERBOARD_TEST_SOURCE':str(stage)};tests=[]
 for name in ['test_motherboard_integration.py','test_motherboard_adc_source_adoption.py','test_motherboard_fpga_current_annotations.py','test_motherboard_fpga_allocation.py']:
  p=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-p',name,'-v'],env=env,cwd=ROOT,capture_output=True,text=True,encoding='utf-8');log=a.out/(name+'.log');log.write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,name;tests.append(dict(name=name,returncode=0,log_sha256=sha(log)))
 controls=[]
 for name,edit in [('false-reference-effective-proof',lambda d:d['adc_reference_component_qualification'].update(reference_effective_capacitance_full_corner_qualified=True)),('old-fuse-footprint',lambda d:d['components']['F11001'].update(footprint='Fuse:Fuseholder_Blade_Mini_Keystone_3568')),('unconfirmed-reference-alias',lambda d:d['components']['C14741'].update(mpn='GRM188R71H105KAALD'))]:
  d=copy.deepcopy(model);edit(d);assert exact_qualification(tree,d,mapping);controls.append(dict(name=name,rejected=True))
 assert all(sha(Path(p))==h for p,h in frozen.items())
 oldhash=file_hashes(before/'motherboard');newhash=file_hashes(stage);delta=sorted(set(newhash)-set(oldhash))+[p for p in oldhash if newhash.get(p)!=oldhash[p]]
 receipt=dict(passed=True,adopted=False,actual_parts=2688,actual_purchased=2642,bare_geometry=44,DNP=2,exact_component_changes=[dict(reference=r,before=old['components'][r],after=model['components'][r])for r in CAPS+FUSES],exact_changed_parent_files=delta,native_ERC_errors=0,native_ERC_warnings=len(issues),ignored_checks=[],all_native_pin_nets_unchanged=True,all_other_native_parts_and_retained327_1229_and_FPGA135_48_preserved=True,source26_input_resolution=input_proof,staged_input_hash_resolution_pass=True,tests=tests,qualification_negative_controls=controls,input_sha256=frozen,source_hashes=newhash,source=str(stage.relative_to(ROOT)),reference_child=str(ai.relative_to(ROOT)),power_child=str(power.relative_to(ROOT)),fuse_geometry=fr,live_child_and_parent_unchanged=True,live_promotion_requires_root_release=True,manufacturing_ready=False)
 write(a.out/'receipt.json',receipt);print(json.dumps(dict(passed=True,adopted=False,parts=2688,changed=list(CAPS+FUSES),ERC_errors=0,ERC_warnings=len(issues),fresh_input_resolutions=len(input_proof))))
if __name__=='__main__':main()
