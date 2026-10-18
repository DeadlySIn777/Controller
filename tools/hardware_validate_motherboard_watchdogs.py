"""Independent native-pin/default/polarity and conditional 20 ms review.

This reads native KiCad XML rather than trusting ERC or historical allocations.
No nominal propagation delay, unimplemented RTL or synthetic peer is promoted
to a guaranteed all-condition physical fault-to-inhibit bound.
"""
from __future__ import annotations
import argparse,copy,hashlib,itertools,json,math,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'reports/motherboard-integration-20260930/r19-2663-status-identity-staged-source'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_native(path):
 t=ET.parse(path);p={}
 for e in t.findall('./components/comp'):
  r=e.attrib['ref']
  if r.startswith('#'):continue
  f={x.attrib['name']:x.text or '' for x in e.findall('fields/field')}
  if r in p:raise ValueError('Duplicate native reference')
  p[r]={'mpn':f.get('MPN',''),'value':e.findtext('value'),'footprint':e.findtext('footprint'),'pins':{}}
 for e in t.findall('./nets/net'):
  n=e.attrib['name'].removeprefix('/')
  for x in e.findall('node'):
   r,k=x.attrib['ref'],x.attrib['pin']
   if r.startswith('#'):continue
   if k in p[r]['pins']:raise ValueError('Native duplicate pin')
   p[r]['pins'][k]=None if n.startswith('unconnected-') else n
 return p

class Permission:
 """Ideal digital model derived from actual U4001..4019 physical pin nets."""
 def __init__(self,p):
  self.p={r:copy.deepcopy(p[r]) for r in [f'U{i}' for i in range(4001,4020)]}
  self.v={'IO_3V3':1,'LOGIC_GND':0};self.q={r:0 for r,c in self.p.items() if c['mpn']=='SN74LVC2G74DCUR'}
  self.settle();self.clock={r:self.v.get(c['pins']['1'],0) for r,c in self.p.items() if r in self.q}
 def settle(self):
  for _ in range(40):
   old=(dict(self.v),dict(self.q))
   for r,c in self.p.items():
    p=c['pins'];g=lambda i:self.v.get(p.get(str(i)),0);mpn=c['mpn']
    if mpn=='SN74LVC1G11DBVR':self.v[p['4']]=g(1)&g(3)&g(6)
    elif mpn=='SN74LVC2G08DCUR':self.v[p['7']]=g(1)&g(2);self.v[p['3']]=g(5)&g(6)
    elif mpn=='SN74LVC2G32DCUR':self.v[p['7']]=g(1)|g(2);self.v[p['3']]=g(5)|g(6)
    elif mpn=='SN74LVC2G04DBVR':self.v[p['6']]=1-g(1);self.v[p['4']]=1-g(3)
    elif mpn=='SN74LVC2G74DCUR':
     if not g(7):raise ValueError('PRE_N must be inactive HIGH')
     if not g(6):self.q[r]=0
     self.v[p['5']]=self.q[r]
     if p.get('3'):self.v[p['3']]=1-self.q[r]
    else:raise ValueError('Unknown actual permission part '+r)
   if old==(self.v,self.q):return
  raise ValueError('Permission graph did not settle')
 def drive(self,**changes):
  self.v.update(changes);self.settle()
  for r in self.q:
   p=self.p[r]['pins'];now=self.v.get(p['1'],0)
   if now and not self.clock[r] and self.v.get(p['6'],0):self.q[r]=self.v.get(p['2'],0)
   self.clock[r]=now
  self.settle();return dict(self.v)

