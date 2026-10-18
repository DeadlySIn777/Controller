"""Explicit source-reviewed capacitor owners; no layout/source mutation."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'bypass-owners-r01.json'
SRC=ROOT/'hardware/motherboard_status'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 if OUT.exists():raise SystemExit('Immutable owner receipt exists')
 model=json.loads((SRC/'design.json').read_text());parts=model['components']
 native={}
 for net in ET.parse(SRC/'netlist.xml').findall('./nets/net'):
  for node in net.findall('node'):native[(node.get('ref'),node.get('pin'))]=net.get('name').removeprefix('/')
 owners=[(f'U{17000+i}',14,[7]) for i in range(1,16)]
 owners += [('U17016',1,[4]),('U17016',8,[4]),('U17017',28,[10,19,24]),('U17018',28,[10,19,24]),('U17019',8,[4])]
 table=[]
 for i,(owner,power,grounds) in enumerate(owners,17001):
  ref=f'C{i}';cp=parts[ref];ic=parts[owner];rail=cp['pins']['1'];ret=cp['pins']['2']
  assert cp['capacitance_f']==1e-7
  assert native[(ref,'1')]==rail==native[(owner,str(power))]==ic['pins'][str(power)]
  assert native[(ref,'2')]==ret and all(native[(owner,str(p))]==ret==ic['pins'][str(p)] for p in grounds)
  table.append({'capacitor':ref,'mpn':cp['mpn'],'capacitance_f':cp['capacitance_f'],'owner':owner,'owner_mpn':ic['mpn'],
   'capacitor_power_pin':'1','capacitor_return_pin':'2','power_net':rail,'return_net':ret,'owner_power_pin':str(power),
   'owner_return_pins':[str(p) for p in grounds],'placement_target':'Local IC supply loop; prefer nearest actual ground pin, do not cross isolation domains',
   'native_pin_net_match':True})
 assert len(table)==20 and {r for r,c in parts.items() if c['kind']=='C'}=={x['capacitor'] for x in table}
 OUT.write_text(json.dumps({'schema_version':1,'status':'exact_local_capacitor_owners_source_verified_not_placement_qualified','count':20,
  'actual_owner_paths':table,'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [SRC/'design.json',SRC/'netlist.xml',ROOT/'tools/hardware_build_motherboard_status.py',Path(__file__)]},
  'source_modified':False,'physical_geometry_or_loop_inductance_qualified':False},indent=2)+'\n')
 print(json.dumps({'receipt':OUT.relative_to(ROOT).as_posix(),'count':20,'native_pin_matches':True}))
if __name__=='__main__':main()
