#include "Vcnc3_runtime.h"
#include "verilated.h"
#include <iostream>
int main(){VerilatedContext context;Vcnc3_runtime r{&context};r.rst_n=0;
 r.sim_context=1;r.sim_expected_session=1;r.sim_expected_config_hash=2;
 r.provider_tag=0x53494d32;r.provider_abi=1;r.provider_session=1;r.provider_config_hash=2;
 r.provider_sequence=1;r.provider_valid_mask=31;r.provider_faults=0;r.provider_strobe=1;
 r.inhibit_n=r.wd_m_ok=r.wd_o_ok=r.reset_arm_ready=r.contactor_deenergized=r.sto_arm_expected=1;
 r.encoder_port_valid=15;r.gate_high=r.opi_ok=15;r.spi_cs_fb_n=r.spi_cs_cmd_n=1;
 for(unsigned i=0;i<10000;++i){if(i==4)r.rst_n=1;r.clk=0;r.eval();r.clk=1;r.eval();
  if(r.sim_ready||r.physical_authority||r.production_profile_complete||r.step_out||r.dout_request||r.enable_n!=4095){std::cerr<<"DEFAULT_DENY_FAIL\n";return 1;}}
 std::cout<<"DEFAULT_DENY_PASS cycles=10000\n";return 0;}
