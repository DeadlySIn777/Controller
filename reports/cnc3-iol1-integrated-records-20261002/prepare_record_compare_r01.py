from pathlib import Path
import hashlib,json,shutil,subprocess
H=Path(__file__).resolve().parent;D=H/'record-compare-stage-r01';D.mkdir()
f=(H/'constant-compare-stage-r01/cnc3_command_validate_logic.v').read_text();fun=f[f.index('function u_ge32;'):f.index('always @* begin')]
changes={
'cnc_mbr2_stream_checker.v':[
('b<33','!u_ge32({24\'d0,b},32\'d33)'),('b>126','!u_le32({24\'d0,b},32\'d126)'),
('d[15:8]<=3','u_le32({24\'d0,d[15:8]},32\'d3)'),('d[7:0]>=3','u_ge32({24\'d0,d[7:0]},32\'d3)'),
('d[63:48]<=1','u_le32({16\'d0,d[63:48]},32\'d1)'),('d[47:32]>=1','u_ge32({16\'d0,d[47:32]},32\'d1)'),
('d[31:16]<=3','u_le32({16\'d0,d[31:16]},32\'d3)'),('d[15:0]>=3','u_ge32({16\'d0,d[15:0]},32\'d3)'),
('index>=27','u_ge32({26\'d0,index},32\'d27)'),('index<=54','u_le32({26\'d0,index},32\'d54)')],
'cnc_iol1_record_master.v':[
('response_age <= 16\'d440','u_le32({16\'d0,response_age},32\'d440)'),
('octet(rx_shift,9)<=2','u_le32({24\'d0,octet(rx_shift,9)},32\'d2)'),
('octet(rx_shift,9)<=11','u_le32({24\'d0,octet(rx_shift,9)},32\'d11)'),
('bit_index >= 32','u_ge32({23\'d0,bit_index},32\'d32)'),
('{ {(32-PERIOD_W){1\'b0}},period_count} < PERIOD_CYCLES-1','!u_ge32({ {(32-PERIOD_W){1\'b0}},period_count},PERIOD_CYCLES-1)')]
}
ledger=[]
for fn,pairs in changes.items():
 src=H/'timing-width-record-candidate-r02'/fn;old=src.read_text();new=old
 for a,b in pairs:
  n=new.count(a);assert n>=1,(fn,a);new=new.replace(a,b);ledger.append({'module':fn,'old':a,'new':b,'occurrences':n,'unsigned_zero_extension_explicit':True})
 pos=new.index(' function') if ' function' in new else new.index('    function')
 new=new[:pos]+fun+'\n'+new[pos:]
 (D/fn).write_text(new,newline='\n');(D/(fn+'.prior')).write_text(old,newline='\n')
(D/'comparator-miter.v').write_text('''module cmp_miter(input wire[31:0]x,k);
'''+fun+'''always @*begin assert(u_ge32(x,k)==(x>=k));assert(u_le32(x,k)==(x<=k));end
endmodule
''',newline='\n')
(D/'prove.ys').write_text('''read_verilog -formal -sv comparator-miter.v
prep -top cmp_miter -flatten
opt
chformal -lower
sat -prove-asserts -set-def-inputs -verify
''',newline='\n')
u='/mnt/'+D.drive[0].lower()+D.as_posix()[2:]
(D/'run.sh').write_text(f'''#!/bin/sh
set -eu
cd '{u}'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/record-compare-r01"
cp comparator-miter.v prove.ys "$rootfs/work/record-compare-r01/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/record-compare-r01; yosys -V > version.txt; yosys -Q -T -s prove.ys > proof.log 2>&1"'
rc=$?
set -e
cp "$rootfs/work/record-compare-r01/"*.txt "$rootfs/work/record-compare-r01/"*.log .
exit "$rc"
''',newline='\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in [*D.glob('*.v'),D/'prove.ys',D/'run.sh']}
r=subprocess.run(['wsl','-d','GarciaMechBuilder','--','sh',u+'/run.sh'],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=150)
(D/'command.log').write_text(r.stdout+r.stderr,newline='\n');passed=r.returncode==0 and 'SAT proof finished - no model found: SUCCESS!' in (D/'proof.log').read_text() and all(sha(Path(p))==h for p,h in before.items())
(D/'receipt.json').write_text(json.dumps({'status':'PASS' if passed else 'FAIL','formal_scope':'arbitrary unsigned32-bit x/k comparison equivalence; exact source expressions zeroextended, constants/parameter values unchanged. No state/timing/authority change.','exact_transform_ledger':ledger,'exact_inputs':before,'inputs_unchanged':all(sha(Path(p))==h for p,h in before.items()),'physical_or_vendor_fit':False},indent=2)+'\n');assert passed
T=H/'prefix-record-candidate-r01';shutil.copytree(H/'timing-width-record-candidate-r02',T,ignore=shutil.ignore_patterns('__pycache__'))
for fn in changes:shutil.copyfile(D/fn,T/fn)
shutil.copyfile(H/'prefix-arithmetic-stage-r01/cnc3_stepgen_runtime.v',T/'inputs/motion/cnc3_stepgen_runtime.v')
(T/'prefix-and-record-comparison-provenance.json').write_text(json.dumps({'comparator_receipt':str(D/'receipt.json'),'prefix_count_magnitude_receipt':str(H/'prefix-arithmetic-stage-r01/receipt.json'),'only_delta':'formally equivalent unsigned compares and exact32-bit count/magnitude Boolean arithmetic; no storage/state/latency/rate change'},indent=2)+'\n')
m=json.loads((T/'bundle-manifest.json').read_text());m['files']={p.relative_to(T).as_posix():sha(p) for p in T.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p not in (T/'bundle-manifest.json',T/'freeze-receipt.json')};(T/'bundle-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print(T,sha(T/'bundle-manifest.json'))
