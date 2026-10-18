#include "rig.hpp"
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
