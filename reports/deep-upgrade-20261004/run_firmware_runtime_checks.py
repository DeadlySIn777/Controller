"""Fresh copied-source host/ARM checks; never opens or flashes a machine."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'firmware-host-target-r01'
if OUT.exists():
    raise SystemExit('Refusing to overwrite evidence directory')
OUT.mkdir()
started = datetime.now(timezone.utc).isoformat()
names = [p.relative_to(ROOT).as_posix() for p in (ROOT / 'firmware/motherboard_iol1_readonly').rglob('*') if p.is_file()]
names += ['controller_config/runtime.py', 'controller_config/persistent_runtime.py', 'controller_config/recovery.py',
          'tests/test_runtime_configuration.py', 'tests/test_persistent_runtime.py', 'tests/test_configuration_recovery.py',
          'tests/test_motherboard_iol1_readonly.py', 'tests/test_recovery_cli.py']
raw = {name: (ROOT / name).read_bytes() for name in names}
for name, data in raw.items():
    target = OUT / 'inputs' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
for name in ['iol1.c', 'iol1.h']:
    target = OUT / 'before' / name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes((OUT.parent / 'before/firmware/motherboard_iol1_readonly' / name).read_bytes())

harness = r'''#include "iol1.h"
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
'''
(OUT / 'late_poll_control.c').write_text(harness, encoding='utf-8', newline='\n')
script = '''#!/bin/sh
set -eu
cd "$(dirname "$0")"
src=inputs/firmware/motherboard_iol1_readonly
clang --version > clang-version.txt
ld.lld --version > linker-version.txt
gcc --version > host-gcc-version.txt
flags="--target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -O2 -g -std=c11 -Wall -Wextra -Werror -ffreestanding -fno-builtin -ffunction-sections -fdata-sections"
clang $flags -c $src/iol1.c -o iol1.o
clang --target=arm-none-eabi -mcpu=cortex-m0plus -mthumb -c $src/startup.S -o startup.o
for slot in 0 1 2 3
do
 clang $flags -I$src/vendor/ST -I$src/vendor/ARM -DNODE_SLOT=$slot -c $src/target.c -o target$slot.o
 clang $flags -S -I$src/vendor/ST -I$src/vendor/ARM -DNODE_SLOT=$slot $src/target.c -o target$slot.s
 ld.lld -T $src/stm32g031.ld --gc-sections -Map=node$slot.map startup.o iol1.o target$slot.o -o node$slot.elf
 readelf -h -l -S -s node$slot.elf > node$slot-elf-review.txt
 size node$slot.elf >> sizes.txt
 objcopy -I elf32-little -O binary node$slot.elf node$slot.bin
done
gcc -O2 -std=c11 -Wall -Wextra -Werror $src/iol1.c $src/test_protocol.c -o host-protocol
./host-protocol > host-protocol.log
gcc -O1 -g -fsanitize=undefined,address -fno-omit-frame-pointer -std=c11 -Wall -Wextra -Werror $src/iol1.c $src/test_protocol.c -o sanitized-protocol
./sanitized-protocol > sanitized-protocol.log
gcc -O2 -std=c11 -Wall -Wextra -Werror -Ibefore before/iol1.c late_poll_control.c -o old-late-poll
./old-late-poll 1 > late-poll-before.log
gcc -O2 -std=c11 -Wall -Wextra -Werror -I$src $src/iol1.c late_poll_control.c -o new-late-poll
./new-late-poll 0 > late-poll-after.log
'''
(OUT / 'run.sh').write_text(script, encoding='utf-8', newline='\n')
wsl_path = '/mnt/' + OUT.drive[0].lower() + '/' + OUT.as_posix()[3:] + '/run.sh'

def host_tests(pattern):
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern, '-v']
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    output = proc.stdout + proc.stderr
    (OUT / (pattern + '.log')).write_text(output, encoding='utf-8')
    match = re.search(r'Ran (\d+) tests?', output)
    return {'pattern': pattern, 'exit_code': proc.returncode, 'tests': int(match[1]) if match else None}

patterns = ['test_runtime_configuration.py', 'test_configuration_recovery.py', 'test_persistent_runtime.py',
            'test_motherboard_iol1_readonly.py', 'test_recovery_cli.py']
with ThreadPoolExecutor(max_workers=6) as executor:
    build = executor.submit(subprocess.run, ['wsl.exe', '-d', 'GarciaMechBuilder', '--', 'sh', wsl_path], capture_output=True, text=True)
    host_results = list(executor.map(host_tests, patterns))
    proc = build.result()
(OUT / 'build.log').write_text(proc.stdout + proc.stderr, encoding='utf-8')
receipt = {'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
           'input_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in raw.items()},
           'inputs_unchanged': all((ROOT / name).read_bytes() == data for name, data in raw.items()),
           'build_exit_code': proc.returncode, 'python_host_suites': host_results,
           'hardware_accessed': False, 'HDL_rerun': False, 'FPGA_synthesis_rerun': False,
           'target_execution': False, 'physical_qualification': False, 'production_ready': False}
if proc.returncode == 0:
    receipt['host_C_checks'] = int(re.search(r'PASS (\d+)', (OUT / 'host-protocol.log').read_text())[1])
    receipt['sanitized_host_C_checks'] = int(re.search(r'PASS (\d+)', (OUT / 'sanitized-protocol.log').read_text())[1])
    receipt['ARM_target_compile_link_slots'] = [0, 1, 2, 3]
    receipt['late_poll_before'] = (OUT / 'late-poll-before.log').read_text().strip()
    receipt['late_poll_after'] = (OUT / 'late-poll-after.log').read_text().strip()
    receipt['target_sizes'] = (OUT / 'sizes.txt').read_text()
    receipt['target_binary_sha256'] = {f'node{slot}.bin': hashlib.sha256((OUT / f'node{slot}.bin').read_bytes()).hexdigest() for slot in range(4)}
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in receipt.items() if key != 'input_sha256'}, indent=2))
raise SystemExit(0 if proc.returncode == 0 and all(item['exit_code'] == 0 for item in host_results) and receipt['inputs_unchanged'] else 1)
