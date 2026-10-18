"""Independent exact new bypass/netlist and preservation check."""
import copy,json,xml.etree.ElementTree as ET
from hardware_apply_io3_reset_bypass import ROOT,OUT,REPORT
def validate(m,native=None,baseline=None):
 c=m['components'];errors=[];cap=c.get('C18001',{})
 if cap.get('pins')!={'1':'IO_3V3','2':'LOGIC_GND'}:errors.append('Dedicated reset bypass is not distributed IO3/LOGIC_GND')
 if cap.get('mpn')!='GRM188R72A104KA35D' or cap.get('footprint')!='Capacitor_SMD:C_0603_1608Metric':errors.append('Exact actual100nF manufacturer/footprint differs')
 if c.get('U2006',{}).get('pins',{}).get('5')!='IO_3V3' or c['U2006']['pins'].get('3')!='LOGIC_GND':errors.append('Owner resetbuffer actual supply/return differs')
 if c.get('C2010',{}).get('pins')!={'1':'IO_3V3_REG_LOCAL','2':'LOGIC_GND'}:errors.append('Local regulator reservoir was disturbed')
 if baseline:
  if set(c)-set(baseline['components'])!={'C18001'}:errors.append('Unbounded added/removed refs')
  for r,p in baseline['components'].items():
   if c.get(r)!=p:errors.append('Retained component mutation '+r)
 if native is not None:
  for r,p in c.items():
   for pin,net in p['pins'].items():
    if native.get((r,pin))!=net:errors.append('Native/model mismatch '+r+'.'+pin)
 return dict(passed=not errors,errors=errors,original_MC_modified=False,local_layout_qualified=False,physical_qualified=False)
def native_nodes(p):
 return{(q.attrib['ref'],q.attrib['pin']):n.attrib['name'].lstrip('/')for n in ET.parse(p).findall('.//nets/net')for q in n.findall('node')}
def main():
 m=json.loads((OUT/'design.json').read_text());base=json.loads((ROOT/'hardware/motherboard_io3_upgrade/design.json').read_text())
 r=validate(m,native_nodes(OUT/'netlist.xml'),base);e=json.loads((REPORT/'erc.json').read_text());v=[v for s in e['sheets']for v in s['violations']]
 r.update(ERC_errors=sum(x['severity']=='error'for x in v),ERC_warnings=sum(x['severity']=='warning'for x in v),ignored_checks=e.get('ignored_checks',[]))
 (REPORT/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']and not v and not r['ignored_checks']
if __name__=='__main__':main()
