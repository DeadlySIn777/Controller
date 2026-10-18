"""Write an unreleased source-level power proposal; does not generate CAD."""
import json
from pathlib import Path

R=Path(__file__).resolve().parent
old=json.loads((R.parent/'r0_2/power_spec.json').read_text())
parts=[p for p in old['parts'] if p['reference'] in ['F20','D20','Q20','D21','R20']]

def add(ref,value,mpn,mfr,footprint,kind,pins,labels=None,types=None,source='',note=''):
    labels=labels or {str(i):str(i) for i in pins}
    types=types or {str(i):'passive' for i in pins}
    parts.append(dict(reference=ref,value=value,mpn=mpn,manufacturer=mfr,footprint=footprint,kind=kind,pins=pins,pin_names=labels,pin_labels=labels,pin_types=types,datasheet=source,source=source,notes=note))

diode_source='https://assets.nexperia.com/documents/data-sheet/PMEG6010CEH.pdf'
def diode(ref,cathode,anode,note):
    add(ref,'60V Schottky','PMEG6010CEH,115','Nexperia','Diode_SMD:D_SOD-123F','diode',{'1':cathode,'2':anode},{'1':'K','2':'A'},source=diode_source,note=note)
def resistor(ref,value,mpn,n1,n2,size='0603',mfr='Yageo',source='https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L.pdf',note=''):
    add(ref,value,mpn,mfr,f'Resistor_SMD:R_{size}_{dict(_0603="1608",_0805="2012",_1206="3216")["_"+size]}Metric','resistor',{'1':n1,'2':n2},source=source,note=note)
def cap(ref,value,mpn,n1,n2,size,source,note=''):
    add(ref,value,mpn,'Samsung Electro-Mechanics',f'Capacitor_SMD:C_{size}_{dict(_0603="1608",_0805="2012",_1206="3216")["_"+size]}Metric','capacitor',{'1':n1,'2':n2},source=source,note=note)

