#include "iol1.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static unsigned checks;
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAILline%d:%s\n",__LINE__,#x);exit(1);}}while(0)
static iol1_transport complete={320,40,40,0,1};
static void crc(uint8_t *f){uint32_t c=iol1_crc32c(f,36);for(unsigned k=0;k<4;k++)f[36+k]=(uint8_t)(c>>(24-8*k));}
static void frame(uint8_t *f,unsigned c,unsigned s,unsigned ep,unsigned seq,unsigned ctl){memset(f,0,40);f[0]=0xa7;f[1]=1;f[2]=c;f[3]=s;f[4]=ep>>8;f[5]=ep;f[6]=seq>>8;f[7]=seq;f[8]=ctl;f[9]=0xff;crc(f);}
int main(void){
 CHECK(iol1_crc32c((const uint8_t *)"123456789",9)==0xe3069283u);
 uint8_t valid=0;
 CHECK(iol1_observation_age(0,0,&valid)==0xffffu);
 valid=1;CHECK(iol1_observation_age(0,0,&valid)==0);
 CHECK(iol1_observation_age(65534,0,&valid)==65534u);
 CHECK(iol1_observation_age(65535,0,&valid)==0xffffu);
 CHECK(iol1_observation_age(65536,0,&valid)==0xffffu);
 valid=1;CHECK(iol1_observation_age(10,0xfffffff0u,&valid)==26u);
 /* DIC and both DO caches: continuous IRQ observations cannot revive a
  * foreground sample after saturation, even when the whole timer wraps. */
 for(unsigned cache=0;cache<3;cache++){
  uint32_t sampled=100;valid=1;
  CHECK(iol1_observation_age(sampled+65534u,sampled,&valid)==65534u&&valid);
  CHECK(iol1_observation_age(sampled+65535u,sampled,&valid)==0xffffu&&!valid);
  CHECK(iol1_observation_age(0xffffffffu,sampled,&valid)==0xffffu&&!valid);
  CHECK(iol1_observation_age(sampled,sampled,&valid)==0xffffu&&!valid);
  CHECK(iol1_observation_age(sampled+1u,sampled,&valid)==0xffffu&&!valid);
  /* Only a fresh foreground acquisition publishes validity again. */
  sampled=101;valid=1;
  CHECK(iol1_observation_age(101,sampled,&valid)==0&&valid);
 }
 for(unsigned slot=0;slot<4;slot++){
  unsigned c=slot==0?IOL1_DIC:slot==3?IOL1_ACC:IOL1_DO;iol1_node n;uint8_t f[40],r[40];iol1_init(&n,c,slot);
  CHECK(!n.field_good&&n.state==IOL1_INIT);iol1_reply(&n,r);CHECK(r[8]==0&&r[4]==0&&r[5]==0);
  frame(f,c,slot,1,0,1);CHECK(iol1_accept(&n,f,complete,0));CHECK(n.good==1&&n.epoch==1&&n.state==IOL1_SYNCED);
  CHECK(!iol1_accept(&n,f,complete,100));CHECK(n.good==1&&n.accepted_us==0); /* duplicateSYNC cannot feed */
  frame(f,c,slot,1,1,0);CHECK(iol1_accept(&n,f,complete,200));CHECK(n.sequence==1&&n.good==2);
  CHECK(!iol1_accept(&n,f,complete,201)); /* stale sequence */
  frame(f,c,slot,1,2,0);
  for(unsigned bit=0;bit<320;bit++){uint8_t bad[40];memcpy(bad,f,40);bad[bit/8]^=(uint8_t)(1u<<(bit%8));CHECK(!iol1_accept(&n,bad,complete,202));}
  CHECK(n.good==2&&n.sequence==1&&n.accepted_us==200);
  for(unsigned edges=0;edges<640;edges++){iol1_transport t=complete;t.clocks=edges;if(edges!=320)CHECK(!iol1_accept(&n,f,t,203));}
  for(unsigned bytes=0;bytes<40;bytes++){iol1_transport t=complete;t.rx_bytes=bytes;CHECK(!iol1_accept(&n,f,t,204));t=complete;t.tx_bytes=bytes;CHECK(!iol1_accept(&n,f,t,204));}
  iol1_transport t=complete;t.overrun=1;CHECK(!iol1_accept(&n,f,t,205));t=complete;t.cs_high=0;CHECK(!iol1_accept(&n,f,t,205));
  for(unsigned ctl=2;ctl<256;ctl++){frame(f,c,slot,1,2,ctl);CHECK(!iol1_accept(&n,f,complete,206));}
  for(unsigned i=10;i<36;i++){frame(f,c,slot,1,2,0);f[i]=1;crc(f);CHECK(!iol1_accept(&n,f,complete,207));}
  for(unsigned i=0;i<4;i++){frame(f,c,slot,1,2,0);f[i]^=1;crc(f);CHECK(!iol1_accept(&n,f,complete,208));}
  frame(f,c,slot,0,2,0);CHECK(!iol1_accept(&n,f,complete,209));frame(f,c,slot,2,2,0);CHECK(!iol1_accept(&n,f,complete,209));
  frame(f,c,slot,1,2,0);f[9]=0;crc(f);CHECK(!iol1_accept(&n,f,complete,209));
  frame(f,c,slot,1,2,0);CHECK(iol1_accept(&n,f,complete,210));
  iol1_timeout(&n,1209);CHECK(n.state==IOL1_SYNCED);iol1_timeout(&n,1210);CHECK(n.state==IOL1_FAULT&&n.card_fault);
  frame(f,c,slot,1,3,0);CHECK(!iol1_accept(&n,f,complete,1211));
  /* A new diagnostic epoch can be accepted but cannot clear the fault latch. */
  frame(f,c,slot,2,0,1);CHECK(iol1_accept(&n,f,complete,1212));CHECK(n.card_fault);
  n.sequence=0xffff;frame(f,c,slot,2,1,0);CHECK(iol1_accept(&n,f,complete,1213));
  iol1_reply(&n,r);CHECK(!(r[8]&0x18));CHECK(iol1_crc32c(r,36)==((uint32_t)r[36]<<24|((uint32_t)r[37]<<16)|((uint32_t)r[38]<<8)|r[39]));
  /* No foreground timeout call: acceptance itself must reject a poll at the
   * exact deadline, preserving the last accepted timestamp and sequence. */
  iol1_init(&n,c,slot);frame(f,c,slot,1,0,1);CHECK(iol1_accept(&n,f,complete,0));
  frame(f,c,slot,1,1,0);CHECK(!iol1_accept(&n,f,complete,1000));
  CHECK(n.state==IOL1_FAULT&&n.card_fault&&n.accepted_us==0&&n.sequence==0&&n.good==1);
  /* Unsigned microsecond timer wrap preserves both the accepted boundary and
   * refusal boundary; the 1000us timeout and fixed frame format are unchanged. */
  iol1_init(&n,c,slot);frame(f,c,slot,1,0,1);CHECK(iol1_accept(&n,f,complete,0xffffff00u));
  frame(f,c,slot,1,1,0);CHECK(iol1_accept(&n,f,complete,0xffffff00u+999u));
  frame(f,c,slot,1,2,0);CHECK(!iol1_accept(&n,f,complete,0xffffff00u+1999u));
  CHECK(n.state==IOL1_FAULT&&n.sequence==1&&n.good==2);
 }
 printf("PASS %u exact protocol/negative checks\n",checks);return 0;
}
