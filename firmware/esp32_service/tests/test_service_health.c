#include "service_health.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void put32(uint8_t *p, uint32_t v) {
    for (unsigned i=0; i<4; ++i) p[i]=(uint8_t)(v>>(8*i));
}
static void put64(uint8_t *p, uint64_t v) {
    put32(p,(uint32_t)v); put32(p+4,(uint32_t)(v>>32));
}
static void frame(uint8_t *p, uint64_t boot, uint32_t seq, uint32_t progress, uint64_t uptime, uint32_t flags) {
    memset(p,0,SH_FRAME_BYTES); memcpy(p,"ESV1",4);
    p[4]=1; p[5]=1; p[6]=28;
    put64(p+8,boot); put32(p+16,seq); put32(p+20,progress);
    put64(p+24,uptime); put32(p+32,flags); put32(p+36,sh_crc32(p,36));
}
static void feed(sh_state *s,const uint8_t *p,size_t n,uint64_t t) {
    for(size_t i=0;i<n;++i) sh_feed(s,p[i],t);
}
/* The README and service_health.h document these exact deadlines and the
   host cadence they imply; keep the test tied to the named constants. */
_Static_assert(SH_LINK_TIMEOUT_MS==1000u,"documented link deadline is 1000 ms");
_Static_assert(SH_PROGRESS_TIMEOUT_MS==500u,"documented progress deadline is 500 ms");
static sh_snapshot at(const sh_state *s,uint64_t t) {
    return sh_observe(s,t,SH_LINK_TIMEOUT_MS,SH_PROGRESS_TIMEOUT_MS);
}
static void check_documented_cadence(void) {
    sh_state s; uint8_t f[SH_FRAME_BYTES];
    /* Exact 1 Hz sender: strict comparison makes the link stale at 1000 ms. */
    sh_init(&s);
    frame(f,7,1,0,0,0); assert(sh_accept(&s,f,sizeof(f),0));
    assert(at(&s,SH_LINK_TIMEOUT_MS-1).link_fresh);
    assert(!at(&s,SH_LINK_TIMEOUT_MS).link_fresh);
    /* Recommended 4 Hz sender with a counter advance in every frame stays
       link- and progress-fresh at every millisecond after the baseline. */
    sh_init(&s);
    uint32_t seq=1;
    for(uint64_t t=0;t<=5000;t+=250,++seq) {
        frame(f,8,seq,seq,t,0); assert(sh_accept(&s,f,sizeof(f),t));
        for(uint64_t u=t;u<t+250;++u) {
            const sh_snapshot o=at(&s,u);
            assert(o.link_fresh&&!o.motion_authority);
            assert(o.backend_progress_fresh==(t>0));
        }
    }
    /* 4 Hz heartbeats whose counter advances only every other frame: the
       link stays fresh but progress expires exactly 500 ms after an advance. */
    sh_init(&s);
    frame(f,9,1,0,0,0); assert(sh_accept(&s,f,sizeof(f),0));
    frame(f,9,2,1,250,0); assert(sh_accept(&s,f,sizeof(f),250));
    frame(f,9,3,1,500,0); assert(sh_accept(&s,f,sizeof(f),500));
    assert(at(&s,250+SH_PROGRESS_TIMEOUT_MS-1).backend_progress_fresh);
    frame(f,9,4,1,750,0); assert(sh_accept(&s,f,sizeof(f),750));
    assert(at(&s,250+SH_PROGRESS_TIMEOUT_MS).link_fresh);
    assert(!at(&s,250+SH_PROGRESS_TIMEOUT_MS).backend_progress_fresh);
    /* Progress freshness never outlives the link, and a stale link is not
       renewed by replaying the last accepted frame. */
    frame(f,9,5,2,1000,0); assert(sh_accept(&s,f,sizeof(f),1000));
    assert(!sh_accept(&s,f,sizeof(f),1000+SH_LINK_TIMEOUT_MS));
    assert(!at(&s,1000+SH_LINK_TIMEOUT_MS).link_fresh);
    assert(!at(&s,1000+SH_LINK_TIMEOUT_MS).backend_progress_fresh);
}
int main(void) {
    sh_state s; uint8_t f[SH_FRAME_BYTES]; sh_snapshot o;
    sh_init(&s);
    assert(!sh_accept(&s,NULL,SH_FRAME_BYTES,0));
    assert(sh_crc32((const uint8_t*)"123456789",9)==UINT32_C(0xcbf43926));
    o=sh_observe(&s,0,1000,500); assert(!o.link_fresh&&!o.motion_authority);
    frame(f,1,1,0,0,SH_HOST_DISARMED);
    assert(sh_accept(&s,f,sizeof(f),100));
    o=sh_observe(&s,100,1000,500); assert(o.link_fresh&&!o.backend_progress_fresh&&o.host_reported_disarmed);
    assert(!sh_accept(&s,f,sizeof(f),101)); /* replay cannot renew freshness */
    assert(s.last_frame_ms==100);
    frame(f,1,2,1,200,0); assert(sh_accept(&s,f,sizeof(f),200));
    o=sh_observe(&s,699,1000,500); assert(o.backend_progress_fresh);
    o=sh_observe(&s,700,1000,500); assert(!o.backend_progress_fresh);
    frame(f,1,3,1,900,0); assert(sh_accept(&s,f,sizeof(f),900));
    o=sh_observe(&s,901,1000,500); assert(o.link_fresh&&!o.backend_progress_fresh);
    frame(f,1,4,2,100,0); assert(!sh_accept(&s,f,sizeof(f),910)); /* decreasing host clock */
    frame(f,1,4,0,1000,0); assert(!sh_accept(&s,f,sizeof(f),910)); /* backwards progress */
    frame(f,1,4,2,1000,0); assert(!sh_accept(&s,f,sizeof(f),899)); /* local clock regression */
    frame(f,1,4,2,1000,4); assert(!sh_accept(&s,f,sizeof(f),1000)); /* unknown flags */
    frame(f,1,4,2,1000,0); f[10]^=1; assert(!sh_accept(&s,f,sizeof(f),1000));
    frame(f,1,4,2,1000,0); assert(!sh_accept(&s,f,39,1000));
    assert(!sh_accept(&s,f,0,1000));
    frame(f,0,4,2,1000,0); assert(!sh_accept(&s,f,sizeof(f),1000));
    frame(f,2,0,0,0,SH_HOST_FAULT); assert(sh_accept(&s,f,sizeof(f),1100));
    o=sh_observe(&s,1100,1000,500); assert(o.host_reported_fault&&!o.backend_progress_fresh&&!o.motion_authority);
    o=sh_observe(&s,2100,1000,500); assert(!o.link_fresh&&!o.host_reported_fault);
    o=sh_observe(&s,1100,0,0); assert(!o.link_fresh);
    sh_init(&s);
    frame(f,3,1,UINT32_MAX,1,0); assert(sh_accept(&s,f,sizeof(f),1));
    assert(!sh_observe(&s,1,1000,500).backend_progress_fresh);
    frame(f,3,2,0,2,0); assert(sh_accept(&s,f,sizeof(f),2)); /* progress counter wrap */
    assert(sh_observe(&s,2,1000,500).backend_progress_fresh);
    frame(f,33,0,100,0,0); assert(sh_accept(&s,f,sizeof(f),3));
    assert(!sh_observe(&s,3,1000,500).backend_progress_fresh); /* new boot needs a second sample */
    sh_init(&s);
    frame(f,4,UINT32_MAX,1,1,0); assert(sh_accept(&s,f,sizeof(f),1));
    frame(f,4,0,2,2,0); assert(!sh_accept(&s,f,sizeof(f),2)); /* sequence cannot wrap */
    sh_init(&s);
    feed(&s,(const uint8_t*)"garbageESV",10,0);
    frame(f,5,1,1,10,0); feed(&s,f,sizeof(f),10); assert(s.accepted==1);
    frame(f,5,2,2,20,0); feed(&s,f,13,20); assert(s.accepted==1);
    frame(f,5,3,3,30,0); feed(&s,f,sizeof(f),30); assert(s.accepted==2&&s.sequence==3);
    /* Corruption at every byte must not mutate accepted health state:
       every health field is compared, not just the sequence number. */
    {
        const sh_state before=s;
        for(size_t i=0;i<SH_FRAME_BYTES;++i) {
            frame(f,5,4,4,40,0); f[i]^=0x80;
            assert(!sh_accept(&s,f,sizeof(f),40));
            assert(s.seen==before.seen&&s.progress_seen==before.progress_seen);
            assert(s.host_boot==before.host_boot&&s.host_uptime==before.host_uptime);
            assert(s.last_frame_ms==before.last_frame_ms);
            assert(s.last_progress_ms==before.last_progress_ms);
            assert(s.sequence==3&&s.progress==before.progress&&s.flags==before.flags);
            assert(s.accepted==2&&s.accepted==before.accepted);
            assert(s.rejected==before.rejected+(uint32_t)i+1u);
            assert(s.used==before.used);
        }
    }
    check_documented_cadence();
    /* Arbitrary stream is bounded and cannot create control authority. */
    uint32_t random=1;
    for(unsigned i=0;i<100000;++i) {
        random=random*1664525u+1013904223u;
        sh_feed(&s,(uint8_t)(random>>24),100+i);
        assert(s.used<SH_FRAME_BYTES);
        assert(!sh_observe(&s,100+i,1000,500).motion_authority);
    }
    puts("PASS: service health CRC, replay, clocks, deadlines, documented cadence, progress, restart, framing and corruption checks");
    return 0;
}
