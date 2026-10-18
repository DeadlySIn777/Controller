from pathlib import Path
p=Path(__file__).parent;s=(p/'inspect_OUT_PERMIT_power_cut_r01.py').read_text()
s=s.replace('hit=p.intersection(removed,narrow)', 'expanded=p.duplicate(a);expanded.Inflate(2,pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);hit=p.subtract(narrow,expanded)')
s=s.replace('actual-power-cut-localization.json','actual-power-precision-escape-localization.json')
(p/'inspect_OUT_PERMIT_power_cut_r02.py').write_text(s)
