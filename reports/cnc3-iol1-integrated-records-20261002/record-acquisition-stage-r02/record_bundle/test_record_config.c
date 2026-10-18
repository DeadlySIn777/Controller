#include "iol1.h"
#include "dic_filter.h"
#include "board_record.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
#define CK(x,s) do{checks++;if(!(x)){fprintf(stderr,"FAIL %s:%u %s\n",__FILE__,__LINE__,s);exit(1);}}while(0)
static void seal(uint8_t *f){uint32_t c=iol1_crc32c(f,36);for(unsigned i=0;i<4;i++)f[36+i]=(uint8_t)(c>>(24-8*i));}
static void record_crc(uint8_t *p){uint32_t c=iol1_crc32c(p,504);for(unsigned i=0;i<4;i++)p[504+i]=(uint8_t)(c>>(24-8*i));}
static void command(uint8_t *f,uint8_t cls,unsigned slot,unsigned epoch,unsigned seq,unsigned ctrl){
 memset(f,0,40);f[0]=0xa7;f[1]=1;f[2]=cls;f[3]=(uint8_t)slot;f[4]=(uint8_t)(epoch>>8);f[5]=(uint8_t)epoch;f[6]=(uint8_t)(seq>>8);f[7]=(uint8_t)seq;f[8]=(uint8_t)ctrl;f[9]=255;seal(f);
}
static iol1_transport valid={320,40,40,0,1};
static void unchanged(const iol1_node *a,const iol1_node *b){
 CK(a->epoch==b->epoch&&a->sequence==b->sequence&&a->accepted_us==b->accepted_us&&a->good==b->good,"rejected frame no accepted progress");
 CK(a->dic_config_valid==b->dic_config_valid&&a->dic_config_crc==b->dic_config_crc&&a->dic_config_generation==b->dic_config_generation&&!memcmp(a->dic_config,b->dic_config,24),"rejected frame config atomic");
 CK(a->ident_pending==b->ident_pending&&a->ident_chunk==b->ident_chunk,"rejected frame no stale identity selection");
}
int main(int argc,char **argv){
 CK(argc==2,"fixture path");FILE *file=fopen(argv[1],"rb");CK(file!=0,"fixture opens");uint8_t record[4][512],new_record[4][512],uid[4][12];CK(fread(record,1,sizeof(record),file)==sizeof(record),"exact4 records");CK(fread(new_record,1,sizeof(new_record),file)==sizeof(new_record),"exact4 successor records");fclose(file);
 for(unsigned s=0;s<4;s++)for(unsigned i=0;i<12;i++)uid[s][i]=(uint8_t)(s*16+i+1);
 uint8_t cls[4]={0x11,0x21,0x21,0x31};
 for(unsigned s=0;s<4;s++){
  CK(mb_record_integrity(record[s],cls[s],s,uid[s]),"actualC record integrity/UID/profile");
  uint8_t erased[512];memset(erased,255,512);CK(mb_record_select(erased,erased,cls[s],s,uid[s])==-1,"erased defaults unprovisioned");
  CK(mb_record_select(record[s],erased,cls[s],s,uid[s])==0,"one valid independentpage");
  CK(mb_record_select(erased,record[s],cls[s],s,uid[s])==1,"fallback independentpage");
  CK(mb_record_select(record[s],record[s],cls[s],s,uid[s])==0,"identicalduplicate coherent");
  CK(mb_record_select(record[s],new_record[s],cls[s],s,uid[s])==1,"newersignedgeneration selected");
  CK(mb_record_select(new_record[s],record[s],cls[s],s,uid[s])==0,"newersignedgeneration independent ofslotorder");
  uint8_t conflict[512];memcpy(conflict,record[s],512);conflict[164]^=1;record_crc(conflict);
  CK(mb_record_integrity(conflict,cls[s],s,uid[s]),"CRC-valid diagnostic conflict, signature not claimed");
  CK(mb_record_select(record[s],conflict,cls[s],s,uid[s])==-1,"same generation different descriptor failsclosed");
  memcpy(conflict,new_record[s],512);conflict[68]^=1;record_crc(conflict);
  CK(mb_record_integrity(conflict,cls[s],s,uid[s]),"CRC-valid source-lineage conflict, signature not claimed");
  CK(mb_record_select(record[s],conflict,cls[s],s,uid[s])==-1,"higher generation foreign source lineage failsclosed");
  for(unsigned b=0;b<4096;b++){
   uint8_t changed[512];memcpy(changed,record[s],512);changed[b/8]^=(uint8_t)(1u<<(b%8));
   CK(!mb_record_integrity(changed,cls[s],s,uid[s]),"every record bitflip rejected");
  }
  for(unsigned cut=0;cut<64;cut++){
   uint8_t torn[512];memset(torn,255,512);memcpy(torn,new_record[s],cut*8);
   CK(!mb_record_integrity(torn,cls[s],s,uid[s]),"torn doubleword prefix rejected including missing commit");
   CK(mb_record_select(record[s],torn,cls[s],s,uid[s])==0,"every torn successor prefix preserves priorpage");
  }
  CK(!mb_record_integrity(record[s],cls[s],s,uid[(s+1)%4]),"foreignMCU UID rejected");
 }
 // Execute the same age helper linked into all four real targets.
 CK(iol1_sample_age_us(0,0,0)==65535,"cold DIC sample unavailable");
 CK(iol1_sample_age_us(100,100,1)==0,"actual current sample age0");
 CK(iol1_sample_age_us(65534,0,1)==65534,"DIC age65534");
 CK(iol1_sample_age_us(65535,0,1)==65535,"DIC age65535 unavailable");
 CK(iol1_sample_age_us(65536,0,1)==65535,"DIC age65536 must not wrap young");
 CK(iol1_sample_age_us(0xffffffffu,0,1)==65535,"very old sample saturated");
 CK(iol1_sample_age_us(0,0xffffffffu,1)==1,"timer rollover1us");
 CK(iol1_sample_age_us(0x0000ffeeu,0xfffffff0u,1)==65534,"rollover65534");
 CK(iol1_sample_age_us(0x0000ffefu,0xfffffff0u,1)==65535,"rollover65535");
 CK(iol1_sample_age_us(0x0000fff0u,0xfffffff0u,1)==65535,"rollover65536");
 uint8_t sample_valid=1;
 if(iol1_sample_age_us(65536,0,sample_valid)==65535)sample_valid=0;
 CK(iol1_sample_age_us(1,0,sample_valid)==65535,"latched stale cannot revive after full timerwrap");
 sample_valid=1;CK(iol1_sample_age_us(11,10,sample_valid)==1,"only actual resample restores young age");
 iol1_node n;iol1_init(&n,IOL1_DIC,0);uint8_t f[40],reply[40];
 CK(!n.dic_config_valid&&!n.factory_record&&!n.hw_major,"cold unconfigured unprovisioned");
 command(f,IOL1_DIC,0,1,0,1);CK(iol1_accept(&n,f,valid,10),"real SYNC");
 command(f,IOL1_DIC,0,1,1,0x10);f[10]=0;f[11]=1;f[12]=0;f[13]=1;f[14]=255;seal(f);
 CK(iol1_accept(&n,f,valid,100),"actual CONFIG_WRITE accepted");CK(n.dic_config_valid&&n.dic_config[2]==1&&n.dic_config[3]==255,"three distinct groups atomically applied");
 CK(n.dic_config_crc==iol1_crc32c(f+11,24),"applied configCRC exact24 bytes");
 iol1_reply(&n,reply);CK(reply[9]==1&&reply[32]==(uint8_t)(n.dic_config_crc>>24)&&reply[35]==(uint8_t)n.dic_config_crc,"actual configCRC telemetry");
 CK((reply[8]&0x1f)==1,"CONFIG noACTIVE/permit/output authority");
 n.factory_record=record[0];n.hw_major=1;
 for(unsigned chunk=0;chunk<64;chunk++){
  command(f,IOL1_DIC,0,1,n.sequence+1,8);f[10]=(uint8_t)chunk;seal(f);
  CK(iol1_accept(&n,f,valid,200+chunk),"IDENT_READ actual next sequence");iol1_reply(&n,reply);
  CK(reply[9]==(0x80|chunk)&&reply[26]==0&&reply[27]==chunk&&!memcmp(reply+28,record[0]+chunk*8,8),"exact readonly 8B chunk");
  CK(reply[3]==0x10&&((reply[8]&0x1f)==1),"observedmajor noACTIVE");
 }
 // Every physical boundary, policy byte, header, sequence and CRC fails before commit.
 command(f,IOL1_DIC,0,1,n.sequence+1,0x10);f[11]=1;seal(f);
 for(unsigned i=0;i<6;i++){
  iol1_node q=n;iol1_transport t=valid;switch(i){case 0:t.clocks=319;break;case 1:t.clocks=321;break;case 2:t.rx_bytes=39;break;case 3:t.tx_bytes=39;break;case 4:t.overrun=1;break;default:t.cs_high=0;}
  CK(!iol1_accept(&q,f,t,500),"physicalframe rejected");unchanged(&n,&q);
 }
 for(unsigned b=0;b<320;b++){
  uint8_t bad[40];memcpy(bad,f,40);bad[b/8]^=(uint8_t)(1u<<(b%8));iol1_node q=n;
  CK(!iol1_accept(&q,bad,valid,500),"every physicalframe bitflip CRC rejected");unchanged(&n,&q);
 }
 for(unsigned i=0;i<36;i++){
  if(i==12||i==13||i==14)continue; // three unrestricted u8 debounce values
  for(unsigned value=0;value<256;value++){
   if(value==f[i])continue;
   uint8_t bad[40];memcpy(bad,f,40);bad[i]=(uint8_t)value;seal(bad);iol1_node q=n;
   CK(!iol1_accept(&q,bad,valid,500),"sealed policy/header/config corruption rejected");unchanged(&n,&q);
  }
 }
 // Other valid command kinds are covered separately, not mistaken for invalidCONFIG.
 command(f,IOL1_DIC,0,2,0,1);CK(iol1_accept(&n,f,valid,1000)&&!n.dic_config_valid&&n.dic_config_crc==0,"new epoch clears applied config qualification");
 command(f,IOL1_DIC,0,2,1,8);seal(f);CK(iol1_accept(&n,f,valid,1001),"read does not set configvalid");
 n.factory_record=0;iol1_reply(&n,reply);for(unsigned i=28;i<36;i++)CK(reply[i]==255,"unprovisioned chunk FF no fake identity");
 iol1_timeout(&n,2000);CK(n.state==IOL1_SYNCED,"exact deadline minus1");iol1_timeout(&n,2001);CK(n.state==IOL1_FAULT,"exact1ms timeout");
 dic_filter d;dic_filter_reset(&d);uint8_t g[3]={0,1,255};
 CK(dic_filter_sample(&d,0xffffff,100,g,1)==255,"group0 immediate group1/2 deferred");
 CK(dic_filter_sample(&d,0xffffff,199,g,1)==255,"100us minus1");
 CK(dic_filter_sample(&d,0xffffff,200,g,1)==65535,"100us exact");
 CK(dic_filter_sample(&d,0xffffff,25599,g,1)==65535,"25.5ms minus1");
 CK(dic_filter_sample(&d,0xffffff,25600,g,1)==0xffffff,"25.5ms exact");
 CK(dic_filter_sample(&d,0,25700,g,1)==0xffff00,"zero-groupfall immediate");
 CK(dic_filter_sample(&d,0xffffff,25750,g,1)==0xffffff,"bounce return cancels pendingfall");
 CK(dic_filter_sample(&d,0,25800,g,1)==0xffff00,"fall restart");
 CK(dic_filter_sample(&d,0,25899,g,1)==0xffff00,"fall minus1");
 CK(dic_filter_sample(&d,0,25900,g,1)==0xff0000,"fall exact");
 dic_filter_reset(&d);g[0]=1;g[1]=1;g[2]=1;
 CK(dic_filter_sample(&d,1,0xfffffff0u,g,1)==0,"timerwrap starts");
 CK(dic_filter_sample(&d,1,0x53,g,1)==0,"timerwrap minus1");CK(dic_filter_sample(&d,1,0x54,g,1)==1,"timerwrap exact");
 dic_filter_reset(&d);CK(dic_filter_sample(&d,1,0,g,1)==0,"generation starts");CK(dic_filter_sample(&d,1,99,g,2)==0,"configgeneration restarts stability");CK(dic_filter_sample(&d,1,198,g,2)==0,"new generation minus1");CK(dic_filter_sample(&d,1,199,g,2)==1,"new generation exact");
 printf("PASS record/config checks=%u\n",checks);return 0;
}
