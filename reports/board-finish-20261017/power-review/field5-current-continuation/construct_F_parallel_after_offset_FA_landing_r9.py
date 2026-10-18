"""Conditional offset FA landing keeps its clearance disk away from power escape."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_F_parallel_after_bounded_FA_transfer_r8.py').read_text().replace("'F-parallel-bounded-FA-transfer-probe-r8'","'F-parallel-offset-FA-landing-probe-r9'")
s=s.replace("'x':297.25,'y':155.65","'x':297.65,'y':155.35")
s=s.replace("'tracks':[t for t in g['tracks']if t['uuid']not in retired]","'tracks':[t for t in g['tracks']if t['uuid']not in retired]+[{'uuid':'9f599c5f-4636-5e8d-b921-0ff0e0e20b68','net':'/motherboard_power_entry/FA_SHDN_CONTACT','layer':'F.Cu','a':[297.25,155.65],'b':[297.65,155.35],'w':.2}]")
exec(compile(s,str(HERE/'construct_F_parallel_after_bounded_FA_transfer_r8.py'),'exec'),globals())
