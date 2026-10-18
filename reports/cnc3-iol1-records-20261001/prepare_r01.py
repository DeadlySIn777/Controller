from pathlib import Path
import hashlib,json,shutil
P=Path(__file__).resolve().parent;ROOT=P.parents[1];O=P/'stage-r01'
if O.exists():raise RuntimeError('fresh stage required')
O.mkdir()
for src in (ROOT/'firmware/motherboard_iol1_readonly').rglob('*'):
 if src.is_file():
  p=O/'originals'/src.relative_to(ROOT/'firmware/motherboard_iol1_readonly');p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
for name in ['iol1.c','iol1.h','target.c','startup.S','stm32g031.ld']:
 shutil.copyfile(O/'originals'/name,O/name)
shutil.copytree(O/'originals/vendor',O/'vendor')
def write(name,s):(O/name).write_text(s,encoding='utf8',newline='\n')
h=(O/'iol1.h').read_text().replace('uint8_t realtime[16];','uint8_t realtime[16];\n    uint8_t dic_config[24],dic_config_valid;\n    uint32_t dic_config_crc,dic_config_generation;')
write('iol1.h',h)
c=(O/'iol1.c').read_text()
c=c.replace('if((f[8]!=0 && f[8]!=1)||f[9]!=0xff)', 'if((f[8]!=0 && f[8]!=1 && f[8]!=0x10)||f[9]!=0xff)')
c=c.replace('for(unsigned i=10;i<36;i++)if(f[i]){n->policy_errors++;return 0;}', '''int config=f[8]==0x10;
    if(config){
        /* Frozen CONFIG_WRITE: one DIC blob at index0, format1, 3 groups,
         * reserved24B tail and final payload byte zero. No output authority. */
        if(n->class_id!=IOL1_DIC||f[10]!=0||f[11]!=1||f[35]){n->policy_errors++;return 0;}
        for(unsigned i=15;i<35;i++)if(f[i]){n->policy_errors++;return 0;}
    }else for(unsigned i=10;i<36;i++)if(f[i]){n->policy_errors++;return 0;}''')
c=c.replace('n->epoch=epoch;n->sequence=0;n->state=IOL1_SYNCED;', 'n->epoch=epoch;n->sequence=0;n->state=IOL1_SYNCED;\n        n->dic_config_valid=0;n->dic_config_crc=0;\n        n->dic_config_generation++;')
c=c.replace('n->accepted_us=now;n->good++;return 1;', '''if(config){
        for(unsigned i=0;i<24;i++)n->dic_config[i]=f[11+i];
        n->dic_config_crc=iol1_crc32c(n->dic_config,24);
        n->dic_config_generation++;n->dic_config_valid=1;
    }
    n->accepted_us=now;n->good++;return 1;''')
c=c.replace('put32(f+26,n->good);put16(f+30,(uint16_t)n->crc_errors);', '''/* Diagnostic page1 proves only actually applied volatile DIC config CRC.
     * Temperature/VDD bytes are zero/unavailable; never production identity. */
    if(n->class_id==IOL1_DIC&&n->dic_config_valid){
        f[9]=1;for(unsigned i=26;i<36;i++)f[i]=0;
        put32(f+32,n->dic_config_crc);
    }else {put32(f+26,n->good);put16(f+30,(uint16_t)n->crc_errors);''')
