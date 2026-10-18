#include "cnc3_proto.h"
#include <stdio.h>
#include <limits.h>
#include <string.h>
int main(void){
 const int32_t rates[]={0,0x01000000,-0x01000000,0x01000001,-0x01000001,INT_MIN,INT_MAX};
 for(unsigned i=0;i<sizeof rates/sizeof rates[0];++i){
  struct cnc3_cmd c;memset(&c,0,sizeof c);c.opcode=CNC3_OP_UPDATE;
  c.session=1;c.sequence=1;c.channel_mask=0xfff;c.rate[0]=rates[i];
  uint8_t frame[CNC3_CS_CMD_BYTES];memset(frame,0,sizeof frame);
  int build=cnc3_build_cmd(frame,&c);
  int incoming=cnc3_validate_command(CNC3_CS_CMD,frame,sizeof frame);
  int forbidden=rates[i]>CNC3_MAX_RATE||rates[i]<-CNC3_MAX_RATE;
  printf("rate=%d build=%d incoming=%d forbidden=%d\n",rates[i],build,incoming,forbidden);
  if(build!=(forbidden?CNC3_E_RATE_CLAMP:CNC3_VALID)||incoming!=CNC3_VALID)return 1;
 }
 puts("FROZEN_C_RATE_BOUNDARY_CONFIRMED cases=7");return 0;
}
