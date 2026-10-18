"""Independent native checks for purchased ESP board power and receive-only sockets."""
import argparse,json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'hardware/motherboard_esp_socket'
PRIMARY_IC_PINS={
 'U16001':{'1':'IN','2':'GND','3':'EN','4':'FAULT_N','5':'ILIM','6':'OUT'},
 'U16002':{'1':'VIN','2':'GND','3':'CE','4':'NC','5':'ST','6':'VOUT'},
 'U16003':{'1':'NC','2':'A','3':'GND','4':'Y','5':'VCC'}}

def validate(tree,model):
 errors=[];actual={};parts=model['components']
 for net in tree.findall('.//nets/net'):
  for node in net.findall('node'):
   k=(node.attrib['ref'],node.attrib['pin'])
   if k in actual:errors.append('Duplicate electrical pad '+repr(k))
   actual[k]=(net.attrib['name'],net.attrib['code'])
 native={p.attrib['ref']:p for p in tree.findall('.//components/comp') if p.attrib['ref'] in parts}
 if set(native)!=set(parts):errors.append('Exact physical inventory mismatch')
 for ref,c in parts.items():
  if ref not in native:continue
  n=native[ref]
  for field,value in [('value',c['value']),('footprint',c['footprint'])]:
   if n.findtext(field)!=value:errors.append('Native '+field+' mismatch '+ref)
  if n.findtext("./fields/field[@name='MPN']")!=c['mpn']:errors.append('Native MPN mismatch '+ref)
  for pin,net in c['pins'].items():
   observed=actual.get((ref,pin),('MISSING',''))[0]
   if net is None:
    if not observed.startswith('unconnected-'):errors.append('Declared NC is connected '+ref+'.'+pin)
   elif observed!='/'+net:errors.append('Native pin/net mismatch '+ref+'.'+pin)
  expected=set(c['pins']);observed={p for r,p in actual if r==ref}
  if expected!=observed:errors.append('Physical pad inventory mismatch '+ref)
 libparts={(p.attrib['lib'],p.attrib['part']):{n.attrib['num']:n.attrib['name'] for n in p.findall('./pins/pin')} for p in tree.findall('.//libparts/libpart')}
 for ref,pins in PRIMARY_IC_PINS.items():
  lib=native[ref].find('libsource')
  if libparts[lib.attrib['lib'],lib.attrib['part']]!=pins:errors.append('Manufacturer IC pin function mismatch '+ref)
 def same(*keys):return len({actual.get(k) for k in keys})==1 and actual.get(keys[0]) is not None
 if not same(('U16002','3'),('U16002','6'),('J16001','21')):errors.append('Reverse-block CE must observe actual output, never ground')
 if same(('U16002','1'),('U16002','6')):errors.append('Reverse-block input/output bypassed')
 if not same(('U16001','6'),('U16002','1')):errors.append('Module branch must pass real current limiter before reverse blocker')
 if not same(('U16003','5'),('J16001','1'),('J16001','2')) or actual[('U16003','5')][0]!='/'+ 'ESP_MODULE_3V3':errors.append('UART buffer must use actual module LDO output')
 if actual[('J16001','11')][0]!='/ESP_SERVICE_RX':errors.append('Service receive must use GPIO18/J1.11')
 if not actual[('J16002','3')][0].startswith('unconnected-'):errors.append('Onboard CP2102 UART0 RX must stay disconnected')
 if not actual[('J16002','2')][0].startswith('unconnected-'):errors.append('ESP TX must have no motherboard control authority')
 for ref,pins in [('J16001',('3','13','14')),('J16002',('11','12','13','14','15','19','20'))]:
  if any(not actual[ref,p][0].startswith('unconnected-') for p in pins):errors.append('Reset/strap/memory/nativeUSB must not be driven '+ref)
 if model.get('manufacturing_ready') or model.get('physical_qualification'):errors.append('Unqualified circuit cannot claim manufacture or measurement')
 if model['branch_power'].get('simultaneous_USB_and_header_power_qualified'):errors.append('Manufacturer mutually exclusive power modes remain unqualified')
 return errors

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 model=json.loads((SOURCE/'design.json').read_text());tree=ET.parse(SOURCE/'netlist.xml');errors=validate(tree,model)
 report=dict(source_checks_pass=not errors,errors=errors,physical_parts=len(model['components']),
   native_numbered_pins=sum(len(c['pins']) for c in model['components'].values()),manufacturing_ready=False,physical_qualification=False)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));raise SystemExit(bool(errors))
if __name__=='__main__':main()
