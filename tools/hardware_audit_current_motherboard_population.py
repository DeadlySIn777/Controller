"""Read-only current-source sanity pass with exclusive function accounting."""
import argparse,collections,csv,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
GROUPS={
 '12 motor interfaces':('mc_motor_buffers','motherboard_motors'),
 '24 digital inputs':('motherboard_di',),
 '16 smart outputs':('motherboard_do',),
 'Encoder / fast inputs':('motherboard_fast_inputs',),
 'Rail regulation / receiving-rail monitoring':('mc_local_power','motherboard_motor_power','motherboard_io3_upgrade','motherboard_io3_window','motherboard_io3_reset_bypass'),
 'FPGA / configuration / clock':('fpga_core',),
 'Watchdog / permission':('mc_permission','watchdog_conditioning','motherboard_control_bridges'),
 'I/O acquisition / control':('motherboard_io_control',),
 'Probe / pendant / port power':('motherboard_operator',),
 'Power entry / distribution':('motherboard_power_entry',),
 'Process / accessory acquisition':('motherboard_process','motherboard_acc_control'),
 'Analog / communications':('motherboard_analog_input','motherboard_analog_output','motherboard_comms'),
 'Indicators':('motherboard_status',),
 'Isolated sensor power / acquisition':('motherboard_safety_sensor',),
 'Terminals / chassis coupling':('motherboard_terminals',),
 'Compute / ESP / storage sockets and support':('motherboard_compute','motherboard_esp_socket'),
 'Diagnostics / motherboard identity':('motherboard_diagnostics','motherboard_identity_io'),
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise ValueError('Preserve historical audits; use a new directory')
 files=[ROOT/'hardware/motherboard'/n for n in ('design.json','netlist.xml','bom.csv','assembly-map.json')]
 frozen={str(f):sha(f)for f in files};model=json.loads(files[0].read_text());parts=model['components']
 native={c.attrib['ref']:c for c in ET.parse(files[1]).findall('.//components/comp')if c.findtext('footprint')}
 bom={r['Reference']:r for r in csv.DictReader(files[2].open(encoding='utf8'))}
 if set(native)!=set(parts)or set(bom)!=set(parts):raise ValueError('Native/source/BOM physical inventory differs')
 for ref,c in parts.items():
  if c['footprint']!=native[ref].findtext('footprint')or c['mpn']!=native[ref].findtext("./fields/field[@name='MPN']"):raise ValueError('Exact native part identity differs '+ref)
 bare={r for r,c in parts.items()if c.get('purchased')is False or c['mpn']=='PCB_COPPER_TEST_PAD_D1.0'}
 dnp={r for r,row in bom.items()if row['DNP'].lower()=='true'};purchased=set(parts)-bare-dnp
 if len(bare)!=44 or len(dnp)!=2 or len(purchased)!=2642:raise ValueError('Adopted r24 assembly categories differ')
 seen=set();rows=[]
 for function,blocks in GROUPS.items():
  refs={r for r,c in parts.items()if c['source_block']in blocks}
  if seen&refs:raise ValueError('Duplicated function accounting')
  seen|=refs;rows.append(dict(function=function,physical_footprints=len(refs),purchased_fitted=len(refs&purchased),bare_PCB_geometry=len(refs&bare),DNP=len(refs&dnp),references=sorted(refs)))
 if seen!=set(parts):raise ValueError('Unclassified actual source blocks')
 def hits(tokens):return [r for r,c in parts.items()if any(t in (c['mpn']+' '+c['footprint']).upper()for t in tokens)]
 rack=hits(('DIN41612','DIN_41612','HAR-BUS','H15_BACKPLANE','CARD_CAGE','CARD_GUIDE'))
 soc=hits(('BCM2711','BCM2712','H616','RK3566','RK3588','ESP32','ESP8266'))
 sockets=[dict(ref=r,mpn=c['mpn'],footprint=c['footprint'],role=c.get('role',''))for r,c in parts.items()if c['mpn']in ('10164227-1001A1RLF','61302211821','503398-1892')]
 if rack or soc:raise ValueError('Actual rack/custom commodity-processor part requires review')
 counts=collections.Counter(''.join(x for x in r if x.isalpha())for r in parts);passive=sum(counts[n]for n in ('R','C','D'))
 grouped=collections.defaultdict(list)
 for r,c in parts.items():grouped[c['mpn']].append(r)
 repeated=[dict(MPN=m,references=sorted(refs),source_regions=sorted({parts[r]['source_block']for r in refs}),roles={r:parts[r].get('role',parts[r]['value'])for r in refs},source_pins={r:parts[r]['pins']for r in refs},automatic_removal_authorized=False)for m,refs in sorted(grouped.items())if len(refs)>1 and any(r.startswith('U')for r in refs)]
 if any(sha(Path(n))!=h for n,h in frozen.items()):raise ValueError('Audit input changed')
 result=dict(passed=True,source_hashes=frozen,physical_footprints=len(parts),purchased_fitted=len(purchased),bare_PCB_geometry=len(bare),DNP=len(dnp),function_counts=rows,composition=dict(counts),R_C_D_footprints=passive,R_C_D_percentage=100*passive/len(parts),rack_only_parts_found=rack,duplicated_compute_or_ESP_die_parts=soc,actual_commodity_module_sockets=sockets,repeated_active_MPN_review=repeated,confirmed_removable_rack_only_parts=[],source_or_PCB_changed=False,source_and_native_BOM_identity_checked=True,module_compatibility_or_boot_qualified=False,manufacturing_ready=False)
 a.out.mkdir(parents=True);(a.out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
 with (a.out/'footprints-by-function.csv').open('w',newline='',encoding='utf8')as f:
  w=csv.DictWriter(f,fieldnames=['function','physical_footprints','purchased_fitted','bare_PCB_geometry','DNP'],extrasaction='ignore');w.writeheader();w.writerows(rows)
 lines=['# Current motherboard population sanity pass','',f'{len(parts)} physical footprints: {len(purchased)} purchased fitted, {len(bare)} bare PCB geometry, {len(dnp)} DNP.','', '| Function | Footprints | Purchased | Bare | DNP |','|---|---:|---:|---:|---:|']
 lines+=['| '+str(r['function'])+' | '+' | '.join(str(r[k])for k in ('physical_footprints','purchased_fitted','bare_PCB_geometry','DNP'))+' |'for r in rows]
 lines+=['',f'{passive} resistors/capacitors/diodes ({100*passive/len(parts):.2f}%). These are already included in the function rows.','', 'No fitted rack connector/cage or duplicated commodity compute/ESP die appears in the actual source/BOM. The actual commodity interfaces are two CM connectors, two ESP headers and one microSD socket. Their presence does not qualify module interchange or boot.','', 'Repeated active MPNs retain their distinct source-region, role and actual pin-net assignments in review.json. Equal MPNs do not authorize deleting distinct receiving rails, isolation domains, protection or permission logic. No rack-only fitted part has been proved removable.','', 'Read-only source/native/BOM inspection. PCB connectivity, runtime, manufacturing and physical qualification are separate acceptance gates. Historical 880-footprint studies remain unchanged.']
 (a.out/'README.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:result[k]for k in ('passed','physical_footprints','purchased_fitted','bare_PCB_geometry','DNP','R_C_D_footprints')}))
if __name__=='__main__':main()
