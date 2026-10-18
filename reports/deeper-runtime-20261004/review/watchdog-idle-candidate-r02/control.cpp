
#include "virtual_provider.hpp"
#include <cstdio>
int main(){
 cnc3_sim::VirtualWatchdog watchdog(550000,100);
 for(unsigned t=0;t<10000;++t)watchdog.tick(t,false,false,false);
 bool fault=false;for(unsigned t=10000;t<10010;++t)fault=watchdog.tick(t,false,false,true);
 bool at_clear=watchdog.tick(10010,false,false,false);
 bool at_99=false;for(unsigned t=10011;t<=10109;++t)at_99=watchdog.tick(t,false,false,false);
 bool at_100=watchdog.tick(10110,false,false,false);
 std::printf("{\"fault_observed_unhealthy\":%s,\"healthy_at_clear\":%s,\"healthy_at_99\":%s,\"healthy_at_100\":%s}\n",fault?"false":"true",at_clear?"true":"false",at_99?"true":"false",at_100?"true":"false");
}
