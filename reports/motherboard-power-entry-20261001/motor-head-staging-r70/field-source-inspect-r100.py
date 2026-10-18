import json
from pathlib import Path
for source in ['hardware/motherboard_motor_power/design.json','hardware/motherboard_power_entry/design.json']:
 m=json.loads(Path(source).read_text());print(source)
 for r in ['U9003','U9004','U9007','R9029','R9030','R9039','R9040','R11070','R11072']:
  if r in m['components']:print(r,m['components'][r])
