/* The SAME target protocol C functions are linked into a disconnected HDL
 * peer. MMIO/ARM execution and real sensor values are not simulated here. */
#include <vpi_user.h>
#include "iol1.h"
#include <string.h>
static iol1_node nodes[4];
static unsigned initialized[4];
static unsigned integer(vpiHandle h){s_vpi_value v={.format=vpiIntVal};vpi_get_value(h,&v);return (unsigned)v.value.integer;}
static void bytes(vpiHandle h,uint8_t *out){s_vpi_value v={.format=vpiVectorVal};vpi_get_value(h,&v);for(unsigned i=0;i<40;i++){unsigned b=39-i;out[i]=(uint8_t)(v.value.vector[b/4].aval>>((b%4)*8));}}
static void put(vpiHandle h,const uint8_t *in){s_vpi_vecval words[10];memset(words,0,sizeof(words));for(unsigned i=0;i<40;i++){unsigned b=39-i;words[b/4].aval|=(uint32_t)in[i]<<((b%4)*8);}s_vpi_value v={.format=vpiVectorVal};v.value.vector=words;vpi_put_value(h,&v,0,vpiNoDelay);}
static void init(unsigned s){iol1_init(&nodes[s],s==0?IOL1_DIC:s==3?IOL1_ACC:IOL1_DO,s);nodes[s].field_good=1;for(unsigned i=0;i<16;i++)nodes[s].realtime[i]=0;if(s==3){nodes[s].realtime[12]=0xff;nodes[s].realtime[13]=0xff;nodes[s].realtime[15]=3;}initialized[s]=1;}
static PLI_INT32 reply(PLI_BYTE8 *user){(void)user;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));unsigned s=integer(vpi_scan(a));vpiHandle dest=vpi_scan(a);unsigned e=integer(vpi_scan(a));uint8_t f[40];if(!initialized[s])init(s);iol1_reply(&nodes[s],f);
 switch(e){case 1:f[39]^=1;break;case 2:f[2]^=1;break;case 3:f[3]^=1;break;case 4:f[5]^=1;break;case 5:f[7]=0;break;case 6:f[8]|=0x40;break;case 7:if(s==0){f[16]=1;f[17]=185;}else if(s<3){f[18]=1;f[19]=185;}else{f[22]=1;f[23]=185;}break;case 8:f[10]=1;break;case 9:f[0]=0;break;case 10:f[1]=2;break;case 11:f[8]|=0x18;break;case 12:if(s==3)f[25]=0;else f[20]=1;break;case 13:if(s==3){f[25]=0x0f;f[24]=0;f[22]=0;f[23]=0;}else f[8]&=(uint8_t)~0x20;break;case 14:memset(f,0,40);break;case 15:if(s==3)f[24]=15;break;case 16:if(s==3){f[22]=0;f[23]=0;}break;default:break;}
 if(e!=1&&e!=14){uint32_t c=iol1_crc32c(f,36);for(unsigned k=0;k<4;k++)f[36+k]=(uint8_t)(c>>(24-k*8));}put(dest,f);return 0;}
static PLI_INT32 accept(PLI_BYTE8 *user){(void)user;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));unsigned s=integer(vpi_scan(a));uint8_t f[40];bytes(vpi_scan(a),f);unsigned clocks=integer(vpi_scan(a)),t=integer(vpi_scan(a));vpiHandle result=vpi_scan(a);if(!initialized[s])init(s);iol1_transport tr={(uint16_t)clocks,(uint8_t)(clocks/8),(uint8_t)(clocks/8),0,1};s_vpi_value v={.format=vpiIntVal};v.value.integer=iol1_accept(&nodes[s],f,tr,t);vpi_put_value(result,&v,0,vpiNoDelay);return 0;}
static PLI_INT32 reset(PLI_BYTE8 *user){(void)user;memset(initialized,0,sizeof(initialized));return 0;}
static void regtask(const char *name,PLI_INT32(*fn)(PLI_BYTE8*)){s_vpi_systf_data d;memset(&d,0,sizeof(d));d.type=vpiSysTask;d.tfname=name;d.calltf=fn;vpi_register_systf(&d);}
static void startup(void){regtask("$iol1_c_reply",reply);regtask("$iol1_c_accept",accept);regtask("$iol1_c_reset",reset);}
void (*vlog_startup_routines[])(void)={startup,0};
