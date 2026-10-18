"""Independent native pin/domain and primary socket-land checks for15xxx."""
from __future__ import annotations
from collections import Counter,defaultdict
import hashlib,json,math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import sys
sys.path.insert(0,str(Path.cwd()/'tools'))
from hardware_build_assembly import parse,children,child,value

ROOT=Path.cwd()
OUT=ROOT/'reports/motherboard-compute-20260930/staging-r02/source'
REPORT=ROOT/'reports/motherboard-compute-20260930'
AUDIT=ROOT/'reports/board-completion-20260930/compute-bay-pin-audit'
SOCKET_MPN='10164227-1001A1RLF'

def native_nodes(tree):
 nodes={};errors=[]
 for net in tree.findall('./nets/net'):
  name=net.attrib['name'].removeprefix('/')
  for node in net.findall('node'):
   key=(node.attrib['ref'],node.attrib['pin'])
   if key in nodes:errors.append('Duplicate native pin '+str(key))
   nodes[key]=name
 return nodes,errors


def validate(tree,model,source_dir=OUT):
 nodes,errors=native_nodes(tree);parts={c.attrib['ref']:c for c in tree.findall('./components/comp')}
 components=model.get('components',{})
 if set(parts)!=set(components):errors.append('Native/model component inventory differs')
 for ref,c in parts.items():
  p=components.get(ref,{})
  native=(c.findtext('value'),c.findtext('footprint',''),c.findtext("./fields/field[@name='MPN']",''))
  if native!=(p.get('value'),p.get('footprint'),p.get('mpn')):errors.append('Native/model MPN/value/footprint differs '+ref)
  prop={x.attrib['name'] for x in c.findall('property')};physical=p.get('physical')
  if physical and {'exclude_from_bom','exclude_from_board'}&prop:errors.append('Physical component excluded '+ref)
  if not physical and (native[1] or native[2] or not {'exclude_from_bom','exclude_from_board'}<=prop):errors.append('Nonphysical boundary became an invented connector '+ref)
  expected=p.get('pins',{});actual={pin:net for (nref,pin),net in nodes.items() if nref==ref}
  if set(expected)!=set(actual):errors.append('Native/model complete pin set differs '+ref)
  for pin,net in expected.items():
   got=actual.get(pin)
   if net is None:
    if not got or not got.startswith('unconnected-'):errors.append('Exact declared NC is actually connected '+ref+'.'+pin)
   elif net!=got:errors.append('Native/model pin net differs '+ref+'.'+pin)
  if physical and (p.get('dnp') or 'dnp' in prop):errors.append('This base compute region has no approved DNP '+ref)
  if physical:
   if ':' not in p.get('footprint',''):errors.append('Physical footprint lacks library '+ref)
   else:
    lib,name=p['footprint'].split(':',1)
    fp=Path(source_dir)/(lib+'.pretty')/(name+'.kicad_mod') if lib=='CNC_COMPUTE' else Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty')/(name+'.kicad_mod')
    if not fp.exists():errors.append('Exact footprint file unavailable '+ref)
    else:
     fpt=parse(fp.read_text(encoding='utf8'));numbered={value(pad[1]) for pad in children(fpt,'pad') if value(pad[1]) and any(value(layer).endswith('.Cu') for layer in child(pad,'layers')[1:])}
     if numbered!=set(expected):errors.append('Exact footprint numbered copper differs from source pins '+ref)
 if model.get('manufacturing_ready') or model.get('physical_qualification'):errors.append('Unproved manufacturing/physical evidence claimed')
 if model.get('compute_som_fitted_on_carrier_bom') or not model.get('module_parts_separate'):errors.append('Commodity compute module duplicated on carrierBOM')
 sockets=[ref for ref,c in components.items() if c.get('mpn')==SOCKET_MPN]
 if sorted(sockets)!=['J15001','J15002']:errors.append('Exactly two physical100-contact sockets required')
 for ref in sockets:
  if not components[ref]['physical'] or len(components[ref]['pins'])!=100:errors.append('Incorrect actual socket count/contact count '+ref)
 matrix=json.loads((AUDIT/'pin-matrix.json').read_text(encoding='utf8'))['pins']
 def contact(pin):return ('J15001',str(pin)) if pin<=100 else ('J15002',str(pin-100))
 for row in matrix:
  if row['cm4_signal']=='GND' and row['cm5_signal']=='GND' and nodes.get(contact(row['global_pin']))!='LOGIC_GND':errors.append('Primary common return not actually connected '+str(row['global_pin']))
 for pin in [77,79,81,83,85,87]:
  if nodes.get(contact(pin))!='SBC_5V':errors.append('Main5V socket contact wrong '+str(pin))
 for pin in [78,84,86]:
  if nodes.get(contact(pin))!='CM_AUX_3V3':errors.append('Pi module-own AUX/VREF contact wrong '+str(pin))
 for pin in [88,90,92,94,96]:
  if not nodes.get(contact(pin),'').startswith('unconnected-'):errors.append('Restricted/unneeded module contact wired without reviewed profile '+str(pin))
 for pin,net in {38:'CM_HOST_SPI_SCLK',40:'CM_HOST_SPI_MISO',44:'CM_HOST_SPI_MOSI',47:'CM_HOST_SPI_CS_CMD_N',54:'CM_HOST_SPI_CS_FB_N',55:'COMPUTE_SERVICE_TX',93:'CM_nRPIBOOT',101:'CM_USB_OTG_ID',103:'CM_USB2_N',105:'CM_USB2_P'}.items():
  if nodes.get(contact(pin))!=net:errors.append('Exact primary common host contact wrong '+str(pin))
 # Hardcoded independently from TI DBV pin tables, not the source generator.
 # Supervisor threshold/open-drain observed rail is not an OS identity signal.
 normative={
  'U15001':('TPS3808G33DBVR',{1:'CM_AUX_RESET_N',2:'LOGIC_GND',3:'CM_AUX_MR_N',4:None,5:'CM_AUX_3V3',6:'CM_AUX_3V3'}),
  'U15002':('SN74LVC1G17DBVR',{1:None,2:'CM_AUX_RESET_N',3:'LOGIC_GND',4:'COMPUTE_3V3_GOOD',5:'IO_3V3'}),
  'U15003':('SN74LVC1G17DBVR',{1:None,2:'FPGA_CRESET_N',3:'LOGIC_GND',4:'CM_FPGA_RAILS_QUALIFIED',5:'IO_3V3'}),
  'U15004':('SN74LVC1G17DBVR',{1:None,2:'FPGA_CDONE',3:'LOGIC_GND',4:'CM_FPGA_CONFIGURED',5:'IO_3V3'}),
  'U15005':('SN74LVC1G10DBVR',{1:'COMPUTE_3V3_GOOD',2:'LOGIC_GND',3:'CM_FPGA_RAILS_QUALIFIED',4:'CM_HOST_OE_N',5:'IO_3V3',6:'CM_FPGA_CONFIGURED'}),
  'U15006':('SN74LVC1G125DBVR',{1:'CM_HOST_OE_N',2:'CM_HOST_SPI_SCLK',3:'LOGIC_GND',4:'CM_FWD_SCLK',5:'IO_3V3'}),
  'U15007':('SN74LVC1G125DBVR',{1:'CM_HOST_OE_N',2:'CM_HOST_SPI_MOSI',3:'LOGIC_GND',4:'CM_FWD_MOSI',5:'IO_3V3'}),
  'U15008':('SN74LVC1G125DBVR',{1:'CM_HOST_OE_N',2:'CM_HOST_SPI_CS_FB_N',3:'LOGIC_GND',4:'CM_FWD_CS_FB_N',5:'IO_3V3'}),
  'U15009':('SN74LVC1G125DBVR',{1:'CM_HOST_OE_N',2:'CM_HOST_SPI_CS_CMD_N',3:'LOGIC_GND',4:'CM_FWD_CS_CMD_N',5:'IO_3V3'}),
  'U15010':('SN74LVC1G125DBVR',{1:'CM_HOST_OE_N',2:'HOST_SPI_MISO',3:'LOGIC_GND',4:'CM_RET_MISO',5:'CM_AUX_3V3'}),
  'U15011':('219-3MSTRF',{1:'COMPUTE_PROFILE0',2:'COMPUTE_PROFILE1',3:'COMPUTE_PROFILE2',4:'IO_3V3',5:'IO_3V3',6:'IO_3V3'})}
 for ref,(mpn,mapping) in normative.items():
  if components.get(ref,{}).get('mpn')!=mpn:errors.append('Unreviewed critical MPN '+ref)
  for pin,net in mapping.items():
   got=nodes.get((ref,str(pin)))
   if net is None:
    if not got or not got.startswith('unconnected-'):errors.append('Critical unusedpin not NC '+ref+'.'+str(pin))
   elif got!=net:errors.append('Independent critical native pin/domain mismatch '+ref+'.'+str(pin))
 pairs=defaultdict(list)
 for ref,p in components.items():
  if p.get('kind')=='R' and p.get('physical'):pairs[frozenset(p['pins'].values())].append((ref,p.get('resistance_ohm')))
 required=[('CM_AUX_RESET_N','CM_AUX_3V3',10000),('CM_AUX_MR_N','CM_AUX_3V3',10000),('CM_AUX_3V3','LOGIC_GND',1000),('CM_HOST_OE_N','IO_3V3',10000),('FPGA_CRESET_N','LOGIC_GND',10000),('FPGA_CDONE','LOGIC_GND',47000)]
 for raw,suffix,default in [('CM_HOST_SPI_SCLK','SCLK','LOW'),('CM_HOST_SPI_MOSI','MOSI','LOW'),('CM_HOST_SPI_CS_FB_N','CS_FB_N','HIGH'),('CM_HOST_SPI_CS_CMD_N','CS_CMD_N','HIGH')]:
  required.extend([(raw,'CM_AUX_3V3' if default=='HIGH' else 'LOGIC_GND',10000),('HOST_SPI_'+suffix,'IO_3V3' if default=='HIGH' else 'LOGIC_GND',10000),('CM_FWD_'+suffix,'HOST_SPI_'+suffix,33)])
 required.extend([('CM_RET_MISO','CM_HOST_SPI_MISO',33),('HOST_SPI_MISO','LOGIC_GND',10000),('CM_HOST_SPI_MISO','LOGIC_GND',10000)])
 required.extend([(f'COMPUTE_PROFILE{i}','LOGIC_GND',10000) for i in range(3)])
 for a,b,ohm in required:
  if not any(v==ohm for _,v in pairs.get(frozenset([a,b]),[])):errors.append('Actual default/series resistor absent '+a+'/'+b)
 for pin,net in nodes.items():
  if pin[0].startswith('U') and components.get(pin[0],{}).get('kind')=='BUF' and nodes.get((pin[0],'5'))=='IO_3V3':
   pass
 # Protect against exact former reset-output-contention class: parent reset/
 # configuration observations are input-only in this carrier, never driven.
 for ref,c in parts.items():
  for net in tree.findall('./nets/net'):
   if net.attrib['name'].removeprefix('/') in ['FPGA_CRESET_N','FPGA_CDONE','COMPUTE_SERVICE_TX','CM_nRPIBOOT']:
    for n in net.findall('node'):
     if n.attrib['ref'].startswith('U') and n.attrib.get('pintype') in ['output','tri_state','open_collector','power_out']:
      errors.append('Carrier drives an observation/read-only/recovery endpoint '+n.attrib['ref']+'.'+n.attrib['pin'])
 selector=model.get('selector',{})
 if selector.get('DIP_controls_electrical_power_or_permission') or selector.get('automatic_hardware_ID_implemented') or selector.get('software_profile_implemented'):errors.append('Selector grants unimplemented authority/identity')
 for profile in model.get('profiles',{}).values():
  if profile.get('target_image_and_pinmux_qualified') or profile.get('full_electrical_qualification') or profile.get('machine_use_enabled'):errors.append('Unproved module profile qualified')
 pwr=model.get('module_power',{})
 for k,want in [('input','SBC_5V'),('ground','LOGIC_GND'),('aux3v3_max_total_a',.6),('aux3v3_max_per_contact_a',.3),('full_capacity_qualified',False)]:
  if pwr.get(k)!=want:errors.append('Modulepower contract changed '+k)
 rating=model.get('socket_rating',{})
 if (rating.get('all_contacts_simultaneous_a'),rating.get('blanket_rating_total_a'),rating.get('planned_2p5A_selective_contact_rating_or_temperature_qualification'))!=(.3,1.8,False):errors.append('Socket blanketrating/qualification boundary changed')
 sd_errors=validate_sd(tree,model,source_dir);errors.extend(sd_errors)
 land_errors=validate_lands(source_dir);errors.extend(land_errors)
 hashes=model.get('input_hashes',{})
 for name,want in hashes.items():
  p=ROOT/name
  if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=want:errors.append('Primary/source input changed '+name)
 return dict(ok=not errors,errors=sorted(set(errors)),physical_count=sum(p.get('physical',False) for p in components.values()),purchased_count=sum(p.get('physical',False) and p.get('kind')!='TP' for p in components.values()),bare_test_pad_count=sum(p.get('kind')=='TP' for p in components.values()),socket_count=len(sockets),native_pin_count=len(nodes),native_net_count=len(tree.findall('./nets/net')),NC_count=sum(v.startswith('unconnected-') for v in nodes.values()),raw_external_interfaces_unimplemented=4,source_scope_only=True,physical_validation=False,manufacturing_ready=False)


