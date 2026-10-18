"""Identify unchanged, actually flashed old ports across real split groups."""
import sys,json,pickle,math,time,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
L=N.L;K=N.K;sha=N.sha
OUT=H/'actual-native-existing-In3-ports-across-current-logic-groups-r311'
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before()
 gp=H/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-all-net-groups.pkl'
 assert sha(gp)=='d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a';groups=pickle.loads(gp.read_bytes())
 ep=H/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json';assert sha(ep)=='13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3';e=json.loads(ep.read_bytes())
 native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());domains={L.norm(n):r['domain']for n,r in native['nets'].items()};flashes=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias']
 oldboard=H/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb';assert sha(oldboard)=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38';oldchunks=K.C.inventory(oldboard.read_bytes())[3]
 supply=Path('Z:/pcb-runs/claude-finish/tools/power_widths.json');power=json.loads(supply.read_bytes());rows=[];pernet=[]
 excluded={'/LOGIC_GND','/IO_3V3','/CORE_1V2','/motherboard_compute/CM_AUX_3V3','/motherboard_analog_output/AO1_ENABLE','/motherboard_analog_output/AO1_DAC_CS_N','/motherboard_analog_output/AO1_VREF'}
 for raw,gg in groups.items():
  net=L.norm(raw)
  if domains.get(net)!='DOM_LOGIC' or len(gg)<2 or net in excluded or net in power or any(tag in net for tag in ('/USB_','/HDMI_','/MIPI_','AO1_','FPGA_CDONE')):continue
  # This is a signal-port census; supplies with names absent from the old
  # historical width table receive no route/current assumptions here.
  ports=[]
  for gi,group in enumerate(gg):
   vv={q['uuid']for q in group if q['kind']=='via' and q['layer']=='In3.Cu'}
   actual=[]
   for uid in vv:
    t=e['copper'].get(uid)
    if not t or t['kind']!='via' or L.norm(t['raw_net'])!=net or uid not in oldchunks:continue
    if t['chunk_sha256']!=hashlib.sha256(oldchunks[uid]).hexdigest() or 'In3.Cu' not in flashes.get(uid,[]):continue
    actual.append({'UUID':uid,'at_mm':[v/1e6 for v in t['at_IU']],'diameters_IU':t['diameters_IU'],'drill_IU':t['drill_IU'],'observed_FULL_BEFORE_flash_layers':flashes[uid],'unchanged_current_native_chunk_SHA256':t['chunk_sha256']})
   if actual:ports.append((gi,actual))
  if len(ports)<2:continue
  candidates=[]
  for i,(left,aa) in enumerate(ports):
   for right,bb in ports[i+1:]:
    nearest=sorted(((math.dist(a['at_mm'],b['at_mm']),a,b)for a in aa for b in bb),key=lambda q:q[0])[:3]
    for distance,a,b in nearest:
     if distance<=60:candidates.append({'normalized_net':net,'raw_graph_net':raw,'left_before_group':left,'right_before_group':right,'left_port':a,'right_port':b,'span_mm':distance,'SOURCE_In4_fullbody_owned-terminal-caps_existing-return-current-rules-clearance-native_AFTER':'OPEN_NOT_ROUTED'})
  if candidates:rows.extend(candidates);pernet.append({'normalized_net':net,'actual_before_split_groups':len(gg),'groups_with_unchanged_actual_In3_ports':len(ports),'bounded_port_pairs':len(candidates)})
 rows.sort(key=lambda r:r['span_mm']);put('actual-unchanged-In3-port-pairs-not-routes.json',rows);put('net-census.json',pernet)
 put('receipt.json',{'status':'ACTUAL_FULL_BEFORE_EXISTING_FLASHED_CURRENT_UNCHANGED_In3_PORT_PAIR_CENSUS','all_net_group_cache_SHA256':sha(gp),'current_Cu_ledger_SHA256':sha(ep),'old_native_board_SHA256':sha(oldboard),'old_actual_flash_SHA256':sha(N.R157/'actual-full-refill-via-flashes.json'),'named_candidate_nets':len(pernet),'port_pairs_le60mm':len(rows),'no_new_via_no_model_or_board_no_production_or_connection_progress_claim':True,'all_source_reference_return_geometry_current_and_native_AFTER':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R311_CENSUS',len(pernet),len(rows),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
