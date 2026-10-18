from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;D=H/'crc-share-combinational-formal-r02'
if D.exists():raise RuntimeError('fresh proof required')
D.mkdir()
F=H/'crc-share-formal-r01';(F/'aborted-receipt.json').write_text(json.dumps({'status':'NOT_RUN','completed_sequential_proof':False,'reason':'Exact proof process deliberately stopped after >6min/7.7GiB to bound resource use; preserved base/induction trace, no proof acceptance. Combinational datapath proof and actual wire regressions are separate successor evidence.','proof_log_sha256':hashlib.sha256((F/'proof.log').read_bytes()).hexdigest()},indent=2)+'\n')
src=(H/'crc-share-stage-r01/cnc_iol1_record_master_original.v').read_text()
fun=src[src.index('    function [31:0] crc_byte;'):src.index('    function [15:0] next_sequence;')]
t='''module crc_datapath_miter(input wire prep,input wire[31:0] tx_crc,rx_crc,input wire[319:0]tx_frame,input wire[5:0]prep_index,input wire[7:0]received_byte);
'''+fun+'''
wire[31:0] shared_crc=crc_byte(prep?tx_crc:rx_crc,prep?octet(tx_frame,{26'b0,prep_index}):received_byte);
always @* begin
 // PREP's reachable index is0..35. SHIFT uses the complete received byte.
 if(prep && prep_index<=35)assert(shared_crc==crc_byte(tx_crc,octet(tx_frame,{26'b0,prep_index})));
 if(prep && prep_index==35)assert(shared_crc==crc_byte(tx_crc,octet(tx_frame,35)));
 if(!prep)assert(shared_crc==crc_byte(rx_crc,received_byte));
end
endmodule
'''
(D/'miter.v').write_text(t,newline='\n');(D/'prove.ys').write_text('''read_verilog -formal -sv miter.v
prep -top crc_datapath_miter -flatten
opt
sat -prove-asserts -set-def-inputs -verify
''',newline='\n')
u='/mnt/'+D.drive[0].lower()+D.as_posix()[2:]
(D/'prove.sh').write_text(f'''#!/bin/sh
set -eu
cd '{u}'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/crc-datapath-r02"
cp miter.v prove.ys "$rootfs/work/crc-datapath-r02/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/crc-datapath-r02; yosys -V > version.txt; yosys -Q -T -s prove.ys > proof.log 2>&1"'
rc=$?
set -e
cp "$rootfs/work/crc-datapath-r02/"*.txt "$rootfs/work/crc-datapath-r02/"*.log .
exit "$rc"
''',newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in [*D.glob('*.v'),D/'prove.ys',D/'prove.sh',* (H/'crc-share-stage-r01').glob('*.v')]}
r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh',u+'/prove.sh'],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=150)
(D/'command.log').write_text(r.stdout+r.stderr,newline='\n');log=(D/'proof.log').read_text() if (D/'proof.log').exists() else '';passed=r.returncode==0 and 'SAT proof finished - no model found: SUCCESS!' in log and all(sha(Path(p))==h for p,h in before.items())
(D/'receipt.json').write_text(json.dumps({'status':'PASS' if passed else 'FAIL','formal_scope':'arbitrary32-bit TX/RX CRCs/arbitrary320-bit frame/arbitrary8-bit RX byte; PREP indices0..35 and final35 output, SHIFT update exactly equivalent. This is combinational next-CRC proof, not full stateful temporal induction.','exact_inputs':before,'inputs_unchanged':all(sha(Path(p))==h for p,h in before.items()),'proof_log_sha256':sha(D/'proof.log'),'exit_code':r.returncode,'full_sequential_proof':False,'physical_or_vendor_fit':False},indent=2)+'\n')
print('PASS' if passed else 'FAIL');raise SystemExit(0 if passed else 1)
