"""Persist and run the new native routing pipeline on an explicit toy fixture.

The six bare native fixture pads are test geometry, not production components,
and the explicitly constructed fixture XML/model are labelled as such. The
actual motherboard's 76-net review is independent. This executes a real DSN,
Freerouting session, donor-only import, native DRC, actual return stitches and
uncapped connectivity; it never substitutes fixture results for motherboard fit.
"""
from pathlib import Path
import argparse,json,subprocess,sys
import xml.etree.ElementTree as ET
import pcbnew
import hardware_route_selected_additive_r02 as h

ROOT=h.ROOT
sys.path.insert(0,str(ROOT/'tests'))
from test_selected_additive_routing_r02_native import make_fixture


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 out=h.require_new_report(a.out);native=out/'native';native.mkdir()
 frozen=[Path(__file__),ROOT/'tools/hardware_route_selected_additive_r02.py',
         ROOT/'tools/hardware_route_selected_additive.py',ROOT/'tools/hardware_check_return_corridors.py',
         ROOT/'tests/test_selected_additive_routing_r02_native.py',
         ROOT/'hardware/motherboard/design.json',ROOT/'hardware/motherboard/netlist.xml']
 input_hashes={str(p):h.sha(p)for p in frozen}
 b,added,rows,ledger,drc,path=make_fixture(native)
 h.write(out/'local-additive-check.json',dict(passed=True,native_drc=drc,
     return_corridors=h.return_corridor_check(b,added,rows),
     stitches=h.validate_added_stitches(b,added,rows,ledger),
     physical_fixture_parts=len(b.GetFootprints()),production_motherboard=False))
 # Route the original retained-copper baseline through the actual interchange.
 base=native/'base.kicad_pcb';b=pcbnew.LoadBoard(str(base));model={'components':{}}
 root=ET.Element('export');parts=ET.SubElement(root,'components');nets={}
 for fp in b.GetFootprints():
  ref=fp.GetReference();pads=list(fp.Pads());ET.SubElement(parts,'comp',ref=ref)
  model['components'][ref]=dict(physical=True,purchased=False,mpn='BARE_NATIVE_FIXTURE_PAD',
      footprint=str(fp.GetFPID().GetLibNickname())+':'+str(fp.GetFPID().GetLibItemName()),
      pins={pad.GetNumber():pad.GetNetname()for pad in pads},role='explicit six-pad toy routing fixture')
  for pad in pads:nets.setdefault(pad.GetNetname(),[]).append((ref,pad.GetNumber()))
 netroot=ET.SubElement(root,'nets')
 for i,(n,ends)in enumerate(sorted(nets.items()),1):
  node=ET.SubElement(netroot,'net',name=n,code=str(i))
  for ref,pin in ends:ET.SubElement(node,'node',ref=ref,pin=pin,pintype='passive')
 design=out/'fixture-design.json';xml=out/'fixture-netlist.xml';h.write(design,model)
 ET.ElementTree(root).write(xml,encoding='utf-8',xml_declaration=True)
 reviewed=rows['/DATA'];reviewed.update(signal_class='digital_fault_observation',return_domain='LOGIC',
    source_pins=[list(t)for t in sorted(nets['/DATA'])],source_endpoints=[
     dict(reference=ref,pin=pin,mpn='BARE_NATIVE_FIXTURE_PAD',function='fixture data pad',electrical_type='passive',
          actual_logic_return_pins=[],actual_logic_supply_pins=[])for ref,pin in sorted(nets['/DATA'])])
 review=out/'fixture-source-review.json';plane=out/'fixture-plane-review.json'
 h.write(review,dict(schema_version=2,electrical_review='Explicit six-pad native fixture only',nets=rows,
    source_review_sha256={str(design):h.sha(design),str(xml):h.sha(xml)},
    actual_native_fixture_source_nodes=nets,production_motherboard=False))
 h.write(plane,dict(passed=True,board_sha256=h.sha(base),production_motherboard=False,
    native_drc=h.read(native/'base-drc.json'),actual_source_ground_anchor=['G1','1'],
    actual_reference_layers=['In1.Cu','In4.Cu'],source_anchoring='actual plated G1 pad on both reference layers'))
 manifest=out/'fixture-manifest.json';h.write(manifest,dict(schema_version=2,
    electrical_review='Explicit six-pad native fixture only',nets=rows,
    board_sha256=h.sha(base),design_sha256=h.sha(design),netlist_sha256=h.sha(xml),
    project_sha256=h.sha(base.with_suffix('.kicad_pro')),rules_sha256=h.sha(base.with_suffix('.kicad_dru')),
    source_review=dict(path=str(review.resolve()),sha256=h.sha(review)),
    plane_review=dict(path=str(plane.resolve()),sha256=h.sha(plane))))
 prepared=out/'prepared';receipt=h.prepare(base,design,xml,manifest,prepared)
 java=ROOT/'tmp/freerouting/runtime/jdk-25.0.4.1+1-jre/bin/java.exe';jar=ROOT/'tmp/freerouting/freerouting-2.4.1.jar'
 session=out/'actual-router.ses';command=[str(java),'-Xmx2g','-jar',str(jar),
    '-de',str(prepared/'selected.dsn'),'-do',str(session),'-mp','4','-mt','1']
 run=subprocess.run(command,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=120)
 (out/'freerouting-command.json').write_text(json.dumps(command,indent=2)+'\n',encoding='utf8')
 (out/'freerouting-log.txt').write_text(run.stdout+run.stderr,encoding='utf8')
 if run.returncode or not session.is_file():raise ValueError('Actual fixture router did not produce a session')
 final=h.import_session(prepared,session,out/'imported')
 if final['independent_connectivity']['uncapped_missing_joins']!=0:
  raise ValueError('Actual fixture is still unconnected')
 if input_hashes!={str(p):h.sha(p)for p in frozen}:raise ValueError('Frozen routing/source inputs changed during actual fixture run')
 h.write(out/'receipt.json',dict(passed=True,production_motherboard=False,input_hashes=input_hashes,
     scope='actual complete six-pad native additive/DSN/SES/stitch/connectivity fixture',
     tool_sha256={str(Path(__file__)):h.sha(__file__),str(ROOT/'tools/hardware_route_selected_additive_r02.py'):h.sha(ROOT/'tools/hardware_route_selected_additive_r02.py')},
     actual_router_jar_sha256=h.sha(jar),actual_java_sha256=h.sha(java),
     native_fixture_sha256=h.sha(base),actual_routed_fixture_sha256=final['board_sha256'],
     native_drc=final['native_drc'],uncapped_missing_joins=0,
     actual_new_signal_items=len(final['added_signal_copper_uuids']),actual_new_return_stitches=len(final['added_return_stitch_uuids']),
     retained_copper_source_and_pad_objects_preserved=True,manufacturing_ready=False))
 print(json.dumps(dict(passed=True,actual_session_import=True,uncapped_missing_joins=0)))


if __name__=='__main__':main()
