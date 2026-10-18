module timer_miter(input wire clk,rst_n,enable,stop,input wire signed[31:0]rate,input wire[15:0]pulse_ticks,space_ticks,setup_ticks,hold_ticks);
wire os,od,of,oq,ns,nd,nf,nq;wire[31:0]oc,nc,op,np;wire[63:0]ot,nt;
cnc3_stepgen_runtime_reference old(clk,rst_n,enable,stop,rate,pulse_ticks,space_ticks,setup_ticks,hold_ticks,os,od,oc,of,oq,ot,op);
cnc3_stepgen_runtime #(.TIMER_BITS(10)) new(clk,rst_n,enable,stop,rate,pulse_ticks,space_ticks,setup_ticks,hold_ticks,ns,nd,nc,nf,nq,nt,np);
always @* begin
 assume(pulse_ticks<=1023 && space_ticks<=1023 && setup_ticks<=1023 && hold_ticks<=1023);
 assert(ot[63:58]==0 && ot[47:42]==0 && ot[31:26]==0 && ot[15:10]==0);

 assert({os,od,oc,of,oq,ot,op}=={ns,nd,nc,nf,nq,nt,np});
 // Reachable-state invariant: HIGH/LOW/SETUP timers never overlap.
 assert(!((|ot[63:48])&&(|ot[47:32])));
 assert(!((|ot[63:48])&&(|ot[31:16])));
 assert(!((|ot[47:32])&&(|ot[31:16])));
end
endmodule
