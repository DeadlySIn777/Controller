"""Extend the existing actual-wire bench; original accepted evidence stays immutable."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent
OUT=HERE/'stage-r02';OUT.mkdir(exist_ok=False)
source=HERE/'stage-r01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in [source/'spi_edge_plant.cpp',source/'edge_plant.hpp',HERE/'run_spi_edge_plant_r01.py',Path(__file__)]}
shutil.copyfile(source/'edge_plant.hpp',OUT/'edge_plant.hpp')
text=(source/'spi_edge_plant.cpp').read_text()
old='''  }else if(scenario=="encoder_unplug"){
'''
new='''  }else if(scenario=="CS_stuck_low"){
   const auto sequence=rig.rtl.last_sequence;
   rig.rtl.spi_cs_cmd_n=0;rig.advance(250100);
   check((rig.rtl.fault_word&2)&&rig.rtl.armed_mask==0,"unreleased physical CS cannot feed watchdog");
   check(rig.rtl.last_sequence==sequence,"incomplete transaction cannot consume sequence");
   rig.rtl.spi_cs_cmd_n=1;rig.advance(12);
  }else if(scenario=="bad_CRC"||scenario=="replayed_update"||scenario=="wrong_session"||
           scenario=="MOSI_stuck_high"||scenario=="MOSI_stuck_low"||scenario=="short_frame"){
   const auto sequence=rig.rtl.last_sequence;
   Frame damaged=frames::fault_update;
   if(scenario=="bad_CRC")damaged.bytes.back()^=1;
   if(scenario=="replayed_update")damaged=frames::updates.back();
   if(scenario=="wrong_session")damaged=frames::foreign_update;
   if(scenario=="MOSI_stuck_high")for(auto&b:damaged.bytes)b=255;
   if(scenario=="MOSI_stuck_low")for(auto&b:damaged.bytes)b=0;
   if(scenario=="short_frame")damaged.bytes.pop_back();
   rig.exchange(damaged,"injected_transport_fault");rig.advance(100);
   check(rig.rtl.fault_word&&rig.rtl.armed_mask==0,"actual malformed or stale SPI transaction inhibits motion");
   check(rig.rtl.last_sequence==sequence,"rejected wire transaction cannot advance command sequence");
  }else if(scenario=="encoder_unplug"){
'''
assert text.count(old)==1;text=text.replace(old,new)
old='''   check(rig.observed_rises==before&&rig.rtl.armed_mask==0,"restoring a fault cannot automatically restart motion");
'''
new=old+'''   rig.exchange(frames::fault_update,"post_fault_valid_update");rig.advance(20000);
   check(rig.observed_rises==before&&rig.rtl.armed_mask==0&&rig.rtl.fault_word,
         "a correctly encoded fresh UPDATE cannot restart faulted real motion");
'''
assert text.count(old)==1;text=text.replace(old,new)
(OUT/'spi_edge_plant.cpp').write_text(text,encoding='utf8',newline='\n')
runner=(HERE/'run_spi_edge_plant_r01.py').read_text().replace('STAGE = HERE / "stage-r01"','STAGE = HERE / "stage-r02"')
runner=runner.replace('"field_power_loss", "provider_missing", "sensor_power_loss")',
    '"field_power_loss", "provider_missing", "sensor_power_loss", "CS_stuck_low", "bad_CRC",\n             "replayed_update", "wrong_session", "MOSI_stuck_high", "MOSI_stuck_low", "short_frame")')
old='''    header = ["#pragma once", "#include <vector>", "#include <cstdint>",'''
new='''    frames["fault_update"] = (False, codec.encode_update(session=0x11223344, sequence=17,
        rates=[0x400000] * 12, channel_mask=0xfff))
    frames["foreign_update"] = (False, codec.encode_update(session=0x11223345, sequence=17,
        rates=[0x400000] * 12, channel_mask=0xfff))
    header = ["#pragma once", "#include <vector>", "#include <cstdint>",'''
assert runner.count(old)==1;runner=runner.replace(old,new)
old='''                decoded[label] = codec.decode_response("CS_FB" if len(b) == 176 else "CS_CMD", b)'''
new='''                if scenario == "short_frame" and label == "injected_transport_fault":
                    try:
                        codec.decode_response("CS_CMD", b)
                    except Exception as exc:
                        decoded[label] = {"expected_truncated_transaction": True, "length": len(b), "decode_error": str(exc)}
                    else:
                        raise RuntimeError("Truncated actual response was incorrectly accepted")
                else:
                    decoded[label] = codec.decode_response("CS_FB" if len(b) == 176 else "CS_CMD", b)'''
assert runner.count(old)==1;runner=runner.replace(old,new)
runner=runner.replace('"actual_LinuxCNC_integration": False,','"actual_LinuxCNC_integration": False,\n               "post_fault_correct_UPDATE_restart_rejected": True,',1)
(HERE/'run_spi_edge_plant_r02.py').write_text(runner,encoding='utf8',newline='\n')
assert all(sha(Path(p))==h for p,h in inputs.items())
(OUT/'derivation.json').write_text(json.dumps(dict(input_sha256=inputs,original_sources_unchanged=True,
    scope='Seven additional real SPI fault injections plus explicit failed restart for every fault; unchanged RTL and ideal external providers',
    physical_qualified=False,manufacturing_ready=False),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(prepared=True,expected_scenarios=16)))
