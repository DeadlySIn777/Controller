module cmp_miter(input wire[31:0]x,k);
function u_ge32;input[31:0] x,k;reg equal,greater;integer n;
 begin equal=1;greater=0;for(n=31;n>=0;n=n-1)begin greater=greater|(equal&&x[n]&&!k[n]);equal=equal&&!(x[n]^k[n]);end u_ge32=greater|equal;end
endfunction
function u_le32;input[31:0] x,k;reg equal,less;integer n;
 begin equal=1;less=0;for(n=31;n>=0;n=n-1)begin less=less|(equal&&!x[n]&&k[n]);equal=equal&&!(x[n]^k[n]);end u_le32=less|equal;end
endfunction
always @*begin assert(u_ge32(x,k)==(x>=k));assert(u_le32(x,k)==(x<=k));end
endmodule
