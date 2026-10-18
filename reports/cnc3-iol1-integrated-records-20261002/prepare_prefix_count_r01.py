from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;D=H/'prefix-arithmetic-stage-r01';D.mkdir()
src=H/'timing-width-stage-r02/cnc3_stepgen_runtime.v';old=src.read_text()
functions=''' function[31:0] count_next;
  input[31:0] c;input reverse;reg carry;integer k;
  begin carry=1;for(k=0;k<32;k=k+1)begin count_next[k]=c[k]^carry;carry=carry&(c[k]^reverse);end end
 endfunction
 function[31:0] magnitude_next;
  input[31:0] r;reg seen;integer k;
  begin seen=0;for(k=0;k<32;k=k+1)begin magnitude_next[k]=r[k]^(r[31]&seen);seen=seen|r[k];end end
 endfunction
'''
new=old.replace(' wire wanted_dir=',functions+' wire wanted_dir=').replace('wanted_dir?(~rate+32\'d1):rate','magnitude_next(rate)').replace("count+(dir?32'hffffffff:32'd1)",'count_next(count,dir)')
(D/'cnc3_stepgen_runtime.v').write_text(new,newline='\n');(D/'prior.v').write_text(old,newline='\n')
(D/'miter.v').write_text('''module prefix_miter(input wire[31:0]count,rate,input wire dir);
'''+functions+'''
always @*begin assert(count_next(count,dir)==count+(dir?32'hffffffff:32'd1));assert(magnitude_next(rate)==(rate[31]?(~rate+32'd1):rate));end
endmodule
''',newline='\n')
(D/'prove.ys').write_text('''read_verilog -formal -sv miter.v
prep -top prefix_miter -flatten
opt
chformal -lower
sat -prove-asserts -set-def-inputs -verify
''',newline='\n')
(D/'map.ys').write_text('''read_verilog -sv prior.v
chparam -set TIMER_BITS 10 cnc3_stepgen_runtime
synth_efinix -top cnc3_stepgen_runtime
tee -o prior-stat.json stat -json
design -reset
read_verilog -sv cnc3_stepgen_runtime.v
chparam -set TIMER_BITS 10 cnc3_stepgen_runtime
synth_efinix -top cnc3_stepgen_runtime
tee -o next-stat.json stat -json
''',newline='\n')
u='/mnt/'+D.drive[0].lower()+D.as_posix()[2:]
(D/'run.sh').write_text(f'''#!/bin/sh
set -eu
cd '{u}'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/prefix-arithmetic-r01"
cp *.v *.ys "$rootfs/work/prefix-arithmetic-r01/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/prefix-arithmetic-r01; yosys -V > version.txt; yosys -Q -T -s prove.ys > proof.log 2>&1; yosys -Q -T -s map.ys > mapping.log 2>&1"'
rc=$?
set -e
cp "$rootfs/work/prefix-arithmetic-r01/"*.txt "$rootfs/work/prefix-arithmetic-r01/"*.log "$rootfs/work/prefix-arithmetic-r01/"*.json .
exit "$rc"
''',newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in [*D.glob('*.v'),D/'prove.ys',D/'map.ys',D/'run.sh']}
r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh',u+'/run.sh'],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=150)
(D/'command.log').write_text(r.stdout+r.stderr,newline='\n');proof='SAT proof finished - no model found: SUCCESS!' in (D/'proof.log').read_text();res={k:json.loads((D/f'{k}-stat.json').read_text())['design']['num_cells_by_type'] for k in ('prior','next')};passed=r.returncode==0 and proof and all(sha(Path(p))==h for p,h in before.items())
(D/'receipt.json').write_text(json.dumps({'status':'PASS' if passed else 'FAIL','formal_scope':'all arbitrary32-bit count/rate andbothdirections; exact modulo2^32 ±1 and unsigned two-complement magnitude, includingINT_MIN. No new rate admission or timing behavior.','resources_single_runtime_only':res,'composed_fit_claim':False,'exact_inputs':before,'inputs_unchanged':all(sha(Path(p))==h for p,h in before.items()),'physical_vendor':False},indent=2)+'\n');print(json.dumps(res));assert passed
