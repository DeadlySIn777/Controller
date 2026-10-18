#include "cnc3_proto.h"
#include <stdio.h>
#include <string.h>
int main(void){unsigned cs,n;char h[4096];unsigned char in[176],out[176];
while(scanf("%u %u %4095s",&cs,&n,h)==3){if(n>176||strlen(h)!=2*n)return 2;
for(unsigned i=0;i<n;i++){unsigned v;if(sscanf(h+2*i,"%2x",&v)!=1)return 3;in[i]=(unsigned char)v;}
if(cs){struct cnc3_status s;if(cnc3_decode_cns3(in,n,&s))return 4;cnc3_encode_cns3(out,&s);}
else{struct cnc3_feedback f;if(cnc3_decode_cnf3(in,n,&f))return 5;cnc3_encode_cnf3(out,&f);}
for(unsigned i=0;i<n;i++){printf("%02x",out[i]);}puts("");}return 0;}