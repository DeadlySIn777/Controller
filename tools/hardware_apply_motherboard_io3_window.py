"""Bounded motherboard-only IO3 monitor-window correction, originals read-only.

This explicitly supersedes the implementation-only3.20..3.40V monitor target
with divider bounds inside the actual T20/oscillator supply intersection.
No watchdog, reset, health logic, pin, return or delay changes are permitted.
"""
from __future__ import annotations
import copy,hashlib,json,shutil,subprocess
from pathlib import Path
from hardware_build_assembly import parse,dump,children,child,value,q,ref_property
from hardware_apply_motherboard_io3_upgrade import coords,exact_label,symbol_for,uid,ROOT,KICAD
OUT=ROOT/'hardware/motherboard_io3_window'
REPORT=ROOT/'reports/motherboard-io3-upgrade-20260930/voltage-window-review'
UV_MPN='TNPW060353K6BEEA'
OV_MPN='TNPW060357K6BEEA'
SERIES_MPN='TNPW0603698RBEEA'
FP='Resistor_SMD:R_0603_1608Metric'
SCOPES={'mc':[('R2061','R2069','R18003')],'motor':[('R9005','R9007','R18004'),('R9015','R9017','R18005')]}

def apply_io3_monitor_window(tree,model,scope):
 if scope not in SCOPES:raise ValueError('Unreviewed source scope')
 t,m=copy.deepcopy(tree),copy.deepcopy(model);p=m['components']
 ledger=[]
 for uv,ov,series in SCOPES[scope]:
  if series in p:raise ValueError('Repeated window correction/ref collision')
  for ref,ohms,old_mpn,new_mpn,new_ohms in [(uv,54500,'PLT0603Z5452LST1',UV_MPN,53600),(ov,57500,'PLT0603Z5752LST1',OV_MPN,57600)]:
   c=p.get(ref,{})
   if c.get('mpn')!=old_mpn or c.get('footprint')!=FP or c.get('pins',{}).get('1')!='IO_3V3':raise ValueError('Unexpected exact monitor top '+ref)
   if c.get('resistance_ohm',c.get('resistance_ohms',ohms))!=ohms:raise ValueError('Unexpected retained resistance '+ref)
   s=symbol_for(t,ref)
   c.update(value=f'{new_ohms}R 0.1% 25ppm',mpn=new_mpn,resistance_ohm=new_ohms,initial_tolerance=.001,tcr_ppm=25,component_substitution='MB-IO3-WINDOW-001',inherited_mpn=old_mpn)
   c.pop('resistance_ohms',None)
   for prop in children(s,'property'):
    if value(prop[1])=='Value':prop[2]=q(c['value'])
    elif value(prop[1])=='MPN':prop[2]=q(new_mpn)
   ledger.append({'ref':ref,'old_mpn':old_mpn,'new_mpn':new_mpn,'old_ohm':ohms,'new_ohm':new_ohms,'unchanged_footprint':FP,'pins_before':dict(c['pins'])})
  old=symbol_for(t,ov);start,definition=coords(t,old)
  label=exact_label(t,ov,'1','IO_3V3')
  if label[0]!='label':raise ValueError('Monitor IO3 endpoint must be local label')
  intermediate='IO_3V3_OV_SERIES_'+scope.upper()+'_'+ov
  label[1]=q(intermediate);p[ov]['pins']['1']=intermediate
  new=copy.deepcopy(old);at=child(new,'at');delta=(76.2,0);at[1:3]=[str(float(at[1])+delta[0]),str(float(at[2])+delta[1])]
  child(new,'uuid')[1]=q(uid(series))
  for prop in children(new,'property'):
   pat=child(prop,'at');pat[1:3]=[str(float(pat[1])+delta[0]),str(float(pat[2])+delta[1])]
   k=value(prop[1])
   if k=='Reference':prop[2]=q(series)
   elif k=='Value':prop[2]=q('698R 0.1% 25ppm')
   elif k=='MPN':prop[2]=q(SERIES_MPN)
  for project in children(child(new,'instances'),'project'):
   for path in children(project,'path'):child(path,'reference')[1]=q(series)
  t.append(new)
  for pin,net in [('1','IO_3V3'),('2',intermediate)]:
   xy=[round(start[pin][0]+delta[0],4),round(start[pin][1]+delta[1],4)]
   t.append(['label',q(net),['at',str(xy[0]),str(xy[1]),'0'],['effects',['font',['size','.85','.85']],['justify','left','bottom']],['uuid',q(uid(series+pin))]])
  p[series]={'kind':'R','value':'698R 0.1% 25ppm','mpn':SERIES_MPN,'footprint':FP,'physical':True,'pins':{'1':'IO_3V3','2':intermediate},'no_connect':[],'resistance_ohm':698,'initial_tolerance':.001,'tcr_ppm':25,'source_block':'motherboard_io3_window','source_reference':series,'role':'catalogue E96 series trim of OV monitor top; effective58298ohm','status':'source_candidate_not_layout_or_physical_qualified'}
  ledger[-1]['pins_after']=dict(p[ov]['pins']);ledger[-1]['series_ref']=series
 old_window_metadata=copy.deepcopy({'windows':m.get('windows'),'receiving_io3_input_v':m.get('contract',{}).get('receiving_io3_input_v')})
 for w in m.get('windows',[]):
  if w.get('rail')=='IO_3V3':
   w['superseded_requirement_limits_v']=w.get('requirement_limits_v');w['requirement_limits_v']=[3.14,3.465]
   w['static_acceptance_v']=[3.250213725012973,3.3479331042040728]
   for d in w['dividers']:
    d['top_ohm']=53600 if d['kind']=='UV' else 58298
    if d['kind']=='OV':d['series_ref']=next(x[2] for x in SCOPES[scope] if x[1]==d['top_ref'])
 if 'receiving_io3_input_v' in m.get('contract',{}):m['contract']['receiving_io3_input_v']=[3.14,3.465]
 m['io3_monitor_window_revision']={'id':'MB-IO3-WINDOW-001','superseded_implementation_limit_v':[3.2,3.4],'actual_rated_intersection_v':[3.14,3.465],'prior_metadata':old_window_metadata,'user_contract_changed':False}
 receipt={'id':'MB-IO3-WINDOW-001','scope':scope,'ledger':ledger,'added_refs':[x[2] for x in SCOPES[scope]],'all_other_retained_components_unchanged':True,'superseded_implementation_monitor_target_v':[3.2,3.4],'source_operating_intersection_v':[3.14,3.465],'user_contract_changed':False,'physical_qualification':False,'manufacturing_ready':False}
 return t,m,receipt