diode('D22','BUCK_VIN','V_EXT_PROT','Isolates buck input reservoir from external-input collapse; buck output reverse-energy behavior remains a test gate.')
add('U20','MP2459 adjustable buck ~5.06V','MP2459GJ-Z','Monolithic Power Systems','Package_TO_SOT_SMD:TSOT-23-6','ic',{'1':'BUCK_BST','2':'GND','3':'BUCK_FB','4':'BUCK_EN','5':'BUCK_VIN','6':'BUCK_SW'},{'1':'BST','2':'GND','3':'FB','4':'EN','5':'IN','6':'SW'},{'1':'passive','2':'power_in','3':'input','4':'input','5':'power_in','6':'power_out'},'https://www.monolithicpower.com/media/document/MP2459_r1.01.pdf','Regulated 5V mode is limited to nominal12/24V external power. At nominal5V, select EXT; the unselected buck can be below its4.5V specified operating input.')
add('L20','15uH 20% Isat2.0A','SRN5040-150M','Bourns','Adapter_R03:L_Bourns_SRN5040','inductor',{'1':'BUCK_SW','2':'V5_REG'},source='https://www.bourns.com/docs/product-datasheets/srn5040.pdf',note='Custom footprint required: two1.5x4.0mm rectangular pads at x=+/-1.8mm. Manufacturer recommended overall pad span5.1mm. Body5.0+/-0.2mm square, height4.0mm maximum. DCRmax0.096ohm; Irms1.8A; Isat2.0A at30% inductance drop,25C. Not a claim that the complete converter supplies these currents.')
diode('D23','BUCK_SW','GND','Asynchronous buck catch diode. Native footprint K=pad1, A=pad2.')
sam='https://product.samsungsem.com/mlcc/'
cap('C20','4.7uF 50V X7R 10%','CL31B475KBHNNNE','BUCK_VIN','GND','1206',sam+'CL31B475KBHNNN.do','Datasheet example uses4.7uF nominal input. Typical biased capacitance ~2.03uF at26.4V; screen ~1.55uF after10% tolerance and15% temperature. Not a guaranteed minimum; validate input ripple/source impedance and surge.')
cap('C21','100nF 50V X7R 10%','CL10B104KB8NNNC','BUCK_VIN','GND','0603',sam+'CL10B104KB8NNN.do','Place immediately at U20 IN/GND hot loop.')
cap('C22','100nF 50V X7R 10%','CL10B104KB8NNNC','BUCK_BST','BUCK_SW','0603',sam+'CL10B104KB8NNN.do','Bootstrap capacitor; differential working voltage ~5V. Both pads switch at input common mode.')
cap('C23','22uF 25V X5R 10%','CL31A226KAHNNNE','V5_REG','GND','1206',sam+'CL31A226KAHNNN.do','Manufacturer buck application recommends22uF nominal output. Samsung typical curve13.19uF at5.2344V; screening10.09uF with tolerance/temperature. Loop/load-transient validation pending.')
resistor('R21','124k 0.1%','RT0603BRD07124KL','V5_REG','BUCK_FB',source='https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RT_1_to_0.01_RoHS_L_17.pdf',note='Use manufacturer5V feedback values, preserving its suggested feedback impedance;0.1% reduces arithmetic output spread.')
resistor('R22','23.7k 0.1%','RT0603BRD0723K7L','BUCK_FB','GND',source='https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RT_1_to_0.01_RoHS_L_17.pdf')
resistor('R23','10k 1% 0.125W','RC0805FR-0710KL','BUCK_VIN','BUCK_EN','0805',note='Pull-up to5.1V external clamp; at26.4V dissipation~46mW.45.4V transient dissipates~0.16W briefly; pulse qualification required.')
add('D24','5.1V EN clamp','BZT52C5V1-7-F','Diodes Incorporated','Diode_SMD:D_SOD-123','zener',{'1':'BUCK_EN','2':'GND'},{'1':'K','2':'A'},source='https://www.diodes.com/datasheet/download/BZT52Cxx.pdf',note='EN absolute maximum6V. Clamp specified4.8..5.4V at5mA, temperature coefficient-2.7..+1.2mV/C. Available current remains below5mA within45.4V transient envelope. This avoids an unprotected100k pull-up to high VIN; do not use5.6V substitute. Startup EN-threshold/current are typical-only in MP2459, requiring measurement.')
resistor('R24','100k 1%','RC0603FR-07100KL','BUCK_EN','GND',note='Discharges EN and provides defined state after reservoir decay.')
diode('D25','V5_SELECT','V5_REG','Reverse block from selected external12/24V or residual COM charge into buck output. 5V label is nominal; actual output includes diode drop.')
resistor('R25','10k 1%','RC0603FR-0710KL','COM_PLUS','GND',note='Selected-output discharge.26.4V ->2.64mA/~69.7mW; use0.1W0603 with ambient≤50C target, temperature verification. This bleeder does not make powered selector operation approved.')
resistor('R26','82ohm 1% 0.66W pulse-tolerant','ERJ-P08F82R0V','COM_PLUS','IND_FEED_R','1206','Panasonic','https://industrial.panasonic.com/ww/products/pt/small-and-high-power-chip-resistors/models/ERJP08F82R0V','Limits indicator reservoir inrush. At26.4V/81.18ohm, ideal initial maximum0.3252A before diode drop, below BAT46W350mA repetitive-pulse limit.45.4V transient yields0.5593A, below750mA/10ms single-surge rating. Pulse-energy and repetition qualification remain open. At5mA DC, drop<=0.4141V. Manufacturer format ERJP08F82R0V; distributor format ERJ-P08F82R0V.')
add('D26','100V indicator input isolation','BAT46W-7-F','Diodes Incorporated','Diode_SMD:D_SOD-123','diode',{'1':'V_IND_IN','2':'IND_FEED_R'},{'1':'K','2':'A'},source='https://www.diodes.com/datasheet/download/BAT46W.pdf',note='Input-isolation diode, not output reverse-clamp. VFmax0.45V at10mA25C. Reverse leakage max7.5uA at10V60C and15uA at50V60C. Cold drop and reservoir decay to be measured.')
cap('C25','4.7uF 50V X7R 10%','CL31B475KBHNNNE','V_IND_IN','GND','1206',sam+'CL31B475KBHNNN.do','Dedicated input hold-up for AP7375 collapse protection. Near3.3V typical4.59uF, screen3.51uF. Do not substitute a smaller/poorer-bias capacitor without repeating decay analysis.')
add('U21','AP7375 3.3V indicator LDO','AP7375-33SA-7','Diodes Incorporated','Package_TO_SOT_SMD:SOT-23','ic',{'1':'V_IND_IN','2':'V_IND_3V3','3':'GND'},{'1':'IN','2':'OUT','3':'GND'},{'1':'power_in','2':'power_out','3':'power_in'},'https://www.diodes.com/datasheet/download/AP7375.pdf','3..45V operating,55V input absolute. VOUT−VIN<=0.3V absolute; not reverse-protected. D26/C25/R27 mitigate input collapse but are not a tested guarantee. No externally powered programmer or other V_IND_3V3 source allowed. Input≈3.65V minimum screen at5mA low buck corner; dropmax50mV at10mA25C. Indicator circuit uses internal ADC reference and≤5MHz CPU.')
cap('C26','2.2uF 25V X7R 10%','CL21B225KAFNNNE','V_IND_3V3','GND','0805',sam+'CL21B225KAFNNN.do','AP7375 minimum effective output1uF. Typical2.056uF at3.3V; tolerance/temperature screening1.573uF. Only100nF MCU rail decoupling additional. Total output capacitance must remain bounded for input-collapse analysis.')
resistor('R27','4.7k 1%','RC0603FR-074K7L','V_IND_3V3','GND',note='Bleeds indicator rail (~0.70mA) and dominates input diode/LDO leakage during collapse. Included in5mA total indicator budget.')
resistor('R28','330ohm 1% 0.125W','RC0805FR-07330RL','V5_REG','GND','0805',note='Buck output bleed even when EXT is selected. Draws<=15.90mA and dissipates<=82.6mW at5.1938V with1% resistance tolerance. Near2.65V UVLO, output discharge7.9508mA with Cin3.4uF/Cout27.83uF allows input drain0.9714mA, exceeding25C IQ+EN+diode screen~0.927mA. Actual IC current below UVLO and SW<=VIN+0.3V must be measured; not a universal reverse-safe claim.')

