"""Tiny unmodified vendor LUT model startup/exhaustive binary probe."""
from pathlib import Path
import re,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/board-finish-20261017'
OUT=BASE/'release-review/vendor-lut-startup-probe-r1'
OUT.mkdir(exist_ok=False)
model=Path('C:/Efinity/2026.1/sim_models/verilog/efx_lut4.v')
mapped=BASE/'event-producer-fifo-r1/native-events-map/outflow/cnc3_runtime_events.map.v'
masks=sorted({int(x,16) for x in re.findall(r'\.LUTMASK\s*=\s*16\x27h([0-9a-fA-F]+);',mapped.read_text())})
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
source=['`timescale 1ns/1ps','module vendor_lut_probe_tb;','reg [3:0] a=0; reg[2:0] three=0;reg[1:0] two=0;','wire [%d:0] y;'%(len(masks)-1)]
for i,mask in enumerate(masks):
    source.append(f"EFX_LUT4 l{i}(.I0(a[0]),.I1(a[1]),.I2(a[2]),.I3(a[3]),.O(y[{i}])); defparam l{i}.LUTMASK=16'h{mask:04x};")
source += ["wire nor3,nor2; EFX_LUT4 u3(.I0(three[0]),.I1(three[1]),.I2(three[2]),.O(nor3));defparam u3.LUTMASK=16'h0101;",
           "EFX_LUT4 u2(.I0(two[0]),.I1(two[1]),.O(nor2));defparam u2.LUTMASK=16'h1111;",
           'integer n; integer failures=0;initial begin',
           '#1;$display("INITIAL_ZERO a=%h y=%h nor3=%b nor2=%b",a,y,nor3,nor2);']
for i,mask in enumerate(masks):
    source.append(f"if(y[{i}]!==1'b{mask&1}) begin failures=failures+1;$display(\"INITIAL_MASK_FAIL mask={mask:04x} actual=%b expected={mask&1}\",y[{i}]);end")
source += ['a=4\'bx;three=3\'bx;two=2\'bx;#1;a=0;three=0;two=0;#1;',
           '$display("EXPLICIT_X_TO_ZERO a=%h y=%h nor3=%b nor2=%b",a,y,nor3,nor2);',
           'for(n=0;n<16;n=n+1)begin a=n;#1;']
for i,mask in enumerate(masks):
    source.append(f"if(y[{i}]!==((16'h{mask:04x}>>n)&1'b1))begin failures=failures+1;$display(\"MASK_FAIL mask={mask:04x} input=%h actual=%b\",a,y[{i}]);end")
source += ['end','$display("VENDOR_LUT_TINY_RESULT masks=%0d failures=%0d",'+str(len(masks))+',failures);$finish;end endmodule']
tb=OUT/'probe_tb.sv';tb.write_text('\n'.join(source)+'\n')
commands=[['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17','iverilog','-g2012','-s','vendor_lut_probe_tb','-o',linux(OUT/'probe.vvp'),linux(model),linux(tb)],
          ['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17','vvp',linux(OUT/'probe.vvp')]]
executions=[]
for phase,cmd in zip(['compile','execute'],commands):
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
    (OUT/(phase+'.log')).write_bytes(r.stdout)
    executions.append({'phase':phase,'exit':r.returncode,'argv':cmd})
    if r.returncode:break
receipt={'status':'PROBE_OBSERVATION_ONLY','distinct_native_masks':len(masks),'vendor_models_modified':False,
    'model_SHA256':hashlib.sha256(model.read_bytes()).hexdigest(),'native_map_SHA256':hashlib.sha256(mapped.read_bytes()).hexdigest(),
    'executions':executions,'output':(OUT/'execute.log').read_text() if (OUT/'execute.log').exists() else None}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
