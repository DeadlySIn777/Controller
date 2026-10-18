#include <vpi_user.h>
#include "iol1.h"
#include "dic_filter.h"
#include <string.h>
#include <stdio.h>
static iol1_node node;
static uint8_t record[512],prepared[40];
static uint32_t raw;
static uint32_t sampled_us;
static uint8_t sample_enabled,sample_valid;
static dic_filter filter;
static unsigned iv(vpiHandle h){s_vpi_value v={.format=vpiIntVal};vpi_get_value(h,&v);return (unsigned)v.value.integer;}
static void bytes(vpiHandle h,uint8_t *out,unsigned n){s_vpi_value v={.format=vpiVectorVal};vpi_get_value(h,&v);for(unsigned i=0;i<n;i++){unsigned b=n-1-i;out[i]=(uint8_t)(v.value.vector[b/4].aval>>((b%4)*8));}}
static void put(vpiHandle h,const uint8_t *in){s_vpi_vecval words[10];memset(words,0,sizeof(words));for(unsigned i=0;i<40;i++){unsigned b=39-i;words[b/4].aval|=(uint32_t)in[i]<<((b%4)*8);}s_vpi_value v={.format=vpiVectorVal};v.value.vector=words;vpi_put_value(h,&v,0,vpiNoDelay);}
static void result(vpiHandle h,int x){s_vpi_value v={.format=vpiIntVal};v.value.integer=x;vpi_put_value(h,&v,0,vpiNoDelay);}
static PLI_INT32 reset(PLI_BYTE8 *u){(void)u;iol1_init(&node,0x11,0);dic_filter_reset(&filter);raw=0;sampled_us=0;sample_enabled=1;sample_valid=0;FILE *f=fopen("fixtures.bin","rb");if(!f||fread(record,1,512,f)!=512){vpi_printf("FAIL record fixture\n");vpi_control(vpiFinish,1);return 0;}fclose(f);node.factory_record=record;node.hw_major=1;iol1_reply(&node,prepared);return 0;}
static PLI_INT32 reply(PLI_BYTE8 *u){(void)u;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));put(vpi_scan(a),prepared);return 0;}
static PLI_INT32 accept(PLI_BYTE8 *u){(void)u;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));uint8_t f[40];bytes(vpi_scan(a),f,40);unsigned clocks=iv(vpi_scan(a)),time=iv(vpi_scan(a));vpiHandle dest=vpi_scan(a);iol1_transport t={(uint16_t)clocks,(uint8_t)(clocks/8),(uint8_t)(clocks/8),0,1};result(dest,iol1_accept(&node,f,t,time));
uint8_t groups[3];for(unsigned g=0;g<3;g++)groups[g]=node.dic_config_valid?node.dic_config[g+1]:1;
if(sample_enabled){uint32_t filtered=dic_filter_sample(&filter,raw,time,groups,node.dic_config_generation);for(unsigned i=0;i<3;i++){node.realtime[i]=(uint8_t)(filtered>>(8*i));node.realtime[i+3]=(uint8_t)(raw>>(8*i));}sampled_us=time;sample_valid=1;}
uint16_t age=iol1_sample_age_us(time,sampled_us,sample_valid);if(age==65535u)sample_valid=0;node.realtime[6]=(uint8_t)(age>>8);node.realtime[7]=(uint8_t)age;node.field_good=1;iol1_reply(&node,prepared);return 0;}
static PLI_INT32 raw_input(PLI_BYTE8 *u){(void)u;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));raw=iv(vpi_scan(a))&0xffffffu;return 0;}
static PLI_INT32 sampling(PLI_BYTE8 *u){(void)u;vpiHandle a=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));sample_enabled=iv(vpi_scan(a))!=0;return 0;}
static void regtask(const char *name,PLI_INT32(*fn)(PLI_BYTE8*)){s_vpi_systf_data d;memset(&d,0,sizeof(d));d.type=vpiSysTask;d.tfname=name;d.calltf=fn;vpi_register_systf(&d);}
static void startup(void){regtask("$record_reset",reset);regtask("$record_reply",reply);regtask("$record_accept",accept);regtask("$record_raw",raw_input);regtask("$record_sampling",sampling);}
void (*vlog_startup_routines[])(void)={startup,0};
