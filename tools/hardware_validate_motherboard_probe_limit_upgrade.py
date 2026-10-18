"""Independent exact bounded operator delta and native current-cap audit."""
import json,math,collections
from pathlib import Path
from hardware_validate_motherboard_do import native
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_probe_limit_upgrade';BASE=ROOT/'hardware/motherboard_operator'
CHANGED={'U14026','U14027','R14057','R14058','R14063','R14064','R14059','R14060','R14065','R14066','C14044','C14049'};ADDED={'R19401','R19402','R19403','R19404'}

def validate(d,base=None,netlist=None,erc=None):
 errors=[]
 def ck(x,msg):
  if not x:errors.append(msg)
 try:
  if base is None:base=json.loads((BASE/'design.json').read_text())
  p=d['components'];op=base['components'];ck(len(p)==d['fitted_component_count']==198 and sum(len(c['pins']) for c in p.values())==d['fitted_pad_count']==587,'198 real footprints587nativepins')
  ck(set(p)==set(op)|ADDED,'exact four new resistors, no removals')
  ck({r for r in op if p.get(r)!=op[r]}==CHANGED,'exact twelve changed components')
  for k,v in base.items():
   if k not in ['components','revision','fitted_component_count','fitted_pad_count','ports_24v','unimplemented_obligations']:ck(d.get(k)==v,'all unrelated operator contracts preserved '+k)
  ck(not d['manufacturing_ready'] and not d['physical_qualification'] and not d['firmware_implemented'],'no physical/target manufacture claims')
  for i in range(2):
   pr=f'PRB{i}';ref=f'U{14026+i}';b=14057+i*6;c=f'C{14044+i*5}';u=p[ref];ck(u['mpn']=='MAX17612AATB+T' and u['footprint']=='CNC_MB_Operator:MAX17612_T1033_ADI','exact source-reviewed device/package')
   ck(u['pins']=={'1':'FIELD_A_24V_PROTECTED','2':pr+'_UVLO','3':'FIELD_GND','4':pr+'_CLMODE','5':pr+'_SHDN_N','6':pr+'_FIELD_FAULT_N','7':pr+'_FIELD_FAULT_N','8':pr+'_ILIM','9':'FIELD_GND','10':pr+'_24V','11':'FIELD_GND'},'ADI10pinmap/UVOV-FLAGwiredOR/domain/actualEN')
   il=p[f'R{b}'];ck(il['mpn']=='TNPW06032K49BEEA' and il['resistance_ohm']==2490 and il['pins']==op[f'R{b}']['pins'] and il['tolerance']==.001 and il['tcr_ppm_K']==25,'actual full-range current accuracy resistor')
   uv=p[f'R{b+1}'];ck(uv['mpn']=='CRCW0603100KFKEA' and uv['resistance_ohm']==100000 and uv['pins']==op[f'R{b+1}']['pins'],'actual UVhigh leg')
   ck(p[c]['pins']=={'1':'FIELD_A_24V_PROTECTED','2':'FIELD_GND'} and p[c]['mpn']=='GRM188R71H105KA12D' and math.isclose(p[c]['capacitance_f'],1e-6),'obsoleteDVDTcap repurposed actualinput bulk')
   for off,net,val,mpn in [(0,pr+'_UVLO',10000,'CRCW060310K0FKEA'),(2,pr+'_CLMODE',150000,'CRCW0603150KFKEA')]:
    z=p[f'R{19401+i+off}'];ck(z['pins']=={'1':net,'2':'FIELD_GND'} and z['mpn']==mpn and z['resistance_ohm']==val and z['tolerance']==.01,'actual latch/UVlower divider')
   ch=d['ports_24v'][i];lo=.95*300/(2490*1.001*1.00375);hi=1.05*300/(2490*.999*.99625)
   ck(ch['normal_load_a']==.1 and ch['frozen_limit_max_a']==.15 and ch['guaranteed_current_bounds_available'] and ch['hard_short_bound_available'] and not ch['transient_peak_qualified'],'normal100mA cap150mA actual steady state source')
   ck(ch['limit_accuracy_fraction']==.05 and math.isclose(ch['current_bound_min_a'],lo) and math.isclose(ch['current_bound_max_a'],hi) and lo>.1+30/99000 and hi<.15,'full resistor/temp bounds plusbleed, no interpolation')
   up=p[f'R{b+2}'];dn=p[f'R{b+3}'];ck(up['pins']==op[f'R{b+2}']['pins'] and up['mpn']=='CRCW06033K32FKEA' and up['resistance_ohm']==3320 and dn['pins']==op[f'R{b+3}']['pins'] and dn['mpn']=='CRCW060310K0FKEA' and dn['resistance_ohm']==10000,'strong same-net EN receiving defaults')
   ck(8e-6*10100<.4 and 3.234*(9900/(9900+3320*1.01))-.000092*(10100*3353.2/(10100+3353.2))>1.4,'ENpowerloss andpoweredHIGH conditional inputcurrent screens')
  if netlist:
   a=native(netlist);ck(set(a)==set(p)|set(d['boundaries']),'native source complete population')
   for r,z in {**p,**d['boundaries']}.items():ck(a.get(r)=={k:z[k] for k in ['mpn','footprint','value','pins']},'native exact part and endpoint '+r)
  if erc:
   e=json.loads(Path(erc).read_text());vs=[v for s in e['sheets'] for v in s['violations']];ck(not e['ignored_checks'] and len(vs)==2 and all(v['severity']=='warning' and v['type']=='isolated_pin_label' for v in vs),'only two intendedprobeSUB labels, noignoredchecks')
 except (KeyError,ValueError,TypeError,OSError) as e:errors.append('invalid source '+str(e))
 return {'ok':not errors,'errors':errors,'manufacturing_ready':False,'physical_qualification':False,'static_current_range_a':[.95*300/(2490*1.001*1.00375),1.05*300/(2490*.999*.99625)],'changed_refs':sorted(CHANGED),'added_refs':sorted(ADDED)}
if __name__=='__main__':
 r=validate(json.loads((OUT/'design.json').read_text()),netlist=OUT/'netlist.xml',erc=OUT/'erc.json');(OUT/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(not r['ok'])
