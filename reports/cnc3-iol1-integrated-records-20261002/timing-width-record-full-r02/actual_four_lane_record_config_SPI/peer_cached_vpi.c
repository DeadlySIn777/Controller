/* Actual unchanged target protocol linked to explicit disconnected observation
 * fixtures. Reply is cached after PREVIOUS CS release, as spi1_arm does. */
#include <vpi_user.h>
#include "target/iol1.h"
#include "target/board_record.h"
#include <stdio.h>
#include <string.h>
static iol1_node node[4];
static unsigned initialized[4];
static uint8_t prepared[4][40];
static unsigned integer(vpiHandle h){s_vpi_value v={.format=vpiIntVal};vpi_get_value(h,&v);return (unsigned)v.value.integer;}
static void bytes(vpiHandle h,uint8_t *out,unsigned n){s_vpi_value v={.format=vpiVectorVal};vpi_get_value(h,&v);for(unsigned i=0;i<n;i++){unsigned b=n-1-i;out[i]=(uint8_t)(v.value.vector[b/4].aval>>((b%4)*8));}}
static void put(vpiHandle h,const uint8_t *in){s_vpi_vecval words[10];memset(words,0,sizeof(words));for(unsigned i=0;i<40;i++){unsigned b=39-i;words[b/4].aval|=(uint32_t)in[i]<<((b%4)*8);}s_vpi_value v={.format=vpiVectorVal};v.value.vector=words;vpi_put_value(h,&v,0,vpiNoDelay);}
static void init(unsigned s){iol1_init(&node[s],s==0?IOL1_DIC:s==3?IOL1_ACC:IOL1_DO,s);initialized[s]=1;iol1_reply(&node[s],prepared[s]);}
static PLI_INT32 fixture(PLI_BYTE8 *user){(void)user;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));unsigned s=integer(vpi_scan(a));if(!initialized[s])init(s);bytes(vpi_scan(a),node[s].realtime,16);node[s].field_good=(uint8_t)integer(vpi_scan(a));node[s].card_fault=(uint8_t)integer(vpi_scan(a));return 0;}
static PLI_INT32 reply(PLI_BYTE8 *user){(void)user;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));unsigned s=integer(vpi_scan(a));vpiHandle dest=vpi_scan(a);unsigned e=integer(vpi_scan(a));uint8_t f[40];if(!initialized[s])init(s);memcpy(f,prepared[s],40);
 switch(e){case 1:f[39]^=1;break;case 2:f[2]^=1;break;case 3:f[3]^=1;break;case 4:f[5]^=1;break;case 5:f[7]^=1;break;case 6:f[8]|=0x40;break;case 7:if(s==0){f[16]=1;f[17]=185;}else if(s<3){f[18]=1;f[19]=185;}else{f[22]=1;f[23]=185;}break;case 8:if(s>0&&s<3)f[10]=1;else f[20]=1;break;case 9:f[0]=0;break;case 10:f[1]=2;break;case 11:f[8]|=0x18;break;case 12:if(s==3)f[25]=0;else f[20]=1;break;case 13:if(s==3){f[25]=0x0f;f[24]=0;f[22]=0;f[23]=0;}else f[8]&=(uint8_t)~0x20;break;case 14:memset(f,0,40);break;case 15:if(s==3)f[24]=15;else f[20]=1;break;case 16:if(s==3){f[22]=0;f[23]=0;}else f[9]=12;break;case 17:f[3]|=0x80;break;case 18:f[8]=(uint8_t)((f[8]&~7u)|3u);break;case 19:f[8]&=(uint8_t)~0x20;break;
 case 20:if(f[9]>=128)f[28]^=1;break;
 case 21:if(f[9]>=128)f[27]^=1;break;
 case 22:if(f[9]>=128)f[9]^=1;break;
 case 23:if(f[9]==1)f[35]^=1;break;default:break;}
 if(e!=1&&e!=14){uint32_t c=iol1_crc32c(f,36);for(unsigned k=0;k<4;k++)f[36+k]=(uint8_t)(c>>(24-k*8));}put(dest,f);return 0;}
