"""Actual Icarus, Verilator and frozen C-oracle checks of staged CNC3 RTL."""
from pathlib import Path
import argparse, hashlib, json, random, subprocess, shutil, sys, importlib.util
HERE=Path(__file__).resolve().parent
STAGE=HERE/'stage-r01'; OUT=HERE/'proof-r01'
EXTERNAL=Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wsl(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def run(name,args,timeout=180):
 r=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=timeout)
 (OUT/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf8')
 if r.returncode:raise RuntimeError(f'{name} exit {r.returncode}: {(r.stdout+r.stderr)[-1800:]}')
 return r.stdout
def main():
 if OUT.exists():raise RuntimeError('Fresh proof output required')
 OUT.mkdir(parents=True)
 m=importlib.util.spec_from_file_location('p3',STAGE/'frozen/protocol_v3.py');p=importlib.util.module_from_spec(m);m.loader.exec_module(p);p._SPEC=p.Spec(str(STAGE/'frozen/spec/protocol.json'))
 originals={str(f):sha(f) for f in (EXTERNAL/'cnc3/src').glob('cnc3_proto*')}
 inputs={str(f.relative_to(STAGE)):sha(f) for f in STAGE.rglob('*') if f.is_file() and '__pycache__' not in f.parts}
 for name in inputs:
  dest=OUT/'inputs'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(STAGE/name,dest)
 c=OUT/'oracle';c.mkdir()
 for f in (EXTERNAL/'cnc3/src').glob('*.h'):shutil.copyfile(f,c/f.name)
 shutil.copyfile(EXTERNAL/'cnc3/src/cnc3_proto.c',c/'cnc3_proto.c')
 (c/'oracle.c').write_text('''#include "cnc3_proto.h"
#include <stdio.h>
#include <string.h>
int main(void){ unsigned cs,n; char hex[4096]; unsigned char b[2048];
while(scanf("%u %u %4095s",&cs,&n,hex)==3){ if(n>2048||strlen(hex)!=n*2)return 2;
for(unsigned i=0;i<n;i++){ unsigned v;if(sscanf(hex+2*i,"%2x",&v)!=1)return 3;b[i]=(unsigned char)v;}
printf("%d\\n",cnc3_validate_command((enum cnc3_cs)cs,b,n));}return 0;}''')
 vectors=json.loads((STAGE/'frozen/vectors.json').read_text())['vectors']
 cases=[(v['name'],int(v['chip_select']=='CS_CMD'),bytes.fromhex(v['hex'])) for v in vectors if v['chip_select']!='IOL1']
 # Exact frozen valid basis; independent C oracle determines each first rejection.
 bases=[row for row in cases if len(row[2]) in (96,176)]
 rand=random.Random(0x434e4333)
 for k in range(640):
  name,cs,data=rand.choice(bases);b=bytearray(data)
  for _ in range(1+(k%3)):
   ix=rand.randrange(len(b)-2);b[ix]^=1<<rand.randrange(8)
  if k%5:b[-2:]=p.crc16_ccitt_false(b[:-2]).to_bytes(2,'big')
  cases.append((f'mutation{k}:{name}',cs,bytes(b)))
 for name,cs,data in list(bases)[:12]:
  cases.extend([(name+':short',cs,data[:-1]),(name+':long',cs,data+b'\x00'),(name+':otherCS',1-cs,data)])
 # All command opcodes and all valid CONFIGURE_IO page classes use real reference builders.
 for op in [0,1,2,3,4,8,9,10,11,13,14,16,5]:
  kw={'session':1,'sequence':1,'channel_mask':1} if op not in (0,1,5,16) else {'session':1}
  if op in (4,8,9):kw['channel_mask']=0
  if op==13:kw['fields']={'rate_0':0x01000000}
  try:
   cs,data=p.encode_command(op,**kw);cases.append((f'opcode{op}',int(cs=='CS_CMD'),data))
  except p.ProtocolError:pass
 cfg=p.encode_configure();cases.append(('validconfigure',0,cfg))
 # Valid embedded MAINT, then bad inner CRC with correctly resealed outer CRC.
 inner=bytearray(40);inner[0:2]=b'\xa7\x01';inner[2]=0x21;inner[3]=1;inner[5]=1;inner[8]=0x21
 inner[36:]=p.crc32c(inner[:36]).to_bytes(4,'big')
 fb=bytearray(176);fb[:6]=b'CNC3\x03\x0c';fb[11]=1;fb[16]=0;fb[17:57]=inner;fb[-2:]=p.crc16_ccitt_false(fb[:-2]).to_bytes(2,'big')
 cases.append(('maintvalid',0,bytes(fb)));fb[53]^=1;fb[-2:]=p.crc16_ccitt_false(fb[:-2]).to_bytes(2,'big');cases.append(('maintbadinner',0,bytes(fb)))
 (OUT/'oracle-input.txt').write_text('\n'.join(f'{cs} {len(b)} {b.hex()}' for _,cs,b in cases)+'\n')
 script=OUT/'run.sh';script.write_text(f'''#!/bin/sh
set -eu
cd '{wsl(OUT)}'
gcc -std=c11 -O1 -Wall -Wextra -Werror oracle/oracle.c oracle/cnc3_proto.c -o oracle/check
oracle/check < oracle-input.txt > oracle-output.txt
iverilog -g2012 -s tb -o validate.vvp '{wsl(STAGE)}/rtl/cnc3_command_validate.v' validate_tb.sv
vvp validate.vvp
iverilog -g2012 -s tb -o spi.vvp '{wsl(STAGE)}/rtl/cnc3_command_validate.v' '{wsl(STAGE)}/rtl/cnc3_spi_transport.v' '{wsl(STAGE)}/rtl/cnc3_frame_endpoint.v' spi_tb.sv
vvp spi.vvp
''',newline='\n')
 # First compile C oracle independently before writing expected RTL checks.
 run('oracle-build',['wsl','-d','GarciaMechBuilder','--','sh','-c',f"cd '{wsl(OUT)}' && gcc -std=c11 -O1 -Wall -Wextra -Werror oracle/oracle.c oracle/cnc3_proto.c -o oracle/check && oracle/check < oracle-input.txt > oracle-output.txt"])
 expected=[int(x) for x in (OUT/'oracle-output.txt').read_text().splitlines()]
 tb=['`timescale 1ns/1ps','module tb; reg [1407:0] f;reg fb,cg,ig;reg[8:0] n;wire[7:0] result;integer checks=0;', 'cnc3_command_validate dut(f,fb,n,cg,ig,result);initial begin']
 for (name,cs,b),want in zip(cases,expected):
  aligned=(b[:176]+bytes(max(0,176-len(b))))
  crc_good=(len(b)>=2 and p.crc16_ccitt_false(b[:-2])==int.from_bytes(b[-2:],'big'))
  inner_good=len(b)>=57 and p.crc32c(b[17:53])==int.from_bytes(b[53:57],'big')
  tb.append(f"f=1408'h{aligned.hex()};fb={1-cs};n={len(b)};cg={int(crc_good)};ig={int(inner_good)};#1;if(result!={want}) $fatal(1,\"case{len(tb)}:{name} result=%d expected={want}\",result);checks=checks+1;")
 tb.append('$display("STATIC_C_ORACLE_PASS checks=%0d",checks);$finish;end endmodule')
 (OUT/'validate_tb.sv').write_text('\n'.join(tb)+'\n')
 # Hardware field packers are checked against exact original reference offsets,
 # including all twelve counter slots and the mandated CNS3 reserved-zero span.
 pack=['`timescale 1ns/1ps','module tb;']
 checks=[]
 response_cases=[]
 for layout_name,module,tag in [('fb_response_CNF3','cnc3_feedback_pack','fb'),('cmd_response_CNS3','cnc3_status_pack','cmd')]:
  lay=p.spec().layout(layout_name);width=(lay.length-2)*8;connections=[];values={}
  for f in lay.fields:
   if f.name in {'magic','abi','crc16'} or f.must_be_zero:continue
   v=rand.getrandbits(f.size*8);values[f.name]=v.to_bytes(f.size,'big') if f.type in ('bytes','ascii') else ([(v>>(f.size*8-(j+1)*p._SCALAR[f.elem][0]*8))&((1<<(p._SCALAR[f.elem][0]*8))-1) for j in range(f.count)] if f.count is not None else (v-(1<<(f.size*8)) if f.type.startswith('s') and v>>(f.size*8-1) else v))
   pack.append(f"reg [{f.size*8-1}:0] {tag}_{f.name}={f.size*8}'h{v:x};")
   connections.append(f'.{f.name}({tag}_{f.name})')
  pack.append(f'wire[{width-1}:0] {tag}_out;'+module+' dut_'+tag+'('+','.join(connections)+f',.payload({tag}_out));')
  raw=p.pack_layout(layout_name,dict(values,magic='CNF3' if tag=='fb' else 'CNS3',abi=3))
  sealed=p.seal(layout_name,raw);response_cases.append((int(tag=='cmd'),sealed))
  checks.append(f"if({tag}_out!={width}'h{raw[:-2].hex()})$fatal(1,\"{module} mapping\");")
 pack+=['initial begin #1;']+checks+['$display("RESPONSE_PACKERS_PASS fields='+str(len(connections))+'");$finish;end endmodule']
 (OUT/'pack_tb.sv').write_text('\n'.join(pack)+'\n')
 (c/'roundtrip.c').write_text('''#include "cnc3_proto.h"
#include <stdio.h>
#include <string.h>
int main(void){unsigned cs,n;char h[4096];unsigned char in[176],out[176];
while(scanf("%u %u %4095s",&cs,&n,h)==3){if(n>176||strlen(h)!=2*n)return 2;
for(unsigned i=0;i<n;i++){unsigned v;if(sscanf(h+2*i,"%2x",&v)!=1)return 3;in[i]=(unsigned char)v;}
if(cs){struct cnc3_status s;if(cnc3_decode_cns3(in,n,&s))return 4;cnc3_encode_cns3(out,&s);}
else{struct cnc3_feedback f;if(cnc3_decode_cnf3(in,n,&f))return 5;cnc3_encode_cnf3(out,&f);}
for(unsigned i=0;i<n;i++){printf("%02x",out[i]);}puts("");}return 0;}''')
 (OUT/'response-input.txt').write_text('\n'.join(f'{cs} {len(b)} {b.hex()}' for cs,b in response_cases)+'\n')
 nop=next(b for name,cs,b in cases if name=='is1_nop_cmd');read=next(b for name,cs,b in cases if name=='is1_fb_read_session0');update=next(b for name,cs,b in cases if name=='update_12ch_limits');maint=next(b for name,cs,b in cases if name=='maintvalid')
 # Nonzero response payloads expose bit order, field snapshots and streamed CRC.
 cmd_resp=bytearray((i*11+3)%256 for i in range(96));cmd_resp[:5]=b'CNS3\x03';cmd_resp[-2:]=p.crc16_ccitt_false(cmd_resp[:-2]).to_bytes(2,'big')
 fb_resp=bytearray((i*17+5)%256 for i in range(176));fb_resp[:5]=b'CNF3\x03';fb_resp[-2:]=p.crc16_ccitt_false(fb_resp[:-2]).to_bytes(2,'big')
 badinner=next(b for name,cs,b in cases if name=='maintbadinner')
 spi=SPI_TB.replace('CMD_BODY',cmd_resp[:-2].hex()).replace('FB_BODY',fb_resp[:-2].hex()).replace('CMD_FULL',cmd_resp.hex()).replace('FB_FULL',fb_resp.hex()).replace('NOP_HEX',nop.hex()).replace('READ_HEX',read.hex()).replace('UPDATE_HEX',update.hex()).replace('MAINT_HEX',maint.hex()).replace('INNER_BAD',badinner.hex())
 (OUT/'spi_tb.sv').write_text(spi)
 with script.open('a',newline='\n') as handle:
  handle.write(f"iverilog -g2012 -s tb -o pack.vvp '{wsl(STAGE)}/rtl/cnc3_feedback_pack.v' '{wsl(STAGE)}/rtl/cnc3_status_pack.v' pack_tb.sv\nvvp pack.vvp\n")
  handle.write('gcc -std=c11 -O1 -Wall -Wextra -Werror oracle/roundtrip.c oracle/cnc3_proto.c -o oracle/roundtrip\noracle/roundtrip < response-input.txt > response-output.txt\n')
 output=run('actual-RTL',['wsl','-d','GarciaMechBuilder','--','sh',wsl(script)],300)
 assert (OUT/'response-output.txt').read_text().splitlines()==[b.hex() for _,b in response_cases],'Frozen C response decode/encode differs'
 lint=run('verilator-lint',['wsl','-d','GarciaMechBuilder','--','verilator','--lint-only','--timing','-Wall','-Wno-fatal','--top-module','cnc3_frame_endpoint',*[wsl(STAGE/'rtl'/n) for n in ['cnc3_command_validate.v','cnc3_spi_transport.v','cnc3_frame_endpoint.v']]],180)
 # Actual synth is run separately in rootfs, which carries Yosys; no vendor fit claim.
 receipt={'status':'PASS','evidence_type':'ACTUAL_CNC3_STRUCTURAL_RTL_SPI','static_oracle_cases':len(cases),'response_C_roundtrip_classes':len(response_cases),'physical_measurement':False,'stateful_CNC3_endpoint':False,'CNC3_HAL':False,'full_twelve_joint_machine':False,'vendor_fit_timing':False,'source_stage_hashes':inputs,'immutable_input_copies':'inputs','original_external_sources_unchanged':all(sha(Path(f))==h for f,h in originals.items()),'logs':{str(f.name):sha(f) for f in OUT.glob('*.log')},'actual_output':output,'verilator_warnings_retained':True}
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({k:receipt[k] for k in ['status','static_oracle_cases','stateful_CNC3_endpoint']}))

