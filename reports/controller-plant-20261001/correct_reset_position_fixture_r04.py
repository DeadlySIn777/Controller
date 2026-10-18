"""Use actual before/after reset position, not an assumed nonzero net displacement."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent;OUT=HERE/'stage-r04';OUT.mkdir(exist_ok=False)
sources=[HERE/'stage-r03/spi_edge_plant.cpp',HERE/'stage-r03/edge_plant.hpp',HERE/'run_spi_edge_plant_r03.py',Path(__file__)]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p)for p in sources}
shutil.copyfile(sources[1],OUT/'edge_plant.hpp')
text=sources[0].read_text()
old='''  }else if(scenario=="FPGA_reset"||scenario=="FPGA_reset_during_CS"){
   const auto before=rig.plant.state();'''
new='''  }else if(scenario=="FPGA_reset"||scenario=="FPGA_reset_during_CS"){'''
assert text.count(old)==1;text=text.replace(old,new)
old='''   rig.rtl.rst_n=0;rig.rtl.eval();rig.advance(20);'''
new='''   const auto immediately_before_reset=rig.plant.state();
   rig.rtl.rst_n=0;rig.rtl.eval();rig.advance(20);'''
assert text.count(old)==1;text=text.replace(old,new)
old='''   for(unsigned i=0;i<12;++i)check(rig.plant.state()[i].accepted_electrical_steps>=before[i].accepted_electrical_steps-2&&
      rig.plant.state()[i].accepted_electrical_steps<=before[i].accepted_electrical_steps+2,
      "interrupted frame and reset do not create uncontrolled mechanical displacement");'''
new='''   for(unsigned i=0;i<12;++i)check(
      rig.plant.state()[i].accepted_electrical_steps==immediately_before_reset[i].accepted_electrical_steps&&
      rig.plant.state()[i].position==immediately_before_reset[i].position,
      "actual reset and release preserve exact ideal mechanical position while hardware counters clear");'''
assert text.count(old)==1;text=text.replace(old,new)
(OUT/'spi_edge_plant.cpp').write_text(text,encoding='utf8',newline='\n')
runner=sources[2].read_text().replace('STAGE = HERE / "stage-r03"','STAGE = HERE / "stage-r04"')
old='assertions["hardware_counter_reset_is_not_mechanical_home"] = all('
new='assertions["hardware_counter_reset_is_not_mechanical_home"] = any('
assert runner.count(old)==1;runner=runner.replace(old,new)
(HERE/'run_spi_edge_plant_r04.py').write_text(runner,encoding='utf8',newline='\n')
assert all(sha(Path(p))==h for p,h in before.items())
(OUT/'derivation.json').write_text(json.dumps(dict(input_sha256=before,unchanged=True,
    failed_prior_report='actual-spi-reset-fault-plant-r05/receipt.json',
    correction='Several reversing axes correctly returned to their initial position before reset. Instead of requiring every net displacement nonzero, check exact before/after-reset position/count for all12 and require at least one observed nonzero displacement with reset hardware counters. No RTL or hardware rule changed.',
    physical_qualified=False),indent=2)+'\n')
