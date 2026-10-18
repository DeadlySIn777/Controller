"""Isolate only bounded capture selector decoding from canonical events."""
from pathlib import Path
import hashlib,json,difflib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];OUT=H/'event-capture-select-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    source=ROOT/'gateware/v3/runtime/cnc3_runtime_events.v';old=source.read_text();new=old
    start=new.index('   if(selector<12)capture=')
    end=new.index('  end\n endfunction',start)
    text='''   // Decode the sixteen legal records directly; avoid arithmetic-controlled
   // wide variable part-selects. Exact case defaults unknown selectors to zero,
   // matching the guarded original, while preserving selected data X/Z bits.
   case(selector)
'''
    for i in range(12):text+=f"    8'd{i}:capture=step_counts[{287-24*i} -:24];\n"
    for i in range(4):text+=f"    8'd{16+i}:capture=encoder_counts[{95-24*i} -:24];\n"
    text+="    default:capture=24'd0;\n   endcase\n"
    new=new[:start]+text+new[end:]
    (OUT/'cnc3_runtime_events.v').write_text(new)
    (OUT/'original.v').write_bytes(source.read_bytes())
    (OUT/'original_diff.v').write_text(old.replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_original('))
    (OUT/'candidate_diff.v').write_text(new.replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_candidate('))
    (OUT/'candidate.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='canonical/cnc3_runtime_events.v',tofile='isolated/cnc3_runtime_events.v')))
    bench=(H/'event_dispatch_diff_tb.sv').read_text().replace('if(dut.accepted_valid!==7\'b1111111)', 'if($countones(dut.write_enable)!==7)')
    bench=bench.replace("288'hf123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789", "{9{32'h12345678}}")
    (OUT/'boundary_tb.sv').write_text(bench)
    record={'status':'CAPTURE_SELECTOR_ONLY_CANDIDATE_PREPARED','source':str(source),'canonical_SHA256':sha(source),'candidate_SHA256':sha(OUT/'cnc3_runtime_events.v'),'previous_dispatch_candidate_included':False,'boundary_test_change':'only coverage assertion references write_enable count rather than dispatch-private accepted_valid; shared initial stimulus literal made exact288bit','adopted':False}
    (OUT/'preparation-receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
