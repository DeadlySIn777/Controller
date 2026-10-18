"""Native physical recipe for the three existing TPS2663 entry cells.

No new circuit or source pin is created. Mechanical terminals/fuseholders stay
fixed; this recipe moves the existing 45 local protection/support parts only.
TPS2663 SLVSE94G section 9.4 requires short reverse-FET/fast-pulldown loops,
close support parts, and power paths sized for twice full-load current.
"""
from pathlib import Path
import json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[1]
def recipes():
    groups={};bottom=[];entries=[]
    for i,name in enumerate(['CORE_ENTRY','FIELD_A_ENTRY','FIELD_B_ENTRY']):
        u=f'U{11002+2*i}';rev=f'U{11001+2*i}';q=f'Q{11001+i}';d=f'D{11001+i}';rs=[f'R{11001+7*i+k}'for k in range(7)]
        raw,dt,inp,out=[f'C{11001+4*i+k}'for k in range(4)]
        g={u:[0,0,0],rev:[-6,-1.5,0],q:[-6,2.5,0],d:[-13,0,180],raw:[-3.5,.75,0],dt:[-2,5,270],inp:[-3.8,-4.8,180],out:[3.8,-4.8,0],rs[0]:[-8.5,6.1,90],rs[1]:[-5.7,5.1,0],rs[2]:[-5.7,7.1,0],rs[3]:[.25,4.5,270],rs[4]:[4.8,-1,0],rs[5]:[4.8,1,180],rs[6]:[4.8,3,0]}
        groups[name]=g;bottom.extend([raw,inp,out]);entries.append(dict(name=name,efuse=u,reverse_fet=rev,fast_pulldown=q,tvs=d,raw_cap=raw,dvdt_cap=dt,in_cap=inp,out_cap=out,uv_top=rs[0],uv_mid=rs[1],ov_bottom=rs[2],ilim=rs[3],pg_top=rs[4],pg_bottom=rs[5],imon=rs[6]))
    primary=ROOT/'reports/motherboard-power-entry-20260930/sources/tps2663.pdf'
    return dict(groups=groups,bottom_refs=bottom,entries=entries,primary_datasheet=str(primary.relative_to(ROOT)),primary_sha256=hashlib.sha256(primary.read_bytes()).hexdigest(),no_new_components_or_pin_changes=True,manufacturing_ready=False)
def main():
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);v=a.parse_args();v.output.parent.mkdir(parents=True,exist_ok=True);v.output.write_text(json.dumps(recipes(),indent=2)+'\n')
if __name__=='__main__':main()
