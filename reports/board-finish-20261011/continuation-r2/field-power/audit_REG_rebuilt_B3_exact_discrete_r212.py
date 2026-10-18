"""Preserve R209 preflight fail; select the exact ten REG tracks by owned UUID."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_REG_rebuilt_B3_on_wider_IO3_r209.py').read_text(encoding='utf-8')
s=s.replace('REG-rebuilt-B3-on-wider-IO3-full-audit-r209','REG-rebuilt-B3-on-wider-IO3-full-audit-r212')
s=s.replace("'tracks':[t for t in reg['tracks'] if C.norm(t['net'])=='/motherboard_power_entry/FIELD_5V']","'tracks':[t for t in reg['tracks'] if t['uuid'] not in {'21cfaa39-440a-5788-898c-147152921e7a','18008563-f6e6-5172-9f62-6d9aff0561b4','f7771804-1031-58d5-b67f-e44f3ded6f0a'}]")
s=s.replace(",('U9002','10'),('R11053','1')",'').replace(",('U10013','4')",'')
# Include a complete actual source census, without pretending the old bare pads closed.
extra=r''' from regulated_outer_joins_r51 import PORTS
 rail_census=[]
 for bank,net,ref,pin,policy in PORTS:
  groups=F.graph(after,net);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));keys=F.discrete_keys(root);unrooted=[]
  for xs in groups:
   pads=[{k:q[k] for k in ('ref','pin','uuid','net','layer')} for q in xs if q['kind']=='pad']
   if pads and not F.discrete_keys(xs).issubset(keys):unrooted.append({'pads':pads,'physical_contact_count':len(F.discrete_keys(xs))})
  rail_census.append({'bank':bank,'source':ref+'.'+pin,'raw_source_net':next(q['net'] for q in root if q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin)),'source_named_pad_count':len({q['uuid'] for q in root if q['kind']=='pad'}),'remaining_unrooted_named_groups':unrooted,'policy_a':policy})
 write(O/'actual-all-regulated-rail-source-census.json',rail_census)
'''
transform="\ns=s.replace("+repr(" b['REG_rebuilt_B3_exact_R206_on_wider_IO3_R209']")+","+repr(extra+" b['REG_rebuilt_B3_exact_R206_on_wider_IO3_R212']")+")\n"
s=s.replace('exec(compile(s,',transform+'exec(compile(s,')
exec(compile(s,str(H/'audit_REG_rebuilt_B3_on_wider_IO3_r209.py'),'exec'))