def validate_sd(tree,model,source_dir):
 nodes,errors=native_nodes(tree);parts=model['components']
 normative={
 'J15003':('503398-1892',{1:'SD_PORT_DAT2',2:'SD_PORT_DAT3',3:'SD_PORT_CMD',4:'SD_PORT_3V3',5:'SD_PORT_CLK',6:'LOGIC_GND',7:'SD_PORT_DAT0',8:'SD_PORT_DAT1',9:'LOGIC_GND',10:'SD_CARD_PRESENT_N',11:'LOGIC_GND'}),
 'U15012':('TPS2553DBVR',{1:'CM_AUX_3V3',2:'LOGIC_GND',3:'CM_SD_PWR_ON',4:'SD_POWER_FAULT_N',5:'SD_ILIM',6:'SD_PORT_3V3'}),
 'U15013':('TPS3808G30DBVR',{1:'SD_PORT_POWER_GOOD',2:'LOGIC_GND',3:'SD_PORT_MR_N',4:'SD_PORT_CT',5:'SD_PORT_3V3',6:'CM_AUX_3V3'}),
 'U15014':('SN74LVC1G00DBVR',{1:'CM_SD_PWR_ON',2:'SD_PORT_POWER_GOOD',3:'LOGIC_GND',4:'SD_BUS_OE_N',5:'CM_AUX_3V3'}),
 'U15015':('TS3A27518EPWR',{1:'SD_PORT_CMD',2:'SD_PORT_CLK',3:None,4:'SD_CLK_DAMPED',5:'LOGIC_GND',6:'CM_SD_CMD',7:'CM_SD_DAT0',8:'CM_AUX_3V3',9:'CM_SD_DAT1',10:'CM_SD_DAT2',11:'SD_UNUSED_NO1',12:'CM_SD_DAT3',13:'SD_UNUSED_NO2',14:'LOGIC_GND',15:'SD_UNUSED_NO3',16:'SD_UNUSED_NO6',17:'SD_UNUSED_NO4',18:'SD_UNUSED_NO5',19:'SD_PORT_DAT2',20:'SD_BUS_OE_N',21:'SD_PORT_DAT1',22:'SD_PORT_DAT3',23:'SD_PORT_DAT0',24:'LOGIC_GND'}),
 'U15016':('TPD4E05U06DQAR',{1:'SD_PORT_CLK',2:'SD_PORT_CMD',3:'LOGIC_GND',4:'SD_PORT_DAT0',5:'SD_PORT_DAT1',6:None,7:None,8:'LOGIC_GND',9:None,10:None}),
 'U15017':('TPD4E05U06DQAR',{1:'SD_PORT_DAT2',2:'SD_PORT_DAT3',3:'LOGIC_GND',4:None,5:None,6:None,7:None,8:'LOGIC_GND',9:None,10:None})}
 for ref,(mpn,pins) in normative.items():
  if parts.get(ref,{}).get('mpn')!=mpn:errors.append('Independent SD criticalMPN '+ref)
  for pin,net in pins.items():
   actual=nodes.get((ref,str(pin)))
   if net is None:
    if not actual or not actual.startswith('unconnected-'):errors.append('SD genuineunusedpinnotNC '+ref+'.'+str(pin))
   elif actual!=net:errors.append('IndependentSD mfrpin/domain mismatch '+ref+'.'+str(pin))
 pairs=defaultdict(list)
 for ref,c in parts.items():
  if c.get('kind')=='R':pairs[frozenset(c['pins'].values())].append((ref,c.get('resistance_ohm'),c.get('tolerance')))
 required=[('SD_ILIM','LOGIC_GND',76800),('CM_SD_PWR_ON','CM_AUX_3V3',10000),('SD_PORT_3V3','LOGIC_GND',1000),('SD_PORT_POWER_GOOD','CM_AUX_3V3',10000),('SD_PORT_MR_N','CM_AUX_3V3',10000),('SD_BUS_OE_N','CM_AUX_3V3',10000),('CM_SD_CLK','SD_CLK_DAMPED',33),('SD_CARD_PRESENT_N','CM_AUX_3V3',10000)]
 required.extend(('SD_UNUSED_NO'+str(i),'LOGIC_GND',49.9) for i in range(1,7))
 required.extend(('SD_PORT_'+x,'SD_PORT_3V3',10000) for x in ['CMD','DAT0','DAT1','DAT2','DAT3'])
 for a,b,r in required:
  if not any(ohm==r and tol==.01 for ref,ohm,tol in pairs.get(frozenset([a,b]),[])):errors.append('SD actualdefault/currentlimit/termination absent '+a+'/'+b)
 ct=[c for c in parts.values() if c.get('kind')=='C' and set(c['pins'].values())=={'SD_PORT_CT','LOGIC_GND'}]
 if len(ct)!=1 or not math.isclose(ct[0].get('capacitance_f',0),130e-12,rel_tol=1e-9):errors.append('SD actual130pF CT missing')
 sd=model.get('sd_port',{});imin=25230/(76.8*1.01)**1.016/1000;imax=22980/(76.8*.99)**.94/1000
 if not math.isclose(sd.get('current_limit_min_a',0),imin,rel_tol=1e-12) or not math.isclose(sd.get('current_limit_max_a',0),imax,rel_tol=1e-12) or not .3<imin<imax<.4:errors.append('SD worstcasecurrentcap equations/tolerance notclosed')
 if sd.get('qualified_cards') or sd.get('boot_image_verified') or sd.get('physical_qualification') or sd.get('hot_swap_qualified') or sd.get('diagnostics_allocated') or sd.get('external_injection_or_ideal_reverse_blocking_claim'):errors.append('SD unprovedboot/hotswap/profile/power claim')
 if not sd.get('cardpoweroff_signal_isolation_implemented'):errors.append('SD off-power signal isolation omitted')
 for suffix in ['CLK','CMD','DAT0','DAT1','DAT2','DAT3']:
  host='CM_SD_'+suffix;card='SD_PORT_'+suffix
  if host==card:errors.append('SD host/card nets notisolated')
  for ref,c in parts.items():
   if c.get('physical') and c.get('kind')!='SD_MUX' and {host,card}<=set(c['pins'].values()) and c.get('kind') not in ['R']:
    errors.append('SD bypasses actualbusisolation '+ref)
 # Every signal path is checked in nativeXML, not model-only metadata.
 source=REPORT/'sources/cm5io-rev2-official/CM5IO.pretty/SDCARD_MOLEX_503398-1892.kicad_mod'
 official=parse(source.read_text(encoding='utf8'));actual=parse((Path(source_dir)/'CNC_COMPUTE.pretty/Molex_503398-1892_SD.kicad_mod').read_text(encoding='utf8'))
 def geometry(t):return sorted((value(p[1]),tuple(child(p,'at')[1:]),tuple(child(p,'size')[1:])) for p in children(t,'pad') if value(p[1]))
 if geometry(official)!=geometry(actual):errors.append('Molex sourcebackedland/pin orientation differs')
 e=parse((Path(source_dir)/'CNC_COMPUTE.pretty/TI_DQA0010A_TPD4E05U06.kicad_mod').read_text(encoding='utf8'))
 for p in children(e,'pad'):
  n=int(value(p[1]));x,y=map(float,child(p,'at')[1:3]);sx,sy=map(float,child(p,'size')[1:3]);expectedx=-.4175 if n<=5 else .4175;expectedy=(-1+(n-1)*.5) if n<=5 else (1-(n-6)*.5)
  if not all(math.isclose(a,b,abs_tol=1e-9) for a,b in [(x,expectedx),(y,expectedy),(sx,.565),(sy,.4 if n in [3,8] else .2)]):errors.append('TI primary DQA ground/pitch/land mismatch')
 return errors