def timer_screen(cap_nf=3.3,cap_tolerance=.05,ic_error=.095,
                 declared_temperature_fraction=.003,declared_parasitic_nf=.010,
                 declared_board_leakage_na=10):
 vals=[cap_nf,cap_tolerance,ic_error,declared_temperature_fraction,declared_parasitic_nf,declared_board_leakage_na]
 if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) for v in vals):raise ValueError('Finite numeric timing inputs required')
 if cap_nf<=0 or not 0<=cap_tolerance<1 or not 0<=ic_error<1 or not 0<=declared_temperature_fraction<1 or declared_parasitic_nf<0 or not 0<=declared_board_leakage_na<347:raise ValueError('Timing inputs outside admissible range')
 nom=3.23*cap_nf+.381
 ideal_min=(3.23*cap_nf*(1-cap_tolerance)+.381)*(1-ic_error)
 ideal_max=(3.23*cap_nf*(1+cap_tolerance)+.381)*(1+ic_error)
 # Board leakage is outside the manufacturer's internal IC tolerance. Use
 # minimum published CWD charge current347nA for this additional screen,
 # never multiply internal347/375 again into the ±9.5% IC error.
 extra_min=(3.23*cap_nf*(1-cap_tolerance)*(1-declared_temperature_fraction)+.381)*(1-ic_error)*347/(347+declared_board_leakage_na)
 extra_max=(3.23*(cap_nf*(1+cap_tolerance)*(1+declared_temperature_fraction)+declared_parasitic_nf)+.381)*(1+ic_error)*347/(347-declared_board_leakage_na)
 return {'standard_suffix_S_formula_ms':'3.23*CWD[nF]+0.381','capacitance_nf':cap_nf,'cap_tolerance_fraction':cap_tolerance,
  'IC_programmed_timeout_error_fraction':ic_error,'ideal_nominal_ms':nom,'capacitor_and_IC_only_ms':[ideal_min,ideal_max],
  'declared_external_screen_ms':[extra_min,extra_max],
  'external_assumptions':{'temperature_fraction':declared_temperature_fraction,'added_parasitic_nf':declared_parasitic_nf,'board_leakage_na':declared_board_leakage_na},
  'C0G_temperature_source':'Samsung official MLCC part-code table: C code ±30ppm/K, reference25C, -55..125C; default0.003 uses maximum100K excursion',
  'external_assumptions_physically_verified':False,'CWD_eval_381us_is_NOM_only':True,
  'SET1_enable_setup_150us_is_NOM_only':True,'startup_300us_is_NOM_only':True,'WDI_to_WDO_50ns_is_NOM_only':True,
  'no_maximum_output_assertion_delay_available_in_table':True,
  'watchdog_RESET_WDO_low_pulse_ms':[170,230],
  'maximum_20ms_all_condition_proven':False}

def conditional_withdrawal():
 t=timer_screen();tim=t['declared_external_screen_ms'][1]
 # Retain unknown terms as null. This useful budget is not a substitute for
 # them, and no old IS-1 4.31ms allocation is added as a measured circuit.
 qnom=60400/50000*1e-6;qt=.01+100e-6*30;qmax=qnom*(1+qt)*(1+.062)
 logic_health_ns=6.2
 permission_motion_ns=5.3+5.3+7.9+6.2 # clear route, latch, final gate
 permission_output_ns=6.2+7.9+6.2
 conditional_motor_max_ms=tim+(logic_health_ns+permission_motion_ns)/1e6+qmax*1000+.001*1000
 return {'timeout':t,'qualification_filter_max_us':qmax*1e6,
  'health_buffer_max_ns_at3p3V_50pF':logic_health_ns,
  'motion_permission_clear_path_max_ns_at3p3V_50pF':permission_motion_ns,
  'output_permission_clear_path_max_ns_at3p3V_50pF':permission_output_ns,
  'motor_NO_open_max_ms_at25C_IF5mA_RL200_VDD20':.2,
  'motor_NC_close_max_ms_at25C_IF5mA_RL200_VDD20':1,
  'motor_NC_open_ASSERTION_max_ms_at_same_testpoint':3,
  'AM26C31I_disable_max_ns_at_datasheet_load':16,
  'ISO7762_propagation_max_ns_equal3p3V_test':18.5,
  'TPS274_tDF_EN_to90percent_max_us_at24V_48ohm':33,
  'TPS274_tOFF_EN_to10percent_57us_is_TYP_only':True,
  'known_terms_motor_NC_conditional_ms':conditional_motor_max_ms,
  'remaining_20ms_budget_for_unknown_terms_ms':20-conditional_motor_max_ms,
  'critical_unknown_terms':{'TPS3851_output_assertion_max_s':None,'MC_buffer_loaded_delay_max_s':None,
    'AHCT_permission_restore_loaded_delay_s':None,'direct_series_contact_gate_actual_RC_s':None,
    'photorelay_open_close_0_to55C_actual_IF_and_load_s':None,'TPS274_complete_output_decay_at_all_loads_s':None,
    'PWM_shunt_turnon_actual_gate_RC_s':None,'AO_terminal_capacitance_decay_s':None,
    'LTC2962_fault_assertion_loaded_s':None,'all_partial_power_ramp_paths_s':None},
  'does_not_wait_for_TPS22918_or_motor_feed_rail_removal':True,
  'watchdog_source_gate_fall_crosses_closed_health_contacts_without_waiting_for_their_opening':True,
  'whole_20ms_requirement_met':False,'physical_qualification':False}

