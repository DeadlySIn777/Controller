#include "cnc3_proto.h"
#include <stdio.h>
#include <string.h>
int main(void){ unsigned cs,n; char hex[4096]; unsigned char b[2048];
while(scanf("%u %u %4095s",&cs,&n,hex)==3){ if(n>2048||strlen(hex)!=n*2)return 2;
for(unsigned i=0;i<n;i++){ unsigned v;if(sscanf(hex+2*i,"%2x",&v)!=1)return 3;b[i]=(unsigned char)v;}
printf("%d\n",cnc3_validate_command((enum cnc3_cs)cs,b,n));}return 0;}