c=c.replace('put16(f+32,(uint16_t)n->framing_errors);put16(f+34,(uint16_t)n->policy_errors);','put16(f+32,(uint16_t)n->framing_errors);put16(f+34,(uint16_t)n->policy_errors);}')
write('iol1.c',c)
write('dic_filter.h',r'''#ifndef CNC_DIC_FILTER_H
#define CNC_DIC_FILTER_H
#include <stdint.h>
typedef struct { uint32_t filtered,candidate,since[24],generation;uint8_t initialized; } dic_filter;
void dic_filter_reset(dic_filter *f);
uint32_t dic_filter_sample(dic_filter *f,uint32_t raw,uint32_t now,const uint8_t groups[3],uint32_t generation);
#endif
''')
write('dic_filter.c',r'''#include "dic_filter.h"
/* Actual sampled time, not polling-loop iteration count. No unsampled pulse
 * or physical propagation/timer-jitter claim. Configuration resets debounce. */
void dic_filter_reset(dic_filter *f){
    f->filtered=0;f->candidate=0;f->generation=0;f->initialized=0;
    for(unsigned i=0;i<24;i++)f->since[i]=0;
}
uint32_t dic_filter_sample(dic_filter *f,uint32_t raw,uint32_t now,const uint8_t groups[3],uint32_t generation){
    raw&=0xffffffu;
    if(!f->initialized||f->generation!=generation){
        f->candidate=raw;for(unsigned i=0;i<24;i++)f->since[i]=now;
        f->generation=generation;f->initialized=1;
    }
    for(unsigned i=0;i<24;i++){
        uint32_t bit=1u<<i;
        if((raw^f->candidate)&bit){f->candidate^=bit;f->since[i]=now;}
        if(((raw^f->filtered)&bit)&&((uint32_t)(now-f->since[i])>=(uint32_t)groups[i/8]*100u))f->filtered^=bit;
    }
    return f->filtered;
}
''')
write('board_record.h',r'''#ifndef CNC_BOARD_RECORD_H
#define CNC_BOARD_RECORD_H
#include <stdint.h>
#define MB_RECORD_BYTES 512u
#define MB_PAGE_BYTES 2048u
#define MB_RECORD_SLOT0 0x0800f000u
#define MB_RECORD_SLOT1 0x0800f800u
/* Proposed IS2 motherboard/region descriptor. No removable-card identity.
 * Target checks integrity and UID only; it CANNOT authenticate a signature. */
int mb_record_integrity(const uint8_t p[MB_RECORD_BYTES],uint8_t class_id,uint8_t slot,const uint8_t uid[12]);
int mb_record_select(const uint8_t a[MB_RECORD_BYTES],const uint8_t b[MB_RECORD_BYTES],uint8_t class_id,uint8_t slot,const uint8_t uid[12]);
#endif
''')
write('board_record.c',r'''#include "board_record.h"
#include "iol1.h"
static uint32_t be32(const uint8_t *p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static int equal(const uint8_t *a,const uint8_t *b,unsigned n){for(unsigned i=0;i<n;i++)if(a[i]!=b[i])return 0;return 1;}
int mb_record_integrity(const uint8_t p[MB_RECORD_BYTES],uint8_t class_id,uint8_t slot,const uint8_t uid[12]){
    static const uint8_t magic[4]={'M','B','R','2'},commit[4]={'C','M','T','2'};
    static const uint8_t population[10]={12,4,24,16,2,2,2,2,4,15};
    if(!equal(p,magic,4)||p[4]!=2||p[5]!=class_id||p[6]!=slot||p[7]>15||p[9]!=1||p[10]!=2||p[11]||!be32(p+12))return 0;
    if((class_id!=IOL1_DIC&&class_id!=IOL1_DO&&class_id!=IOL1_ACC)||slot>3||!equal(p+32,uid,12))return 0;
    if((class_id==IOL1_DIC&&slot!=0)||(class_id==IOL1_DO&&(slot!=1&&slot!=2))||(class_id==IOL1_ACC&&slot!=3))return 0;
    unsigned chars=0,padded=0;for(unsigned i=16;i<32;i++){
        if(!p[i])padded=1;
        else {if(padded||p[i]<33||p[i]>126)return 0;chars++;}
    }
    if(!chars||(!p[44]&&!p[45])||p[46]>3||p[47]<3||!equal(p+56,population,10)||p[66]||p[67])return 0;
    for(unsigned i=212;i<440;i++)if(p[i]!=0xff)return 0;
    if(!equal(p+508,commit,4)||be32(p+504)!=iol1_crc32c(p,504))return 0;
    return 1;
}
int mb_record_select(const uint8_t a[MB_RECORD_BYTES],const uint8_t b[MB_RECORD_BYTES],uint8_t class_id,uint8_t slot,const uint8_t uid[12]){
    int av=mb_record_integrity(a,class_id,slot,uid),bv=mb_record_integrity(b,class_id,slot,uid);
    if(!av)return bv?1:-1;if(!bv)return 0;
    uint32_t ag=be32(a+12),bg=be32(b+12);
    if(ag==bg)return equal(a,b,MB_RECORD_BYTES)?0:-1;
    /* Different motherboard/source/region lineages cannot be a fallback pair. */
    if(!equal(a+5,b+5,7)||!equal(a+16,b+16,32)||!equal(a+56,b+56,44))return -1;
    return bg>ag?1:0;
}
''')
t=(O/'target.c').read_text().replace('#include "iol1.h"','#include "iol1.h"\n#include "board_record.h"\n#include "dic_filter.h"')
t=t.replace('static uint8_t debounce[24];','static dic_filter di_filter;')
t=t.replace('static uint8_t slot_valid;', '''static uint8_t slot_valid;
static volatile int8_t record_slot=-1;
static void inspect_factory_flash(void){
    uint8_t uid[12];for(unsigned i=0;i<12;i++)uid[i]=*(volatile const uint8_t *)(UID_BASE+i);
    record_slot=(int8_t)mb_record_select((const uint8_t *)MB_RECORD_SLOT0,(const uint8_t *)MB_RECORD_SLOT1,
        NODE_SLOT==0?IOL1_DIC:NODE_SLOT==3?IOL1_ACC:IOL1_DO,NODE_SLOT,uid);
    /* This result is diagnostic integrity, NEVER authenticated factory trust,
     * ACTIVE, CARD_EN, output permission or a fabricated removable-card ID. */
}''')
start=t.index('    if((uint32_t)(t-last_di_us)>=10){');end=t.index('\n}\n#endif\nstatic void observe',start)
t=t[:start]+'''    if((uint32_t)(t-last_di_us)>=10){
        uint8_t groups[3];uint32_t generation;
        __disable_irq();generation=node.dic_config_generation;
        for(unsigned g=0;g<3;g++)groups[g]=node.dic_config_valid?node.dic_config[1+g]:0;
        __enable_irq();
        uint32_t next_raw=0;for(unsigned i=0;i<24;i++)next_raw|=input(gp[port[i]],bit[i])<<i;
        uint32_t next_filtered=dic_filter_sample(&di_filter,next_raw,t,groups,generation);
        __disable_irq();
        if(generation==node.dic_config_generation){raw_di=next_raw;filtered_di=next_filtered;last_di_us=t;}
        __enable_irq();
    }'''+t[end:]
t=t.replace('slot_valid=fitted_slot()==NODE_SLOT;', 'inspect_factory_flash();\n    slot_valid=fitted_slot()==NODE_SLOT;')
write('target.c',t)
ld=(O/'stm32g031.ld').read_text().replace('LENGTH = 64K','LENGTH = 60K')
ld+='\n/* Two independent factory-only2KiB pages; no application/MAINT erase driver. */\n_factory_slot0=0x0800f000;\n_factory_slot1=0x0800f800;\nASSERT(LOADADDR(.data)+SIZEOF(.data)<=0x0800f000,"application overlaps factory flash")\n'
write('stm32g031.ld',ld)
manifest={str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.rglob('*') if p.is_file()}
(O/'prepare-receipt.json').write_text(json.dumps({'status':'STAGED','originals_unchanged':True,'exact_inputs':manifest,'proposal_not_shared_adoption':True,'production_factory_authentication':False,'ACTIVE_outputs':False},indent=2)+'\n')
print(O)
