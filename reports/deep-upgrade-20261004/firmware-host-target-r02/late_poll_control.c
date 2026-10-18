#include "iol1.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void make_frame(uint8_t *f, unsigned seq, unsigned ctl) {
    memset(f, 0, 40); f[0]=0xa7; f[1]=1; f[2]=IOL1_DIC; f[3]=0;
    f[5]=1; f[7]=seq; f[8]=ctl; f[9]=0xff;
    uint32_t c=iol1_crc32c(f,36);
    for (unsigned k=0;k<4;k++) f[36+k]=(uint8_t)(c>>(24-8*k));
}
int main(int argc, char **argv) {
    iol1_node n; uint8_t f[40]; iol1_transport t={320,40,40,0,1};
    iol1_init(&n,IOL1_DIC,0); make_frame(f,0,1);
    if (!iol1_accept(&n,f,t,0)) return 2;
    make_frame(f,1,0); int accepted=iol1_accept(&n,f,t,1000);
    printf("poll_at_deadline_accepted=%d state=%u good=%lu timestamp=%lu\n",accepted,n.state,(unsigned long)n.good,(unsigned long)n.accepted_us);
    return argc != 2 || accepted != atoi(argv[1]);
}