for p in parts:
    if p['reference']=='R20':
        p['datasheet']='https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L.pdf'
        p['source']=p['datasheet']
    p.setdefault('source',p.get('datasheet',''))
    p.setdefault('pin_labels',p.get('pin_names',{}))
    p.setdefault('unit_price_usd_100',None)
    p.setdefault('procurement_status','Not ordered; price/stock and Amazon exact-MPN availability not confirmed.')

spec={
 'schema_version':1,'revision':'r0.3-power-proposal-3','date':'2026-10-06',
 'status':'UNRELEASED PROPOSED POWER CIRCUIT - SOURCE REVIEW ONLY',
 'manufacturing_ready':False,'native_erc_performed':False,'physical_measurements_performed':False,
 'shared_nets':['EXT_RAW','V_EXT_PROT','V5_REG','V5_SELECT','COM_PLUS','V_IND_3V3','GND'],
 'ownership':'Power input/protection/buck/indicator LDO and COM bleeder. J4/SW1/header/output/sinks owned by logic_spec; MCU/LEDs/ADC/programming owned by indicator_spec.',
 'operating_contract':{'terminal_range_v':[4.75,26.4],'nominal_inputs_v':[5,12,24],'five_volt_external_requires_EXT':True,'regulated_buck_requires_nominal_12_or_24_input':True,'buck_output_design_load_ma':90,'signal_common_max_ma':60,'indicator_total_budget_ma':5,'nominal_ambient_target_c':[0,50],'selector_change_only_power_off_and_discharged':True,'no_48v_input':True,'not_universal_driver_interface':True},
 'topology':['EXT_RAW -> F20 -> V_EXT_FUSED; D20 bidirectional TVS from fused node toGND.','Q20 reverse-polarity P-FET: drain=fused input, source=V_EXT_PROT,12V source-to-gate clamp and100k gate pull-down.','V_EXT_PROT -> D22 -> BUCK_VIN -> MP2459/L20 -> V5_REG -> D25 -> V5_SELECT; R28 discharges V5_REG in both selector positions.','SW1 selects V5_SELECT or V_EXT_PROT to COM_PLUS.','COM_PLUS ->82ohm R26 -> BAT46W D26 -> C25/V_IND_IN -> AP7375 -> V_IND_3V3.'],
 'voltage_screen':{'buck_nominal_v':0.812*(1+124/23.7),'buck_25c_ref_resistor_min_v':0.792*(1+124*.999/(23.7*1.001)),'buck_25c_ref_resistor_max_v':0.832*(1+124*1.001/(23.7*.999)),'selected_buck_voltage_drop_allowance_25c_v':0.4,'selected_buck_low_25c_screen_v':0.792*(1+124*.999/(23.7*1.001))-.4,'warning':'FB bias current has typical value only; regulator temperature, diode cold behavior, cable losses and switching ripple need measured corners. D25 has no minimum forward-voltage guarantee, so do not claim COM<=5.0V across all corners. These are arithmetic screens, not guaranteed total output bounds.'},
 'reverse_collapse_basis':{'strategy':'Series diode isolates indicator input reservoir; input capacitance near critical3.3V exceeds worst nominal/tolerance/temperature output capacitance plus100n MCUdecap. R27 ensures output discharge even while MCU/BOD off.','input_screen_uf_near_3v3':3.51,'output_nominal_tolerance_temperature_upper_uf_including_100nf':(2.2+.1)*1.1*1.15,'constraints':['No external power into V_IND_3V3/UPDI. Programmer voltage is target-powered reference only.','No added rail bulk capacitance without review.','ADC filter connected to ADC, not directly to VDD; its bounded injection is included by indicator reviewer.','AP7375 VOUT−VIN<=0.3V must be scoped through abrupt COM short, ramp-down, selector dead interval and repeated brownout.','An input capacitor does not qualify arbitrary regulator reverse-current behavior; retain this explicit prototype gate.']},
 'buck_collapse_basis':{'strategy':'D22 isolates input capacitor, and330ohm R28 continuously discharges output including when EXT is selected.','input_capacitance_screen_near_critical_voltage_uf':3.4,'output_capacitance_upper_screen_uf':27.83,'input_decay_current_allowance_ma_at_2v65':2.65/333.3*3.4/27.83*1000,'estimated_25c_input_drain_screen_ma':0.927,'qualification':'MP2459 SW absolute maximum is VIN+0.3V. IQ is specified at12V/25C, not across/below UVLO; scope SW,VIN,VOUT on shutdown in both selector modes. Screens are not manufacturer guarantees.'},
 'release_gates':['Cross-check all part pinouts and footprint lands against current primary drawings.','Capture manufacturer capacitor curves and final pulse-energy/current screening.','ERC/DRC/native netlist parity and one-sided mechanical packing still not performed.','Bench90mA buck startup/regulation/ripple/thermal,0..50C target and12/24V nominal input corners.','Scope buck SW versus VIN through abrupt input collapse and shutdown with EXT selected.','Input reverse polarity, current-limited shorts, TVS/fuse pulse coordination and ringing below absolute ratings.','Indicator input-collapse and ADC prebias behavior; no programmer backfeed.','Exact procurement and complete landed cost inclPCB,harness,labor,yield,shipping/taxes.'],
 'parts':parts,
 'cost_status':{'complete_bom_cost_known':False,'landed_target_usd':6,'retail_ceiling_usd':15,'pcb_parent_browser_estimate_100_hasl_usd_each':0.9876,'pcb_parent_browser_estimate_100_enig_usd_each':1.221,'pcb_note':'Parent read provisionalPCBWay calculator for50x15.24mm,purple,two layers; includesDHL beforetax/duties. NofinalCADupload ororder. Earlier0.65–1.10PCB+harness+freight allowance is withdrawn.'}
}
(R/'power_spec.json').write_text(json.dumps(spec,indent=2)+'\n')
print('Wrote',R/'power_spec.json',len(parts),'proposed parts')
