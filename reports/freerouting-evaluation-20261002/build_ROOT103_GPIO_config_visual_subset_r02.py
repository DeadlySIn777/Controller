"""Separate exact GPIO/config/visual review; original112 rows stay immutable."""
from pathlib import Path
import sys,json,copy,collections
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
import hardware_route_ordinary_wip_r05 as issued
import hardware_bind_ordinary_route_manifest_r03 as binder
e=issued.engine
BASE=ROOT/'reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb'
FIRST=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-visual-allowlist-r01'
OUT=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-visual-allowlist-r02'
assert not OUT.exists();OUT.mkdir(parents=True)
assert e.sha(BASE)=='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
review=ROOT/issued.SOURCE;r=e.read(review)
models={name:e.read(ROOT/'hardware'/name/'design.json')for name in('motherboard_di','motherboard_io_control','motherboard_acc_control','motherboard_status')}
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();conn=b.GetConnectivity()
pads={(fp.GetReference(),p.GetNumber()):p for fp in b.GetFootprints()for p in fp.Pads()if p.GetNumber()}
potential=[]
for n,row in r['nets'].items():
 if row['signal_class']in{'isolated_general_input_state','strapped_configuration'}or n in{'/motherboard_status/OBS'+str(i)+'_INVERTED'for i in range(24)}:potential.append(n)
assert len(potential)==64
rows=[];selected=[]
for n in sorted(potential):
 row=r['nets'][n];end=row['source_endpoints'];cls=row['signal_class']
 assert row['return_net']=='/LOGIC_GND' and row['maximum_voltage_v']<=5.5
 for ep in end:
  comp=models[ep['source_block']]['components'][ep['reference']]
  assert comp['mpn']==ep['mpn'] and comp['pins'][ep['pin']]==ep['model_pin_net']
  assert ep['function']not in{'NRST','BOOT0','SWCLK','SWDIO','VDD','VSS'}
 if cls=='isolated_general_input_state':
  assert len(end)==4 and row['declared_producer'][0].startswith('U80')
  roles={ep['reference']:models[ep['source_block']]['components'][ep['reference']].get('role','')for ep in end}
  assert {ep['mpn']for ep in end}=={'ISO1212DBQR','STM32G031C8T6','SN74AHCT04PWR','CRCW0603100KFKEA'}
  assert all(ep['reference']=='U13001'or ep['mpn']!='STM32G031C8T6'for ep in end)
  assert next(ep for ep in end if ep['mpn']=='ISO1212DBQR')['function']in{'OUT1','OUT2'}
  assert next(ep for ep in end if ep['mpn']=='SN74AHCT04PWR')['electrical_type']=='input'
  reason='General24 isolated DI logic: exact ISO1212 output, acquisition-MCU GPIO,100k own-logic bias and independent visual buffer input only. No physical hard permission/inhibit/fault/STEP/DIR/encoder/watchdog node is an endpoint. Dedicated safety/probe/frequency receivers remain excluded. Software use as a limit does not change the existing electrical/reference contract.'
 elif cls=='strapped_configuration':
  assert len(end)==2 and sum(ep['reference'].startswith('R')for ep in end)==1
  rp=next(ep for ep in end if ep['reference'].startswith('R'));comp=models[rp['source_block']]['components'][rp['reference']]
  assert comp['pins']['2']in{'LOGIC_GND','IO_3V3'} and comp['resistance_ohm']==10000
  assert 'strap'in comp['role'] and 'presence'in comp['role']
  assert all(ep['mpn']in{'CRCW060310K0FKEA','STM32G031C8T6','STM32G031K8T6'}for ep in end)
  reason='Fixed IOL1 node-address GPIO strap: exact10k pull plus MCU GPIO, with actual own logic return and supply. No reset/BOOT0/FPGA configuration/clock endpoint, no removable-card presence or authority inference.'
 else:
  assert len(end)==2 and models['motherboard_status']['components'][row['declared_producer'][0]]['role']=='TTL receive buffer, no motion/DI authority'
  reason='Independent general-DI visual intermediate only; main watchdog/status fault qualifiers and all motor alarm observations remain excluded.'
 groups=set();all_source=[]
 for pair in row['source_pins']:
  p=pads[tuple(pair)];assert p.GetNetname()==n
  connected={v.m_Uuid.AsString()for v in conn.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T};connected.add(p.m_Uuid.AsString())
  groups.add(tuple(sorted(connected)));all_source.append(p.m_Uuid.AsString())
 missing=len(groups)-1
 rows.append(dict(net=n,classification=cls,actual_full_endpoints=end,source_pad_UUIDs=all_source,actual_source_components_before=len(groups),required_joins_before=missing,disposition=reason,unchanged_source_row_sha256=e.sha(review)))
 if missing:selected.append(n)
assert selected
plane=FIRST/'literal-plane-eligibility.json'
manifest=binder.bind(BASE,plane,OUT/'manifest.json',set(selected))
assert all(manifest['nets'][n]==r['nets'][n]for n in selected)
e.write(OUT/'selected-nets.json',selected)
e.write(OUT/'baseline-disposition.json',e.read(FIRST/'baseline-disposition.json'))
protected=copy.deepcopy(e.read(FIRST/'protected-native-manifest.json'))
protected['excluded_physical_nets']=sorted(str(net.GetNetname())for net in b.GetNetsByName().values()if str(net.GetNetname())not in selected)
protected['parent_visual_protection_manifest_sha256']=e.sha(FIRST/'protected-native-manifest.json')
e.write(OUT/'protected-native-manifest.json',protected)
inputs={str(p):e.sha(p)for p in(BASE,review,FIRST/'source-scope-review.json',FIRST/'protected-native-manifest.json',plane,Path(__file__))}
inputs.update({str(ROOT/'hardware'/name/'design.json'):e.sha(ROOT/'hardware'/name/'design.json')for name in models})
e.write(OUT/'source-scope-review.json',dict(passed=True,input_sha256=inputs,board_sha256=e.sha(BASE),eligible_exact_rows=rows,reviewed_categories=dict(collections.Counter(v['classification']for v in rows)),selected_nets=selected,actual_selected_unjoined_nets=len(selected),required_joins_before=sum(v['required_joins_before']for v in rows),exact_native_source_rows_unchanged=True,no_new_unreviewed_source_class_promoted=True,excluded_prior112_nets=sorted(set(r['nets'])-set(potential)),protected_categories=['all watchdogs/timers/permission/enables/hardware-inhibit and fault qualifiers','main motor alarms and all their visual intermediates','power/distribution/analog/precision/highspeed/clock/STEP/DIR/encoder','dedicated probe/safety/frequency inputs','reset/boot/FPGA configuration/debug/buses'],actual_qualified_GPIO_firmware_or_machine_use_claimed=False,signal_integrity_latency_or_manufacturing_ready=False))
assert all(e.sha(p)==h for p,h in inputs.items())
print(json.dumps(dict(passed=True,eligible=len(rows),selected=len(selected),joins=sum(v['required_joins_before']for v in rows),categories=dict(collections.Counter(v['classification']for v in rows)))))
