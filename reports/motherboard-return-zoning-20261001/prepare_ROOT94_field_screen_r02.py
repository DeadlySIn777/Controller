from pathlib import Path
p=Path(__file__).with_name('screen_ROOT94_health_field_reference_r01.py')
q=p.with_name('screen_ROOT94_health_field_reference_r02.py')
assert not q.exists()
s=p.read_text()
old="if c.get('physical')}"
new="if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')}"
assert s.count(old)==1
s=s.replace(old,new).replace('ROOT94-health-field-collar-screen-r01','ROOT94-health-field-collar-screen-r02')
q.write_text(s)
