#include "edge_plant.hpp"
#include <iostream>
#include <string>
using namespace controller_plant;
static unsigned checks=0;
static void check(bool v,const char*why){++checks;if(!v)throw std::runtime_error(why);}
static bool near(double a,double b){return std::abs(a-b)<1e-8;}
static Config simple(){Config c;for(auto&j:c.joint){j.units_per_output_rev=20;j.full_steps_per_motor_rev=200;j.microsteps=1;}
 for(auto&e:c.encoder){e.edges_per_output_rev=200;e.minimum_edge_cycles=2;}return c;}
static PhysicalDriveState on(){return {true,true,0,all_joints,true};}
struct Rig {
 EdgePlant plant;uint64_t cycle=0;Sensors last;uint16_t last_ab=0;int decoded=0;
 explicit Rig(Config c=simple(),uint64_t seed=1):plant(c,seed){tick(0,0);last_ab=(last.encoder_a&1)*2+(last.encoder_b&1);}
 void tick(uint16_t step,uint16_t dir,PhysicalDriveState d=on()){
  last=plant.tick(cycle++,{step,dir},d);
  int ab=(last.encoder_a&1)*2+(last.encoder_b&1),t=(last_ab<<2)|ab;
  if(last.encoder_connected&1){
   if(t==1||t==7||t==14||t==8)++decoded;
   if(t==2||t==11||t==13||t==4)--decoded;
  }
  last_ab=ab;
 }
 void pulse(uint16_t mask,uint16_t dir=0,PhysicalDriveState d=on()){
  tick(mask,dir,d);for(int i=0;i<7;++i)tick(0,dir,d);
 }
};
int main(){
 try{
  {Rig r;for(int i=0;i<20;++i)r.pulse(all_joints);
   for(const auto&j:r.plant.state()){check(near(j.position,52),"all12 forward physical travel");check(j.accepted_electrical_steps==20,"actual rise count");}
   check(r.decoded==20,"independent Gray decode follows actual movement");
   for(int i=0;i<10;++i)r.pulse(all_joints,all_joints);
   for(const auto&j:r.plant.state())check(near(j.position,51),"all12 reversal");check(r.decoded==10,"reverse Gray decode");}
  {Rig r;PhysicalDriveState d=on();d.tx_permit=false;
   r.tick(all_joints,0,d);check(r.last.step_during_inhibit==all_joints,"inhibit detects emitted rising edges");
   for(int i=0;i<10;++i)r.tick(all_joints,0,d);
   for(const auto&j:r.plant.state()){check(near(j.position,50),"inhibit prevents movement");check(j.inhibited_edges==1,"high level not extra rising edge");}}
  {Rig r;auto d=on();d.valid=false;r.pulse(all_joints,0,d);check(!r.last.sensors_valid,"invalid physical provider unavailable");
   for(const auto&j:r.plant.state())check(j.accepted_electrical_steps==0,"no trusted permission means no physical movement");}
  {Rig r;auto d=on();d.enable_n=1;d.powered&=~2u;r.pulse(all_joints,0,d);
   check(near(r.plant.state()[0].position,50)&&near(r.plant.state()[1].position,50),"individual drive and power gating");
   check(near(r.plant.state()[2].position,50.1),"unaffected drive moves");}
  {Rig r;Faults f;f.lose_every_nth[0]=2;f.reverse_motor=2;f.stalled=4;r.plant.faults(f);
   for(int i=0;i<20;++i)r.pulse(7);
   check(near(r.plant.state()[0].position,51)&&r.plant.state()[0].lost_steps==10,"missed steps visible in physical position");
   check(r.plant.state()[0].accepted_electrical_steps==20,"command edges cannot fabricate successful physical movement");
   check(near(r.plant.state()[1].position,48),"reversed motor");check(near(r.plant.state()[2].position,50),"stalled motor");check(r.decoded==10,"encoder measures actual remaining travel");}
  {Config c=simple();c.joint[0].backlash=.4;Rig r(c);
   for(int i=0;i<10;++i)r.pulse(1);check(near(r.plant.state()[0].position,50.8),"initial half gap explicit");
   for(int i=0;i<4;++i)r.pulse(1,1);check(near(r.plant.state()[0].position,50.8),"reversal takes full backlash gap");
   r.pulse(1,1);check(near(r.plant.state()[0].position,50.7),"contact after reversal gap");}
  {Config c=simple();c.joint[0].maximum=50.2;c.joint[0].home=50.2;c.joint[0].home_width=.01;c.probe_joint=0;c.probe_surface=50.3;Rig r(c);
   for(int i=0;i<5;++i)r.pulse(1);check(near(r.plant.state()[0].position,50.2),"hard stop");check(r.last.home&1,"physical home");check(r.last.limit_high&1,"positive limit");check(r.last.probe,"probe plane");
   r.pulse(1,1);check(near(r.plant.state()[0].position,50.1),"hard-stop loss does not create fictitious motor windup");}
  {Rig r;Faults f;f.reverse_encoder=1;f.encoder_unplugged=2;f.home_stuck_active=4;f.forced_alarm=8;r.plant.faults(f);
   for(int i=0;i<10;++i)r.pulse(1);check(r.decoded==-10,"reversed encoder phase");check(!(r.last.encoder_connected&2),"encoder unplugged explicit");check(r.last.home&4,"stuck home");check(r.last.alarm&8,"drive alarm");}
  {Rig a(simple(),0x91abc),b(simple(),0x91abc);Faults f;f.random_loss_ppm[0]=400000;a.plant.faults(f);b.plant.faults(f);
   for(int i=0;i<1000;++i){a.pulse(1);b.pulse(1);check(a.plant.state()[0].lost_steps==b.plant.state()[0].lost_steps,"repeatable fault seed");}
   auto n=a.plant.state()[0].lost_steps;check(n>300&&n<500,"actual fault generator active");}
  {Config c=simple();c.encoder[0].edges_per_output_rev=20000;Rig r(c);r.pulse(1);
   check(r.last.encoder_backlog[0]>0,"encoder waveform debt explicitly exposed");check(r.decoded<100,"undelivered edges cannot masquerade as feedback");}
  {Rig r;bool caught=false;try{r.plant.tick(r.cycle+1,{0,0},on());}catch(const std::invalid_argument&){caught=true;}check(caught,"missing core cycles rejected");}
  {Config c=simple();c.joint[0].microsteps=0;bool caught=false;try{EdgePlant p(c);}catch(const std::invalid_argument&){caught=true;}check(caught,"invalid physical scale rejected");}
  {Rig r;auto d=on();d.sensor_supply=false;r.pulse(1,0,d);
   check(near(r.plant.state()[0].position,50.1),"sensor loss does not itself invent a motor power cut");
   check(!r.last.sensors_valid && !r.last.encoder_connected && !r.last.home && !r.last.probe,"unpowered feedback unavailable");}
  {Config c=simple();c.joint[0].max_units_per_second=1;Rig r(c);
   r.pulse(1);r.tick(1,0);check((r.last.kinematic_limit&1)&&r.plant.state()[0].lost_steps==1,"explicit ideal velocity envelope");
   check(near(r.plant.state()[0].position,50.1),"over-speed pulse cannot invent achieved travel");}
  {Config c=simple();c.joint[0].units_per_output_rev=5;c.joint[0].motor_revs_per_output_rev=2;c.joint[0].microsteps=4;Rig r(c);
   for(int i=0;i<80;++i)r.pulse(1);check(near(r.plant.state()[0].position,50.25),"screw lead gear ratio and microstep scale");}
  {Config c=simple();for(auto&j:c.joint){j.start=0;j.home=0;}
   Rig r(c);check(r.last.encoder_z==15,"all four configured index windows");
   r.pulse(15);check(r.last.encoder_z==0,"index follows actual encoder phase");
   check(r.last.encoder_b==15 && r.last.encoder_a==0,"four independently connected Gray encoders");
   Faults f;f.home_stuck_inactive=1;f.limit_stuck_inactive=2;f.probe_stuck_active=true;r.plant.faults(f);
   r.pulse(15,15);check(!(r.last.home&1)&&!(r.last.limit_low&2),"inactive home and limit fault masks");check(r.last.probe,"forced probe");}
  {Rig r;bool caught=false;Faults f;f.reverse_motor=0x1000;
   try{r.plant.faults(f);}catch(const std::invalid_argument&){caught=true;}check(caught,"unsupported joint fault bit rejected");}
  {Rig r;bool caught=false;Faults f;f.encoder_unplugged=0x10;
   try{r.plant.faults(f);}catch(const std::invalid_argument&){caught=true;}check(caught,"unsupported encoder fault bit rejected");}
  {Rig r;bool caught=false;Faults f;f.home_stuck_inactive=f.home_stuck_active=1;
   try{r.plant.faults(f);}catch(const std::invalid_argument&){caught=true;}check(caught,"contradictory fault rejected");}
  {Config c=simple();c.joint[0].units_per_output_rev=1e-250;bool caught=false;
   try{EdgePlant p(c);}catch(const std::invalid_argument&){caught=true;}check(caught,"unrepresentable displacement rejected");}
  std::cout<<"EDGE_PLANT_PASS checks="<<checks<<" joints=12 encoders=4 actual_FPGA_integration=0 physical_qualification=0\n";
 }catch(const std::exception&e){std::cerr<<"EDGE_PLANT_FAIL "<<e.what()<<"\n";return 1;}
}