def bringup_pin_map(p):
 """Exact reviewed native U1001 balls, not a guessed vendor constraint file."""
 rows={
  'clk':('H3','FPGA_CLK_50M'),'reset_n':('D5','FPGA_USER_RESET_N'),
  'inhibit_n':('A2','RAW_INHIBIT_N'),'rails_ok':('P4','RAILS_OK_FPGA'),
  'spi_cs_n':('M9','HOST_SPI_CS_CMD_N'),'spi_sclk':('D3','HOST_SPI_SCLK'),
  'spi_mosi':('D4','HOST_SPI_MOSI'),'spi_miso':('C3','HOST_SPI_MISO'),
  'motion_request':('B3','FPGA_MOTION_REQUEST'),'endpoint_ready':('C4','FPGA_ENDPOINT_READY'),
  'output_request':('K4','FPGA_OUTPUT_REQUEST'),'progress_m':('E4','FPGA_PROGRESS_M'),
  'progress_o':('L2','FPGA_PROGRESS_O'),'link_fault':('A3','FPGA_LINK_FAULT'),
  'watchdog_fault':('C6','FPGA_WATCHDOG_FAULT'),'inhibit_fault':('A4','FPGA_INHIBIT_FAULT'),
  'timing_fault':('E5','FPGA_TIMING_FAULT'),'pwm[0]':('C2','PWM0_FPGA'),'pwm[1]':('B4','PWM1_FPGA'),
  'process_request[0]':('G1','PEN0_CMD'),'process_request[1]':('F2','PEN1_CMD'),
  'permit_out_request':('F5','PERMIT_OUT_REQ'),'arm_lamp_request':('L4','ARM_LAMP_FPGA'),
  'fast_ports_enable':('M4','FAST_PORTS_ENABLE'),'xf_power_enable':('M6','XF_POWER_ENABLE'),
  'trip_clear':('D6','WATCHDOG_TRIP_CLEAR'),'opi_rearm_m':('J2','OPI_REARM_M'),
  'opi_rearm_o':('H5','OPI_REARM_OUT'),'xs_cs_n':('K16','XS_CS_N'),
  'xs_sync':('L13','XS_SYNC_STROBE'),'xs_sclk':('K15','XS_SCLK'),
  'xs_mosi':('J13','XS_MOSI'),'xs_refclk':('J14','XS_REFCLK'),
  'fast_sr_clk':('A8','FAST_SR_CLK'),'fast_sr_load_n':('C5','FAST_SR_LOAD_N'),
  'health_sr_clk':('C8','HEALTH_SR_CLK'),'health_sr_load_n':('D8','HEALTH_SR_LOAD_N')}
 for name,balls in [('step_out',['P2','J4','J3','K2','L1','H4','G5','F1','E2','D1','E3','F4']),('dir_out',['J5','K3','K1','H1','H2','G3','G2','C1','F3','E1','G4','B1']),('enable_n',['H12','J12','L16','M15','M16','P16','L15','K12','N14','N16','P15','M14'])]:
  for i,ball in enumerate(balls):rows[f'{name}[{i}]']=(ball,f'STEP{i}_FPGA' if name=='step_out' else f'DIR{i}_FPGA' if name=='dir_out' else f'EN{i}_N_FPGA')
 for i,balls in enumerate([('A9','D11','A10','R13'),('E11','E13','D14','T14'),('A15','C15','A13','P12'),('F13','F16','F15','T15')]):
  for sig,ball,net in zip(['iol1_cs_n','iol1_sclk','iol1_mosi','iol1_miso'],balls,['CS_N','SCLK','MOSI','MISO']):rows[f'{sig}[{i}]']=(ball,f'IOL1_L{i}_{net}')
 for i,balls in enumerate([('B5','A7','B7'),('B6','A6','E7')]):
  for sig,ball,ch in zip(['enc_a','enc_b','enc_z'],balls,['A','B','Z']):rows[f'{sig}[{i}]']=(ball,f'ENC{i}_{ch}_FPGA')
 errors=[];seen=set();result={}
 for port,(ball,signal) in rows.items():
  actual=p['U1001']['pins'].get(ball)
  if ball in seen or not actual or actual.rsplit('/',1)[-1]!=signal:errors.append('Native FPGA ball mismatch '+port+'/'+ball)
  seen.add(ball);result[port]={'ball':ball,'native_net':actual,'signal':signal}
 return {'passed':not errors,'errors':errors,'ports':result,
  'internal_ports_not_physical_pads':['spi_miso_oe','io_fault[3:0]'],
  'unused_second_host_select':'B2/HOST_SPI_CS_N is ignored in this single-CS CNC1 diagnostic image; choose the CMD-select device explicitly',
  'never_claims_production_CNC3_or_twelve_axis_capability':True,
  'FPGA_package_fit_and_vendor_constraint_file_qualified':False,
  'IOL1_epoch_requires_new_nonzero_provisioned_value_after_link_restart':True}

