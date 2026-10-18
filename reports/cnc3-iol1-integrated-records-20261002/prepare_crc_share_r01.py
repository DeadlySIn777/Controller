from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent
D=H/'crc-share-stage-r01'
if D.exists():raise RuntimeError('fresh stage required')
D.mkdir();src=H/'timer-share-record-candidate-r02/cnc_iol1_record_master.v';old=src.read_text()
(D/'cnc_iol1_record_master_original.v').write_text(old,newline='\n')
oldcalls=['crc_byte(tx_crc,octet(tx_frame,{26\'b0,prep_index}))','crc_byte(tx_crc,octet(tx_frame,35))','crc_byte(rx_crc,{rx_shift[6:0],miso})']
for c in oldcalls:assert old.count(c)==1,c
new=old.replace('    assign checked_frame', '''    // PREP and SHIFT are mutually exclusive. One combinational byte CRC
    // datapath serves TX preparation and the received complete-byte update.
    wire [31:0] shared_crc = crc_byte(state==PREP ? tx_crc : rx_crc,
       state==PREP ? octet(tx_frame,{26'b0,prep_index}) : {rx_shift[6:0],miso});
    assign checked_frame''')
for c in oldcalls:new=new.replace(c,'shared_crc')
(D/'cnc_iol1_record_master.v').write_text(new,newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(D/'transform-ledger.json').write_text(json.dumps({'prior':str(src),'prior_sha256':sha(src),'next_sha256':sha(D/'cnc_iol1_record_master.v'),'exact_crc_call_replacements':oldcalls,'transaction_or_clock_or_timing_delta':False},indent=2)+'\n')
F=H/'crc-share-formal-r01';F.mkdir()
for name,text,module in [('old.v',old,'cnc_iol1_record_master_reference'),('new.v',new,'cnc_iol1_record_master')]:
 text=text.replace('module cnc_iol1_record_master #(',f'module {module} #(')
 text=text.replace('output wire link_synced, output wire [1:0] failed_polls','output wire link_synced, output wire [1:0] failed_polls,output wire[1023:0] state_witness')
 text=text.replace('    assign checked_frame', '''    assign state_witness={state,phase,period_count,guard_count,bit_index,prep_index,tx_frame,rx_shift,tx_crc,rx_crc,synced,tx_sequence,expected_sequence,failures,expected_control,expected_chunk};
    assign checked_frame''')
 (F/name).write_text(text,newline='\n')
m='''module crc_miter(input wire clk,reset_n,enable,miso,input wire[7:0]request_control,input wire[207:0]request_payload);
'''
for i,cl in enumerate([17,33,49]):
 m+=f'''wire a{i},b{i},cs{i},ns{i},ck{i},nk{i},mo{i},nm{i},ac{i},na{i},fl{i},nf{i},fs{i},nfs{i},hg{i},nhg{i},ls{i},nls{i};
wire[7:0]sc{i},nsc{i},ctrl{i},nctrl{i};wire[5:0]ch{i},nch{i};wire[1:0]fp{i},nfp{i};wire[319:0]f{i},n{i};wire[1023:0]w{i},nw{i};
cnc_iol1_record_master_reference #(.CLASS_ID(8'd{cl}),.SLOT_ID(4'd{i})) old{i}(clk,reset_n,enable,miso,request_control,request_payload,a{i},sc{i},ctrl{i},ch{i},cs{i},ck{i},mo{i},ac{i},fl{i},fs{i},hg{i},f{i},ls{i},fp{i},w{i});
cnc_iol1_record_master #(.CLASS_ID(8'd{cl}),.SLOT_ID(4'd{i})) new{i}(clk,reset_n,enable,miso,request_control,request_payload,b{i},nsc{i},nctrl{i},nch{i},ns{i},nk{i},nm{i},na{i},nf{i},nfs{i},nhg{i},n{i},nls{i},nfp{i},nw{i});
always @* assert({{a{i},sc{i},ctrl{i},ch{i},cs{i},ck{i},mo{i},ac{i},fl{i},fs{i},hg{i},f{i},ls{i},fp{i},w{i}}}=={{b{i},nsc{i},nctrl{i},nch{i},ns{i},nk{i},nm{i},na{i},nf{i},nfs{i},nhg{i},n{i},nls{i},nfp{i},nw{i}}});
'''
m+='endmodule\n';(F/'miter.v').write_text(m,newline='\n')
(F/'prove.ys').write_text('''read_verilog -formal -sv old.v new.v miter.v
prep -top crc_miter -flatten
async2sync
opt
sat -seq 3 -tempinduct -prove-asserts -set-def-inputs -set-init-zero -maxsteps 8 -verify
''',newline='\n')
u='/mnt/'+F.drive[0].lower()+F.as_posix()[2:]
(F/'prove.sh').write_text(f'''#!/bin/sh
set -eu
cd '{u}'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/crc-share-proof-r01"
cp *.v prove.ys "$rootfs/work/crc-share-proof-r01/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/crc-share-proof-r01; yosys -V > version.txt; yosys -Q -T -s prove.ys > proof.log 2>&1"'
rc=$?
set -e
cp "$rootfs/work/crc-share-proof-r01/"*.txt "$rootfs/work/crc-share-proof-r01/"*.log .
exit "$rc"
''',newline='\n')
(F/'input-witness.json').write_text(json.dumps({str(p):sha(p) for p in [src,*D.glob('*.v'),*F.glob('*.v'),F/'prove.ys',F/'prove.sh']},indent=2)+'\n')
print(F)
