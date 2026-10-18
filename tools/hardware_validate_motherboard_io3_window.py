"""Independent source/native/voltage review of the three IO3 monitor dividers."""
from __future__ import annotations
import copy,json,xml.etree.ElementTree as ET
from itertools import product
from hardware_apply_motherboard_io3_window import ROOT,OUT,REPORT
SCOPES={'mc':[('R2061','R2069','R18003')],'motor':[('R9005','R9007','R18004'),('R9015','R9017','R18005')]}
MPNS={'uv':'TNPW060353K6BEEA','ov':'TNPW060357K6BEEA','series':'TNPW0603698RBEEA'}
def nodes(path):
 out={}
 for net in ET.parse(path).findall('.//nets/net'):
  for p in net.findall('node'):
   k=(p.attrib['ref'],p.attrib['pin'])
   if k in out:raise ValueError('Duplicate native endpoint')
   out[k]=net.attrib['name'].lstrip('/')
 return out

def review(model,scope,baseline=None,native=None):
 p=model['components'];errors=[]
 for uv,ov,series in SCOPES[scope]:
  expected={uv:(MPNS['uv'],53600,None),ov:(MPNS['ov'],57600,{'1':'IO_3V3_OV_SERIES_'+scope.upper()+'_'+ov,'2':baseline['components'][ov]['pins']['2'] if baseline else p[ov]['pins']['2']}),series:(MPNS['series'],698,{'1':'IO_3V3','2':'IO_3V3_OV_SERIES_'+scope.upper()+'_'+ov})}
  for ref,(mpn,r,pins) in expected.items():
   c=p.get(ref,{})
   if c.get('mpn')!=mpn or c.get('resistance_ohm')!=r:errors.append('Wrong exact monitor part '+ref)
   if c.get('footprint')!='Resistor_SMD:R_0603_1608Metric':errors.append('Wrong monitor footprint '+ref)
   if c.get('initial_tolerance')!=.001 or c.get('tcr_ppm')!=25:errors.append('Wrong monitor tolerance/TCR '+ref)
   if pins is not None and c.get('pins')!=pins:errors.append('Series divider bypass/pin mismatch '+ref)
  if p[uv]['pins']['1']!='IO_3V3':errors.append('UV receiving rail disconnected')
 if baseline:
  changed={r for x in SCOPES[scope] for r in x[:2]}
  added={x[2] for x in SCOPES[scope]}
  if set(p)!=set(baseline['components'])|added:errors.append('Unbounded component add/remove')
  for ref,old in baseline['components'].items():
   if ref not in p:continue
   if ref not in changed and p[ref]!=old:errors.append('Unbounded retained mutation '+ref)
   elif ref in changed:
    for k,v in old.items():
     if k not in ['value','mpn','resistance_ohm','resistance_ohms','initial_tolerance','tcr_ppm','pins'] and p[ref].get(k)!=v:errors.append('Unbounded monitor property '+ref+'.'+k)
    if p[ref]['pins']['2']!=old['pins']['2']:errors.append('Monitor sense endpoint changed '+ref)
 if native:
  for ref,c in p.items():
   for pin,net in c['pins'].items():
    if net is not None and native.get((ref,pin))!=net:errors.append('Native/model endpoint mismatch '+ref+'.'+pin)
 # Explicit initial, 25ppm/K at0..85C, and manufacturer's500ppm/1000h
 # general-operation drift bound; bottom retains old0.1% total screen.
 top_eps=.001+60*25e-6+.0005;bottom_eps=.001
 corners=[]
 for top in [53600,57600+698]:
  x=[v*(1+r/b)+i*r for v,r,b,i in product([.4975,.5025],[top*(1-top_eps),top*(1+top_eps)],[10000*(1-bottom_eps),10000*(1+bottom_eps)],[-15e-9,15e-9])];corners.append([min(x),max(x)])
 uv,ov=corners
 if uv[0]<=3.14 or ov[1]>=3.465:errors.append('Trip corners exceed actual operating intersection')
 screening={'uv_trip_v':uv,'ov_trip_v':ov,'retained_bottom_total_error_fraction':bottom_eps,'new_top_total_error_fraction':top_eps,'source_operating_intersection_v':[3.14,3.465],'distribution_noise_margin_low_v':3.250213725012973-uv[1],'distribution_noise_margin_high_v':ov[0]-3.3479331042040728,'lower_rating_guard_v':uv[0]-3.14,'upper_rating_guard_v':3.465-ov[1],'lifetime_condition':'500ppm at1000h generaloperation film<=125C; arbitrarylife/environment not guaranteed','default_health_reset_wdt_delay_changed':False,'full_partial_power_or_fault_delay_qualified':False}
 return {'consistency_pass':not errors,'errors':errors,'screening':screening,'physical_qualification':False,'manufacturing_ready':False}

def run():
 out={}
 for scope,folder,stem in [('mc','motherboard_io3_upgrade','motherboard_io3_upgrade'),('motor','motherboard_motor_power','motherboard_motor_power')]:
  model=json.loads((OUT/scope/'design.json').read_text());baseline=json.loads((ROOT/'hardware'/folder/'design.json').read_text())
  r=review(model,scope,baseline,nodes(OUT/scope/'netlist.xml'));erc=json.loads((REPORT/(scope+'-erc.json')).read_text());v=[v for s in erc['sheets'] for v in s['violations']]
  r['erc']={'errors':sum(x['severity']=='error' for x in v),'warnings':sum(x['severity']=='warning' for x in v),'ignored_checks':erc.get('ignored_checks',[])};out[scope]=r
 (REPORT/'validation.json').write_text(json.dumps(out,indent=2)+'\n');return out
if __name__=='__main__':print(json.dumps(run(),indent=2))
