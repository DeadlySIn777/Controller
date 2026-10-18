from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent
D=H/'timer-share-formal-r01'
if D.exists():raise RuntimeError('fresh proof required')
D.mkdir()
S=H/'timer-share-stage-r01'
for name,src,module in [('old.v','cnc3_stepgen_runtime_reference.v','cnc3_stepgen_runtime_reference'),('new.v','cnc3_stepgen_runtime.v','cnc3_stepgen_runtime')]:
 t=(S/src).read_text().replace('output wire quiescent','output wire quiescent, output wire[63:0] timer_witness, output wire[31:0] phase_witness')
 t=t.replace(' assign quiescent=', ' assign timer_witness={high_left,low_left,setup_left,hold_left};\n assign phase_witness=phase;\n assign quiescent=')
 (D/name).write_text(t,newline='\n')
(D/'miter.v').write_text('''module timer_miter(input wire clk,rst_n,enable,stop,input wire signed[31:0]rate,input wire[15:0]pulse_ticks,space_ticks,setup_ticks,hold_ticks);
wire os,od,of,oq,ns,nd,nf,nq;wire[31:0]oc,nc,op,np;wire[63:0]ot,nt;
cnc3_stepgen_runtime_reference old(clk,rst_n,enable,stop,rate,pulse_ticks,space_ticks,setup_ticks,hold_ticks,os,od,oc,of,oq,ot,op);
cnc3_stepgen_runtime new(clk,rst_n,enable,stop,rate,pulse_ticks,space_ticks,setup_ticks,hold_ticks,ns,nd,nc,nf,nq,nt,np);
always @* begin
 assert({os,od,oc,of,oq,ot,op}=={ns,nd,nc,nf,nq,nt,np});
 // Reachable-state invariant: HIGH/LOW/SETUP timers never overlap.
 assert(!((|ot[63:48])&&(|ot[47:32])));
 assert(!((|ot[63:48])&&(|ot[31:16])));
 assert(!((|ot[47:32])&&(|ot[31:16])));
end
endmodule
''',newline='\n')
(D/'prove.ys').write_text('''read_verilog -formal -sv old.v new.v miter.v
prep -top timer_miter -flatten
async2sync
opt
sat -seq 3 -tempinduct -prove-asserts -set-def-inputs -set-init-zero -maxsteps 12 -verify
''',newline='\n')
u='/mnt/'+D.drive[0].lower()+D.as_posix()[2:]
(D/'prove.sh').write_text(f'''#!/bin/sh
set -eu
cd '{u}'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/timer-proof-r01"
cp *.v prove.ys "$rootfs/work/timer-proof-r01/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/timer-proof-r01; yosys -V > version.txt; yosys -Q -T -s prove.ys > proof.log 2>&1"'
rc=$?
set -e
cp "$rootfs/work/timer-proof-r01/"*.txt "$rootfs/work/timer-proof-r01/"*.log .
exit "$rc"
''',newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(D/'input-witness.json').write_text(json.dumps({str(p):sha(p) for p in [*S.glob('*.v'),S/'tb_timer_equivalence.sv',*D.glob('*.v'),D/'prove.ys',D/'prove.sh']},indent=2)+'\n')
print(D)