static PLI_INT32 accept(PLI_BYTE8 *user){(void)user;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));unsigned s=integer(vpi_scan(a));uint8_t f[40];bytes(vpi_scan(a),f,40);unsigned clocks=integer(vpi_scan(a)),t=integer(vpi_scan(a));vpiHandle result=vpi_scan(a);if(!initialized[s])init(s);iol1_transport tr={(uint16_t)clocks,(uint8_t)(clocks/8),(uint8_t)(clocks/8),0,1};s_vpi_value v={.format=vpiIntVal};v.value.integer=iol1_accept(&node[s],f,tr,t);vpi_put_value(result,&v,0,vpiNoDelay);iol1_reply(&node[s],prepared[s]);return 0;}
static PLI_INT32 reset(PLI_BYTE8 *user){(void)user;memset(initialized,0,sizeof(initialized));return 0;}
/* Reachable long-running boundary state fixture; all following frames still
 * cross actual SPI and unchanged C acceptance/CRC. Not an identity grant. */
static PLI_INT32 seed_sequence(PLI_BYTE8 *user){(void)user;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));unsigned s=integer(vpi_scan(a));if(!initialized[s])init(s);node[s].sequence=(uint16_t)integer(vpi_scan(a));iol1_reply(&node[s],prepared[s]);return 0;}
/* Test-only record delivery: reads a real fixture generated and signed by the
 * frozen host code, validates the actual target integrity/UID routine, then
 * exposes that record's own major. No signature/trust/ACTIVE grant. */
static uint8_t records[4][512];
static PLI_INT32 record_fixture(PLI_BYTE8 *user){(void)user;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));unsigned s=integer(vpi_scan(a));vpiHandle result=vpi_scan(a);s_vpi_value v={.format=vpiIntVal};uint8_t uid[12];for(unsigned k=0;k<12;k++)uid[k]=(uint8_t)(s*16+k);FILE *f=fopen("records.bin","rb");if(s>=4||!f){v.value.integer=0;}else{fseek(f,(long)(s*512),SEEK_SET);size_t got=fread(records[s],1,512,f);fclose(f);uint8_t blank[512];memset(blank,0xff,sizeof(blank));int selected=got==512?mb_record_select(records[s],blank,s==0?IOL1_DIC:s==3?IOL1_ACC:IOL1_DO,s,uid):-1;v.value.integer=selected==0;if(v.value.integer){if(!initialized[s])init(s);node[s].factory_record=records[s];node[s].hw_major=records[s][7];iol1_reply(&node[s],prepared[s]);}}vpi_put_value(result,&v,0,vpiNoDelay);return 0;}
static PLI_INT32 chunk_check(PLI_BYTE8 *user){(void)user;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));unsigned s=integer(vpi_scan(a)),c=integer(vpi_scan(a));uint8_t actual[8];bytes(vpi_scan(a),actual,8);vpiHandle dest=vpi_scan(a);s_vpi_value v={.format=vpiIntVal};v.value.integer=s<4&&c<64&&memcmp(actual,records[s]+c*8,8)==0;vpi_put_value(dest,&v,0,vpiNoDelay);return 0;}
static void regtask(const char *name,PLI_INT32(*fn)(PLI_BYTE8*)){s_vpi_systf_data d;memset(&d,0,sizeof(d));d.type=vpiSysTask;d.tfname=name;d.calltf=fn;vpi_register_systf(&d);}
static void startup(void){regtask("$iol1_record_fixture",record_fixture);regtask("$iol1_actual_chunk_check",chunk_check);regtask("$iol1_c_reply",reply);regtask("$iol1_c_accept",accept);regtask("$iol1_c_reset",reset);regtask("$iol1_observation_fixture",fixture);regtask("$iol1_reachable_sequence_fixture",seed_sequence);}
void (*vlog_startup_routines[])(void)={startup,0};
