"""Prepare an exact-source, report-local routing experiment; does not edit PCB."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_build_ordinary_route_manifest import native

here=Path(__file__).parent
model=json.loads((ROOT/'hardware/motherboard/design.json').read_text())
nodes,nets,functions=native(model,ROOT/'hardware/motherboard/netlist.xml')
review=ROOT/'reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/independent-connectivity/review.json'
data=json.loads(review.read_text())
ground=next(n for n in data['nets']if n['net']=='/LOGIC_GND')
unjoined={p for cluster in sorted(ground['clusters'],key=len,reverse=True)[1:]for p in cluster}
prefixes=('SN74','74LVC','74AHCT','STM32G031','TPS3808','TPS3839','TPS3851','LTC6994','TCA9517','TCA9534','W25Q32')
rows=[]
for name in sorted(unjoined):
 ref,pin=name.rsplit('.',1);part=model['components'][ref]
 if ref.startswith('U110')or not part.get('mpn','').startswith(prefixes):continue
 function=functions[ref][pin]
 if function['name']not in('GND','VSS','EP')or function['type']!='power_in':continue
 rows.append(dict(reference=ref,pin=pin,MPN=part['mpn'],exact_source_role=part.get('role'),native_function=function))
assert len(rows)==34
template=here/'route-actual-digital-bias-returns-r02.py'
text=template.read_text()
begin=text.index(' selected=[]\n')
end=text.index(' assert selected\n',begin)
replacement=" selected="+repr(rows)+"\n"
replacement+=" for row in selected:\n  assert nodes[row['reference'],row['pin']]=='/LOGIC_GND'\n  assert functions[row['reference']][row['pin']]==row['native_function']\n  assert model['components'][row['reference']]['mpn']==row['MPN']\n"
text=text[:begin]+replacement+text[end:]
text=text.replace("\"\"\"Complete actual high-value digital pull-down ground branches, on a copy.\n\nNo supply, motor current, precision sense, shunt, discharge or Kelvin branch\nis selected. Exact source roles and >=4.7k resistance restrict this pass to\nlogic defaults. Native SOURCE connectivity and real plated reference contact\nare required; no same-name ground or global ampacity qualification is inferred.\n\"\"\"", "\"\"\"Connect 34 exact low-current CMOS/supervisor ground pins to local own fill.\n\nOnly actual native GND/VSS/EP power-input pins of listed devices are eligible.\nNo signal, regulator, high-current switch, Kelvin, analog reference, module\nsocket, capacitor, or motor-bank head is selected. Source, placements, prior\ntracks, zones, and every pad assignment remain unchanged. Adjacent reference\ncontact is proved in actual native copper. This is not global ground or HF\nloop qualification. Physical short-to-ground current qualification is pending.\n\"\"\"")
text=text.replace('for distance in(.7,.85,1.,1.2,1.5,1.8,2.2,2.6,3.):','for distance in(.7,.85,1.,1.2,1.5,1.8,2.):')
text=text.replace("digital-bias-return-candidate.kicad_pcb","exact-CMOS-ground-candidate.kicad_pcb")
text=text.replace("actual_existing_connected_via_UUIDs=[v.m_Uuid.AsString()for v in anchors]","actual_existing_connected_via_UUIDs=[anchors[0].m_Uuid.AsString()],actual_existing_connected_via_count=len(anchors)")
output=here/'route-remaining-CMOS-ground-stitches-r01.py'
assert not output.exists()
output.write_text(text)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope=dict(exact_native_source_rows=rows,source_sha256=sha(ROOT/'hardware/motherboard/design.json'),native_netlist_sha256=sha(ROOT/'hardware/motherboard/netlist.xml'),base_connectivity_sha256=sha(review),parent_generator_sha256=sha(template),generator_sha256=sha(output),maximum_stitch_length_mm=2.,width_mm=.3,via_diameter_mm=.5,drill_mm=.2,adjacent_actual_annulus_required=True,foreign_barrel_spacing_mm=.6,source_geometry_unchanged=True,global_ground_distribution_qualified=False)
(here/'remaining-CMOS-ground-scope-r01.json').write_text(json.dumps(scope,indent=2)+'\n')
print(dict(prepared_rows=len(rows),generator=str(output),source_sha256=scope['source_sha256']))