def build():
 OUT.mkdir(exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True);receipts=[]
 for scope,folder,stem in [('mc','motherboard_io3_upgrade','motherboard_io3_upgrade'),('motor','motherboard_motor_power','motherboard_motor_power')]:
  src=ROOT/'hardware'/folder;dst=OUT/scope;dst.mkdir(exist_ok=True)
  t=parse((src/(stem+'.kicad_sch')).read_text(encoding='utf8'));m=json.loads((src/'design.json').read_text())
  t,m,r=apply_io3_monitor_window(t,m,scope)
  for file in src.iterdir():
   if file.suffix in ['.kicad_sym'] or file.name in ['sym-lib-table','fp-lib-table']:shutil.copyfile(file,dst/file.name)
   elif file.is_dir() and file.name.endswith('.pretty'):shutil.copytree(file,dst/file.name,dirs_exist_ok=True)
  for h in children(t,'hierarchical_label'):
   h[0]='label';h.remove(child(h,'shape'))
  (dst/(stem+'.kicad_sch')).write_text(dump(t)+'\n',encoding='utf8')
  (dst/'design.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf8')
  (dst/(stem+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':stem+'.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n',encoding='utf8')
  for args in [('sch','export','netlist','--format','kicadxml','-o',str(dst/'netlist.xml'),str(dst/(stem+'.kicad_sch'))),('sch','erc','--format','json','--output',str(REPORT/(scope+'-erc.json')),str(dst/(stem+'.kicad_sch')))]:
   run=subprocess.run([KICAD,*args],capture_output=True,text=True,encoding='utf8')
   if run.returncode:raise RuntimeError(run.stdout+run.stderr)
  r['original_source_sha256']={str(x.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(x.read_bytes()).hexdigest() for x in [src/(stem+'.kicad_sch'),src/'design.json']};receipts.append(r)
 (REPORT/'ledger.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf8');return receipts
if __name__=='__main__':print(json.dumps(build(),indent=2))
