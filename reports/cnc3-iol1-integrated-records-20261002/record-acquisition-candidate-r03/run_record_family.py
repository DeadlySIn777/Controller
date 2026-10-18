from pathlib import Path
import argparse,hashlib,json,subprocess,shutil,uuid,re,os
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MOTION=HERE/'inputs/motion'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
def main(out):
 if out.exists():raise RuntimeError('fresh output required')
 out.mkdir(parents=True)
 sources=[HERE/'cnc_iol1_record_master.v',HERE/'cnc_iol1_record_acquisition.v',HERE/'cnc_mbr2_stream_checker.v',*sorted(MOTION.glob('cnc3_*.v')),MOTION/'inputs/workspace/gateware/v3/rtl/cnc3_spi_transport.v',MOTION/'inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v']
 before={str(p):sha(p) for p in sources}
 for p in sources:shutil.copyfile(p,out/p.name)
 old=(MOTION/'cnc3_motion_spi.v').read_text();header=old[old.index('module cnc3_motion_spi ('):old.index(');')+2]
 header=header.replace('cnc3_motion_spi (','cnc3_motion_acquisition_composition (')
 header=header[:-3]+''',
 input wire diagnostic_enable,input wire[3:0]iol1_miso,
 output wire[3:0]iol1_cs_n,iol1_sclk,iol1_mosi,iol1_fault,iol1_accepted,
 output wire[3:0]diagnostic_sample_valid,diagnostic_transport_seen,
 output wire[3:0]commercial_active,factory_identity_verified,analog_valid,
 output wire[511:0]last_valid_realtime,last_integrity_realtime,
 output wire[63:0]sample_age_us,last_reply_sequence,analog_codes,
 output wire[11:0]last_reply_state,
 output wire[23:0]diagnostic_filtered_di,diagnostic_raw_di,
 output wire[15:0]diagnostic_do_applied,
 output wire[3:0] record_integrity_observed,record_failed,chunk_accepted,
 output wire[511:0]observed_board_serial,output wire[383:0]observed_mcu_uid,
 output wire[127:0]observed_generation,output wire[23:0]chunk_index,output wire[255:0]chunk_data,
 output wire dic_configuration_echo_valid,signature_authenticated,output wire[31:0]dic_configuration_crc
);
// Composition counts retained exact motion + real acquisition. Diagnostic data
// cannot substitute for the absent qualified factory/provider inputs of motion.
cnc3_motion_spi motion(.*);
cnc_iol1_record_acquisition diagnostic(.clk(clk),.reset_n(rst_n),.enable(diagnostic_enable),.miso(iol1_miso),.cs_n(iol1_cs_n),.sclk(iol1_sclk),.mosi(iol1_mosi),.fault_latched(iol1_fault),.accepted(iol1_accepted),.diagnostic_sample_valid(diagnostic_sample_valid),.diagnostic_transport_seen(diagnostic_transport_seen),.commercial_active(commercial_active),.factory_identity_verified(factory_identity_verified),.last_valid_realtime(last_valid_realtime),.last_integrity_realtime(last_integrity_realtime),.sample_age_us(sample_age_us),.last_reply_sequence(last_reply_sequence),.last_reply_state(last_reply_state),.diagnostic_filtered_di(diagnostic_filtered_di),.diagnostic_raw_di(diagnostic_raw_di),.diagnostic_do_applied(diagnostic_do_applied),.analog_valid(analog_valid),.analog_codes(analog_codes),.record_integrity_observed(record_integrity_observed),.record_failed(record_failed),.chunk_accepted(chunk_accepted),.chunk_index(chunk_index),.chunk_data(chunk_data),.observed_board_serial(observed_board_serial),.observed_mcu_uid(observed_mcu_uid),.observed_generation(observed_generation),.dic_configuration_echo_valid(dic_configuration_echo_valid),.dic_configuration_crc(dic_configuration_crc),.signature_authenticated(signature_authenticated));
endmodule
'''
 (out/'cnc3_motion_acquisition_composition.v').write_text(header,encoding='utf8',newline='\n')
 files=' '.join(p.name for p in sources)+' cnc3_motion_acquisition_composition.v';work='iol1-acquire-'+uuid.uuid4().hex[:10]
 (out/'synth.ys').write_text(f'''read_verilog -sv {files}
hierarchy -check -top cnc3_motion_acquisition_composition
proc
check -assert
select -assert-none t:$dlatch t:$adlatch t:$dlatchsr
synth_efinix -top cnc3_motion_acquisition_composition
delete t:$scopeinfo
check -assert -mapped
select -assert-none t:EFX_LATCH t:$_DLATCH_* t:$dlatch t:$adlatch t:$dlatchsr
tee -o mapped-stat.json stat -json
write_json family-mapped.json
''',encoding='utf8',newline='\n')
 (out/'run.sh').write_text(f'''#!/bin/sh
set -eu
cd '{unix(out)}'
verilator --lint-only --top-module cnc3_motion_acquisition_composition -Wall --Wno-fatal {files} > lint.log 2>&1
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/{work}"
cp *.v synth.ys "$rootfs/work/{work}/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/{work}; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/{work}/"*.json "$rootfs/work/{work}/"*.log "$rootfs/work/{work}/"*.txt .
test "$result" -eq 0
''',encoding='utf8',newline='\n')
 r=subprocess.run(['wsl','-d',os.environ.get('CNC3_WSL_DISTRO','GarciaMechBuilder'),'--','sh',unix(out/'run.sh')],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=900)
 (out/'command.log').write_text(r.stdout+r.stderr,encoding='utf8',newline='\n')
 lint=(out/'lint.log').read_text() if(out/'lint.log').is_file() else ''
 warnings=re.findall(r'%Warning-([A-Z0-9_]+):',lint);errors=re.findall(r'%Error[^\n]*',lint)
 mapped=json.loads((out/'mapped-stat.json').read_text()) if(out/'mapped-stat.json').is_file() else {}
 resources=mapped.get('design',{}).get('num_cells_by_type',{})
 admitted=[]
 for block in re.split(r'(?=%Warning-)',lint):
  if not block.startswith('%Warning-'):continue
  category=block.split(':',1)[0].removeprefix('%Warning-')
  if category=='UNUSEDSIGNAL' or(category=='BLKSEQ' and 'cnc3_motion_state.v:' in block and 'cycle_faults=0;' in block):admitted.append(category)
 lint_pass=not errors and len(admitted)==len(warnings)
 unchanged=all(sha(Path(p))==h for p,h in before.items())
 receipt={'status':'PASS' if r.returncode==0 and lint_pass and unchanged and resources else 'FAIL','mapped_resources':resources,'retained_motion_baseline_LUT4':12835,'retained_diagnostic_composition_LUT4':16154,'record_increment_vs_diagnostic':resources.get('EFX_LUT4',0)-16154,'LUT4_increment':resources.get('EFX_LUT4',0)-12835,'lint_categories':warnings,'lint_errors':errors,'lint_pass':lint_pass,'lint_admission':'Only explicitly unused diagnostic/provider/index outputs and retained exact two cycle_faults=0 same-cycle union scratch assignments; no width/latch/errors admitted','input_hashes':before,'inputs_unchanged':unchanged,'scope':'actual exact motion baseline + read-only record/config acquisition physically independent, no factory qualifier linkage; dormant incomplete IS2 CAP3 page mux not included','coarse_T20_capacity_screen':{'status':'PASS' if resources.get('EFX_LUT4',0)+resources.get('EFX_ADD',0)<=19728 else 'FAIL','device_LEs':19728,'mapped_LUT4_plus_ADD':resources.get('EFX_LUT4',0)+resources.get('EFX_ADD',0),'frozen_diagnostic_LUT4_plus_ADD':16154+6806,'basis':'T20 manufacturer LE contains a LUT OR full adder; current mapped primitive lower-bound screen. Vendor resynthesis/optimization can change the netlist; no board/device change or fit claim','primary_local':'research/fpga-core/trion20-ds-v6.0.txt','primary_URL':'https://www.efinixinc.com/shop/t20.php'},'vendor_T20_fit_timing_bitstream':False,'physical_timing_or_new_ratings':False,'output_hashes':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'resources':resources,'increment':receipt['LUT4_increment']}));return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);raise SystemExit(main(p.parse_args().out.resolve()))
