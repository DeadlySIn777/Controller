"""Add exactly one distributed-IO3 reset-buffer bypass to upgraded copies.

Call after apply_io3_upgrade(). Historical helper, MC source and copper stay
unchanged. The native fixture is evidence of connectivity, not final layout.
"""
from pathlib import Path
import copy,json,hashlib,shutil,subprocess,uuid
from hardware_build_assembly import parse,dump,child,children,value,q,point
from hardware_apply_motherboard_io3_upgrade import symbol_for,coords,ROOT
OUT=ROOT/'hardware/motherboard_io3_reset_bypass'
REPORT=ROOT/'reports/motherboard-io3-upgrade-20260930/reset-bypass-r02'
NS=uuid.UUID('ec5d4779-52f0-56b3-b40b-9517a5d9dbaa')
def uid(s):return str(uuid.uuid5(NS,s))
def apply_io3_reset_bypass(tree,model):
 t,m=copy.deepcopy(tree),copy.deepcopy(model);c=m['components'] if 'components'in m else m
 if 'C18001'in c:raise ValueError('Reset bypass ref already fitted')
 if c.get('U2006',{}).get('pins',{}).get('5')!='IO_3V3' or c['U2006']['pins'].get('3')!='LOGIC_GND':raise ValueError('Actual reset-buffer receiving supply/return differs')
 if c.get('C2010',{}).get('pins')!={'1':'IO_3V3_REG_LOCAL','2':'LOGIC_GND'}:raise ValueError('Expected reviewed local reservoir split')
 if c['C2010']['mpn']!='GRM188R72A104KA35D' or c['C2010']['footprint']!='Capacitor_SMD:C_0603_1608Metric':raise ValueError('Unreviewed bypass manufacturer/land')
 s=copy.deepcopy(symbol_for(t,'C2010'));xy,_=coords(t,s);old=point(child(s,'at'));new=(old[0]+30.48,old[1]+30.48);dx,dy=new[0]-old[0],new[1]-old[1]
 child(s,'at')[1:3]=[str(x)for x in new];child(s,'uuid')[1]=q(uid('C18001'))
 for prop in children(s,'property'):
  at=child(prop,'at');at[1:3]=[str(round(float(at[1])+dx,4)),str(round(float(at[2])+dy,4))]
  if value(prop[1])=='Reference':prop[2]=q('C18001')
 for p in children(s,'pin'):child(p,'uuid')[1]=q(uid('C18001'+value(p[1])))
 for project in children(child(s,'instances'),'project'):
  for path in children(project,'path'):child(path,'reference')[1]=q('C18001')
 t.append(s)
 for p,net in [('1','IO_3V3'),('2','LOGIC_GND')]:
  x,y=xy[p];t.append(['label',q(net),['at',str(round(x+dx,4)),str(round(y+dy,4)),'0'],['effects',['font',['size','.85','.85']],['justify','left','bottom']],['uuid',q(uid('C18001'+p+'net'))]])
 c['C18001']=dict(copy.deepcopy(c['C2010']),pins={'1':'IO_3V3','2':'LOGIC_GND'},source_block='motherboard_io3_reset_bypass',source_reference='C18001',role='Dedicated distributedIO3 local100nF bypass for actual resetbufferU2006.VCC5/GND3; never pre-damping REG_LOCAL')
 receipt=dict(id='MB-IO3-002',added_refs=['C18001'],new_components={'C18001':c['C18001']},retained_parts_and_pins_unchanged=True,
  owner={'ref':'U2006','power_pin':'5','return_pin':'3'},native_parent_endpoints={'C18001.1':'/IO_3V3','C18001.2':'/LOGIC_GND'},
  local_layout_qualified=False,effective_capacitance_qualified=False,manufacturing_ready=False)
 return t,m,receipt
def main():
 if REPORT.exists():raise SystemExit('Immutable new bypass report exists')
 REPORT.mkdir(parents=True);OUT.mkdir(exist_ok=True)
 old=ROOT/'hardware/motherboard_io3_upgrade'
 t=parse((old/'motherboard_io3_upgrade.kicad_sch').read_text());m=json.loads((old/'design.json').read_text());t,m,r=apply_io3_reset_bypass(t,m)
 root=value(child(t,'uuid')[1])
 for s in children(t,'symbol'):
  prop=next(p for p in children(s,'property')if value(p[1])=='Reference');ref=value(prop[2]);inst=child(s,'instances')
  if inst:inst[1:]=[['project',q('motherboard_io3_reset_bypass'),['path',q('/'+root),['reference',q(ref)],['unit','1']]]]
 (OUT/'motherboard_io3_reset_bypass.kicad_sch').write_text(dump(t)+'\n')
 (OUT/'design.json').write_text(json.dumps(m,indent=2)+'\n')
 for p in old.iterdir():
  if p.is_dir()and p.suffix=='.pretty':shutil.copytree(p,OUT/p.name)
  elif p.name in ['sym-lib-table','fp-lib-table']or p.suffix=='.kicad_sym':shutil.copyfile(p,OUT/p.name)
 pro=json.loads((old/'motherboard_io3_upgrade.kicad_pro').read_text());pro['meta']['filename']='motherboard_io3_reset_bypass.kicad_pro';(OUT/'motherboard_io3_reset_bypass.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
 cli='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
 for cmd in [('sch','export','netlist','--format','kicadxml','-o',str(OUT/'netlist.xml'),str(OUT/'motherboard_io3_reset_bypass.kicad_sch')),
   ('sch','erc','--format','json','--output',str(REPORT/'erc.json'),str(OUT/'motherboard_io3_reset_bypass.kicad_sch'))]:
  x=subprocess.run([cli,*cmd],capture_output=True,text=True);assert x.returncode==0,x.stdout+x.stderr
 r['inputs']=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in [old/'design.json',old/'motherboard_io3_upgrade.kicad_sch',Path(__file__).resolve(),OUT/'design.json',OUT/'motherboard_io3_reset_bypass.kicad_sch',OUT/'netlist.xml']]
 (REPORT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['owner']))
if __name__=='__main__':main()
