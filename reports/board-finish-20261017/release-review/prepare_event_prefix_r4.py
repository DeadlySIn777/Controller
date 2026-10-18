"""Isolate fixed producer offers and admitted-prefix dispatch; strict bus parity."""
from pathlib import Path
import hashlib,json,difflib
H=Path(__file__).resolve().parent;BASE=H/'event-capture-select-r2';OUT=H/'event-prefix-admission-r4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    old=(BASE/'original.v').read_text();new=(BASE/'cnc3_runtime_events.v').read_text()
    new=new.replace(' integer i,j,k;reg[8:0]temp_count;',' integer i,j,k,b,p;reg[8:0]temp_count;')
    marker=' reg [1:0] next_filtered,edges;'
    declarations=''' // Fixed producers preserve their source ordering. Admission is a small
 // prefix of offered records; wide payloads are assembled once per producer.
 reg[6:0] offered_valid,accepted_valid,bank_select;
 reg[151:0] offered_payload[0:6];
 reg[159:0] accepted_payload[0:6];
 reg[7:0] accepted_slot[0:6],slot_value[0:7],sequence_value[0:7];
 reg[2:0] offered_prefix,accepted_count;
'''
    assert new.count(marker)==1;new=new.replace(marker,declarations+marker)
    start=new.index(' task enqueue;');end=new.index(' always@(posedge clk',start)
    new=new[:start]+''' task enqueue;
  input[2:0]producer;
  input[7:0]kind,origin,flags;
  input[95:0]data;
  begin
   offered_valid[producer]=1'b1;
   offered_payload[producer]={kind,origin,flags,ticks,data};
  end
 endtask
'''+new[end:]
    marker='   next_filtered=filtered;edges=0;'
    extra='''   offered_valid=0;accepted_valid=0;
   for(p=0;p<7;p=p+1)begin offered_payload[p]=0;accepted_payload[p]=0;accepted_slot[p]=0;end
'''
    assert new.count(marker)==1;new=new.replace(marker,extra+marker)
    new=new.replace("enqueue(8'd1,i[7:0]", "enqueue(i[2:0],8'd1,i[7:0]")
    new=new.replace("enqueue(8'd2,i[7:0]", "enqueue(i+2,8'd2,i[7:0]")
    new=new.replace("enqueue(8'd3,source", "enqueue(3'd6,8'd3,source")
    marker='   wr<=temp_wr[7:0];count<=temp_count[8:0];next_sequence<=temp_sequence[7:0];'
    dispatch='''   // Prefix zero is copied literally: adding zero to a partially X/Z
   // value would erase known bits in four-state simulation.
   sequence_value[0]=temp_sequence;slot_value[0]=temp_wr;
   for(p=1;p<8;p=p+1)begin
    sequence_value[p]=sequence_value[p-1]==255?8'd1:sequence_value[p-1]+8'd1;
    slot_value[p]=temp_wr+p[7:0];
   end
   offered_prefix=0;accepted_count=0;
   for(p=0;p<7;p=p+1)begin
    if(offered_valid[p])begin
     if(temp_count<256 && {6'd0,offered_prefix}<(9'd256-temp_count))begin
      accepted_valid[p]=1'b1;
      accepted_slot[p]=slot_value[offered_prefix];
      accepted_payload[p]={sequence_value[offered_prefix],offered_payload[p]};
      accepted_count=accepted_count+3'd1;
     end else overflow<=1;
     offered_prefix=offered_prefix+3'd1;
    end
   end
   for(b=0;b<8;b=b+1)begin
    bank_select=0;
    for(p=0;p<7;p=p+1)begin
     if(accepted_valid[p] && accepted_slot[p][2:0]==b[2:0])bank_select[p]=1'b1;
    end
    case(bank_select)
'''
    for p in range(7):dispatch+=f"     7'b{1<<p:07b}:begin next_write_enable[b]=1'b1;next_write_address[5*b +:5]=accepted_slot[{p}][7:3];next_write_data[160*b +:160]=accepted_payload[{p}];end\n"
    dispatch+='''     default:begin end
    endcase
   end
   if(accepted_count!=0)begin
    temp_wr=temp_wr+{5'd0,accepted_count};
    temp_count=temp_count+{6'd0,accepted_count};
    temp_sequence=sequence_value[accepted_count];
   end
'''
    assert new.count(marker)==1;new=new.replace(marker,dispatch+marker)
    (OUT/'cnc3_runtime_events.v').write_text(new);(OUT/'original.v').write_bytes((BASE/'original.v').read_bytes())
    (OUT/'original_diff.v').write_text(old.replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_original('))
    (OUT/'candidate_diff.v').write_text(new.replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_candidate('))
    (OUT/'candidate.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='canonical/cnc3_runtime_events.v',tofile='isolated/cnc3_runtime_events.v')))
    (OUT/'boundary_tb.sv').write_bytes((BASE/'boundary_tb.sv').read_bytes())
    prep={'status':'ISOLATED_FIXED_PRODUCER_PREFIX_CANDIDATE_PREPARED','source':str(H.parents[2]/'gateware/v3/runtime/cnc3_runtime_events.v'),'canonical_SHA256':sha(BASE/'original.v'),'candidate_SHA256':sha(OUT/'cnc3_runtime_events.v'),'base_capture_only_SHA256':sha(BASE/'cnc3_runtime_events.v'),'held_disabled_bus_delta_included':False,'strict_whole_bus_comparison':True,'prefix_zero_literal_preserved':True,'adopted':False}
    (OUT/'preparation-receipt.json').write_text(json.dumps(prep,indent=2)+'\n');print(json.dumps(prep))
    qualify=(H/'qualify_event_capture_r2.py').read_text().replace("OUT=H/'event-capture-select-r2'","OUT=H/'event-prefix-admission-r4'").replace('CAPTURE_ONLY_SELECTOR_EXHAUSTION_AND_STRICT_BOUNDARY_DIFFERENTIAL_PASS','CAPTURE_AND_PREFIX_STRICT_BOUNDARY_DIFFERENTIAL_PASS')
    (H/'qualify_event_prefix_r4.py').write_text(qualify)
    maps=(H/'map_event_capture_r2.py').read_text().replace("RUN=H/'event-capture-select-r2'","RUN=H/'event-prefix-admission-r4'")
    maps=maps.replace("[('original',RUN/'original.v'),('literal-case',RUN/'cnc3_runtime_events.v')]", "[('fixed-producer-prefix',RUN/'cnc3_runtime_events.v')]").replace('len(records)==2','len(records)==1').replace('NATIVE_EVENTS_ONLY_CAPTURE_COMPARISON_COMPLETE','NATIVE_EVENTS_ONLY_FIXED_PREFIX_MAP_COMPLETE')
    (H/'map_event_prefix_r4.py').write_text(maps)
if __name__=='__main__':main()
