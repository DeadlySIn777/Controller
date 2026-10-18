"""Bounded derived operator source; originals, parent schematic and PCB untouched."""
import copy,hashlib,json,shutil
from pathlib import Path
import hardware_build_motherboard_operator as operator
from hardware_build_motherboard_safety_sensor import KINDS as SAFETY_KINDS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'hardware/motherboard_probe_limit_upgrade';REPORT=ROOT/'reports/motherboard-probe-limit-20260930'

def upgrade(baseline):
 d=copy.deepcopy(baseline);p=d['components'];ledger=[]
 for i in range(2):
  u=f'U{14026+i}';b=14057+i*6;c=f'C{14044+i*5}';pr=f'PRB{i}';old=copy.deepcopy(p[u])
  expected={'1':'FIELD_A_24V_PROTECTED','2':pr+'_UVLO','3':'FIELD_GND','4':pr+'_SHDN_N','5':'FIELD_GND','6':'FIELD_GND','7':pr+'_ILIM','8':pr+'_DVDT','9':pr+'_FIELD_FAULT_N','10':pr+'_24V','11':'FIELD_GND'}
  if p[u]['mpn']!='TPS26624DRCR' or p[u]['pins']!=expected:raise ValueError('Unreviewed original probe switch '+u)
  p[u].update(mpn='MAX17612AATB+T',value='MAX17612AATB+T',footprint='CNC_MB_Operator:MAX17612_T1033_ADI',pins={'1':'FIELD_A_24V_PROTECTED','2':pr+'_UVLO','3':'FIELD_GND','4':pr+'_CLMODE','5':pr+'_SHDN_N','6':pr+'_FIELD_FAULT_N','7':pr+'_FIELD_FAULT_N','8':pr+'_ILIM','9':'FIELD_GND','10':pr+'_24V','11':'FIELD_GND'},role='source-qualified20–250mA current limiter; UV/current/reverse faults combined; latched fault')
  il=f'R{b}';oldil=copy.deepcopy(p[il]);p[il].update(mpn='TNPW06032K49BEEA',value='2490R0.1%',resistance_ohm=2490,tolerance=.001,tcr_ppm_K=25,role='fullrange ±5% current accuracy,100mA load and150mA static cap')
  uv=f'R{b+1}';olduv=copy.deepcopy(p[uv]);p[uv].update(mpn='CRCW0603100KFKEA',value='100000R1%',resistance_ohm=100000,role='16.5V nominalUV threshold highleg')
  p[f'R{b+2}'].update(mpn='CRCW06033K32FKEA',value='3320R1%',resistance_ohm=3320,role='strong receiving ENpullup,maintainsHIGH with ENinputload')
  p[f'R{b+3}'].update(mpn='CRCW060310K0FKEA',value='10000R1%',resistance_ohm=10000,role='ENinternal8uA pullupcannot exceed .0808V with field3.3absent')
  p[c].update(mpn='GRM188R71H105KA12D',value='1000nF50V',pins={'1':'FIELD_A_24V_PROTECTED','2':'FIELD_GND'},capacitance_f=1e-6,voltage_rating_v=50,role='actual inputbulk,effective>=.47uF DCbias remains qualification')
  # New UV divider bottom and exact manufacturer latch mode selection.
  for off,net,val,mpn,role in [(0,pr+'_UVLO',10000,'CRCW060310K0FKEA','UVLO16.5V bottom'),(2,pr+'_CLMODE',150000,'CRCW0603150KFKEA','manufacturer150k latch-off')]:
   ref=f'R{19401+i+off}';
   if ref in p:raise ValueError('Probe upgrade ref collision')
   p[ref]={'kind':'R','mpn':mpn,'value':f'{val}R1%','footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':net,'2':'FIELD_GND'},'resistance_ohm':val,'tolerance':.01,'role':role}
  ch=d['ports_24v'][i];ch.update(ilim_ohm=2490,guaranteed_current_bounds_available=True,hard_short_bound_available=True,engineering_gate='Static current range sourced; transient peak/energy/rail drop and startup qualification remain',limit_accuracy_fraction=.05,current_bound_min_a=.95*300/(2490*1.001*1.00375),current_bound_max_a=1.05*300/(2490*.999*.99625),transient_peak_qualified=False)
 d['revision']='motherboard-probe-limit-upgrade-r0.1';d['fitted_component_count']=len(p);d['fitted_pad_count']=sum(len(c['pins']) for c in p.values());d['unimplemented_obligations'][0]='MAX17612 programmed static100mA/150mA load-cap requirement closed; transient shortpeak/energy, input/output DCbias, inrush and thermal/ramp qualification remain.'
 changed={r:{'old':baseline['components'][r],'new':c} for r,c in p.items() if r in baseline['components'] and c!=baseline['components'][r]};added={r:c for r,c in p.items() if r not in baseline['components']}
 return d,{'changed_components':changed,'added_components':added,'removed_components':[],'all_other_original_components_unchanged':True,'baseline_revision':baseline['revision'],'physical_qualification':False}

def build(out=OUT):
 base=json.loads((ROOT/'hardware/motherboard_operator/design.json').read_text());d,receipt=upgrade(base);saved_description=operator.description;saved_fp=operator.footprints;saved_kinds=copy.deepcopy(operator.KINDS)
 try:
  operator.description=lambda:d;operator.KINDS['SW24']=SAFETY_KINDS['MAX17612A']
  def fps(out):
   saved_fp(out);src=ROOT/'hardware/motherboard_safety_sensor/CNC_MB_Safety.pretty/MAX17612_T1033_ADI.kicad_mod';shutil.copyfile(src,Path(out)/'CNC_MB_Operator.pretty'/src.name)
  operator.footprints=fps;operator.build(Path(out))
 finally:operator.description=saved_description;operator.footprints=saved_fp;operator.KINDS=saved_kinds
 REPORT.mkdir(exist_ok=True);(REPORT/'bounded-delta.json').write_text(json.dumps(receipt,indent=2)+'\n');return d
if __name__=='__main__':build()
