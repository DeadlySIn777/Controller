"""Real CNC3 wire qualification of supported motion and missing I/O boundaries.

Uses actual frozen command codec, actual Verilated state/transport/generators,
and explicit ideal external gate/mechanics fixtures. Never opens a device.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'explicit-boundaries-r02'
OUT.mkdir(exist_ok=False)
BASE = HERE / 'spi-twelve-four-plant-r01/inputs'
COPIED = OUT / 'inputs'
COPIED.mkdir()
shutil.copyfile(Path(__file__), COPIED / 'runner-source.py')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
unix = lambda path: '/mnt/' + path.resolve().drive[0].lower() + path.resolve().as_posix()[2:]
sources = list(BASE.glob('*.v')) + [BASE / name for name in ('frames.hpp', 'edge_plant.hpp', 'spi_edge_plant.cpp', 'protocol_v3.py', 'protocol.json')]
source_hashes = {str(path.relative_to(ROOT)): sha(path) for path in sources}
for path in sources:
    shutil.copyfile(path, COPIED / path.name)
spec = importlib.util.spec_from_file_location('boundary_codec', COPIED / 'protocol_v3.py')
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
codec._SPEC = codec.Spec(str(COPIED / 'protocol.json'))
frames = {}
for label, fields in [('DO_UPDATE', {'dout_image': 65535}), ('PROBE_UPDATE', {'probe_arm': 3}),
                      ('INDEX_UPDATE', {'index_arm_mask': 15}), ('PWM_UPDATE', {'pwm0_duty': 1})]:
    frames[label] = codec.encode_update(session=0x11223344, sequence=6, channel_mask=0xfff, rates=[0x400000]*12, **fields)
frames['IO_ENABLE'] = codec.encode_command('IO_ENABLE', session=0x11223344, sequence=6)[1]
frames['IO_WRITE'] = codec.encode_command('IO_WRITE', session=0x11223344, sequence=6, fields={'dout_image': 65535})[1]
frames['motion'] = codec.encode_update(session=0x11223344, sequence=5, channel_mask=0xfff, rates=[0x400000]*12)
header = ['#pragma once', 'namespace boundary {']
for label, data in frames.items():
    header.append('inline const Frame ' + label + '{false,{' + ','.join(map(str, data)) + '}};')
header.append('}')
(COPIED / 'boundary_frames.hpp').write_text('\n'.join(header)+'\n', encoding='utf-8')
(OUT / 'command-frames.json').write_text(json.dumps({name: raw.hex() for name, raw in frames.items()}, indent=2)+'\n', encoding='utf-8')
rig = (COPIED / 'spi_edge_plant.cpp').read_text(encoding='utf-8').split('int main(int argc,char**argv){')[0]
rig = rig.replace('std::ofstream responses{"responses.txt"};', 'std::ofstream responses;')
rig = rig.replace('explicit Rig(){', 'explicit Rig(const std::string& label): responses(label+"-responses.txt"){')
(COPIED / 'rig.hpp').write_text(rig, encoding='utf-8', newline='\n')
(COPIED / 'boundaries.cpp').write_text(r'''#include "rig.hpp"
#include "boundary_frames.hpp"
#include <functional>
static void moving(Rig& r){
 r.commissioning();r.exchange(boundary::motion,"nominal_motion");r.advance(30000);
 check(r.rtl.armed_mask==all_joints&&!r.rtl.fault_word,"actual all12 concurrent movement before boundary");
 for(unsigned i=0;i<12;++i)check(r.observed_rises[i]>20,"all12 pins emit real edges before injection");
 check(!r.rtl.output_request&&!r.rtl.progress_o,"no general I/O request/progress after selftest; motion permit is separate");
}
int main(){try{
 std::ofstream cases("cases.jsonl");
 const std::array<std::pair<std::string,Frame>,6> commands{{
  {"DO_UPDATE",boundary::DO_UPDATE},{"PROBE_UPDATE",boundary::PROBE_UPDATE},
  {"INDEX_UPDATE",boundary::INDEX_UPDATE},{"PWM_UPDATE",boundary::PWM_UPDATE},
  {"IO_ENABLE",boundary::IO_ENABLE},{"IO_WRITE",boundary::IO_WRITE}}};
 for(const auto& item:commands){
  unsigned start=checks;Rig r(item.first);moving(r);auto sequence=r.rtl.last_sequence;
  r.exchange(item.second,"unsupported_command");r.advance(100);
  check(r.rtl.fault_word&&!r.rtl.armed_mask&&r.rtl.enable_n==all_joints&&!r.rtl.step_out,
        "unsupported I/O/probe/index field fails closed at actual state boundary");
  check(r.rtl.last_sequence==sequence,"unsupported command does not consume motion sequence");
  check(!r.rtl.permit_out_req&&!r.rtl.output_request&&!r.rtl.progress_o,"unsupported request cannot enable I/O");
  auto stopped=r.observed_rises;r.exchange(frames::read,"boundary_feedback");r.advance(1000);
  check(r.observed_rises==stopped,"feedback read cannot restart failed request");
  cases<<"{\"case\":\""<<item.first<<"\",\"checks\":"<<checks-start<<",\"sequence\":"<<r.rtl.last_sequence<<",\"reject\":"<<unsigned(r.rtl.last_reject)<<",\"fault\":"<<r.rtl.fault_word<<",\"passed\":true}\n";
 }
 for(unsigned channel=0;channel<12;++channel){
  std::string label="alarm_M"+std::to_string(channel);unsigned start=checks;Rig r(label);moving(r);
  Faults f;f.forced_alarm=static_cast<uint16_t>(1u<<channel);r.plant.faults(f);r.advance(3000);
  check((r.rtl.fault_word&0x10)&&!r.rtl.armed_mask&&r.rtl.enable_n==all_joints,"each of12 alarm channels trips all motion");
  r.exchange(frames::read,"boundary_feedback");
  cases<<"{\"case\":\""<<label<<"\",\"channel\":"<<channel<<",\"checks\":"<<checks-start<<",\"passed\":true}\n";
 }
 for(unsigned channel=0;channel<4;++channel){
  std::string label="encoder_E"+std::to_string(channel);unsigned start=checks;Rig r(label);moving(r);
  Faults f;f.encoder_unplugged=static_cast<uint8_t>(1u<<channel);r.plant.faults(f);r.advance(600);
  check((r.rtl.fault_word&0x80000)&&!r.rtl.armed_mask&&r.rtl.enable_n==all_joints,"each of4 required encoders losing validity trips motion");
  r.exchange(frames::read,"boundary_feedback");
  cases<<"{\"case\":\""<<label<<"\",\"channel\":"<<channel<<",\"checks\":"<<checks-start<<",\"passed\":true}\n";
 }
 std::cout<<"CNC3_BOUNDARIES_PASS cases=22 checks="<<checks<<" real_SPI=1 simulation_only=1\n";
}catch(const std::exception&e){std::cerr<<"CNC3_BOUNDARIES_FAIL "<<e.what()<<'\n';return 1;}}
''', encoding='utf-8', newline='\n')
commands = []
def run(name, argv, stdin=None):
    started = time.monotonic()
    result = subprocess.run(argv, input=stdin, capture_output=True, timeout=900)
    log = OUT / (name+'.log')
    log.write_bytes(result.stdout + result.stderr)
    commands.append({'name': name, 'argv': argv, 'exit': result.returncode, 'seconds': time.monotonic()-started, 'log_sha256': sha(log)})
    if result.returncode:
        raise RuntimeError(name+' failed: '+str(log))
    return result.stdout.decode('utf-8', errors='replace')
failure, cases, parsed = None, [], {}
started = datetime.now(timezone.utc).isoformat()
copied_hashes = {path.name: sha(path) for path in COPIED.iterdir() if path.is_file()}
try:
    # This oracle is the newly compiled immutable frozen C validator. Every
    # boundary frame must be structurally valid before testing state refusal.
    oracle_input = ''.join(f'1 {len(data)} {data.hex()}\n' for data in frames.values()).encode('ascii')
    oracle = HERE / 'cnc3-structural-r01/oracle/check'
    oracle_result = run('frozen-C-command-oracle', ['wsl.exe','-d','GarciaMechBuilder','--',unix(oracle)], oracle_input)
    if oracle_result.splitlines() != ['0']*len(frames):
        raise RuntimeError('Boundary frame is not structurally valid in frozen C oracle')
    obj = OUT / 'obj'
    run('verilate', ['wsl.exe','-d','GarciaMechBuilder','--','verilator','--cc','--compiler','clang',
        '--top-module','cnc3_motion_spi','--Mdir',unix(obj),'-Wall','-Wno-fatal',*[unix(path) for path in sorted(COPIED.glob('*.v'))]])
    run('compile', ['wsl.exe','-d','GarciaMechBuilder','--','clang++','-std=c++17','-O1','-pthread',
        '-I/usr/share/verilator/include','-I/usr/share/verilator/include/vltstd','-I'+unix(obj),'-I'+unix(COPIED),
        unix(COPIED/'boundaries.cpp'),*[unix(path) for path in sorted(obj.glob('*.cpp'))],
        '/usr/share/verilator/include/verilated.cpp','/usr/share/verilator/include/verilated_threads.cpp','-o',unix(OUT/'boundaries')])
    output = run('execute', ['wsl.exe','-d','GarciaMechBuilder','--cd',unix(OUT),'--',unix(OUT/'boundaries')])
    if 'CNC3_BOUNDARIES_PASS cases=22' not in output:
        raise RuntimeError('Missing boundary pass marker')
    cases = [json.loads(line) for line in (OUT/'cases.jsonl').read_text().splitlines()]
    for case in cases:
        rows = (OUT/(case['case']+'-responses.txt')).read_text().splitlines()
        final = next(row for row in rows if row.startswith('boundary_feedback '))
        _, length, raw = final.split()
        data = bytes.fromhex(raw)
        assert len(data) == int(length) == 176
        value = codec.decode_response('CS_FB', data)
        assert value['armed_mask'] == 0 and value['pos_continuity'] == 0 and value['fault_word'] != 0
        assert value['din_age'] == 255 and value['ain_age'] == 255 and value['ain_status'] == 0
        assert value['index_armed_mask'] == 0
        if case['case'].startswith('alarm_'):
            assert value['alarm_levels'] & (1 << case['channel'])
            assert value['alarm_trip_latched'] & (1 << case['channel'])
        if case['case'].startswith('encoder_'):
            assert not value['encoder_valid_mask'] & (1 << case['channel'])
            assert value['encoder_fault_mask'] & (1 << case['channel'])
        parsed[case['case']] = value
    (OUT/'decoded-feedback.json').write_text(json.dumps(parsed, indent=2)+'\n', encoding='utf-8')
except Exception as error:
    failure = repr(error)
unchanged = all(sha(ROOT/name) == digest for name, digest in source_hashes.items()) and all(sha(COPIED/name) == digest for name,digest in copied_hashes.items())
receipt = {'status': 'PASS' if failure is None and unchanged and len(cases)==22 else 'FAIL', 'failure': failure,
    'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(), 'cases': cases,
    'source_sha256': source_hashes, 'copied_input_sha256': copied_hashes, 'inputs_unchanged': unchanged,
    'executions': commands, 'actual_CNC3_96_176_transport': True, 'actual_twelve_generators': True,
    'DI_DO_probe_implemented': False, 'adopted_into_product': False, 'source_IS2_qualified': False,
    'HAL_or_LinuxCNC_run': False, 'physical_evidence': False, 'full_machine_milestone': False,
    'qualification_providers': 'explicit ideal external permission/watchdog and mechanical simulation fixtures',
    'meaning': 'Unsupported I/O/probe/index requests refuse; each real alarm and encoder-valid lane inhibits actual motion; stale DI/AI not promoted'}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:receipt[key] for key in ('status','failure','completed_utc','inputs_unchanged')},indent=2))
raise SystemExit(0 if receipt['status']=='PASS' else 1)
