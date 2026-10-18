"""Authorized non-electrical SBC planning correction; preserve frozen r04."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=HERE/'receipt-r04b.json';prior=HERE/'prior-r04-before-planning-clarification'
 if out.exists() or prior.exists():raise SystemExit('Immutable planning receipt/archive exists')
 r=json.loads((HERE/'receipt-r04.json').read_text());old=json.loads((ROOT/'hardware/motherboard_power_entry/design.json').read_text())
 for name,h in r['source_sha256'].items():
  assert sha(ROOT/name)==h,name
  p=prior/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p);assert sha(p)==h
 shutil.copy2(HERE/'receipt-r04.json',prior/'receipt-r04.json')
 builder=ROOT/'tools/hardware_build_motherboard_power_entry.py';s=builder.read_text();token="'host_profile_max_a':3";assert s.count(token)==1
 s=s.replace(token,"'host_profile_planning_reserve_a':3.6,'host_profile_delivery_qualified':False")
 builder.write_text(s)
 readme=ROOT/'hardware/motherboard_power_entry/README.md';s=readme.read_text();token='SBC_5V is the staged commodity-compute branch, with a planning cap of 3 A pending profile/inrush qualification.';assert s.count(token)==1
 readme.write_text(s.replace(token,'SBC_5V is the staged commodity-compute branch. Its conditional ordinary-load screen is 3.151 A and candidate planning reserve is 3.6 A. TPS22990 is a load switch, not a current limiter; neither value qualifies board delivery, socket contact current, profile enforcement or inrush.'))
 run=subprocess.run([sys.executable,'-X','utf8',str(builder)],cwd=ROOT,capture_output=True,text=True);assert run.returncode==0,run.stderr
 new=json.loads((ROOT/'hardware/motherboard_power_entry/design.json').read_text());assert new['components']==old['components'];assert new['nets']==old['nets']
 limits=new['inherited_requirements'];assert 'host_profile_max_a' not in limits and limits['host_profile_planning_reserve_a']==3.6 and limits['host_profile_delivery_qualified'] is False
 cli='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe';source=ROOT/'hardware/motherboard_power_entry/motherboard_power_entry.kicad_sch'
 for command in [[cli,'sch','export','netlist','--output',str(source.parent/'netlist.xml'),'--format','kicadxml',str(source)],[cli,'sch','erc','--output',str(source.parent/'erc.json'),'--format','json',str(source)]]:
  run=subprocess.run(command,capture_output=True,text=True);assert run.returncode==0,run.stderr
 cmd=[sys.executable,'-X','utf8','-m','pytest','-q']+[str(ROOT/'tests'/('test_motherboard_'+n+'.py')) for n in ['motors','motor_power','power_entry','io3_upgrade','io3_window','safety_sensor','probe_limit_upgrade','status','watchdogs']]
 run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);(HERE/'regression-r04b.log').write_text(run.stdout+'\n'+run.stderr);assert run.returncode==0,run.stderr
 run=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/hardware_validate_motherboard_power_entry.py')],cwd=ROOT,capture_output=True,text=True);assert run.returncode==0,run.stderr
 r['revision']='motherboard-power-entry-r0.4b-SBC-planning-clarification';r['prior_r04_archived_before_planning_edit']=True
 r['metadata_only_delta']={'removed':{'host_profile_max_a':3},'added':{'host_profile_planning_reserve_a':3.6,'host_profile_delivery_qualified':False},'normal_SBC_screen_a':3.1513546439628484,'TPS22990_is_not_current_limiter':True}
 r['native_components_pins_nets_equal_r04']=True;r['regression_stdout']=json.loads((HERE/'receipt-r04.json').read_text())['regression_stdout']
 r['source_sha256']={name:sha(ROOT/name) for name in r['source_sha256']}
 r['source_sha256'][Path(__file__).relative_to(ROOT).as_posix()]=sha(Path(__file__));r['source_sha256'][(HERE/'regression-r04b.log').relative_to(ROOT).as_posix()]=sha(HERE/'regression-r04b.log')
 out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'receipt':out.relative_to(ROOT).as_posix(),'parts_pins_nets_unchanged':True,'tests_passed':True,'planning_reserve_a':3.6,'delivery_qualified':False}))
if __name__=='__main__':main()
