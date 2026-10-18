#include "manifest.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include <ctype.h>

#define MAX_BYTES (2u*1024u*1024u)
#define MAX_TOKENS 32768u
struct token {size_t start,end,next;char kind;};
struct parser {const char*s;size_t length,pos,count;struct token*t;};
static void ws(struct parser*p){while(p->pos<p->length&&strchr(" \r\n\t",p->s[p->pos]))++p->pos;}
static int json_number(const char*s,size_t n){
    size_t i=0;if(i<n&&s[i]=='-')++i;if(i>=n)return 0;
    if(s[i]=='0')++i;else{if(s[i]<'1'||s[i]>'9')return 0;while(i<n&&isdigit((unsigned char)s[i]))++i;}
    if(i<n&&s[i]=='.'){++i;size_t first=i;while(i<n&&isdigit((unsigned char)s[i]))++i;if(i==first)return 0;}
    if(i<n&&(s[i]=='e'||s[i]=='E')){++i;if(i<n&&(s[i]=='+'||s[i]=='-'))++i;size_t first=i;while(i<n&&isdigit((unsigned char)s[i]))++i;if(i==first)return 0;}
    return i==n;
}
static int parse(struct parser*p,unsigned depth){
    if(depth>64||p->count>=MAX_TOKENS)return -1;ws(p);
    if(p->pos>=p->length)return -1;
    size_t at=p->count++;struct token*t=&p->t[at];t->start=p->pos;t->kind=p->s[p->pos++];
    if(t->kind=='{'||t->kind=='['){
        const char close=t->kind=='{'?'}':']';ws(p);
        if(p->pos<p->length&&p->s[p->pos]!=close)for(;;){
            if(t->kind=='{'&&(p->pos>=p->length||p->s[p->pos]!='"'))return -1;
            size_t key_index=p->count;
            if(parse(p,depth+1))return -1;ws(p);
            if(t->kind=='{'){
                const struct token*k=&p->t[key_index];
                /* Prepared manifest keys are plain canonical ASCII/path keys.
                 * Escaped aliases are refused rather than normalized partially. */
                if(memchr(p->s+k->start,'\\',k->end-k->start))return -1;
                for(size_t prior=at+1;prior<key_index;){
                    const struct token*q=&p->t[prior];
                    if(q->end-q->start==k->end-k->start&&!memcmp(p->s+q->start,p->s+k->start,k->end-k->start))return -1;
                    prior=p->t[p->t[prior].next].next;
                }
            }
            if(t->kind=='{'){if(p->pos>=p->length||p->s[p->pos++]!=':')return -1;if(parse(p,depth+1))return -1;ws(p);}
            if(p->pos>=p->length)return -1;if(p->s[p->pos]==close)break;
            if(p->s[p->pos++]!=',')return -1;ws(p);
        }
        if(p->pos>=p->length||p->s[p->pos++]!=close)return -1;
    }else if(t->kind=='"'){
        for(;;){
            if(p->pos>=p->length)return -1;unsigned char c=(unsigned char)p->s[p->pos++];
            if(c=='"')break;if(c<32)return -1;
            if(c=='\\'){
                if(p->pos>=p->length)return -1;char e=p->s[p->pos++];
                if(e=='u'){for(unsigned i=0;i<4;++i)if(p->pos>=p->length||!isxdigit((unsigned char)p->s[p->pos++]))return -1;}
                else if(!strchr("\"\\/bfnrt",e))return -1;
            }
        }
    }else{
        t->kind='p';while(p->pos<p->length&&!strchr(" \r\n\t,]}",p->s[p->pos]))++p->pos;
        size_t n=p->pos-t->start;const char*s=p->s+t->start;
        if(!(n==4&&!memcmp(s,"true",4))&&!(n==5&&!memcmp(s,"false",5))&&
           !(n==4&&!memcmp(s,"null",4))&&!json_number(s,n))return -1;
    }
    t->end=p->pos;t->next=p->count;return 0;
}
static int key(const struct parser*p,size_t i,const char*name){
    const struct token*t=&p->t[i];size_t n=strlen(name);
    return t->kind=='"'&&t->end-t->start==n+2&&!memcmp(p->s+t->start+1,name,n);
}
static int literal(const struct parser*p,size_t i,const char*word){
    if(i==SIZE_MAX)return 0;const struct token*t=&p->t[i];size_t n=strlen(word);
    return t->end-t->start==n&&!memcmp(p->s+t->start,word,n);
}
static size_t field(const struct parser*p,size_t object,const char*name){
    if(p->t[object].kind!='{')return SIZE_MAX;
    size_t found=SIZE_MAX;
    for(size_t i=object+1;i<p->t[object].next;){
        size_t v=p->t[i].next;if(v>=p->t[object].next)return SIZE_MAX;
        if(key(p,i,name)){if(found!=SIZE_MAX)return SIZE_MAX;found=v;}
        i=p->t[v].next;
    }
    return found;
}
static int number(const struct parser*p,size_t i,double*out){
    if(i==SIZE_MAX||p->t[i].kind!='p')return -1;
    const struct token*t=&p->t[i];size_t n=t->end-t->start;if(!n||n>=64)return -1;
    char b[64];memcpy(b,p->s+t->start,n);b[n]=0;
    if(!isdigit((unsigned char)b[0])&&b[0]!='-')return -1;
    char*end;errno=0;double v=strtod(b,&end);
    if(errno||*end||!isfinite(v))return -1;*out=v;return 0;
}
static int integer(const struct parser*p,size_t i,uint32_t max,uint32_t*out){
    double v;if(number(p,i,&v)||v<0||v>(double)max||floor(v)!=v)return -1;*out=(uint32_t)v;return 0;
}
static int scalar(const struct parser*p,size_t o,const char*n,uint32_t max,uint32_t*out){return integer(p,field(p,o,n),max,out);}
static int hex_digit(char c){if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;return -1;}
static int digest(const struct parser*p,size_t i,uint8_t*out){
    if(i==SIZE_MAX||p->t[i].kind!='"'||p->t[i].end-p->t[i].start!=66)return -1;
    unsigned nonzero=0;for(unsigned k=0;k<32;++k){
        int a=hex_digit(p->s[p->t[i].start+1+2*k]),b=hex_digit(p->s[p->t[i].start+2+2*k]);
        if(a<0||b<0)return -1;out[k]=(uint8_t)((a<<4)|b);nonzero|=out[k];
    }return nonzero?0:-1;
}
static int doubles(const struct parser*p,size_t i,double*out){
    if(i==SIZE_MAX||p->t[i].kind!='[')return -1;size_t at=i+1;
    for(unsigned k=0;k<12;++k){if(at>=p->t[i].next||number(p,at,&out[k]))return -1;at=p->t[at].next;}
    return at==p->t[i].next?0:-1;
}
static int decode(const struct parser*p,struct cnc3_sim_manifest*m){
    if(p->t[0].kind!='{')return -1;
    size_t host=field(p,0,"cnc3_host"),context=field(p,0,"simulation_context");uint32_t v;
    if(host==SIZE_MAX||context==SIZE_MAX||p->t[host].kind!='{'||p->t[context].kind!='{')return -1;
    if(!literal(p,field(p,0,"kind"),"\"cnc3_sim2_reviewed_runtime\"")||
       !literal(p,field(p,0,"scope"),"\"disconnected_integration_candidate\"")||
       !literal(p,field(p,0,"schema_version"),"1")||
       !literal(p,field(p,0,"simulation_only"),"true")||
       !literal(p,field(p,0,"physical_commissioning_complete"),"false")||
       !literal(p,field(p,0,"motion_authorized"),"false")||
       !literal(p,field(p,0,"outputs_inhibited"),"true")||
       !literal(p,field(p,0,"homed"),"false")||
       !literal(p,field(p,0,"physical_backend_allowed"),"false")||
       !literal(p,field(p,context,"kind"),"\"cnc3_sim2_context\"")||
       !literal(p,field(p,context,"schema_version"),"1")||
       !literal(p,field(p,context,"transport"),"\"disconnected_compiled_rtl_spi\"")||
       !literal(p,field(p,context,"physical_backend_allowed"),"false")||
       scalar(p,context,"gateware_build_id",UINT32_MAX,&v)||v!=CNC3_SIM_GATEWARE_BUILD)return -1;
#define U32(name,target,max) if(scalar(p,host,name,max,&v))return -1;target=v
    U32("active_mask",m->config.axis_mask,0xfff);U32("fitted_mask",v,0xfff);if(v!=0xfff)return -1;
    U32("config_hash",m->config.config_hash,UINT32_MAX);if(!v)return -1;
    U32("provider_session",m->provider_session,UINT32_MAX);if(!v)return -1;
    U32("source_id",m->source_id,UINT32_MAX);if(!v)return -1;
    U32("required_encoder_mask",m->config.required_encoder_mask,15);
    U32("dout_enable_mask",m->config.dout_enable_mask,0xffff);
    U32("alarm_trip_mask",m->config.alarm_trip_mask,0xfff);
    U32("alarm_on_no_current",m->config.alarm_on_no_current,0xfff);
    U32("encoder_filter_ticks",m->config.encoder_filter_ticks,15);
    U32("encoder_expansion_class",m->config.encoder_expansion_class,0);
    U32("mpg_config",m->config.mpg_config,0);
#undef U32
    if(!m->config.axis_mask||m->config.alarm_trip_mask!=m->config.axis_mask||m->config.alarm_on_no_current!=m->config.axis_mask)return -1;
    if(digest(p,field(p,context,"config_digest"),m->config_digest)||digest(p,field(p,context,"source_digest"),m->source_digest))return -1;
    if(doubles(p,field(p,host,"scale"),m->config.scale)||doubles(p,field(p,host,"max_velocity"),m->max_velocity))return -1;
    size_t array=field(p,host,"timing_ticks");if(array==SIZE_MAX||p->t[array].kind!='[')return -1;size_t row=array+1;
    for(unsigned k=0;k<12;++k){
        if(row>=p->t[array].next||p->t[row].kind!='[')return -1;size_t at=row+1;
        for(unsigned j=0;j<4;++j){if(at>=p->t[row].next||integer(p,at,1023,&v)||v<100)return -1;m->config.timing[k][j]=(uint16_t)v;at=p->t[at].next;}
        if(at!=p->t[row].next)return -1;row=p->t[row].next;
        int active=!!(m->config.axis_mask&(1u<<k));
        double rate_word=ceil(m->config.scale[k]*m->max_velocity[k]*4294967296.0/50000000.0);
        uint32_t guarded_period=(uint32_t)m->config.timing[k][0]+m->config.timing[k][1]+1u;
        if(active&&(m->config.scale[k]<1||m->config.scale[k]>1e6||m->max_velocity[k]<=0||
            rate_word>16777216.0||rate_word*(double)guarded_period>4294967296.0))return -1;
        if(!active&&(m->config.scale[k]!=0||m->max_velocity[k]!=0))return -1;
    }
    if(row!=p->t[array].next)return -1;
    memcpy(m->config.maximum_velocity,m->max_velocity,sizeof m->max_velocity);
    uint32_t motor_pulses[12]={0};
    array=field(p,0,"motors");if(array==SIZE_MAX||p->t[array].kind!='[')return -1;
    for(size_t at=array+1;at<p->t[array].next;at=p->t[at].next){
        uint32_t channel,pulses;
        if(scalar(p,at,"channel",11,&channel)||scalar(p,at,"electrical_steps_per_revolution",UINT32_MAX,&pulses)||!pulses||motor_pulses[channel])return -1;
        motor_pulses[channel]=pulses;
    }
    size_t configured=field(p,0,"configured_io");if(configured==SIZE_MAX)return -1;
    array=field(p,configured,"encoders");if(array==SIZE_MAX||p->t[array].kind!='[')return -1;
    for(unsigned i=0;i<4;++i)m->encoder_steps_per_revolution[i]=3200; /* explicitly unselected fixture inputs */
    uint32_t encmask=0;
    for(size_t at=array+1;at<p->t[array].next;at=p->t[at].next){
        uint32_t channel,count;
        if(scalar(p,at,"channel",3,&channel)||scalar(p,at,"counts_per_revolution",UINT32_MAX,&count)||count<4||
           count!=motor_pulses[channel]||(encmask&(1u<<channel)))return -1;
        encmask|=1u<<channel;m->encoder_steps_per_revolution[channel]=count;
    }
    if(encmask!=m->config.required_encoder_mask)return -1;
    return 0;
}
int cnc3_sim_manifest_read(const char*path,struct cnc3_sim_manifest*m){
    if(!path||!m)return -1;FILE*f=fopen(path,"rb");if(!f)return -1;
    int result=-1;char*s=malloc(MAX_BYTES+1u);struct token*t=calloc(MAX_TOKENS,sizeof(*t));
    if(s&&t){size_t n=fread(s,1,MAX_BYTES+1u,f);if(n&&n<=MAX_BYTES&&!ferror(f)){
        struct parser p={s,n,0,0,t};memset(m,0,sizeof(*m));
        if(!parse(&p,0)){ws(&p);if(p.pos==n)result=decode(&p,m);}
    }}fclose(f);free(t);free(s);return result;
}
