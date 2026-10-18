"""Second finite source-window extension; all R326/R327 constraints retained."""
from pathlib import Path
p=Path(__file__).with_name('nominate_CM79_external_larger_In2_broadened_source_window_r327.py')
s=p.read_text(encoding='utf-8').replace('nominations-r327','nominations-r328').replace('R327_ROUTE','R328_ROUTE').replace('R327_COMPLETE','R328_COMPLETE')
s=s.replace('region=box(90,145,175,225)','region=box(10,145,215,228)').replace('[90,145,175,225]','[10,145,215,228]')
exec(compile(s,str(__file__),'exec'))