def validate_lands(source_dir=OUT):
 errors=[];source=REPORT/'sources/cm5io-rev2-official/CM5IO.pretty/Raspberry-Pi-5-Compute-Module.kicad_mod';original=parse(source.read_text(encoding='utf8'));op={int(value(p[1])):p for p in children(original,'pad') if value(p[1])}
 for idx,name,cx in [(0,'Amphenol_10164227_1001_CM_A',-.5),(1,'Amphenol_10164227_1001_CM_B',33.5)]:
  fp=Path(source_dir)/'CNC_COMPUTE.pretty'/(name+'.kicad_mod')
  if not fp.exists():errors.append('Socket derivedland file missing '+name);continue
  t=parse(fp.read_text(encoding='utf8'));pads={int(value(p[1])):p for p in children(t,'pad') if value(p[1])}
  if set(pads)!=set(range(1,101)):errors.append('Socket exact100land set wrong '+name);continue
  for i,p in pads.items():
   primary=op[i+idx*100];at=child(p,'at');oa=child(primary,'at');want=(float(oa[1])-cx,float(oa[2])+21.5,float(oa[3]))
   if any(abs(float(v)-w)>1e-8 for v,w in zip(at[1:],want)) or child(p,'size')!=child(primary,'size') or child(p,'layers')!=child(primary,'layers'):errors.append('Socket land mirror/pitch/size/orientation changed '+name+'.'+str(i))
  holes=[p for p in children(t,'pad') if not value(p[1])]
  if len(holes)!=2 or any(p[2]!='np_thru_hole' or child(p,'drill')[1]!='2.7' for p in holes):errors.append('Socket module mountingholes wrong '+name)
 dip=Path(source_dir)/'CNC_COMPUTE.pretty/CTS_219-3M_GullWing.kicad_mod'
 if not dip.exists():errors.append('Exact CTSland file missing')
 else:
  t=parse(dip.read_text(encoding='utf8'));pads={int(value(p[1])):p for p in children(t,'pad')}
  expected={1:(-2.54,4.3),2:(0,4.3),3:(2.54,4.3),4:(2.54,-4.3),5:(0,-4.3),6:(-2.54,-4.3)}
  if set(pads)!=set(expected):errors.append('CTS sixland set changed')
  for i,xy in expected.items():
   if i in pads and (tuple(map(float,child(pads[i],'at')[1:3]))!=xy or tuple(map(float,child(pads[i],'size')[1:3]))!=(1.13,2.44)):errors.append('CTS primary land dimensions changed '+str(i))
 return errors


def main():
 model=json.loads((OUT/'design.json').read_text(encoding='utf8'));report=validate(ET.parse(OUT/'netlist.xml'),model)
 (REPORT/'staging-r02/validation-r02.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2));return 0 if report['ok'] else 1
if __name__=='__main__':sys.exit(main())
