"""Show why external X/reset edges do not initialize stable FF-fed LUTs."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/board-finish-20261017'
OUT=BASE/'release-review/vendor-ff-lut-reset-probe-r1';OUT.mkdir(exist_ok=False)
models=[Path('C:/Efinity/2026.1/sim_models/verilog')/n for n in ['efx_ff.v','efx_lut4.v']]
tb=OUT/'probe_tb.sv'
tb.write_text('''`timescale 1ns/1ps
module ff_lut_reset_probe_tb;
reg clk=0,rst_n=0,d=0;wire[3:0]q;wire nor4,nor3;
genvar i;generate for(i=0;i<4;i=i+1)begin:f
 EFX_FF x(.D(d),.CE(1'b1),.CLK(clk),.SR(rst_n),.Q(q[i]));
 defparam x.SR_POLARITY=1'b0;defparam x.SR_SYNC=1'b0;defparam x.SR_VALUE=1'b0;
end endgenerate
EFX_LUT4 four(.I0(q[0]),.I1(q[1]),.I2(q[2]),.I3(q[3]),.O(nor4));defparam four.LUTMASK=16'h0001;
EFX_LUT4 three(.I0(q[0]),.I1(q[1]),.I2(q[2]),.O(nor3));defparam three.LUTMASK=16'h0101;
integer initial_wrong=0,reset_still_wrong=0;
initial begin
 #1;$display("FF_INIT q=%h nor4=%b expected1 nor3=%b",q,nor4,nor3);
 initial_wrong=(q===0&&nor4===0&&nor3===1);
 clk=1'bx;rst_n=1'bx;d=1'bx;#1;clk=0;rst_n=0;d=0;#1;
 clk=1;#1;$display("EXPLICIT_EXTERNAL_X_AND_RESET q=%h nor4=%b expected1 nor3=%b",q,nor4,nor3);
 reset_still_wrong=(q===0&&nor4===0&&nor3===1);
 clk=0;rst_n=1;d=1;#1;clk=1;#1;
 $display("ACTUAL_FF_CHANGE q=%h nor4=%b expected0 nor3=%b",q,nor4,nor3);
 if(q!==4'hf||nor4!==0||nor3!==0)$fatal(1,"FF change control failed");
 rst_n=0;#1;$display("RESET_AFTER_ACTUAL_FF_CHANGE q=%h nor4=%b expected1 nor3=%b",q,nor4,nor3);
 if(q!==0||nor4!==1||nor3!==1)$fatal(1,"actual reset after FF transition control failed");
 if(!initial_wrong||!reset_still_wrong)$fatal(1,"reported startup mechanism not reproduced");
 $display("FF_FED_LUT_MODEL_STARTUP_DEFECT_REPRODUCED_WITH_RESET_CONTROL");$finish;
end
endmodule
''')
def linux(p):return '/mnt/'+p.drive[0].lower()+str(p.resolve())[2:].replace('\\','/')
commands=[['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17','iverilog','-g2012','-s','ff_lut_reset_probe_tb','-o',linux(OUT/'probe.vvp'),*map(linux,models),linux(tb)],
          ['wsl.exe','-d','GarciaMechBuilder','--','taskset','-c','16,17','vvp',linux(OUT/'probe.vvp')]]
executions=[]
for phase,cmd in zip(['compile','execute'],commands):
 r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
 (OUT/(phase+'.log')).write_bytes(r.stdout);executions.append({'phase':phase,'exit':r.returncode,'argv':cmd})
 if r.returncode:break
receipt={'status':'FF_FED_LUT_MODEL_STARTUP_DEFECT_REPRODUCED' if all(e['exit']==0 for e in executions) and len(executions)==2 else 'PROBE_FAILED',
 'models_SHA256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in models},
 'vendor_models_modified':False,'executions':executions,'output':(OUT/'execute.log').read_text() if (OUT/'execute.log').exists() else None,
 'scope':'Tiny primitive/model mechanism only; complete mapped event-engine behavior is a separate unclosed gate.'}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