def validate(p,model):
 errors=[];checks=0
 def ck(test,msg):
  nonlocal checks
  checks+=1
  if not test:errors.append(msg)
 def exact(r,mpn,pins):
  ck(r in p and p[r]['mpn']==mpn,'Manufacturer MPN '+r)
  if r in p:
   for k,n in pins.items():ck(p[r]['pins'].get(str(k),'ABSENT')==n,'Native pin '+r+'.'+str(k))
 for j,tag in enumerate(('M','O')):
  w=f'U{3001+j}';cwd=f'watchdog_conditioning/WD_{tag}_CWD';health=f'watchdog_conditioning/WD_{tag}_HEALTH_RAW'
  exact(w,'TPS3851G18SDRBT',{1:'IO_3V3',2:cwd,3:None,4:'LOGIC_GND',5:f'WD_{tag}_SET1_BUF',6:f'watchdog_conditioning/WD_{tag}_WDI_BUF',7:health,8:health,9:'LOGIC_GND'})
  cap=model['components'][f'C{3001+j}'];ck(cap.get('capacitance_f')==3.3e-9 and cap.get('tolerance')==.05 and cap.get('dielectric')=='C0G' and cap['mpn']=='CL10C332JB8NNNC','Exact fitted timing capacitor, no extended/4.7nF substitution '+tag)
  exact(f'C{3001+j}','CL10C332JB8NNNC',{1:cwd,2:'LOGIC_GND'})
  request='FPGA_MOTION_REQUEST' if tag=='M' else 'FPGA_OUTPUT_REQUEST'
  exact(f'U{3006+j}','SN74LVC1G08DCKR',{1:request,2:'FPGA_USER_RESET_N',3:'LOGIC_GND',4:f'WD_{tag}_SET1_BUF',5:'IO_3V3'})
  exact(f'U{3003+j}','SN74LVC1G34DBVR',{1:None,2:'FPGA_PROGRESS_M' if tag=='M' else 'watchdog_conditioning/FPGA_PROGRESS_O',3:'LOGIC_GND',4:f'watchdog_conditioning/WD_{tag}_WDI_BUF',5:'IO_3V3'})
  r=f'R{3003+j}';ck(model['components'][r]['resistance_ohm']==4700 and model['components'][r]['mpn']=='CRCW06034K70FKEA','Actual receiving startup 4.7k bias '+tag)
 exact('U3005','SN74LVC2G17DBVR',{1:'watchdog_conditioning/WD_M_HEALTH_RAW',2:'LOGIC_GND',3:'watchdog_conditioning/WD_O_HEALTH_RAW',4:'WD_O_OK',5:'IO_3V3',6:'WD_M_OK'})
 exact('U4003','SN74LVC2G08DCUR',{1:'mc_permission/BASE_OK',2:'WD_M_OK',7:'RAW_INHIBIT_N',5:'RAW_INHIBIT_N',6:'FPGA_ENDPOINT_READY',3:'mc_permission/LATCH_CLEAR_M_N'})
 exact('U4004','SN74LVC1G11DBVR',{1:'mc_permission/BASE_OK',3:'WD_O_OK',6:'FPGA_ENDPOINT_READY',4:'mc_permission/LATCH_CLEAR_O_N'})
 for i,t in [(4005,'M'),(4006,'O')]:
  req='FPGA_MOTION_REQUEST' if t=='M' else 'FPGA_OUTPUT_REQUEST'
  exact(f'U{i}','SN74LVC2G74DCUR',{1:req,2:'IO_3V3',3:None,4:'LOGIC_GND',5:f'mc_permission/ARM_{t}_Q',6:f'mc_permission/LATCH_CLEAR_{t}_N',7:'IO_3V3',8:'IO_3V3'})
 for i,t in [(4014,'M'),(4015,'O')]:exact(f'U{i}','SN74LVC2G74DCUR',{1:f'mc_permission/WD_{t}_FALL_CLK',2:f'mc_permission/WD_{t}_TRIP_D',3:f'mc_permission/WD_{t}_TRIP_N',4:'LOGIC_GND',5:f'mc_permission/WD_{t}_TRIP_Q',6:f'mc_permission/WD_{t}_TRIP_CLEAR_N',7:'IO_3V3',8:'IO_3V3'})
 exact('U4010','SN74LVC1G11DBVR',{1:'TX_PERMIT',3:'mc_permission/OUT_PERMIT',6:'mc_permission/PROCESS_PERMIT_EXT_3V3',4:'mc_permission/PROC_PERMIT'})
 for b,driverpin in [('A',7),('B',3)]:
  stem='motherboard_motors/MOTOR_TX_GATE_';source=stem+'SOURCE_'+b;final=stem+b;mid='motherboard_power_entry/MOTOR_TX_GATE_CONTACT_MID_'+b
  ck(p['U6042']['pins'][str(driverpin)]==source,'Only source output renamed for interposition '+b)
  links=[c for c in p.values() if c['mpn']=='TLP3640A(TPL,E' and c['pins'].get('3') in (source,mid)]
  ck(len(links)==2 and {tuple(c['pins'].get(str(i)) for i in (3,4)) for c in links}=={(source,mid),(mid,final)},'Exactly two series health signal contacts '+b)
  tx=[c for c in p.values() if c['mpn']=='AM26C31IPWR' and c['pins'].get('4')==final]
  ck(len(tx)==(4 if b=='A' else 2),'All six AM26C31 packages use FINAL gates '+b)
  ck(all(c['pins'].get('12')==c['pins'].get('16') for c in tx),'G_N tied own5V while G is permission '+b)
  for i in (range(8) if b=='A' else range(8,12)):
   stemi=f'motherboard_motors/MOTOR{i}'
   pairs=((1,2,3),(4,5,6),(9,10,8),(12,13,11));a,c,y=pairs[i%4]
   gates=[v for v in p.values() if v['mpn']=='SN74LVC00APWR' and v['pins'].get(str(y))==stemi+'_SINK_OFF']
   ck(len(gates)==1 and gates[0]['pins'][str(a)]==stemi+'_EN_ACTIVE' and gates[0]['pins'][str(c)]==final,'Every individual enable is NAND-interlocked with FINAL gate '+str(i))
   no=[v for v in p.values() if v['mpn']=='TLP3640A(TPL,E' and v['pins'].get('3')==f'motherboard_motors/EN{i}_NO']
   nc=[v for v in p.values() if v['mpn']=='TLP4176A(TP,F' and v['pins'].get('3')==f'motherboard_motors/EN{i}_NC']
   ck(len(no)==len(nc)==1 and no[0]['pins']['2']==nc[0]['pins']['1'],'Actual series NO+NC LED chain '+str(i))
 for bank,driver_refs in [('A',(10004,10009)),('B',(10017,10022))]:
  iso=p[f'U{10003 if bank=="A" else 10016}'];n=iso['pins']['12']
  ck(iso['mpn']=='ISO7762FDBQR' and iso['pins']['5']==f'motherboard_do/DO{bank}_DO_EN_LOGIC','Hardware DO enable crosses explicit default-LOW F isolator '+bank)
  for r in driver_refs:ck(p[f'U{r}']['mpn']=='TPS274C65ASRHAR' and p[f'U{r}']['pins']['3']==n,'Actual smart-switch hardware DO_EN endpoint '+str(r))
 # Exhaustive ideal digital equations, evaluated from native physical pins.
 names=['FPGA_CRESET_N','FPGA_USER_RESET_N','mc_permission/DIC_OK_QUALIFIED','mc_permission/EXT_PERMIT_3V3','mc_permission/TAMPER_CLEAR_N','WD_M_OK','WD_O_OK','FPGA_ENDPOINT_READY','FPGA_MOTION_REQUEST','FPGA_OUTPUT_REQUEST','mc_permission/PROCESS_PERMIT_EXT_3V3','mc_permission/PERMIT_OUT_REQ']
 for bits in itertools.product((0,1),repeat=len(names)):
  v=dict(zip(names,bits));c=Permission(p);c.q['U4005']=c.q['U4006']=1;c.v.update(v);c.settle()
  base=all(bits[:5]);tx=int(base and bits[5] and bits[7] and bits[8]);out=int(base and bits[6] and bits[7] and bits[9])
  ck(c.v.get('TX_PERMIT')==tx and c.v.get('mc_permission/OUT_PERMIT')==out and c.v.get('mc_permission/PROC_PERMIT')==int(tx and out and bits[10]),'Exhaustive native permission equation')
  if errors:break
 healthy={n:1 for n in names if n not in ('FPGA_MOTION_REQUEST','FPGA_OUTPUT_REQUEST','mc_permission/PERMIT_OUT_REQ')}
 for fault in names[:8]:
  c=Permission(p);c.drive(**healthy);ck(c.v['TX_PERMIT']==c.v['mc_permission/OUT_PERMIT']==0,'No startup request edge stays disarmed')
  c.drive(FPGA_MOTION_REQUEST=1,FPGA_OUTPUT_REQUEST=1);ck(c.v['TX_PERMIT']==c.v['mc_permission/OUT_PERMIT']==1,'Deliberate healthy ARM/IO_ENABLE edges')
  c.drive(**{fault:0});wanted=(0,1) if fault=='WD_M_OK' else (1,0) if fault=='WD_O_OK' else (0,0)
  ck((c.v['TX_PERMIT'],c.v['mc_permission/OUT_PERMIT'])==wanted,'Actual fault asynchronously withdraws expected permission '+fault)
  c.drive(**{fault:1});ck((c.v['TX_PERMIT'],c.v['mc_permission/OUT_PERMIT'])==wanted,'Fault return cannot automatically rearm '+fault)
  c.drive(FPGA_MOTION_REQUEST=0,FPGA_OUTPUT_REQUEST=0);c.drive(FPGA_MOTION_REQUEST=1,FPGA_OUTPUT_REQUEST=1);ck(c.v['TX_PERMIT']==c.v['mc_permission/OUT_PERMIT']==1,'New deliberate edges required after fault '+fault)
 fpga=p['U1001']['pins'];ck(fpga.get('E4')=='FPGA_PROGRESS_M' and fpga.get('L2')=='watchdog_conditioning/FPGA_PROGRESS_O','Exact independent M/O native FPGA balls')
 return {'passed':not errors,'errors':errors,'native_source_assertions':checks,'six_or_twelve_runtime_claim':False,'physical_qualification':False,'manufacturing_ready':False}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--directory',type=Path,default=DEFAULT);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args()
 if a.output_dir.exists():raise SystemExit('Immutable output directory exists')
 p=read_native(a.directory/'netlist.xml');model=json.loads((a.directory/'design.json').read_text());r=validate(p,model);r['conditional_20ms']=conditional_withdrawal();r['bringup_pin_map']=bringup_pin_map(p)
 if not r['bringup_pin_map']['passed']:r['passed']=False;r['errors'].extend(r['bringup_pin_map']['errors'])
 r['source_files']={str(x.resolve()):sha(x) for x in [a.directory/'netlist.xml',a.directory/'design.json',Path(__file__)]}
 a.output_dir.mkdir(parents=True);(a.output_dir/'review.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({k:v for k,v in r.items() if k not in ('conditional_20ms','source_files')},indent=2));return not r['passed']
if __name__=='__main__':raise SystemExit(main())
