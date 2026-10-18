module prefix_miter(input wire[31:0]count,rate,input wire dir);
 function[31:0] count_next;
  input[31:0] c;input reverse;reg carry;integer k;
  begin carry=1;for(k=0;k<32;k=k+1)begin count_next[k]=c[k]^carry;carry=carry&(c[k]^reverse);end end
 endfunction
 function[31:0] magnitude_next;
  input[31:0] r;reg seen;integer k;
  begin seen=0;for(k=0;k<32;k=k+1)begin magnitude_next[k]=r[k]^(r[31]&seen);seen=seen|r[k];end end
 endfunction

always @*begin assert(count_next(count,dir)==count+(dir?32'hffffffff:32'd1));assert(magnitude_next(rate)==(rate[31]?(~rate+32'd1):rate));end
endmodule
