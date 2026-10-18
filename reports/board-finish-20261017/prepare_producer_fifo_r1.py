"""Prepare an isolated seven-producer FIFO experiment. Canonical RTL is read-only."""
from pathlib import Path
import hashlib,json,re

H=Path(__file__).resolve().parent
OUT=H/'event-producer-fifo-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(s,old,new):
    assert s.count(old)==1,old[:120]
    return s.replace(old,new)

def main():
    assert not OUT.exists();OUT.mkdir()
    source=H/'release-review/event-capture-select-r2/cnc3_runtime_events.v'
    original=H/'release-review/event-capture-select-r2/original.v'
    s=source.read_text()
    a=s.index(' // At most seven producers');b=s.index(' reg [8:0] count;',a)
    s=s[:a]+''' // Seven fixed producers share a global 256-entry admission/order contract.
 // Every producer can write once per cycle without a wide producer/bank crossbar.
 reg[6:0] write_enable;reg[55:0] write_address;reg[1175:0] write_data;
 wire[167:0] bank_data[0:6];reg[7:0] prefetched_rd;
 reg [7:0] rd,wr,next_sequence,snapshot_sequence,delivered_sequence;
 reg [7:0] producer_rd[0:6],producer_wr[0:6],producer_prefetched_rd[0:6];
 reg [8:0] producer_count[0:6],temp_producer_count[0:6];
 reg [7:0] temp_producer_wr[0:6];
 genvar bank;
 generate for(bank=0;bank<7;bank=bank+1)begin:producers
  cnc3_event_producer_bank memory(.clk(clk),.write_enable(write_enable[bank]),
   .write_address(write_address[8*bank +:8]),.write_data(write_data[168*bank +:168]),
   .read_address(producer_rd[bank]),.read_data(bank_data[bank]));
 end endgenerate
'''+s[b:]
    s=replace(s,'integer i,j,k;','integer i,j,k,p;')
    s=replace(s,'reg[7:0]next_write_enable;reg[39:0]next_write_address;reg[1279:0]next_write_data;',
      'reg[6:0]next_write_enable;reg[55:0]next_write_address;reg[1175:0]next_write_data;')
    a=s.index(' wire head_pending=');b=s.index(' assign event_status=',a)
    s=s[:a]+''' wire [6:0] producer_head_valid;
 generate for(bank=0;bank<7;bank=bank+1)begin:heads
  wire pending=write_enable[bank] && write_address[8*bank +:8]==producer_rd[bank];
  assign producer_head_valid[bank]=producer_count[bank]!=0 &&
   producer_prefetched_rd[bank]==producer_rd[bank] && !pending &&
   bank_data[bank][167:160]==rd;
 end endgenerate
 wire head_valid=count!=0 && prefetched_rd==rd && |producer_head_valid;
 reg [159:0] selected_head;
 reg [2:0] head_producer;
 integer h;
 always@*begin
  selected_head=0;head_producer=0;
  for(h=0;h<7;h=h+1)if(producer_head_valid[h])begin
   selected_head=bank_data[h][159:0];head_producer=h;
  end
 end
 assign event_head=head_valid?selected_head:160'd0;
'''+s[b:]
    a=s.index(' task enqueue;');b=s.index(' always@(posedge clk or negedge rst_n)',a)
    s=s[:a]+''' task enqueue;
  input integer producer;
  input [7:0] kind,origin,flags;
  input [95:0] data;
  begin
   if(temp_count<256)begin
    next_write_enable[producer]=1;
    next_write_address[8*producer +:8]=temp_producer_wr[producer];
    next_write_data[168*producer +:168]={temp_wr,temp_sequence,kind,origin,flags,ticks,data};
    temp_producer_wr[producer]=temp_producer_wr[producer]+8'd1;
    temp_producer_count[producer]=temp_producer_count[producer]+9'd1;
    temp_wr=temp_wr+8'd1;temp_count=temp_count+9'd1;
    temp_sequence=temp_sequence==255?8'd1:temp_sequence+8'd1;
   end else overflow<=1;
  end
 endtask
'''+s[b:]
    s=replace(s,'   write_enable<=0;write_address<=0;write_data<=0;prefetched_rd<=0;',
      '''   write_enable<=0;write_address<=0;write_data<=0;prefetched_rd<=0;
   for(p=0;p<7;p=p+1)begin
    producer_rd[p]<=0;producer_wr[p]<=0;producer_count[p]<=0;producer_prefetched_rd[p]<=0;
   end''')
    s=replace(s,'   temp_count=count;temp_wr=wr;temp_sequence=next_sequence;',
      '''   temp_count=count;temp_wr=wr;temp_sequence=next_sequence;
   for(p=0;p<7;p=p+1)begin
    temp_producer_count[p]=producer_count[p];temp_producer_wr[p]=producer_wr[p];
    producer_prefetched_rd[p]<=producer_rd[p];
   end''')
    s=replace(s,"    rd<=rd+1'b1;temp_count=temp_count-1;delivered_sequence<=0;",
      """    rd<=rd+1'b1;temp_count=temp_count-1;delivered_sequence<=0;
    producer_rd[head_producer]<=producer_rd[head_producer]+8'd1;
    temp_producer_count[head_producer]=temp_producer_count[head_producer]-9'd1;""")
    s=replace(s,"enqueue(8'd1,i[7:0]", "enqueue(i,8'd1,i[7:0]")
    s=replace(s,"enqueue(8'd2,i[7:0]", "enqueue(i+2,8'd2,i[7:0]")
    s=replace(s,"enqueue(8'd3,source", "enqueue(6,8'd3,source")
    s=replace(s,'   wr<=temp_wr[7:0];count<=temp_count[8:0];next_sequence<=temp_sequence[7:0];',
      '''   wr<=temp_wr[7:0];count<=temp_count[8:0];next_sequence<=temp_sequence[7:0];
   for(p=0;p<7;p=p+1)begin
    producer_wr[p]<=temp_producer_wr[p];producer_count[p]<=temp_producer_count[p];
   end''')
    s=replace(s,'    write_enable<=0;prefetched_rd<=0;',
      '''    write_enable<=0;prefetched_rd<=0;
    for(p=0;p<7;p=p+1)begin
     producer_rd[p]<=0;producer_wr[p]<=0;producer_count[p]<=0;producer_prefetched_rd[p]<=0;
    end''')
    s+='''
// Registered memory read and collision bypass preserve the original write-first
// visibility. Tags are global modulo-256 positions, independent of sequence IDs.
module cnc3_event_producer_bank(input wire clk,write_enable,
 input wire[7:0]write_address,read_address,input wire[167:0]write_data,
 output wire[167:0]read_data);
 reg[167:0]memory[0:255];
 reg[167:0]ram_read,forward_data;
 reg forward_valid;
 always@(posedge clk)begin
  if(write_enable)memory[write_address]<=write_data;
  ram_read<=memory[read_address];
  if(write_enable && write_address==read_address)forward_valid<=1'b1;
  else forward_valid<=1'b0;
  forward_data<=write_data;
 end
 assign read_data=forward_valid?forward_data:ram_read;
endmodule
'''
    (OUT/'cnc3_runtime_events.v').write_text(s)
    (OUT/'original_diff.v').write_text(original.read_text().replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_original('))
    (OUT/'candidate_diff.v').write_text(s.replace('module cnc3_runtime_events(', 'module cnc3_runtime_events_candidate('))
    rec={'status':'ISOLATED_EXPERIMENT_PREPARED_NOT_VERIFIED','source':str(source),'source_SHA256':sha(source),'original':str(original),'original_SHA256':sha(original),'candidate_SHA256':sha(OUT/'cnc3_runtime_events.v'),'script_SHA256':sha(Path(__file__)),'canonical_unchanged':sha(original)==sha(H.parent.parent/'gateware/v3/runtime/cnc3_runtime_events.v'),'adopted':False}
    (OUT/'preparation-receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
    print(json.dumps(rec,indent=2))
if __name__=='__main__':main()
