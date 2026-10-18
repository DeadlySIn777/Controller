#include "manifest.h"
#include <stdio.h>
int main(int argc,char**argv){
    struct cnc3_sim_manifest manifest;
    if(argc!=2)return 2;
    int result=cnc3_sim_manifest_read(argv[1],&manifest);
    printf("%s\n",result?"REFUSED":"ACCEPTED");return result?1:0;
}
