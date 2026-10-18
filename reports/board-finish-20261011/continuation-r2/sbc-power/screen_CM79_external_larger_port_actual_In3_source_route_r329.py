"""Read-only alternate actual-source layer screen; original In2 failures frozen."""
from pathlib import Path
p=Path(__file__).with_name('nominate_CM79_external_larger_port_actual_In2_source_route_r326.py')
s=p.read_text(encoding='utf-8').replace('In2','In3').replace('r326','r329').replace('R326','R329')
s=s.replace('region=box(104,158,144,214)','region=box(10,145,215,228)').replace('[104,158,144,214]','[10,145,215,228]')
s=s.replace("started=time.monotonic();assert not O.exists();O.mkdir()", "started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-read-only-layer-screen.py').write_text(s,encoding='utf-8')")
exec(compile(s,str(__file__),'exec'))
