module crc_miter(input wire clk,reset_n,enable,miso,input wire[7:0]request_control,input wire[207:0]request_payload);
wire a0,b0,cs0,ns0,ck0,nk0,mo0,nm0,ac0,na0,fl0,nf0,fs0,nfs0,hg0,nhg0,ls0,nls0;
wire[7:0]sc0,nsc0,ctrl0,nctrl0;wire[5:0]ch0,nch0;wire[1:0]fp0,nfp0;wire[319:0]f0,n0;wire[1023:0]w0,nw0;
cnc_iol1_record_master_reference #(.CLASS_ID(8'd17),.SLOT_ID(4'd0)) old0(clk,reset_n,enable,miso,request_control,request_payload,a0,sc0,ctrl0,ch0,cs0,ck0,mo0,ac0,fl0,fs0,hg0,f0,ls0,fp0,w0);
cnc_iol1_record_master #(.CLASS_ID(8'd17),.SLOT_ID(4'd0)) new0(clk,reset_n,enable,miso,request_control,request_payload,b0,nsc0,nctrl0,nch0,ns0,nk0,nm0,na0,nf0,nfs0,nhg0,n0,nls0,nfp0,nw0);
always @* assert({a0,sc0,ctrl0,ch0,cs0,ck0,mo0,ac0,fl0,fs0,hg0,f0,ls0,fp0,w0}=={b0,nsc0,nctrl0,nch0,ns0,nk0,nm0,na0,nf0,nfs0,nhg0,n0,nls0,nfp0,nw0});
wire a1,b1,cs1,ns1,ck1,nk1,mo1,nm1,ac1,na1,fl1,nf1,fs1,nfs1,hg1,nhg1,ls1,nls1;
wire[7:0]sc1,nsc1,ctrl1,nctrl1;wire[5:0]ch1,nch1;wire[1:0]fp1,nfp1;wire[319:0]f1,n1;wire[1023:0]w1,nw1;
cnc_iol1_record_master_reference #(.CLASS_ID(8'd33),.SLOT_ID(4'd1)) old1(clk,reset_n,enable,miso,request_control,request_payload,a1,sc1,ctrl1,ch1,cs1,ck1,mo1,ac1,fl1,fs1,hg1,f1,ls1,fp1,w1);
cnc_iol1_record_master #(.CLASS_ID(8'd33),.SLOT_ID(4'd1)) new1(clk,reset_n,enable,miso,request_control,request_payload,b1,nsc1,nctrl1,nch1,ns1,nk1,nm1,na1,nf1,nfs1,nhg1,n1,nls1,nfp1,nw1);
always @* assert({a1,sc1,ctrl1,ch1,cs1,ck1,mo1,ac1,fl1,fs1,hg1,f1,ls1,fp1,w1}=={b1,nsc1,nctrl1,nch1,ns1,nk1,nm1,na1,nf1,nfs1,nhg1,n1,nls1,nfp1,nw1});
wire a2,b2,cs2,ns2,ck2,nk2,mo2,nm2,ac2,na2,fl2,nf2,fs2,nfs2,hg2,nhg2,ls2,nls2;
wire[7:0]sc2,nsc2,ctrl2,nctrl2;wire[5:0]ch2,nch2;wire[1:0]fp2,nfp2;wire[319:0]f2,n2;wire[1023:0]w2,nw2;
cnc_iol1_record_master_reference #(.CLASS_ID(8'd49),.SLOT_ID(4'd2)) old2(clk,reset_n,enable,miso,request_control,request_payload,a2,sc2,ctrl2,ch2,cs2,ck2,mo2,ac2,fl2,fs2,hg2,f2,ls2,fp2,w2);
cnc_iol1_record_master #(.CLASS_ID(8'd49),.SLOT_ID(4'd2)) new2(clk,reset_n,enable,miso,request_control,request_payload,b2,nsc2,nctrl2,nch2,ns2,nk2,nm2,na2,nf2,nfs2,nhg2,n2,nls2,nfp2,nw2);
always @* assert({a2,sc2,ctrl2,ch2,cs2,ck2,mo2,ac2,fl2,fs2,hg2,f2,ls2,fp2,w2}=={b2,nsc2,nctrl2,nch2,ns2,nk2,nm2,na2,nf2,nfs2,nhg2,n2,nls2,nfp2,nw2});
endmodule
