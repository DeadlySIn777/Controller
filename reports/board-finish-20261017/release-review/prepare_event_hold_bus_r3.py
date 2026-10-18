"""Separate capture+held-disabled-bank-bus experiment; explicit masked proof."""
from pathlib import Path
import hashlib,json,difflib
H=Path(__file__).resolve().parent;BASE=H/'event-capture-select-r2';OUT=H/'event-hold-disabled-bus-r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    old=(BASE/'original.v').read_text();base=(BASE/'cnc3_runtime_events.v').read_text()
    token='next_write_enable=0;next_write_address=0;next_write_data=0;prefetched_rd<=rd;'
    assert base.count(token)==1
    new=base.replace(token,'next_write_enable=0;next_write_address=write_address;next_write_data=write_data;prefetched_rd<=rd;')
    (OUT/'cnc3_runtime_events.v').write_text(new)
    (OUT/'original.v').write_bytes((BASE/'original.v').read_bytes())
    (OUT/'original_diff.v').write_text(old.replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_original('))
    (OUT/'candidate_diff.v').write_text(new.replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_candidate('))
    (OUT/'candidate.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='canonical/cnc3_runtime_events.v',tofile='isolated/cnc3_runtime_events.v')))
    bench=(BASE/'boundary_tb.sv').read_text()
    before='{old.write_enable,old.write_address,old.write_data} !== {dut.write_enable,dut.write_address,dut.write_data}'
    assert bench.count(before)==1;bench=bench.replace(before,'old.write_enable !== dut.write_enable')
    bench=bench.replace('integer cycles=0,cases=0,seven=0,acks=0,wraps=0,fulls=0;', 'integer cycles=0,cases=0,seven=0,acks=0,wraps=0,fulls=0,ignored_disabled_bus_diffs=0;')
    marker=' end\n end endtask\n task tick;'
    assert bench.count(marker)==1
    replacement=''' end
  for(z=0;z<8;z=z+1)begin
   if(old.write_enable[z]===1'b1)begin
    if({old.write_address[5*z +:5],old.write_data[160*z +:160]} !==
       {dut.write_address[5*z +:5],dut.write_data[160*z +:160]})$fatal(1,"enabled-bank bus differs cycle=%0d bank=%0d",cycles,z);
   end else if(old.write_enable[z]===1'b0 &&
       {old.write_address[5*z +:5],old.write_data[160*z +:160]} !==
       {dut.write_address[5*z +:5],dut.write_data[160*z +:160]})ignored_disabled_bus_diffs=ignored_disabled_bus_diffs+1;
  end
 end endtask
 task tick;'''
    bench=bench.replace(marker,replacement)
    bench=bench.replace('EVENT_DISPATCH_DIFF_PASS','EVENT_MASKED_BUS_DIFF_PASS')
    bench=bench.replace('  $finish;\n end\nendmodule', '  if(ignored_disabled_bus_diffs==0)$fatal(1,"masked bus differences not exercised");\n  $display("DISABLED_BUS_DIFFERENCES_EXERCISED count=%0d",ignored_disabled_bus_diffs);\n  $finish;\n end\nendmodule')
    (OUT/'boundary_tb.sv').write_text(bench)
    record={'status':'ISOLATED_CAPTURE_AND_HELD_DISABLED_BUS_CANDIDATE_PREPARED','baseline_candidate_SHA256':sha(BASE/'cnc3_runtime_events.v'),'candidate_SHA256':sha(OUT/'cnc3_runtime_events.v'),'canonical_reference_SHA256':sha(BASE/'original.v'),'logical_delta':'retain each bank write_data/address while its write_enable=0; zero reset and identical enabled writes preserved','proof_boundary':'full write_enable equality and per-bank address/data equality whenever enabled; all observable outputs/queue state exact; disabled bus differences counted explicitly','adopted':False}
    (OUT/'preparation-receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
    # Qualifier remains separately named; old strict test receipts are untouched.
    qualify=(H/'qualify_event_capture_r2.py').read_text()
    qualify=qualify.replace("OUT=H/'event-capture-select-r2'","OUT=H/'event-hold-disabled-bus-r3'")
    qualify=qualify.replace("source=Path(prep['source']);assert sha(source)==prep['canonical_SHA256']", "source=H.parents[2]/'gateware/v3/runtime/cnc3_runtime_events.v';assert sha(source)==prep['canonical_reference_SHA256']")
    qualify=qualify.replace('CAPTURE_ONLY_SELECTOR_EXHAUSTION_AND_STRICT_BOUNDARY_DIFFERENTIAL_PASS','CAPTURE_HELD_DISABLED_BUS_MASKED_BOUNDARY_DIFFERENTIAL_PASS')
    qualify=qualify.replace('full original strict1280bitwrite bus/address/enable, output, pointer/count/ACK/sequence comparison unchanged; same seeded-state and30000externalstress scope as r1','full write_enable plus enabled-bank address/data equality; public outputs and queue state exact; disabled bus differences explicitly counted; same seeded-state and30000externalstress scope as r1')
    (H/'qualify_event_hold_bus_r3.py').write_text(qualify)
    maps=(H/'map_event_capture_r2.py').read_text().replace("RUN=H/'event-capture-select-r2'","RUN=H/'event-hold-disabled-bus-r3'")
    maps=maps.replace("[('original',RUN/'original.v'),('literal-case',RUN/'cnc3_runtime_events.v')]", "[('held-disabled-bus',RUN/'cnc3_runtime_events.v')]")
    maps=maps.replace('len(records)==2','len(records)==1').replace('NATIVE_EVENTS_ONLY_CAPTURE_COMPARISON_COMPLETE','NATIVE_EVENTS_ONLY_HELD_DISABLED_BUS_MAP_COMPLETE')
    (H/'map_event_hold_bus_r3.py').write_text(maps)
if __name__=='__main__':main()