SPI_TB=r'''`timescale 1ns/1ps
module tb;
reg clk=0;always #10 clk=~clk;reg rst=0,fb=1,cmd=1,sck=0,mosi=0,ready=0;
reg[1391:0] fp=1392'hFB_BODY;reg[751:0] sp=752'hCMD_BODY;
wire miso,oe,valid,reqfb,fault,reject,snap,snapfb;wire[1407:0] request_frame;wire[7:0] op,code;wire[15:0]mask;wire[31:0]sess,seq;wire[383:0]rates;wire[239:0]outs;
integer accepts=0,rejects=0,checks=0;reg[1407:0] reply;
cnc3_frame_endpoint dut(clk,rst,fb,cmd,sck,mosi,fp,sp,miso,oe,ready,valid,reqfb,request_frame,op,mask,sess,seq,rates,outs,fault,reject,code,snap,snapfb);
always @(posedge clk) if(reject) rejects=rejects+1;
task ticks(input integer n);begin repeat(n)@(negedge clk);end endtask
task transaction(input bit f,input[1407:0] data,input integer bits,input integer pre,input integer post,input integer half,input integer idle=12,input integer phase=0,input bit handoff=0);
integer i;begin
ticks(idle);#(phase);if(f)fb=0;else cmd=0;#(pre*20);reply=0;
for(i=0;i<bits;i=i+1)begin mosi=data[1407-i];#(half*20);sck=1;reply={reply[1406:0],miso};#(half*20);sck=0;end
#(post*20);fb=1;cmd=1;if(handoff)begin if(f)cmd=0;else fb=0;end ticks(8);end endtask
task consume;begin if(!valid)$fatal(1,"missing request");ready=1;ticks(2);ready=0;ticks(2);if(valid)$fatal(1,"request not consumed");checks=checks+1;end endtask
initial begin
ticks(4);rst=1;ticks(16);if(oe||valid||fault)$fatal(1,"reset defaults");
transaction(0,{768'hNOP_HEX,640'b0},768,8,8,4);
if(!valid||op!=0||reqfb||request_frame[1407-:768]!=768'hNOP_HEX)$fatal(1,"NOP decode");
if(reply[767:0]!=768'hCMD_FULL)$fatal(1,"CMD streamed snapshot/CRC");consume();
transaction(1,1408'hREAD_HEX,1408,8,8,4);
if(!valid||op!=16||!reqfb||request_frame!=1408'hREAD_HEX)$fatal(1,"FB decode");
if(reply!=1408'hFB_FULL)$fatal(1,"FB streamed snapshot/CRC");consume();
transaction(0,{768'hUPDATE_HEX,640'b0},768,8,8,4);if(!valid||mask!=12'hfff||rates[63:32]!=32'h01000000||rates[31:0]!=32'hff000000)$fatal(1,"12-rate atomic decode");consume();
transaction(1,1408'hMAINT_HEX,1408,8,8,4);if(!valid||op!=12)$fatal(1,"embedded CRC32C valid");consume();
// Valid pending frame remains byte-exact while a second complete request arrives.
transaction(0,{768'hNOP_HEX,640'b0},768,8,8,4);
transaction(1,1408'hREAD_HEX,1408,8,8,4);
if(!valid||request_frame[1407-:768]!=768'hNOP_HEX||!fault)$fatal(1,"pending overwrite");consume();
// Snapshots are captured at CS assertion, not read live during transfer.
fork begin transaction(0,{768'hNOP_HEX,640'b0},768,8,8,4);end
begin ticks(40);sp=0;end join
if(reply[767:0]!=768'hCMD_FULL)$fatal(1,"torn status snapshot");consume();
// CRC corruption, short, long, pre/post guard, SCLK too fast, wrong CS opcode.
transaction(0,{768'hNOP_HEX ^ 768'h1,640'b0},768,8,8,4);if(valid)$fatal(1,"bad CRC accepted");checks=checks+1;
transaction(0,{768'hNOP_HEX,640'b0},767,8,8,4);if(valid)$fatal(1,"short accepted");checks=checks+1;
transaction(0,{768'hNOP_HEX,640'b0},769,8,8,4);if(valid)$fatal(1,"long accepted");checks=checks+1;
transaction(0,{768'hNOP_HEX,640'b0},768,0,8,4);if(valid)$fatal(1,"CS preguard accepted");checks=checks+1;
transaction(0,{768'hNOP_HEX,640'b0},768,8,0,4);if(valid)$fatal(1,"CS postguard accepted");checks=checks+1;
transaction(0,{768'hNOP_HEX,640'b0},768,8,8,3);if(valid)$fatal(1,"fast SCLK accepted");checks=checks+1;
transaction(0,1408'hREAD_HEX,768,8,8,4);if(valid)$fatal(1,"wrong opcode accepted");checks=checks+1;
transaction(1,1408'hINNER_BAD,1408,8,8,4);if(valid||code!=16)$fatal(1,"bad embedded CRC accepted");checks=checks+1;
transaction(0,{768'hNOP_HEX,640'b0},768,3,8,4);if(valid)$fatal(1,"7-tick CS to first-rise accepted");checks=checks+1;
transaction(0,{768'hNOP_HEX,640'b0},768,4,8,4);if(!valid)$fatal(1,"8-tick CS to first-rise rejected");consume();
transaction(0,{768'hNOP_HEX,640'b0},768,8,7,4);if(valid)$fatal(1,"7-tick last-fall to CS accepted");checks=checks+1;
transaction(0,{768'hNOP_HEX,640'b0},768,8,8,4,12,0,1);if(valid)$fatal(1,"zero-gap CMD to FB handoff accepted");fb=1;cmd=1;ticks(12);checks=checks+1;
transaction(1,1408'hREAD_HEX,1408,8,8,4,12,0,1);if(valid)$fatal(1,"zero-gap FB to CMD handoff accepted");fb=1;cmd=1;ticks(12);checks=checks+1;
// All asynchronous input phases of the 20ns core period at max allowed SCLK.
begin integer ph;for(ph=0;ph<20;ph=ph+1)begin transaction(0,{768'hNOP_HEX,640'b0},768,8,8,4,12,ph);consume();end end
ticks(12);fb=0;cmd=0;ticks(20);if(oe)$fatal(1,"both CS drove MISO");fb=1;cmd=1;ticks(12);if(valid)$fatal(1,"both CS accepted");checks=checks+1;
// Asynchronous reset immediately releases bus and discards pending transaction.
fb=0;ticks(12);rst=0;#1;if(oe||valid)$fatal(1,"reset did not release");fb=1;cmd=1;sck=0;ticks(5);rst=1;ticks(16);if(fault)$fatal(1,"reset did not clear fault");checks=checks+1;
if(rejects<9)$fatal(1,"missing reject pulses");
$display("ACTUAL_SPI_PASS checks=%0d rejects=%0d",checks,rejects);$finish;
end
initial begin #12000000;$fatal(1,"timeout");end
endmodule
'''
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path);args=a.parse_args()
 if args.out:OUT=args.out.resolve()
 try:main()
 except Exception as e:
  if OUT.exists() and not (OUT/'receipt.json').exists():
   (OUT/'receipt.json').write_text(json.dumps({'status':'FAIL','reason':str(e),'full_machine_validation':False},indent=2)+'\n')
  raise
