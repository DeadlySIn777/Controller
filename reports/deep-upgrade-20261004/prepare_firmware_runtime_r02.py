"""Prepare a second fresh verification runner, preserving the first run."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
script = (HERE / 'run_firmware_runtime_checks.py').read_text(encoding='utf-8')
script = script.replace("'firmware-host-target-r01'", "'firmware-host-target-r02'")
insert = '''
for name in ['iol1.c', 'iol1.h']:
    target = OUT / 'cache-before' / name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes((OUT.parent / 'firmware-host-target-r01/inputs/firmware/motherboard_iol1_readonly' / name).read_bytes())
cache_harness = r\'''#include "iol1.h"
#include <stdio.h>
#include <stdlib.h>
static uint16_t age(uint32_t now, uint32_t sampled, volatile uint8_t *valid) {
#ifdef CACHE_API_POINTER
    return iol1_observation_age(now,sampled,valid);
#else
    return iol1_observation_age(now,sampled,*valid);
#endif
}
int main(int argc, char **argv) {
    uint8_t valid=1; uint32_t sampled=100;
    uint16_t saturated=age(sampled+65535u,sampled,&valid);
    uint8_t valid_after_saturation=valid;
    uint16_t wrapped=age(sampled,sampled,&valid);
    printf("at_saturation=%u validity=%u at_full_wrap=%u validity=%u\\n", saturated,valid_after_saturation,wrapped,valid);
    return argc != 2 || saturated != 0xffffu || wrapped != (atoi(argv[1])?0:0xffffu) || valid != atoi(argv[1]);
}
\'''
(OUT / 'cache_lifecycle_control.c').write_text(cache_harness, encoding='utf-8', newline='\\n')
'''
script = script.replace("harness = r'''", insert + "\nharness = r'''", 1)
commands = '''
gcc -O2 -std=c11 -Wall -Wextra -Werror -Icache-before cache-before/iol1.c cache_lifecycle_control.c -o old-cache-lifecycle
./old-cache-lifecycle 1 > cache-lifecycle-before.log
gcc -O2 -std=c11 -Wall -Wextra -Werror -DCACHE_API_POINTER -I$src $src/iol1.c cache_lifecycle_control.c -o new-cache-lifecycle
./new-cache-lifecycle 0 > cache-lifecycle-after.log
'''
script = script.replace('./new-late-poll 0 > late-poll-after.log\n', './new-late-poll 0 > late-poll-after.log\n' + commands)
script = script.replace("    receipt['target_sizes']", "    receipt['cache_lifecycle_before'] = (OUT / 'cache-lifecycle-before.log').read_text().strip()\n    receipt['cache_lifecycle_after'] = (OUT / 'cache-lifecycle-after.log').read_text().strip()\n    receipt['target_sizes']")
with (HERE / 'run_firmware_runtime_checks_r02.py').open('x', encoding='utf-8', newline='\n') as handle:
    handle.write(script)
print('Prepared r02 runner without changing r01 evidence')
