"""Extend real serial/mechanics fault proof with reset and interrupted-frame epochs."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;OUT=HERE/'stage-r03';OUT.mkdir(exist_ok=False)
sources=[HERE/'stage-r02/spi_edge_plant.cpp',HERE/'stage-r02/edge_plant.hpp',HERE/'run_spi_edge_plant_r02.py',Path(__file__)]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p)for p in sources}
shutil.copyfile(sources[1],OUT/'edge_plant.hpp')
text=sources[0].read_text()
old='''  }else if(scenario=="CS_stuck_low"){
'''
new='''  }else if(scenario=="FPGA_reset"||scenario=="FPGA_reset_during_CS"){
   const auto before=rig.plant.state();
   if(scenario=="FPGA_reset_during_CS"){
    rig.rtl.spi_cs_cmd_n=0;rig.advance(12);
    // Real clocks shift part of a command; reset occurs before CS release.
    for(unsigned bit=0;bit<37;++bit){
     rig.rtl.spi_mosi=(frames::fault_update.bytes[bit/8]>>(7-bit%8))&1;
     rig.advance(4);rig.rtl.spi_sclk=1;rig.advance(4);rig.rtl.spi_sclk=0;
    }
   }
   rig.rtl.rst_n=0;rig.rtl.eval();rig.advance(20);
   check(rig.rtl.enable_n==all_joints&&rig.rtl.step_out==0&&rig.rtl.pos_continuity==0,
         "actual asynchronous reset removes enable and invalidates continuity");
   check(!rig.rtl.spi_miso_oe&&!rig.rtl.config_valid&&!rig.rtl.session,
         "reset releases serial driver and discards configuration/session authority");
   rig.rtl.spi_sclk=rig.rtl.spi_mosi=0;rig.rtl.spi_cs_fb_n=rig.rtl.spi_cs_cmd_n=1;
   rig.rtl.rst_n=1;rig.advance(3000);
   check(rig.rtl.enable_n==all_joints&&!rig.rtl.armed_mask&&!rig.rtl.config_valid,
         "reset release does not automatically configure or arm");
   for(unsigned i=0;i<12;++i)check(rig.plant.state()[i].accepted_electrical_steps>=before[i].accepted_electrical_steps-2&&
      rig.plant.state()[i].accepted_electrical_steps<=before[i].accepted_electrical_steps+2,
      "interrupted frame and reset do not create uncontrolled mechanical displacement");
  }else if(scenario=="CS_stuck_low"){
'''
assert text.count(old)==1;text=text.replace(old,new)
# Reset makes hardware counters start a new epoch. The mechanics and independent
# lifetime observer intentionally retain their history; invalid continuity must
# keep software from treating zeroed hardware counts as an actual return home.
(OUT/'spi_edge_plant.cpp').write_text(text,encoding='utf8',newline='\n')
runner=sources[2].read_text().replace('STAGE = HERE / "stage-r02"','STAGE = HERE / "stage-r03"')
runner=runner.replace('"MOSI_stuck_high", "MOSI_stuck_low", "short_frame")',
                      '"MOSI_stuck_high", "MOSI_stuck_low", "short_frame", "FPGA_reset", "FPGA_reset_during_CS")')
runner=runner.replace('except Exception as exc:\n                        decoded[label]',
    'except codec.ProtocolError as exc:\n                        if exc.code != "LENGTH" or len(b) != 95:\n                            raise RuntimeError("Unexpected truncated-frame rejection") from exc\n                        decoded[label]')
old='''            if scenario in ("clean", "missed_steps"):
'''
new='''            if scenario in ("FPGA_reset", "FPGA_reset_during_CS"):
                assertions["all_twelve_pin_counts"] = (fb["pos_continuity"] == 0 and
                    all(fb[f"step_count_{i}"] == 0 for i in range(12)) and
                    all(state["joints"][i]["observed_rises"] > 20 for i in range(12)))
                assertions["hardware_counter_reset_is_not_mechanical_home"] = all(
                    abs(state["joints"][i]["position"] - 50) > 0.01 for i in range(12))
            if scenario in ("clean", "missed_steps"):
'''
assert runner.count(old)==1;runner=runner.replace(old,new)
runner=runner.replace('"post_fault_correct_UPDATE_restart_rejected": True,',
    '"post_fault_correct_UPDATE_restart_rejected": status == "PASS" and len(cases) == len(SCENARIOS),')
runner=runner.replace('"gaps": ["actual CNC3 HAL and LinuxCNC",',
    '"gaps": ["actual CNC3 HAL and LinuxCNC", "clock-stall inhibition through actual independent electrical watchdog/gating",')
(HERE/'run_spi_edge_plant_r03.py').write_text(runner,encoding='utf8',newline='\n')
assert all(sha(Path(p))==h for p,h in before.items())
(OUT/'derivation.json').write_text(json.dumps(dict(input_sha256=before,unchanged=True,expected_scenarios=18,
    scope='Actual reset and interrupted transaction invalidate counter epoch while independent ideal mechanics retains position; no physical or HAL claim'),indent=2)+'\n')
