#include "iol1.h"
/* Original commercial application source. This file makes no open-source
 * release or freeware promise; see the project's commercial licensing policy. */
static const uint32_t crc_table[256] = {
    0x00000000u,0xf26b8303u,0xe13b70f7u,0x1350f3f4u,0xc79a971fu,0x35f1141cu,0x26a1e7e8u,0xd4ca64ebu,
    0x8ad958cfu,0x78b2dbccu,0x6be22838u,0x9989ab3bu,0x4d43cfd0u,0xbf284cd3u,0xac78bf27u,0x5e133c24u,
    0x105ec76fu,0xe235446cu,0xf165b798u,0x030e349bu,0xd7c45070u,0x25afd373u,0x36ff2087u,0xc494a384u,
    0x9a879fa0u,0x68ec1ca3u,0x7bbcef57u,0x89d76c54u,0x5d1d08bfu,0xaf768bbcu,0xbc267848u,0x4e4dfb4bu,
    0x20bd8edeu,0xd2d60dddu,0xc186fe29u,0x33ed7d2au,0xe72719c1u,0x154c9ac2u,0x061c6936u,0xf477ea35u,
    0xaa64d611u,0x580f5512u,0x4b5fa6e6u,0xb93425e5u,0x6dfe410eu,0x9f95c20du,0x8cc531f9u,0x7eaeb2fau,
    0x30e349b1u,0xc288cab2u,0xd1d83946u,0x23b3ba45u,0xf779deaeu,0x05125dadu,0x1642ae59u,0xe4292d5au,
    0xba3a117eu,0x4851927du,0x5b016189u,0xa96ae28au,0x7da08661u,0x8fcb0562u,0x9c9bf696u,0x6ef07595u,
    0x417b1dbcu,0xb3109ebfu,0xa0406d4bu,0x522bee48u,0x86e18aa3u,0x748a09a0u,0x67dafa54u,0x95b17957u,
    0xcba24573u,0x39c9c670u,0x2a993584u,0xd8f2b687u,0x0c38d26cu,0xfe53516fu,0xed03a29bu,0x1f682198u,
    0x5125dad3u,0xa34e59d0u,0xb01eaa24u,0x42752927u,0x96bf4dccu,0x64d4cecfu,0x77843d3bu,0x85efbe38u,
    0xdbfc821cu,0x2997011fu,0x3ac7f2ebu,0xc8ac71e8u,0x1c661503u,0xee0d9600u,0xfd5d65f4u,0x0f36e6f7u,
    0x61c69362u,0x93ad1061u,0x80fde395u,0x72966096u,0xa65c047du,0x5437877eu,0x4767748au,0xb50cf789u,
    0xeb1fcbadu,0x197448aeu,0x0a24bb5au,0xf84f3859u,0x2c855cb2u,0xdeeedfb1u,0xcdbe2c45u,0x3fd5af46u,
    0x7198540du,0x83f3d70eu,0x90a324fau,0x62c8a7f9u,0xb602c312u,0x44694011u,0x5739b3e5u,0xa55230e6u,
    0xfb410cc2u,0x092a8fc1u,0x1a7a7c35u,0xe811ff36u,0x3cdb9bddu,0xceb018deu,0xdde0eb2au,0x2f8b6829u,
    0x82f63b78u,0x709db87bu,0x63cd4b8fu,0x91a6c88cu,0x456cac67u,0xb7072f64u,0xa457dc90u,0x563c5f93u,
    0x082f63b7u,0xfa44e0b4u,0xe9141340u,0x1b7f9043u,0xcfb5f4a8u,0x3dde77abu,0x2e8e845fu,0xdce5075cu,
    0x92a8fc17u,0x60c37f14u,0x73938ce0u,0x81f80fe3u,0x55326b08u,0xa759e80bu,0xb4091bffu,0x466298fcu,
    0x1871a4d8u,0xea1a27dbu,0xf94ad42fu,0x0b21572cu,0xdfeb33c7u,0x2d80b0c4u,0x3ed04330u,0xccbbc033u,
    0xa24bb5a6u,0x502036a5u,0x4370c551u,0xb11b4652u,0x65d122b9u,0x97baa1bau,0x84ea524eu,0x7681d14du,
    0x2892ed69u,0xdaf96e6au,0xc9a99d9eu,0x3bc21e9du,0xef087a76u,0x1d63f975u,0x0e330a81u,0xfc588982u,
    0xb21572c9u,0x407ef1cau,0x532e023eu,0xa145813du,0x758fe5d6u,0x87e466d5u,0x94b49521u,0x66df1622u,
    0x38cc2a06u,0xcaa7a905u,0xd9f75af1u,0x2b9cd9f2u,0xff56bd19u,0x0d3d3e1au,0x1e6dcdeeu,0xec064eedu,
    0xc38d26c4u,0x31e6a5c7u,0x22b65633u,0xd0ddd530u,0x0417b1dbu,0xf67c32d8u,0xe52cc12cu,0x1747422fu,
    0x49547e0bu,0xbb3ffd08u,0xa86f0efcu,0x5a048dffu,0x8ecee914u,0x7ca56a17u,0x6ff599e3u,0x9d9e1ae0u,
    0xd3d3e1abu,0x21b862a8u,0x32e8915cu,0xc083125fu,0x144976b4u,0xe622f5b7u,0xf5720643u,0x07198540u,
    0x590ab964u,0xab613a67u,0xb831c993u,0x4a5a4a90u,0x9e902e7bu,0x6cfbad78u,0x7fab5e8cu,0x8dc0dd8fu,
    0xe330a81au,0x115b2b19u,0x020bd8edu,0xf0605beeu,0x24aa3f05u,0xd6c1bc06u,0xc5914ff2u,0x37faccf1u,
    0x69e9f0d5u,0x9b8273d6u,0x88d28022u,0x7ab90321u,0xae7367cau,0x5c18e4c9u,0x4f48173du,0xbd23943eu,
    0xf36e6f75u,0x0105ec76u,0x12551f82u,0xe03e9c81u,0x34f4f86au,0xc69f7b69u,0xd5cf889du,0x27a40b9eu,
    0x79b737bau,0x8bdcb4b9u,0x988c474du,0x6ae7c44eu,0xbe2da0a5u,0x4c4623a6u,0x5f16d052u,0xad7d5351u,
};
static uint16_t be16(const uint8_t *p){ return (uint16_t)((uint16_t)p[0]<<8)|p[1]; }
static void put16(uint8_t *p,uint16_t x){p[0]=(uint8_t)(x>>8);p[1]=(uint8_t)x;}
static void put32(uint8_t *p,uint32_t x){p[0]=(uint8_t)(x>>24);p[1]=(uint8_t)(x>>16);p[2]=(uint8_t)(x>>8);p[3]=(uint8_t)x;}
static uint16_t next_seq(uint16_t x){return x==0xffffu?1u:(uint16_t)(x+1u);}
uint32_t iol1_crc32c(const uint8_t *p,size_t n){uint32_t c=0xffffffffu;while(n--){c=crc_table[(c^*p++)&255u]^(c>>8);}return c^0xffffffffu;}
void iol1_init(iol1_node *n,uint8_t c,uint8_t s){
    uint8_t *p=(uint8_t *)n;for(size_t i=0;i<sizeof(*n);i++)p[i]=0;
    n->class_id=c;n->slot=s;n->state=IOL1_INIT;
    /* Missing observations are unavailable, never zero-age valid. */
    unsigned age=c==IOL1_DIC?6u:c==IOL1_DO?8u:12u;
    n->realtime[age]=0xff;n->realtime[age+1u]=0xff;
}
int iol1_accept(iol1_node *n,const uint8_t f[IOL1_BYTES],iol1_transport t,uint32_t now){
    if(!t.cs_high||t.overrun||t.clocks!=IOL1_CLOCKS||t.rx_bytes!=IOL1_BYTES||t.tx_bytes!=IOL1_BYTES){n->framing_errors++;return 0;}
    uint32_t crc=((uint32_t)f[36]<<24)|((uint32_t)f[37]<<16)|((uint32_t)f[38]<<8)|f[39];
    if(iol1_crc32c(f,36)!=crc){n->accepted_us=now;n->crc_errors++;return 0;}
    if(f[0]!=0xa7||f[1]!=1||f[2]!=n->class_id||f[3]!=n->slot){n->policy_errors++;return 0;}
    /* This staged diagnostic image accepts polls, new-epoch SYNC, the bounded
     * DIC configuration below and proposed read-only IDENT chunks. None grants
     * commercial factory trust, ACTIVE, arming or output authority. */
    if((f[8]!=0 && f[8]!=1 && f[8]!=0x10 && f[8]!=0x08)||f[9]!=0xff){n->policy_errors++;return 0;}
    int config=f[8]==0x10,ident=f[8]==0x08;
    if(config){
        /* Frozen CONFIG_WRITE: one DIC blob at index0, format1, 3 groups,
         * reserved24B tail and final payload byte zero. No output authority. */
        if(n->class_id!=IOL1_DIC||f[10]!=0||f[11]!=1||f[35]){n->policy_errors++;return 0;}
        for(unsigned i=15;i<35;i++)if(f[i]){n->policy_errors++;return 0;}
    }else if(ident){
        /* Proposed IS2 IDENT_READ supplement: payload0 chunk0..63,
         * payload1..25 zero. Telemetry8B chunks preserve realtime16B. */
        if(f[10]>=64){n->policy_errors++;return 0;}
        for(unsigned i=11;i<36;i++)if(f[i]){n->policy_errors++;return 0;}
    }else for(unsigned i=10;i<36;i++)if(f[i]){n->policy_errors++;return 0;}
    uint16_t epoch=be16(f+4),seq=be16(f+6);
    if(!epoch){n->policy_errors++;return 0;}
    if(f[8]==1){
        if(seq || epoch==n->epoch){n->policy_errors++;return 0;}
        n->epoch=epoch;n->sequence=0;n->state=IOL1_SYNCED;
        n->dic_config_valid=0;n->dic_config_crc=0;
        n->dic_config_generation++;
    }else{
        if(n->state!=IOL1_SYNCED||epoch!=n->epoch||seq!=next_seq(n->sequence)){n->policy_errors++;return 0;}
        n->sequence=seq;
    }
    if(config){
        for(unsigned i=0;i<24;i++)n->dic_config[i]=f[11+i];
        n->dic_config_crc=iol1_crc32c(n->dic_config,24);
        n->dic_config_generation++;n->dic_config_valid=1;
    }
    n->ident_pending=(uint8_t)ident;
    n->ident_chunk=ident?f[10]:0;
    n->accepted_us=now;n->good++;return 1;
}
void iol1_timeout(iol1_node *n,uint32_t now){
    if(n->state==IOL1_SYNCED&&(uint32_t)(now-n->accepted_us)>=1000u){n->state=IOL1_FAULT;n->card_fault=1;}
}
void iol1_reply(const iol1_node *n,uint8_t f[IOL1_BYTES]){
    for(unsigned i=0;i<40;i++)f[i]=0;
    f[0]=0x7a;f[1]=1;f[2]=n->class_id;f[3]=(uint8_t)(n->slot|(n->hw_major<<4));
    put16(f+4,n->epoch);put16(f+6,n->sequence);
    /* OUT_PERMIT_SEEN and OUT_ENABLED deliberately remain LOW. */
    f[8]=n->state|(n->field_good?0x20u:0)|(n->card_fault?0x40u:0);
    f[9]=n->class_id==IOL1_DIC?2u:n->class_id==IOL1_DO?9u:6u;
    for(unsigned i=0;i<16;i++)f[10+i]=n->realtime[i];
    /* Diagnostic page1 proves only actually applied volatile DIC config CRC.
     * Temperature/VDD bytes are zero/unavailable; never production identity. */
    if(n->class_id==IOL1_DIC&&n->dic_config_valid){
        f[9]=1;for(unsigned i=26;i<36;i++)f[i]=0;
        put32(f+32,n->dic_config_crc);
    }else {put32(f+26,n->good);put16(f+30,(uint16_t)n->crc_errors);
    put16(f+32,(uint16_t)n->framing_errors);put16(f+34,(uint16_t)n->policy_errors);}
    if(n->ident_pending){
        f[9]=(uint8_t)(0x80u|n->ident_chunk);put16(f+26,n->ident_chunk);
        for(unsigned i=0;i<8;i++)f[28+i]=n->factory_record?n->factory_record[(unsigned)n->ident_chunk*8u+i]:0xff;
    }
    put32(f+36,iol1_crc32c(f,36));
}
