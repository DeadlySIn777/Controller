"""One genuine ordinary target return for the exact retained DI13 transition."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_DI13_native_barrel_bound_r156.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r156','r158').replace('R156','R158')
s=s.replace("for gv in cur['h']['vias']:","for gv in cur['h']['vias']+newvias:")
s=s.replace("'actual_flash_layers':gv['flashed'],'distance_mm':distance","'actual_flash_layers':gv['flashed'],'new_return_conservative_all6_not_yet_native':gv['uuid'] not in inventory[3],'distance_mm':distance")
old=";attempts=[];nominee=None\n for nom in r124['best_nominations'][:1]:"
new=""";attempts=[];nominee=None;cpraw=A.read(H/'fresh-partial-annular-return-r108-physical-checkpoint.pkl');assert C.sha(cpraw)=='0aa98f5c476d32127623ca1de144bdca4e595527dc90b17db6b075af8a5be803';cp=pickle.loads(cpraw);assert cp['current']['h']['tracks']==h0['tracks'] and cp['current']['h']['vias']==h0['vias'] and cp['current']['h']['pads']==h0['pads'];targetpoint=Point(131.25,117.15);reg=cp['physical_GND_return_region'].intersection(targetpoint.buffer(.995,quad_segs=128).difference(targetpoint.buffer(.820,quad_segs=128)));targetreturns=[]
 for site in K.sites(reg,[131.25,118.05],12):
  point=Point(site['at_mm']);ann=point.buffer(.25,quad_segs=128).difference(point.buffer(.1,quad_segs=128));areas={l:ann.intersection(cur['source_planes'][l].intersection(point.buffer(1))).area for l in('In1.Cu','In4.Cu')}
  if all(x>.004 for x in areas.values()):targetreturns.append({**site,'actual_current_source_annular_contact_mm2':areas,'retained_signal_UUID':'161402e1-bd66-40c6-a860-82b78474ff0c','actual_signal_at_mm':[131.25,117.15],'distance_mm':point.distance(targetpoint)})
 print(json.dumps({'phase':'DI13_exact_retained_target_return','ordinary_region_mm2':reg.area,'finite_return_candidates':targetreturns}),flush=True)
 for nom in [{**r124['best_nominations'][0],'extra_target_return':q} for q in targetreturns[:8]]:"""
assert old in s;s=s.replace(old,new)
old="if len(branches)!=2:continue\n  shape=island.union"
new="""if len(branches)!=2:continue
  extra=nom['extra_target_return'];pos=extra['at_mm'];uid,ch=SERIAL.serial_via(identity,GND,pos);assert uid not in inventory[3] and uid not in chunks;assert all(math.dist(pos,[v['x'],v['y']])>=.815 for v in nv);nv.append({'uuid':uid,'net':identity.raw(GND),'x':pos[0],'y':pos[1],'d':.5,'drill':.2,'flashed':list(LAYERS)});chunks[uid]=ch;row['exact_target_new_return_nomination']={**extra,'new_UUID':uid,'conservative_all6_native_annuli_gate':'OPEN'}
  shape=island.union"""
assert old in s;s=s.replace(old,new)
s=s.replace("'actual_native_scope_barrels':","'exact_target_return_candidates':targetreturns,'actual_native_scope_barrels':")
s=s.replace("'new_DI13_signal_vias':0","'new_DI13_signal_vias':0,'one_new_ordinary_DI13_target_GND_return_prospective_native_gate':'OPEN'")
dst=H/'construct_DI15_DI13_exact_target_return_r158.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI13-exact-target-return-r158.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'R156 binds real source barrel3915 with actual existing fcee7e06 return0.8422065mm and finite source annuli. R158 adds at most one ordinary current all6 .5/.2 return within1mm of actual retained target161402e1, retaining its unchanged .575mm disk only after genuine final In1/In4 annular root contact. No DI13 new signal barrel or >3-leg path. Full current/native gates open.'},indent=1)+'\n');print(sha(dst.read_bytes()))
