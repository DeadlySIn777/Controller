"""Record retained ESP32-S3 build and host-test evidence.

Compile/host-test evidence only. This script never flashes, monitors or opens a
serial port. It optionally runs the two ESP-IDF builds through build-local.ps1
and the host core tests in WSL, then copies the images and logs from the
git-ignored .build/ folder into evidence/, writes evidence/SHA256SUMS and
evidence/manifest.json, and refreshes the build/source hashes in
reports/ESP_SERVICE_BUILD.json.

Without --build it refuses to record when any firmware input (source, Kconfig,
CMake file, sdkconfig defaults or the variant's effective sdkconfig) is newer
than the image in .build/, so current source hashes are never paired with
stale images. Without --host-tests any earlier host-core-test.log is removed
from evidence/ instead of being carried forward, and the report says the host
tests were not rerun by this record.

    python firmware/esp32_service/record_evidence.py --build --clean --host-tests
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = HERE / '.build'
EVIDENCE = HERE / 'evidence'
REPORT = ROOT / 'reports' / 'ESP_SERVICE_BUILD.json'

VARIANTS = (
    # variant, build dir, sdkconfig, build switch, log, retained image name
    ('esp32s3', BUILD / 'esp32s3', HERE / 'sdkconfig', [],
     'default-build.log', 'cnc_service-esp32s3.bin'),
    ('uart-compile-check', BUILD / 'uart-compile-check', BUILD / 'uart-sdkconfig',
     ['-UartCompileCheck'], 'uart-build-check.log',
     'cnc_service-uart-compile-check.bin'),
)
# The UART variant's effective configuration is generated (git-ignored) from
# sdkconfig.defaults + sdkconfig.uart-build-check.defaults; a copy is retained.
UART_SDKCONFIG_RETAINED = 'uart-compile-check.sdkconfig'
HOST_LOG = 'host-core-test.log'
# Inputs whose change must invalidate a retained image (relative to HERE).
FIRMWARE_INPUTS = (
    'core/service_health.c', 'core/service_health.h',
    'main/service_main.c', 'main/CMakeLists.txt', 'main/Kconfig.projbuild',
    'CMakeLists.txt', 'sdkconfig.defaults', 'sdkconfig.uart-build-check.defaults',
)
SOURCES = (
    'firmware/esp32_service/core/service_health.c',
    'firmware/esp32_service/core/service_health.h',
    'firmware/esp32_service/main/service_main.c',
    'firmware/esp32_service/main/CMakeLists.txt',
    'firmware/esp32_service/main/Kconfig.projbuild',
    'firmware/esp32_service/CMakeLists.txt',
    'firmware/esp32_service/sdkconfig',
    'firmware/esp32_service/sdkconfig.defaults',
    'firmware/esp32_service/sdkconfig.uart-build-check.defaults',
    'firmware/esp32_service/build-local.ps1',
    'firmware/esp32_service/record_evidence.py',
    'firmware/esp32_service/tests/test_service_health.c',
    'controller_lab/service_health.py',
    'tests/test_service_health.py',
)
HOST_TEST = (
    'set -e; cd "$1"; mkdir -p firmware/esp32_service/.build; '
    'echo "$(. /etc/os-release; echo $PRETTY_NAME)"; gcc --version | head -n 1; '
    'set -x; '
    'gcc -std=c11 -O1 -g -Wall -Wextra -Werror -pedantic '
    '-fsanitize=address,undefined -fno-omit-frame-pointer '
    '-Ifirmware/esp32_service/core firmware/esp32_service/core/service_health.c '
    'firmware/esp32_service/tests/test_service_health.c '
    '-o firmware/esp32_service/.build/test_service_health_sanitized; '
    'firmware/esp32_service/.build/test_service_health_sanitized'
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path, text):
    with open(path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text)


def run_logged(command, log):
    # ESP-IDF's export.ps1 refuses to activate when launched from Git Bash/MSYS.
    env = {k: v for k, v in os.environ.items() if k not in ('MSYSTEM', 'MSYSTEM_PREFIX')}
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    text = result.stdout.decode('utf-8', 'replace').replace('\r\n', '\n')
    write_text(log, text + f'\n[record_evidence] exit status {result.returncode}\n')
    if result.returncode != 0:
        sys.exit(f'{" ".join(command)} failed ({result.returncode}); see {log}')
    return text


def powershell():
    return shutil.which('pwsh') or shutil.which('powershell') or 'powershell'


def wsl_path(path):
    drive, rest = path.drive.rstrip(':').lower(), path.as_posix()[2:]
    return f'/mnt/{drive}{rest}'


def sdk_flags(sdkconfig):
    text = sdkconfig.read_text(encoding='utf-8')
    def flag(name):
        if re.search(rf'^CONFIG_{name}=y$', text, re.M):
            return True
        return False
    gpio = re.search(r'^CONFIG_CNC_SERVICE_HOST_RX_GPIO=(-?\d+)$', text, re.M)
    return {
        'app_reproducible_build': flag('APP_REPRODUCIBLE_BUILD'),
        'app_compile_time_date': flag('APP_COMPILE_TIME_DATE'),
        'bootloader_compile_time_date': flag('BOOTLOADER_COMPILE_TIME_DATE'),
        'host_rx_gpio': int(gpio.group(1)) if gpio else None,
    }


def app_description(image):
    """Decode esp_app_desc_t, which follows the image and first segment headers."""
    data = image.read_bytes()[24 + 8:24 + 8 + 256]
    magic, secure_version = struct.unpack_from('<II', data, 0)
    if magic != 0xABCD5432:
        sys.exit(f'{image}: esp_app_desc_t magic not found')
    text = lambda start, size: data[start:start + size].split(b'\0')[0].decode('ascii')
    return {
        'project_version': text(16, 32), 'project_name': text(48, 32),
        'embedded_time': text(80, 16), 'embedded_date': text(96, 16),
        'idf_ver': text(112, 32), 'app_elf_sha256': data[144:176].hex(),
    }


def stale_inputs(image, inputs):
    """Return the inputs newer than image (every input if image is missing)."""
    if not image.is_file():
        return [str(image)]
    built = image.stat().st_mtime
    return [str(path) for path in inputs if path.is_file() and path.stat().st_mtime > built]


def refuse_stale_images(variants=None):
    """Exit if any variant image in .build/ is older than one of its inputs."""
    problems = []
    for variant, build_dir, sdkconfig, *_ in (variants or VARIANTS):
        inputs = [HERE / name for name in FIRMWARE_INPUTS] + [sdkconfig]
        stale = stale_inputs(build_dir / 'cnc_service.bin', inputs)
        if stale:
            problems.append(f'{variant}: ' + ', '.join(stale))
    if problems:
        sys.exit('refusing to record images older than their inputs; rerun with --build '
                 '(--clean for evidence):\n  ' + '\n  '.join(problems))


def drop_unrun_host_log(evidence=None):
    """Remove a host-test log left by an earlier record so it is not re-hashed."""
    log = (evidence or EVIDENCE) / HOST_LOG
    if log.is_file():
        log.unlink()
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--build', action='store_true',
                        help='run both build-local.ps1 variants first (compile only)')
    parser.add_argument('--clean', action='store_true',
                        help='with --build: delete each variant build directory first so '
                             'every object is recompiled (build output only)')
    parser.add_argument('--host-tests', action='store_true',
                        help='run the strict-warning ASan/UBSan host core tests in WSL')
    parser.add_argument('--wsl-distro', default='GarciaMechBuilder')
    args = parser.parse_args()
    BUILD.mkdir(exist_ok=True)
    EVIDENCE.mkdir(exist_ok=True)

    if args.clean and not args.build:
        sys.exit('--clean requires --build')
    if args.build:
        for _, build_dir, sdkconfig, switch, log, _ in VARIANTS:
            if args.clean and build_dir.is_dir():
                assert build_dir.parent == BUILD
                shutil.rmtree(build_dir)
            if args.clean and sdkconfig.parent == BUILD and sdkconfig.is_file():
                # Generated config: regenerate it from the tracked defaults files.
                sdkconfig.unlink()
            run_logged([powershell(), '-NoProfile', '-ExecutionPolicy', 'Bypass',
                        '-File', str(HERE / 'build-local.ps1'), *switch], BUILD / log)
    refuse_stale_images()
    host = None
    if args.host_tests:
        output = run_logged(['wsl', '-d', args.wsl_distro, '--exec', 'sh', '-c', HOST_TEST,
                             'host-test', wsl_path(ROOT)], BUILD / HOST_LOG)
        passed = [line for line in output.splitlines() if line.startswith('PASS:')]
        if len(passed) != 1:
            sys.exit('host core test did not print exactly one PASS line')
        host = {'result': 'passed', 'distro': args.wsl_distro,
                'environment': output.splitlines()[0],
                'compiler': output.splitlines()[1], 'pass_line': passed[0]}

    builds = []
    for variant, build_dir, sdkconfig, _, log, retained in VARIANTS:
        image = build_dir / 'cnc_service.bin'
        shutil.copyfile(image, EVIDENCE / retained)
        shutil.copyfile(BUILD / log, EVIDENCE / log)
        description = app_description(EVIDENCE / retained)
        flags = sdk_flags(sdkconfig)
        if sdkconfig.parent == BUILD:
            shutil.copyfile(sdkconfig, EVIDENCE / UART_SDKCONFIG_RETAINED)
            config_path = f'firmware/esp32_service/evidence/{UART_SDKCONFIG_RETAINED}'
        else:
            config_path = sdkconfig.relative_to(ROOT).as_posix()
        builds.append({
            'variant': variant, 'result': 'compiled-and-linked',
            'host_rx_gpio': flags.pop('host_rx_gpio'),
            'gpio_approved_for_hardware': False,
            'retained_image': f'firmware/esp32_service/evidence/{retained}',
            'size_bytes': (EVIDENCE / retained).stat().st_size,
            'sha256': sha256(EVIDENCE / retained),
            'build_log': f'firmware/esp32_service/evidence/{log}',
            'build_log_sha256': sha256(EVIDENCE / log),
            'effective_sdkconfig': config_path,
            'effective_sdkconfig_sha256': sha256(ROOT / config_path),
            'app_description': description, 'sdkconfig': flags,
        })
    if host:
        shutil.copyfile(BUILD / HOST_LOG, EVIDENCE / HOST_LOG)
        host['log'] = f'firmware/esp32_service/evidence/{HOST_LOG}'
        host['log_sha256'] = sha256(EVIDENCE / HOST_LOG)
    else:
        drop_unrun_host_log()

    reproducible = all(b['sdkconfig']['app_reproducible_build'] and
                       not b['sdkconfig']['app_compile_time_date'] for b in builds)
    manifest = {
        'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'evidence_class': ('target compilation (ESP-IDF)' +
                           (' plus host test' if host else '') + '; no device flashed'),
        'reproducible_build': reproducible,
        'reproducibility_note': (
            'Configured reproducible.' if reproducible else
            'Not reproducible: CONFIG_APP_COMPILE_TIME_DATE embeds the time at which '
            'the ESP-IDF app descriptor was compiled (app_description.embedded_date/time; '
            'an incremental build keeps the earlier stamp) and CONFIG_APP_REPRODUCIBLE_BUILD '
            'is unset, so a clean rebuild of identical source yields different image '
            'hashes. The hashes identify the retained copies in this folder, not '
            'something a rebuild is expected to reproduce.'),
        'ran_builds_this_record': args.build,
        'build_mode': (('clean' if args.clean else 'incremental') if args.build else
                       'not rebuilt (images checked newer than all firmware inputs)'),
        'ran_host_tests_this_record': bool(host),
        'flashed': False, 'physical_hardware_tested': False,
        'motion_authority': False,
        'builds': builds, 'host_core_test': host,
        'source_sha256': {name: sha256(ROOT / name) for name in SOURCES},
    }
    write_text(EVIDENCE / 'manifest.json', json.dumps(manifest, indent=2) + '\n')
    retained = sorted(p.name for p in EVIDENCE.iterdir()
                      if p.is_file() and p.name not in ('SHA256SUMS',))
    write_text(EVIDENCE / 'SHA256SUMS',
               ''.join(f'{sha256(EVIDENCE / name)} *{name}\n' for name in retained))

    report = json.loads(REPORT.read_text(encoding='utf-8'))
    report['date'] = manifest['recorded_utc'][:10]
    report['target_builds'] = [
        {key: b[key] for key in ('variant', 'result', 'host_rx_gpio', 'size_bytes',
                                 'sha256', 'gpio_approved_for_hardware')}
        for b in builds]
    report['source_sha256'] = manifest['source_sha256']
    report['evidence_record'] = {
        key: manifest[key] for key in ('recorded_utc', 'ran_builds_this_record', 'build_mode',
                                       'ran_host_tests_this_record')}
    validation = report.setdefault('host_core_validation', {})
    if host:
        validation['result'] = 'passed'
        validation['compiler'] = f"WSL {host['environment']}, {host['compiler']}"
    else:
        validation['result'] = ('not rerun by this record; no host-test log is retained '
                                'for these sources')
    retention = report.setdefault('evidence_retention', {})
    retention.update({
        'policy': 'retained-copies', 'reproducible_build': reproducible,
        'note': manifest['reproducibility_note'],
        'manifest': 'firmware/esp32_service/evidence/manifest.json',
        'manifest_sha256': sha256(EVIDENCE / 'manifest.json'),
        'files': {b['variant']: b['retained_image'] for b in builds} | {
            'default_build_log': builds[0]['build_log'],
            'uart_build_check_log': builds[1]['build_log'],
            'uart_compile_check_sdkconfig': builds[1]['effective_sdkconfig'],
        } | ({'host_core_test_log': host['log']} if host else {}),
    })
    write_text(REPORT, json.dumps(report, indent=2) + '\n')
    print(json.dumps({'reproducible_build': reproducible,
                      'builds': {b['variant']: b['sha256'] for b in builds},
                      'host_core_test': host and host['result']}, indent=2))


if __name__ == '__main__':
    main()
