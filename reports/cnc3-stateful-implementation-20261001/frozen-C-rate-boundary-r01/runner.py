"""Execute the unchanged C codec to distinguish builder and incoming checks."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2]
src=Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec/cnc3/src')
out=ROOT/'reports/cnc3-stateful-implementation-20261001/frozen-C-rate-boundary-r01'
out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
unix=lambda p:'/mnt/'+p.drive[0].lower()+p.as_posix()[2:]
names=['cnc3_proto.c','cnc3_proto.h','cnc3_proto_types.h','cnc3_layout.h','cnc3_rules.h']
bound={str(src/n):sha(src/n) for n in names}
for n in names:shutil.copyfile(src/n,out/n)
c=r'''#include "cnc3_proto.h"
#include <stdio.h>
#include <limits.h>
#include <string.h>
int main(void){
 const int32_t rates[]={0,0x01000000,-0x01000000,0x01000001,-0x01000001,INT_MIN,INT_MAX};
 for(unsigned i=0;i<sizeof rates/sizeof rates[0];++i){
  struct cnc3_cmd c;memset(&c,0,sizeof c);c.opcode=CNC3_OP_UPDATE;
  c.session=1;c.sequence=1;c.channel_mask=0xfff;c.rate[0]=rates[i];
  uint8_t frame[CNC3_CS_CMD_BYTES];memset(frame,0,sizeof frame);
  int build=cnc3_build_cmd(frame,&c);
  int incoming=cnc3_validate_command(CNC3_CS_CMD,frame,sizeof frame);
  int forbidden=rates[i]>CNC3_MAX_RATE||rates[i]<-CNC3_MAX_RATE;
  printf("rate=%d build=%d incoming=%d forbidden=%d\n",rates[i],build,incoming,forbidden);
  if(build!=(forbidden?CNC3_E_RATE_CLAMP:CNC3_OK)||incoming!=CNC3_OK)return 1;
 }
 puts("FROZEN_C_RATE_BOUNDARY_CONFIRMED cases=7");return 0;
}
'''
(out/'audit.c').write_text(c,encoding='utf8',newline='\n')
cmd=['wsl','-d','GarciaMechBuilder','--','clang','-std=c11','-Wall','-Wextra','-Werror','-O1',
     '-I'+unix(out),unix(out/'audit.c'),unix(out/'cnc3_proto.c'),'-o',unix(out/'audit')]
r=subprocess.run(cmd,capture_output=True,timeout=60)
(out/'compile.log').write_bytes(r.stdout+r.stderr)
run=None
if r.returncode==0:
 run=subprocess.run(['wsl','-d','GarciaMechBuilder','--',unix(out/'audit')],capture_output=True,timeout=20)
 (out/'execute.log').write_bytes(run.stdout+run.stderr)
unchanged=bound=={str(src/n):sha(src/n) for n in names}
v={'passed':bool(r.returncode==0 and run and run.returncode==0 and unchanged),
   'input_sha256':bound,'original_external_sources_unchanged':unchanged,
   'builder_and_structural_incoming_validation_are_distinct':True,
   'incoming_structural_acceptance_does_not_prove_stateful_rate_safety':True,
   'endpoint_enforcement_qualified':False,'physical_qualified':False,'manufacturing_ready':False,
   'compile_argv':cmd,'compile_exit':r.returncode,'execution_exit':run.returncode if run else None,
   'runner_sha256':sha(Path(__file__)),'fixture_sha256':sha(out/'audit.c')}
(out/'receipt.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
print(json.dumps(v));raise SystemExit(0 if v['passed'] else 1)
