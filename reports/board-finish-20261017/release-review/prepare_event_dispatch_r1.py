"""Create an isolated event-dispatch experiment; never edit canonical RTL."""
from pathlib import Path
import hashlib, json, difflib
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'event-dispatch-r1'
SOURCE=ROOT/'gateware/v3/runtime/cnc3_runtime_events.v'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists(); OUT.mkdir()
    old=SOURCE.read_text()
    new=old
    new=new.replace(' integer i,j,k;reg[8:0]temp_count;', ' integer i,j,k,b,p;reg[8:0]temp_count;')
    token=' reg [1:0] next_filtered,edges;'
    extra=''' // Each accepted producer is built once. At most seven consecutive writes
 // occupy distinct low-three-bit banks; one-hot selection removes the wide
 // cascaded per-producer bank update muxes without changing queue admission.
 reg [6:0] accepted_valid,bank_select;
 reg [7:0] accepted_slot[0:6];
 reg [159:0] accepted_payload[0:6];
'''
    assert new.count(token)==1;new=new.replace(token,extra+token)
    start=new.index('    case(temp_wr[2:0])')
    end=new.index('    temp_wr=temp_wr+8\'d1;',start)
    new=new[:start]+'''    accepted_valid[producer]=1'b1;
    accepted_slot[producer]=temp_wr;
    accepted_payload[producer]={temp_sequence,kind,origin,flags,ticks,data};
'''+new[end:]
    new=new.replace(' task enqueue;\n', ' task enqueue;\n  input [2:0] producer;\n')
    new=new.replace("enqueue(8'd1,i[7:0]", "enqueue(i[2:0],8'd1,i[7:0]")
    new=new.replace("enqueue(8'd2,i[7:0]", "enqueue(i+2,8'd2,i[7:0]")
    new=new.replace("enqueue(8'd3,source", "enqueue(3'd6,8'd3,source")
    token='   next_filtered=filtered;edges=0;'
    assert new.count(token)==1;new=new.replace(token,'''   accepted_valid=0;
   for(p=0;p<7;p=p+1)begin accepted_slot[p]=0;accepted_payload[p]=0;end
'''+token)
    token='   wr<=temp_wr[7:0];count<=temp_count[8:0];next_sequence<=temp_sequence[7:0];'
    dispatch='''   for(b=0;b<8;b=b+1)begin
    bank_select=0;
    for(p=0;p<7;p=p+1)begin
     if(accepted_valid[p] && accepted_slot[p][2:0]==b[2:0])bank_select[p]=1'b1;
    end
    // Exact one-hot case preserves payload X/Z values in RTL simulation.
    // Distinct consecutive addresses prove there is at most one selected word.
    case(bank_select)
'''
    for p in range(7):
        dispatch+=f"     7'b{1<<p:07b}:begin next_write_enable[b]=1'b1;next_write_address[5*b +:5]=accepted_slot[{p}][7:3];next_write_data[160*b +:160]=accepted_payload[{p}];end\n"
    dispatch+='''     default:begin end
    endcase
   end
'''
    assert new.count(token)==1;new=new.replace(token,dispatch+token)
    (OUT/'cnc3_runtime_events.v').write_text(new)
    (OUT/'original.v').write_bytes(SOURCE.read_bytes())
    (OUT/'original_diff.v').write_text(old.replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_original('))
    (OUT/'candidate_diff.v').write_text(new.replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_candidate('))
    (OUT/'candidate.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='canonical/cnc3_runtime_events.v',tofile='isolated/cnc3_runtime_events.v')))
    record={'status':'ISOLATED_DISPATCH_CANDIDATE_PREPARED_QUALIFICATION_REQUIRED','canonical_source':str(SOURCE),'canonical_SHA256':sha(SOURCE),'candidate_SHA256':sha(OUT/'cnc3_runtime_events.v'),'source_unchanged':True,'adopted':False,'manufacturing_ready':False}
    (OUT/'preparation-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))
if __name__=='__main__':main()
