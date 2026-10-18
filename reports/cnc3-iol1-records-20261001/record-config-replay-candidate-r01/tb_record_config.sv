`timescale 1ns/1ps
module tb_record_config;
 reg cs=1,sclk=0,mosi=0,miso=0;
 reg [319:0] incoming,prepared,received;
 integer bits,result,checks=0;
 always @(negedge cs)begin bits=0;incoming=0;$record_reply(prepared);miso=prepared[319];end
 always @(posedge sclk)if(!cs)begin incoming={incoming[318:0],mosi};bits++;end
 always @(negedge sclk)if(!cs)miso=bits<320?prepared[319-bits]:0;
 always @(posedge cs)if(bits>0)begin $record_accept(incoming,bits,$rtoi($realtime/1000.0),result);miso=0;end
 function automatic[31:0] crc(input[287:0] b);
  reg[31:0] c;reg[7:0] x;integer i,j;
  begin c='1;for(i=0;i<36;i++)begin x=b[287-i*8-:8];for(j=0;j<8;j++)c=(c[0]^x[j])?((c>>1)^32'h82f63b78):(c>>1);end crc=c^32'hffffffff;end
 endfunction
 function automatic[319:0] frame(input[15:0] epoch,seq,input[7:0] ctrl,chunk,input[23:0] groups);
  reg[319:0] f;begin f=0;f[319:288]=32'ha7011100;f[287:272]=epoch;f[271:256]=seq;f[255:248]=ctrl;f[247:240]=255;
   if(ctrl==16)begin f[239:232]=0;f[231:224]=1;f[223:200]=groups;end
   else if(ctrl==8)f[239:232]=chunk;
   f[31:0]=crc(f[319:32]);frame=f;
  end
 endfunction
 task automatic ck(input bit condition,input string label);begin checks++;if(!condition)$fatal(1,"FAIL %s",label);end endtask
 task automatic send(input[319:0] f,input integer n=320);
  integer i;begin received=0;cs=0;#20000;
   for(i=319;i>=320-n;i--)begin mosi=f[i];#60;sclk=1;received={received[318:0],miso};#60;sclk=0;end
   #5000;cs=1;mosi=0;#1000;
  end
 endtask
 integer k;reg[319:0] f;reg[31:0] config_crc;reg[4095:0] assembled;
 initial begin bits=0;$record_reset;#100;
  send(frame(1,0,1,0,0));ck(result==1,"actual wire SYNC");
  send(frame(1,1,16,0,24'h0001ff));ck(result==1,"actual wire DIC CONFIG");
  send(frame(1,2,0,0,0));ck(result==1&&received[247:240]==1,"next actual reply applied config page");config_crc=received[63:32];ck(config_crc!=0,"actual appliedCRC nonzero");
  $record_raw(24'hffffff);
  for(k=0;k<64;k++)begin
   send(frame(1,3+k,8,k,0));ck(result==1,"wire IDENT accepted");
   if(k>0)begin ck(received[247:240]==(128+k-1)&&received[111:96]==(k-1),"previous actual reply chunk index/telemetry");assembled[4095-(k-1)*64-:64]=received[95:32];end
   ck(received[255:248]==8'h21,"no ACTIVE/permission despiteconfig andrecord fixture");
  end
  send(frame(1,67,0,0,0));assembled[63:0]=received[95:32];ck(assembled[4095:4064]==32'h4d425232&&assembled[31:0]==32'h434d5432,"full wire record envelope assembled");
  ck(received[239:232]==8'hff&&received[231:224]==8'hff&&received[223:216]==0,"three distinct configured groups actual filtered images");
  // Corruption cannot refresh sequence; next exact command can recover.
  f=frame(1,68,16,0,24'h010203);send(f^1);ck(result==0,"wire badCRCCONFIG rejected");
  send(frame(1,68,0,0,0));ck(result==1,"wire rejectedCONFIG sequence retained");
  send(frame(1,69,16,0,24'h010203),319);ck(result==0,"truncatedCONFIG rejected");
  send(frame(1,69,0,0,0));ck(result==1,"truncatedCONFIG no progress");
  f=frame(1,70,16,0,24'h010203);f[231:224]=2;f[31:0]=crc(f[319:32]);send(f);ck(result==0,"sealed wrongformatCONFIG rejected");
  send(frame(1,70,0,0,0));ck(result==1,"wrongformat no progress");
  ck(received[63:32]==config_crc,"all rejectedCONFIG retainappliedCRC");
  $display("PASS actual wire record/config checks=%0d",checks);$finish;
 end
endmodule
