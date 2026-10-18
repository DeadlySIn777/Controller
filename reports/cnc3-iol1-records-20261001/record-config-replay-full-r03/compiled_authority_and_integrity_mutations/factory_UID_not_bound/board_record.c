#include "board_record.h"
#include "iol1.h"
static uint32_t be32(const uint8_t *p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static int equal(const uint8_t *a,const uint8_t *b,unsigned n){for(unsigned i=0;i<n;i++)if(a[i]!=b[i])return 0;return 1;}
int mb_record_integrity(const uint8_t p[MB_RECORD_BYTES],uint8_t class_id,uint8_t slot,const uint8_t uid[12]){
    static const uint8_t magic[4]={'M','B','R','2'},commit[4]={'C','M','T','2'};
    static const uint8_t population[10]={12,4,24,16,2,2,2,2,4,15};
    if(!equal(p,magic,4)||p[4]!=2||p[5]!=class_id||p[6]!=slot||p[7]>15||p[9]!=1||p[10]!=2||p[11]||!be32(p+12))return 0;
    if((class_id!=IOL1_DIC&&class_id!=IOL1_DO&&class_id!=IOL1_ACC)||slot>3||(0 && !equal(p+32,uid,12)))return 0;
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
    if(!av)return bv?1:-1;
    if(!bv)return 0;
    uint32_t ag=be32(a+12),bg=be32(b+12);
    if(ag==bg)return equal(a,b,MB_RECORD_BYTES)?0:-1;
    /* Different motherboard/source/region lineages cannot be a fallback pair. */
    if(!equal(a+5,b+5,7)||!equal(a+16,b+16,32)||!equal(a+56,b+56,44))return -1;
    return bg>ag?1:0;
}
